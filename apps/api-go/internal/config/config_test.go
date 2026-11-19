package config

import (
	"path/filepath"
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

func TestRutaDeSQLite(t *testing.T) {
	casos := map[string]string{
		"sqlite:///./pluvifor.db":      "./pluvifor.db",
		"sqlite:////tmp/demo.db":       "/tmp/demo.db",
		"sqlite+pysqlite:////tmp/a.db": "/tmp/a.db",
		"sqlite:////tmp/a.db?mode=ro":  "/tmp/a.db",
	}
	for url, want := range casos {
		cfg, err := Load(func(k string) (string, bool) {
			if k == "DATABASE_URL" {
				return url, true
			}
			return "", false
		})
		if err != nil || cfg.Database.SQLitePath != want {
			t.Errorf("%s → %q (%v), quería %q", url, cfg.Database.SQLitePath, err, want)
		}
	}
}

func TestPostgreSQLNoGuardaRutaNiClave(t *testing.T) {
	cfg, err := Load(func(k string) (string, bool) {
		if k == "DATABASE_URL" {
			return "postgresql://usuario:secreto@host/db", true
		}
		return "", false
	})
	if err != nil || cfg.Database.SQLitePath != "" || cfg.Database.Engine != "postgresql" {
		t.Fatalf("cfg = %+v err = %v", cfg.Database, err)
	}
}

func TestLimitesDePedidosPorDefectoYValidacion(t *testing.T) {
	cfg, err := Load(func(string) (string, bool) { return "", false })
	if err != nil || cfg.RateLimitPerMinute != 120 || cfg.RateLimitImportPerMinute != 10 {
		t.Fatalf("cfg = %+v err = %v", cfg, err)
	}
	for _, malo := range []string{"-1", "abc", "1000001", "1.5"} {
		_, err := Load(func(k string) (string, bool) {
			if k == "API_GO_RATE_LIMIT_PER_MINUTE" {
				return malo, true
			}
			return "", false
		})
		if err == nil {
			t.Errorf("%q debía rechazarse", malo)
		}
	}
	cfg, err = Load(func(k string) (string, bool) {
		if k == "API_GO_RATE_LIMIT_PER_MINUTE" {
			return "0", true
		}
		return "", false
	})
	if err != nil || cfg.RateLimitPerMinute != 0 {
		t.Fatalf("0 debe desactivar el límite: %+v %v", cfg, err)
	}
}

func TestEscuchaSoloEnLocalhostPorDefecto(t *testing.T) {
	cfg, err := Load(func(string) (string, bool) { return "", false })
	if err != nil || cfg.Host != "127.0.0.1" {
		t.Fatalf("host = %q err = %v", cfg.Host, err)
	}
	cfg, err = Load(func(k string) (string, bool) {
		if k == "API_GO_HOST" {
			return "0.0.0.0", true
		}
		return "", false
	})
	if err != nil || cfg.Host != "0.0.0.0" {
		t.Fatalf("API_GO_HOST debía poder abrirse a la red a pedido: %q %v", cfg.Host, err)
	}
	for _, malo := range []string{"host:8080", "a b", "http://x", "x/y"} {
		if _, err := Load(func(k string) (string, bool) {
			if k == "API_GO_HOST" {
				return malo, true
			}
			return "", false
		}); err == nil {
			t.Errorf("%q debía rechazarse", malo)
		}
	}
}

func TestResolveSQLitePathBuscaLaBaseDePython(t *testing.T) {
	existe := func(set ...string) func(string) bool {
		return func(p string) bool {
			for _, s := range set {
				if filepath.ToSlash(filepath.Clean(p)) == s {
					return true
				}
			}
			return false
		}
	}
	casos := []struct {
		nombre, ruta string
		hay          []string
		want         string
	}{
		{"absoluta Unix", "/tmp/a.db", nil, "/tmp/a.db"},
		{"absoluta Windows", "C:/datos/a.db", nil, "C:/datos/a.db"},
		{"relativa donde corre Go", "./pluvifor.db", []string{"pluvifor.db"}, "pluvifor.db"},
		{"relativa en el backend (desde apps/api-go)", "./pluvifor.db", []string{"../backend/pluvifor.db"}, "../backend/pluvifor.db"},
		{"relativa en el backend (desde la raíz)", "./pluvifor.db", []string{"apps/backend/pluvifor.db"}, "apps/backend/pluvifor.db"},
		{"no existe: queda la original", "./pluvifor.db", nil, "./pluvifor.db"},
	}
	for _, c := range casos {
		if got := filepath.ToSlash(filepath.Clean(ResolveSQLitePath(c.ruta, existe(c.hay...)))); got != filepath.ToSlash(filepath.Clean(c.want)) {
			t.Errorf("%s: %q, quería %q", c.nombre, got, c.want)
		}
	}
}
