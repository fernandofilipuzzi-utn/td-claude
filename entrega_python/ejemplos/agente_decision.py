#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agente_decision.py — Agente de decisión FIR/IIR (Paso 4).

Propósito
---------
Implementa el agente de decisión del Paso 4 con DOS estrategias en un solo
archivo:

  1. Reglas IF-THEN puras (sistema experto): ``recomendar_reglas(specs)``.
     SOLO usa la biblioteca estándar (sin numpy/scipy/sklearn) -> es el núcleo
     embebible y portátil. Codifica R1–R7 (las R1–R4 son las reglas de
     referencia del enunciado).

  2. Árbol de decisión (scikit-learn): genera un dataset sintético etiquetado
     por las MISMAS reglas, entrena un ``DecisionTreeClassifier`` y muestra las
     reglas aprendidas con ``export_text``. El import de sklearn/numpy está
     guardado en try/except: si no están instalados, se avisa y se continúa.

El ``main`` valida los 3 escenarios del KB (05-agente-ia.md §9):
  (a) ECG fase lineal estricta -> FIR / DF
  (b) Arduino UNO (2 kB, sin FPU, ordenFIR>50) -> IIR / SOS
  (c) ESP32 transición estrecha + FPU -> IIR (elíptico) / SOS

Ejecutar:  python agente_decision.py
"""

from __future__ import annotations

# Imports de la stdlib SOLAMENTE para el bloque de reglas (sin dependencias).
from dataclasses import dataclass, field

# ----------------------------------------------------------------------------
# Estructuras de E/S del agente
# ----------------------------------------------------------------------------
# specs (entrada) es un dict con las variables del Paso 4. Claves esperadas:
#   fs              : float  (Hz)
#   ram_kB          : float  (kB de RAM del µC)
#   mhz             : float  (frecuencia de reloj / MIPS aprox)
#   fpu             : bool   (¿tiene unidad de punto flotante?)
#   fase_lineal     : bool   (¿se exige fase lineal estricta?)
#   snr_in_dB       : float  (SNR de entrada)
#   latencia        : str    ('baja' | 'media' | 'alta')
#   transicion      : str    ('estrecha' | 'amplia')
#   orden_fir_est   : int    (orden FIR estimado para cumplir la máscara)


@dataclass
class Resultado:
    """Salida del agente: familia, estructura, justificación y confianza."""
    tipo: str = "INDEFINIDO"          # 'FIR' | 'IIR'
    estructura: str = "INDEFINIDO"    # 'DF' | 'DFII' | 'SOS' | 'lattice'
    justificacion: str = ""
    confianza: float = 0.0
    reglas_activadas: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "estructura": self.estructura,
            "justificacion": self.justificacion,
            "confianza": self.confianza,
            "reglas_activadas": self.reglas_activadas,
        }


# ----------------------------------------------------------------------------
# Estrategia 1 — Sistema experto de reglas IF-THEN (stdlib pura)
# ----------------------------------------------------------------------------
def recomendar_reglas(specs: dict) -> dict:
    """Aplica reglas IF-THEN priorizadas y devuelve la recomendación.

    Motor de inferencia con encadenamiento hacia adelante: las reglas se evalúan
    por prioridad (alta -> baja); la PRIMERA que dispara fija familia/estructura
    /confianza, pero todas las que se cumplen quedan registradas para trazar la
    decisión. R7 es la red de seguridad (FIR por defecto).

    Reglas (05-agente-ia.md §2.3):
      R1  fase_lineal estricta                       -> FIR / DF      (0.95)
      R2  ram < 2 kB Y orden_fir > 50                -> IIR / SOS     (0.90)
      R3  estabilidad crítica sin FPU (orden_fir>30) -> IIR / SOS     (0.90)
      R4  transición estrecha Y cómputo suficiente   -> IIR / SOS     (0.85)
      R5  latencia baja Y FIR de orden alto inviable -> IIR / DFII    (0.70)
      R6  FPU Y transición amplia Y fase deseada     -> FIR / DF      (0.80)
      R7  ninguna anterior                           -> FIR / DF      (0.50)
    """
    # Extracción con valores por defecto sensatos.
    ram = float(specs.get("ram_kB", 256))
    mhz = float(specs.get("mhz", 240))
    fpu = bool(specs.get("fpu", True))
    fase_lineal = bool(specs.get("fase_lineal", False))
    transicion = str(specs.get("transicion", "amplia")).lower()
    latencia = str(specs.get("latencia", "media")).lower()
    orden_fir = int(specs.get("orden_fir_est", 0))

    res = Resultado()

    def fijar(regla: str, tipo: str, estructura: str, conf: float, just: str):
        """Registra la regla; fija la salida solo si aún está INDEFINIDA."""
        res.reglas_activadas.append(regla)
        if res.tipo == "INDEFINIDO":
            res.tipo = tipo
            res.estructura = estructura
            res.confianza = conf
            res.justificacion = just

    computo_suficiente = fpu or mhz >= 80

    # R1 — fase lineal estricta -> FIR (preserva morfología, p.ej. P-QRS-T)
    if fase_lineal and not (ram < 2 and orden_fir > 50):
        fijar("R1", "FIR", "DF", 0.95,
              "Fase lineal estricta: solo el FIR (h[n] simétrico) la garantiza; "
              "preserva la morfología de la señal.")
    # R2 — poca RAM + FIR de orden alto -> IIR SOS
    if ram < 2 and orden_fir > 50:
        fijar("R2", "IIR", "SOS", 0.90,
              "RAM < 2 kB con orden FIR > 50: el FIR es inviable; el IIR logra "
              "igual selectividad con orden bajo (SOS por estabilidad).")
    # R3 — estabilidad crítica sin float -> IIR SOS
    if (not fpu) and orden_fir > 30:
        fijar("R3", "IIR", "SOS", 0.90,
              "Sin FPU/float y orden FIR alto: estabilidad numérica crítica -> "
              "IIR en cascada SOS (biquads), robusta a la cuantización.")
    # R4 — transición estrecha + cómputo suficiente -> IIR (elíptico) SOS
    if transicion == "estrecha" and computo_suficiente:
        fijar("R4", "IIR", "SOS", 0.85,
              "Transición estrecha con cómputo suficiente: IIR de orden adecuado "
              "(prototipo elíptico) da la pendiente más abrupta; SOS asegura "
              "estabilidad.")
    # R5 — latencia baja + FIR de orden alto -> IIR (menor retardo de grupo)
    if latencia == "baja" and orden_fir > 64:
        fijar("R5", "IIR", "DFII", 0.70,
              "Latencia baja con FIR de orden alto: el IIR tiene menor retardo "
              "de grupo para la misma selectividad.")
    # R6 — FPU + transición amplia + fase deseada -> FIR
    if fpu and transicion == "amplia" and fase_lineal:
        fijar("R6", "FIR", "DF", 0.80,
              "Plataforma con FPU y transición amplia con fase lineal deseada: "
              "FIR por ventana/Parks-McClellan, el cómputo absorbe el orden.")
    # R7 — red de seguridad
    if res.tipo == "INDEFINIDO":
        fijar("R7", "FIR", "DF", 0.50,
              "Ninguna regla específica disparó: FIR por defecto (simple y "
              "siempre estable).")

    return res.as_dict()


# ----------------------------------------------------------------------------
# Estrategia 2 — Árbol de decisión (scikit-learn, opcional)
# ----------------------------------------------------------------------------
# Imports pesados/opcionales guardados: la parte de reglas funciona sin ellos.
try:
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.model_selection import train_test_split
    _SKLEARN_OK = True
except ImportError:  # pragma: no cover - depende del entorno
    _SKLEARN_OK = False


_FEATURES = ["fase_lineal", "ram_kB", "mhz", "fpu", "transicion_estrecha", "orden_fir"]


def _etiqueta_por_reglas(fase_lin, ram, mhz, fpu, trans_estrecha, orden_fir) -> int:
    """Etiqueta sintética (1 = FIR, 0 = IIR) con las mismas reglas de ingeniería."""
    if fase_lin and not (ram < 2 and orden_fir > 50):
        return 1                                   # R1 -> FIR
    if ram < 2 and orden_fir > 50:
        return 0                                   # R2 -> IIR
    if (not fpu) and orden_fir > 30:
        return 0                                   # R3 -> IIR
    if trans_estrecha and (fpu or mhz >= 80):
        return 0                                   # R4 -> IIR
    return 1                                       # por defecto -> FIR


def generar_dataset(n: int = 4000, seed: int = 0):
    """Genera un dataset sintético etiquetado por las reglas (requiere numpy)."""
    rng = np.random.default_rng(seed)
    fase = rng.integers(0, 2, n)
    ram = rng.choice([2, 8, 32, 256], n).astype(float)
    mhz = rng.choice([16, 48, 80, 160, 240], n).astype(float)
    fpu = rng.integers(0, 2, n)
    trans = rng.integers(0, 2, n)                  # 1 = estrecha
    orden = rng.integers(8, 121, n)
    X = np.column_stack([fase, ram, mhz, fpu, trans, orden])
    y = np.array([
        _etiqueta_por_reglas(int(fase[i]), float(ram[i]), float(mhz[i]),
                             bool(fpu[i]), bool(trans[i]), int(orden[i]))
        for i in range(n)
    ])
    return X, y


def entrenar_arbol(n: int = 4000, seed: int = 0):
    """Entrena un DecisionTreeClassifier y muestra las reglas (export_text).

    Devuelve el clasificador entrenado o None si sklearn no está disponible.
    """
    if not _SKLEARN_OK:
        print("\n[ÁRBOL] scikit-learn/numpy no instalados: se omite la estrategia 2.")
        print("        Instale con: pip install numpy scikit-learn")
        return None

    X, y = generar_dataset(n=n, seed=seed)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=seed)
    clf = DecisionTreeClassifier(criterion="gini", max_depth=4,
                                 min_samples_leaf=20, random_state=seed)
    clf.fit(Xtr, ytr)
    acc = clf.score(Xte, yte)
    print(f"\n[ÁRBOL] DecisionTreeClassifier entrenado — accuracy test = {acc:.3f}")
    print("        (1 = FIR, 0 = IIR). Reglas aprendidas:")
    print(export_text(clf, feature_names=_FEATURES))
    return clf


def predecir_arbol(clf, specs: dict) -> dict:
    """Inferencia del árbol para un caso del agente (requiere sklearn)."""
    if clf is None or not _SKLEARN_OK:
        return {}
    caso = np.array([[
        int(bool(specs.get("fase_lineal", False))),
        float(specs.get("ram_kB", 256)),
        float(specs.get("mhz", 240)),
        int(bool(specs.get("fpu", True))),
        1 if str(specs.get("transicion", "amplia")).lower() == "estrecha" else 0,
        int(specs.get("orden_fir_est", 0)),
    ]])
    pred = int(clf.predict(caso)[0])
    conf = float(clf.predict_proba(caso).max())
    return {"tipo": "FIR" if pred == 1 else "IIR", "confianza": round(conf, 3)}


# ----------------------------------------------------------------------------
# Escenarios de validación (05-agente-ia.md §9)
# ----------------------------------------------------------------------------
ESCENARIOS = [
    ("(a) ECG diagnóstico — fase lineal estricta", {
        "fs": 500, "ram_kB": 32, "mhz": 160, "fpu": True,
        "fase_lineal": True, "snr_in_dB": 15, "latencia": "media",
        "transicion": "amplia", "orden_fir_est": 166,
    }, "FIR"),
    ("(b) Arduino UNO — 2 kB RAM, sin FPU, ordenFIR>50", {
        "fs": 500, "ram_kB": 2, "mhz": 16, "fpu": False,
        "fase_lineal": False, "snr_in_dB": 10, "latencia": "media",
        "transicion": "amplia", "orden_fir_est": 80,
    }, "IIR"),
    ("(c) ESP32 — transición estrecha + FPU (elíptico)", {
        "fs": 500, "ram_kB": 256, "mhz": 160, "fpu": True,
        "fase_lineal": False, "snr_in_dB": 12, "latencia": "media",
        "transicion": "estrecha", "orden_fir_est": 60,
    }, "IIR"),
]


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main() -> None:
    print("=" * 72)
    print("AGENTE DE DECISIÓN FIR/IIR — Paso 4 (reglas IF-THEN + árbol)")
    print("=" * 72)

    # --- Estrategia 1: reglas (siempre disponible, stdlib pura) ------------
    print("\n--- Estrategia 1: Sistema experto de reglas IF-THEN ---")
    for titulo, specs, esperado in ESCENARIOS:
        r = recomendar_reglas(specs)
        ok = "OK" if r["tipo"] == esperado else "FALLA"
        print(f"\n{titulo}")
        print(f"  entrada : ram={specs['ram_kB']}kB fpu={specs['fpu']} "
              f"fase_lineal={specs['fase_lineal']} transicion={specs['transicion']} "
              f"ordenFIR={specs['orden_fir_est']}")
        print(f"  salida  : {r['tipo']} / {r['estructura']} "
              f"(conf {r['confianza']:.2f}) reglas={r['reglas_activadas']}")
        print(f"  esperado: {esperado}  [{ok}]")
        print(f"  motivo  : {r['justificacion']}")

    # --- Estrategia 2: árbol de decisión (opcional) ------------------------
    print("\n" + "-" * 72)
    print("--- Estrategia 2: Árbol de decisión (scikit-learn) ---")
    clf = entrenar_arbol()
    if clf is not None:
        print("\nInferencia del árbol sobre los 3 escenarios:")
        for titulo, specs, esperado in ESCENARIOS:
            r = predecir_arbol(clf, specs)
            ok = "OK" if r.get("tipo") == esperado else "FALLA"
            print(f"  {titulo:<48} -> {r.get('tipo')} "
                  f"(conf {r.get('confianza')})  esperado {esperado} [{ok}]")


if __name__ == "__main__":
    main()
