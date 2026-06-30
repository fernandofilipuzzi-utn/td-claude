# 05 · Agente de decisión asistido por IA (FIR vs IIR)

> **Módulo del Paso 4.** Cubre la **generación del agente** que recomienda FIR/IIR y la estructura de implementación.
> Contexto y variables de entrada/salida: ver `00-enunciado.md` § *Paso 4 — Agente de IA* (no se repite aquí, se refiere).
> Coherencia técnica: todas las recomendaciones se apoyan en los criterios de ingeniería de [[04-criterios-diseno]].
> Implementaciones Python → [[07-python]] · Sistema experto en Octave/MATLAB → [[06-octave]].

---

## 1. Definición: ¿qué es un "agente de decisión / sistema experto" aquí?

Un **agente de decisión** (o **sistema experto** en su versión clásica) es un componente de software que **mapea un conjunto de restricciones de ingeniería a una recomendación de diseño de filtro**, emulando el razonamiento que haría un especialista en PDS. No diseña el filtro (eso es el Paso 2); **decide la familia y la estructura** y **justifica** la elección.

Formalmente es una función:

$$
\text{Agente}: \mathbf{x} \in \mathcal{X} \;\longrightarrow\; \mathbf{y} \in \mathcal{Y}
$$

### 1.1 Entradas $\mathbf{x}$ (variables del Paso 4)

| Variable | Símbolo | Tipo / rango típico | Origen |
|----------|---------|---------------------|--------|
| Frecuencia de muestreo | `fs` | Hz (10 … 5000) | Paso 1 (Nyquist) |
| Memoria del µC | `RAM`, `Flash` | kB (2 … 512) | plataforma (Anexo I) |
| Cómputo disponible | `MIPS` / `MHz` | 16 … 240 MHz; con/sin FPU | plataforma |
| Fase lineal requerida | `fase_lineal` | booleano (sí/no) | Paso 1 (¿preserva morfología?) |
| Nivel de ruido / SNR entrada | `SNR_in` | dB (p.ej. 0 … 40) | Paso 1 |
| Latencia admisible | `latencia` | {baja, media, alta} | requisito de aplicación |
| Pendiente de transición | `transicion` | {estrecha, amplia} → $\Delta f$ | Paso 1 |

### 1.2 Salidas $\mathbf{y}$

| Salida | Dominio | Comentario |
|--------|---------|------------|
| Recomendación | `{FIR, IIR}` | decisión primaria |
| Estructura | `{DF I, DF II, SOS (cascada), lattice}` | realización sugerida |
| Justificación | texto / reglas activadas | trazabilidad de la decisión |
| Confianza | $[0,1]$ (opcional) | grado de certeza |

> **Recordatorio de criterio** ([[04-criterios-diseno]]): FIR ⇒ fase lineal exacta por simetría de `h[n]`, siempre estable, pero orden alto (coste ≈ `N+1` MAC/muestra). IIR ⇒ orden bajo para la misma selectividad, pero fase no lineal y cuidado con la estabilidad ⇒ realizar en **SOS** (secciones de 2.º orden, ≈ `5·secciones` MAC/muestra) cuando no hay FPU.

### 1.3 Las 5 estrategias de generación (panorama)

El enunciado pide **elegir y justificar una** estrategia. Las cinco difieren en **cómo se construye/genera** el agente:

```
              ┌───────────────────────────── conocimiento experto explícito
1. Reglas IF-THEN  ── elicitación manual de reglas
3. Lógica difusa   ── reglas + funciones de pertenencia (conocimiento + grados)
              ├───────────────────────────── aprendizaje a partir de datos
2. Árbol decisión  ── entrenamiento (fit) sobre dataset etiquetado
5. Red neuronal MLP── entrenamiento por backpropagation
              └───────────────────────────── delegación a un modelo de lenguaje
4. API IA generativa ── prompt engineering + validación de la salida
```

---

## 2. Estrategia 1 — Reglas IF-THEN (sistema experto)

### 2.1 Definición

Un **sistema experto basado en reglas** consta de tres partes:

1. **Base de hechos:** las variables de entrada `fs`, `RAM`, `fase_lineal`, …
2. **Base de reglas:** sentencias `IF <condición> THEN <conclusión>` que codifican el conocimiento del especialista.
3. **Motor de inferencia:** recorre las reglas y deduce las conclusiones. Aquí usamos **encadenamiento hacia adelante** (*forward chaining*): de los hechos se disparan reglas hasta obtener la recomendación.

