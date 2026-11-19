// Package apierror define el formato único de errores: {"error": {"code", "message"}}.
// Es el mismo que usa la API de Python. Nunca se devuelve el detalle interno de un fallo
// ni el valor que mandó quien consulta.
package apierror

import (
	"encoding/json"
	"net/http"
)

type body struct {
	Error detail `json:"error"`
}

type detail struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// Mensajes en español para los errores sin detalle propio.
var defaults = map[int]struct{ code, message string }{
	http.StatusBadRequest:            {"bad_request", "La solicitud no es válida."},
	http.StatusNotFound:              {"not_found", "No se encontró lo que pediste."},
	http.StatusMethodNotAllowed:      {"method_not_allowed", "Ese método no está permitido en esta ruta."},
	http.StatusRequestEntityTooLarge: {"payload_too_large", "El pedido es demasiado grande."},
	http.StatusBadGateway:            {"bad_gateway", "El servicio de datos no está disponible. Probá de nuevo en un momento."},
	http.StatusGatewayTimeout:        {"gateway_timeout", "El servicio de datos tardó demasiado en responder."},
	http.StatusTooManyRequests:       {"too_many_requests", "Hiciste demasiados pedidos. Probá de nuevo en un minuto."},
	http.StatusInternalServerError:   {"internal_error", "Ocurrió un error interno."},
}

// Write responde con el código HTTP indicado. Si code o message vienen vacíos usa los de la tabla.
func Write(w http.ResponseWriter, status int, code, message string) {
	d, ok := defaults[status]
	if !ok {
		d = defaults[http.StatusInternalServerError]
	}
	if code == "" {
		code = d.code
	}
	if message == "" {
		message = d.message
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body{Error: detail{Code: code, Message: message}})
}

// Status escribe el error estándar de un código HTTP.
func Status(w http.ResponseWriter, status int) { Write(w, status, "", "") }
