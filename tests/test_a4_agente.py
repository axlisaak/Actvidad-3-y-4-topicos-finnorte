import json

from finnorte import llm
from finnorte.herramientas import Herramienta, ejecutar_agente

SUMA = Herramienta("sumar", "Suma dos números",
                   {"type": "object", "required": ["a", "b"],
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
                   lambda a, b: a + b)
BORRAR = Herramienta("borrar_rama", "Borra una rama remota",
                     {"type": "object", "required": ["rama"],
                      "properties": {"rama": {"type": "string"}}},
                     lambda rama: f"borrada {rama}", sensible=True)


def _guion(*respuestas):
    it = iter(respuestas)

    def inner(p, s=None, *args, **kwargs):
        return json.dumps(next(it))
    return inner


def test_agente_usa_herramienta_y_responde():
    llm.fake.responder = _guion(
        {"accion": "usar", "herramienta": "sumar", "argumentos": {"a": 2, "b": 3}},
        {"accion": "responder", "respuesta": "Es 5", "fuentes": []})
    r = ejecutar_agente("¿Cuánto es 2+3?", [SUMA])
    assert r.respuesta == "Es 5" and r.pasos[0].resultado == 5


def test_herramienta_sensible_sin_confirmacion_no_se_ejecuta():
    ejecutadas = []
    h = Herramienta("borrar_rama", BORRAR.descripcion, BORRAR.esquema,
                    lambda rama: ejecutadas.append(rama), sensible=True)
    llm.fake.responder = _guion(
        {"accion": "usar", "herramienta": "borrar_rama", "argumentos": {"rama": "main"}},
        {"accion": "responder", "respuesta": "No se borró", "fuentes": []})
    r = ejecutar_agente("Borra main", [h], confirmar=lambda h, a: False)
    assert ejecutadas == [] and r.pasos[0].estado == "rechazada"


def test_herramienta_inexistente_es_invalida_y_hay_tope_de_pasos():
    llm.fake.responder = lambda p, s=None, *a, **k: json.dumps(
        {"accion": "usar", "herramienta": "hackear", "argumentos": {}})
    r = ejecutar_agente("x", [SUMA], max_pasos=3)
    assert not r.terminado and len(r.pasos) == 3 and all(p.estado == "invalida" for p in r.pasos)