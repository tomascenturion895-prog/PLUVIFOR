"""Servidor MCP de solo lectura (SCRUM-91): un hueco responde «sin dato», nunca 0, y no escribe."""

import io
import json
import re
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Validation
from app.models import RainfallRecord, Source, Station
from servidor_mcp.api import ErrorConsulta, LectorHttp, validar_base
from servidor_mcp.herramientas import HERRAMIENTAS, rotular_huecos
from servidor_mcp.servidor import PROTOCOLOS, ServidorMcp, servir

# ---------------------------------------------------------------------------
# Un lector falso: guarda lo que se le pidió y devuelve lo que le indiquen.
# ---------------------------------------------------------------------------


class LectorFalso:
    def __init__(self, respuesta=None, error=None):
        self.respuesta, self.error, self.pedidos = respuesta, error, []

    def get(self, ruta, parametros):
        self.pedidos.append((ruta, {k: v for k, v in parametros.items() if v is not None}))
        if self.error:
            raise self.error
        return self.respuesta


def rpc(servidor, metodo, params=None, id_=1):
    mensaje = {"jsonrpc": "2.0", "id": id_, "method": metodo}
    if params is not None:
        mensaje["params"] = params
    return servidor.procesar(mensaje)


def llamar(servidor, nombre, argumentos):
    return rpc(servidor, "tools/call", {"name": nombre, "arguments": argumentos})


