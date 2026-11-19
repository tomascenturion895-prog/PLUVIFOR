package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// WithStations registra GET /api/stations y GET /api/stations/{station_id} con el lector indicado.
// Tienen prioridad sobre el reenvío a Python: el contrato es el mismo (openapi.yaml).
func WithStations(r station.Reader, logger *slog.Logger) Option {
	h := &stationHandlers{svc: station.NewService(r), logger: logger}
	return func(mux *http.ServeMux) {
		mux.HandleFunc("GET /api/stations", h.list)
		mux.HandleFunc("GET /api/stations/{station_id}", h.get)
	}
}

type stationHandlers struct {
	svc    *station.Service
	logger *slog.Logger
}

type stationList struct {
	Items  []station.Station `json:"items"`
	Total  int               `json:"total"`
	Limit  int               `json:"limit"`
	Offset int               `json:"offset"`
}

func (h *stationHandlers) list(w http.ResponseWriter, r *http.Request) {
	p := &params{values: r.URL.Query()}
	f := station.Filters{
		SourceCode: p.text("source", 64),
		Network:    p.text("network", 100),
		Department: p.text("department", 100),
		Zone:       p.text("zone", 100),
	}
	f.CoordsStatus = p.oneOf("coords_status", "", station.CoordsVerified, station.CoordsPending)
	f.Text = p.text("q", 100)
	defLimit, defOffset := 100, 0
	limit := p.queryInt("limit", &defLimit, 1, 200)
	offset := p.queryInt("offset", &defOffset, 0, maxID)
	if !p.valid() {
		apierror.Validation(w, p.errs)
		return
	}
	items, total, err := h.svc.Search(r.Context(), f, station.Page{Limit: limit, Offset: offset})
	if err != nil {
		h.internal(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, stationList{Items: items, Total: total, Limit: limit, Offset: offset})
}

func (h *stationHandlers) get(w http.ResponseWriter, r *http.Request) {
	p := &params{}
	id := p.intIn("path", "station_id", r.PathValue("station_id"), true, nil, 1, maxID)
	if !p.valid() {
		apierror.Validation(w, p.errs)
		return
	}
	st, err := h.svc.Get(r.Context(), id)
	switch {
	case errors.Is(err, station.ErrNotFound):
		apierror.Write(w, http.StatusNotFound, "station_not_found", "No existe la estación pedida.")
	case err != nil:
		h.internal(w, r, err)
	default:
		writeJSON(w, http.StatusOK, st)
	}
}

func (h *stationHandlers) internal(w http.ResponseWriter, r *http.Request, err error) {
	logInternal(r.Context(), h.logger, r, err)
	apierror.Status(w, http.StatusInternalServerError)
}

// logInternal deja el detalle solo en el registro del servidor; nunca va en la respuesta.
func logInternal(ctx context.Context, logger *slog.Logger, r *http.Request, err error) {
	if logger != nil {
		logger.ErrorContext(ctx, "fallo al consultar la base", "ruta", r.URL.Path, "detalle", err)
	}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
