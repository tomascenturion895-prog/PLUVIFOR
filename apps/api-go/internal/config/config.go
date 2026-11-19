// Package config lee la configuración del entorno. Nunca imprime ni devuelve secretos.
package config

import (
	"errors"
	"fmt"
	"net/url"
	"os"
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
	// BackendURL es la API de datos en Python (apps/backend), a la que Go reenvía /api/*.
	BackendURL *url.URL
}

// Database describe la base sin guardar la URL completa (puede llevar usuario y clave).
type Database struct {
	Engine string // "sqlite" o "postgresql"
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
	engine, err := engineOf(get("DATABASE_URL", defaultDatabaseURL))
	if err != nil {
		return Config{}, err
	}
	cfg.Database = Database{Engine: engine}
	backend, err := backendURL(get("BACKEND_URL", defaultBackendURL))
	if err != nil {
		return Config{}, err
	}
	cfg.BackendURL = backend
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