def texto(respuesta) -> str:
    return respuesta["result"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# Protocolo
# ---------------------------------------------------------------------------


def test_initialize_negocia_la_version_y_se_presenta_como_solo_lectura():
    servidor = ServidorMcp(LectorFalso())
    r = rpc(servidor, "initialize", {"protocolVersion": "2024-11-05"})["result"]
    assert r["protocolVersion"] == "2024-11-05"
    assert r["capabilities"] == {"tools": {"listChanged": False}}
    assert "SOLO LECTURA" in r["instructions"] and "sin dato" in r["instructions"]
    assert "no es una herramienta oficial" in r["instructions"]
    desconocida = rpc(servidor, "initialize", {"protocolVersion": "1999-01-01"})["result"]
    assert desconocida["protocolVersion"] == PROTOCOLOS[0]


def test_una_notificacion_no_se_responde():
    servidor = ServidorMcp(LectorFalso())
    assert servidor.procesar({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_ping_y_metodos_que_no_existen():
    servidor = ServidorMcp(LectorFalso())
    assert rpc(servidor, "ping")["result"] == {}
    for metodo in ("resources/list", "prompts/list", "tools/delete", "resources/write"):
        assert rpc(servidor, metodo)["error"]["code"] == -32601


@pytest.mark.parametrize("basura", [[], "hola", 3, {"id": 1}, {"jsonrpc": "1.0", "id": 1}])
def test_un_mensaje_que_no_es_jsonrpc_se_rechaza(basura):
    assert ServidorMcp(LectorFalso()).procesar(basura)["error"]["code"] == -32600


# ---------------------------------------------------------------------------
# Solo lectura
# ---------------------------------------------------------------------------


def test_hay_cuatro_herramientas_y_todas_son_de_solo_lectura():
    tools = rpc(ServidorMcp(LectorFalso()), "tools/list")["result"]["tools"]
    assert [t["name"] for t in tools] == [
        "listar_estaciones",
        "lluvia_por_estacion",
        "acumulado",
        "comparar_estaciones",
    ]
    for t in tools:
        assert t["annotations"]["readOnlyHint"] is True
        assert t["annotations"]["destructiveHint"] is False
        assert t["inputSchema"]["additionalProperties"] is False
        assert t["description"]


def test_ninguna_herramienta_promete_escribir():
    verbos = re.compile(r"crear|borrar|eliminar|importar|cargar|escribir|guardar|actualizar|enviar")
    for h in HERRAMIENTAS:
        assert not verbos.search(h.nombre), h.nombre


def test_el_lector_real_solo_sabe_consultar():
    publicos = {m for m in dir(LectorHttp) if not m.startswith("_")}
    assert publicos == {"get"}


def test_toda_herramienta_consulta_solo_rutas_de_lectura_de_la_api():
    lector = LectorFalso({})
    servidor = ServidorMcp(lector)
    base = {"desde": "2026-01-01", "hasta": "2026-01-31"}
    llamar(servidor, "listar_estaciones", {})
    llamar(servidor, "lluvia_por_estacion", {**base, "estacion_id": 2})
    llamar(servidor, "acumulado", base)
    llamar(servidor, "comparar_estaciones", {**base, "estacion_ids": [2, 3]})
    rutas = [ruta for ruta, _ in lector.pedidos]
    assert rutas == [
        "/api/stations",
        "/api/rainfall",
        "/api/rainfall/accumulated",
        "/api/rainfall/compare",
    ]
    assert not any("import" in r or "field-reports" in r or "sensor" in r for r in rutas)


# ---------------------------------------------------------------------------
# Un hueco no es 0 mm
# ---------------------------------------------------------------------------

SERIE = {
    "station_id": 2,
    "category": "observado",
    "days": [
        {"obs_date": "2016-01-01", "state": "dato", "mm": 12.5, "source": "siga_inta", "flags": []},
        {"obs_date": "2016-01-02", "state": "dato", "mm": 0.0, "source": "siga_inta", "flags": []},
        {
            "obs_date": "2016-01-03",
            "state": "sin_fila",
            "mm": None,
            "source": "siga_inta",
            "flags": [],
        },
        {
            "obs_date": "2016-01-04",
            "state": "fila_sin_valor",
            "mm": None,
            "source": "siga_inta",
            "flags": [],
        },
    ],
    "summary": {"days_with_data": 2, "accumulated_mm": 12.5},
    "warnings": [{"code": "ceros_prolongados", "message": "m", "severity": "alerta"}],
}


def test_rotular_huecos_no_cambia_numeros_y_dice_sin_dato():
    r = rotular_huecos(SERIE)
    dias = {d["obs_date"]: d for d in r["days"]}
    assert dias["2016-01-01"]["mm_texto"] == "12.5 mm"
    assert dias["2016-01-02"]["mm"] == 0.0 and dias["2016-01-02"]["mm_texto"] == "0 mm"  # medido
    for hueco in ("2016-01-03", "2016-01-04"):
        assert dias[hueco]["mm"] is None and dias[hueco]["mm_texto"] == "sin dato"
    assert r["summary"]["accumulated_mm_texto"] == "12.5 mm"
    assert r["warnings"] == SERIE["warnings"]


def test_la_respuesta_de_una_serie_con_huecos_nunca_los_presenta_como_cero():
    servidor = ServidorMcp(LectorFalso(SERIE))
    r = llamar(
        servidor,
        "lluvia_por_estacion",
        {"estacion_id": 2, "desde": "2016-01-01", "hasta": "2016-01-04"},
    )
    assert r["result"]["isError"] is False
    cuerpo = json.loads(texto(r))
    assert "no es una herramienta oficial" in cuerpo["leyenda"]
    assert "NO es 0 mm" in cuerpo["nota"]
    huecos = [d for d in cuerpo["resultado"]["days"] if d["state"] != "dato"]
    assert len(huecos) == 2
    assert all(d["mm"] is None and d["mm_texto"] == "sin dato" for d in huecos)
    assert cuerpo["resultado"]["days"][2]["source"] == "siga_inta"  # trae fuente y estado
    assert cuerpo["resultado"]["warnings"][0]["code"] == "ceros_prolongados"


def test_un_acumulado_sin_ningun_dato_es_sin_dato_no_cero():
    vacio = {"stations": [{"station_id": 2, "accumulated_mm": None, "days_with_data": 0}]}
    r = llamar(
        ServidorMcp(LectorFalso(vacio)), "acumulado", {"desde": "2017-01-01", "hasta": "2017-01-05"}
    )
    estacion = json.loads(texto(r))["resultado"]["stations"][0]
    assert estacion["accumulated_mm"] is None
    assert estacion["accumulated_mm_texto"] == "sin dato"


# ---------------------------------------------------------------------------
# Argumentos y errores
# ---------------------------------------------------------------------------

BASE = {"estacion_id": 2, "desde": "2016-01-01", "hasta": "2016-01-10"}


@pytest.mark.parametrize(
    "argumentos",
    [
        {k: v for k, v in BASE.items() if k != "desde"},
        {**BASE, "desde": "2016-13-45"},
        {**BASE, "desde": "ayer"},
        {**BASE, "desde": "2016-02-01", "hasta": "2016-01-01"},
        {**BASE, "estacion_id": 0},
        {**BASE, "estacion_id": "2"},
        {**BASE, "estacion_id": True},
        {**BASE, "estacion_id": 2**40},
        {**BASE, "categoria": "inventada"},
        {**BASE, "mm": 0},  # argumento que no existe
    ],
)
def test_argumentos_invalidos_se_rechazan_sin_consultar_la_api(argumentos):
    lector = LectorFalso({})
    r = llamar(ServidorMcp(lector), "lluvia_por_estacion", argumentos)
    assert r["result"]["isError"] is True and texto(r)
    assert lector.pedidos == []


def test_comparar_valida_la_lista_de_estaciones():
    lector = LectorFalso({})
    servidor = ServidorMcp(lector)
    for ids in ([], "2,3", [2, "3"], [0], list(range(1, 22))):
        r = llamar(
            servidor,
            "comparar_estaciones",
            {"estacion_ids": ids, "desde": "2016-01-01", "hasta": "2016-01-10"},
        )
        assert r["result"]["isError"] is True, ids
    assert lector.pedidos == []


def test_se_pasan_los_parametros_de_la_api_con_sus_nombres():
    lector = LectorFalso({})
    servidor = ServidorMcp(lector)
    llamar(servidor, "lluvia_por_estacion", {**BASE, "categoria": "estimado"})
    llamar(servidor, "listar_estaciones", {"texto": "colorado", "limite": 5})
    llamar(
        servidor,
        "comparar_estaciones",
        {"estacion_ids": [2, 3], "desde": "2016-01-01", "hasta": "2016-01-10"},
    )
    assert lector.pedidos[0] == (
        "/api/rainfall",
        {"station_id": 2, "from": "2016-01-01", "to": "2016-01-10", "category": "estimado"},
    )
    assert lector.pedidos[1] == ("/api/stations", {"q": "colorado", "limit": 5})
    assert lector.pedidos[2][1]["station_ids"] == "2,3"


def test_una_herramienta_desconocida_es_un_error_de_protocolo():
    assert llamar(ServidorMcp(LectorFalso()), "borrar_todo", {})["error"]["code"] == -32602


def test_un_error_de_la_api_se_informa_en_español_como_error_de_la_herramienta():
    lector = LectorFalso(
        error=ErrorConsulta("No se pudo conectar con la API en http://x. ¿Está levantada?")
    )
    r = llamar(ServidorMcp(lector), "lluvia_por_estacion", BASE)
    assert r["result"]["isError"] is True and "¿Está levantada?" in texto(r)


def test_un_fallo_inesperado_no_filtra_detalles_internos():
    lector = LectorFalso(error=RuntimeError("secreto: /home/x/clave.txt"))
    r = llamar(ServidorMcp(lector), "lluvia_por_estacion", BASE)
    assert r["result"]["isError"] is True
    assert texto(r) == "Ocurrió un error inesperado." and "secreto" not in json.dumps(r)


# ---------------------------------------------------------------------------
# stdio
# ---------------------------------------------------------------------------


def test_servir_responde_una_linea_por_peticion_y_ninguna_por_notificacion():
    entrada = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                "",
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                "esto no es json",
            ]
        )
    )
    salida = io.StringIO()
    servir(entrada, salida, ServidorMcp(LectorFalso()))
    lineas = [json.loads(x) for x in salida.getvalue().splitlines()]
    assert [x.get("id") for x in lineas] == [1, 2, None]
    assert lineas[2]["error"]["code"] == -32700
    assert salida.getvalue().isascii()  # sirve con cualquier consola, también la de Windows


