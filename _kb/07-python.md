# 07 · Herramientas Python para PDS y ML (referencia con ejemplos)

> **Uso:** referencia práctica de funciones de Python científico para diseño, simulación y agente de IA. El contexto del examen y los 5 pasos están en [[00-enunciado]] (no se repite). Los fundamentos teóricos están en [[01-fundamentos-pds]]; el diseño FIR en [[02-fir]] e IIR en [[03-iir]]; las estrategias del agente en [[05-agente-ia]]. Aquí solo se documenta **qué función llamar, con qué firma y un ejemplo corto**.
>
> **Caso de referencia transversal:** ECG, `fs = 500 Hz` (Anexo I, opción A). Banda útil del ECG ≈ 0.5–40 Hz; interferencia de red 50/60 Hz a eliminar con notch IIR; LP FIR fase lineal `fc = 40 Hz` para preservar morfología P-QRS-T.

---

## 1. Stack y entorno

> **No ejecutar `pip install` en este trabajo.** Solo se documenta el comando. Toda instalación debe hacerse en un **entorno virtual** aislado (`python -m venv .venv` y activación), nunca en el Python del sistema.

```bash
# Crear y activar entorno virtual (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1          # en Linux/macOS: source .venv/bin/activate

# Instalar el stack (DOCUMENTADO; no ejecutar en este trabajo)
pip install numpy scipy matplotlib scikit-learn scikit-fuzzy anthropic
```

| Paquete | `import` habitual | Rol | Versión típica (2025-2026) |
|---|---|---|---|
| **numpy** | `import numpy as np` | Arrays, FFT, álgebra, métricas | ≥ 1.26 / 2.x |
| **scipy** | `from scipy import signal` | Diseño y aplicación de filtros, ventanas, PSD | ≥ 1.11 |
| **matplotlib** | `import matplotlib.pyplot as plt` | Gráficos (Bode, tiempo, FFT, polos-ceros) | ≥ 3.8 |
| **scikit-learn** | `from sklearn...` | Árbol de decisión, MLP, split | ≥ 1.4 |
| **scikit-fuzzy** | `import skfuzzy as fuzz` / `from skfuzzy import control as ctrl` | Lógica difusa del agente | ≥ 0.4.2 |
| **anthropic** | `from anthropic import Anthropic` | Agente vía LLM (API Claude) | ≥ 0.40 |

Notas:
- `scikit-fuzzy` requiere `numpy<2` en algunas versiones antiguas; verificar compatibilidad en el `venv`.
- `wfdb` (mencionado en [[00-enunciado]], Anexo II) sirve para descargar/convertir registros de PhysioNet a CSV; no se cubre aquí.

---

## 2. Diseño FIR — `scipy.signal`

Todas las funciones FIR devuelven el vector de coeficientes `h` (de longitud `numtaps`); el filtro se aplica luego con `lfilter` o `filtfilt` (sección 5). El orden del filtro es `N = numtaps - 1`. Teoría en [[02-fir]].

### 2.1 `firwin` — método de ventanas

```
scipy.signal.firwin(numtaps, cutoff, *, width=None, window='hamming',
                    pass_zero=True, scale=True, fs=None)
```
- **`numtaps`**: número de coeficientes = `N + 1`. Para fase lineal tipo I (LP), conviene **impar**.
- **`cutoff`**: frecuencia(s) de corte. En las mismas unidades que `fs`; si se omite `fs`, normalizada a Nyquist (0–1, donde 1 = `fs/2`).
- **`window`**: `'hamming'`, `'hann'`, `'blackman'`, `'rectangular'`, o `('kaiser', beta)`.
- **`pass_zero`**: `True`→LP/BR (deja pasar DC); `False`→HP/BP.
- **`fs`**: frecuencia de muestreo; si se pasa, `cutoff` va en Hz.
- **Devuelve:** `h` (ndarray, longitud `numtaps`).

```python
import numpy as np
from scipy import signal

fs = 500
# LP fase lineal, fc=40 Hz, 101 taps (orden N=100), ventana Hamming
h = signal.firwin(numtaps=101, cutoff=40, fs=fs, window='hamming')   # pass_zero=True → LP
# Sin fs sería: cutoff = 40/(fs/2) = 0.16 (normalizado a Nyquist)
print(h.shape)   # (101,)  → suma de coeficientes ≈ 1 (ganancia DC unidad, scale=True)
```

