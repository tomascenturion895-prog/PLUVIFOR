// Package secheaders define los encabezados de seguridad de la API. Son los mismos que pone la API
// de Python (apps/backend/app/security.py): la respuesta de una ruta propia de Go y la de una ruta
// reenviada llevan lo mismo.
package secheaders

import "net/http"

var values = map[string]string{
	"X-Content-Type-Options":       "nosniff",
	"X-Frame-Options":              "DENY",
	"Referrer-Policy":              "no-referrer",
	"Permissions-Policy":           "geolocation=(), camera=(), microphone=()",
	"Cross-Origin-Resource-Policy": "same-site",
	"Content-Security-Policy":      "default-src 'none'; frame-ancestors 'none'",
	"Cache-Control":                "no-store",
}

// Apply pone los encabezados de seguridad en la respuesta.
func Apply(h http.Header) {
	for k, v := range values {
		h.Set(k, v)
	}
}

// Strip los quita para que el backend en Python ponga los suyos sin duplicarlos.
func Strip(h http.Header) {
	for k := range values {
		h.Del(k)
	}
}
