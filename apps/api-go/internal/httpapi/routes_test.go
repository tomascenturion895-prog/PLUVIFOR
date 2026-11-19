package httpapi

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func get(t *testing.T, h http.Handler, path string) *httptest.ResponseRecorder {
	t.Helper()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
	return rec
}

func TestEstacionInexistenteDevuelve404EnEspañol(t *testing.T) {
	rec := get(t, newParityServer(t, loadMemStore(t)), "/api/stations/4242")
	if rec.Code != 404 || !strings.Contains(rec.Body.String(), `"station_not_found"`) || !strings.Contains(rec.Body.String(), "No existe la estación pedida.") {
		t.Fatalf("%d %s", rec.Code, rec.Body.String())
	}
}

func TestFiltroInvalidoDevuelve422ConTodosLosErrores(t *testing.T) {
	rec := get(t, newParityServer(t, loadMemStore(t)), "/api/stations?limit=0&coords_status=x&offset=-1")
	if rec.Code != 422 {
		t.Fatalf("estado = %d", rec.Code)
	}
	for _, campo := range []string{`"query.limit"`, `"query.coords_status"`, `"query.offset"`} {
		if !strings.Contains(rec.Body.String(), campo) {
			t.Errorf("falta %s en %s", campo, rec.Body.String())
		}
	}
	if strings.Contains(rec.Body.String(), "=x") {
		t.Error("el error no debe repetir el valor que mandó quien consulta")
	}
}

func TestSerieSinParametrosPideTodosLosObligatorios(t *testing.T) {
	rec := get(t, newParityServer(t, loadMemStore(t)), "/api/rainfall")
	for _, campo := range []string{`"query.station_id"`, `"query.from"`, `"query.to"`} {
		if !strings.Contains(rec.Body.String(), campo) {
			t.Errorf("falta %s en %s", campo, rec.Body.String())
		}
	}
}

func TestUnHuecoSeDevuelveSinDatoNuncaCero(t *testing.T) {
	// La estación 1 no tiene datos en 2020: todo el período es «sin_fila» y mm es null.
	rec := get(t, newParityServer(t, loadMemStore(t)), "/api/rainfall?station_id=1&from=2020-01-01&to=2020-01-03")
	body := rec.Body.String()
	if rec.Code != 200 || strings.Count(body, `"state":"sin_fila"`) != 3 || strings.Contains(body, `"mm":0`) {
		t.Fatalf("%d %s", rec.Code, body)
	}
	if !strings.Contains(body, `"accumulated_mm":null`) {
		t.Fatalf("el acumulado de un período sin datos debe ser null: %s", body)
	}
}

func TestFalloDeLaBaseEs500SinDetalleInterno(t *testing.T) {
	store := loadMemStore(t)
	store.fail = errors.New("password=secreto en la cadena de conexión")
	srv := newParityServer(t, store)
	for _, path := range []string{"/api/stations", "/api/stations/1", "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-02"} {
		rec := get(t, srv, path)
		if rec.Code != 500 || strings.Contains(rec.Body.String(), "secreto") || !strings.Contains(rec.Body.String(), "internal_error") {
			t.Errorf("%s: %d %s", path, rec.Code, rec.Body.String())
		}
	}
}

func TestMetodoNoPermitidoSigueEnElFormatoUnico(t *testing.T) {
	rec := httptest.NewRecorder()
	newParityServer(t, loadMemStore(t)).ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/api/stations", nil))
	if rec.Code != 405 || !strings.Contains(rec.Body.String(), "method_not_allowed") {
		t.Fatalf("%d %s", rec.Code, rec.Body.String())
	}
}

// Las rutas propias de Go ganan sobre el reenvío a Python; las demás siguen yendo a Python.
func TestRutasPropiasGananAlReenvioYElRestoSeReenvia(t *testing.T) {
	var reenviadas []string
	backend := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reenviadas = append(reenviadas, r.URL.Path)
		w.WriteHeader(http.StatusNoContent)
	})
	store := loadMemStore(t)
	logger := newParityLogger()
	srv := New(testConfig(), logger, WithBackend(backend), WithStations(store, logger), WithRainfall(store, mustDate(t, "2026-10-31"), logger))

	if rec := get(t, srv, "/api/stations/1"); rec.Code != 200 {
		t.Fatalf("/api/stations/1 → %d", rec.Code)
	}
	if rec := get(t, srv, "/api/rainfall?station_id=1&from=2015-01-01&to=2015-01-02"); rec.Code != 200 {
		t.Fatalf("/api/rainfall → %d", rec.Code)
	}
	for _, p := range []string{"/api/rainfall/compare", "/api/rainfall/accumulated", "/api/reports/summary", "/api/network/health"} {
		if rec := get(t, srv, p); rec.Code != http.StatusNoContent {
			t.Errorf("%s debía reenviarse a Python, devolvió %d", p, rec.Code)
		}
	}
	if len(reenviadas) != 4 {
		t.Fatalf("se reenviaron %d rutas, quería 4: %v", len(reenviadas), reenviadas)
	}
}
