package ratelimit

import (
	"testing"
	"time"
)

type clock struct{ t time.Time }

func (c *clock) now() time.Time { return c.t }

func TestPermiteHastaElMaximoYBloqueaElSiguiente(t *testing.T) {
	c := &clock{t: time.Unix(1000, 0)}
	l := New(c.now)
	for i := 0; i < 3; i++ {
		if ok, _ := l.Allow("a", 3); !ok {
			t.Fatalf("el pedido %d debía pasar", i+1)
		}
	}
	ok, wait := l.Allow("a", 3)
	if ok || wait != 60 {
		t.Fatalf("ok=%v wait=%d: el cuarto pedido debía bloquearse con 60 s de espera", ok, wait)
	}
}

func TestLaVentanaSeLibera(t *testing.T) {
	c := &clock{t: time.Unix(1000, 0)}
	l := New(c.now)
	l.Allow("a", 1)
	if ok, _ := l.Allow("a", 1); ok {
		t.Fatal("debía bloquearse")
	}
	c.t = c.t.Add(61 * time.Second)
	if ok, _ := l.Allow("a", 1); !ok {
		t.Fatal("pasado el minuto debía volver a permitir")
	}
}

func TestClientesIndependientesYLimiteCeroDesactiva(t *testing.T) {
	l := New(nil)
	l.Allow("a", 1)
	if ok, _ := l.Allow("b", 1); !ok {
		t.Fatal("otro cliente no debe verse afectado")
	}
	for i := 0; i < 1000; i++ {
		if ok, _ := l.Allow("c", 0); !ok {
			t.Fatal("con límite 0 nunca se bloquea")
		}
	}
}
