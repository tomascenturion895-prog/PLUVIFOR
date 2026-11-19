package proxy_test

import (
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/httpapi"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/proxy"
)

func logger() *slog.Logger { return slog.New(slog.NewTextHandler(io.Discard, nil)) }

// servidor arma Go delante de un «backend» falso y devuelve la dirección de Go.
func servidor(t *testing.T, backend http.Handler) (*httptest.Server, *httptest.Server) {
	t.Helper()
	py := httptest.NewServer(backend)
	t.Cleanup(py.Close)
	target, _ := url.Parse(py.URL)
	cfg := config.Config{Env: "test", CutoffDate: "2026-10-31", BackendURL: target}
	goAPI := httptest.NewServer(httpapi.New(cfg, logger(), httpapi.WithBackend(proxy.New(target, logger()))))
	t.Cleanup(goAPI.Close)
	return goAPI, py
}

func TestReenviaElPedidoYDevuelveLoMismoQuePython(t *testing.T) {
	const cuerpo = `{"items":[],"total":0,"limit":100,"offset":0}`
	goAPI, _ := servidor(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/stations" || r.URL.RawQuery != "zone=norte&limit=5" {
			t.Errorf("el backend recibió otra ruta: %s?%s", r.URL.Path, r.URL.RawQuery)
		}
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		_, _ = io.WriteString(w, cuerpo)
	}))
	resp, err := http.Get(goAPI.URL + "/api/stations?zone=norte&limit=5")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	got, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 || string(got) != cuerpo || resp.Header.Get("Content-Type") != "application/json" {
		t.Fatalf("respuesta cambiada: %d %q %v", resp.StatusCode, got, resp.Header)
	}
	if n := len(resp.Header.Values("X-Content-Type-Options")); n != 1 {
		t.Fatalf("el encabezado de seguridad no debe duplicarse: %d", n)
	}
}

func TestReenviaElCuerpoYLaClaveDeAdministracion(t *testing.T) {
	goAPI, _ := servidor(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		b, _ := io.ReadAll(r.Body)
		if r.Method != http.MethodPost || string(b) != `{"station_ids":[2,3]}` || r.Header.Get("X-API-Key") != "clave-de-prueba" {
			t.Errorf("pedido alterado: %s %q %q", r.Method, b, r.Header.Get("X-API-Key"))
		}
		w.WriteHeader(http.StatusCreated)
	}))
	req, _ := http.NewRequest(http.MethodPost, goAPI.URL+"/api/reports/summary", strings.NewReader(`{"station_ids":[2,3]}`))
	req.Header.Set("X-API-Key", "clave-de-prueba")
	resp, err := http.DefaultClient.Do(req)
	if err != nil || resp.StatusCode != http.StatusCreated {
		t.Fatalf("esperaba 201: %v %v", resp, err)
	}
}

func TestElErrorPropioDelBackendNoSeReescribe(t *testing.T) {
	const msg = `{"error":{"code":"station_not_found","message":"La estación 9 no existe."}}`
	goAPI, _ := servidor(t, http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		_, _ = io.WriteString(w, msg)
	}))
	resp, _ := http.Get(goAPI.URL + "/api/stations/9")
	got, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 404 || string(got) != msg {
		t.Fatalf("el 404 del backend se alteró: %d %s", resp.StatusCode, got)
	}
}

func TestSiElBackendNoEstaDevuelve502EnEspanolSinFiltrarLaDireccion(t *testing.T) {
	goAPI, py := servidor(t, http.NotFoundHandler())
	py.Close() // el backend se cae
	resp, err := http.Get(goAPI.URL + "/api/stations")
	if err != nil {
		t.Fatal(err)
	}
	b, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusBadGateway || !strings.Contains(string(b), `"bad_gateway"`) || !strings.Contains(string(b), "no está disponible") {
		t.Fatalf("502 inesperado: %d %s", resp.StatusCode, b)
	}
	if strings.Contains(string(b), "127.0.0.1") || strings.Contains(string(b), "dial") {
		t.Fatalf("el error no puede filtrar la dirección interna: %s", b)
	}
}

func TestUnCuerpoDemasiadoGrandeDa413(t *testing.T) {
	goAPI, _ := servidor(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.Copy(io.Discard, r.Body)
	}))
	resp, err := http.Post(goAPI.URL+"/api/import/rainfall", "text/csv", strings.NewReader(strings.Repeat("x", proxy.MaxBodyBytes+1)))
	if err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != http.StatusRequestEntityTooLarge {
		t.Fatalf("esperaba 413, llegó %d", resp.StatusCode)
	}
}

func TestSoloSeReenvianLasRutasDeApiYHealthLoResponderGo(t *testing.T) {
	llamadas := 0
	goAPI, _ := servidor(t, http.HandlerFunc(func(http.ResponseWriter, *http.Request) { llamadas++ }))
	for _, ruta := range []string{"/health", "/otra-cosa", "/admin"} {
		resp, _ := http.Get(goAPI.URL + ruta)
		_ = resp.Body.Close()
	}
	if llamadas != 0 {
		t.Fatalf("Go reenvió %d pedidos que no son de /api", llamadas)
	}
}

func TestUnaRutaPropiaDeGoGanaSobreElReenvio(t *testing.T) {
	py := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { _, _ = io.WriteString(w, "python") }))
	defer py.Close()
	target, _ := url.Parse(py.URL)
	propia := func(mux *http.ServeMux) {
		mux.HandleFunc("GET /api/stations", func(w http.ResponseWriter, _ *http.Request) { _, _ = io.WriteString(w, "go") })
	}
	cfg := config.Config{CutoffDate: "2026-10-31", BackendURL: target}
	goAPI := httptest.NewServer(httpapi.New(cfg, logger(), propia, httpapi.WithBackend(proxy.New(target, logger()))))
	defer goAPI.Close()
	for ruta, quien := range map[string]string{"/api/stations": "go", "/api/rainfall": "python"} {
		resp, _ := http.Get(goAPI.URL + ruta)
		b, _ := io.ReadAll(resp.Body)
		if string(b) != quien {
			t.Errorf("%s debía responder %s y respondió %s", ruta, quien, b)
		}
	}
}