### 2.2 `firwin2` — respuesta arbitraria por frecuencia/ganancia

```
scipy.signal.firwin2(numtaps, freq, gain, *, window='hamming', fs=None)
```
- **`freq`, `gain`**: puntos (frecuencia, ganancia deseada) que definen `|H|` por tramos. `freq` debe ir de 0 a `fs/2` (o 0–1 normalizado), monótono.
- Útil para multibanda o respuestas no estándar.

```python
# LP suave: ganancia 1 hasta 35 Hz, transición a 0 en 45 Hz
h = signal.firwin2(numtaps=101, freq=[0, 35, 45, 250], gain=[1, 1, 0, 0], fs=fs)
```

### 2.3 `remez` — Parks-McClellan (equiripple, óptimo)

```
scipy.signal.remez(numtaps, bands, desired, *, weight=None, type='bandpass', fs=None)
```
- **`bands`**: bordes de banda **por pares** (inicio, fin de cada banda), en Hz si se pasa `fs`. Incluye las bandas de transición implícitamente (lo no listado es transición).
- **`desired`**: ganancia deseada por banda (un valor por banda).
- **`weight`**: pesos relativos de error por banda (controla el reparto del rizado).
- **Devuelve:** `h`. Minimiza el error máximo (Chebyshev) → rizado uniforme.

```python
# LP equiripple: paso 0–40 Hz (g=1), rechazo 50–250 Hz (g=0)
h = signal.remez(numtaps=101, bands=[0, 40, 50, fs/2], desired=[1, 0], fs=fs)
```

### 2.4 Dimensionado Kaiser — `kaiserord`, `kaiser_beta`, `kaiser_atten`

```
numtaps, beta = scipy.signal.kaiserord(ripple, width)
beta  = scipy.signal.kaiser_beta(a)      # a = atenuación deseada en dB (>0)
a     = scipy.signal.kaiser_atten(numtaps, width)
```
- **`kaiserord(ripple, width)`**: estima `numtaps` y `beta` para una atenuación `ripple` (dB, positiva) y un ancho de transición `width` **normalizado a Nyquist** (0–1).
- `width = Δf / (fs/2)`.

```python
delta_f = 10                       # ancho de transición 40→50 Hz = 10 Hz
width   = delta_f / (fs/2)         # normalizado a Nyquist
numtaps, beta = signal.kaiserord(ripple=40, width=width)   # As ≈ 40 dB
h = signal.firwin(numtaps, cutoff=45, fs=fs, window=('kaiser', beta))  # corte en el centro de transición
```

---

## 3. Diseño IIR — `scipy.signal`

Las funciones de diseño aceptan `output='ba'|'zpk'|'sos'`. **Siempre usar `output='sos'`** para órdenes ≥ 4: la forma de segundos órdenes en cascada (Second-Order Sections) es numéricamente estable, mientras que `'ba'` (coeficientes `b, a` globales) acumula error y puede volverse inestable. Teoría y bilineal en [[03-iir]].

- **`'ba'`** → `(b, a)`: numerador/denominador globales. Forma directa; frágil para orden alto.
- **`'zpk'`** → `(z, p, k)`: ceros, polos, ganancia. Bueno para analizar estabilidad (|p|<1) y graficar.
- **`'sos'`** → matriz `(n_secciones, 6)`: cada fila `[b0 b1 b2 a0 a1 a2]`. **Preferida.**

### 3.1 Prototipos: `butter`, `cheby1`, `cheby2`, `ellip`

```
scipy.signal.butter(N, Wn, btype='low', *, output='ba', fs=None)
scipy.signal.cheby1(N, rp, Wn, btype='low', *, output='ba', fs=None)        # rp = rizado banda paso (dB)
scipy.signal.cheby2(N, rs, Wn, btype='low', *, output='ba', fs=None)        # rs = atenuación banda rechazo (dB)
scipy.signal.ellip (N, rp, rs, Wn, btype='low', *, output='ba', fs=None)
```
- **`N`**: orden del filtro.
- **`Wn`**: frecuencia(s) de corte. En Hz si se pasa `fs`; si no, normalizada a Nyquist (0–1).
- **`btype`**: `'low'`, `'high'`, `'bandpass'`, `'bandstop'`.
- **Devuelve:** según `output`.

### 3.2 Estimadores de orden: `buttord`, `cheb1ord`, `cheb2ord`, `ellipord`