### 2.2 Cómo se "genera" el agente: elicitación de conocimiento

No hay entrenamiento. El agente se **construye a mano** mediante **elicitación de conocimiento experto**: se entrevista (o se consulta la bibliografía / [[04-criterios-diseno]]) y se traduce cada criterio a una regla, asignándole una **prioridad** y, opcionalmente, un **peso de confianza**.

### 2.3 Tabla de reglas (≥6, incluye las de referencia del enunciado)

| # | Prioridad | SI (condición) | ENTONCES | Confianza |
|---|-----------|----------------|----------|-----------|
| R1 | alta | `fase_lineal == sí` (estricta) | **FIR**, estructura DF (directa) | 0.95 |
| R2 | alta | `RAM < 2 kB` Y orden FIR estimado `> 50` | **IIR**, estructura **SOS** | 0.90 |
| R3 | alta | estabilidad numérica crítica Y sin DSP/FPU float | **IIR** en **SOS** (cascada 2.º orden) | 0.90 |
| R4 | media | `transicion == estrecha` Y cómputo suficiente (FPU/≥ decenas MHz) | **IIR** (orden adecuado, p.ej. Elíptico) | 0.85 |
| R5 | media | `latencia == baja` Y orden FIR alto inviable | **IIR** (menor retardo de grupo) | 0.70 |
| R6 | baja | plataforma con FPU Y `transicion == amplia` Y se desea fase lineal | **FIR** (ventana/Parks-McClellan) | 0.80 |
| R7 | baja | ninguna regla anterior disparada | **FIR** por defecto (simple, estable) | 0.50 |

> R1–R4 son las **reglas de referencia** del enunciado (`00-enunciado.md`). R5–R7 las extienden.

### 2.4 Motor de inferencia (pseudocódigo)

```pseudocode
ENTRADA: hechos = {fs, RAM, Flash, MHz, FPU, fase_lineal, SNR_in,
                   latencia, transicion, orden_FIR_estimado}
SALIDA:  recomendacion, estructura, reglas_activadas, confianza

funcion MOTOR_INFERENCIA(hechos):
    reglas_activadas <- []
    recomendacion    <- INDEFINIDA
    estructura       <- INDEFINIDA
    confianza        <- 0

    # Reglas ordenadas por prioridad (alta -> baja)
    PARA cada regla R en BASE_REGLAS (ordenada por prioridad):
        SI evaluar(R.condicion, hechos) == VERDADERO ENTONCES:
            reglas_activadas.agregar(R.id)
            SI recomendacion == INDEFINIDA ENTONCES:    # 1.ª que dispara fija la familia
                recomendacion <- R.conclusion.familia
                estructura    <- R.conclusion.estructura
                confianza     <- R.confianza
            FIN SI
        FIN SI
    FIN PARA

    SI recomendacion == INDEFINIDA ENTONCES:            # red de seguridad (R7)
        recomendacion <- "FIR"; estructura <- "DF"; confianza <- 0.5
    FIN SI

    DEVOLVER (recomendacion, estructura, reglas_activadas, confianza)
```

### 2.5 Implementación como sistema experto en **Octave/MATLAB** → [[06-octave]]

> Este bloque sirve como **agente embebible/portátil** sin dependencias de ML; ideal para el documento de Octave.

