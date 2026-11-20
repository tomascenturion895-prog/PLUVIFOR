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

func TestRutasPropiasLlevanLosEncabezadosDeSeguridadDePython(t *testing.T) {
	srv := newParityServer(t, loadMemStore(t))
	for _, path := range []string{"/api/stations", "/api/stations/4242", "/health", "/no-existe"} {
		h := get(t, srv, path).Header()
		for k, want := range map[string]string{
			"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
			"Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
		} {
			if got := h.Get(k); got != want || len(h.Values(k)) != 1 {
				t.Errorf("%s %s = %v, quería %q una sola vez", path, k, h.Values(k), want)
			}
		}
	}
}

func TestLimiteDePedidosPorClienteDevuelve429ConEspera(t *testing.T) {
	cfg := testConfig()
	cfg.RateLimitPerMinute = 3
	store := loadMemStore(t)
	logger := newParityLogger()
	srv := New(cfg, logger, WithStations(store, logger))

	pedir := func(remote string) *httptest.ResponseRecorder {
		req := httptest.NewRequest(http.MethodGet, "/api/stations/1", nil)
		req.RemoteAddr = remote
		rec := httptest.NewRecorder()
		srv.ServeHTTP(rec, req)
		return rec
	}
	for i := 1; i <= 3; i++ {
		if rec := pedir("10.0.0.1:5000"); rec.Code != 200 {
			t.Fatalf("pedido %d → %d", i, rec.Code)
		}
	}
	rec := pedir("10.0.0.1:5001") // otro puerto, mismo cliente
	if rec.Code != 429 || rec.Header().Get("Retry-After") == "" || !strings.Contains(rec.Body.String(), "too_many_requests") ||
		!strings.Contains(rec.Body.String(), "Esperá") {
		t.Fatalf("%d %v %s", rec.Code, rec.Header(), rec.Body.String())
	}
	if rec.Header().Get("X-Frame-Options") != "DENY" {
		t.Error("el 429 también debe llevar los encabezados de seguridad")
	}
	if other := pedir("10.0.0.2:5000"); other.Code != 200 {
		t.Fatalf("otro cliente no debe verse afectado: %d", other.Code)
	}
	// /health no cuenta para el límite
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	req.RemoteAddr = "10.0.0.1:5000"
	hrec := httptest.NewRecorder()
	srv.ServeHTTP(hrec, req)
	if hrec.Code != 200 {
		t.Fatalf("/health → %d", hrec.Code)
	}
}

func TestLaImportacionTieneSuPropioMaximo(t *testing.T) {
	cfg := testConfig()
	cfg.RateLimitPerMinute = 100
	cfg.RateLimitImportPerMinute = 1
	backend := http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusNoContent) })
	srv := New(cfg, newParityLogger(), WithBackend(backend))
	codes := []int{}
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodPost, "/api/import/audit", nil)
		req.RemoteAddr = "10.0.0.1:1"
		rec := httptest.NewRecorder()
		srv.ServeHTTP(rec, req)
		codes = append(codes, rec.Code)
	}
	if codes[0] != 204 || codes[1] != 429 {
		t.Fatalf("códigos = %v, quería [204 429]", codes)
	}
}
