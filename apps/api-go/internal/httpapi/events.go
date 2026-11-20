package httpapi

import (
	"context"
	"errors"
	"log/slog"
	"net/http"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/events"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// maxZoneStations limita cuántas estaciones se analizan en una consulta por zona.
const maxZoneStations = 100

// defaultMinDryDays es el largo mínimo de una racha seca para listarla. Valor provisional,
// pendiente de confirmar: la racha más larga se informa siempre.
const defaultMinDryDays = 7

// ZoneSearcher es lo que se necesita del catálogo para resolver una zona.
type ZoneSearcher interface {
	Search(ctx context.Context, f station.Filters, p station.Page) ([]station.Station, int, error)
}

// WithEvents registra GET /api/events (días de lluvia intensa y rachas secas, descriptivo).
func WithEvents(r rainfall.Reader, z ZoneSearcher, cutoff civil.Date, logger *slog.Logger) Option {
	h := &eventHandlers{svc: rainfall.NewService(r, cutoff), zones: z, logger: logger}
	return func(mux *http.ServeMux) { mux.HandleFunc("GET /api/events", h.list) }
}

type eventHandlers struct {
	svc    *rainfall.Service
	zones  ZoneSearcher
	logger *slog.Logger
}

type eventsStationOut struct {
	StationID        int                `json:"station_id"`
	StationName      string             `json:"station_name"`
	Source           station.Source     `json:"source"`
	Summary          rainfall.Summary   `json:"summary"`
	Ge50             []events.Event     `json:"days_50mm_or_more"`
	Ge100            []events.Event     `json:"days_100mm_or_more"`
	DryStreaks       []events.DryStreak `json:"dry_streaks"`
	LongestDryStreak *events.DryStreak  `json:"longest_dry_streak"`
	Warnings         []rainfall.Warning `json:"warnings"`
}

type eventsOut struct {
	Category       string             `json:"category"`
	DateFrom       civil.Date         `json:"date_from"`
	DateTo         civil.Date         `json:"date_to"`
	DataCutoffDate civil.Date         `json:"data_cutoff_date"`
	Clipped        bool               `json:"clipped_to_cutoff"`
	MinDryDays     int                `json:"min_dry_days"`
	Stations       []eventsStationOut `json:"stations"`
	Notice         string             `json:"notice"`
	Description    string             `json:"description"`
}

const eventsDescription = "Cuenta descriptiva de lo que pasó, no una alerta ni una predicción. " +
	"Un día sin dato no es un día seco: corta la racha seca y no la extiende."

func (h *eventHandlers) list(w http.ResponseWriter, r *http.Request) {
	p := &params{values: r.URL.Query()}
	idRaw, hasID := p.raw("station_id")
	id := 0
	if hasID {
		id = p.intIn("query", "station_id", idRaw, hasID, nil, 1, maxID)
	}
	zone := p.text("zone", 100)
	from := p.date("from")
	to := p.date("to")
	def := defaultMinDryDays
	minDry := p.queryInt("min_dry_days", &def, 1, 3660)
	cat, _ := rainfall.ParseCategory(p.oneOf("category", string(rainfall.Observado),
		string(rainfall.Observado), string(rainfall.Referencia), string(rainfall.Estimado)))
	if hasID == (zone != "") && p.valid() {
		p.fail("query", "station_id", "Hay que indicar station_id o zone, pero no los dos ni ninguno.")
	}
	if !p.valid() {
		apierror.Validation(w, p.errs)
		return
	}

	end, clipped, err := h.svc.CheckRange(from, to)
	if err != nil {
		h.fail(w, r, err)
		return
	}
	ids := []int{id}
	if zone != "" {
		list, _, err := h.zones.Search(r.Context(), station.Filters{Zone: zone}, station.Page{Limit: maxZoneStations})
		if err != nil {
			h.fail(w, r, err)
			return
		}
		ids = ids[:0]
		for _, s := range list {
			ids = append(ids, s.ID)
		}
	}

	out := eventsOut{
		Category: string(cat), DateFrom: from, DateTo: end, DataCutoffDate: h.svc.Cutoff(),
		Clipped: clipped, MinDryDays: minDry, Stations: []eventsStationOut{},
		Notice: notice, Description: eventsDescription,
	}
	for _, sid := range ids {
		res, err := h.svc.Series(r.Context(), sid, from, to, cat)
		if err != nil {
			h.fail(w, r, err)
			return
		}
		a := events.Analyze(res.Days, res.Warnings, minDry)
		out.Stations = append(out.Stations, eventsStationOut{
			StationID: res.Station.ID, StationName: res.Station.Name, Source: res.Station.Source,
			Summary: res.Summary, Ge50: a.Ge50, Ge100: a.Ge100, DryStreaks: a.DryStreaks,
			LongestDryStreak: a.Longest, Warnings: res.Warnings,
		})
	}
	writeJSON(w, http.StatusOK, out)
}

func (h *eventHandlers) fail(w http.ResponseWriter, r *http.Request, err error) {
	var biz *rainfall.Error
	if errors.As(err, &biz) {
		apierror.Write(w, biz.Status, biz.Code, biz.Message)
		return
	}
	logInternal(r.Context(), h.logger, r, err)
	apierror.Status(w, http.StatusInternalServerError)
}
