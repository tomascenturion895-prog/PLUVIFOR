package httpapi

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"strings"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
)

func newEventsServer(t testing.TB, store *memStore) http.Handler {
	t.Helper()
	cfg := config.Config{Env: "test", CutoffDate: "2026-10-31"}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	return New(cfg, logger, WithEvents(store, store, mustDate(t, "2026-10-31"), logger))
}

type eventsBody struct {
	Category   string `json:"category"`
	MinDryDays int    `json:"min_dry_days"`
	Stations   []struct {
		StationID  int              `json:"station_id"`
		Ge50       []map[string]any `json:"days_50mm_or_more"`
		Ge100      []map[string]any `json:"days_100mm_or_more"`
		DryStreaks []map[string]any `json:"dry_streaks"`
		Longest    map[string]any   `json:"longest_dry_streak"`
		Summary    map[string]any   `json:"summary"`
		Warnings   []map[string]any `json:"warnings"`
	} `json:"stations"`
	Notice string `json:"notice"`
}

func decodeEvents(t *testing.T, body string) eventsBody {
	t.Helper()
	var b eventsBody
	if err := json.Unmarshal([]byte(body), &b); err != nil {
		t.Fatalf("JSON inválido: %v\n%s", err, body)
	}
	return b
}

func TestEventosDeLaEstacionConCerosProlongadosSeAdvierten(t *testing.T) {
	// Caso de demostración de AGENTS.md: la 424 marca 0 mm durante 281 días seguidos.
	srv := newEventsServer(t, loadMemStore(t))
	rec := get(t, srv, "/api/events?station_id=2&from=2015-09-20&to=2016-06-26")
	if rec.Code != 200 {
		t.Fatalf("%d %s", rec.Code, rec.Body.String())
	}
	b := decodeEvents(t, rec.Body.String())
	if len(b.Stations) != 1 || b.Stations[0].Longest == nil {
		t.Fatalf("falta la racha más larga: %s", rec.Body.String())
	}
	l := b.Stations[0].Longest
	if l["days"].(float64) != 281 || l["zero_run_warning"] != true {
		t.Errorf("la racha de 281 días debe venir con la advertencia de ceros: %v", l)
	}
	if !strings.Contains(rec.Body.String(), "ceros_prolongados") {
		t.Error("la respuesta debe llevar la advertencia de ceros prolongados")
	}
	if b.Category != "observado" || !strings.Contains(b.Notice, "PROTOTIPO") {
		t.Errorf("categoría o leyenda: %+v", b)
	}
}

func TestSinDatosNoHayEventosNiRachaYLasListasSonVacias(t *testing.T) {
	// La estación 1 no tiene datos en 2020: todo es sin_fila, nada es un evento ni un día seco.
	rec := get(t, newEventsServer(t, loadMemStore(t)), "/api/events?station_id=1&from=2020-01-01&to=2020-01-31")
	body := rec.Body.String()
	if rec.Code != 200 {
		t.Fatalf("%d %s", rec.Code, body)
	}
	for _, esperado := range []string{`"days_50mm_or_more":[]`, `"days_100mm_or_more":[]`, `"dry_streaks":[]`, `"longest_dry_streak":null`} {
		if !strings.Contains(body, esperado) {
			t.Errorf("falta %s en %s", esperado, body)
		}
	}
}

func TestRangoYParametrosInvalidos(t *testing.T) {
	srv := newEventsServer(t, loadMemStore(t))
	casos := map[string]string{
		"/api/events": `"query.from"`,
		"/api/events?station_id=2&from=2016-02-01&to=2016-01-01":                "invalid_range",
		"/api/events?station_id=2&from=2026-11-05&to=2026-11-09":                "after_cutoff",
		"/api/events?station_id=0&from=2016-01-01&to=2016-01-31":                `"query.station_id"`,
		"/api/events?from=2016-01-01&to=2016-01-31":                             "station_id o zone",
		"/api/events?station_id=2&zone=x&from=2016-01-01&to=2016-01-31":         "station_id o zone",
		"/api/events?station_id=2&from=2016-01-01&to=2016-01-31&min_dry_days=0": `"query.min_dry_days"`,
		"/api/events?station_id=2&from=2016-01-01&to=2016-01-31&category=otra":  `"query.category"`,
		"/api/events?station_id=4242&from=2016-01-01&to=2016-01-31":             "station_not_found",
	}
	for path, esperado := range casos {
		rec := get(t, srv, path)
		if rec.Code < 400 || !strings.Contains(rec.Body.String(), esperado) {
			t.Errorf("%s: %d %s (se esperaba %s)", path, rec.Code, rec.Body.String(), esperado)
		}
	}
}

func TestElPeriodoSeRecortaALaFechaDeCorte(t *testing.T) {
	rec := get(t, newEventsServer(t, loadMemStore(t)), "/api/events?station_id=2&from=2026-10-25&to=2026-12-31")
	if rec.Code != 200 || !strings.Contains(rec.Body.String(), `"date_to":"2026-10-31"`) || !strings.Contains(rec.Body.String(), `"clipped_to_cutoff":true`) {
		t.Fatalf("%d %s", rec.Code, rec.Body.String())
	}
}

func TestEventosConFalloDeLaBaseEs500SinDetalleInterno(t *testing.T) {
	store := loadMemStore(t)
	store.fail = io.ErrUnexpectedEOF
	rec := get(t, newEventsServer(t, store), "/api/events?station_id=2&from=2016-01-01&to=2016-01-31")
	if rec.Code != 500 || !strings.Contains(rec.Body.String(), "internal_error") || strings.Contains(rec.Body.String(), "EOF") {
		t.Fatalf("%d %s", rec.Code, rec.Body.String())
	}
}

func TestPorZonaAnalizaCadaEstacionDeLaZona(t *testing.T) {
	store := loadMemStore(t)
	zona := "Zona de prueba"
	n := 0
	for i := range store.stations {
		if store.stations[i].ID == 2 || store.stations[i].ID == 3 {
			store.stations[i].Zone = &zona
			n++
		}
	}
	if n != 2 {
		t.Fatalf("la base de demostración debería tener las estaciones 2 y 3, hay %d", n)
	}
	rec := get(t, newEventsServer(t, store), "/api/events?zone=Zona%20de%20prueba&from=2015-09-20&to=2016-06-26")
	b := decodeEvents(t, rec.Body.String())
	if rec.Code != 200 || len(b.Stations) != 2 {
		t.Fatalf("esperadas 2 estaciones en la zona, devueltas %d (%d): %s", len(b.Stations), rec.Code, rec.Body.String())
	}
	vacia := get(t, newEventsServer(t, store), "/api/events?zone=Inexistente&from=2015-09-20&to=2015-09-30")
	if vacia.Code != 200 || !strings.Contains(vacia.Body.String(), `"stations":[]`) {
		t.Errorf("una zona sin estaciones devuelve lista vacía: %d %s", vacia.Code, vacia.Body.String())
	}
}
