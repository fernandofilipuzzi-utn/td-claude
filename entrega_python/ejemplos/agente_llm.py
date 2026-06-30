#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agente_llm.py — Agente de decisión FIR/IIR vía API LLM (Claude), Paso 4.

Propósito
---------
Estrategia 4 del agente: se DELEGA la decisión FIR/IIR a un modelo de lenguaje
(familia Claude) accedido por la API de Anthropic. Se construye un system prompt
con el rol + criterios de ingeniería y un user prompt estructurado con las
variables del caso; se pide salida JSON estricta:
    {recomendacion, estructura, justificacion, confianza}
y se valida con json.loads + comprobaciones.

IMPORTANTE (fase de diseño, NO tiempo real):
  - Esta estrategia es útil para EXPLORAR/JUSTIFICAR/DOCUMENTAR en la fase de
    diseño. NO es apta para el microcontrolador en tiempo real: cada llamada
    tiene latencia (cientos de ms a segundos), coste por tokens y es NO
    determinista. En el µC se usa el agente de reglas (ver agente_decision.py).

Seguridad:
  - La API key se lee SOLO de os.environ['ANTHROPIC_API_KEY']; NUNCA se escribe
    en el código. El SDK Anthropic la toma automáticamente del entorno.
  - Si falta el SDK 'anthropic' o la variable de entorno, se imprimen
    instrucciones y se sale limpiamente (sin trazas ni claves).

