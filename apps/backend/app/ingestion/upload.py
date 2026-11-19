"""Controles de un archivo subido antes de leerlo. Un archivo es una entrada no confiable."""

from pathlib import PurePath

from app.ingestion.types import InvalidFileError, UploadTooLargeError

DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Firmas de formatos binarios que no son CSV aunque se llamen «.csv».
_BINARY_SIGNATURES = (
    b"PK\x03\x04",  # zip, xlsx, docx
    b"%PDF",
    b"MZ",  # ejecutables de Windows
    b"\x7fELF",
    b"\x89PNG",
    b"GIF8",
    b"\xff\xd8\xff",  # jpeg
    b"\xd0\xcf\x11\xe0",  # xls y doc antiguos
    b"\x1f\x8b",  # gzip
    b"SQLite format 3",
)


def check_upload(filename: str, content: bytes, max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES) -> None:
    """Rechaza lo que no es un CSV de texto razonable. No interpreta el contenido."""
    name = PurePath(filename.replace("\\", "/")).name
    if not name.lower().endswith(".csv"):
        raise InvalidFileError("Solo se aceptan archivos .csv.")
    if not content.strip():
        raise InvalidFileError("El archivo está vacío.")
    if len(content) > max_bytes:
        raise UploadTooLargeError(
            f"El archivo supera el máximo permitido de {max_bytes // (1024 * 1024)} MB."
        )
    if b"\x00" in content or content.startswith(_BINARY_SIGNATURES):
        raise InvalidFileError("El contenido no es un CSV de texto.")
