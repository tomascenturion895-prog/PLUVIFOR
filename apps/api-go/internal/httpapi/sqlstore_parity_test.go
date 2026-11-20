//go:build sqlite

package httpapi

import (
	"database/sql"
	"encoding/json"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/sqlstore"
)

// Mismo esquema que crea Alembic (solo las columnas que lee Go).
const ddl = `
CREATE TABLE sources (id INTEGER PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL, network TEXT NOT NULL, category TEXT NOT NULL, day_cutoff_local TEXT);
CREATE TABLE stations (id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, code TEXT NOT NULL, internal_code TEXT, name TEXT NOT NULL, kind TEXT, locality TEXT, department TEXT, zone TEXT, lat DOUBLE, lon DOUBLE, elevation_m DOUBLE, coords_status TEXT NOT NULL, active_from DATE, active_to DATE);
CREATE TABLE rainfall_records (id INTEGER PRIMARY KEY, station_id INTEGER NOT NULL, obs_date DATE NOT NULL, state TEXT NOT NULL, mm NUMERIC(8,2), category TEXT NOT NULL, validation TEXT NOT NULL, CHECK ((state = 'dato') = (mm IS NOT NULL)));
CREATE TABLE quality_flags (id INTEGER PRIMARY KEY, station_id INTEGER NOT NULL, code TEXT NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL, severity TEXT NOT NULL);
`

// newSQLiteFile arma una base SQLite real con la base de demostración que volcó Python.
func newSQLiteFile(t *testing.T) string {
	t.Helper()
	raw, err := os.ReadFile("../../testdata/parity/db.json")
	if err != nil {
		t.Fatal(err)
	}
	var dump dbDump
	if err := json.Unmarshal(raw, &dump); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "demo.db")
	db, err := sql.Open(sqlstore.DriverName, "file:"+path)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(ddl); err != nil {
		t.Fatal(err)
	}
	must := func(q string, args ...any) {
		if _, err := db.Exec(q, args...); err != nil {
			t.Fatalf("%s: %v", q, err)
		}
	}
	for _, s := range dump.Sources {
		must("INSERT INTO sources VALUES (?,?,?,?,?,?)", s.ID, s.Code, s.Name, s.Network, s.Category, s.DayCutoffLocal)
	}
	for _, s := range dump.Stations {
		must("INSERT INTO stations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", s.ID, s.SourceID, s.Code, s.InternalCode, s.Name, s.Kind,
			s.Locality, s.Department, s.Zone, s.Lat, s.Lon, s.ElevationM, s.CoordsStatus, s.ActiveFrom, s.ActiveTo)
	}
	for _, f := range dump.Flags {
		must("INSERT INTO quality_flags (station_id, code, start_date, end_date, severity) VALUES (?,?,?,?,?)", f.StationID, f.Code, f.Start, f.End, f.Severity)
	}
	tx, _ := db.Begin()
	for _, r := range dump.Records {
		if _, err := tx.Exec("INSERT INTO rainfall_records (station_id, obs_date, state, mm, category, validation) VALUES (?,?,?,?,?,?)",
			r[0], r[1], r[2], r[3], r[4], r[5]); err != nil {
			t.Fatal(err)
		}
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	return path
}

// TestParidadConPythonDesdeSQLite: las mismas 47 consultas, pero leyendo una base SQLite de verdad
// a través de sqlstore. Es la prueba de que el SQL devuelve lo mismo que SQLAlchemy.
func TestParidadConPythonDesdeSQLite(t *testing.T) {
	store, err := sqlstore.OpenSQLite(newSQLiteFile(t))
	if err != nil {
		t.Fatal(err)
	}
	defer store.Close()
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	srv := New(testConfig(), logger,
		WithStations(store, logger),
		WithRainfall(store, mustDate(t, "2026-10-31"), logger),
	)
	runParity(t, srv)
}

// El driver abre en solo lectura: Go nunca escribe en la base que mantiene Python.
func TestLaBaseSeAbreSoloLectura(t *testing.T) {
	path := newSQLiteFile(t)
	store, err := sqlstore.OpenSQLite(path)
	if err != nil {
		t.Fatal(err)
	}
	defer store.Close()
	if _, err := store.DB().Exec("DELETE FROM rainfall_records"); err == nil {
		t.Fatal("la conexión de Go no debería poder borrar datos")
	}
}
