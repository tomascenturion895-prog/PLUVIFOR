//go:build sqlite

package sqlstore

// Driver de SQLite en Go puro (sin cgo). Es el único archivo que conoce el driver elegido: cambiarlo
// por otro es cambiar esta línea y el nombre. Se compila con `-tags sqlite`.
import (
	_ "github.com/ncruces/go-sqlite3/driver"
	_ "github.com/ncruces/go-sqlite3/embed" // trae el binario de SQLite dentro del programa
)

// DriverName es el nombre con el que el driver se registra en database/sql.
const DriverName = "sqlite3"