```matlab
% --- agente_reglas.m : sistema experto FIR/IIR (Octave/MATLAB) ---
function [rec, estructura, reglas, conf] = agente_reglas(h)
  % h: struct con campos fs, RAM, Flash, MHz, FPU(bool), fase_lineal(bool),
  %    SNR_in, latencia('baja'|'media'|'alta'),
  %    transicion('estrecha'|'amplia'), ordenFIR
  rec = ''; estructura = ''; reglas = {}; conf = 0;

  function fijar(r, fam, est, c)
    if isempty(rec), rec = fam; estructura = est; conf = c; end
    reglas{end+1} = r;                                  %#ok<AGROW>
  end

  % R1: fase lineal estricta -> FIR
  if h.fase_lineal, fijar('R1','FIR','DF',0.95); end
  % R2: RAM < 2 kB y orden FIR alto -> IIR SOS
  if h.RAM < 2 && h.ordenFIR > 50, fijar('R2','IIR','SOS',0.90); end
  % R3: estabilidad crítica sin float -> IIR SOS
  if ~h.FPU && h.ordenFIR > 30,     fijar('R3','IIR','SOS',0.90); end
  % R4: transicion estrecha + computo suficiente -> IIR (eliptico)
  if strcmp(h.transicion,'estrecha') && (h.FPU || h.MHz >= 80)
    fijar('R4','IIR','SOS',0.85);
  end
  % R5: latencia baja + FIR inviable -> IIR
  if strcmp(h.latencia,'baja') && h.ordenFIR > 64, fijar('R5','IIR','DFII',0.70); end
  % R6: FPU + transicion amplia + fase lineal deseada -> FIR
  if h.FPU && strcmp(h.transicion,'amplia'),       fijar('R6','FIR','DF',0.80); end
  % R7: por defecto
  if isempty(rec), fijar('R7','FIR','DF',0.50); end
end
```

### 2.6 Ventajas / limitaciones

| Ventajas | Limitaciones |
|----------|--------------|
| **Totalmente interpretable** (trazabilidad de reglas) | No generaliza fuera de lo previsto |
| **Determinista** y reproducible | Mantenimiento manual si crece la base |
| No necesita datos ni entrenamiento | Conflicto/solapamiento de reglas requiere prioridades |
| **Ligero** ⇒ embebible en el µC | Define fronteras "duras" (todo-o-nada) |

---

## 3. Estrategia 2 — Árbol de decisión (scikit-learn)

### 3.1 Definición

Un **árbol de decisión** es un clasificador que parte recursivamente el espacio de entrada en nodos. En cada nodo elige la variable y el umbral que mejor separan las clases, según un **criterio de impureza**:

- **Gini:** $G = 1 - \sum_k p_k^2$
- **Entropía:** $H = -\sum_k p_k \log_2 p_k$ (ganancia de información)

donde $p_k$ es la proporción de la clase $k$ (FIR/IIR) en el nodo. El árbol se queda con el split que **minimiza la impureza ponderada** de los hijos.

### 3.2 Cómo se "genera" = **entrenamiento** (`fit`)

A diferencia del sistema experto, el árbol **aprende** las fronteras desde un **dataset etiquetado**: `features = [fs, RAM, MHz, FPU, fase_lineal, SNR_in, transicion, ordenFIR]`, `label = {FIR, IIR}`. Como aquí no tenemos datos reales, los **etiquetamos sintéticamente con las reglas de ingeniería** (§7) — el árbol "destila" esas reglas y las suaviza.

### 3.3 Ejemplo en **Python (sklearn)** → [[07-python]]

```python
# --- arbol_fir_iir.py ---
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text

# 1) Dataset sintetico etiquetado por reglas (ver seccion 7 para el generador)
X, y, feat_names = generar_dataset(n=4000, seed=0)   # X: features, y: 'FIR'/'IIR'

# 2) Entrenamiento ("generacion" del agente)
clf = DecisionTreeClassifier(
    criterion="gini",       # o "entropy"
    max_depth=4,            # limita profundidad -> evita overfitting + interpretable
    min_samples_leaf=20,
    random_state=0,
)
clf.fit(X, y)

# 3) Extraccion de las reglas aprendidas (interpretabilidad)
print(export_text(clf, feature_names=feat_names))

# 4) Inferencia para un caso nuevo
caso = np.array([[500, 2, 16, 0, 1, 10, 0, 80]])      # fs,RAM,MHz,FPU,fase_lin,SNR,transEstrecha,ordenFIR
print("Recomendacion:", clf.predict(caso)[0])
print("Confianza:", clf.predict_proba(caso).max())    # prob. de la clase ganadora
```

`export_text` produce algo como:

```
|--- fase_lineal <= 0.50
|   |--- ordenFIR <= 50.50
|   |   |--- class: IIR
|   |--- ordenFIR >  50.50
|   |   |--- class: IIR
|--- fase_lineal >  0.50
|   |--- RAM <= 2.00
|   |   |--- ordenFIR <= 50.50 -> class: FIR
|   |   |--- ordenFIR >  50.50 -> class: IIR
|   |--- RAM >  2.00 -> class: FIR
```

