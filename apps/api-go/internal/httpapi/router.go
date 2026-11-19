// Package httpapi arma el servidor HTTP: rutas, errores y protección ante fallos.
package httpapi

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
)

// Version de la API.
const Version = "0.1.0"

// Option agrega rutas al servidor (las tareas siguientes se apoyan en esto).
type Option func(*http.ServeMux)

// New devuelve el manejador con las rutas, el 404/405 en el formato único y la recuperación de fallos.
func New(cfg config.Config, logger *slog.Logger, opts ...Option) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", health(cfg))
	for _, opt := range opts {
		opt(mux)
	}
	return recoverer(logger, securityHeaders(notFoundAs404JSON(mux)))
}

type healthResponse struct {
	Status         string `json:"status"`
	Version        string `json:"version"`
	Env            string `json:"env"`
	DataCutoffDate string `json:"data_cutoff_date"`
}

func health(cfg config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(healthResponse{
			Status: "ok", Version: Version, Env: cfg.Env, DataCutoffDate: cfg.CutoffDate,
		})
	}
}

// notFoundAs404JSON cambia el 404 y el 405 de texto plano del mux por el error estándar.
func notFoundAs404JSON(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		next.ServeHTTP(&errorRewriter{ResponseWriter: w}, r)
	})
}

// errorRewriter intercepta los 404 y 405 que genera el mux (cuerpo de texto) y escribe el JSON.
type errorRewriter struct {
	http.ResponseWriter
	rewritten bool
}

func (e *errorRewriter) WriteHeader(status int) {
	if status == http.StatusNotFound || status == http.StatusMethodNotAllowed {
		if e.Header().Get("Content-Type") != "application/json; charset=utf-8" {
			e.rewritten = true
			e.ResponseWriter.Header().Del("Content-Length")
			apierror.Status(e.ResponseWriter, status)
			return
		}
	}
	e.ResponseWriter.WriteHeader(status)
}

func (e *errorRewriter) Write(b []byte) (int, error) {
	if e.rewritten {
		return len(b), nil // se descarta el texto plano del mux
	}
	return e.ResponseWriter.Write(b)
}

func securityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Cache-Control", "no-store")
		next.ServeHTTP(w, r)
	})
}

// recoverer convierte cualquier pánico en un 500 en español, sin detalles internos.
// El detalle va solo al registro del servidor.
func recoverer(logger *slog.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				logger.Error("fallo no controlado", "ruta", r.URL.Path, "detalle", rec)
				apierror.Status(w, http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}