Ejecutar:  python agente_llm.py
"""

from __future__ import annotations

import json
import os
import sys

# Modelo de la familia Claude actual. claude-opus-4-8 = máxima capacidad;
# claude-haiku-4-5 = más rápido y económico (elegir según coste/latencia).
MODELO = "claude-opus-4-8"          # alternativa: "claude-haiku-4-5"
MAX_TOKENS = 1024

# Import guardado del SDK opcional: la parte de reglas (agente_decision.py)
# funciona sin él; aquí solo lo necesitamos para llamar a la API.
try:
    from anthropic import Anthropic
    _ANTHROPIC_OK = True
except ImportError:  # pragma: no cover - depende del entorno
    _ANTHROPIC_OK = False


# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "Eres un especialista en procesamiento digital de señales (PDS). Dadas las "
    "restricciones de un sistema embebido, recomiendas FIR o IIR y una estructura "
    "de realización (DF I, DF II, SOS o lattice).\n\n"
    "Criterios obligatorios:\n"
    "- Fase lineal estricta (preservar morfología, p.ej. ECG) => FIR.\n"
    "- RAM < 2 kB con orden FIR > 50 => IIR.\n"
    "- Estabilidad numérica crítica sin FPU/float => IIR en SOS.\n"
    "- Transición estrecha con cómputo suficiente => IIR (p.ej. Elíptico) de orden adecuado.\n\n"
    "Devuelve ÚNICAMENTE un objeto JSON válido, sin texto adicional ni vallas de "
    "código, con EXACTAMENTE estas claves: recomendacion (FIR|IIR), estructura "
    "(DF I|DF II|SOS|lattice), justificacion (texto), confianza (número 0-1)."
)


def construir_user_prompt(specs: dict) -> str:
    """Inyecta las variables del caso en un user prompt estructurado."""
    return (
        "Restricciones del caso (JSON):\n"
        + json.dumps(specs, ensure_ascii=False, indent=2)
        + "\n\nRecomienda FIR o IIR y la estructura; responde solo con el JSON pedido."
    )


# ----------------------------------------------------------------------------
# Validación de la salida del modelo
# ----------------------------------------------------------------------------
def validar_salida(texto: str) -> dict:
    """Parsea y valida el JSON devuelto por el modelo.

    Lanza ValueError si el JSON no es parseable o no cumple el esquema. El LLM
    es NO determinista, por eso se valida siempre (alucinaciones/formato).
    """
    # Por robustez, si el modelo envolviera en ```json ... ```, lo limpiamos.
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = limpio.strip("`")
        if limpio.lower().startswith("json"):
            limpio = limpio[4:]
        limpio = limpio.strip()

    try:
        data = json.loads(limpio)
    except json.JSONDecodeError as exc:
        raise ValueError(f"El modelo no devolvió JSON válido: {exc}") from exc

    if data.get("recomendacion") not in {"FIR", "IIR"}:
        raise ValueError("recomendacion debe ser 'FIR' o 'IIR'")
    if not isinstance(data.get("estructura"), str):
        raise ValueError("estructura debe ser texto")
    try:
        conf = float(data.get("confianza"))
    except (TypeError, ValueError) as exc:
        raise ValueError("confianza debe ser un número 0-1") from exc
    if not 0.0 <= conf <= 1.0:
        raise ValueError("confianza fuera de rango [0,1]")
    data["confianza"] = conf
    return data


# ----------------------------------------------------------------------------
# Llamada al LLM
# ----------------------------------------------------------------------------
def recomendar_llm(specs: dict, modelo: str = MODELO) -> dict:
    """Llama a la API de Claude y devuelve la recomendación validada.

    Requiere el SDK 'anthropic' y ANTHROPIC_API_KEY en el entorno.
    """
    # Anthropic() toma la clave de ANTHROPIC_API_KEY automáticamente. No se
    # hardcodea la clave en ningún punto.
    client = Anthropic()
    msg = client.messages.create(
        model=modelo,
        max_tokens=MAX_TOKENS,
        # Thinking adaptativo: el modelo decide cuánto razonar (familia 4.6+).
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": construir_user_prompt(specs)}],
    )
    # Tomamos el primer bloque de tipo 'text' (puede haber bloques 'thinking').
    texto = next((b.text for b in msg.content if b.type == "text"), "")
    return validar_salida(texto)


# ----------------------------------------------------------------------------
# Comprobación de prerrequisitos y salida limpia si faltan
# ----------------------------------------------------------------------------
def prerrequisitos_ok() -> bool:
    """Verifica SDK y API key; imprime instrucciones si falta algo."""
    if not _ANTHROPIC_OK:
        print("[agente_llm] El SDK 'anthropic' no está instalado.")
        print("  Instálelo en su entorno virtual:")
        print("    pip install anthropic")
        return False
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[agente_llm] Falta la variable de entorno ANTHROPIC_API_KEY.")
        print("  Expórtela ANTES de ejecutar (no se escribe en el código):")
        print("    Windows PowerShell:  $env:ANTHROPIC_API_KEY = '<su_clave>'")
        print("    Linux/macOS (bash):  export ANTHROPIC_API_KEY='<su_clave>'")
        return False
    return True


# Escenario de ejemplo (caso ECG, coherente con 05-agente-ia.md).
ESCENARIO_DEMO = {
    "aplicacion": "ECG",
    "fs_Hz": 500,
    "fase_lineal": True,
    "ram_kB": 8,
    "mips": 80,
    "snr_in_dB": 12,
    "latencia": "media",
    "transicion": "amplia",
}


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("AGENTE LLM (Claude) — recomendación FIR/IIR (fase de DISEÑO)")
    print("=" * 70)
    print("Recordatorio: latencia + coste + no-determinismo => NO para el µC en")
    print("tiempo real; úselo para explorar/justificar/documentar el diseño.\n")

    if not prerrequisitos_ok():
        # Salida limpia: no es un error del script, faltan prerrequisitos.
        sys.exit(0)

    print(f"Modelo: {MODELO}")
    print(f"Escenario de entrada:\n{json.dumps(ESCENARIO_DEMO, ensure_ascii=False, indent=2)}\n")

    try:
        salida = recomendar_llm(ESCENARIO_DEMO)
    except Exception as exc:  # noqa: BLE001 - reportamos cualquier fallo de red/API
        print(f"[agente_llm] La llamada o la validación falló: {exc}")
        print("  Sugerencia: reintentar o caer a las reglas IF-THEN de respaldo")
        print("  (ver agente_decision.recomendar_reglas).")
        sys.exit(1)

    print("Salida del modelo (JSON validado):")
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    print(f"\n=> Recomendación: {salida['recomendacion']} / {salida['estructura']} "
          f"(confianza {salida['confianza']:.2f})")


if __name__ == "__main__":
    main()