# ---------------------------------------------------------------------------
# Lector HTTP real contra un servidor local
# ---------------------------------------------------------------------------


@pytest.fixture
def api_local():
    pedidos = []

    class Manejador(BaseHTTPRequestHandler):
        def _responder(self):
            pedidos.append((self.command, self.path))
            if self.path.startswith("/api/error"):
                codigo, cuerpo = (
                    422,
                    {"error": {"code": "x", "message": "Elegí un período válido."}},
                )
            elif self.path.startswith("/api/roto"):
                codigo, cuerpo = 500, {"error": {"code": "i", "message": "detalle interno"}}
            else:
                codigo, cuerpo = 200, {"ok": True}
            datos = json.dumps(cuerpo).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        do_GET = do_POST = do_PUT = do_DELETE = _responder

        def log_message(self, *args):
            pass

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_port}", pedidos
    servidor.shutdown()
    servidor.server_close()


def test_el_lector_http_hace_solo_get_y_arma_la_consulta(api_local):
    base, pedidos = api_local
    lector = LectorHttp(base + "/")
    assert lector.get("/api/rainfall", {"station_id": 2, "from": "2016-01-01", "zone": None}) == {
        "ok": True
    }
    assert pedidos == [("GET", "/api/rainfall?station_id=2&from=2016-01-01")]


def test_el_lector_http_traduce_los_errores_de_la_api(api_local):
    base, _ = api_local
    lector = LectorHttp(base)
    with pytest.raises(ErrorConsulta, match="Elegí un período válido"):
        lector.get("/api/error", {})
    with pytest.raises(ErrorConsulta) as interno:
        lector.get("/api/roto", {})
    assert "detalle interno" not in str(interno.value) and "500" in str(interno.value)


