// Package ratelimit limita los pedidos por cliente en una ventana deslizante de un minuto, igual
// que la API de Python. El estado vive en la memoria del proceso: alcanza para un prototipo con un
// solo servidor; con varios habría que moverlo a un almacén compartido o al balanceador.
package ratelimit

import (
	"math"
	"sync"
	"time"
)

// Window es el largo de la ventana.
const Window = time.Minute

const pruneAbove = 10_000

// Limiter cuenta pedidos por clave. Es seguro para uso concurrente.
type Limiter struct {
	mu   sync.Mutex
	now  func() time.Time
	hits map[string][]time.Time
}

// New arma un limitador. El reloj es inyectable para probar sin esperar.
func New(now func() time.Time) *Limiter {
	if now == nil {
		now = time.Now
	}
	return &Limiter{now: now, hits: map[string][]time.Time{}}
}

// Allow dice si la clave puede hacer un pedido más con el máximo indicado. Un máximo de 0 o menos
// desactiva el límite. Si no puede, devuelve los segundos que faltan para reintentar.
func (l *Limiter) Allow(key string, limit int) (ok bool, retryAfter int) {
	if limit <= 0 {
		return true, 0
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	now := l.now()
	if len(l.hits) > pruneAbove {
		l.prune(now)
	}
	w := l.hits[key]
	for len(w) > 0 && now.Sub(w[0]) >= Window {
		w = w[1:]
	}
	if len(w) >= limit {
		l.hits[key] = w
		wait := int(math.Ceil((Window - now.Sub(w[0])).Seconds()))
		return false, max(1, wait)
	}
	l.hits[key] = append(w, now)
	return true, 0
}

func (l *Limiter) prune(now time.Time) {
	for k, w := range l.hits {
		if len(w) == 0 || now.Sub(w[len(w)-1]) >= Window {
			delete(l.hits, k)
		}
	}
}