> La **confianza** sale directamente de `predict_proba` (fracción de muestras de cada clase en la hoja).

### 3.4 Riesgo de overfitting y profundidad máxima

- Sin límite, el árbol **memoriza** el ruido del dataset (hojas con 1 muestra) ⇒ **overfitting**.
- Mitigación: `max_depth` (4–6), `min_samples_leaf`, poda. Con datos generados por reglas, un árbol *poco profundo* recupera las reglas casi exactas y **generaliza** a combinaciones intermedias.

### 3.5 Ventajas / limitaciones

| Ventajas | Limitaciones |
|----------|--------------|
| Interpretable (se exporta a reglas) | Necesita dataset (aquí, sintético) |
| Captura interacciones entre variables | Sensible al ruido ⇒ overfitting |
| Inferencia muy rápida y determinista (una vez entrenado) | Fronteras "en escalera" (axis-aligned) |
| Exportable a `if/else` ⇒ embebible | Requiere instalar sklearn en fase de diseño |

---

## 4. Estrategia 3 — Lógica difusa (fuzzy)

### 4.1 Definición

La **lógica difusa** sustituye las fronteras duras ("RAM < 2 kB") por **grados de pertenencia** $\mu \in [0,1]$. Una variable lingüística (p.ej. *ruido*) toma valores **bajo / medio / alto** descritos por **funciones de pertenencia** (triangulares, trapezoidales). El motor (**Mamdani**) combina reglas difusas y produce una salida graduada → ideal para un **grado de recomendación / confianza** suave.

Etapas: **fuzzificación → inferencia (Mamdani) → defuzzificación (centroide)**.

### 4.2 Variables lingüísticas y funciones de pertenencia (ejemplo)

```
ruido (SNR_in, dB):     bajo  [>25]   medio [10..25]   alto [<12]   (trapezoidales con solape)
transicion (Δf):        amplia          estrecha
recursos (MHz, RAM):    escasos         amplios
salida -> "preferencia_IIR" ∈ [0,1]:  bajo  medio  alto
```

Ejemplo de pertenencia triangular del ruido "alto":

$$
\mu_{\text{alto}}(s)=
\begin{cases}
0 & s \ge 18\\
\dfrac{18 - s}{18 - 6} & 6 < s < 18\\
1 & s \le 6
\end{cases}\qquad (s=\text{SNR en dB})
$$

### 4.3 Reglas difusas (Mamdani)

```
SI ruido ES alto    Y transicion ES estrecha            ENTONCES preferencia_IIR ES alta
SI recursos ES escasos Y transicion ES estrecha         ENTONCES preferencia_IIR ES alta
SI fase_lineal ES requerida                             ENTONCES preferencia_IIR ES baja   (=> FIR)
SI transicion ES amplia Y recursos ES amplios           ENTONCES preferencia_IIR ES media
```

La salida `preferencia_IIR` cercana a 1 ⇒ **IIR** (con confianza = valor defuzzificado); cercana a 0 ⇒ **FIR**. El **centroide** del conjunto de salida agregado da el número final:

$$
y^\* = \frac{\int y\,\mu_{\text{agg}}(y)\,dy}{\int \mu_{\text{agg}}(y)\,dy}
$$

### 4.4 Cómo se "genera" el agente

Igual que el sistema experto, **no hay entrenamiento**: se diseñan a mano las **funciones de pertenencia** y las **reglas difusas**. La "generación" consiste en elegir formas/solapes de las MF y el conjunto de reglas. Aporta sobre IF-THEN la **gradación** (decisiones suaves y confianza continua).

### 4.5 Ejemplo en **Python (scikit-fuzzy)** → [[07-python]]

