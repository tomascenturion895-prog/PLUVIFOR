// Package rainfall arma la serie diaria de una estación con su cobertura y sus advertencias.
// Regla central: un hueco no es 0 mm. Un día sin dato tiene mm nulo y un estado que dice por qué.
package rainfall

import (
	"context"
	"fmt"
	"strconv"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// MaxDays es el período máximo de una consulta (diez años).
const MaxDays = 3660

// LowCoverageThreshold es la cobertura bajo la cual se advierte. Valor provisional, igual que en Python.
const LowCoverageThreshold = 0.8

// State es el estado de un día. Solo Dato lleva milímetros.
type State string

const (
	Dato         State = "dato"
	FilaSinValor State = "fila_sin_valor" // el día existe en la fuente pero sin valor
	SinFila      State = "sin_fila"       // el día no existe en la fuente
)

// Category: observado, referencia y estimado nunca se suman ni se promedian entre sí.
type Category string

const (
	Observado  Category = "observado"
	Referencia Category = "referencia"
	Estimado   Category = "estimado"
)

// ParseCategory valida una categoría.
func ParseCategory(s string) (Category, bool) {
	switch c := Category(s); c {
	case Observado, Referencia, Estimado:
		return c, true
	}
	return "", false
}

// Severity de una advertencia: descriptiva, no es una alerta de riesgo.
type Severity string

// Day es un día de la serie.
type Day struct {
	Date  civil.Date
	State State
	MM    *float64 // nil = sin dato; nunca 0
}

// Data es lo que devuelve la base para un período: solo los días que existen.
type Data struct {
	Days        []Day
	Unvalidated int // días con dato que no pasaron una validación externa
}

// Flag es una bandera de calidad guardada (por ejemplo, ceros prolongados).
type Flag struct {
	Code     string
	Severity Severity
	Start    civil.Date
	End      civil.Date
}

// Warning es una advertencia que acompaña a la serie.
type Warning struct {
	Code      string      `json:"code"`
	Message   string      `json:"message"`
	Severity  Severity    `json:"severity"`
	StartDate *civil.Date `json:"start_date"`
	EndDate   *civil.Date `json:"end_date"`
}

// Summary resume el período.
type Summary struct {
	DaysInPeriod     int      `json:"days_in_period"`
	DaysWithData     int      `json:"days_with_data"`
	DaysSinFila      int      `json:"days_sin_fila"`
	DaysFilaSinValor int      `json:"days_fila_sin_valor"`
	Coverage         float64  `json:"coverage"`
	AccumulatedMM    *float64 `json:"accumulated_mm"` // nil si no hay ningún día con dato
}

// Result es la serie completa de una estación.
type Result struct {
	Station  station.Station
	Category Category
	From     civil.Date
	To       civil.Date // ya recortada a la fecha de corte
	Clipped  bool
	Days     []Day
	Summary  Summary
	Warnings []Warning
}

// Reader es lo que el servicio necesita de la base.
type Reader interface {
	Station(ctx context.Context, id int) (station.Station, bool, error)
	Days(ctx context.Context, stationID int, c Category, from, to civil.Date) (Data, error)
	Flags(ctx context.Context, stationID int, from, to civil.Date) ([]Flag, error)
}

// Error es un error de negocio controlado, con el código HTTP, el código y el mensaje en español.
type Error struct {
	Status  int
	Code    string
	Message string
}

func (e *Error) Error() string { return e.Message }

// FillCalendar devuelve un valor por día del período; el día que la base no tiene figura sin_fila.
func FillCalendar(days []Day, from, to civil.Date) []Day {
	byDate := make(map[string]Day, len(days))
	for _, d := range days {
		byDate[d.Date.String()] = d
	}
	total := from.DaysTo(to) + 1
	out := make([]Day, 0, max(total, 0))
	for i := 0; i < total; i++ {
		cur := from.AddDays(i)
		if d, ok := byDate[cur.String()]; ok {
			out = append(out, d)
			continue
		}
		out = append(out, Day{Date: cur, State: SinFila})
	}
	return out
}

// Summarize cuenta los estados y acumula solo los días con dato.
func Summarize(calendar []Day) Summary {
	s := Summary{DaysInPeriod: len(calendar)}
	var sum float64
	for _, d := range calendar {
		switch {
		case d.State == Dato && d.MM != nil:
			s.DaysWithData++
			sum += *d.MM
		case d.State == SinFila:
			s.DaysSinFila++
		case d.State == FilaSinValor:
			s.DaysFilaSinValor++
		}
	}
	if s.DaysInPeriod > 0 {
		s.Coverage = round(float64(s.DaysWithData)/float64(s.DaysInPeriod), 4)
	}
	if s.DaysWithData > 0 {
		r := round(sum, 2)
		s.AccumulatedMM = &r
	}
	return s
}

// round redondea como Python (mitad al par sobre el valor binario exacto), pasando por texto.
func round(v float64, decimals int) float64 {
	r, _ := strconv.ParseFloat(strconv.FormatFloat(v, 'f', decimals, 64), 64)
	return r
}

// Service arma las series.
type Service struct {
	reader Reader
	cutoff civil.Date
}

// NewService arma el servicio con el lector inyectado y la fecha de corte de los datos.
func NewService(r Reader, cutoff civil.Date) *Service { return &Service{reader: r, cutoff: cutoff} }

// Cutoff devuelve la fecha de corte de los datos.
func (s *Service) Cutoff() civil.Date { return s.cutoff }

// Series devuelve la serie diaria de una estación. Valida el período antes de buscar la estación.
func (s *Service) Series(ctx context.Context, stationID int, from, to civil.Date, c Category) (Result, error) {
	to, clipped, err := s.normalizeRange(from, to)
	if err != nil {
		return Result{}, err
	}
	st, ok, err := s.reader.Station(ctx, stationID)
	if err != nil {
		return Result{}, err
	}
	if !ok {
		return Result{}, &Error{404, "station_not_found", "No existe la estación pedida."}
	}
	data, err := s.reader.Days(ctx, stationID, c, from, to)
	if err != nil {
		return Result{}, err
	}
	calendar := FillCalendar(data.Days, from, to)
	summary := Summarize(calendar)
	flags, err := s.reader.Flags(ctx, stationID, from, to)
	if err != nil {
		return Result{}, err
	}
	return Result{
		Station: st, Category: c, From: from, To: to, Clipped: clipped,
		Days: calendar, Summary: summary, Warnings: warnings(flags, summary, data.Unvalidated),
	}, nil
}

// normalizeRange valida el período y lo recorta a la fecha de corte. Devuelve (hasta, recortado).
func (s *Service) normalizeRange(from, to civil.Date) (civil.Date, bool, error) {
	if from.After(to) {
		return to, false, &Error{422, "invalid_range", "La fecha inicial no puede ser posterior a la final."}
	}
	if from.After(s.cutoff) {
		return to, false, &Error{422, "after_cutoff", fmt.Sprintf(
			"No hay datos posteriores a la fecha de corte (%s).", s.cutoff.Format("02/01/2006"))}
	}
	clipped := to.After(s.cutoff)
	if clipped {
		to = s.cutoff
	}
	if from.DaysTo(to)+1 > MaxDays {
		return to, clipped, &Error{422, "range_too_large", fmt.Sprintf("El período no puede superar %d días.", MaxDays)}
	}
	return to, clipped, nil
}

func warnings(flags []Flag, sum Summary, unvalidated int) []Warning {
	out := []Warning{}
	for _, f := range flags {
		start, end := f.Start, f.End
		msg := "Advertencia de calidad."
		if f.Code == "ceros_prolongados" {
			msg = "Racha de 60 días o más con 0 mm: puede ser un sensor sin registrar, " +
				"no ausencia de lluvia. No se da por buena."
		}
		out = append(out, Warning{Code: f.Code, Message: msg, Severity: f.Severity, StartDate: &start, EndDate: &end})
	}
	if sum.Coverage < LowCoverageThreshold {
		out = append(out, Warning{
			Code: "cobertura_baja", Severity: "aviso",
			Message: fmt.Sprintf("Solo %.0f%% de los días tiene dato: el acumulado puede quedar por debajo de lo que llovió.", sum.Coverage*100),
		})
	}
	if unvalidated > 0 {
		out = append(out, Warning{
			Code: "dato_sin_validar", Severity: "aviso",
			Message: "Los datos de este período no pasaron una validación externa.",
		})
	}
	return out
}

// FlagsOnDay devuelve los códigos de las advertencias con fechas que cubren el día.
func FlagsOnDay(ws []Warning, d civil.Date) []string {
	out := []string{}
	for _, w := range ws {
		if w.StartDate != nil && w.EndDate != nil && !d.Before(*w.StartDate) && !d.After(*w.EndDate) {
			out = append(out, w.Code)
		}
	}
	return out
}