```
N, Wn = scipy.signal.buttord(wp, ws, gpass, gstop, *, fs=None)
N, Wn = scipy.signal.cheb1ord(wp, ws, gpass, gstop, *, fs=None)
# análogo: cheb2ord, ellipord
```
- **`wp`, `ws`**: borde de banda de paso y de rechazo (Hz con `fs`, o normalizado).
- **`gpass`**: atenuación máxima en banda de paso (dB) = `Rp`.
- **`gstop`**: atenuación mínima en banda de rechazo (dB) = `As`.
- **Devuelve:** orden mínimo `N` y frecuencia crítica `Wn` lista para pasar al prototipo.

```python
# Butterworth LP: fp=40 Hz (Rp=1 dB), fr=60 Hz (As=40 dB), fs=500
N, Wn = signal.buttord(wp=40, ws=60, gpass=1, gstop=40, fs=fs)
sos = signal.butter(N, Wn, btype='low', output='sos', fs=fs)
print(N)                      # orden mínimo que cumple la plantilla
print(sos.shape)              # (ceil(N/2), 6)
```

### 3.3 Diseño genérico: `iirfilter`, `iirdesign`

```
scipy.signal.iirfilter(N, Wn, *, rp=None, rs=None, btype='band',
                       ftype='butter', output='ba', fs=None)
scipy.signal.iirdesign(wp, ws, gpass, gstop, *, ftype='ellip', output='ba', fs=None)
```
- **`iirfilter`**: prototipo + orden explícitos (`ftype='butter'|'cheby1'|'cheby2'|'ellip'`).
- **`iirdesign`**: dado el gabarito (`wp, ws, gpass, gstop`) calcula orden y diseña en un paso. Equivale a `*ord` + prototipo.

```python
sos = signal.iirdesign(wp=40, ws=60, gpass=1, gstop=40, ftype='ellip', output='sos', fs=fs)
```

### 3.4 Notch / peak: `iirnotch`, `iirpeak`

```
b, a = scipy.signal.iirnotch(w0, Q, fs=None)     # rechaza banda (notch)
b, a = scipy.signal.iirpeak (w0, Q, fs=None)      # realza banda (peak)
```
- **`w0`**: frecuencia central (Hz con `fs`).
- **`Q`**: factor de calidad; mayor `Q` → notch más estrecho. `BW ≈ w0 / Q`.
- **Devuelve:** `(b, a)` de un biquad (2.º orden). Convertir a SOS con `tf2sos` si se desea cascada.

```python
# Notch 50 Hz (red eléctrica) para ECG, Q=30
b_n, a_n = signal.iirnotch(w0=50, Q=30, fs=fs)
sos_n = signal.tf2sos(b_n, a_n)        # a SOS para encadenar con el LP
```

---

## 4. Análisis: respuesta en frecuencia, polos-ceros, retardo

### 4.1 `freqz` / `sosfreqz` — respuesta en frecuencia

```
w, H = scipy.signal.freqz(b, a=1, worN=512, *, fs=2*np.pi)
w, H = scipy.signal.sosfreqz(sos, worN=512, *, fs=2*np.pi)
```
- **`worN`**: número de puntos de frecuencia (o vector de frecuencias).
- **`fs`**: si se pasa, `w` sale en Hz (0–`fs/2`); por defecto en rad/muestra (0–π).
- **Devuelve:** `w` (frecuencias) y `H` (complejo). Magnitud y fase:

```python
w, H = signal.sosfreqz(sos, worN=2048, fs=fs)
mag_db = 20 * np.log10(np.abs(H) + 1e-12)     # +eps evita log10(0)
fase   = np.unwrap(np.angle(H))               # rad; *180/np.pi → grados
```

### 4.2 `group_delay` — retardo de grupo

```
w, gd = scipy.signal.group_delay((b, a), w=512, fs=2*np.pi)
```
- **Devuelve:** retardo de grupo en **muestras** vs frecuencia. Para FIR de fase lineal es constante = `N/2`. Concepto en [[01-fundamentos-pds]].

```python
w, gd = signal.group_delay((h, 1), fs=fs)     # FIR: a = 1
```

### 4.3 Conversión entre formas

```
z, p, k = scipy.signal.tf2zpk(b, a)
z, p, k = scipy.signal.sos2zpk(sos)
sos     = scipy.signal.zpk2sos(z, p, k)
sos     = scipy.signal.tf2sos(b, a)
```
- Útiles para pasar de la salida de un diseño a la forma que conviene analizar (`zpk` para estabilidad/polos-ceros) o aplicar (`sos`).

