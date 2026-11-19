package httpapi

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"reflect"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
)

type parityCase struct {
	Path   string          `json:"path"`
	Status int             `json:"status"`
	Body   json.RawMessage `json:"body"`
}

func newParityServer(t testing.TB, store *memStore) http.Handler {
	t.Helper()
	cfg := config.Config{Env: "test", CutoffDate: "2026-10-31"}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	return New(cfg, logger,
		WithStations(store, logger),
		WithRainfall(store, mustDate(t, "2026-10-31"), logger),
	)
}

// TestParidadConPython compara cada consulta con lo que respondió la API de Python con los mismos
// datos. El JSON se compara por valor (0 y 0.0 son el mismo número), no por texto.
func TestParidadConPython(t *testing.T) {
	runParity(t, newParityServer(t, loadMemStore(t)))
}

func runParity(t *testing.T, srv http.Handler) {
	t.Helper()
	raw, err := os.ReadFile("../../testdata/parity/cases.json")
	if err != nil {
		t.Fatalf("falta testdata/parity/cases.json (se genera con generate.py): %v", err)
	}
	var cases []parityCase
	if err := json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	if len(cases) < 40 {
		t.Fatalf("se esperaban al menos 40 casos, hay %d", len(cases))
	}
	for _, c := range cases {
		t.Run(c.Path, func(t *testing.T) {
			rec := httptest.NewRecorder()
			srv.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, c.Path, nil))
			if rec.Code != c.Status {
				t.Fatalf("estado = %d, Python devolvió %d: %s", rec.Code, c.Status, rec.Body.String())
			}
			var got, want any
			if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
				t.Fatalf("la respuesta de Go no es JSON: %v", err)
			}
			if err := json.Unmarshal(c.Body, &want); err != nil {
				t.Fatal(err)
			}
			if c.Status == http.StatusUnprocessableEntity && isDateFormatError(want) {
				// Los textos de fecha mal formada de pydantic varían según el defecto; se exige
				// el mismo código y el mismo parámetro, no la misma frase en inglés.
				got, want = dropMessages(got), dropMessages(want)
			}
			if !reflect.DeepEqual(got, want) {
				g, _ := json.MarshalIndent(got, "", " ")
				w, _ := json.MarshalIndent(want, "", " ")
				t.Fatalf("la respuesta difiere de Python.\nGo:\n%.1500s\nPython:\n%.1500s", g, w)
			}
		})
	}
}

func isDateFormatError(v any) bool {
	m, _ := v.(map[string]any)
	e, _ := m["error"].(map[string]any)
	ds, _ := e["details"].([]any)
	for _, d := range ds {
		dm, _ := d.(map[string]any)
		if msg, _ := dm["message"].(string); len(msg) > 33 && msg[:33] == "Input should be a valid date or d" {
			return true
		}
	}
	return false
}

func dropMessages(v any) any {
	m, _ := v.(map[string]any)
	e, _ := m["error"].(map[string]any)
	ds, _ := e["details"].([]any)
	for _, d := range ds {
		delete(d.(map[string]any), "message")
	}
	return v
}

func newParityLogger() *slog.Logger { return slog.New(slog.NewTextHandler(io.Discard, nil)) }

func testConfig() config.Config { return config.Config{Env: "test", CutoffDate: "2026-10-31"} }