```python
# --- agente_fuzzy.py (scikit-fuzzy) ---
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Antecedentes / consecuente
ruido = ctrl.Antecedent(np.arange(0, 41, 1), 'ruido')          # SNR_in (dB)
trans = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'trans')      # 0=amplia,1=estrecha
pref  = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'pref_IIR')

ruido['alto']  = fuzz.trimf(ruido.universe, [0, 0, 18])
ruido['medio'] = fuzz.trimf(ruido.universe, [8, 18, 28])
ruido['bajo']  = fuzz.trimf(ruido.universe, [22, 40, 40])
trans['estrecha'] = fuzz.trimf(trans.universe, [0.4, 1, 1])
trans['amplia']   = fuzz.trimf(trans.universe, [0, 0, 0.6])
pref['baja']  = fuzz.trimf(pref.universe, [0, 0, 0.5])
pref['media'] = fuzz.trimf(pref.universe, [0.25, 0.5, 0.75])
pref['alta']  = fuzz.trimf(pref.universe, [0.5, 1, 1])

reglas = [
    ctrl.Rule(ruido['alto'] & trans['estrecha'], pref['alta']),
    ctrl.Rule(trans['amplia'],                   pref['media']),
    ctrl.Rule(ruido['bajo'],                     pref['baja']),
]
sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem(reglas))

sim.input['ruido'] = 8.0      # SNR baja -> ruido alto
sim.input['trans'] = 0.9      # transicion estrecha
sim.compute()
p = sim.output['pref_IIR']    # defuzzificado por centroide
print("pref_IIR =", round(p, 3),
      "-> recomendacion:", "IIR" if p >= 0.5 else "FIR",
      "| confianza:", round(abs(p - 0.5) * 2, 3))
```

### 4.6 Ventajas / limitaciones

| Ventajas | Limitaciones |
|----------|--------------|
| Decisiones **suaves** + confianza continua | Diseño de MF y reglas es manual/artesanal |
| Robusto a entradas ambiguas/imprecisas | Más parámetros que ajustar (formas, solapes) |
| Interpretable (reglas lingüísticas) | Defuzzificación añade coste de cómputo |
| No requiere datos | Requiere librería (scikit-fuzzy) en diseño |

---

## 5. Estrategia 4 — API de IA generativa (Claude / GPT)

### 5.1 Definición

Se **delega la decisión a un LLM** (modelo de lenguaje) accedido por API. El agente no se "programa" con reglas: se **construye mediante *prompt engineering* estructurado** — un *system prompt* con rol + criterios + formato de salida — y se **valida** la respuesta. El LLM razona en lenguaje natural y devuelve una recomendación con **justificación rica**.

### 5.2 Cómo se "genera" el agente: prompt engineering + salida estructurada

1. **System prompt:** define el **rol** (experto en PDS), los **criterios** (los de [[04-criterios-diseno]]) y el **formato de salida** (JSON estricto).
2. **User prompt:** inyecta las **variables** del caso.
3. **Structured output / tool use:** se fuerza un **esquema JSON** para que la respuesta sea parseable y verificable.
4. **Validación:** se comprueba que `recomendacion ∈ {FIR, IIR}`, que la estructura es válida y que la confianza está en `[0,1]`; si no, se reintenta o se cae a un agente de reglas (fallback).

### 5.3 Ejemplo de prompt estructurado

**System prompt**

```text
Eres un especialista en procesamiento digital de señales (PDS). Dadas las
restricciones de un sistema embebido, recomiendas FIR o IIR y una estructura
de realizacion (DF I, DF II, SOS o lattice).

Criterios obligatorios:
- Fase lineal estricta (preservar morfologia, p.ej. ECG) => FIR.
- RAM < 2 kB con orden FIR > 50 => IIR.
- Estabilidad numerica critica sin FPU/float => IIR en SOS.
- Transicion estrecha con computo suficiente => IIR (p.ej. Eliptico) de orden adecuado.

Devuelve UNICAMENTE un objeto JSON con el formato indicado, sin texto adicional.
```

**User prompt (variables del caso)**

```text
Caso:
- fs = 500 Hz
- RAM = 2 kB, Flash = 32 kB
- MHz = 16, FPU = no
- fase_lineal = si (ECG diagnostico)
- SNR_in = 12 dB
- latencia = media
- transicion = estrecha
```

**Formato de salida (JSON)**

```json
{
  "recomendacion": "FIR",
  "estructura": "DF",
  "justificacion": "Fase lineal estricta para preservar P-QRS-T; FIR de fase lineal por simetria de h[n].",
  "confianza": 0.92
}
```

### 5.4 Llamada con el SDK `anthropic` (familia Claude actual) → [[07-python]]

> Requiere **API key** (`ANTHROPIC_API_KEY` en el entorno) y conexión a internet. **Nunca** se escriben claves en el código.

