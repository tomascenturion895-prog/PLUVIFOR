package dotenv

import (
	"os"
	"path/filepath"
	"testing"
)

func TestParseLine(t *testing.T) {
	casos := []struct {
		in, key, value string
		ok             bool
	}{
		{"A=1", "A", "1", true},
		{"  B = dos  ", "B", "dos", true},
		{`C="con espacios"`, "C", "con espacios", true},
		{"D='simple'", "D", "simple", true},
		{"export E=cinco", "E", "cinco", true},
		{"F=valor # comentario", "F", "valor", true},
		{"G=", "G", "", true},
		{"\ufeffH=bom", "H", "bom", true},
		{"URL=sqlite:///./x.db", "URL", "sqlite:///./x.db", true},
		{"# comentario", "", "", false},
		{"", "", "", false},
		{"sin igual", "", "", false},
		{"=vacio", "", "", false},
		{"dos palabras=x", "", "", false},
	}
	for _, c := range casos {
		k, v, ok := parseLine(c.in)
		if ok != c.ok || k != c.key || v != c.value {
			t.Errorf("parseLine(%q) = %q, %q, %v; quería %q, %q, %v", c.in, k, v, ok, c.key, c.value, c.ok)
		}
	}
}

func TestLoadNoPisaElEntornoReal(t *testing.T) {
	path := filepath.Join(t.TempDir(), ".env")
	if err := os.WriteFile(path, []byte("YA=del_archivo\nNUEVA=si\n# nada\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	env := map[string]string{"YA": "del_entorno"}
	n := Load(path,
		func(k string) (string, bool) { v, ok := env[k]; return v, ok },
		func(k, v string) error { env[k] = v; return nil })
	if n != 1 || env["YA"] != "del_entorno" || env["NUEVA"] != "si" {
		t.Fatalf("n=%d env=%v: el entorno real debe ganar sobre el archivo", n, env)
	}
}

func TestLoadSinArchivoNoFalla(t *testing.T) {
	if n := Load(filepath.Join(t.TempDir(), "no-existe"), nil, nil); n != 0 {
		t.Fatalf("n = %d", n)
	}
}

func TestLoadNearestBuscaHaciaArriba(t *testing.T) {
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, ".env"), []byte("PLUVIFOR_PRUEBA_DOTENV=ok\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	deep := filepath.Join(root, "apps", "api-go")
	if err := os.MkdirAll(deep, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Chdir(deep)
	t.Setenv("PLUVIFOR_PRUEBA_DOTENV", "") // se restaura al terminar
	os.Unsetenv("PLUVIFOR_PRUEBA_DOTENV")
	path, n := LoadNearest()
	if path != filepath.Join(root, ".env") || n != 1 || os.Getenv("PLUVIFOR_PRUEBA_DOTENV") != "ok" {
		t.Fatalf("path=%q n=%d", path, n)
	}
}
