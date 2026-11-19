package config

import (
	"strings"
	"testing"
)

func env(values map[string]string) Lookup {
	return func(key string) (string, bool) { v, ok := values[key]; return v, ok }
}

func TestLoadUsaLosValoresPorDefecto(t *testing.T) {
	cfg, err := Load(env(nil))
	if err != nil {
		t.Fatalf("no debía fallar: %v", err)
	}
	if cfg.CutoffDate != "2026-10-31" || cfg.Port != "8080" || cfg.Database.Engine != "sqlite" {
		t.Fatalf("valores por defecto inesperados: %+v", cfg)
	}
}

func TestLoadLeeLaMismaBaseQuePython(t *testing.T) {
	cfg, err := Load(env(map[string]string{"DATABASE_URL": "postgresql+psycopg://u:clave@host:5432/pluvifor"}))
	if err != nil || cfg.Database.Engine != "postgresql" {
		t.Fatalf("debía reconocer PostgreSQL: %+v %v", cfg, err)
	}
}

func TestLoadRechazaEntradasInvalidas(t *testing.T) {
	casos := map[string]map[string]string{
		"fecha de corte mal escrita": {"DATA_CUTOFF_DATE": "31/10/2026"},
		"fecha de corte inexistente": {"DATA_CUTOFF_DATE": "2026-02-31"},
		"base sin formato":           {"DATABASE_URL": "pluvifor.db"},
		"motor no soportado":         {"DATABASE_URL": "mysql://u:clave@host/db"},
	}
	for nombre, valores := range casos {
		if _, err := Load(env(valores)); err == nil {
			t.Errorf("%s: debía dar error", nombre)
		}
	}
}

func TestElErrorNoRepiteLaClaveDeLaBase(t *testing.T) {
	_, err := Load(env(map[string]string{"DATABASE_URL": "mysql://usuario:SECRETO@host/db"}))
	if err == nil || strings.Contains(err.Error(), "SECRETO") {
		t.Fatalf("el error no puede incluir la clave: %v", err)
	}
}

func TestBackendURLPorDefectoYValidacion(t *testing.T) {
	cfg, err := Load(env(nil))
	if err != nil || cfg.BackendURL.String() != "http://127.0.0.1:8000" {
		t.Fatalf("valor por defecto inesperado: %v %v", cfg.BackendURL, err)
	}
	for _, malo := range []string{"127.0.0.1:8000", "ftp://host/", "http://", "http://u:SECRETO@host:8000"} {
		_, err := Load(env(map[string]string{"BACKEND_URL": malo}))
		if err == nil {
			t.Errorf("%q debía rechazarse", malo)
		} else if strings.Contains(err.Error(), "SECRETO") {
			t.Errorf("el error repite la clave: %v", err)
		}
	}
}