```python
# --- agente_llm.py (SDK anthropic) ---
import os, json
import anthropic
from pydantic import BaseModel, field_validator

class Recom(BaseModel):
    recomendacion: str
    estructura: str
    justificacion: str
    confianza: float
    @field_validator("recomendacion")
    @classmethod
    def fam_valida(cls, v):
        assert v in {"FIR", "IIR"}, "recomendacion debe ser FIR o IIR"
        return v

client = anthropic.Anthropic()    # toma la clave de ANTHROPIC_API_KEY (no hardcodear)

SYSTEM = (
    "Eres un especialista en PDS. Recomiendas FIR o IIR y una estructura "
    "(DF I, DF II, SOS o lattice) segun las restricciones del sistema embebido. "
    "Aplica: fase lineal estricta=>FIR; RAM<2kB y ordenFIR>50=>IIR; "
    "estabilidad critica sin FPU=>IIR en SOS; transicion estrecha con computo "
    "suficiente=>IIR. Devuelve solo JSON."
)

user = (
    "Caso: fs=500 Hz; RAM=2 kB; MHz=16; FPU=no; fase_lineal=si (ECG); "
    "SNR_in=12 dB; latencia=media; transicion=estrecha."
)

# Salida estructurada validada contra un esquema JSON
resp = client.messages.parse(
    model="claude-opus-4-8",        # familia actual; usar 'claude-haiku-4-5' si se prioriza coste/latencia
    max_tokens=1024,
    system=SYSTEM,
    messages=[{"role": "user", "content": user}],
    output_format=Recom,            # fuerza y valida el esquema
)

rec = resp.parsed_output            # instancia Recom validada
print(rec.recomendacion, rec.estructura, round(rec.confianza, 2))
print(rec.justificacion)
```

> Notas de modelo (familia Claude actual): `claude-opus-4-8` para máxima capacidad de razonamiento; `claude-haiku-4-5` cuando interesan coste/latencia. La salida estructurada se obtiene con `messages.parse(...)` + esquema (`output_config.format` a bajo nivel). No usar parámetros obsoletos (`temperature`, `budget_tokens` no aplican en esta familia).

### 5.5 Ventajas / riesgos

| Ventajas | Riesgos / limitaciones |
|----------|------------------------|
| Justificación **rica** en lenguaje natural | **No determinista** (misma entrada, salida variable) |
| Maneja casos poco previstos / lenguaje libre | **Latencia** y **coste** por llamada |
| No requiere mantener reglas a mano | **Requiere conexión** ⇒ poco apto para tiempo real embebido |
| Rápido de prototipar | Necesita **validación** de la salida (alucinaciones) |

> **Conclusión de uso:** muy útil en **fase de diseño** (explorar, justificar, documentar), **no** como agente embebido en tiempo real. En el µC conviene un agente de reglas (§2) o un árbol exportado a `if/else` (§3).

---

## 6. Estrategia 5 — Red neuronal simple (MLP, perceptrón multicapa)

### 6.1 Definición y arquitectura

Un **MLP** es una red de neuronas en capas: **entrada** (tantas neuronas como variables), una o más **capas ocultas** (activación no lineal, p.ej. ReLU o `tanh`) y **salida**. Para clasificación binaria FIR/IIR: salida con **1 neurona sigmoide** o **2 neuronas softmax**.

```
[fs, RAM, MHz, FPU, fase_lineal, SNR_in, transicion, ordenFIR]   (8 entradas)
        │
   capa oculta 1  (p.ej. 16, ReLU)
        │
   capa oculta 2  (p.ej.  8, ReLU)
        │
   salida softmax (2)  ->  P(FIR), P(IIR)
```

### 6.2 Cómo se "genera" = entrenamiento por **backpropagation**

Se minimiza la **entropía cruzada** ajustando pesos $\mathbf{W}$ por **descenso de gradiente** (los gradientes se calculan con *retropropagación*). Igual que el árbol, **requiere un dataset etiquetado** (aquí, sintético — §7). La salida softmax da directamente una **confianza** = $P(\text{clase ganadora})$.

### 6.3 Ejemplo conceptual con **`MLPClassifier` de sklearn** → [[07-python]]

