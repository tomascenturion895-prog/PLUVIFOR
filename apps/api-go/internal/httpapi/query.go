package httpapi

import (
	"errors"
	"fmt"
	"net/url"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/apierror"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
)

// maxID es el mayor entero de 32 bits: cabe en cualquier columna INTEGER (igual que en Python).
const maxID = 2_147_483_647

// params valida los parámetros de una consulta y junta todos los errores, en el orden en que se
// leen, con los mismos mensajes que la API de Python. Nunca incluye el valor recibido.
type params struct {
	values url.Values
	errs   []apierror.FieldError
}

func (p *params) fail(loc, name, msg string) {
	p.errs = append(p.errs, apierror.FieldError{Field: loc + "." + name, Message: msg})
}

// raw devuelve el último valor del parámetro (como hace FastAPI) y si vino.
func (p *params) raw(name string) (string, bool) {
	vs, ok := p.values[name]
	if !ok || len(vs) == 0 {
		return "", false
	}
	return vs[len(vs)-1], true
}

// text lee un texto opcional con largo máximo en caracteres.
func (p *params) text(name string, maxLen int) string {
	v, _ := p.raw(name)
	if utf8.RuneCountInString(v) > maxLen {
		p.fail("query", name, fmt.Sprintf("String should have at most %d characters", maxLen))
		return ""
	}
	return v
}

// intIn lee un entero entre min y max. Si falta y def es nil, es obligatorio.
func (p *params) intIn(loc, name, v string, present bool, def *int, minV, maxV int) int {
	if !present {
		if def == nil {
			p.fail(loc, name, "Field required")
			return 0
		}
		return *def
	}
	n, err := strconv.ParseInt(strings.TrimSpace(v), 10, 64)
	if err != nil {
		var ne *strconv.NumError
		if errors.As(err, &ne) && errors.Is(ne.Err, strconv.ErrRange) {
			// Un entero enorme es un entero válido pero fuera de rango, no un texto inválido.
			if strings.HasPrefix(strings.TrimSpace(v), "-") {
				p.fail(loc, name, fmt.Sprintf("Input should be greater than or equal to %d", minV))
			} else {
				p.fail(loc, name, fmt.Sprintf("Input should be less than or equal to %d", maxV))
			}
			return 0
		}
		p.fail(loc, name, "Input should be a valid integer, unable to parse string as an integer")
		return 0
	}
	switch {
	case n < int64(minV):
		p.fail(loc, name, fmt.Sprintf("Input should be greater than or equal to %d", minV))
	case n > int64(maxV):
		p.fail(loc, name, fmt.Sprintf("Input should be less than or equal to %d", maxV))
	default:
		return int(n)
	}
	return 0
}

// queryInt lee un entero de la consulta.
func (p *params) queryInt(name string, def *int, minV, maxV int) int {
	v, ok := p.raw(name)
	return p.intIn("query", name, v, ok, def, minV, maxV)
}

// date lee una fecha obligatoria AAAA-MM-DD de la consulta.
func (p *params) date(name string) civil.Date {
	v, ok := p.raw(name)
	if !ok {
		p.fail("query", name, "Field required")
		return civil.Date{}
	}
	d, err := civil.Parse(v)
	if err != nil {
		p.fail("query", name, "Input should be a valid date or datetime, expected YYYY-MM-DD")
		return civil.Date{}
	}
	return d
}

// oneOf lee un valor de una lista cerrada. Si no vino, devuelve def.
func (p *params) oneOf(name, def string, allowed ...string) string {
	v, ok := p.raw(name)
	if !ok {
		return def
	}
	for _, a := range allowed {
		if v == a {
			return v
		}
	}
	p.fail("query", name, "Input should be "+quoteList(allowed))
	return def
}

func quoteList(items []string) string {
	q := make([]string, len(items))
	for i, s := range items {
		q[i] = "'" + s + "'"
	}
	if len(q) == 1 {
		return q[0]
	}
	return strings.Join(q[:len(q)-1], ", ") + " or " + q[len(q)-1]
}

// valid informa si no hubo errores.
func (p *params) valid() bool { return len(p.errs) == 0 }