### 4.4 Diagrama de polos-ceros (no hay `zplane` nativo)

`scipy`/`matplotlib` no tienen `zplane`; se dibuja a mano el círculo unitario + scatter de ceros (`o`) y polos (`x`).

```python
import matplotlib.pyplot as plt

def zplane(z, p, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))
    theta = np.linspace(0, 2*np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), 'k--', lw=1)     # círculo unitario
    ax.scatter(np.real(z), np.imag(z), marker='o', facecolors='none',
               edgecolors='b', label='ceros')
    ax.scatter(np.real(p), np.imag(p), marker='x', color='r', label='polos')
    ax.axhline(0, color='gray', lw=0.5); ax.axvline(0, color='gray', lw=0.5)
    ax.set_aspect('equal'); ax.set_xlabel('Re'); ax.set_ylabel('Im')
    ax.legend(); ax.grid(True, alpha=0.3)
    return ax

z, p, k = signal.sos2zpk(sos)
zplane(z, p)        # estable ⟺ todos los |p| < 1 (dentro del círculo)
```

---

## 5. Aplicación del filtro

| Función | Forma | Fase | Uso |
|---|---|---|---|
| `lfilter(b, a, x)` | directa, **causal** | introduce retardo/fase | tiempo real, IIR/FIR `ba` |
| `sosfilt(sos, x)` | cascada SOS, causal | con retardo | IIR estable orden alto |
| `filtfilt(b, a, x)` | doble pasada (ida y vuelta) | **fase cero** | offline, FIR/IIR `ba` |
| `sosfiltfilt(sos, x)` | doble pasada SOS | **fase cero** | offline, IIR SOS |
| `convolve(x, h)` | convolución directa | FIR causal | FIR pequeño, didáctico |

```
y = scipy.signal.lfilter(b, a, x)
y = scipy.signal.sosfilt(sos, x)
y = scipy.signal.filtfilt(b, a, x)          # cuidado: requiere len(x) > 3*orden
y = scipy.signal.sosfiltfilt(sos, x)
y = scipy.signal.convolve(x, h, mode='same')
```

- **Causal (`lfilter`/`sosfilt`):** una sola pasada; añade retardo (FIR: `N/2` muestras; IIR: fase no lineal). Es lo que ocurre en el micro (Paso 5).
- **Fase cero (`filtfilt`/`sosfiltfilt`):** filtra hacia adelante y hacia atrás → retardo neto nulo y `|H|²` (el doble de atenuación en dB). Solo offline; **ideal para no deformar el ECG** en análisis.

```python
# ECG: notch 50 Hz + LP FIR 40 Hz, fase cero (análisis offline)
ecg_n  = signal.sosfiltfilt(sos_n, ecg)        # quita 50 Hz
ecg_f  = signal.filtfilt(h, 1, ecg_n)          # LP FIR, preserva morfología
```

---

## 6. Espectro

### 6.1 FFT con numpy (señal real)

```
X = numpy.fft.rfft(x)                      # espectro de señal real (mitad positiva)
f = numpy.fft.rfftfreq(len(x), d=1/fs)     # eje de frecuencias en Hz
```
- `rfft` devuelve `len(x)//2 + 1` valores complejos (evita la simetría redundante de `fft`).
- Magnitud normalizada y en dB:

```python
N  = len(x)
X  = np.fft.rfft(x)
f  = np.fft.rfftfreq(N, d=1/fs)
mag = np.abs(X) / N * 2                     # escala a amplitud (factor 2 por banda única)
mag_db = 20 * np.log10(mag + 1e-12)
```

### 6.2 PSD con Welch — `scipy.signal.welch`

```
f, Pxx = scipy.signal.welch(x, fs=1.0, *, window='hann', nperseg=256, noverlap=None)
```
- Promedia periodogramas de segmentos solapados → PSD suave (menos varianza que un FFT directo).
- **`nperseg`**: longitud de segmento (compromiso resolución vs varianza).
- **Devuelve:** `f` (Hz) y `Pxx` (densidad espectral de potencia, V²/Hz).

```python
f, Pxx = signal.welch(ecg, fs=fs, nperseg=1024)
# pico claro en 50 Hz antes del notch; debe desaparecer después
```

### 6.3 Ventanas — `get_window`

