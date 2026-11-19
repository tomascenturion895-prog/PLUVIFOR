//go:build !sqlite

package sqlstore

// DriverName está vacío: este binario no trae driver y la API reenvía a Python.
const DriverName = ""
