package httpapi

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
)

func nuevo(opts ...Option) http.Handler {
	cfg := config.Config{Env: "test", Port: "0", CutoffDate: "2026-10-31", Database: config.Database{Engine: "sqlite"}}
	return New(cfg, slog.New(slog.NewTextHandler(io.Discard, nil)), opts...)
}

func pedir(h http.Handler, method, path string) *httptest.ResponseRecorder {
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(method, path, nil))
	return rec
}

type errorBody struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

func TestHealthResponde(t *testing.T) {
	rec := pedir(nuevo(), http.MethodGet, "/health")
	if rec.Code != http.StatusOK {
		t.Fatalf("esperaba 200, llegó %d", rec.Code)
	}
	var got map[string]string
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatal(err)
	}
	if got["status"] != "ok" || got["version"] != Version || got["data_cutoff_date"] != "2026-10-31" {
		t.Fatalf("respuesta inesperada: %v", got)
	}
	if strings.Contains(rec.Body.String(), "sqlite") {
		t.Fatal("/health no debe mostrar datos de la base")
	}
}

func TestRutaInexistenteDaErrorEnEspanol(t *testing.T) {
	rec := pedir(nuevo(), http.MethodGet, "/no-existe")
	var e errorBody
	_ = json.Unmarshal(rec.Body.Bytes(), &e)
	if rec.Code != http.StatusNotFound || e.Error.Code != "not_found" || e.Error.Message != "No se encontró lo que pediste." {
		t.Fatalf("404 inesperado: %d %s", rec.Code, rec.Body.String())
	}
}

func TestMetodoNoPermitidoDaErrorEnEspanol(t *testing.T) {
	rec := pedir(nuevo(), http.MethodPost, "/health")
	var e errorBody
	_ = json.Unmarshal(rec.Body.Bytes(), &e)
	if rec.Code != http.StatusMethodNotAllowed || e.Error.Code != "method_not_allowed" {
		t.Fatalf("405 inesperado: %d %s", rec.Code, rec.Body.String())
	}
	if !strings.HasPrefix(rec.Header().Get("Content-Type"), "application/json") {
		t.Fatal("el error debe ser JSON")
	}
}

func TestUnFalloForzadoNoFiltraDetallesInternos(t *testing.T) {
	boom := func(mux *http.ServeMux) {
		mux.HandleFunc("GET /boom", func(http.ResponseWriter, *http.Request) {
			panic("conexión a postgres://usuario:SECRETO@host falló")
		})
	}
	rec := pedir(nuevo(boom), http.MethodGet, "/boom")
	var e errorBody
	_ = json.Unmarshal(rec.Body.Bytes(), &e)
	if rec.Code != http.StatusInternalServerError || e.Error.Code != "internal_error" || e.Error.Message != "Ocurrió un error interno." {
		t.Fatalf("500 inesperado: %d %s", rec.Code, rec.Body.String())
	}
	if strings.Contains(rec.Body.String(), "SECRETO") || strings.Contains(rec.Body.String(), "postgres") {
		t.Fatal("el 500 no puede filtrar el detalle del fallo")
	}
}

func TestEncabezadosDeSeguridad(t *testing.T) {
	rec := pedir(nuevo(), http.MethodGet, "/health")
	if rec.Header().Get("X-Content-Type-Options") != "nosniff" || rec.Header().Get("Cache-Control") != "no-store" {
		t.Fatalf("faltan encabezados: %v", rec.Header())
	}
}