```
w = scipy.signal.get_window(window, Nx)    # window: 'hann','hamming','blackman',('kaiser',beta)...
```
- Genera una ventana de longitud `Nx` para aplicar antes de la FFT (reduce fuga espectral) o como argumento de `welch`/`firwin`.

```python
win = signal.get_window('hann', N)
X = np.fft.rfft(x * win)                    # FFT con ventana Hann
```

---

## 7. Métricas: SNR y RMSE (numpy)

Definiciones usadas para evaluar el filtrado (clean = señal limpia de referencia; noisy/filt = señal a evaluar). Ver [[01-fundamentos-pds]].

$$
\mathrm{SNR_{dB}} = 10\log_{10}\!\frac{\sum x_{\text{clean}}^2}{\sum (x_{\text{clean}} - x_{\text{eval}})^2}, \qquad
\mathrm{RMSE} = \sqrt{\frac{1}{N}\sum (x_{\text{clean}} - x_{\text{eval}})^2}
$$

```python
import numpy as np

def snr(clean, x):
    """SNR en dB tomando (clean - x) como ruido/error."""
    noise = clean - x
    return 10 * np.log10(np.sum(clean**2) / (np.sum(noise**2) + 1e-12))

def rmse(clean, x):
    return np.sqrt(np.mean((clean - x)**2))

# Mejora del filtrado: SNR debe subir, RMSE bajar
print("SNR in :", snr(ecg_clean, ecg_noisy))
print("SNR out:", snr(ecg_clean, ecg_filt))
print("RMSE   :", rmse(ecg_clean, ecg_filt))
```

---

## 8. matplotlib — patrones de graficado

### 8.1 Respuesta en frecuencia (magnitud + fase)

```python
import matplotlib.pyplot as plt

w, H = signal.sosfreqz(sos, worN=2048, fs=fs)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

ax1.plot(w, 20*np.log10(np.abs(H) + 1e-12))
ax1.set_ylabel('|H| [dB]'); ax1.grid(True, alpha=0.3)
ax1.axvline(40, color='r', ls='--', lw=1)          # marca fc

ax2.plot(w, np.unwrap(np.angle(H)) * 180/np.pi)
ax2.set_ylabel('Fase [°]'); ax2.set_xlabel('Frecuencia [Hz]'); ax2.grid(True, alpha=0.3)
fig.suptitle('Respuesta en frecuencia'); fig.tight_layout()
plt.show()
```

### 8.2 Señal en el tiempo y FFT

```python
t = np.arange(len(ecg)) / fs
fig, (a, b) = plt.subplots(2, 1, figsize=(8, 6))
a.plot(t, ecg, label='crudo'); a.plot(t, ecg_filt, label='filtrado')
a.set_xlabel('t [s]'); a.set_ylabel('Amplitud'); a.legend(); a.grid(alpha=0.3)

f = np.fft.rfftfreq(len(ecg), 1/fs)
b.plot(f, 20*np.log10(np.abs(np.fft.rfft(ecg)) + 1e-12))
b.set_xlabel('f [Hz]'); b.set_ylabel('|X| [dB]'); b.grid(alpha=0.3)
fig.tight_layout(); plt.show()
```

---

## 9. scikit-learn — agente por árbol de decisión / MLP

Estrategias 2 (árbol) y 5 (MLP) del agente; ver el diseño completo y las variables E/S en [[05-agente-ia]]. Aquí solo las firmas y un ejemplo sintético mínimo.

```
sklearn.tree.DecisionTreeClassifier(max_depth=None, criterion='gini', random_state=None)
sklearn.neural_network.MLPClassifier(hidden_layer_sizes=(100,), max_iter=200, random_state=None)
sklearn.model_selection.train_test_split(X, y, test_size=0.25, random_state=None)
sklearn.tree.export_text(clf, feature_names=None)     # reglas del árbol en texto
```
- Métodos clave de los clasificadores: `.fit(X, y)`, `.predict(X)`, `.predict_proba(X)` (confianza), `.score(X, y)`.

