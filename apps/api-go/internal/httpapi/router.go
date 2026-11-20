// Package httpapi arma el servidor HTTP: rutas, errores y protección ante fallos.
package httpapi

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"strconv"
	"strings"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/ratelimit"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/secheaders"
)

// Version de la API.
const Version = "0.1.0"

// Option agrega rutas al servidor (las tareas siguientes se apoyan en esto).
type Option func(*http.ServeMux)

// WithBackend reenvía /api/* al handler indicado (el proxy al backend en Python). Las rutas propias
// de Go se registran con otra Option y tienen prioridad sobre este reenvío: la más específica gana.
func WithBackend(h http.Handler) Option {
	return func(mux *http.ServeMux) { mux.Handle("/api/", h) }
}

// New devuelve el manejador con las rutas, el 404/405 en el formato único y la recuperación de fallos.
func New(cfg config.Config, logger *slog.Logger, opts ...Option) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", health(cfg))
	for _, opt := range opts {
		opt(mux)
	}
	limiter := ratelimit.New(nil)
	return recoverer(logger, securityHeaders(rateLimited(limiter, cfg, notFoundAs404JSON(mux))))
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
		// Un 404/405 que ya viene en JSON (por ejemplo, el del backend en Python) se respeta tal cual.
		if !strings.HasPrefix(e.Header().Get("Content-Type"), "application/json") {
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
		secheaders.Apply(w.Header())
		next.ServeHTTP(w, r)
	})
}

// rateLimited limita los pedidos por dirección (la que ve el servidor: no se confía en encabezados
// que quien consulta puede falsear). /health queda afuera y la importación tiene su propio máximo.
func rateLimited(l *ratelimit.Limiter, cfg config.Config, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			next.ServeHTTP(w, r)
			return
		}
		limit, bucket := cfg.RateLimitPerMinute, ""
		if strings.HasPrefix(r.URL.Path, "/api/import") {
			limit, bucket = cfg.RateLimitImportPerMinute, "import|"
		}
		host, _, err := net.SplitHostPort(r.RemoteAddr)
		if err != nil {
			host = r.RemoteAddr
		}
		if ok, wait := l.Allow(bucket+host, limit); !ok {
			w.Header().Set("Retry-After", strconv.Itoa(wait))
			apierror.Write(w, http.StatusTooManyRequests, "too_many_requests",
				fmt.Sprintf("Hiciste demasiados pedidos seguidos. Esperá %d segundos e intentá de nuevo.", wait))
			return
		}
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
