# Ejemplos en Python — Filtrado Digital FIR/IIR + Agente de IA

Scripts ejecutables de referencia para el examen de PDS (caso ECG, `fs = 500 Hz`):
diseño y caracterización de filtros, pipeline de filtrado sobre señal sintética
y agente de decisión FIR/IIR (reglas, árbol y vía LLM).

## Requisitos e instalación

Python 3.10 o superior. Use siempre un **entorno virtual** aislado (no el Python
del sistema).

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS (bash)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> El stack se documenta en `requirements.txt`. `numpy`, `scipy` y `matplotlib`
> son necesarios para los scripts de filtros; `scikit-learn` y `anthropic` son
> **opcionales** (ver más abajo).

## Cómo ejecutar cada script

| Script | Qué hace | Deps necesarias |
|--------|----------|-----------------|
| `diseno_filtros.py` | Diseña FIR (Hamming, fc=40, ~167 taps) e IIR (Chebyshev I en SOS + notch 50 Hz). Grafica respuesta en frecuencia, retardo de grupo, polos-ceros e impulso. Verifica simetría del FIR. | numpy, scipy, matplotlib |
| `procesar_senal.py` | Genera un ECG sintético (P-QRS-T) + 50 Hz + ruido, aplica FIR/IIR (causal y fase cero), grafica tiempo y espectro (FFT/Welch) e imprime tabla SNR/RMSE. | numpy, scipy, matplotlib |
| `agente_decision.py` | Agente de decisión: reglas IF-THEN (stdlib pura) + árbol de decisión (sklearn). Valida los 3 escenarios del KB. | stdlib (reglas); sklearn (árbol, opcional) |
| `agente_llm.py` | Agente vía API Claude: prompt estructurado → JSON validado `{recomendacion, estructura, justificacion, confianza}`. | anthropic + `ANTHROPIC_API_KEY` (opcional) |

```bash
python diseno_filtros.py
python procesar_senal.py
python agente_decision.py
python agente_llm.py
```

Los scripts de filtros abren ventanas de matplotlib; ciérrelas para terminar.

## Dependencias opcionales

- **scikit-learn** (`agente_decision.py`): solo la estrategia del **árbol de
  decisión** lo usa. El bloque de **reglas IF-THEN** corre con la biblioteca
  estándar (sin numpy ni sklearn). Si sklearn no está instalado, el script
  avisa y continúa solo con las reglas.

- **anthropic** (`agente_llm.py`): SDK de la API de Claude. Requiere además la
  variable de entorno `ANTHROPIC_API_KEY` (la clave **nunca** se escribe en el
  código). Si falta el SDK o la clave, el script imprime instrucciones y sale
  limpiamente.

  ```powershell
  $env:ANTHROPIC_API_KEY = "<su_clave>"   # Windows PowerShell
  ```
  ```bash
  export ANTHROPIC_API_KEY="<su_clave>"   # Linux/macOS
  ```

  El agente LLM es para la **fase de diseño** (explorar/justificar/documentar):
  por latencia, coste y no-determinismo **no** es apto para el microcontrolador
  en tiempo real; allí se usa el agente de reglas de `agente_decision.py`.

## Notas de coherencia técnica

- FIR LP Hamming: `numtaps ≈ 167` (orden N ≈ 166), fase lineal exacta.
- IIR LP: Butterworth daría `N = 13` (inviable en forma directa) → se usa
  **Chebyshev I** (`N ≈ 6`) o **elíptico** (`N ≈ 4`) en **SOS** (estable).
- Notch IIR de red: **50 Hz**, `Q = 30`.
