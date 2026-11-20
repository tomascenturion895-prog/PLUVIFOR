// Package dotenv carga un archivo .env a las variables de entorno, con solo la biblioteca estándar.
// Lo que ya está definido en el entorno real gana sobre el archivo. Nunca imprime valores: un .env
// puede llevar claves.
package dotenv

import (
	"bufio"
	"os"
	"path/filepath"
	"strings"
)

// maxLevels es cuántas carpetas hacia arriba se busca el .env (desde apps/api-go llega a la raíz).
const maxLevels = 3

// LoadNearest busca un .env en la carpeta actual y en las de arriba, y carga el primero que
// encuentra. Devuelve la ruta cargada ("" si no había ninguno) y cuántas variables nuevas definió.
func LoadNearest() (path string, loaded int) {
	dir, err := os.Getwd()
	if err != nil {
		return "", 0
	}
	for i := 0; i <= maxLevels; i++ {
		candidate := filepath.Join(dir, ".env")
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			return candidate, Load(candidate, os.LookupEnv, os.Setenv)
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return "", 0
}

// Load lee el archivo y define cada variable que todavía no existe. Devuelve cuántas definió.
func Load(path string, lookup func(string) (string, bool), set func(key, value string) error) int {
	f, err := os.Open(path)
	if err != nil {
		return 0
	}
	defer f.Close()
	n := 0
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		key, value, ok := parseLine(sc.Text())
		if !ok {
			continue
		}
		if _, exists := lookup(key); exists {
			continue
		}
		if set(key, value) == nil {
			n++
		}
	}
	return n
}

// parseLine entiende CLAVE=valor, con "export " opcional, comillas simples o dobles y comentarios
// de línea completa. Una línea vacía o sin "=" se ignora.
func parseLine(line string) (key, value string, ok bool) {
	line = strings.TrimSpace(strings.TrimPrefix(line, "\ufeff")) // Windows puede agregar una marca BOM
	if line == "" || strings.HasPrefix(line, "#") {
		return "", "", false
	}
	line = strings.TrimSpace(strings.TrimPrefix(line, "export "))
	key, value, found := strings.Cut(line, "=")
	key = strings.TrimSpace(key)
	if !found || key == "" || strings.ContainsAny(key, " \t") {
		return "", "", false
	}
	value = strings.TrimSpace(value)
	if len(value) >= 2 && (value[0] == '"' || value[0] == '\'') && value[len(value)-1] == value[0] {
		return key, value[1 : len(value)-1], true
	}
	if i := strings.Index(value, " #"); i >= 0 { // comentario al final de la línea
		value = strings.TrimSpace(value[:i])
	}
	return key, value, true
}
