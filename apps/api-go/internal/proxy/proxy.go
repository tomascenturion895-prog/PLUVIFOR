// Package proxy reenvía las rutas de datos (/api/*) al backend en Python con el mismo contrato.
//
// Es el camino «Go como puerta de entrada» mientras las rutas no se portan una por una: las rutas
// propias de Go ganan sobre este reenvío, y las que Go aún no tiene siguen respondiendo desde Python.
// No cambia ninguna respuesta: estado, cuerpo y encabezados del backend pasan tal cual.
package proxy

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/secheaders"
)

// MaxBodyBytes limita el cuerpo de un pedido (el backend limita la importación a 5 MiB).
const MaxBodyBytes = 6 << 20

// New arma el reenvío al backend. El detalle de un fallo de red va solo al registro del servidor.
func New(target *url.URL, logger *slog.Logger) http.Handler {
	rp := &httputil.ReverseProxy{
		Rewrite: func(r *httputil.ProxyRequest) {
			r.SetURL(target)
			r.SetXForwarded()
		},
		Transport: &http.Transport{
			DialContext:           (&net.Dialer{Timeout: 3 * time.Second}).DialContext,
			ResponseHeaderTimeout: 30 * time.Second,
			MaxIdleConnsPerHost:   16,
			IdleConnTimeout:       60 * time.Second,
		},
		ErrorHandler: func(w http.ResponseWriter, r *http.Request, err error) {
			if errors.Is(err, context.Canceled) {
				return // quien consultaba cortó la conexión: no hay a quién responder ni falla que registrar
			}
			logger.Error("el backend no respondió", "ruta", r.URL.Path, "error", err)
			var tooBig *http.MaxBytesError
			switch {
			case errors.As(err, &tooBig):
				apierror.Status(w, http.StatusRequestEntityTooLarge)
			case isTimeout(err):
				apierror.Status(w, http.StatusGatewayTimeout)
			default:
				apierror.Status(w, http.StatusBadGateway)
			}
		},
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Los encabezados de seguridad del backend pasan sin duplicarse.
		secheaders.Strip(w.Header())
		r.Body = http.MaxBytesReader(w, r.Body, MaxBodyBytes)
		rp.ServeHTTP(w, r)
	})
}

func isTimeout(err error) bool {
	var ne net.Error
	return errors.As(err, &ne) && ne.Timeout()
}
