// Package sqlstore lee de la base (la misma que escribe Python) y cumple las interfaces Reader de
// station y rainfall. Usa solo database/sql: el driver concreto se elige aparte (driver_sqlite.go),
// así la lógica no depende de un motor. Solo lee: nunca escribe.
//
// Todas las consultas llevan parámetros (nunca texto armado con datos de quien consulta).
package sqlstore

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// Dialect es el motor de la base. Solo cambia el estilo de los parámetros.
type Dialect int

const (
	SQLite     Dialect = iota // parámetros ?
	PostgreSQL                // parámetros $1, $2... (sin probar contra un servidor real)
)

// ErrNoDriver indica que este binario se compiló sin driver de base de datos.
var ErrNoDriver = errors.New("este programa se compiló sin driver de base de datos (usar -tags sqlite)")

// Store lee estaciones y lluvia. Cumple station.Reader y rainfall.Reader.
type Store struct {
	db      *sql.DB
	dialect Dialect
}

// New arma el lector sobre una conexión ya abierta.
func New(db *sql.DB, d Dialect) *Store { return &Store{db: db, dialect: d} }

// OpenSQLite abre un archivo SQLite en solo lectura con el driver compilado. Si no hay driver,
// devuelve ErrNoDriver. El error nunca repite la ruta ni datos de acceso.
func OpenSQLite(path string) (*Store, error) {
	if DriverName == "" {
		return nil, ErrNoDriver
	}
	db, err := sql.Open(DriverName, "file:"+path+"?mode=ro")
	if err != nil {
		return nil, errors.New("no se pudo abrir la base")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, errors.New("no se pudo abrir la base")
	}
	return New(db, SQLite), nil
}

// DB expone la conexión para las pruebas de solo lectura.
func (s *Store) DB() *sql.DB { return s.db }

// Close cierra la conexión.
func (s *Store) Close() error { return s.db.Close() }

// rebind adapta los ? al estilo del motor.
func (s *Store) rebind(q string) string {
	if s.dialect != PostgreSQL {
		return q
	}
	var b strings.Builder
	n := 0
	for _, r := range q {
		if r == '?' {
			n++
			fmt.Fprintf(&b, "$%d", n)
			continue
		}
		b.WriteRune(r)
	}
	return b.String()
}

const stationColumns = `st.id, st.code, st.internal_code, st.name, st.kind, st.locality, st.department,
	st.zone, st.lat, st.lon, st.elevation_m, st.coords_status, st.active_from, st.active_to,
	so.code, so.name, so.network, so.category, so.day_cutoff_local`

const stationFrom = ` FROM stations st JOIN sources so ON so.id = st.source_id`

// Search devuelve una página del catálogo ordenada por nombre y id, y el total sin paginar.
func (s *Store) Search(ctx context.Context, f station.Filters, p station.Page) ([]station.Station, int, error) {
	where, args := stationWhere(f)
	var total int
	if err := s.db.QueryRowContext(ctx, s.rebind("SELECT COUNT(*)"+stationFrom+where), args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("contar estaciones: %w", err)
	}
	q := "SELECT " + stationColumns + stationFrom + where + " ORDER BY st.name, st.id LIMIT ? OFFSET ?"
	rows, err := s.db.QueryContext(ctx, s.rebind(q), append(args, p.Limit, p.Offset)...)
	if err != nil {
		return nil, 0, fmt.Errorf("buscar estaciones: %w", err)
	}
	defer rows.Close()
	items := []station.Station{}
	for rows.Next() {
		st, err := scanStation(rows)
		if err != nil {
			return nil, 0, err
		}
		items = append(items, st)
	}
	return items, total, rows.Err()
}

// stationWhere arma las condiciones con parámetros. Un filtro vacío no filtra.
func stationWhere(f station.Filters) (string, []any) {
	var conds []string
	var args []any
	add := func(cond string, v any) { conds = append(conds, cond); args = append(args, v) }
	if f.SourceCode != "" {
		add("so.code = ?", f.SourceCode)
	}
	if f.Network != "" {
		add("so.network = ?", f.Network)
	}
	if f.Department != "" {
		add("st.department = ?", f.Department)
	}
	if f.Zone != "" {
		add("st.zone = ?", f.Zone)
	}
	if f.CoordsStatus != "" {
		add("st.coords_status = ?", f.CoordsStatus)
	}
	if f.Text != "" {
		pattern := "%" + strings.ToLower(f.Text) + "%"
		conds = append(conds, "(LOWER(st.name) LIKE ? OR LOWER(st.locality) LIKE ?)")
		args = append(args, pattern, pattern)
	}
	if len(conds) == 0 {
		return "", nil
	}
	return " WHERE " + strings.Join(conds, " AND "), args
}

// Get devuelve la ficha de una estación.
func (s *Store) Get(ctx context.Context, id int) (station.Station, bool, error) {
	q := "SELECT " + stationColumns + stationFrom + " WHERE st.id = ?"
	rows, err := s.db.QueryContext(ctx, s.rebind(q), id)
	if err != nil {
		return station.Station{}, false, fmt.Errorf("leer estación: %w", err)
	}
	defer rows.Close()
	if !rows.Next() {
		return station.Station{}, false, rows.Err()
	}
	st, err := scanStation(rows)
	return st, err == nil, err
}

