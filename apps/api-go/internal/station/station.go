// Package station es el catálogo de estaciones: qué se mide y dónde. Las reglas no saben si detrás
// hay SQL u otra cosa: dependen de la interfaz Reader, que define este paquete (el consumidor).
package station

import (
	"context"
	"errors"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
)

// Valores de coords_status. Una estación sin coordenadas figura como pendiente: no se inventan.
const (
	CoordsVerified = "verificada"
	CoordsPending  = "pendiente"
)

// Source dice de dónde viene el dato: toda estación informa su fuente y su categoría.
type Source struct {
	Code           string  `json:"code"`
	Name           string  `json:"name"`
	Network        string  `json:"network"`
	Category       string  `json:"category"`
	DayCutoffLocal *string `json:"day_cutoff_local"`
}

// Station es una estación de medición. Los campos opcionales vacíos se devuelven como null.
type Station struct {
	ID           int         `json:"id"`
	Code         string      `json:"code"`
	InternalCode *string     `json:"internal_code"`
	Name         string      `json:"name"`
	Kind         *string     `json:"kind"`
	Locality     *string     `json:"locality"`
	Department   *string     `json:"department"`
	Zone         *string     `json:"zone"`
	Lat          *float64    `json:"lat"`
	Lon          *float64    `json:"lon"`
	ElevationM   *float64    `json:"elevation_m"`
	CoordsStatus string      `json:"coords_status"`
	ActiveFrom   *civil.Date `json:"active_from"`
	ActiveTo     *civil.Date `json:"active_to"`
	Source       Source      `json:"source"`
}

// Filters son los filtros del catálogo. Un campo vacío no filtra.
type Filters struct {
	SourceCode   string
	Network      string
	Department   string
	Zone         string
	CoordsStatus string
	Text         string // en nombre o localidad, sin distinguir mayúsculas
}

// Page es la paginación del catálogo.
type Page struct {
	Limit  int
	Offset int
}

// Reader es lo que el servicio necesita de la base. Search devuelve la página pedida, ordenada por
// nombre y luego por id, y el total sin paginar.
type Reader interface {
	Search(ctx context.Context, f Filters, p Page) (items []Station, total int, err error)
	Get(ctx context.Context, id int) (Station, bool, error)
}

// ErrNotFound indica que la estación pedida no existe.
var ErrNotFound = errors.New("no existe la estación pedida")

// Service consulta el catálogo.
type Service struct{ reader Reader }

// NewService arma el servicio con el lector inyectado.
func NewService(r Reader) *Service { return &Service{reader: r} }

// Search devuelve una página del catálogo. La lista nunca es nil.
func (s *Service) Search(ctx context.Context, f Filters, p Page) ([]Station, int, error) {
	items, total, err := s.reader.Search(ctx, f, p)
	if err != nil {
		return nil, 0, err
	}
	if items == nil {
		items = []Station{}
	}
	return items, total, nil
}

// Get devuelve la ficha de una estación o ErrNotFound.
func (s *Service) Get(ctx context.Context, id int) (Station, error) {
	st, ok, err := s.reader.Get(ctx, id)
	if err != nil {
		return Station{}, err
	}
	if !ok {
		return Station{}, ErrNotFound
	}
	return st, nil
}
