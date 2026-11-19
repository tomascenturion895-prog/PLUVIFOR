package events

import (
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
)

var start = func() civil.Date {
	d, err := civil.Parse("2020-01-01")
	if err != nil {
		panic(err)
	}
	return d
}()

// serie arma días consecutivos: un número es un día con dato; "s" es sin_fila; "v" es fila_sin_valor.
func serie(items ...any) []rainfall.Day {
	out := make([]rainfall.Day, len(items))
	for i, it := range items {
		d := rainfall.Day{Date: start.AddDays(i)}
		switch v := it.(type) {
		case float64:
			mm := v
			d.State, d.MM = rainfall.Dato, &mm
		case int:
			mm := float64(v)
			d.State, d.MM = rainfall.Dato, &mm
		case string:
			if v == "v" {
				d.State = rainfall.FilaSinValor
			} else {
				d.State = rainfall.SinFila
			}
		}
		out[i] = d
	}
	return out
}

func TestUmbralesSonInclusivosYUnDiaDeCienEstaEnLasDosListas(t *testing.T) {
	a := Analyze(serie(49.9, 50, 99.9, 100, 0), nil, 1)
	if len(a.Ge50) != 3 || len(a.Ge100) != 1 {
		t.Fatalf("≥50: %d (esperado 3), ≥100: %d (esperado 1)", len(a.Ge50), len(a.Ge100))
	}
	if a.Ge100[0].MM != 100 || a.Ge50[2].MM != 100 {
		t.Errorf("el día de 100 mm debe figurar en las dos listas: %+v %+v", a.Ge50, a.Ge100)
	}
}

func TestUnHuecoNoEsUnEventoNiUnDiaSeco(t *testing.T) {
	a := Analyze(serie("s", "v", 0, "s", "v"), nil, 1)
	if len(a.Ge50) != 0 || len(a.Ge100) != 0 {
		t.Errorf("un hueco no es un evento: %+v", a)
	}
	if len(a.DryStreaks) != 1 || a.DryStreaks[0].Days != 1 {
		t.Errorf("solo el día con dato y 0 mm es seco: %+v", a.DryStreaks)
	}
}

func TestUnHuecoCortaLaRachaSecaYNoLaExtiende(t *testing.T) {
	a := Analyze(serie(0, 0, 0, "s", 0, 0), nil, 1)
	if len(a.DryStreaks) != 2 || a.DryStreaks[0].Days != 3 || a.DryStreaks[1].Days != 2 {
		t.Fatalf("esperadas 2 rachas de 3 y 2 días: %+v", a.DryStreaks)
	}
	if a.Longest == nil || a.Longest.Days != 3 {
		t.Errorf("la más larga es de 3 días: %+v", a.Longest)
	}
}

func TestLaLluviaCortaLaRacha(t *testing.T) {
	a := Analyze(serie(0, 0, 0.2, 0, 0, 0, 0), nil, 1)
	if len(a.DryStreaks) != 2 || a.DryStreaks[0].Days != 2 || a.DryStreaks[1].Days != 4 {
		t.Fatalf("%+v", a.DryStreaks)
	}
	if a.DryStreaks[1].Start.String() != "2020-01-04" || a.DryStreaks[1].End.String() != "2020-01-07" {
		t.Errorf("fechas de la racha: %+v", a.DryStreaks[1])
	}
}

func TestMinimoDeDiasFiltraLaListaPeroNoLaMasLarga(t *testing.T) {
	a := Analyze(serie(0, 0, 5, 0), nil, 3)
	if len(a.DryStreaks) != 0 {
		t.Errorf("ninguna racha llega a 3 días: %+v", a.DryStreaks)
	}
	if a.Longest == nil || a.Longest.Days != 2 {
		t.Errorf("la más larga igual se informa: %+v", a.Longest)
	}
}

func TestSinNingunDiaSecoNoHayRachaMasLarga(t *testing.T) {
	a := Analyze(serie(1, "s", 2), nil, 1)
	if a.Longest != nil || len(a.DryStreaks) != 0 {
		t.Errorf("no hay racha: %+v", a)
	}
	b := Analyze(nil, nil, 1)
	if b.Ge50 == nil || b.Ge100 == nil || b.DryStreaks == nil {
		t.Error("las listas vacías deben ser [] y no null")
	}
}

func TestEmpateDeRachasDevuelveLaPrimera(t *testing.T) {
	a := Analyze(serie(0, 0, 1, 0, 0), nil, 1)
	if a.Longest.Start.String() != "2020-01-01" {
		t.Errorf("%+v", a.Longest)
	}
}

func TestUnaRachaSobreCerosProlongadosSeMarcaYNoSeDaPorBuena(t *testing.T) {
	ini, fin := start, start.AddDays(2)
	w := []rainfall.Warning{{Code: ZeroRunCode, StartDate: &ini, EndDate: &fin}}
	a := Analyze(serie(0, 0, 0, 1, 0, 0), w, 1)
	if !a.DryStreaks[0].ZeroRunWarning {
		t.Errorf("la primera racha toca la advertencia: %+v", a.DryStreaks[0])
	}
	if a.DryStreaks[1].ZeroRunWarning {
		t.Errorf("la segunda no la toca: %+v", a.DryStreaks[1])
	}
}
