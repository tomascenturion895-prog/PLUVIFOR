package httpapi

import (
	"context"
	"encoding/json"
	"os"
	"sort"
	"strings"
	"testing"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/rainfall"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

// memStore es un lector en memoria cargado con la base de demostración que volcó Python.
// Cumple las dos interfaces (station.Reader y rainfall.Reader) sin tocar una base real.
type memStore struct {
	stations []station.Station
	days     map[string][]dayRow // clave: estación|categoría
	flags    map[int][]rainfall.Flag
	fail     error // si no es nil, todas las consultas fallan (prueba del 500)
}

type dayRow struct {
	day         rainfall.Day
	unvalidated bool
}

type dbDump struct {
	Sources []struct {
		ID             int     `json:"id"`
		Code           string  `json:"code"`
		Name           string  `json:"name"`
		Network        string  `json:"network"`
		Category       string  `json:"category"`
		DayCutoffLocal *string `json:"day_cutoff_local"`
	} `json:"sources"`
	Stations []struct {
		ID           int      `json:"id"`
		SourceID     int      `json:"source_id"`
		Code         string   `json:"code"`
		InternalCode *string  `json:"internal_code"`
		Name         string   `json:"name"`
		Kind         *string  `json:"kind"`
		Locality     *string  `json:"locality"`
		Department   *string  `json:"department"`
		Zone         *string  `json:"zone"`
		Lat          *float64 `json:"lat"`
		Lon          *float64 `json:"lon"`
		ElevationM   *float64 `json:"elevation_m"`
		CoordsStatus string   `json:"coords_status"`
		ActiveFrom   *string  `json:"active_from"`
		ActiveTo     *string  `json:"active_to"`
	} `json:"stations"`
	Flags []struct {
		StationID int    `json:"station_id"`
		Code      string `json:"code"`
		Start     string `json:"start_date"`
		End       string `json:"end_date"`
		Severity  string `json:"severity"`
	} `json:"flags"`
	Records [][]any `json:"records"` // station_id, obs_date, state, mm, category, validation
}

func mustDate(t testing.TB, s string) civil.Date {
	t.Helper()
	d, err := civil.Parse(s)
	if err != nil {
		t.Fatalf("fecha %q: %v", s, err)
	}
	return d
}

func optDate(t testing.TB, s *string) *civil.Date {
	if s == nil {
		return nil
	}
	d := mustDate(t, *s)
	return &d
}

func loadMemStore(t testing.TB) *memStore {
	t.Helper()
	raw, err := os.ReadFile("../../testdata/parity/db.json")
	if err != nil {
		t.Fatalf("falta testdata/parity/db.json (se genera con generate.py): %v", err)
	}
	var dump dbDump
	if err := json.Unmarshal(raw, &dump); err != nil {
		t.Fatal(err)
	}
	sources := map[int]station.Source{}
	for _, s := range dump.Sources {
		sources[s.ID] = station.Source{Code: s.Code, Name: s.Name, Network: s.Network, Category: s.Category, DayCutoffLocal: s.DayCutoffLocal}
	}
	m := &memStore{days: map[string][]dayRow{}, flags: map[int][]rainfall.Flag{}}
	for _, s := range dump.Stations {
		m.stations = append(m.stations, station.Station{
			ID: s.ID, Code: s.Code, InternalCode: s.InternalCode, Name: s.Name, Kind: s.Kind,
			Locality: s.Locality, Department: s.Department, Zone: s.Zone, Lat: s.Lat, Lon: s.Lon,
			ElevationM: s.ElevationM, CoordsStatus: s.CoordsStatus,
			ActiveFrom: optDate(t, s.ActiveFrom), ActiveTo: optDate(t, s.ActiveTo), Source: sources[s.SourceID],
		})
	}
	for _, f := range dump.Flags {
		m.flags[f.StationID] = append(m.flags[f.StationID], rainfall.Flag{
			Code: f.Code, Severity: rainfall.Severity(f.Severity), Start: mustDate(t, f.Start), End: mustDate(t, f.End),
		})
	}
	for _, r := range dump.Records {
		id := int(r[0].(float64))
		d := rainfall.Day{Date: mustDate(t, r[1].(string)), State: rainfall.State(r[2].(string))}
		if v, ok := r[3].(float64); ok {
			d.MM = &v
		}
		key := rowKey(id, rainfall.Category(r[4].(string)))
		m.days[key] = append(m.days[key], dayRow{day: d, unvalidated: d.MM != nil && r[5].(string) == "sin_validar"})
	}
	return m
}

func rowKey(id int, c rainfall.Category) string {
	return string(c) + "|" + string(rune('0'+id%10)) + "|" + itoa(id)
}

func itoa(n int) string {
	b, _ := json.Marshal(n)
	return string(b)
}

func (m *memStore) Search(_ context.Context, f station.Filters, p station.Page) ([]station.Station, int, error) {
	if m.fail != nil {
		return nil, 0, m.fail
	}
	var out []station.Station
	for _, s := range m.stations {
		if f.SourceCode != "" && s.Source.Code != f.SourceCode ||
			f.Network != "" && s.Source.Network != f.Network ||
			f.Department != "" && (s.Department == nil || *s.Department != f.Department) ||
			f.Zone != "" && (s.Zone == nil || *s.Zone != f.Zone) ||
			f.CoordsStatus != "" && s.CoordsStatus != f.CoordsStatus {
			continue
		}
		if f.Text != "" {
			needle := strings.ToLower(f.Text)
			inName := strings.Contains(strings.ToLower(s.Name), needle)
			inLoc := s.Locality != nil && strings.Contains(strings.ToLower(*s.Locality), needle)
			if !inName && !inLoc {
				continue
			}
		}
		out = append(out, s)
	}
	sort.SliceStable(out, func(i, j int) bool {
		if out[i].Name != out[j].Name {
			return out[i].Name < out[j].Name
		}
		return out[i].ID < out[j].ID
	})
	total := len(out)
	if p.Offset >= total {
		return nil, total, nil
	}
	end := min(p.Offset+p.Limit, total)
	return out[p.Offset:end], total, nil
}

func (m *memStore) Get(_ context.Context, id int) (station.Station, bool, error) {
	if m.fail != nil {
		return station.Station{}, false, m.fail
	}
	for _, s := range m.stations {
		if s.ID == id {
			return s, true, nil
		}
	}
	return station.Station{}, false, nil
}

func (m *memStore) Station(ctx context.Context, id int) (station.Station, bool, error) {
	return m.Get(ctx, id)
}

func (m *memStore) Days(_ context.Context, id int, c rainfall.Category, from, to civil.Date) (rainfall.Data, error) {
	if m.fail != nil {
		return rainfall.Data{}, m.fail
	}
	var data rainfall.Data
	for _, r := range m.days[rowKey(id, c)] {
		if r.day.Date.Before(from) || r.day.Date.After(to) {
			continue
		}
		data.Days = append(data.Days, r.day)
		if r.unvalidated {
			data.Unvalidated++
		}
	}
	return data, nil
}

func (m *memStore) Flags(_ context.Context, id int, from, to civil.Date) ([]rainfall.Flag, error) {
	if m.fail != nil {
		return nil, m.fail
	}
	var out []rainfall.Flag
	for _, f := range m.flags[id] {
		if !f.Start.After(to) && !f.End.Before(from) {
			out = append(out, f)
		}
	}
	return out, nil
}
