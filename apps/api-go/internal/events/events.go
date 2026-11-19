// Package events cuenta, de forma descriptiva, los días de lluvia intensa y las rachas secas.
// No predice nada y no es una alerta de riesgo.
//
// Regla central: un hueco no es 0 mm. Un día sin dato no es un día seco: no suma a una racha seca
// y la corta. Un día con dato y 0 mm sí es seco.
package events

import (
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
)

// Umbrales de lluvia intensa, en milímetros por día (AGENTS.md).
const (
	Level50  = 50.0
	Level100 = 100.0
)

// ZeroRunCode es el código de la advertencia de racha de ceros de 60 días o más.
const ZeroRunCode = "ceros_prolongados"

// Event es un día con dato que alcanza un umbral.
type Event struct {
	Date civil.Date `json:"obs_date"`
	MM   float64    `json:"mm"`
}

// DryStreak son días seguidos con dato y 0 mm.
type DryStreak struct {
	Start civil.Date `json:"start_date"`
	End   civil.Date `json:"end_date"`
	Days  int        `json:"days"`
	// ZeroRunWarning es true si la racha toca un período con la advertencia de ceros prolongados:
	// puede ser un sensor sin registrar, no ausencia de lluvia. No se da por buena.
	ZeroRunWarning bool `json:"zero_run_warning"`
}

// Analysis es el resultado descriptivo de una serie.
type Analysis struct {
	// Ge50 incluye los días de 100 mm o más: un día de 100 mm figura en las dos listas.
	Ge50  []Event
	Ge100 []Event
	// DryStreaks son las rachas de al menos minDry días.
	DryStreaks []DryStreak
	// Longest es la racha más larga del período (la primera si hay empate), sin importar minDry.
	Longest *DryStreak
}

// Analyze recorre una serie diaria ya completada (un valor por día, con los huecos como tales).
func Analyze(days []rainfall.Day, warnings []rainfall.Warning, minDry int) Analysis {
	a := Analysis{Ge50: []Event{}, Ge100: []Event{}, DryStreaks: []DryStreak{}}
	var run *DryStreak
	flush := func() {
		if run == nil {
			return
		}
		run.ZeroRunWarning = touchesWarning(*run, warnings)
		if a.Longest == nil || run.Days > a.Longest.Days {
			l := *run
			a.Longest = &l
		}
		if run.Days >= minDry {
			a.DryStreaks = append(a.DryStreaks, *run)
		}
		run = nil
	}
	for _, d := range days {
		if d.State != rainfall.Dato || d.MM == nil {
			flush() // un hueco corta la racha y no cuenta como seco
			continue
		}
		mm := *d.MM
		if mm >= Level50 {
			a.Ge50 = append(a.Ge50, Event{d.Date, mm})
		}
		if mm >= Level100 {
			a.Ge100 = append(a.Ge100, Event{d.Date, mm})
		}
		if mm != 0 {
			flush()
			continue
		}
		if run == nil {
			run = &DryStreak{Start: d.Date}
		}
		run.End = d.Date
		run.Days++
	}
	flush()
	return a
}

func touchesWarning(s DryStreak, ws []rainfall.Warning) bool {
	for _, w := range ws {
		if w.Code != ZeroRunCode || w.StartDate == nil || w.EndDate == nil {
			continue
		}
		if !s.End.Before(*w.StartDate) && !s.Start.After(*w.EndDate) {
			return true
		}
	}
	return false
}
