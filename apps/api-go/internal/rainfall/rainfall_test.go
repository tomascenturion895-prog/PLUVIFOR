package rainfall

import (
	"context"
	"errors"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

func d(s string) civil.Date {
	v, err := civil.Parse(s)
	if err != nil {
		panic(err)
	}
	return v
}

func mm(v float64) *float64 { return &v }

type fakeReader struct {
	st    *station.Station
	data  Data
	flags []Flag
	err   error
}

func (f fakeReader) Station(context.Context, int) (station.Station, bool, error) {
	if f.err != nil || f.st == nil {
		return station.Station{}, false, f.err
	}
	return *f.st, true, nil
}
func (f fakeReader) Days(context.Context, int, Category, civil.Date, civil.Date) (Data, error) {
	return f.data, f.err
}
func (f fakeReader) Flags(context.Context, int, civil.Date, civil.Date) ([]Flag, error) {
	return f.flags, f.err
}

func TestHuecoNoEsCeroMilimetros(t *testing.T) {
	// 1/ene con dato 0, 2/ene fila sin valor, 3/ene no existe en la fuente.
	cal := FillCalendar([]Day{
		{Date: d("2026-01-01"), State: Dato, MM: mm(0)},
		{Date: d("2026-01-02"), State: FilaSinValor},
	}, d("2026-01-01"), d("2026-01-03"))
	if len(cal) != 3 {
		t.Fatalf("días = %d, quería 3", len(cal))
	}
	if cal[0].MM == nil || *cal[0].MM != 0 {
		t.Fatal("un dato de 0 mm tiene que seguir siendo 0")
	}
	for _, day := range cal[1:] {
		if day.MM != nil {
			t.Fatalf("%s: un hueco no puede tener mm (tiene %v)", day.Date, *day.MM)
		}
	}
	if cal[1].State != FilaSinValor || cal[2].State != SinFila {
		t.Fatalf("estados = %s y %s", cal[1].State, cal[2].State)
	}
	s := Summarize(cal)
	if s.DaysWithData != 1 || s.DaysFilaSinValor != 1 || s.DaysSinFila != 1 {
		t.Fatalf("resumen = %+v", s)
	}
	if s.AccumulatedMM == nil || *s.AccumulatedMM != 0 {
		t.Fatal("con un día con dato de 0 mm el acumulado es 0, no nulo")
	}
}

func TestAcumuladoEsNuloSinNingunDiaConDato(t *testing.T) {
	s := Summarize(FillCalendar(nil, d("2026-01-01"), d("2026-01-05")))
	if s.AccumulatedMM != nil {
		t.Fatal("sin días con dato el acumulado debe ser nulo, no 0")
	}
	if s.DaysSinFila != 5 || s.Coverage != 0 {
		t.Fatalf("resumen = %+v", s)
	}
}

func TestRedondeoComoPython(t *testing.T) {
	s := Summarize([]Day{
		{Date: d("2026-01-01"), State: Dato, MM: mm(0.1)},
		{Date: d("2026-01-02"), State: Dato, MM: mm(0.2)},
	})
	// 0.1 + 0.2 da 0.30000000000000004 en binario: se informa 0.3, igual que Python.
	if *s.AccumulatedMM != 0.3 || s.Coverage != 1 {
		t.Fatalf("acumulado = %v, cobertura = %v", *s.AccumulatedMM, s.Coverage)
	}
	if got := Summarize(FillCalendar([]Day{{Date: d("2026-01-01"), State: Dato, MM: mm(1)}}, d("2026-01-01"), d("2026-01-03"))).Coverage; got != 0.3333 {
		t.Fatalf("cobertura = %v, quería 0.3333", got)
	}
}

func newService(r fakeReader) *Service { return NewService(r, d("2026-10-31")) }

func TestSerieCasoFeliz(t *testing.T) {
	st := station.Station{ID: 1, Name: "Estación"}
	svc := newService(fakeReader{st: &st, data: Data{Days: []Day{{Date: d("2026-01-02"), State: Dato, MM: mm(12.5)}}}})
	res, err := svc.Series(context.Background(), 1, d("2026-01-01"), d("2026-01-02"), Observado)
	if err != nil {
		t.Fatal(err)
	}
	if res.Clipped || len(res.Days) != 2 || res.Days[0].State != SinFila || *res.Summary.AccumulatedMM != 12.5 {
		t.Fatalf("resultado inesperado: %+v", res)
	}
	if len(res.Warnings) == 0 || res.Warnings[0].Code != "cobertura_baja" {
		t.Fatalf("con 50%% de cobertura se esperaba la advertencia de cobertura baja: %+v", res.Warnings)
	}
}

func TestSerieRecortaALaFechaDeCorte(t *testing.T) {
	st := station.Station{ID: 1}
	res, err := newService(fakeReader{st: &st}).Series(context.Background(), 1, d("2026-10-30"), d("2026-12-31"), Observado)
	if err != nil {
		t.Fatal(err)
	}
	if !res.Clipped || res.To.String() != "2026-10-31" || len(res.Days) != 2 {
		t.Fatalf("no recortó al corte: hasta=%s recortado=%v días=%d", res.To, res.Clipped, len(res.Days))
	}
}

func TestSerieEntradasInvalidas(t *testing.T) {
	st := station.Station{ID: 1}
	svc := newService(fakeReader{st: &st})
	casos := []struct {
		nombre, desde, hasta, codigo string
		estado                       int
	}{
		{"desde posterior a hasta", "2026-02-01", "2026-01-01", "invalid_range", 422},
		{"posterior al corte", "2026-11-01", "2026-11-30", "after_cutoff", 422},
		{"período enorme", "2000-01-01", "2026-10-31", "range_too_large", 422},
	}
	for _, c := range casos {
		_, err := svc.Series(context.Background(), 1, d(c.desde), d(c.hasta), Observado)
		var e *Error
		if !errors.As(err, &e) || e.Code != c.codigo || e.Status != c.estado {
			t.Errorf("%s: error = %v", c.nombre, err)
		}
	}
	// El máximo exacto (3.660 días) sí se acepta.
	if _, err := svc.Series(context.Background(), 1, d("2016-10-31"), d("2026-10-31"), Observado); err != nil {
		t.Errorf("3.653 días debían aceptarse: %v", err)
	}
}

func TestEstacionInexistenteEs404(t *testing.T) {
	_, err := newService(fakeReader{}).Series(context.Background(), 9, d("2026-01-01"), d("2026-01-02"), Observado)
	var e *Error
	if !errors.As(err, &e) || e.Status != 404 || e.Code != "station_not_found" {
		t.Fatalf("error = %v", err)
	}
}

func TestErrorDeLaBaseSePropaga(t *testing.T) {
	boom := errors.New("base caída")
	_, err := newService(fakeReader{err: boom}).Series(context.Background(), 1, d("2026-01-01"), d("2026-01-02"), Observado)
	if !errors.Is(err, boom) {
		t.Fatalf("error = %v", err)
	}
}

func TestBanderasPorDia(t *testing.T) {
	ws := warnings([]Flag{{Code: "ceros_prolongados", Severity: "alerta", Start: d("2026-01-02"), End: d("2026-01-04")}}, Summary{Coverage: 1}, 3)
	if len(ws) != 2 || ws[1].Code != "dato_sin_validar" {
		t.Fatalf("advertencias = %+v", ws)
	}
	for day, want := range map[string]int{"2026-01-01": 0, "2026-01-02": 1, "2026-01-04": 1, "2026-01-05": 0} {
		if got := len(FlagsOnDay(ws, d(day))); got != want {
			t.Errorf("%s: %d banderas, quería %d", day, got, want)
		}
	}
}

func TestParseCategory(t *testing.T) {
	for _, ok := range []string{"observado", "referencia", "estimado"} {
		if _, valid := ParseCategory(ok); !valid {
			t.Errorf("%q debía ser válida", ok)
		}
	}
	for _, bad := range []string{"", "OBSERVADO", "simulado", "x"} {
		if _, valid := ParseCategory(bad); valid {
			t.Errorf("%q no debía ser válida", bad)
		}
	}
}
