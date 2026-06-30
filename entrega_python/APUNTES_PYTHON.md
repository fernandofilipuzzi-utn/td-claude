# Apuntes de PDS y Agente de IA — Implementación en Python

> **Asignatura:** Técnicas Digitales III — Procesamiento Digital de Señales / Filtrado Digital (2026).
> **Proyecto:** Diseño, simulación e implementación de un sistema de filtrado digital FIR/IIR **asistido por IA** para una aplicación de ingeniería (Evaluación Basada en Problemas, modalidad grupal).
> **Documento síntesis de:** `../_kb/00-enunciado.md`, `01-fundamentos-pds.md`, `02-fir.md`, `03-iir.md`, `04-criterios-diseno.md`, `05-agente-ia.md`, `07-python.md`.
> **Foco de esta entrega:** las **herramientas de Python** (numpy, scipy.signal, matplotlib, scikit-learn, scikit-fuzzy, SDK `anthropic`) y la **generación del agente de decisión IA** (árbol de decisión, lógica difusa, API LLM Claude, MLP), más los criterios de diseño y selección de filtros.

Documento **autónomo**: el lector no necesita abrir el KB. Las referencias `../_kb/NN.md` aparecen como *ampliación* opcional. No se ejecuta código ni se instalan paquetes (solo se documenta el comando); no hay claves de API reales.

---

## 0. Índice

