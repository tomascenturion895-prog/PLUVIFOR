// Package config lee la configuración del entorno. Nunca imprime ni devuelve secretos.
package config

import (
	"errors"
	"fmt"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

const (
	defaultDatabaseURL = "sqlite:///./pluvifor.db"
	defaultCutoff      = "2026-10-31"
	defaultPort        = "8080"
	defaultBackendURL  = "http://127.0.0.1:8000"
)

// Config es la configuración de la API. La base es la misma que usa Python (DATABASE_URL).
type Config struct {
	Env        string
	Port       string
	CutoffDate string // AAAA-MM-DD: fecha de corte de los datos
	Database   Database
	// Pedidos por minuto y por cliente (0 desactiva el límite): general y de importación.
	RateLimitPerMinute       int
	RateLimitImportPerMinute int
	// BackendURL es la API de datos en Python (apps/backend), a la que Go reenvía /api/*.
	BackendURL *url.URL
}

// Database describe la base sin guardar la URL completa (puede llevar usuario y clave).
type Database struct {
	Engine string // "sqlite" o "postgresql"
	// SQLitePath es la ruta del archivo cuando el motor es SQLite (no es un secreto). Vacía en PostgreSQL.
	// Una ruta relativa se resuelve desde donde corre Go, no desde donde corre Python: conviene absoluta.
	SQLitePath string
}

// Lookup permite probar sin tocar el entorno real.
type Lookup func(key string) (string, bool)

// FromEnv lee la configuración del entorno del proceso.
func FromEnv() (Config, error) { return Load(os.LookupEnv) }

// Load valida y arma la configuración. Un valor inválido es un error, no un valor por defecto.
func Load(lookup Lookup) (Config, error) {
	get := func(key, fallback string) string {
		if v, ok := lookup(key); ok && strings.TrimSpace(v) != "" {
			return strings.TrimSpace(v)
		}
		return fallback
	}

	cfg := Config{
		Env:        get("APP_ENV", "development"),
		Port:       get("API_GO_PORT", defaultPort),
		CutoffDate: get("DATA_CUTOFF_DATE", defaultCutoff),
	}
	if _, err := time.Parse("2006-01-02", cfg.CutoffDate); err != nil {
		return Config{}, errors.New("DATA_CUTOFF_DATE debe tener el formato AAAA-MM-DD")
	}
	dbURL := get("DATABASE_URL", defaultDatabaseURL)
	engine, err := engineOf(dbURL)
	if err != nil {
		return Config{}, err
	}
	cfg.Database = Database{Engine: engine}
	if engine == "sqlite" {
		cfg.Database.SQLitePath = sqlitePath(dbURL)
	}
	backend, err := backendURL(get("BACKEND_URL", defaultBackendURL))
	if err != nil {
		return Config{}, err
	}
	cfg.BackendURL = backend
	if cfg.RateLimitPerMinute, err = nonNegative(get("API_GO_RATE_LIMIT_PER_MINUTE", "120"), "API_GO_RATE_LIMIT_PER_MINUTE"); err != nil {
		return Config{}, err
	}
	if cfg.RateLimitImportPerMinute, err = nonNegative(get("API_GO_RATE_LIMIT_IMPORT_PER_MINUTE", "10"), "API_GO_RATE_LIMIT_IMPORT_PER_MINUTE"); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

// backendURL valida la dirección del backend. El error no repite la URL: podría llevar datos de acceso.
func backendURL(raw string) (*url.URL, error) {
	u, err := url.Parse(raw)
	if err != nil || (u.Scheme != "http" && u.Scheme != "https") || u.Host == "" {
		return nil, errors.New("BACKEND_URL debe ser una dirección http o https con servidor")
	}
	if u.User != nil {
		return nil, errors.New("BACKEND_URL no puede llevar usuario ni clave")
	}
	u.Path, u.RawQuery, u.Fragment = "", "", ""
	return u, nil
}

// engineOf devuelve solo el motor. El mensaje de error no repite la URL: puede llevar la clave.
func engineOf(url string) (string, error) {
	scheme, _, found := strings.Cut(url, "://")
	if !found {
		return "", errors.New("DATABASE_URL no tiene un formato válido")
	}
	switch base, _, _ := strings.Cut(scheme, "+"); base {
	case "sqlite":
		return "sqlite", nil
	case "postgresql", "postgres":
		return "postgresql", nil
	default:
		return "", fmt.Errorf("DATABASE_URL: motor %q no soportado (sqlite o postgresql)", scheme)
	}
}

// sqlitePath saca la ruta de una URL de SQLAlchemy: sqlite:///./x.db (relativa) o sqlite:////tmp/x.db (absoluta).
func sqlitePath(url string) string {
	_, rest, _ := strings.Cut(url, "://")
	rest = strings.TrimPrefix(rest, "/") // el primer / separa el servidor (vacío) de la ruta
	if i := strings.IndexAny(rest, "?#"); i >= 0 {
		rest = rest[:i]
	}
	return rest
}

func nonNegative(raw, name string) (int, error) {
	n, err := strconv.Atoi(raw)
	if err != nil || n < 0 || n > 1_000_000 {
		return 0, fmt.Errorf("%s debe ser un entero entre 0 y 1000000", name)
	}
	return n, nil
}