```python
# --- agente_mlp.py ---
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

X, y, feat = generar_dataset(n=8000, seed=1)     # mismo generador de la seccion 7

# Escalar + MLP (2 capas ocultas). "Generacion" = .fit (backprop, Adam)
modelo = make_pipeline(
    StandardScaler(),
    MLPClassifier(hidden_layer_sizes=(16, 8),
                  activation="relu", solver="adam",
                  max_iter=500, random_state=1),
)
modelo.fit(X, y)

caso = [[500, 2, 16, 0, 1, 12, 1, 80]]
print("Recomendacion:", modelo.predict(caso)[0])
print("Confianza:", modelo.predict_proba(caso).max())
```

### 6.4 ¿Cuándo es **excesivo** frente a reglas?

- El problema FIR/IIR tiene **pocas variables** y fronteras **explicables** ⇒ un sistema de reglas o un árbol ya lo resuelven, son interpretables y embebibles.
- Un MLP es **caja negra**, necesita **más datos**, puede sobre-ajustar y es **difícil de justificar** ante un tribunal o auditoría.
- **Justifica su uso** solo si hubiese muchas variables continuas con interacciones no lineales complejas y un dataset real abundante — **no es el caso** de este examen. Aquí el MLP es sobre-ingeniería; se incluye por completitud.

| Ventajas | Limitaciones |
|----------|--------------|
| Aprende fronteras no lineales suaves | **No interpretable** (caja negra) |
| Confianza continua (softmax) | Necesita **más datos** y ajuste de hiperparámetros |
| — | Riesgo de overfitting; difícil de justificar |
| — | Excesivo para 8 variables con reglas claras |

---

## 7. Generación de **datos sintéticos** de entrenamiento

Las estrategias 2 y 5 (árbol, MLP) necesitan datos. Como no hay un dataset real de "decisiones FIR/IIR", se **fabrica** muestreando combinaciones de variables y **etiquetando con las reglas de ingeniería** ([[04-criterios-diseno]] + reglas de referencia del enunciado). El clasificador entonces **destila** esas reglas y generaliza a casos intermedios.

```python
# --- generador de dataset sintetico (para arbol y MLP) ---
import numpy as np

def etiqueta_por_reglas(fs, RAM, MHz, FPU, fase_lin, SNR, trans_estrecha, ordenFIR):
    # Reglas de ingenieria (mismas que el sistema experto, seccion 2)
    if fase_lin and not (RAM < 2 and ordenFIR > 50):
        return "FIR"                                   # R1 (salvo conflicto memoria)
    if RAM < 2 and ordenFIR > 50:
        return "IIR"                                   # R2
    if (not FPU) and ordenFIR > 30:
        return "IIR"                                   # R3 (estabilidad / SOS)
    if trans_estrecha and (FPU or MHz >= 80):
        return "IIR"                                   # R4
    return "FIR"                                       # por defecto

def generar_dataset(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    fs       = rng.uniform(10, 5000, n)
    RAM      = rng.choice([2, 8, 32, 256], n)           # kB
    MHz      = rng.choice([16, 48, 80, 160, 240], n)
    FPU      = rng.integers(0, 2, n)
    fase_lin = rng.integers(0, 2, n)
    SNR      = rng.uniform(0, 40, n)
    trans    = rng.integers(0, 2, n)                    # 1 = estrecha
    ordenFIR = rng.integers(8, 121, n)                  # orden FIR estimado
    X = np.column_stack([fs, RAM, MHz, FPU, fase_lin, SNR, trans, ordenFIR])
    y = np.array([etiqueta_por_reglas(*fila) for fila in X])
    feat = ["fs","RAM","MHz","FPU","fase_lineal","SNR_in","transicion","ordenFIR"]
    return X, y, feat
```

> Buenas prácticas: **balancear** clases (evitar que domine FIR/IIR), **añadir ruido** controlado a algunas etiquetas para forzar generalización, y **separar train/test** para medir si el modelo recupera las reglas (`accuracy` cercana a 1 en datos limpios).

---

## 8. Tabla comparativa de las 5 estrategias