1. [Portada y propósito](#1-portada-y-propósito)
2. [Mapa de conocimientos (temas ↔ pasos del examen ↔ secciones)](#2-mapa-de-conocimientos)
3. [Fundamentos de PDS](#3-fundamentos-de-pds)
4. [Diseño de filtros FIR](#4-diseño-de-filtros-fir)
5. [Diseño de filtros IIR](#5-diseño-de-filtros-iir)
6. [Criterios de ingeniería para el diseño y selección de filtros](#6-criterios-de-ingeniería-para-el-diseño-y-selección-de-filtros)
7. [Herramientas Python (núcleo de la entrega)](#7-herramientas-python-núcleo-de-la-entrega)
8. [Agente de decisión IA — enfoque Python (núcleo de la entrega)](#8-agente-de-decisión-ia--enfoque-python-núcleo-de-la-entrega)
9. [Flujo de trabajo recomendado en Python](#9-flujo-de-trabajo-recomendado-en-python)
10. [Glosario de símbolos + Referencias](#10-glosario-de-símbolos--referencias)

---

## 1. Portada y propósito

El **examen parcial integrador** plantea un proyecto completo de filtrado digital con cinco pasos evaluables. Sobre una señal de ingeniería (caso canónico transversal: **ECG**, `fs = 500 Hz`, banda útil ≈ 0.5–40 Hz, interferencia de red 50/60 Hz), el alumno debe:

| Paso | Título | Núcleo técnico |
|------|--------|----------------|
| **1** | Análisis del problema y especificaciones | Caracterizar la señal; justificar `fs` por Nyquist-Shannon; banda útil vs ruido; tipo de filtro (LP/HP/BP/BR-notch); `fp`, `fr`, `Rp` (dB), `As` (dB); fase lineal sí/no; tabla de requerimientos |
| **2** | Desarrollo matemático del diseño | **FIR:** método (ventanas o Parks-McClellan), orden `N`, coeficientes `h[n]`, simetría → fase lineal, `H(z)`. **IIR:** prototipo, orden `N`, `Ha(s)` polos/ceros, **transformada bilineal** con pre-distorsión (*prewarping*), `H(z)`, ecuación en diferencias, estabilidad |
| **3** | Simulación en MATLAB/Octave o **Python** | Respuesta en frecuencia (\|H\| dB y fase), `h[n]`, retardo de grupo, polos-ceros; señal contaminada antes/después; FFT/PSD; métricas SNR/RMSE; **tabla comparativa FIR vs IIR** |
| **4** | **Agente de decisión asistido por IA** | Sistema que recomienda **FIR o IIR** + estructura según restricciones del sistema embebido |
| **5** | Implementación en microcontrolador | Arduino/STM32/ESP32; punto fijo (Q) vs float; buffers; validación; fuentes de error |

**Alcance de este documento.** Es la entrega **Python**: profundiza en (i) los fundamentos teóricos, (ii) **las herramientas de Python** para diseñar, simular y evaluar filtros, y (iii) **la generación del agente de IA** con técnicas de machine learning, lógica difusa y LLM. El Paso 5 (embebido) se cubre solo como criterio de diseño (sección 6).

---

## 2. Mapa de conocimientos

Tabla **temas ↔ pasos del examen (1–5) ↔ secciones de este documento**:

| Tema | Pasos del examen | Sección aquí | Módulo KB origen |
|------|:---------------:|:------------:|-----------------|
| Muestreo, Nyquist, aliasing, espectro | 1 | §3 | `01` |
| DTFT / DFT / FFT / Transformada Z | 1, 3 | §3 | `01` |
| Convolución, fase lineal, retardo de grupo | 1, 3 | §3 | `01` |
| Métricas SNR / RMSE / distorsión de fase | 3 | §3, §7.7 | `01`, `07` |
| Diseño FIR (ventanas, Parks-McClellan, orden, `H(z)`) | 2 | §4 | `02` |
| Diseño IIR (prototipos, bilineal, prewarping, SOS) | 2 | §5 | `03` |
| Criterios FIR vs IIR, ventana/prototipo, MACs, punto fijo | 1, 4, 5 | §6 | `04` |
| Herramientas Python (numpy, scipy.signal, matplotlib) | 3 | §7 | `07` |
| Agente de decisión IA (reglas, árbol, fuzzy, LLM, MLP) | 4 | §8 | `05`, `07` |
| Flujo de trabajo Python (entorno, orden de pasos) | 3, 4 | §9 | `07` |

> **Ampliación:** mapa maestro en `../_kb/INDEX.md`.

---

## 3. Fundamentos de PDS

> Síntesis fiel de `../_kb/01-fundamentos-pds.md`.

### 3.1 Señal analógica vs digital, muestreo y cuantización

Una **señal analógica** $x_a(t)$ es continua en tiempo y amplitud; una **señal digital** $x[n]$ es discreta en ambos ejes. El paso ocurre en dos etapas: **muestreo** (discretización temporal) y **cuantización** (discretización de amplitud a $2^B$ niveles).

El muestreo ideal produce
$$
x[n] = x_a(nT), \qquad f_s = \frac{1}{T}\ [\text{Hz}], \qquad \omega_s = 2\pi f_s\ [\text{rad/s}].
$$

La **frecuencia digital (normalizada)** es independiente de $f_s$:
$$
\omega = \Omega T = \frac{2\pi f}{f_s}\ [\text{rad/muestra}], \qquad \omega \in (-\pi, \pi],
$$
donde $\omega = \pi$ corresponde exactamente a $f = f_s/2$.

**Cuantización.** Con $B$ bits y rango pico a pico $V_{pp}$, el paso (LSB) es $\Delta = V_{pp}/2^B$. Modelando el error como ruido uniforme en $[-\Delta/2, \Delta/2]$ ($\sigma_q^2 = \Delta^2/12$), la relación señal-ruido de cuantización es:
$$
\mathrm{SQNR}_{\max} \approx 6{,}02\,B + 1{,}76\ [\text{dB}].
$$
Cada bit añade $\approx 6$ dB. Es un piso de ruido irreducible y fuente de error en el embebido (Paso 5).

### 3.2 Teorema de Nyquist-Shannon y aliasing

> Una señal de **banda limitada** ($X_a(f) = 0$ para $|f| \ge f_B$) queda completamente determinada por sus muestras tomadas a $f_s > 2 f_B$, y se reconstruye con interpolación sinc.

$2 f_B$ es la **tasa de Nyquist**; su mitad $f_N = f_s/2$ es la **frecuencia de Nyquist**. Si $f_s \le 2 f_B$, las réplicas espectrales se solapan (**aliasing**): una frecuencia $f_0 > f_s/2$ aparece plegada en
$$
f_{\text{alias}} = \left| f_0 - f_s \cdot \operatorname{round}\!\left(\frac{f_0}{f_s}\right) \right|.
$$
El aliasing es **irreversible**; por eso se usa un **filtro anti-aliasing analógico** (paso bajo, antes del ADC).

**Ejemplo numérico.** Con $f_s = 500$ Hz ($f_N = 250$ Hz): una componente parásita de **480 Hz** se pliega a
$$
f_{\text{alias}} = |480 - 500\cdot\operatorname{round}(480/500)| = |480 - 500| = 20\ \text{Hz},
$$
contaminando la banda útil sin posibilidad de remoción digital.

**Justificación de $f_s = 500$ Hz (ECG).** Banda útil $f_B = 40$ Hz ⇒ Nyquist mínimo $80$ Hz. Elegir $500$ Hz da factor de sobremuestreo $\approx 6{,}25\times$: (i) banda de transición amplia al anti-aliasing analógico; (ii) la red de 50 Hz queda muy por debajo de $f_N = 250$ Hz, se muestrea sin alias y se elimina con un **notch IIR**; (iii) mejor resolución temporal del QRS y margen para el LP FIR de 40 Hz.

### 3.3 Representaciones tiempo ↔ frecuencia

**DTFT** (función continua y periódica $2\pi$):
$$
X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n]\, e^{-j\omega n}.
$$

**DFT** (muestrea la DTFT en $N$ puntos $\omega_k = 2\pi k/N$):
$$
X[k] = \sum_{n=0}^{N-1} x[n]\, e^{-j 2\pi k n / N}, \qquad k = 0,\dots,N-1.
$$
La **FFT** computa la DFT en $O(N \log N)$, con valores idénticos. **Resolución frecuencial:**
$$
\boxed{\;\Delta f = \frac{f_s}{N}\;}\ [\text{Hz/bin}], \qquad f_k = k\,f_s/N.
$$
Ejemplo ECG: $f_s = 500$ Hz, $N = 5000$ (10 s) ⇒ $\Delta f = 0{,}1$ Hz, suficiente para resolver el pico de 50 Hz. Truncar a $N$ muestras aplica una ventana rectangular implícita y produce *fuga espectral* (leakage); las ventanas (Hann/Hamming/Blackman) la reducen ensanchando el lóbulo principal.

**Transformada Z** (generaliza la DTFT a todo $\mathbb{C}$):
$$
X(z) = \sum_{n=-\infty}^{\infty} x[n]\, z^{-n}, \qquad z = r e^{j\omega}.
$$
La **ROC** no incluye polos. Un sistema LTI causal es **estable (BIBO)** sii la ROC incluye el círculo unitario $|z|=1$, es decir **todos los polos dentro** del círculo. Evaluando $X(z)$ sobre $|z|=1$ se recupera la DTFT. El **círculo unitario** es el eje de frecuencias discreto: un **cero** cerca del círculo crea una muesca (base del notch); un **polo** cerca crea realce resonante.

### 3.4 Convolución y filtrado

Un sistema LTI queda caracterizado por su **respuesta al impulso** $h[n]$. **Filtrar es convolucionar:**
$$
y[n] = x[n] * h[n] = \sum_{k=-\infty}^{\infty} x[k]\, h[n-k].
$$
Para FIR la suma es directa (soporte finito); para IIR conviene la forma recursiva (**ecuación en diferencias**):
$$
y[n] = \sum_{k=0}^{M} b_k\, x[n-k] - \sum_{k=1}^{N} a_k\, y[n-k].
$$
En Z la convolución es producto: $Y(z) = H(z) X(z)$, con $H(z) = B(z)/A(z)$ (ceros = raíces de $B$, polos = raíces de $A$). La **respuesta en frecuencia** es $H(e^{j\omega}) = |H(e^{j\omega})|\, e^{j\phi(\omega)}$.

### 3.5 Magnitud, fase, fase lineal y retardo de grupo

**Magnitud en dB:** $|H(e^{j\omega})|_{\text{dB}} = 20\log_{10}|H(e^{j\omega})|$. Banda de paso $\approx 0$ dB; banda de rechazo $\to -\infty$ dB. Especificaciones: $R_p$ (rizado de paso) y $A_s$ (atenuación de rechazo), ambas en dB.

**Fase lineal:** $\phi(\omega) = -\alpha\,\omega\ (+\beta)$ ⇒ **retardo constante** de $\alpha$ muestras para todas las frecuencias ⇒ la forma de onda se traslada **sin deformarse**. Si el retardo depende de la frecuencia, la **morfología se distorsiona**. En ECG es crítico (diagnóstico depende de amplitudes/tiempos relativos de P-QRS-T); por eso el LP de 40 Hz se exige **FIR de fase lineal**. Los FIR simétricos ($h[n] = \pm h[M-1-n]$) garantizan fase lineal exacta con $\alpha = (M-1)/2$.

**Retardo de grupo:**
$$
\boxed{\;\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}\;}\ [\text{muestras}].
$$
Fase lineal ⇒ $\tau_g = \alpha = $ constante (FIR simétrico de $M$ taps: $\tau_g = (M-1)/2$). Fase no lineal ⇒ $\tau_g(\omega)$ varía ⇒ distorsión morfológica; la **variación** de $\tau_g$ en banda útil la cuantifica.

### 3.6 Densidad espectral de potencia (PSD)

La **PSD** $S_x(f)$ describe el reparto de potencia por frecuencia (Wiener-Khinchin: TF de la autocorrelación). Estimación práctica: **periodograma** $\hat S_x[k] = \tfrac{1}{N}|X[k]|^2$ o método de **Welch** (promedio de periodogramas de segmentos solapados y ventaneados → menos varianza). En un ECG ruidoso típico la PSD muestra: lóbulo diagnóstico 0.5–40 Hz, **pico agudo en 50 Hz** (red), y piso de banda ancha. Comparar PSD **antes vs después** del filtrado muestra la eficacia.

### 3.7 Métricas de calidad del filtrado

A partir de la señal **limpia** $s[n]$, **ruidosa** $x[n]=s[n]+r[n]$ y **filtrada** $\hat s[n]$:

**SNR (dB):**
$$
\boxed{\;\mathrm{SNR}_{\text{dB}} = 10\log_{10}\frac{\sum_n s^2[n]}{\sum_n(\hat s[n]-s[n])^2}\;}, \qquad \Delta\mathrm{SNR} = \mathrm{SNR}_{\text{out}} - \mathrm{SNR}_{\text{in}}.
$$

**RMSE:**
$$
\mathrm{RMSE} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1}(\hat s[n]-s[n])^2}\qquad (\text{NRMSE} = \mathrm{RMSE}/\text{rango}(s)).
$$

**Distorsión de fase:** variación de $\tau_g$ en banda útil ($\max_\omega \tau_g - \min_\omega \tau_g$), o error residual tras compensar el retardo nominal.

**Ejemplo numérico (SNR).** $P_{\text{señal}} = 1000$, ruido inicial $P_r = 250$:
$$
\mathrm{SNR}_{\text{in}} = 10\log_{10}\tfrac{1000}{250} = 6{,}02\ \text{dB}.
$$
Tras notch + LP, ruido residual $P_e = 10$:
$$
\mathrm{SNR}_{\text{out}} = 10\log_{10}\tfrac{1000}{10} = 20\ \text{dB}, \qquad \Delta\mathrm{SNR} \approx \mathbf{14\ dB}.
$$

---

## 4. Diseño de filtros FIR

> Síntesis fiel de `../_kb/02-fir.md`, con el ejemplo ECG (Hamming, $f_c=40$, $f_s=500$).

### 4.1 Qué es un filtro FIR

Un FIR (*Finite Impulse Response*) tiene $h[n]$ de soporte **finito**: orden $N$ ⇒ $N+1$ coeficientes (*taps*). Ecuación en diferencias (convolución finita, sin recursión):
$$
y[n] = \sum_{k=0}^{N} h[k]\, x[n-k], \qquad \text{coste} \approx N+1\ \text{MACs/muestra}.
$$
Función de transferencia (**solo ceros**):
$$
H(z) = \sum_{k=0}^{N} h[k]\, z^{-k}.
$$
Todos los polos están en $z=0$ ⇒ **incondicionalmente estable** (BIBO), no puede desestabilizarse por cuantización de coeficientes.

| Propiedad | FIR |
|---|---|
| Memoria | $N+1$ coef. + buffer de $N$ muestras |
| Estabilidad | Siempre estable |
| Fase lineal | Exacta por simetría de $h[n]$ |
| Orden típico | Alto (decenas a cientos) |
| Coste | $\approx N+1$ MACs/muestra |

### 4.2 Fase lineal y los 4 tipos

Fase lineal sii coeficientes **simétricos** ($h[n]=h[N-n]$, fase lineal pura) o **antisimétricos** ($h[n]=-h[N-n]$, +desfase $90°$). Retardo de grupo constante:
$$
\tau_g = \frac{N}{2}\ \text{muestras} = \frac{N}{2 f_s}\ \text{s}.
$$

| Tipo | Simetría | $N$ | Coef. $N+1$ | Usos |
|------|----------|-----|-------------|------|
| **I** | Simétrico | par | impar | LP, HP, BP, BR (el más versátil) |
| **II** | Simétrico | impar | par | $H(e^{j\pi})=0$ → **no HP ni BR** |
| **III** | Antisimétrico | par | impar | $H(0)=H(e^{j\pi})=0$ → BP, derivadores, Hilbert |
| **IV** | Antisimétrico | impar | par | $H(0)=0$ → HP, derivadores, Hilbert |

**Regla:** pasa-bajos general → **Tipo I**. Antisimétrico siempre tiene $H(0)=0$ (inútil para LP).

### 4.3 Método de ventanas

Partir de la respuesta ideal infinita y truncar/suavizar con ventana $w[n]$: $h[n] = h_d[n]\cdot w[n]$. Para un pasa-bajos ideal con $\omega_c = 2\pi f_c/f_s$:
$$
h_d[n] = \frac{\sin\!\big(\omega_c(n-\tfrac N2)\big)}{\pi(n-\tfrac N2)}, \qquad h_d\!\left[\tfrac N2\right]=\frac{\omega_c}{\pi}.
$$
El truncamiento abrupto produce el **fenómeno de Gibbs** (sobreimpulso fijo ~9% que no desaparece al crecer $N$). Compromiso fundamental: **atenuación de lóbulos laterales ↔ ancho de transición**.

| Ventana | Lóbulo principal | Atenuación lóbulo lateral | $A_s$ lograble | $N$ aprox. |
|---------|:---:|:---:|:---:|:---:|
| Rectangular | $4\pi/(N+1)$ | $-13$ dB | $\approx 21$ dB | $0{,}9\,f_s/\Delta f$ |
| Hann | $8\pi/(N+1)$ | $-31$ dB | $\approx 44$ dB | $3{,}1\,f_s/\Delta f$ |
| **Hamming** | $8\pi/(N+1)$ | $-41$ dB | $\approx 53$ dB | $3{,}3\,f_s/\Delta f$ |
| Blackman | $12\pi/(N+1)$ | $-57$ dB | $\approx 74$ dB | $5{,}5\,f_s/\Delta f$ |
| **Kaiser** | depende de $\beta$ | ajustable | **a pedido** | fórmula |

Definiciones ($0\le n\le N$, $M=N$):
$$
w_{\text{Hamming}}[n] = 0{,}54 - 0{,}46\cos\frac{2\pi n}{M}, \qquad w_{\text{Hann}}[n] = 0{,}5 - 0{,}5\cos\frac{2\pi n}{M}.
$$

**Kaiser (paramétrica).** A partir de $A = A_s$ (dB):
$$
\beta = \begin{cases} 0{,}1102(A-8{,}7), & A>50 \\ 0{,}5842(A-21)^{0{,}4}+0{,}07886(A-21), & 21\le A\le 50 \\ 0, & A<21 \end{cases}
\qquad
\boxed{\,N \approx \frac{A-8}{2{,}285\,\Delta\omega}\,}, \quad \Delta\omega = \frac{2\pi\Delta f}{f_s}.
$$

### 4.4 Ejemplo numérico canónico (ECG)

| Parámetro | Valor |
|-----------|-------|
| Tipo | Pasa-bajos FIR, fase lineal |
| $f_s$ | 500 Hz |
| $f_c$ | 40 Hz |
| Transición | $40\to50$ Hz ⇒ $\Delta f = 10$ Hz |
| Ventana | Hamming ($A_s \approx 53$ dB) |

**Orden (Hamming):**
$$
N \approx \frac{3{,}3\,f_s}{\Delta f} = \frac{3{,}3\times500}{10} = 165 \;\Rightarrow\; N=166\ (\text{par, Tipo I}) \;\Rightarrow\; 167\ \text{coeficientes}.
$$
Verificación con Kaiser ($A_s=53$): $\Delta\omega=0{,}1257$, $N\approx(53-8)/(2{,}285\cdot0{,}1257)\approx 157$ (mismo orden de magnitud, coherente).

**Frecuencia de corte de diseño** (centro de transición): $f_c' = 45$ Hz ⇒ normalizada $45/250 = 0{,}18$, $\omega_c = 0{,}5655$ rad.

**Coeficientes:**
$$
h[n] = \frac{\sin\!\big(\omega_c(n-83)\big)}{\pi(n-83)}\cdot\Big(0{,}54-0{,}46\cos\tfrac{2\pi n}{166}\Big), \quad n=0,\dots,166.
$$
Centro $h[83] \approx 0{,}18$; simetría $h[n]=h[166-n]$.

**Retardo de grupo:**
$$
\tau_g = \frac{166}{2} = 83\ \text{muestras} = \frac{83}{500} = 0{,}166\ \text{s} = \mathbf{166\ ms}\ (\text{constante}).
$$

**Coste:** $\approx 167$ MACs/muestra $= 83{,}5$ kMAC/s a 500 Hz. Viable en ESP32/STM32 con FPU; inviable en Arduino UNO punto fijo.

### 4.5 Parks-McClellan / Remez (equiripple)

El método de ventanas reparte el error de forma desigual. **Parks-McClellan** (intercambio de Remez) diseña el FIR **óptimo minimax** (reparte el error máximo uniformemente → *equiripple*):
$$
\min_h\ \max_{\omega\in\text{bandas}}\ |W(\omega)[A(\omega)-D(\omega)]|.
$$
El **teorema de alternancia** garantiza unicidad (el error alcanza $\pm\delta$ alternado en $\ge L+2$ frecuencias). Estimación de orden (Kaiser para equiripple):
$$
N \approx \frac{-10\log_{10}(\delta_p\delta_s)-13}{2{,}324\,\Delta\omega}.
$$
**Conviene equiripple** cuando el orden mínimo es prioritario (cómputo/memoria ajustados) o se requieren ripples distintos en paso y rechazo. **Conviene ventanas** cuando se quiere un diseño simple/robusto; Kaiser ya da casi-óptimo con una fórmula.

### 4.6 $H(z)$ y verificación

$H(z) = \sum_{k=0}^{166} h[k]z^{-k}$ con $h[k]=h[166-k]$. Qué mirar en simulación (Paso 3):
1. **Magnitud** dB: comprobar $f_c$, ripple $\le R_p$, atenuación $\ge A_s$.
2. **Fase / $\tau_g$:** fase lineal recta, $\tau_g = N/2$ constante.
3. **Polos-ceros:** polos en $z=0$; ceros en cuádruplas recíprocas conjugadas ($z_0, z_0^*, 1/z_0, 1/z_0^*$).
4. **Suma de coeficientes:** $\sum_k h[k] = H(e^{j0}) \approx 1$ (ganancia DC unitaria).

---

## 5. Diseño de filtros IIR

> Síntesis fiel de `../_kb/03-iir.md`, que es la **AUTORIDAD** para el ejemplo numérico IIR.

### 5.1 Qué es un filtro IIR

Un IIR (*Infinite Impulse Response*) es **recursivo**: la salida depende de entradas **y** salidas pasadas (realimentación) ⇒ $h[n]$ de duración infinita. Ecuación en diferencias:
$$
\boxed{\;y[n] = \sum_{k=0}^{M} b_k x[n-k] - \sum_{k=1}^{N} a_k y[n-k]\;}\qquad (a_0=1).
$$
Función de transferencia:
$$
H(z) = \frac{B(z)}{A(z)} = \frac{b_0+b_1z^{-1}+\cdots+b_Mz^{-M}}{1+a_1z^{-1}+\cdots+a_Nz^{-N}}.
$$
Los **polos** (raíces de $A$) introducen realimentación y $h[n]$ infinita; **su ubicación determina la estabilidad**.

| Aspecto | **IIR** | **FIR** |
|--------|---------|---------|
| $h[n]$ | Infinita | Finita |
| Polos | Sí | No (solo en $z=0$) |
| Orden p/ igual $A_s$ | **Bajo** (2–10) | Alto (5–20× mayor) |
| Fase | **No lineal** | Lineal exacta si simétrica |
| Estabilidad | Verificar $|d_k|<1$ | Garantizada |
| Sensibilidad cuantización | Alta → usar SOS | Baja |
| Coste | $\approx 5\cdot$secciones MACs | $\approx N+1$ MACs |

### 5.2 Prototipos analógicos

El diseño parte de un prototipo analógico $H_a(s)$ y aplica la **transformada bilineal**. Los cuatro prototipos:

| Prototipo | Ripple paso | Ripple rechazo | Transición | Fase | Orden | Ceros finitos |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Butterworth** (máx. plano) | No | No | Suave | La mejor | **Máximo** | No |
| **Chebyshev I** | Sí ($R_p$) | No | Media-alta | Media | Medio | No |
| **Chebyshev II** | No | Sí ($A_s$) | Media-alta | Media | Medio | Sí ($j\Omega$) |
| **Elíptico (Cauer)** | Sí | Sí | **La más abrupta** | La peor | **Mínimo** | Sí ($j\Omega$) |

Butterworth (máx. plano): $|H_a(j\Omega)|^2 = 1/[1+(\Omega/\Omega_c)^{2N}]$. Chebyshev I: $|H_a|^2 = 1/[1+\varepsilon^2 T_N^2(\Omega/\Omega_p)]$. **Regla mnemotécnica:** *Butterworth paga con orden la suavidad; Elíptico paga con fase la eficiencia.*

### 5.3 Cálculo del orden

Con $\varepsilon = \sqrt{10^{R_p/10}-1}$ y frecuencias analógicas $\Omega_p,\Omega_r$ (tras prewarping):

**Butterworth:**
$$
\boxed{\;N \ge \frac{\log_{10}\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}{2\log_{10}(\Omega_r/\Omega_p)}\;}
$$

**Chebyshev** (usa $\cosh^{-1}$, siempre $\le$ Butterworth):
$$
N \ge \frac{\cosh^{-1}\!\sqrt{\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}}{\cosh^{-1}(\Omega_r/\Omega_p)}, \qquad \cosh^{-1}(x)=\ln(x+\sqrt{x^2-1}).
$$

**Elíptico** (integrales elípticas $K$, el **mínimo** de los cuatro).

### 5.4 $H_a(s)$ y transformada bilineal (TBL)

$H_a(s) = H_0\,\prod_m(s-z_m)/\prod_k(s-p_k)$. Butterworth y Cheby I son **todo-polos**. Los polos Butterworth normalizados ($\Omega_c=1$) están equiespaciados en una semicircunferencia del semiplano izquierdo. Para $N=2$: $H_a(s) = \Omega_c^2/(s^2+\sqrt2\,\Omega_c s+\Omega_c^2)$.

**Mapeo bilineal:**
$$
\boxed{\;s = \frac{2}{T}\cdot\frac{1-z^{-1}}{1+z^{-1}}\;}, \qquad T = 1/f_s.
$$
Mapea el SPI ($\text{Re}\{s\}<0$) al interior del círculo unitario ⇒ **prototipo estable produce IIR estable**. Mapea el eje $j\Omega$ completo al círculo unitario sin aliasing.

**Warping y prewarping.** La relación $\Omega = \frac{2}{T}\tan(\omega/2)$ no es lineal (alabea las frecuencias). Para que las críticas caigan exactas se **predistorsiona** cada frecuencia de diseño:
$$
\Omega_{\text{diseño}} = \frac{2}{T}\tan\!\left(\frac{\omega_{\text{deseado}}}{2}\right).
$$

### 5.5 Ejemplo numérico canónico — IIR LP para ECG (AUTORIDAD)

| Parámetro | Valor |
|-----------|-------|
| $f_s$ | 500 Hz ($T=2$ ms) |
| $f_p$ | 40 Hz |
| $f_r$ | 60 Hz |
| $R_p$ | 1 dB |
| $A_s$ | 40 dB |
| Prototipo | Butterworth (LP) |

**Paso 1 — frecuencias digitales:** $\omega_p = 2\pi\cdot40/500 = 0{,}5027$ rad $= 0{,}16\pi$; $\omega_r = 0{,}7540$ rad $= 0{,}24\pi$.

**Paso 2 — prewarping** ($2/T=1000$):
$$
\Omega_p = 1000\tan(0{,}2513) = \mathbf{256{,}76}\ \text{rad/s}\ (\approx 40{,}86\ \text{Hz}),
$$
$$
\Omega_r = 1000\tan(0{,}3770) = \mathbf{395{,}93}\ \text{rad/s}\ (\approx 63{,}01\ \text{Hz}).
$$

**Paso 3 — orden Butterworth:**
$$
10^{A_s/10}-1 = 9999, \qquad 10^{R_p/10}-1 = 0{,}2589, \qquad \tfrac{9999}{0{,}2589} = 38\,617,
$$
$$
\log_{10}(38\,617) = 4{,}5868, \qquad \tfrac{\Omega_r}{\Omega_p} = 1{,}5420, \qquad \log_{10}(1{,}5420) = 0{,}1881,
$$
$$
N \ge \frac{4{,}5868}{2\cdot0{,}1881} = 12{,}19 \;\Longrightarrow\; \boxed{N=13}.
$$

> **Lectura de ingeniería (reconciliación clave).** $N=13$ es **altísimo**: la transición $40\to60$ Hz (relación $1{,}54$) con 40 dB es muy exigente para Butterworth. Esto motiva tres decisiones reales:
> 1. **Relajar la máscara** ($A_s=20$–$30$ dB o $f_r$ más amplia) baja $N$ a 4–6.
> 2. **Cambiar de prototipo** con la **misma** máscara: con la fórmula $\cosh^{-1}$, **Chebyshev I** da $N\approx5{,}97 \Rightarrow N\approx6$, y el **elíptico** $N\approx4$. Compromiso: ripple/fase.
> 3. Si se mantiene $N$ alto, es **obligatorio** realizar el filtro en cascada de biquads (**SOS**); una forma directa de orden 13 es numéricamente inviable.
>
> *(Nota de coherencia: donde `04-criterios-diseno.md` menciona "Butterworth orden 6" como ejemplo aproximado, esta entrega usa la versión rigurosa de `03-iir.md`: Butterworth $N=13$ con la máscara $fp=40/fr=60/Rp=1/As=40$, que motiva Chebyshev I $N\approx6$ o elíptico $N\approx4$ y SOS.)*

**Pasos 4–5 — $H_a(s)$, TBL y $H(z)$.** $\Omega_c = \Omega_p/\varepsilon^{1/N}$ con $\varepsilon = \sqrt{10^{0{,}1}-1} = 0{,}5088$; 13 polos en el semicírculo. Tras la TBL:
$$
H(z) = \prod_i \frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}\quad(\text{6 biquads + 1 sección de 1.er orden}).
$$
Ecuación en diferencias por sección:
$$
y_i[n] = b_{0i}x_i[n]+b_{1i}x_i[n-1]+b_{2i}x_i[n-2]-a_{1i}y_i[n-1]-a_{2i}y_i[n-2].
$$
Todos los polos $|d_k|<1$ ⇒ estable (la TBL lo garantiza). En Python esto es una línea: `butter(N, Wn, output='sos', fs=fs)`.

### 5.6 Notch IIR de la red (50 Hz)

Rechaza-banda de orden 2 con ceros en el círculo en $\omega_0 = 2\pi\cdot50/500 = 0{,}2\pi$ y polos a radio $r\lesssim1$:
$$
H_{\text{notch}}(z) = \frac{1-2\cos\omega_0\,z^{-1}+z^{-2}}{1-2r\cos\omega_0\,z^{-1}+r^2z^{-2}}.
$$
El radio $r$ ($0{,}95$–$0{,}99$) fija el ancho del notch ($r\to1$ ⇒ muesca más estrecha, transitorio más largo). Coste mínimo (1 biquad, ~5 MACs); por eso se prefiere IIR para el notch aun con LP FIR (estrategia mixta del ECG).

### 5.7 Estabilidad y estructuras

**Criterio:** $|d_k| < 1\ \forall k$. Verificación: `max(abs(roots(a))) < 1` o `zplane`. Polos muy cerca de $|z|=1$ son frágiles ante cuantización de coeficientes.

**Estructuras de realización** (equivalentes en aritmética exacta, distintas en punto fijo):
- **DF-I:** literal; usa $M+N$ retardos; robusta, más memoria.
- **DF-II / traspuesta (DF-II-T):** comparte la línea de retardo ($\max(M,N)$ retardos); la traspuesta acumula menos error (default de `lfilter`).
- **SOS (cascada de biquads):** factoriza en secciones de 2.º orden. Cada par de polos/ceros se cuantiza por separado ⇒ baja sensibilidad (problema de Wilkinson resuelto). **Estándar para IIR de orden $\ge 3$**; recomendación por defecto cuando "estabilidad numérica crítica sin DSP float".
- **Lattice:** parametrizada por coeficientes de reflexión $k_i$ ($|k_i|<1$ ⇒ estable); baja sensibilidad; más operaciones por muestra.

---

## 6. Criterios de ingeniería para el diseño y selección de filtros

> Síntesis de `../_kb/04-criterios-diseno.md` (corregido a la versión coherente de §5.5).

### 6.1 FIR vs IIR

| Criterio | FIR | IIR | Gana |
|----------|-----|-----|------|
| Estabilidad | Siempre | Condicional ($\|z\|<1$) | FIR |
| Fase | **Lineal exacta** | No lineal | FIR |
| Orden p/ igual $A_s$ | Alto (50–300) | Bajo (2–10) | IIR |
| Coste (MACs/muestra) | $\approx N+1$ | $\approx 5S$ (SOS) | IIR |
| Memoria coeficientes | $N+1$ | $6S$ | IIR |
| Sensibilidad cuantización | Baja | Alta | FIR |
| Latencia / $\tau_g$ | Constante $=N/2$ (grande) | Variable, menor | IIR |
| Facilidad de diseño | Directo | Prototipo + bilineal + prewarp | FIR |
| Réplica de analógicos | Pobre | Excelente | IIR |

**Gana FIR:** fase lineal estricta (ECG P-QRS-T, EMG), estabilidad numérica crítica, cómputo/memoria de sobra (ESP32/STM32 con FPU).
**Gana IIR:** recursos escasos (Arduino UNO, RAM < 2 kB), transición abrupta con orden mínimo, réplica de analógico sin fase crítica.

### 6.2 Elección de ventana (FIR) y prototipo (IIR)

Elegir la ventana **más simple** cuya $A_s$ supere lo pedido: Rectangular (≤20 dB), Hann (~44), **Hamming (defecto biomédico, 40–50 dB)**, Blackman (~74), **Kaiser** (ajustable). Kaiser cuando $A_s$ no encaja en las fijas; **equiripple (firpm/remez)** cuando el orden mínimo es prioritario o se requieren ripples independientes.

Prototipo IIR: **Butterworth** (fase/planitud importan, sobra orden); **Chebyshev** (compromiso); **Elíptico** (orden/cómputo mínimo, fase no crítica).

### 6.3 Coste computacional y memoria

$$
\text{MACs}_{\text{FIR}} \approx N+1, \quad \text{Coef}_{\text{FIR}} = N+1; \qquad
\text{MACs}_{\text{IIR(SOS)}} \approx 5S, \quad \text{Coef}_{\text{IIR}} = 6S\ (S=\lceil N/2\rceil).
$$

Ejemplo ECG (LP $f_c=40$, $A_s\approx40$ dB):

| Métrica | FIR Hamming | IIR (SOS) |
|---------|:---:|:---:|
| Orden $N$ | ~165 | ~4–6 (elíptico/Cheby; **Butterworth=13**) |
| MACs/muestra | 166 | $\approx 10$–$15$ |
| Memoria float32 | $\approx 1{,}3$ kB | $\approx 100$ B |
| Carga a 500 Hz | 83 kMAC/s | $\approx 7{,}5$ kMAC/s |

El IIR es ~11× más barato en cómputo y ~14× en memoria. Como en ECG **sí** importa la fase, se acepta el coste FIR — o se usa IIR con `filtfilt` (forward-backward, fase cero) **offline**.

### 6.4 Punto fijo vs flotante

**Formato Q$m.n$:** $x_{\text{real}} = x_{\text{int}}\cdot 2^{-n}$. Coeficientes normalizados → Q15/Q14; acumulador más ancho (32/64 bits, $\lceil\log_2 N\rceil$ bits de guarda). Prevenir overflow con escalado/saturación; ruido de cuantización $\sigma_q^2 = \Delta^2/12$ con $\Delta = 2^{-n}$.

**Regla:** IIR de orden > 2 en punto fijo ⇒ siempre **SOS** en cascada. `sin_FPU` → punto fijo Q15; `con_FPU` → float32.

| Plataforma | Reloj | RAM | FPU | Aritmética | Filtro recomendado |
|------------|-------|-----|-----|------------|--------------------|
| **Arduino UNO** | 16 MHz | 2 kB | No | Q15 | **IIR orden bajo (SOS)**; FIR solo $N\lesssim20$ |
| **ESP32** | 160–240 MHz | 320 kB+ | Sí | Float32 | **FIR orden alto** o IIR libre |
| **STM32F4** | 168 MHz | 128–192 kB | Sí | Float32 | FIR/IIR sin restricción práctica |

Coste FIR $\approx N+1$ MACs/muestra; IIR (SOS) $\approx 5\cdot$secciones.

### 6.5 Reglas atómicas accionables (base del agente)

1. `fase_lineal == estricta` → **FIR** (regla dominante).
2. `RAM < 2 kB AND orden_FIR > 50` → **IIR**.
3. `estabilidad_numérica_crítica AND sin_FPU_float` → **SOS** (obligatorio).
4. `transición_estrecha AND cómputo_suficiente` → **IIR** (Elíptico/Cheby).
5. `sin_FPU` → punto fijo Q15; `con_FPU` → float32.
6. `orden_IIR > 2` → **SOS en cascada**.
7. `tiempo_real_estricto` → timer-ISR + buffer circular; DMA si $f_s$ alta.

---

## 7. Herramientas Python (núcleo de la entrega)

> Profundidad alta — síntesis de `../_kb/07-python.md`. Referencia con propósito, firma, parámetros, salida y ejemplo de cada función.

### 7.1 Stack y entorno

> **No ejecutar `pip install` en este trabajo.** Solo se documenta el comando. Toda instalación en un **entorno virtual** aislado.

```bash
# Crear y activar entorno virtual (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate

# Instalar el stack (DOCUMENTADO; no ejecutar en este trabajo)
pip install numpy scipy matplotlib scikit-learn scikit-fuzzy anthropic
```

| Paquete | `import` habitual | Rol |
|---|---|---|
| **numpy** | `import numpy as np` | Arrays, FFT, métricas |
| **scipy** | `from scipy import signal` | Diseño/aplicación de filtros, PSD |
| **matplotlib** | `import matplotlib.pyplot as plt` | Gráficos (Bode, tiempo, FFT, polos-ceros) |
| **scikit-learn** | `from sklearn...` | Árbol, MLP, split |
| **scikit-fuzzy** | `import skfuzzy as fuzz` | Lógica difusa |
| **anthropic** | `from anthropic import Anthropic` | Agente vía LLM (API Claude) |

`scikit-fuzzy` puede requerir `numpy<2` en versiones antiguas; verificar en el `venv`.

### 7.2 Diseño FIR — `scipy.signal`

Todas devuelven el vector `h` (longitud `numtaps`); se aplica con `lfilter`/`filtfilt`. Orden $N = $ `numtaps - 1`.

**`firwin` — método de ventanas.**
```
scipy.signal.firwin(numtaps, cutoff, *, width=None, window='hamming',
                    pass_zero=True, scale=True, fs=None)
```
- `numtaps`: $N+1$ (impar para Tipo I LP).
- `cutoff`: corte (Hz si se pasa `fs`; si no, normalizado a Nyquist 0–1).
- `window`: `'hamming'`, `'hann'`, `'blackman'`, `'rectangular'`, `('kaiser', beta)`.
- `pass_zero`: `True`→LP/BR; `False`→HP/BP.
- Devuelve `h` (ndarray).

```python
import numpy as np
from scipy import signal

fs = 500
# LP fase lineal, fc=40 Hz, 101 taps (orden N=100), Hamming
h = signal.firwin(numtaps=101, cutoff=40, fs=fs, window='hamming')   # LP
print(h.shape)   # (101,)  → sum(h) ≈ 1 (ganancia DC unidad)
```

**`firwin2` — respuesta arbitraria.**
```
scipy.signal.firwin2(numtaps, freq, gain, *, window='hamming', fs=None)
```
`freq`/`gain`: puntos que definen $|H|$ por tramos (0 a $f_s/2$, monótono). Útil para multibanda.
```python
h = signal.firwin2(numtaps=101, freq=[0, 35, 45, 250], gain=[1, 1, 0, 0], fs=fs)
```

**`remez` — Parks-McClellan (equiripple).**
```
scipy.signal.remez(numtaps, bands, desired, *, weight=None, type='bandpass', fs=None)
```
`bands`: bordes por pares (lo no listado es transición); `desired`: ganancia por banda; `weight`: reparto del rizado. Minimiza el error máximo.
```python
# LP equiripple: paso 0–40 Hz (g=1), rechazo 50–250 Hz (g=0)
h = signal.remez(numtaps=101, bands=[0, 40, 50, fs/2], desired=[1, 0], fs=fs)
```

**Dimensionado Kaiser — `kaiserord`.**
```
numtaps, beta = scipy.signal.kaiserord(ripple, width)
```
`ripple`: atenuación deseada (dB, positiva); `width`: ancho de transición **normalizado a Nyquist** ($\Delta f/(f_s/2)$).
```python
delta_f = 10                       # 40→50 Hz
width   = delta_f / (fs/2)
numtaps, beta = signal.kaiserord(ripple=40, width=width)   # As ≈ 40 dB
h = signal.firwin(numtaps, cutoff=45, fs=fs, window=('kaiser', beta))  # corte en centro
```

### 7.3 Diseño IIR — `scipy.signal`

**Siempre `output='sos'` para órdenes ≥ 4** (estable). Tres formas:
- **`'ba'`** → `(b, a)`: numerador/denominador globales. Forma directa, frágil en orden alto.
- **`'zpk'`** → `(z, p, k)`: ceros, polos, ganancia. Para analizar estabilidad ($|p|<1$) y graficar.
- **`'sos'`** → matriz `(n_secciones, 6)`, filas `[b0 b1 b2 a0 a1 a2]`. **Preferida.**

**Prototipos.**
```
scipy.signal.butter(N, Wn, btype='low', *, output='ba', fs=None)
scipy.signal.cheby1(N, rp, Wn, btype='low', *, output='ba', fs=None)   # rp = ripple paso (dB)
scipy.signal.cheby2(N, rs, Wn, btype='low', *, output='ba', fs=None)   # rs = atenuación rechazo (dB)
scipy.signal.ellip (N, rp, rs, Wn, btype='low', *, output='ba', fs=None)
```
`Wn`: corte (Hz con `fs`); `btype`: `'low'|'high'|'bandpass'|'bandstop'`.

**Estimadores de orden.**
```
N, Wn = scipy.signal.buttord(wp, ws, gpass, gstop, *, fs=None)
N, Wn = scipy.signal.cheb1ord(...)   # análogos: cheb2ord, ellipord
```
`gpass = Rp`, `gstop = As`. Devuelve orden mínimo `N` y `Wn` listo para el prototipo.
```python
# Butterworth LP del ejemplo: fp=40 (Rp=1), fr=60 (As=40), fs=500
N, Wn = signal.buttord(wp=40, ws=60, gpass=1, gstop=40, fs=fs)
sos = signal.butter(N, Wn, btype='low', output='sos', fs=fs)
print(N)             # → 13 (coherente con §5.5: máscara exigente para Butterworth)
print(sos.shape)     # (7, 6)  → ceil(13/2)=7 secciones
```
> *Verificación de coherencia con §5.5:* `buttord` reproduce $N=13$. Para bajar el orden, cambiar de prototipo: `cheb1ord` → $N\approx6$, `ellipord` → $N\approx4$.

**Diseño genérico.**
```
scipy.signal.iirfilter(N, Wn, *, rp=None, rs=None, btype='band', ftype='butter', output='ba', fs=None)
scipy.signal.iirdesign(wp, ws, gpass, gstop, *, ftype='ellip', output='ba', fs=None)
```
`iirdesign` calcula orden + diseña en un paso (equivale a `*ord` + prototipo):
```python
sos = signal.iirdesign(wp=40, ws=60, gpass=1, gstop=40, ftype='ellip', output='sos', fs=fs)
```

**Notch / peak.**
```
b, a = scipy.signal.iirnotch(w0, Q, fs=None)   # rechaza banda
b, a = scipy.signal.iirpeak (w0, Q, fs=None)   # realza banda
```
`Q`: factor de calidad ($BW \approx w0/Q$). Devuelve un biquad; convertir a SOS con `tf2sos`.
```python
b_n, a_n = signal.iirnotch(w0=50, Q=30, fs=fs)   # notch 50 Hz
sos_n = signal.tf2sos(b_n, a_n)                  # a SOS para encadenar
```

### 7.4 Análisis: frecuencia, polos-ceros, retardo

**`freqz` / `sosfreqz` — respuesta en frecuencia.**
```
w, H = scipy.signal.freqz(b, a=1, worN=512, *, fs=2*np.pi)
w, H = scipy.signal.sosfreqz(sos, worN=512, *, fs=2*np.pi)
```
Con `fs`, `w` sale en Hz (0–`fs/2`). Devuelve `w` y `H` complejo:
```python
w, H = signal.sosfreqz(sos, worN=2048, fs=fs)
mag_db = 20*np.log10(np.abs(H) + 1e-12)   # +eps evita log10(0)
fase   = np.unwrap(np.angle(H))           # rad
```

**`group_delay` — retardo de grupo** (en muestras vs frecuencia):
```
w, gd = scipy.signal.group_delay((b, a), w=512, fs=2*np.pi)
```
```python
w, gd = signal.group_delay((h, 1), fs=fs)   # FIR: a = 1, debe ser ≈ N/2 constante
```

**Conversiones entre formas.**
```
z, p, k = scipy.signal.tf2zpk(b, a)
z, p, k = scipy.signal.sos2zpk(sos)
sos     = scipy.signal.zpk2sos(z, p, k)
sos     = scipy.signal.tf2sos(b, a)
```
`zpk` para estabilidad/polos-ceros; `sos` para aplicar.

**Diagrama de polos-ceros (no hay `zplane` nativo).** Se dibuja a mano:
```python
import matplotlib.pyplot as plt

def zplane(z, p, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))
    theta = np.linspace(0, 2*np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), 'k--', lw=1)        # círculo unitario
    ax.scatter(np.real(z), np.imag(z), marker='o', facecolors='none',
               edgecolors='b', label='ceros')
    ax.scatter(np.real(p), np.imag(p), marker='x', color='r', label='polos')
    ax.axhline(0, color='gray', lw=0.5); ax.axvline(0, color='gray', lw=0.5)
    ax.set_aspect('equal'); ax.set_xlabel('Re'); ax.set_ylabel('Im')
    ax.legend(); ax.grid(True, alpha=0.3)
    return ax

z, p, k = signal.sos2zpk(sos)
zplane(z, p)        # estable ⟺ todos los |p| < 1
```

### 7.5 Aplicación del filtro

| Función | Forma | Fase | Uso |
|---|---|---|---|
| `lfilter(b, a, x)` | directa, causal | introduce retardo/fase | tiempo real, `ba` |
| `sosfilt(sos, x)` | cascada SOS, causal | con retardo | IIR estable orden alto |
| `filtfilt(b, a, x)` | doble pasada | **fase cero** | offline, `ba` |
| `sosfiltfilt(sos, x)` | doble pasada SOS | **fase cero** | offline, IIR SOS |
| `convolve(x, h)` | convolución | FIR causal | FIR pequeño, didáctico |

- **Causal** (`lfilter`/`sosfilt`): una pasada, añade retardo (FIR: $N/2$; IIR: fase no lineal). Es lo que ocurre en el micro (Paso 5).
- **Fase cero** (`filtfilt`/`sosfiltfilt`): filtra adelante y atrás → retardo neto nulo y $|H|^2$ (doble atenuación en dB). Solo offline; **ideal para no deformar el ECG**. Requiere `len(x) > 3·orden`.

```python
# ECG: notch 50 Hz + LP FIR 40 Hz, fase cero (análisis offline)
ecg_n = signal.sosfiltfilt(sos_n, ecg)   # quita 50 Hz
ecg_f = signal.filtfilt(h, 1, ecg_n)     # LP FIR, preserva morfología
```

### 7.6 Espectro

**FFT con numpy (señal real):**
```
X = numpy.fft.rfft(x)                    # mitad positiva (len(x)//2 + 1 valores)
f = numpy.fft.rfftfreq(len(x), d=1/fs)   # eje en Hz
```
```python
N  = len(x)
X  = np.fft.rfft(x)
f  = np.fft.rfftfreq(N, d=1/fs)
mag = np.abs(X) / N * 2                   # escala a amplitud (factor 2 banda única)
mag_db = 20*np.log10(mag + 1e-12)
```

**PSD con Welch:**
```
f, Pxx = scipy.signal.welch(x, fs=1.0, *, window='hann', nperseg=256, noverlap=None)
```
Promedia periodogramas → PSD suave (menos varianza). `nperseg`: longitud de segmento.
```python
f, Pxx = signal.welch(ecg, fs=fs, nperseg=1024)   # pico en 50 Hz antes del notch
```

**Ventanas — `get_window`:**
```python
win = signal.get_window('hann', N)        # reduce fuga antes de la FFT
X = np.fft.rfft(x * win)
```

### 7.7 Métricas: SNR y RMSE (numpy)

$$
\mathrm{SNR_{dB}} = 10\log_{10}\!\frac{\sum x_{\text{clean}}^2}{\sum(x_{\text{clean}}-x_{\text{eval}})^2}, \qquad \mathrm{RMSE} = \sqrt{\tfrac{1}{N}\sum(x_{\text{clean}}-x_{\text{eval}})^2}.
$$
```python
def snr(clean, x):
    noise = clean - x
    return 10 * np.log10(np.sum(clean**2) / (np.sum(noise**2) + 1e-12))

def rmse(clean, x):
    return np.sqrt(np.mean((clean - x)**2))

print("SNR in :", snr(ecg_clean, ecg_noisy))   # SNR debe subir
print("SNR out:", snr(ecg_clean, ecg_filt))
print("RMSE   :", rmse(ecg_clean, ecg_filt))    # RMSE debe bajar
```

### 7.8 matplotlib — patrones de graficado

**Respuesta en frecuencia (magnitud + fase):**
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

**Señal en el tiempo y FFT:**
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

### 7.9 'ba' vs 'zpk' vs 'sos' — cuándo cada una

| Forma | Qué guarda | Ventaja | Cuándo usarla |
|-------|-----------|---------|---------------|
| **`ba`** | $(b, a)$ globales | simple, didáctica | FIR, IIR orden bajo, fórmulas |
| **`zpk`** | ceros, polos, ganancia | analizar estabilidad ($\|p\|<1$), graficar polos-ceros | inspección/diagnóstico |
| **`sos`** | matriz $(S, 6)$ de biquads | numéricamente estable | **IIR orden ≥ 4 (default)** |

Para FIR la forma natural es `ba` con `a=1`. Para IIR de orden alto, **siempre `sos`**: una forma directa de orden 13 (ejemplo §5.5) acumula error y puede volverse inestable.

### 7.10 Plantilla de script integradora

Flujo completo Paso 3: diseño → respuesta en frecuencia → filtrado → FFT → métricas.
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

### 7.11 Tabla de equivalencias Python ↔ Octave

| Tarea | Python | Octave/MATLAB |
|---|---|---|
| FIR ventana | `firwin` | `fir1` |
| FIR equiripple | `remez` | `firpm` |
| Dimensionar Kaiser | `kaiserord` | `kaiserord` |
| IIR prototipo | `butter`/`cheby1`/`cheby2`/`ellip` | íd. |
| Orden IIR | `buttord`/`cheb1ord`/… | íd. |
| Notch | `iirnotch` | `iirnotch` |
| Respuesta frecuencia | `freqz`/`sosfreqz` | `freqz` |
| Polos-ceros | `zplane` casero | `zplane` |
| Filtrar causal | `lfilter`/`sosfilt` | `filter`/`sosfilt` |
| Fase cero | `filtfilt`/`sosfiltfilt` | `filtfilt` |
| PSD | `welch` | `pwelch` |

---

## 8. Agente de decisión IA — enfoque Python (núcleo de la entrega)

> Síntesis profunda de `../_kb/05-agente-ia.md` + `07-python.md`. Foco de esta entrega.

### 8.1 Definición y variables E/S

Un **agente de decisión** mapea restricciones de ingeniería a una recomendación de diseño de filtro, emulando a un especialista en PDS. No diseña el filtro (eso es el Paso 2): **decide la familia y la estructura** y **justifica** la elección. Formalmente:
$$
\text{Agente}: \mathbf{x} \in \mathcal{X} \;\longrightarrow\; \mathbf{y} \in \mathcal{Y}.
$$

**Entradas $\mathbf{x}$:**

| Variable | Símbolo | Tipo / rango |
|----------|---------|--------------|
| Frecuencia de muestreo | `fs` | Hz (10…5000) |
| Memoria del µC | `RAM`, `Flash` | kB (2…512) |
| Cómputo | `MIPS`/`MHz` | 16…240 MHz; con/sin FPU |
| Fase lineal requerida | `fase_lineal` | booleano |
| Nivel de ruido / SNR | `SNR_in` | dB (0…40) |
| Latencia admisible | `latencia` | {baja, media, alta} |
| Pendiente de transición | `transicion` | {estrecha, amplia} |

**Salidas $\mathbf{y}$:** recomendación `{FIR, IIR}`; estructura `{DF I, DF II, SOS, lattice}`; justificación (texto/reglas activadas); confianza $[0,1]$ (opcional).

Las 5 estrategias difieren en **cómo se genera** el agente: conocimiento experto explícito (1 reglas IF-THEN, 3 difusa), aprendizaje desde datos (2 árbol, 5 MLP), o delegación a un LLM (4 API).

### 8.2 Generación de dataset sintético etiquetado por reglas

Las estrategias 2 (árbol) y 5 (MLP) necesitan datos. Como no hay dataset real de "decisiones FIR/IIR", se **fabrica** muestreando combinaciones y **etiquetando con las reglas de ingeniería** (§6.5). El clasificador **destila** esas reglas y generaliza.
```python
import numpy as np

def etiqueta_por_reglas(fs, RAM, MHz, FPU, fase_lin, SNR, trans_estrecha, ordenFIR):
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
Buenas prácticas: **balancear** clases, **añadir ruido** controlado a algunas etiquetas, y **separar train/test** (`accuracy` ≈ 1 si el modelo recupera las reglas).

### 8.3 Estrategia (a) — Reglas IF-THEN (sistema experto)

Tres partes: base de hechos, base de reglas `IF…THEN`, motor de inferencia (encadenamiento hacia adelante). **No hay entrenamiento**: el agente se construye por elicitación de conocimiento. Reglas (la primera que dispara fija la familia):

| # | Prioridad | SI | ENTONCES | Confianza |
|---|-----------|----|----------|-----------|
| R1 | alta | `fase_lineal == sí` | **FIR**, DF | 0.95 |
| R2 | alta | `RAM < 2 kB` Y orden FIR `> 50` | **IIR**, SOS | 0.90 |
| R3 | alta | estabilidad crítica Y sin FPU float | **IIR**, SOS | 0.90 |
| R4 | media | `transicion == estrecha` Y cómputo suficiente | **IIR** (Elíptico) | 0.85 |
| R5 | media | `latencia == baja` Y FIR alto inviable | **IIR** | 0.70 |
| R6 | baja | FPU Y `transicion == amplia` Y fase lineal deseada | **FIR** | 0.80 |
| R7 | baja | ninguna anterior | **FIR** por defecto | 0.50 |

```python
def agente_reglas(h):
    """h: dict con fs, RAM, MHz, FPU(bool), fase_lineal(bool), SNR_in,
       latencia, transicion, ordenFIR."""
    rec, est, reglas, conf = None, None, [], 0.0
    def fijar(r, fam, e, c):
        nonlocal rec, est, conf
        if rec is None:
            rec, est, conf = fam, e, c
        reglas.append(r)
    if h["fase_lineal"]:
        fijar("R1", "FIR", "DF", 0.95)
    if h["RAM"] < 2 and h["ordenFIR"] > 50:
        fijar("R2", "IIR", "SOS", 0.90)
    if not h["FPU"] and h["ordenFIR"] > 30:
        fijar("R3", "IIR", "SOS", 0.90)
    if h["transicion"] == "estrecha" and (h["FPU"] or h["MHz"] >= 80):
        fijar("R4", "IIR", "SOS", 0.85)
    if h["latencia"] == "baja" and h["ordenFIR"] > 64:
        fijar("R5", "IIR", "DFII", 0.70)
    if h["FPU"] and h["transicion"] == "amplia":
        fijar("R6", "FIR", "DF", 0.80)
    if rec is None:
        fijar("R7", "FIR", "DF", 0.50)
    return rec, est, reglas, conf
```
Ventajas: totalmente interpretable, determinista, ligero (embebible). Limitaciones: no generaliza, mantenimiento manual, fronteras "duras".

### 8.4 Estrategia (b) — Árbol de decisión (`DecisionTreeClassifier`)

Clasificador que parte recursivamente el espacio según un criterio de impureza: **Gini** $G = 1-\sum_k p_k^2$ o **Entropía** $H = -\sum_k p_k\log_2 p_k$. Se genera por **entrenamiento** (`fit`) sobre el dataset etiquetado (§8.2): el árbol "destila" las reglas y las suaviza.
```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text

X, y, feat = generar_dataset(n=4000, seed=0)

clf = DecisionTreeClassifier(
    criterion="gini",       # o "entropy"
    max_depth=4,            # evita overfitting + interpretable
    min_samples_leaf=20,
    random_state=0,
)
clf.fit(X, y)

# Reglas aprendidas (interpretabilidad)
print(export_text(clf, feature_names=feat))

# Inferencia para un caso: fs,RAM,MHz,FPU,fase_lin,SNR,transEstrecha,ordenFIR
caso = np.array([[500, 2, 16, 0, 1, 10, 0, 80]])
print("Recomendacion:", clf.predict(caso)[0])
print("Confianza:", clf.predict_proba(caso).max())   # fracción de la clase ganadora en la hoja
```
`export_text` produce un árbol legible (`fase_lineal <= 0.50 → ...`). La **confianza** sale de `predict_proba`. Riesgo de overfitting: mitigar con `max_depth` (4–6), `min_samples_leaf`, poda. Ventajas: interpretable, exportable a `if/else` (embebible). Limitaciones: necesita dataset, fronteras "en escalera", sensible al ruido.

### 8.5 Estrategia (c) — Lógica difusa (scikit-fuzzy)

Sustituye fronteras duras por **grados de pertenencia** $\mu\in[0,1]$. Variables lingüísticas (bajo/medio/alto) con funciones de pertenencia triangulares/trapezoidales. Motor **Mamdani**: fuzzificación → inferencia → defuzzificación (centroide). **No hay entrenamiento**: se diseñan a mano las MF y reglas; aporta **gradación** (decisiones suaves + confianza continua).

Ejemplo de pertenencia triangular ("ruido alto", $s$ = SNR en dB):
$$
\mu_{\text{alto}}(s) = \begin{cases} 0 & s\ge18 \\ \frac{18-s}{18-6} & 6<s<18 \\ 1 & s\le6 \end{cases}
$$
Centroide de la salida agregada:
$$
y^* = \frac{\int y\,\mu_{\text{agg}}(y)\,dy}{\int\mu_{\text{agg}}(y)\,dy}.
$$
```python
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

ruido = ctrl.Antecedent(np.arange(0, 41, 1), 'ruido')          # SNR_in (dB)
trans = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'trans')     # 0=amplia, 1=estrecha
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
`pref_IIR` cercano a 1 ⇒ IIR; cercano a 0 ⇒ FIR. Ventajas: decisiones suaves, robusto a entradas ambiguas, interpretable. Limitaciones: diseño manual de MF, más parámetros, coste de defuzzificación.

### 8.6 Estrategia (d) — API LLM con SDK `anthropic`

Se **delega la decisión a un LLM Claude** vía API. El agente se construye por **prompt engineering estructurado** (rol + criterios + formato de salida JSON) y se **valida** la respuesta.

**Generación:** (1) *system prompt* con rol (experto PDS), criterios (§6) y formato; (2) *user prompt* con las variables; (3) salida estructurada (esquema JSON `{recomendacion, estructura, justificacion, confianza}`); (4) validación (`recomendacion ∈ {FIR,IIR}`, confianza en `[0,1]`; reintento o fallback a reglas si falla).

**System prompt:**
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

**Formato de salida (JSON):**
```json
{
  "recomendacion": "FIR",
  "estructura": "DF",
  "justificacion": "Fase lineal estricta para preservar P-QRS-T; FIR de fase lineal por simetria de h[n].",
  "confianza": 0.92
}
```

**Llamada con el SDK `anthropic` (familia Claude actual).** La clave se lee del entorno (`ANTHROPIC_API_KEY`); **nunca** se escribe en el código.
```python
# --- agente_llm.py (SDK anthropic, salida estructurada validada) ---
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

client = anthropic.Anthropic()    # toma ANTHROPIC_API_KEY del entorno (no hardcodear)

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

# Salida estructurada validada contra el esquema Pydantic
resp = client.messages.parse(
    model="claude-opus-4-8",        # familia actual; usar 'claude-haiku-4-5' si prima coste/latencia
    max_tokens=1024,
    system=SYSTEM,
    messages=[{"role": "user", "content": user}],
    output_format=Recom,            # fuerza y valida el esquema JSON
)

rec = resp.parsed_output            # instancia Recom validada
print(rec.recomendacion, rec.estructura, round(rec.confianza, 2))
print(rec.justificacion)
```

**Alternativa sin Pydantic** (parseo manual con `json.loads` y `try/except`):
```python
import os, json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])   # o simplemente Anthropic()

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
try:
    salida = json.loads(msg.content[0].text)        # validar/normalizar
    print(salida["recomendacion"], salida["estructura"], round(salida["confianza"], 2))
except (json.JSONDecodeError, KeyError):
    salida = agente_reglas({...})                   # fallback a reglas IF-THEN
```

**Notas de modelo, coste, latencia y aptitud.**
- Modelos de la familia Claude actual: **`claude-opus-4-8`** (máxima capacidad de razonamiento) o **`claude-haiku-4-5`** (coste/latencia bajos). Elegir según el compromiso coste ↔ calidad.
- **Coste:** cada llamada consume tokens (coste \$); `claude-opus-4-8` ≈ \$5/\$25 por 1M tokens (in/out), `claude-haiku-4-5` ≈ \$1/\$5.
- **Latencia:** cientos de ms a segundos por llamada → **no apto para tiempo real** en el micro.
- **No determinismo:** la misma entrada puede dar salida variable; por eso se fija el formato JSON y se valida. La familia actual usa salida estructurada (`messages.parse` + esquema); **no** se usan parámetros obsoletos (`temperature` no aplica en esta familia).
- **Aptitud:** muy útil **solo en fase de diseño** (explorar, justificar, documentar). Requiere conexión a internet ⇒ poco apto para el µC embebido. En producción conviene un agente de reglas (§8.3) o un árbol exportado a `if/else` (§8.4).

Ventajas: justificación rica en lenguaje natural, maneja casos poco previstos, rápido de prototipar. Riesgos: no determinista, coste/latencia, requiere conexión, necesita validación (alucinaciones).

### 8.7 Estrategia (e) — Red neuronal MLP (`MLPClassifier`)

Un **MLP** (perceptrón multicapa): entrada (8 neuronas), 1+ capas ocultas (ReLU/tanh) y salida (softmax 2 → P(FIR), P(IIR)). Se genera por **entrenamiento por backpropagation** (minimiza entropía cruzada por descenso de gradiente); requiere dataset etiquetado (§8.2). Softmax da la confianza = P(clase ganadora).
```python
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

X, y, feat = generar_dataset(n=8000, seed=1)

modelo = make_pipeline(
    StandardScaler(),                              # escalar es importante para el MLP
    MLPClassifier(hidden_layer_sizes=(16, 8),      # 2 capas ocultas
                  activation="relu", solver="adam",
                  max_iter=500, random_state=1),
)
modelo.fit(X, y)                                   # "generacion" = backprop (Adam)

caso = [[500, 2, 16, 0, 1, 12, 1, 80]]
print("Recomendacion:", modelo.predict(caso)[0])
print("Confianza:", modelo.predict_proba(caso).max())
```
**¿Cuándo es excesivo?** El problema FIR/IIR tiene **pocas variables** y fronteras explicables ⇒ reglas o árbol ya lo resuelven (interpretables, embebibles). Un MLP es **caja negra**, necesita más datos, puede sobreajustar y es difícil de justificar ante un tribunal. Aquí es **sobre-ingeniería**; se incluye por completitud.

### 8.8 Tabla comparativa de las 5 estrategias

| Criterio | (a) Reglas | (b) Árbol | (c) Difusa | (d) API LLM | (e) MLP |
|----------|:--:|:--:|:--:|:--:|:--:|
| Interpretabilidad | Muy alta | Alta | Alta | Media | Baja |
| Datos necesarios | Ninguno | Dataset (sint.) | Ninguno | Ninguno | Dataset (más) |
| Determinismo | Total | Total (tras fit) | Total | **No** | Total (tras fit) |
| Idoneidad embebida | Excelente | Buena (→`if/else`) | Media | **Nula** (online) | Baja |
| Esfuerzo de generación | Medio (elicitar) | Bajo (entrenar) | Alto (diseñar MF) | Bajo (prompt) | Medio-alto |
| Aporta confianza | Opcional (pesos) | Sí (`predict_proba`) | Sí (centroide) | Sí (campo JSON) | Sí (softmax) |
| Recomendado para | µC tiempo real | diseño + exportar | entradas imprecisas | **fase de diseño** | (sobre-ingeniería) |

### 8.9 Validación — 3 escenarios

Validar con ≥3 escenarios distintos; las salidas deben ser coherentes con §6 y los Pasos 1–3.

| Escenario | Entrada clave | Salida esperada | Regla |
|-----------|---------------|-----------------|-------|
| **(a) ECG diagnóstico** | fase lineal estricta; FPU (ESP32/STM32); transición amplia | **FIR** / DF | R1 |
| **(b) Arduino UNO** | 2 kB RAM, ordenFIR>50, sin FPU; fase no estricta | **IIR** / SOS (Q15) | R2, R3 |
| **(c) ESP32 transición exigente** | transición estrecha; FPU ≥160 MHz; fase no requerida | **IIR (Elíptico)** / SOS | R4 |

Justificaciones: (a) la morfología clínica exige fase lineal exacta; FIR la garantiza, el FPU absorbe el orden mayor. (b) FIR de orden >50 inviable con 2 kB; IIR logra la selectividad con orden bajo; sin float ⇒ SOS. (c) transición estrecha + cómputo suficiente ⇒ IIR de orden adecuado; el elíptico da la pendiente más abrupta con menor orden. Si una estrategia de aprendizaje **no** reproduce estas salidas: dataset mal balanceado u overfitting (revisar §8.2, `max_depth`).

### 8.10 Recomendación de cierre

- **Para embeber:** estrategia **(a) reglas IF-THEN** — interpretable, determinista, ligera; exportable a C para el Paso 5.
- **Para enriquecer el documento Python:** **(b) árbol + (c) difusa + (d) LLM** muestran el espectro de técnicas.
- **El MLP (e)** se documenta como referencia pero es **excesivo** aquí.
- Todas las recomendaciones se anclan en los criterios de §6 y son coherentes con los Pasos 1–3.

---

## 9. Flujo de trabajo recomendado en Python

> Orden de pasos, sin ejecutar.

1. **Entorno virtual aislado:** `python -m venv .venv` y activación (§7.1). Documentar (no ejecutar) `pip install numpy scipy matplotlib scikit-learn scikit-fuzzy anthropic`. `scikit-fuzzy` puede exigir `numpy<2`.
2. **Especificación (Paso 1):** definir `fs` (justificada por Nyquist), `fp`, `fr`, `Rp`, `As`, tipo de filtro, fase lineal sí/no. Tabla de requerimientos.
3. **Diseño FIR (Paso 2):** `firwin`/`firwin2`/`remez`/`kaiserord` (§7.2). Verificar simetría y orden.
4. **Diseño IIR (Paso 2):** `*ord` → prototipo (`butter`/`cheby1`/`cheby2`/`ellip`) con **`output='sos'`** (§7.3). Notch con `iirnotch` + `tf2sos`. Prewarping interno.
5. **Análisis (Paso 3):** `sosfreqz`/`freqz` (magnitud+fase), `group_delay`, `zplane` casero (§7.4). Comprobar máscara, fase lineal, estabilidad ($|p|<1$).
6. **Filtrado y métricas (Paso 3):** `filtfilt`/`sosfiltfilt` (fase cero, offline) sobre la señal contaminada; `welch`/`rfft` para PSD antes/después; `snr`/`rmse` (§7.5–§7.7). Tabla comparativa FIR vs IIR.
7. **Plantilla integradora (§7.10):** ejecutar el flujo completo y graficar (§7.8).
8. **Agente de IA (Paso 4):** generar dataset sintético (§8.2); implementar la(s) estrategia(s) elegida(s) (§8.3–§8.7); validar con los 3 escenarios (§8.9).
9. **Cierre:** documentar decisiones de diseño y criterios (§6); preparar exportación a C para el embebido (Paso 5, fuera del alcance de esta entrega).

---

## 10. Glosario de símbolos + Referencias

### 10.1 Glosario de símbolos

| Símbolo | Significado | Unidad |
|---|---|---|
| $f_s$ | Frecuencia de muestreo | Hz |
| $T = 1/f_s$ | Periodo de muestreo | s |
| $f_N = f_s/2$ | Frecuencia de Nyquist | Hz |
| $\omega = 2\pi f/f_s$ | Frecuencia digital normalizada | rad/muestra |
| $f_p$ | Borde de banda de paso | Hz |
| $f_r$ | Borde de banda de rechazo | Hz |
| $\omega_c$ | Frecuencia de corte (normalizada) | rad/muestra |
| $\Omega$ | Frecuencia angular analógica | rad/s |
| $R_p$ | Rizado máximo en banda de paso | dB |
| $A_s$ | Atenuación mínima en banda de rechazo | dB |
| $N$ | Orden del filtro (o nº de puntos de la DFT) | — |
| $M$ | Longitud de $h[n]$ FIR ($M=N+1$ taps) | muestras |
| $h[n]$ | Respuesta al impulso | — |
| $H(z)$ | Función de transferencia (dominio Z) | — |
| $H(e^{j\omega})$ | Respuesta en frecuencia | — |
| $\phi(\omega)$ | Fase de la respuesta | rad |
| $\tau_g(\omega)$ | Retardo de grupo $-d\phi/d\omega$ | muestras |
| $\Delta f = f_s/N$ | Resolución frecuencial de la DFT | Hz/bin |
| $b_k, a_k$ | Coeficientes numerador/denominador de $H(z)$ | — |
| $\varepsilon$ | Factor de ondulación, $\sqrt{10^{R_p/10}-1}$ | — |
| $\beta$ | Parámetro de la ventana de Kaiser | — |
| $\Delta = 2^{-n}$ | Paso de cuantización (Q$m.n$) | — |
| $\mu$ | Grado de pertenencia (lógica difusa) | $[0,1]$ |

### 10.2 Referencias (formato IEEE)

[1] A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*, 3rd ed. Upper Saddle River, NJ, USA: Pearson, 2010.

[2] J. G. Proakis and D. G. Manolakis, *Digital Signal Processing: Principles, Algorithms, and Applications*, 4th ed. Upper Saddle River, NJ, USA: Pearson Prentice Hall, 2007.

[3] S. K. Mitra, *Digital Signal Processing: A Computer-Based Approach*, 4th ed. New York, NY, USA: McGraw-Hill, 2011.

[4] The SciPy community, "Signal processing (`scipy.signal`)," *SciPy v1.x Reference Guide*. [En línea]. Disponible: https://docs.scipy.org/doc/scipy/reference/signal.html

[5] F. Pedregosa *et al.*, "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011. [En línea]. Disponible: https://scikit-learn.org/stable/

[6] J. Warner *et al.*, "scikit-fuzzy: Fuzzy logic toolkit for SciPy." [En línea]. Disponible: https://pythonhosted.org/scikit-fuzzy/

[7] Anthropic, "Claude Developer Platform — API documentation and Python SDK (`anthropic`)." [En línea]. Disponible: https://docs.claude.com/

[8] J. D. Hunter, "Matplotlib: A 2D graphics environment," *Comput. Sci. Eng.*, vol. 9, no. 3, pp. 90–95, 2007.

---

> *Documento generado como apuntes técnicos de la asignatura. Ampliaciones por módulo en `../_kb/`.*