```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(0)
n = 2000
# Features del agente: [fase_lineal(0/1), ram_kB, orden_estimado, transicion_estrecha(0/1)]
fase  = rng.integers(0, 2, n)
ram   = rng.uniform(1, 64, n)
orden = rng.integers(4, 120, n)
trans = rng.integers(0, 2, n)
X = np.column_stack([fase, ram, orden, trans])

# Etiqueta por reglas de referencia ([[00-enunciado]]): 1=FIR, 0=IIR
y = np.where(fase == 1, 1,                                  # fase lineal estricta → FIR
     np.where((ram < 2) & (orden > 50), 0,                 # poca RAM y FIR grande → IIR
     np.where(trans == 1, 0, 1))).astype(int)              # transición estrecha → IIR

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)
clf = DecisionTreeClassifier(max_depth=4, random_state=0).fit(Xtr, ytr)
print("acc:", clf.score(Xte, yte))
print(export_text(clf, feature_names=['fase', 'ram_kB', 'orden', 'trans']))

# Inferencia para un caso nuevo: ECG, fase lineal sí, 8 kB, orden 80, transición amplia
caso = [[1, 8, 80, 0]]
print("FIR" if clf.predict(caso)[0] == 1 else "IIR",
      "conf:", clf.predict_proba(caso).max())
```

MLP (estrategia 5) — mismo `X, y`, solo cambia el estimador:

```python
from sklearn.neural_network import MLPClassifier
mlp = MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=500, random_state=0).fit(Xtr, ytr)
print("acc MLP:", mlp.score(Xte, yte))
```

---

## 10. scikit-fuzzy — agente difuso

Estrategia 3 (lógica difusa) del agente; ver [[05-agente-ia]]. Modela las variables con grados de pertenencia y combina reglas.

```
ctrl.Antecedent(universe, label)        # variable de entrada
ctrl.Consequent(universe, label)        # variable de salida
fuzz.trimf(x, [a, b, c])                # función de pertenencia triangular
ctrl.Rule(antecedente, consecuente)
ctrl.ControlSystem([reglas...])
ctrl.ControlSystemSimulation(sistema)
```

```python
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Entradas: SNR de entrada (dB) y RAM disponible (kB). Salida: "score FIR" (0-100)
snr_in = ctrl.Antecedent(np.arange(0, 41, 1), 'snr_in')
ram    = ctrl.Antecedent(np.arange(0, 65, 1), 'ram')
fir    = ctrl.Consequent(np.arange(0, 101, 1), 'fir')

snr_in['bajo'] = fuzz.trimf(snr_in.universe, [0, 0, 20])
snr_in['alto'] = fuzz.trimf(snr_in.universe, [10, 40, 40])
ram['poca']    = fuzz.trimf(ram.universe, [0, 0, 8])
ram['mucha']   = fuzz.trimf(ram.universe, [4, 64, 64])
fir['no']      = fuzz.trimf(fir.universe, [0, 0, 50])
fir['si']      = fuzz.trimf(fir.universe, [50, 100, 100])

r1 = ctrl.Rule(ram['mucha'] & snr_in['alto'], fir['si'])   # holgura → FIR
r2 = ctrl.Rule(ram['poca'],                    fir['no'])   # poca RAM → IIR
sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem([r1, r2]))

sim.input['snr_in'] = 30; sim.input['ram'] = 32
sim.compute()
print(sim.output['fir'])         # >50 ⇒ recomienda FIR; <50 ⇒ IIR
```

---

## 11. SDK anthropic — agente vía API (IA generativa)

Estrategia 4 del agente ([[05-agente-ia]]). Se envía un prompt estructurado con las restricciones y se pide salida **JSON**. Modelos: `claude-opus-4-8` (máxima capacidad) o `claude-haiku-4-5` (rápido y económico) — elegir según coste/latencia.

> **Nunca** incrustar la API key en el código. Leerla del entorno: `os.environ['ANTHROPIC_API_KEY']` (el SDK la toma automáticamente si la variable existe).

```
from anthropic import Anthropic
client = Anthropic()                      # toma ANTHROPIC_API_KEY del entorno
client.messages.create(model=..., system=..., messages=[...], max_tokens=...)
```

```python
import os, json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])   # o simplemente Anthropic()

SYSTEM = (
    "Eres un asesor de diseño de filtros digitales para sistemas embebidos. "
    "Recomienda FIR o IIR y la estructura (DF I, DF II, SOS, lattice) según las "
    "restricciones. Responde SOLO con JSON válido, sin texto adicional, con las claves: "
    "recomendacion (FIR|IIR), estructura, justificacion, confianza (0-1)."
)

restricciones = {
    "aplicacion": "ECG", "fs_Hz": 500, "fase_lineal": True,
    "ram_kB": 8, "mips": 80, "snr_in_dB": 12,
    "latencia": "media", "transicion": "amplia",
}

msg = client.messages.create(
    model="claude-haiku-4-5",                      # o "claude-opus-4-8"
    max_tokens=512,
    system=SYSTEM,
    messages=[{"role": "user",
               "content": f"Restricciones:\n{json.dumps(restricciones, ensure_ascii=False)}"}],
)
salida = json.loads(msg.content[0].text)
print(salida["recomendacion"], salida["estructura"], round(salida["confianza"], 2))
# {recomendacion:'FIR', estructura:'DF I', justificacion:'...', confianza:0.9}
```

