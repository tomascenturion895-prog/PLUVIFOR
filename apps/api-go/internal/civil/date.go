// Package civil define una fecha de calendario sin hora ni zona (AAAA-MM-DD), como la que guarda
// la base: el «día de lluvia» no es un instante.
package civil

import (
	"encoding/json"
	"fmt"
	"time"
)

const layout = "2006-01-02"

// Date es un día del calendario. El valor cero no es una fecha válida.
type Date struct{ t time.Time }

// Parse acepta solo AAAA-MM-DD con ceros a la izquierda.
func Parse(s string) (Date, error) {
	t, err := time.Parse(layout, s)
	if err != nil {
		return Date{}, fmt.Errorf("fecha inválida: se espera AAAA-MM-DD")
	}
	return Date{t: t}, nil
}

// New arma una fecha a partir de año, mes y día.
func New(year int, month time.Month, day int) Date {
	return Date{t: time.Date(year, month, day, 0, 0, 0, 0, time.UTC)}
}

func (d Date) String() string { return d.t.Format(layout) }

// IsZero informa si es el valor cero.
func (d Date) IsZero() bool { return d.t.IsZero() }

// AddDays suma (o resta) días corridos.
func (d Date) AddDays(n int) Date { return Date{t: d.t.AddDate(0, 0, n)} }

// DaysTo devuelve los días corridos desde d hasta other (negativo si other es anterior).
func (d Date) DaysTo(other Date) int { return int(other.t.Sub(d.t).Hours() / 24) }

// Before, After y Equal comparan fechas.
func (d Date) Before(o Date) bool { return d.t.Before(o.t) }
func (d Date) After(o Date) bool  { return d.t.After(o.t) }
func (d Date) Equal(o Date) bool  { return d.t.Equal(o.t) }

// Format da formato con un layout de Go (por ejemplo, "02/01/2006").
func (d Date) Format(layout string) string { return d.t.Format(layout) }

// MarshalJSON serializa como "AAAA-MM-DD".
func (d Date) MarshalJSON() ([]byte, error) { return json.Marshal(d.String()) }

// UnmarshalJSON lee "AAAA-MM-DD".
func (d *Date) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}
	parsed, err := Parse(s)
	if err != nil {
		return err
	}
	*d = parsed
	return nil
}
