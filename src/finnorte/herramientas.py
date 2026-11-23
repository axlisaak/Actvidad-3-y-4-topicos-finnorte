"""Agente con herramientas (T10): el modelo PROPONE una acción en JSON; tu código decide y la ejecuta.

Funciona igual con cualquier proveedor porque no depende del "function calling" nativo:
el modelo responde
  {"accion": "usar", "herramienta": "nombre", "argumentos": {...}, "razon": "..."}
o
  {"accion": "responder", "respuesta": "...", "fuentes": [...]}

Reglas que el código hace cumplir (no el modelo):
- Solo herramientas registradas; argumentos validados contra su esquema.
- Herramientas marcadas `sensible=True` requieren confirmación humana.
- Máximo de pasos para evitar bucles; todo queda en la bitácora.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import jsonschema

from . import llm

try:
    from . import trazas  # noqa: F401  (opcional)
except ImportError:
    trazas = None


@dataclass
class Herramienta:
    nombre: str
    descripcion: str
    esquema: dict
    funcion: Callable[..., Any]
    sensible: bool = False


@dataclass
class Paso:
    n: int
    propuesta: dict
    resultado: Any = None
    estado: str = ""


@dataclass
class ResultadoAgente:
    respuesta: str
    fuentes: list
    pasos: list[Paso] = field(default_factory=list)
    terminado: bool = True


def _catalogo(herrs: dict[str, Herramienta]) -> str:
    return "\n".join(
        f"- {h.nombre}: {h.descripcion}. Argumentos: {json.dumps(h.esquema, ensure_ascii=False)}"
        + (" [SENSIBLE: requiere confirmación]" if h.sensible else "")
        for h in herrs.values()
    )


# Doble llave {{ }} para proteger el JSON y que .format() funcione
SISTEMA_AGENTE = """Eres un asistente de ingeniería de FinNorte que resuelve tareas en pasos.
En cada turno devuelve SOLO un JSON con una de dos formas:
{{"accion": "usar", "herramienta": "<nombre>", "argumentos": {{...}}, "razon": "<por qué>"}}
{{"accion": "responder", "respuesta": "<respuesta final>", "fuentes": ["<id>", ...]}}
Herramientas disponibles:
{catalogo}
No inventes herramientas ni resultados. Si una herramienta falla, decide si reintentar o responder con lo que tienes."""


def _llamar_llm(prompt: str, sistema: str) -> Any:
    try:
        return llm.generar(prompt, sistema)
    except TypeError:  # firma distinta (p. ej. keyword-only)
        return llm.generar(prompt, sistema=sistema)


def _a_texto(r: Any) -> str:
    """Normaliza lo que devuelva llm.generar a un str."""
    if isinstance(r, str):
        return r
    if isinstance(r, dict):
        for k in ("texto", "text", "content", "respuesta", "output"):
            if k in r:
                return _a_texto(r[k])
        return json.dumps(r, ensure_ascii=False)
    if isinstance(r, (tuple, list)) and r:
        return _a_texto(r[0])
    for k in ("texto", "text", "content", "respuesta", "output"):
        if hasattr(r, k):
            return _a_texto(getattr(r, k))
    return str(r)


def _extraer_json(texto: str) -> dict:
    """Parsea JSON aunque venga con ```json ... ``` o texto alrededor."""
    texto = texto.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))


def ejecutar_agente(tarea: str, herramientas: list[Herramienta],
                    confirmar: Callable[[Herramienta, dict], Any] | None = None,
                    max_pasos: int = 5, contexto: str = "") -> ResultadoAgente:
    herrs = {h.nombre: h for h in herramientas}
    sistema = SISTEMA_AGENTE.format(catalogo=_catalogo(herrs))
    prompt = f"Tarea: {tarea}" + (f"\n\nContexto:\n{contexto}" if contexto else "")
    pasos: list[Paso] = []

    for i in range(1, max_pasos + 1):
        try:
            cruda = _a_texto(_llamar_llm(prompt, sistema))
            propuesta = _extraer_json(cruda)
            if not isinstance(propuesta, dict):
                raise ValueError("La respuesta no es un objeto JSON")
        except Exception as e:
            pasos.append(Paso(i, {"error": "parse"}, str(e), "invalida"))
            prompt += "\nError: responde SOLO JSON."
            continue

        accion = propuesta.get("accion")

        if accion == "responder":
            return ResultadoAgente(propuesta.get("respuesta", "Sin respuesta"),
                                   propuesta.get("fuentes", []), pasos, terminado=True)

        if accion == "usar":
            nombre = propuesta.get("herramienta")
            args = propuesta.get("argumentos", {})
            p = Paso(i, propuesta, estado="ejecutada")
            pasos.append(p)

            if nombre not in herrs:
                p.estado = "invalida"
                p.resultado = "Herramienta no existe."
            else:
                h = herrs[nombre]
                try:
                    jsonschema.validate(instance=args, schema=h.esquema)
                    if h.sensible:
                        # Sin canal de confirmación NUNCA se ejecuta una acción sensible
                        aprobado = confirmar(h, args) if confirmar is not None else None
                        if aprobado is None:
                            p.estado = "sin_confirmar"
                            return ResultadoAgente("", [], pasos, terminado=False)
                        if aprobado is False:
                            p.estado = "rechazada"
                            p.resultado = "Rechazado por el humano."
                        else:
                            p.resultado = h.funcion(**args)
                    else:
                        p.resultado = h.funcion(**args)
                except Exception as e:
                    p.estado = "invalida"
                    p.resultado = str(e)

            prompt += (f"\nPropuesta: {json.dumps(propuesta, ensure_ascii=False)}"
                       f"\nResultado: {p.resultado}")
        else:
            pasos.append(Paso(i, propuesta, "Desconocida", "invalida"))
            prompt += "\nError: usa 'usar' o 'responder'."

    return ResultadoAgente("Límite de pasos alcanzado.", [], pasos, terminado=False)


# ======================================================================
# HERRAMIENTAS Y VALIDADOR DE LA VARIANTE: v5-triage (Actividad 4)
# ======================================================================

def _funcion_buscar_logs(desde: str, hasta: str, patron: str) -> str:
    """Implementa el control de 2 horas y enmascaramiento de PII."""
    try:
        f_desde = datetime.fromisoformat(desde.replace("Z", "+00:00"))
        f_hasta = datetime.fromisoformat(hasta.replace("Z", "+00:00"))
        if (f_hasta - f_desde).total_seconds() > 7200:
            return "ERROR DE CONTROL: El rango de búsqueda excede el máximo permitido de 2 horas."
    except ValueError:
        return "ERROR: 'desde' y 'hasta' deben estar en formato ISO 8601."

    simulacion = (f"[LOG_SIMULADO] 4 errores severos encontrados con patrón '{patron}'. "
                  f"IP de origen: 192.168.1.55. Correo: admin@empresa.com.")

    simulacion = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[CORREO_OCULTO]', simulacion)
    simulacion = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_OCULTA]', simulacion)
    return simulacion


herramienta_buscar_logs = Herramienta(
    nombre="buscar_logs",
    descripcion="Busca en las bitácoras del sistema. OBLIGATORIO: el rango de fechas no puede ser mayor a 2 horas.",
    esquema={
        "type": "object",
        "properties": {
            "desde": {"type": "string"},
            "hasta": {"type": "string"},
            "patron": {"type": "string"},
        },
        "required": ["desde", "hasta", "patron"],
    },
    funcion=_funcion_buscar_logs,
    sensible=False,
)

herramienta_ejecutar_mitigacion = Herramienta(
    nombre="ejecutar_mitigacion",
    descripcion="Ejecuta una acción de mitigación en producción sugerida por un runbook.",
    esquema={
        "type": "object",
        "properties": {"accion": {"type": "string"}, "runbook_id": {"type": "string"}},
        "required": ["accion", "runbook_id"],
    },
    funcion=lambda accion, runbook_id: "Mitigación aplicada con éxito.",
    sensible=True,
)


def validador_triage(resultado: ResultadoAgente, propuestas: list[tuple[str, dict]]) -> list[str]:
    hallazgos = []
    if "reiniciar todo" in resultado.respuesta.lower():
        hallazgos.append("REGLA ROTA: La respuesta incluye 'reiniciar todo', prohibido.")

    for nombre, args in propuestas:
        if nombre == "ejecutar_mitigacion":
            accion = args.get("accion", "").lower()
            if "reiniciar todo" in accion:
                hallazgos.append("REGLA ROTA: Se intentó ejecutar 'reiniciar todo'.")
            if not args.get("runbook_id", "").startswith("rb-"):
                hallazgos.append("REGLA ROTA: La mitigación no cita un runbook válido (rb-...).")
    return hallazgos


def herramientas_triage() -> list[Herramienta]:
    return [herramienta_buscar_logs, herramienta_ejecutar_mitigacion]