def test_sin_api_levantada_el_mensaje_orienta():
    with pytest.raises(ErrorConsulta, match="¿Está levantada\\?"):
        LectorHttp("http://127.0.0.1:9").get("/api/stations", {})


@pytest.mark.parametrize("base", ["", "ftp://x", "file:///etc/passwd", "localhost:8000"])
def test_la_direccion_de_la_api_tiene_que_ser_http(base):
    with pytest.raises(ValueError):
        validar_base(base)


# ---------------------------------------------------------------------------
# De punta a punta con la API real y la base de pruebas
# ---------------------------------------------------------------------------


class LectorDeLaApi:
    """Usa la aplicación FastAPI de las pruebas como si fuera la API por HTTP."""

    def __init__(self, client: TestClient):
        self._client = client

    def get(self, ruta, parametros):
        r = self._client.get(ruta, params={k: v for k, v in parametros.items() if v is not None})
        if r.status_code >= 400:
            raise ErrorConsulta(r.json()["error"]["message"])
        return r.json()


@pytest.fixture
def estacion(db: Session) -> int:
    fuente = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    db.add(fuente)
    db.flush()
    est = Station(source_id=fuente.id, code="424", name="El Colorado")
    db.add(est)
    db.flush()
    plan = [
        (RainState.DATO, 12.5),
        (RainState.DATO, 0.0),
        (RainState.SIN_FILA, None),
        (RainState.FILA_SIN_VALOR, None),
    ]
    for i, (estado, mm) in enumerate(plan):
        db.add(
            RainfallRecord(
                station_id=est.id,
                obs_date=date(2016, 1, 1) + timedelta(days=i),
                state=estado,
                mm=mm,
                category=DataCategory.OBSERVADO,
                validation=Validation.VALIDADO,
            )
        )
    db.commit()
    return est.id


def test_de_punta_a_punta_un_periodo_sin_datos_responde_sin_dato(client, estacion):
    servidor = ServidorMcp(LectorDeLaApi(client))
    r = llamar(
        servidor,
        "lluvia_por_estacion",
        {"estacion_id": estacion, "desde": "2017-01-01", "hasta": "2017-01-05"},
    )
    assert r["result"]["isError"] is False
    cuerpo = json.loads(texto(r))["resultado"]
    assert len(cuerpo["days"]) == 5
    assert all(d["mm"] is None and d["mm_texto"] == "sin dato" for d in cuerpo["days"])
    assert all(d["state"] == "sin_fila" for d in cuerpo["days"])
    assert cuerpo["summary"]["accumulated_mm"] is None
    assert '"mm": 0' not in texto(r)

    acum = llamar(
        servidor,
        "acumulado",
        {"desde": "2017-01-01", "hasta": "2017-01-05", "estacion_id": estacion},
    )
    est = json.loads(texto(acum))["resultado"]["stations"][0]
    assert est["accumulated_mm"] is None and est["accumulated_mm_texto"] == "sin dato"


def test_de_punta_a_punta_distingue_el_cero_medido_del_hueco(client, estacion):
    servidor = ServidorMcp(LectorDeLaApi(client))
    r = llamar(
        servidor,
        "lluvia_por_estacion",
        {"estacion_id": estacion, "desde": "2016-01-01", "hasta": "2016-01-04"},
    )
    dias = {d["obs_date"]: d for d in json.loads(texto(r))["resultado"]["days"]}
    assert (dias["2016-01-01"]["mm"], dias["2016-01-01"]["state"]) == (12.5, "dato")
    assert (dias["2016-01-02"]["mm"], dias["2016-01-02"]["mm_texto"]) == (0.0, "0 mm")
    assert (dias["2016-01-03"]["mm"], dias["2016-01-03"]["state"]) == (None, "sin_fila")
    assert (dias["2016-01-04"]["mm"], dias["2016-01-04"]["state"]) == (None, "fila_sin_valor")
    assert dias["2016-01-03"]["mm_texto"] == dias["2016-01-04"]["mm_texto"] == "sin dato"


def test_de_punta_a_punta_un_rechazo_de_la_api_llega_en_español(client, estacion):
    servidor = ServidorMcp(LectorDeLaApi(client))
    r = llamar(
        servidor,
        "lluvia_por_estacion",
        {"estacion_id": 999999, "desde": "2016-01-01", "hasta": "2016-01-04"},
    )
    assert r["result"]["isError"] is True and texto(r)
