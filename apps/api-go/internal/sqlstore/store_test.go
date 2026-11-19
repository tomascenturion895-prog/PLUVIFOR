package sqlstore

import (
	"errors"
	"testing"
	"time"
)

func TestRebindParaPostgreSQL(t *testing.T) {
	s := &Store{dialect: PostgreSQL}
	if got := s.rebind("a = ? AND b BETWEEN ? AND ?"); got != "a = $1 AND b BETWEEN $2 AND $3" {
		t.Fatalf("rebind = %q", got)
	}
	if got := (&Store{dialect: SQLite}).rebind("a = ?"); got != "a = ?" {
		t.Fatalf("SQLite no debe cambiar los parámetros: %q", got)
	}
}

func TestToDateAceptaTextoYHora(t *testing.T) {
	for _, v := range []any{"2026-10-31", "2026-10-31 00:00:00", []byte("2026-10-31"), time.Date(2026, 10, 31, 0, 0, 0, 0, time.UTC)} {
		d, err := toDate(v)
		if err != nil || d.String() != "2026-10-31" {
			t.Errorf("toDate(%v) = %v, %v", v, d, err)
		}
	}
	for _, v := range []any{"", "no es fecha", 42, nil} {
		if _, err := toDate(v); err == nil {
			t.Errorf("toDate(%v) debía fallar", v)
		}
	}
}

func TestStationWhereArmaParametrosSinInterpolar(t *testing.T) {
	where, args := stationWhere(stationFiltersMalicioso())
	if len(args) != 4 || containsAny(where, "'; DROP", "x'") {
		t.Fatalf("where=%q args=%v: el valor del usuario debe ir solo como parámetro", where, args)
	}
}

func TestSinDriverAbrirDevuelveErrorClaro(t *testing.T) {
	if DriverName != "" {
		t.Skip("este binario trae driver")
	}
	if _, err := OpenSQLite("/tmp/no-importa.db"); !errors.Is(err, ErrNoDriver) {
		t.Fatalf("err = %v", err)
	}
}
