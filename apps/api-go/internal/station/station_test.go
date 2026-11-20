package station

import (
	"context"
	"errors"
	"testing"
)

type fakeReader struct {
	items []Station
	err   error
}

func (f fakeReader) Search(context.Context, Filters, Page) ([]Station, int, error) {
	return f.items, len(f.items), f.err
}

func (f fakeReader) Get(_ context.Context, id int) (Station, bool, error) {
	for _, s := range f.items {
		if s.ID == id {
			return s, true, f.err
		}
	}
	return Station{}, false, f.err
}

func TestBuscarDevuelveListaNoNula(t *testing.T) {
	items, total, err := NewService(fakeReader{}).Search(context.Background(), Filters{}, Page{Limit: 10})
	if err != nil || total != 0 || items == nil {
		t.Fatalf("items=%v total=%d err=%v: la lista vacía debe ser [] y no null", items, total, err)
	}
}

func TestGetExistenteYFaltante(t *testing.T) {
	svc := NewService(fakeReader{items: []Station{{ID: 7, Name: "Siete"}}})
	if st, err := svc.Get(context.Background(), 7); err != nil || st.Name != "Siete" {
		t.Fatalf("st=%+v err=%v", st, err)
	}
	if _, err := svc.Get(context.Background(), 8); !errors.Is(err, ErrNotFound) {
		t.Fatalf("err = %v, quería ErrNotFound", err)
	}
}

func TestErrorDeLaBaseSePropaga(t *testing.T) {
	boom := errors.New("base caída")
	svc := NewService(fakeReader{err: boom})
	if _, _, err := svc.Search(context.Background(), Filters{}, Page{}); !errors.Is(err, boom) {
		t.Fatalf("Search: %v", err)
	}
	if _, err := svc.Get(context.Background(), 1); !errors.Is(err, boom) {
		t.Fatalf("Get: %v", err)
	}
}