Notas:
- **Coste/latencia:** cada llamada consume tokens (coste $) y tarda cientos de ms a segundos; no apto para tiempo real en el micro.
- **No determinismo:** la salida puede variar entre llamadas; por eso se fija el formato JSON y se valida con `json.loads`. Conviene `temperature=0` (si se expone) y validar/normalizar el JSON recibido.
- **Robustez:** envolver el `json.loads` en `try/except` y reintentar o caer a una regla IF-THEN de respaldo si el modelo devuelve texto no parseable.

---

## 12. Plantilla integradora (esqueleto)

Flujo completo Paso 3 en Python: diseño → respuesta en frecuencia → filtrado → FFT → métricas.

```python
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

fs = 500                                                  # ECG, Anexo I-A
t  = np.arange(0, 4, 1/fs)                                # 4 s
ecg_clean = np.sin(2*np.pi*1.2*t)                         # latido sintético (placeholder)
ruido     = 0.3*np.sin(2*np.pi*50*t) + 0.1*np.random.randn(t.size)
ecg       = ecg_clean + ruido                            # señal contaminada

# 1) Diseño: notch 50 Hz (IIR) + LP FIR 40 Hz (fase lineal)
b_n, a_n = signal.iirnotch(w0=50, Q=30, fs=fs)
sos_n    = signal.tf2sos(b_n, a_n)
h_lp     = signal.firwin(numtaps=101, cutoff=40, fs=fs, window='hamming')

# 2) Respuesta en frecuencia del LP
w, H = signal.freqz(h_lp, 1, worN=2048, fs=fs)
mag_db = 20*np.log10(np.abs(H) + 1e-12)

# 3) Filtrado fase cero (offline) → no deforma P-QRS-T
ecg_f = signal.sosfiltfilt(sos_n, ecg)
ecg_f = signal.filtfilt(h_lp, 1, ecg_f)

# 4) FFT antes/después
f  = np.fft.rfftfreq(ecg.size, 1/fs)
Xi = 20*np.log10(np.abs(np.fft.rfft(ecg))   + 1e-12)
Xo = 20*np.log10(np.abs(np.fft.rfft(ecg_f)) + 1e-12)

# 5) Métricas (mejora del SNR, caída del RMSE)
snr  = lambda c, x: 10*np.log10(np.sum(c**2)/(np.sum((c-x)**2)+1e-12))
print("SNR in :", round(snr(ecg_clean, ecg),   2),
      "| SNR out:", round(snr(ecg_clean, ecg_f), 2),
      "| RMSE  :", round(np.sqrt(np.mean((ecg_clean-ecg_f)**2)), 4))
```

---

## 13. Resumen de equivalencias (cierre)

| Tarea | Python (este doc) | Octave/MATLAB ([[06-octave]]) |
|---|---|---|
| FIR ventana | `firwin` | `fir1` |
| FIR equiripple | `remez` | `firpm` |
| Dimensionar Kaiser | `kaiserord` | `kaiserord` |
| IIR prototipo | `butter`/`cheby1`/`cheby2`/`ellip` | íd. |
| Orden IIR | `buttord`/`cheb1ord`/… | íd. |
| Notch | `iirnotch` | `iirnotch` |
| Respuesta frecuencia | `freqz`/`sosfreqz` | `freqz` |
| Polos-ceros | `zplane` casero (matplotlib) | `zplane` |
| Filtrar causal | `lfilter`/`sosfilt` | `filter`/`sosfilt` |
| Fase cero | `filtfilt`/`sosfiltfilt` | `filtfilt` |
| PSD | `welch` | `pwelch` |

Criterios de cuándo elegir cada herramienta (FIR vs IIR, ventana vs equiripple, SOS, punto fijo) en [[04-criterios-diseno]]. Fundamentos en [[01-fundamentos-pds]].
