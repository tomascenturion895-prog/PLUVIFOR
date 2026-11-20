package secheaders

import (
	"net/http"
	"testing"
)

func TestApplyYStrip(t *testing.T) {
	h := http.Header{}
	Apply(h)
	for _, k := range []string{"X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Content-Security-Policy", "Cross-Origin-Resource-Policy", "Permissions-Policy"} {
		if h.Get(k) == "" {
			t.Errorf("falta %s", k)
		}
	}
	Strip(h)
	if len(h) != 0 {
		t.Fatalf("Strip debía dejar los encabezados vacíos: %v", h)
	}
}
