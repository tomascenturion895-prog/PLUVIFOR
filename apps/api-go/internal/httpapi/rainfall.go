package httpapi

import (
	"errors"
	"log/slog"
	"net/http"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// Leyenda obligatoria, igual que en la API de Python.
const notice = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"

// WithRainfall registra GET /api/rainfall (serie diaria de una estación). Las rutas hermanas
// /api/rainfall/compare y /api/rainfall/accumulated siguen en Python por el reenvío.
func WithRainfall(r rainfall.Reader, cutoff civil.Date, logger *slog.Logger) Option {
	h := &rainfallHandlers{svc: rainfall.NewService(r, cutoff), logger: logger}
	return func(mux *http.ServeMux) { mux.HandleFunc("GET /api/rainfall", h.series) }
}

type rainfallHandlers struct {
	svc    *rainfall.Service
	logger *slog.Logger
}

type dayOut struct {
	ObsDate  civil.Date `json:"obs_date"`
	State    string     `json:"state"`
	MM       *float64   `json:"mm"` // null en un hueco, nunca 0
	Category string     `json:"category"`
	Source   string     `json:"source"`
	Flags    []string   `json:"flags"`
}

type seriesOut struct {
	StationID      int                `json:"station_id"`
	StationName    string             `json:"station_name"`
	Source         station.Source     `json:"source"`
	Category       string             `json:"category"`
	DateFrom       civil.Date         `json:"date_from"`
	DateTo         civil.Date         `json:"date_to"`
	DataCutoffDate civil.Date         `json:"data_cutoff_date"`
	Clipped        bool               `json:"clipped_to_cutoff"`
	Summary        rainfall.Summary   `json:"summary"`
	Warnings       []rainfall.Warning `json:"warnings"`
	Days           []dayOut           `json:"days"`
	Notice         string             `json:"notice"`
}

func (h *rainfallHandlers) series(w http.ResponseWriter, r *http.Request) {
	p := &params{values: r.URL.Query()}
	idRaw, idOK := p.raw("station_id")
	id := p.intIn("query", "station_id", idRaw, idOK, nil, 1, maxID)
	from := p.date("from")
	to := p.date("to")
	cat, _ := rainfall.ParseCategory(p.oneOf("category", string(rainfall.Observado),
		string(rainfall.Observado), string(rainfall.Referencia), string(rainfall.Estimado)))
	if !p.valid() {
		apierror.Validation(w, p.errs)
		return
	}

	res, err := h.svc.Series(r.Context(), id, from, to, cat)
	var bizErr *rainfall.Error
	switch {
	case errors.As(err, &bizErr):
		apierror.Write(w, bizErr.Status, bizErr.Code, bizErr.Message)
		return
	case err != nil:
		logInternal(r.Context(), h.logger, r, err)
		apierror.Status(w, http.StatusInternalServerError)
		return
	}

	days := make([]dayOut, len(res.Days))
	for i, d := range res.Days {
		days[i] = dayOut{
			ObsDate: d.Date, State: string(d.State), MM: d.MM, Category: string(res.Category),
			Source: res.Station.Source.Code, Flags: rainfall.FlagsOnDay(res.Warnings, d.Date),
		}
	}
	writeJSON(w, http.StatusOK, seriesOut{
		StationID: res.Station.ID, StationName: res.Station.Name, Source: res.Station.Source,
		Category: string(res.Category), DateFrom: res.From, DateTo: res.To,
		DataCutoffDate: h.svc.Cutoff(), Clipped: res.Clipped, Summary: res.Summary,
		Warnings: res.Warnings, Days: days, Notice: notice,
	})
}