| Criterio | 1. Reglas IF-THEN | 2. Árbol (sklearn) | 3. Lógica difusa | 4. API IA generativa | 5. MLP |
|----------|:--:|:--:|:--:|:--:|:--:|
| **Interpretabilidad** | Muy alta | Alta | Alta | Media (texto) | Baja |
| **Datos necesarios** | Ninguno | Dataset (sintético) | Ninguno | Ninguno | Dataset (más) |
| **Determinismo** | Total | Total (tras `fit`) | Total | **No** | Total (tras `fit`) |
| **Idoneidad embebida** | Excelente | Buena (exporta a `if/else`) | Media (coste defuzz.) | **Nula** (online) | Baja |
| **Esfuerzo de generación** | Medio (elicitar reglas) | Bajo (entrenar) | Alto (diseñar MF) | Bajo (prompt) | Medio-alto |
| **Aporta confianza** | Opcional (pesos) | Sí (`predict_proba`) | Sí (centroide) | Sí (campo JSON) | Sí (softmax) |
| **Recomendado para** | µC en tiempo real | diseño + exportar | entradas imprecisas | **fase de diseño** | (sobre-ingeniería aquí) |

---

## 9. Validación del agente (escenarios del enunciado)

Se valida con ≥3 escenarios de restricciones distintas; las salidas deben ser **coherentes con [[04-criterios-diseno]]** y los Pasos 1–3. Para cada estrategia, todas las entradas siguientes deben producir la misma recomendación (los métodos de aprendizaje, si están bien entrenados, replican las reglas).

### Escenario (a) — ECG diagnóstico, fase lineal estricta

| Entrada | Valor |
|---------|-------|
| `fase_lineal` | sí (preservar P-QRS-T) |
| `fs` | 500 Hz, `transicion` amplia, `SNR_in` 15 dB |
| plataforma | ESP32/STM32 con FPU |

→ **Salida esperada:** **FIR**, estructura **DF** (fase lineal por simetría de `h[n]`).
**Justificación:** la morfología clínica exige **fase lineal exacta**; FIR la garantiza (R1). El cómputo con FPU absorbe el orden mayor.

### Escenario (b) — Arduino UNO, RAM 2 kB, orden FIR alto

| Entrada | Valor |
|---------|-------|
| plataforma | Arduino UNO (16 MHz, 2 kB RAM, **sin FPU**) |
| `ordenFIR` estimado | > 50 |
| `fase_lineal` | no estricta |

→ **Salida esperada:** **IIR**, estructura **SOS** (cascada de 2.º orden, punto fijo Q).
**Justificación:** FIR de orden > 50 es **inviable** con 2 kB; IIR logra la misma selectividad con orden bajo (R2). Sin float ⇒ **SOS** por estabilidad numérica (R3).

### Escenario (c) — Transición exigente + ESP32 con FPU

| Entrada | Valor |
|---------|-------|
| `transicion` | estrecha (banda de transición muy angosta) |
| plataforma | ESP32 con **FPU**, ≥ 160 MHz |
| `fase_lineal` | no requerida |

→ **Salida esperada:** **IIR** (prototipo **Elíptico**), estructura **SOS**.
**Justificación:** transición estrecha + cómputo suficiente ⇒ **IIR de orden adecuado** (R4); el Elíptico da la pendiente más abrupta para el menor orden; SOS asegura estabilidad numérica.

### 9.1 Tabla resumen de validación

| Escenario | Entrada clave | Salida esperada | Regla / criterio |
|-----------|---------------|-----------------|------------------|
| (a) ECG | fase lineal estricta | **FIR** / DF | R1 · [[04-criterios-diseno]] |
| (b) Arduino UNO | 2 kB RAM, ordenFIR>50, sin FPU | **IIR** / SOS | R2, R3 |
| (c) ESP32 | transición estrecha + FPU | **IIR (Elíptico)** / SOS | R4 |

> Si una estrategia de aprendizaje (árbol/MLP) **no** reproduce estas salidas, es señal de **dataset mal balanceado** o de **overfitting**: revisar §7 (balanceo, profundidad/`max_depth`).

---

## 10. Recomendación de cierre

- **Para entregar y embeber:** estrategia **1 (reglas IF-THEN)** — interpretable, determinista y ligera; se implementa en Octave/MATLAB ([[06-octave]]) o se exporta a C para el Paso 5.
- **Para enriquecer el documento Python:** **2 (árbol)** + **3 (fuzzy)** + **4 (LLM)** muestran el espectro de técnicas ([[07-python]]).
- **El MLP (5)** se documenta como referencia pero se señala como **excesivo** para este problema.
- Todas las recomendaciones de familia/estructura se anclan en los criterios de [[04-criterios-diseno]] y son coherentes con los Pasos 1–3.