// Station cumple rainfall.Reader.
func (s *Store) Station(ctx context.Context, id int) (station.Station, bool, error) {
	return s.Get(ctx, id)
}

// Days devuelve solo los días que existen en la base, de una categoría y un período. Un día que
// falta lo completa el servicio como sin_fila: acá nunca se inventa un valor.
func (s *Store) Days(ctx context.Context, id int, c rainfall.Category, from, to civil.Date) (rainfall.Data, error) {
	const q = `SELECT obs_date, state, mm, validation FROM rainfall_records
		WHERE station_id = ? AND category = ? AND obs_date BETWEEN ? AND ? ORDER BY obs_date`
	rows, err := s.db.QueryContext(ctx, s.rebind(q), id, string(c), from.String(), to.String())
	if err != nil {
		return rainfall.Data{}, fmt.Errorf("leer lluvia: %w", err)
	}
	defer rows.Close()
	var data rainfall.Data
	for rows.Next() {
		var (
			rawDate    any
			state, val string
			mm         sql.NullFloat64
		)
		if err := rows.Scan(&rawDate, &state, &mm, &val); err != nil {
			return rainfall.Data{}, fmt.Errorf("leer lluvia: %w", err)
		}
		date, err := toDate(rawDate)
		if err != nil {
			return rainfall.Data{}, err
		}
		day := rainfall.Day{Date: date, State: rainfall.State(state)}
		if mm.Valid { // un NULL de la base es «sin dato»: nunca se convierte en 0
			v := mm.Float64
			day.MM = &v
			if val == "sin_validar" {
				data.Unvalidated++
			}
		}
		data.Days = append(data.Days, day)
	}
	return data, rows.Err()
}

// Flags devuelve las banderas de calidad que tocan el período.
func (s *Store) Flags(ctx context.Context, id int, from, to civil.Date) ([]rainfall.Flag, error) {
	const q = `SELECT code, severity, start_date, end_date FROM quality_flags
		WHERE station_id = ? AND start_date <= ? AND end_date >= ? ORDER BY start_date`
	rows, err := s.db.QueryContext(ctx, s.rebind(q), id, to.String(), from.String())
	if err != nil {
		return nil, fmt.Errorf("leer banderas: %w", err)
	}
	defer rows.Close()
	var out []rainfall.Flag
	for rows.Next() {
		var (
			code, sev string
			rs, re    any
		)
		if err := rows.Scan(&code, &sev, &rs, &re); err != nil {
			return nil, fmt.Errorf("leer banderas: %w", err)
		}
		start, err := toDate(rs)
		if err != nil {
			return nil, err
		}
		end, err := toDate(re)
		if err != nil {
			return nil, err
		}
		out = append(out, rainfall.Flag{Code: code, Severity: rainfall.Severity(sev), Start: start, End: end})
	}
	return out, rows.Err()
}

type scanner interface{ Scan(dest ...any) error }

func scanStation(r scanner) (station.Station, error) {
	var (
		st                                       station.Station
		internalCode, kind, locality, dept, zone sql.NullString
		lat, lon, elev                           sql.NullFloat64
		from, to                                 any
		dayCutoff                                sql.NullString
	)
	if err := r.Scan(&st.ID, &st.Code, &internalCode, &st.Name, &kind, &locality, &dept, &zone,
		&lat, &lon, &elev, &st.CoordsStatus, &from, &to,
		&st.Source.Code, &st.Source.Name, &st.Source.Network, &st.Source.Category, &dayCutoff); err != nil {
		return station.Station{}, fmt.Errorf("leer estación: %w", err)
	}
	st.InternalCode, st.Kind, st.Locality = str(internalCode), str(kind), str(locality)
	st.Department, st.Zone = str(dept), str(zone)
	st.Lat, st.Lon, st.ElevationM = num(lat), num(lon), num(elev)
	st.Source.DayCutoffLocal = str(dayCutoff)
	var err error
	if st.ActiveFrom, err = optDate(from); err != nil {
		return station.Station{}, err
	}
	if st.ActiveTo, err = optDate(to); err != nil {
		return station.Station{}, err
	}
	return st, nil
}

func str(n sql.NullString) *string {
	if !n.Valid {
		return nil
	}
	return &n.String
}

func num(n sql.NullFloat64) *float64 {
	if !n.Valid {
		return nil
	}
	return &n.Float64
}

// toDate lee una fecha guardada como texto AAAA-MM-DD o, según el driver, como time.Time.
func toDate(v any) (civil.Date, error) {
	switch x := v.(type) {
	case time.Time:
		return civil.New(x.Year(), x.Month(), x.Day()), nil
	case string:
		return civil.Parse(strings.TrimSpace(x)[:min(len(strings.TrimSpace(x)), 10)])
	case []byte:
		return toDate(string(x))
	}
	return civil.Date{}, errors.New("fecha con formato inesperado en la base")
}

func optDate(v any) (*civil.Date, error) {
	if v == nil {
		return nil, nil
	}
	d, err := toDate(v)
	if err != nil {
		return nil, err
	}
	return &d, nil
}
