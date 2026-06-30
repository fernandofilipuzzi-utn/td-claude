# Apuntes de Filtrado Digital FIR/IIR asistido por IA — Enfoque Octave/MATLAB

> **Documento de síntesis autónomo.** Reúne fundamentos de PDS, diseño de filtros FIR/IIR, criterios de ingeniería, la referencia completa de herramientas de **Octave/MATLAB** y la construcción del **agente de decisión** como sistema experto en `.m`. El lector no necesita abrir el *Knowledge Base*; cuando interese ampliar un punto se cita el módulo fuente como `../_kb/NN.md`.

---

## Índice

1. [Portada y propósito](#1-portada-y-proposito)
2. [Mapa de conocimientos (temas ↔ pasos ↔ secciones)](#2-mapa-de-conocimientos)
3. [Fundamentos de PDS](#3-fundamentos-de-pds)
4. [Diseño de filtros FIR](#4-diseno-de-filtros-fir)
5. [Diseño de filtros IIR](#5-diseno-de-filtros-iir)
6. [Criterios de ingeniería para diseño y selección](#6-criterios-de-ingenieria)
7. [Herramientas Octave/MATLAB (núcleo de esta entrega)](#7-herramientas-octave-matlab)
8. [Agente de decisión IA — enfoque Octave/MATLAB](#8-agente-de-decision-ia)
9. [Flujo de trabajo recomendado en Octave](#9-flujo-de-trabajo)
10. [Glosario de símbolos y referencias](#10-glosario-y-referencias)

---

<a id="1-portada-y-proposito"></a>
## 1. Portada y propósito

- **Asignatura:** Técnicas Digitales III — Procesamiento Digital de Señales / Filtrado Digital (2026).
- **Proyecto:** Diseño, simulación e implementación de un **sistema de filtrado digital FIR/IIR asistido por IA** para una aplicación de ingeniería (Evaluación Basada en Problemas, modalidad grupal). Herramientas permitidas: MATLAB/Octave, Python, IA generativa, plataformas embebidas, simuladores.
- **Caso de hilo conductor:** electrocardiograma (**ECG**, aplicación A del enunciado): banda útil 0.5–40 Hz, interferencia de red 50 Hz, $f_s = 500$ Hz; cadena de filtrado *Notch* 50 Hz (IIR de 2.º orden) + paso-bajos $f_c = 40$ Hz (FIR de fase lineal para preservar el complejo P-QRS-T).
- **Alcance de ESTE documento (entrega Octave/MATLAB):** cubre las tres tareas del usuario:
  1. **Evaluación de todos los temas** involucrados en los 5 pasos del examen (§2–§8).
  2. **Fundamentos** de PDS y diseño + **las herramientas de Octave/MATLAB** (cómo funcionan, sintaxis, parámetros, salidas y ejemplos) — §3–§7.
  3. **Generación del agente de IA y criterios de diseño** con enfoque Octave/MATLAB: el agente se implementa como **sistema experto de reglas IF-THEN en `.m`** (§8); las variantes basadas en aprendizaje (árbol, fuzzy, LLM, MLP) se resumen y se remite su implementación a la **entrega Python** (`../entrega_python/APUNTES_PYTHON.md`).
- **Restricciones del trabajo:** no se ejecuta código ni se instala nada; los números provienen del KB y se respetan tal cual.

> Ampliación del contexto del examen y anexos: `../_kb/00-enunciado.md`.

---

<a id="2-mapa-de-conocimientos"></a>
## 2. Mapa de conocimientos

### 2.1 Los 5 pasos evaluables del examen

| Paso | Título | Núcleo técnico |
|------|--------|----------------|
| **1** | Análisis del problema y especificaciones | Caracterizar señal; justificar $f_s$ por Nyquist-Shannon; banda útil vs ruido; tipo (LP/HP/BP/BR-notch); $f_p$, $f_r$, $R_p$, $A_s$; fase lineal sí/no; tabla de requerimientos |
| **2** | Desarrollo matemático del diseño | **FIR:** método (ventanas o Parks-McClellan), orden $N$, $h[n]$, simetría→fase lineal, $H(z)$. **IIR:** prototipo, orden $N$, $H_a(s)$, transformada bilineal + *prewarping*, $H(z)$, ecuación en diferencias, estabilidad |
| **3** | Simulación en MATLAB/Octave | $\lvert H\rvert$ dB y fase, $h[n]$, retardo de grupo, polos-ceros, señal antes/después, FFT/PSD, métricas SNR/RMSE, tabla comparativa FIR vs IIR |
| **4** | Agente de decisión asistido por IA | Recomienda **FIR o IIR** + estructura (DF I, DF II, SOS, lattice) según restricciones |
| **5** | Implementación en microcontrolador | Arduino/STM32/ESP32; punto fijo (Q) vs float; buffers; código; validación; fuentes de error |

### 2.2 Tabla temas ↔ pasos ↔ secciones de este documento

| Tema | Paso(s) | Sección de este doc | Módulo KB de origen |
|------|---------|---------------------|---------------------|
| Muestreo, Nyquist, aliasing, espectro, DTFT/DFT/Z, convolución, fase lineal, retardo de grupo, SNR/RMSE | 1, 3 | [§3](#3-fundamentos-de-pds) | `01-fundamentos-pds.md` |
| Diseño FIR (ventanas, Parks-McClellan, orden, simetría, $H(z)$) | 2 | [§4](#4-diseno-de-filtros-fir) | `02-fir.md` |
| Diseño IIR (prototipos, $H_a(s)$, bilineal+prewarping, estabilidad, SOS) | 2 | [§5](#5-diseno-de-filtros-iir) | `03-iir.md` |
| Criterios de ingeniería (FIR vs IIR, ventana/prototipo, MACs/memoria, punto fijo vs float, embebido) | 1, 5 | [§6](#6-criterios-de-ingenieria) | `04-criterios-diseno.md` |
| Herramientas Octave/MATLAB (paquete `signal`) | 3 | [§7](#7-herramientas-octave-matlab) | `06-octave.md` |
| Agente de decisión IA (reglas IF-THEN en `.m`) | 4 | [§8](#8-agente-de-decision-ia) | `05-agente-ia.md` |
| Flujo de trabajo en Octave | 1–4 | [§9](#9-flujo-de-trabajo) | `06-octave.md` |

---

<a id="3-fundamentos-de-pds"></a>
## 3. Fundamentos de Procesamiento Digital de Señales (PDS)

> Síntesis fiel de `../_kb/01-fundamentos-pds.md`. Base teórica que asumen los capítulos de FIR (§4) e IIR (§5).

### 3.1 Señal analógica vs digital, muestreo y cuantización

Una **señal analógica** $x_a(t)$ es continua en tiempo y amplitud; una **señal digital** $x[n]$ es discreta en ambos. El paso ocurre en dos etapas independientes:

1. **Muestreo** (discretización temporal): $x[n] = x_a(nT)$, con $T$ el **periodo de muestreo** y
$$
f_s = \frac{1}{T}\ [\text{Hz}], \qquad \omega_s = 2\pi f_s\ [\text{rad/s}].
$$
2. **Cuantización** (discretización de amplitud): cada muestra se aproxima a uno de $2^B$ niveles ($B$ = bits del ADC).

La **frecuencia digital normalizada** es
$$
\omega = \Omega T = \frac{2\pi f}{f_s}\ [\text{rad/muestra}], \qquad \omega\in(-\pi,\pi],
$$
donde $\Omega = 2\pi f$. El valor $\omega=\pi$ corresponde exactamente a $f = f_s/2$. Toda la teoría de filtros digitales se expresa en $\omega$, lo que la hace independiente de $f_s$.

**Cuantización.** Con $B$ bits y rango $V_{pp}$, el paso (LSB) es $\Delta = V_{pp}/2^{B}$; modelando el error como ruido uniforme en $[-\Delta/2,\Delta/2]$ su potencia es $\sigma_q^2 = \Delta^2/12$, lo que da la cota
$$
\mathrm{SQNR}_{\max} \approx 6{,}02\,B + 1{,}76\ [\text{dB}].
$$
Cada bit añade $\approx 6$ dB. Es un piso de ruido irreducible y una fuente de error en la implementación embebida (Paso 5: punto fijo Q vs float, §6.5).

### 3.2 Teorema de Nyquist-Shannon y aliasing

> Si $x_a(t)$ es de **banda limitada** ($X_a(f)=0$ para $\lvert f\rvert\ge f_B$), queda **completamente determinada** por sus muestras $x[n]=x_a(nT)$ si $f_s > 2f_B$, y se reconstruye con interpolación sinc:
> $$ x_a(t)=\sum_{n=-\infty}^{\infty} x[n]\,\operatorname{sinc}\!\Big(\frac{t-nT}{T}\Big),\quad \operatorname{sinc}(u)=\frac{\sin(\pi u)}{\pi u}. $$

La **tasa de Nyquist** es $2f_B$ (mínima admisible); su mitad $f_N = f_s/2$ es la **frecuencia de Nyquist** (máxima frecuencia representable sin ambigüedad).

**Aliasing.** Si $f_s\le 2f_B$ o existen componentes por encima de $f_s/2$, las réplicas espectrales se solapan. Una componente $f_0 > f_s/2$ se pliega:
$$
f_{\text{alias}} = \Big\lvert f_0 - f_s\cdot\operatorname{round}\!\big(\tfrac{f_0}{f_s}\big)\Big\rvert.
$$
El aliasing es **irreversible** una vez muestreada la señal; por eso se usa un **filtro anti-aliasing analógico** (paso-bajo, antes del ADC).

**Ejemplo numérico.** Con $f_s = 500$ Hz ($f_N = 250$ Hz): una interferencia de 80 Hz se representa bien; un parásito de 480 Hz se pliega a $\lvert 480 - 500\cdot\operatorname{round}(480/500)\rvert = \lvert 480-500\rvert = 20$ Hz, disfrazándose de 20 Hz y contaminando la banda útil.

**Justificación de $f_s = 500$ Hz para ECG.** Banda útil $f_B = 40$ Hz, interferencia de red 50 Hz, Nyquist mínima $2\times40 = 80$ Hz. Se elige $f_s = 500$ Hz (factor de sobremuestreo $\approx 6{,}25\times$):

| Magnitud | Valor | Comentario |
|---|---|---|
| Banda útil $f_B$ | 40 Hz | Contenido diagnóstico P-QRS-T |
| Nyquist mínima | 80 Hz | Cota teórica estricta |
| Interferencia de red | 50 Hz | Debe quedar sin alias para poder filtrarla (notch) |
| $f_s$ elegida | 500 Hz | $f_N = 250$ Hz |
| Sobremuestreo | $\approx 6{,}25\times$ | Margen para roll-off del anti-aliasing |

El factor $\approx 6\times$ deja banda de transición amplia al anti-aliasing analógico, mantiene la red de 50 Hz muy por debajo de $f_N$ (se muestrea sin alias y se elimina con notch IIR) y mejora la resolución temporal del QRS.

### 3.3 Representaciones tiempo ↔ frecuencia

**DTFT** (continua y $2\pi$-periódica en $\omega$):
$$
X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n]\,e^{-j\omega n}.
$$
Es la herramienta teórica para la **respuesta en frecuencia** de un sistema.

**DFT** (muestrea la DTFT en $N$ puntos $\omega_k = 2\pi k/N$):
$$
X[k] = \sum_{n=0}^{N-1} x[n]\,e^{-j2\pi kn/N},\qquad k=0,\dots,N-1.
$$
La **FFT** es un algoritmo $O(N\log N)$ que produce **exactamente** la misma DFT que el cálculo directo $O(N^2)$. Como $X[k]=X(e^{j\omega})\big\rvert_{\omega=2\pi k/N}$, la DFT son muestras de la DTFT sobre el círculo unitario.

**Resolución frecuencial.** Con $N$ muestras a tasa $f_s$:
$$
\boxed{\;\Delta f = \frac{f_s}{N}\;}\ [\text{Hz/bin}], \qquad f_k = k\,\frac{f_s}{N}.
$$
Ejemplo ECG: $f_s = 500$ Hz, $N = 5000$ (10 s) ⇒ $\Delta f = 0{,}1$ Hz, suficiente para resolver el pico de 50 Hz frente a la banda diagnóstica.

> **Ventaneo:** truncar a $N$ muestras aplica una ventana rectangular implícita → *fuga espectral* (leakage). Las ventanas (Hann, Hamming, Blackman) reducen lóbulos laterales a costa de ensanchar el lóbulo principal. El mismo concepto reaparece en el diseño FIR por ventaneo (§4.3) pero con rol distinto (conformar $h[n]$, no analizar el espectro).

**Transformada Z** (generaliza la DTFT a todo $\mathbb{C}$):
$$
X(z) = \sum_{n=-\infty}^{\infty} x[n]\,z^{-n},\qquad z = re^{j\omega}.
$$
La **ROC** es un anillo $r_1<\lvert z\rvert<r_2$ que **no incluye polos**. Para señal causal la ROC es el exterior de un círculo. Un sistema LTI causal es **estable (BIBO)** si y solo si su ROC incluye el círculo unitario $\lvert z\rvert=1$, lo que equivale a que **todos los polos estén dentro** del círculo unitario — criterio central del diseño IIR (§5.7). Evaluando $X(z)$ sobre $z=e^{j\omega}$ se recupera la DTFT.

**Plano z.** El círculo unitario es el eje de frecuencias discreto: de $z=1$ ($\omega=0$, DC) a $z=-1$ ($\omega=\pi$, $f_s/2$). Un **cero** cerca del círculo crea una muesca (base del notch); un **polo** cerca del círculo crea un realce resonante. El mapa $z=e^{sT}$ vincula plano $s$ y plano $z$ (base de la transformada bilineal, §5.5).

### 3.4 Convolución lineal y filtrado

Un sistema LTI queda caracterizado por su **respuesta al impulso** $h[n]$. **Filtrar es convolucionar**:
$$
y[n] = x[n]*h[n] = \sum_{k=-\infty}^{\infty} x[k]\,h[n-k].
$$
Para un **FIR** de longitud $M$, $h[n]$ es finita y la suma es directa (§4). Para un **IIR**, $h[n]$ es infinita y conviene la forma recursiva (§5):
$$
y[n] = \sum_{k=0}^{M} b_k\,x[n-k] - \sum_{k=1}^{N} a_k\,y[n-k].
$$
En el dominio Z la convolución es producto, $Y(z)=H(z)X(z)$, con
$$
H(z) = \frac{\sum_{k=0}^{M} b_k z^{-k}}{1+\sum_{k=1}^{N} a_k z^{-k}}.
$$
Las raíces del numerador son los **ceros** y las del denominador los **polos**. La respuesta en frecuencia es $H(e^{j\omega})=\lvert H(e^{j\omega})\rvert e^{j\phi(\omega)}$.

### 3.5 Magnitud, fase, fase lineal y retardo de grupo

**Magnitud en dB:** $\lvert H(e^{j\omega})\rvert_{\text{dB}} = 20\log_{10}\lvert H(e^{j\omega})\rvert$. La banda de paso ideal tiene $\approx 0$ dB; la de rechazo $\to -\infty$ dB. Las specs $R_p$ (rizado de paso) y $A_s$ (atenuación de rechazo) se expresan en dB.

**Fase lineal.** Un filtro tiene fase lineal si $\phi(\omega) = -\alpha\omega\ (+\beta)$, es decir una recta en $\omega$ → **retardo constante** de $\alpha$ muestras para todas las frecuencias. Si todas las componentes se retrasan lo mismo, la forma de onda se traslada **sin deformarse**. Con fase no lineal, unas componentes se atrasan más que otras y la **morfología se distorsiona**. En ECG es crítico: el diagnóstico depende de amplitudes y tiempos relativos de las ondas P-QRS-T. Los FIR simétricos ($h[n]=\pm h[M-1-n]$) garantizan fase lineal exacta con retardo $\alpha=(M-1)/2$; los IIR **no** la tienen en general.

**Retardo de grupo:**
$$
\boxed{\;\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}\;}\ [\text{muestras}].
$$
Fase lineal ⇒ $\tau_g$ = constante (sin distorsión de forma); fase no lineal ⇒ $\tau_g(\omega)$ varía (distorsión morfológica). La **variación** de $\tau_g$ en la banda útil cuantifica esa distorsión.

### 3.6 Densidad espectral de potencia (PSD)

La **PSD** $S_x(f)$ describe el reparto de potencia por frecuencia (potencia/Hz). Para una señal aleatoria estacionaria es la TF de la autocorrelación (Wiener-Khinchin). Se estima con el **periodograma** $\hat S_x[k]=\tfrac1N\lvert X[k]\rvert^2$ o el método de **Welch** (promedio de periodogramas de segmentos solapados y ventaneados → menos varianza). En un ECG ruidoso la PSD muestra: lóbulo diagnóstico 0.5–40 Hz, pico agudo en 50 Hz (red) y piso de ruido de banda ancha. Comparar PSD **antes vs después** del filtrado evidencia la eficacia del filtro (Paso 3).

### 3.7 Métricas de calidad

Se calculan con tres señales alineadas: limpia $s[n]$ (referencia), contaminada $x[n]=s[n]+r[n]$ y filtrada $\hat s[n]$.

**SNR:**
$$
\boxed{\;\mathrm{SNR}_{\text{dB}} = 10\log_{10}\frac{\sum_n s^2[n]}{\sum_n (\hat s[n]-s[n])^2}\;}
$$
La mejora es $\Delta\mathrm{SNR}=\mathrm{SNR}_{\text{out}}-\mathrm{SNR}_{\text{in}}$.

**RMSE:** $\mathrm{RMSE}=\sqrt{\tfrac1N\sum_n(\hat s[n]-s[n])^2}$ (mismas unidades que la señal; conviene normalizar a NRMSE = RMSE/rango).

**Distorsión de fase:** variación de $\tau_g$ en la banda útil ($\max_\omega\tau_g-\min_\omega\tau_g$; cero ⇒ fase lineal perfecta), o el residuo tras compensar el retardo nominal (un FIR de fase lineal deja residuo $\approx 0$; un IIR deja residuo no nulo).

**Ejemplo numérico de SNR.** ECG con $P_{\text{señal}}=1000$ y ruido inicial $P_r=250$:
$$
\mathrm{SNR}_{\text{in}} = 10\log_{10}\tfrac{1000}{250} = 10\log_{10}4 = 6{,}02\ \text{dB}.
$$
Tras notch 50 Hz + LP 40 Hz, el residuo baja a $P_e=10$:
$$
\mathrm{SNR}_{\text{out}} = 10\log_{10}\tfrac{1000}{10} = 20\ \text{dB},\qquad \Delta\mathrm{SNR} = 20-6{,}02 \approx \mathbf{14\ dB}.
$$

---

<a id="4-diseno-de-filtros-fir"></a>
## 4. Diseño de filtros FIR

> Síntesis fiel de `../_kb/02-fir.md`. Prerrequisitos: §3 (Nyquist, transformada Z, respuesta en frecuencia). Implementación en §7 (`fir1`, `firpm`, `kaiserord`).

### 4.1 Qué es un filtro FIR

Un filtro **FIR** (*Finite Impulse Response*) tiene respuesta al impulso $h[n]$ con un número **finito** de muestras no nulas. De orden $N$, tiene $N+1$ coeficientes (taps). La salida es una **convolución finita**:
$$
y[n] = \sum_{k=0}^{N} h[k]\,x[n-k].
$$
No hay realimentación; la salida solo depende de la entrada actual y de $N$ entradas pasadas. Coste $\approx N+1$ **MACs**/muestra.

**Función de transferencia — solo ceros:**
$$
H(z) = \sum_{k=0}^{N} h[k]\,z^{-k} = h[0]+h[1]z^{-1}+\cdots+h[N]z^{-N}.
$$
Es un polinomio en $z^{-1}$: **solo tiene ceros** (todos los polos en $z=0$, sin efecto sobre estabilidad). Es **incondicionalmente estable** (BIBO) porque $\sum_k\lvert h[k]\rvert<\infty$ y no hay realimentación que diverja; no puede volverse inestable por cuantización de coeficientes.

| Propiedad | FIR |
|---|---|
| Memoria | $N+1$ coeficientes + buffer de $N$ muestras |
| Estabilidad | Siempre estable |
| Fase lineal | Alcanzable exactamente por simetría de $h[n]$ |
| Orden típico | Alto (decenas a cientos) para transiciones estrechas |
| Coste | $\approx N+1$ MACs/muestra |

### 4.2 Fase lineal y los 4 tipos

Un FIR tiene fase lineal si y solo si sus coeficientes son **simétricos** o **antisimétricos**:
$$
h[n] = \pm\,h[N-n],\qquad n=0,\dots,N.
$$
Signo $+$ → simétrico (fase lineal pura); signo $-$ → antisimétrico (desfase adicional de $90°$). Demostración (caso simétrico): factorizando el retardo central $\tau=N/2$, los términos exponenciales se combinan en cosenos, de modo que
$$
H(e^{j\omega}) = e^{-j\omega N/2}\,A(\omega),\quad A(\omega)\in\mathbb{R}
\;\Rightarrow\; \angle H = -\omega\frac{N}{2}+\{0\text{ ó }\pi\},
$$
con retardo de grupo constante $\tau_g = N/2$ muestras $= N/(2f_s)$ segundos.

| Tipo | Simetría | $N$ | N.º coef. | Restricciones de uso |
|------|----------|-----|-----------|----------------------|
| **I** | Simétrico | par | impar | El más versátil: **LP, HP, BP, BR** todos posibles |
| **II** | Simétrico | impar | par | $H(e^{j\pi})=0$ → **no** sirve para HP ni BR (cero forzado en Nyquist) |
| **III** | Antisimétrico | par | impar | $H(0)=H(e^{j\pi})=0$ → solo **BP, derivadores, Hilbert** |
| **IV** | Antisimétrico | impar | par | $H(0)=0$ → **HP, derivadores, Hilbert** (no LP) |

**Regla mnemotécnica:** para un **pasa-bajos** general use **Tipo I** (orden par, simétrico). Antisimétrico siempre fuerza $H(0)=0$ (inútil para LP).

### 4.3 Método de ventanas

Idea: partir de la respuesta al impulso **ideal** (infinita), **truncarla** a $N+1$ muestras y suavizar bordes con una ventana $w[n]$. Para un **pasa-bajos ideal** con $\omega_c=2\pi f_c/f_s$, la respuesta ideal es la sinc:
$$
h_d[n] = \frac{\sin\!\big(\omega_c(n-\tfrac N2)\big)}{\pi(n-\tfrac N2)},\qquad h_d\!\big[\tfrac N2\big]=\frac{\omega_c}{\pi}.
$$
El filtro real es $h[n] = h_d[n]\,w[n]$.

**Fenómeno de Gibbs.** El truncamiento abrupto (ventana rectangular) produce ondulaciones cerca del corte y un **sobreimpulso fijo de ~9 %** que **no desaparece** al aumentar $N$ (solo se estrecha). Las ventanas suaves reducen los lóbulos laterales a cambio de **ensanchar la transición**: compromiso fundamental atenuación de lóbulos ↔ ancho de transición.

| Ventana | Ancho lóbulo principal | Atenuación lóbulo lateral | $A_s$ lograble | Ripple $\delta_p$ |
|---------|------------------------|----------------------------|----------------|-------------------|
| Rectangular | $4\pi/(N+1)$ | $-13$ dB | $\approx 21$ dB | $\sim 0{,}74$ dB |
| Hann | $8\pi/(N+1)$ | $-31$ dB | $\approx 44$ dB | $\sim 0{,}055$ dB |
| **Hamming** | $8\pi/(N+1)$ | $-41$ dB | $\approx 53$ dB | $\sim 0{,}019$ dB |
| Blackman | $12\pi/(N+1)$ | $-57$ dB | $\approx 74$ dB | $\sim 0{,}0017$ dB |
| **Kaiser** ($\beta$) | depende de $\beta$ | ajustable | **$A_s$ a pedido** | ajustable |

Definiciones ($0\le n\le M$, $M=N$):
$$
w_{\text{Hann}}[n]=0{,}5-0{,}5\cos\tfrac{2\pi n}{M},\quad w_{\text{Hamming}}[n]=0{,}54-0{,}46\cos\tfrac{2\pi n}{M},
$$
$$
w_{\text{Blackman}}[n]=0{,}42-0{,}5\cos\tfrac{2\pi n}{M}+0{,}08\cos\tfrac{4\pi n}{M}.
$$

### 4.4 Fórmulas de orden

La transición $\Delta f = f_r-f_p$ determina el orden; en radianes $\Delta\omega = 2\pi\Delta f/f_s$.

| Ventana | Estimación de orden $N$ | $A_s$ asociada |
|---------|--------------------------|----------------|
| Rectangular | $N\approx 0{,}9\,f_s/\Delta f$ | $\sim 21$ dB |
| Hann | $N\approx 3{,}1\,f_s/\Delta f$ | $\sim 44$ dB |
| **Hamming** | $N\approx 3{,}3\,f_s/\Delta f$ | $\sim 53$ dB |
| Blackman | $N\approx 5{,}5\,f_s/\Delta f$ | $\sim 74$ dB |

> Redondear hacia arriba y, en Tipo I, ajustar $N$ a **par**.

**Fórmula de Kaiser (paramétrica):** dada la atenuación $A=A_s$ (dB),
$$
\beta =
\begin{cases}
0{,}1102\,(A-8{,}7), & A>50\\
0{,}5842\,(A-21)^{0{,}4}+0{,}07886\,(A-21), & 21\le A\le 50\\
0, & A<21
\end{cases}
\qquad
\boxed{\,N\approx\frac{A-8}{2{,}285\,\Delta\omega}\,}.
$$
Con Kaiser se especifica $A_s$ y la transición y la fórmula devuelve $N$ y $\beta$ directamente (`kaiserord`, §7.2.6).

### 4.5 Ejemplo numérico canónico (ECG)

**Especificación** (aplicación A): pasa-bajos FIR de fase lineal, $f_s = 500$ Hz, $f_c = 40$ Hz, transición $40\to50$ Hz ($\Delta f = 10$ Hz), ventana Hamming ($A_s\approx 53$ dB).

**Orden (regla de Hamming):**
$$
N \approx \frac{3{,}3\,f_s}{\Delta f} = \frac{3{,}3\times500}{10} = 165 \;\Rightarrow\; N=166\ (\text{par, Tipo I}),\quad N+1 = \mathbf{167}\ \text{coef.}
$$
> Verificación cruzada con Kaiser para $A_s=53$ dB: $\Delta\omega = 2\pi\cdot10/500 = 0{,}1257$, $N\approx(53-8)/(2{,}285\cdot0{,}1257)\approx 157$. Mismo orden de magnitud (Hamming algo más conservadora).

**Frecuencia de corte de diseño:** se centra en la transición, $f_c'=(40+50)/2=45$ Hz ⇒ $\omega_c = 2\pi\cdot45/500 = 0{,}5655 = 0{,}18\pi$. Normalizada a Nyquist: $45/250 = 0{,}18$.

**Coeficientes:**
$$
h[n] = \underbrace{\frac{\sin\!\big(\omega_c(n-\tfrac N2)\big)}{\pi(n-\tfrac N2)}}_{\text{sinc ideal}}\cdot\underbrace{\Big(0{,}54-0{,}46\cos\tfrac{2\pi n}{N}\Big)}_{\text{Hamming}},\quad n=0,\dots,166.
$$
- Centro $n=83$: $h[83]=\omega_c/\pi\approx 0{,}18$ (pico).
- Simetría $h[n]=h[166-n]$ ⇒ Tipo I, fase lineal exacta.
- Los extremos son pequeños; crecen oscilando con el signo de la sinc hacia el pico central y decrecen simétricamente; la envolvente Hamming suprime el ripple de Gibbs.

**Retardo de grupo:** $\tau_g = N/2 = 83$ muestras $= 83/500 = 0{,}166$ s $= \mathbf{166\ ms}$, constante (no distorsiona P-QRS-T). Si fuera excesivo, se reduciría $N$ (relajando la transición) o se pasaría a IIR aceptando fase no lineal.

**Coste:** $\approx 167$ MACs/muestra; a 500 Hz son $\approx 83{,}5$ kMAC/s — viable en ESP32/STM32 con FPU, inviable en Arduino UNO en punto fijo.

### 4.6 Parks-McClellan / Remez (equiripple)

El método de ventanas reparte el error de forma desigual. **Parks-McClellan** (intercambio de **Remez**) diseña el FIR **óptimo minimax**: minimiza el error máximo repartiéndolo uniformemente (respuesta **equiripple**):
$$
\min_{h}\ \max_{\omega\in\text{bandas}}\ \big\lvert W(\omega)\,[A(\omega)-D(\omega)]\big\rvert,
$$
donde $D(\omega)$ es la respuesta deseada (1 en paso, 0 en rechazo) y $W(\omega)$ una ponderación que permite **ripples distintos** en paso ($\delta_p$) y rechazo ($\delta_s$). El **teorema de alternancia** caracteriza la solución única (el error alcanza $\pm\delta$ con signos alternados en $\ge L+2$ frecuencias).

**Estimación de orden (Kaiser para equiripple):**
$$
N\approx\frac{-10\log_{10}(\delta_p\delta_s)-13}{2{,}324\,\Delta\omega}.
$$
**Cuándo:** equiripple logra el **menor orden** para una spec dada (ideal si cómputo/memoria son críticos); ventanas son más simples, predecibles y robustas (Kaiser ya da casi-óptimo con una fórmula).

### 4.7 Verificación de $H(z)$ (qué mirar en simulación, Paso 3)

1. **Magnitud** en dB: comprobar $f_c$, ripple $\le R_p$, atenuación $\ge A_s$.
2. **Fase / retardo de grupo:** confirmar fase lineal y $\tau_g=N/2$ constante.
3. **Polos-ceros** (`zplane`): polos en $z=0$; ceros sobre/cerca del círculo (los del corte). En FIR de fase lineal los ceros aparecen en **cuádruplas recíprocas conjugadas** ($z_0,z_0^*,1/z_0,1/z_0^*$).
4. **Suma de coeficientes:** $\sum_k h[k] = H(e^{j0})\approx 1$ (ganancia unitaria en DC para LP).
5. **Respuesta al impulso:** reproduce exactamente $h[n]$.

---

<a id="5-diseno-de-filtros-iir"></a>
## 5. Diseño de filtros IIR

> Síntesis fiel de `../_kb/03-iir.md` (autoridad para los números del ejemplo IIR). Prerrequisitos: §3 (transformada Z, plano $z$, fase/retardo de grupo). Implementación en §7 (`butter`/`cheby1`/`cheby2`/`ellip`, `*ord`, `tf2sos`/`sosfilt`).

### 5.1 Qué es un filtro IIR

Un filtro **IIR** (*Infinite Impulse Response*) es **recursivo**: la salida depende de entradas **y** de salidas pasadas (realimentación). Su $h[n]$ tiene duración **infinita**.

**Ecuación en diferencias:**
$$
\boxed{\;y[n] = \sum_{k=0}^{M} b_k\,x[n-k] - \sum_{k=1}^{N} a_k\,y[n-k]\;}
$$
Los $b_k$ forman el numerador (ceros, parte no recursiva); los $a_k$ con $k\ge1$ la parte recursiva (polos), con $a_0=1$.

**Función de transferencia:**
$$
H(z) = \frac{B(z)}{A(z)} = \frac{b_0+b_1 z^{-1}+\cdots+b_M z^{-M}}{1+a_1 z^{-1}+\cdots+a_N z^{-N}}.
$$
Los **ceros** $c_m$ (raíces de $B$) anulan la salida en sus frecuencias (útil para notch); los **polos** $d_k$ (raíces de $A$) producen resonancias y **determinan la estabilidad** (§5.7).

| Aspecto | **IIR** | **FIR** |
|---------|---------|---------|
| $h[n]$ | Infinita | Finita ($N+1$) |
| Polos | Sí | No (solo en $z=0$) → siempre estable |
| Orden para igual $A_s$ | **Bajo** (típ. 2–10) | Alto (típ. 5–20× mayor) |
| Fase | **No lineal** | Lineal exacta si $h[n]$ simétrica |
| Estabilidad | Debe verificarse ($\lvert d_k\rvert<1$) | Garantizada |
| Sensibilidad a cuantización | Alta (polos cerca de $\lvert z\rvert=1$) → usar SOS | Baja |
| Coste/muestra | $\approx 5\cdot(\text{secciones})$ MACs (SOS) | $\approx N+1$ MACs |

### 5.2 Prototipos analógicos

El diseño IIR parte de un **prototipo analógico** $H_a(s)$ y lo lleva al dominio digital por **transformada bilineal** (§5.5). Los cuatro prototipos canónicos:

| Prototipo | Ripple paso | Ripple rechazo | Transición | Fase | Orden | Ceros finitos |
|-----------|:-----------:|:--------------:|:----------:|:----:|:-----:|:-------------:|
| **Butterworth** | No (plano) | No (monótono) | Suave | La mejor | **Máximo** | No |
| **Chebyshev I** | Sí ($R_p$) | No | Media-alta | Media | Medio | No |
| **Chebyshev II** | No (plano) | Sí ($A_s$) | Media-alta | Media | Medio | Sí ($j\Omega$) |
| **Elíptico (Cauer)** | Sí ($R_p$) | Sí ($A_s$) | **La más abrupta** | La peor | **Mínimo** | Sí ($j\Omega$) |

Módulos característicos:
$$
\lvert H_a(j\Omega)\rvert^2_{\text{Butter}} = \frac{1}{1+(\Omega/\Omega_c)^{2N}},\qquad
\lvert H_a(j\Omega)\rvert^2_{\text{Cheby I}} = \frac{1}{1+\varepsilon^2 T_N^2(\Omega/\Omega_p)}.
$$
**Cuándo elegir:** Butterworth → banda pasante limpia y fase benigna (defecto biomédico); Chebyshev I → se admite rizado en la banda útil para bajar orden; Chebyshev II → banda pasante plana con ripple en rechazo; Elíptico → transición estrechísima con orden mínimo y fase no crítica. *Butterworth paga con orden la suavidad; Elíptico paga con fase la eficiencia.*

### 5.3 Cálculo del orden $N$

Parámetros: $R_p$ [dB] (ripple de paso), $A_s$ [dB] (atenuación de rechazo), $\varepsilon=\sqrt{10^{R_p/10}-1}$, y $\Omega_p,\Omega_r$ (frecuencias angulares analógicas tras *prewarping*).

**Butterworth:**
$$
\boxed{\;N\ge\frac{\log_{10}\!\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}{2\log_{10}(\Omega_r/\Omega_p)}\;}
$$

**Chebyshev (I y II):**
$$
\boxed{\;N\ge\frac{\cosh^{-1}\!\sqrt{\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}}{\cosh^{-1}(\Omega_r/\Omega_p)}\;},\qquad \cosh^{-1}(x)=\ln(x+\sqrt{x^2-1}).
$$
Como $\cosh^{-1}$ crece más rápido que $\log_{10}$, el orden Chebyshev es **siempre $\le$** Butterworth para idéntica máscara. El **elíptico** (integrales elípticas $K$) da el **mínimo** de los cuatro. En la práctica se delega a `buttord`/`cheb1ord`/`cheb2ord`/`ellipord` (§7).

### 5.4 $H_a(s)$ del prototipo

$$
H_a(s) = H_0\,\frac{\prod_m(s-z_m)}{\prod_{k=1}^{N}(s-p_k)}.
$$
Butterworth y Cheby I son **todo-polos**; Cheby II y elíptico añaden ceros sobre $j\Omega$. Los polos Butterworth (prototipo normalizado $\Omega_c=1$) están **equiespaciados sobre el semicírculo de radio $\Omega_c$ en el semiplano izquierdo**:
$$
p_k = \Omega_c\,\exp\!\Big[j\,\frac{\pi(2k+N-1)}{2N}\Big],\quad k=1,\dots,N.
$$
Para $N=2$: $H_a(s)=\dfrac{\Omega_c^2}{s^2+\sqrt2\,\Omega_c s+\Omega_c^2}$ (el amortiguamiento $\sqrt2$ es la firma del Butterworth de 2.º orden).

| Prototipo | Polos | Ceros finitos |
|-----------|-------|---------------|
| Butterworth | Círculo de radio $\Omega_c$ (SPI) | Ninguno |
| Chebyshev I | Sobre una elipse | Ninguno |
| Chebyshev II | Recíprocos de Cheby I | Sobre $j\Omega$ |
| Elíptico | Dentro de una elipse | Sobre $j\Omega$ |

### 5.5 Transformada bilineal (TBL) y prewarping

**Mapeo $s\leftrightarrow z$:**
$$
\boxed{\;s = \frac{2}{T}\cdot\frac{1-z^{-1}}{1+z^{-1}}\;},\qquad T = 1/f_s.
$$
Sustituyendo en $H_a(s)$ se obtiene directamente $H(z)$. La TBL mapea el **semiplano izquierdo** ($\operatorname{Re}\{s\}<0$) al **interior del círculo unitario** ($\lvert z\rvert<1$) — por eso un prototipo analógico estable produce un IIR estable — y el **eje $j\Omega$** completo al círculo unitario **una sola vez** (sin aliasing, a diferencia de la invariante al impulso).

**Warping y prewarping.** Evaluando en $s=j\Omega$, $z=e^{j\omega}$:
$$
\boxed{\;\Omega = \frac{2}{T}\tan\!\Big(\frac{\omega}{2}\Big)\;}
$$
Esta relación **no es lineal** (comprime $\Omega\in(0,\infty)$ en $\omega\in(0,\pi)$): es el **warping**. Para que las frecuencias críticas caigan exactamente donde se quiere, se **predistorsiona** cada frecuencia analógica antes de calcular $H_a(s)$:
$$
\Omega_{\text{diseño}} = \frac{2}{T}\tan\!\Big(\frac{\omega_{\text{deseado}}}{2}\Big),\qquad \omega_{\text{deseado}} = \frac{2\pi f}{f_s}.
$$
Tras la TBL esa $\Omega$ vuelve a $\omega_{\text{deseado}}$ con error nulo. **Procedimiento:** prewarpear $\Omega_p,\Omega_r$, diseñar $H_a(s)$, aplicar TBL.

**Desarrollo $H_a(s)\to H(z)$ (1.er orden).** Para $H_a(s)=\dfrac{\Omega_c}{s+\Omega_c}$, con $\alpha=2/T$:
$$
H(z) = \underbrace{\frac{\Omega_c}{\alpha+\Omega_c}}_{b_0=b_1}\cdot\frac{1+z^{-1}}{1+\dfrac{\Omega_c-\alpha}{\Omega_c+\alpha}z^{-1}},\qquad a_1 = \frac{\Omega_c-\alpha}{\Omega_c+\alpha},
$$
con ecuación en diferencias $y[n]=b_0 x[n]+b_1 x[n-1]-a_1 y[n-1]$. Para órdenes altos se procede sección por sección (biquads, §5.8).

### 5.6 Ejemplo numérico canónico — IIR Butterworth LP para ECG

> **Autoridad numérica:** este ejemplo sigue `../_kb/03-iir.md`. El resultado clave ($N=13$ para Butterworth) motiva el cambio de prototipo y el uso de SOS — ver nota de reconciliación al final de §6.3.

**Especificación:** $f_s = 500$ Hz ($T=2$ ms), $f_p = 40$ Hz, $f_r = 60$ Hz, $R_p = 1$ dB, $A_s = 40$ dB, prototipo Butterworth LP.

**Paso 1 — frecuencias digitales:**
$$
\omega_p = \frac{2\pi\cdot40}{500} = 0{,}5027 = 0{,}16\pi,\qquad \omega_r = \frac{2\pi\cdot60}{500} = 0{,}7540 = 0{,}24\pi.
$$

**Paso 2 — prewarping** (con $2/T = 1000$):
$$
\Omega_p = 1000\tan(0{,}2513) = \mathbf{256{,}76}\ \text{rad/s}\ (\approx 40{,}86\ \text{Hz}),
$$
$$
\Omega_r = 1000\tan(0{,}3770) = \mathbf{395{,}93}\ \text{rad/s}\ (\approx 63{,}01\ \text{Hz}).
$$

**Paso 3 — orden (Butterworth):**
$$
10^{A_s/10}-1 = 9999,\qquad 10^{R_p/10}-1 = 0{,}2589,\qquad \frac{9999}{0{,}2589} = 38\,617,
$$
$$
\log_{10}(38\,617) = 4{,}5868,\qquad \frac{\Omega_r}{\Omega_p} = 1{,}5420,\qquad \log_{10}(1{,}5420) = 0{,}1881,
$$
$$
N \ge \frac{4{,}5868}{2\cdot0{,}1881} = \frac{4{,}5868}{0{,}3762} = 12{,}19 \;\Longrightarrow\; \boxed{N = 13}.
$$

> **Lectura de ingeniería.** $N=13$ es altísimo: la transición $40\to60$ Hz (relación $1{,}54$) con 40 dB es **muy exigente para Butterworth**. Esto motiva tres decisiones reales:
> 1. **Relajar la máscara** ($A_s=20$–$30$ dB o ensanchar $f_r$) → $N$ baja a 4–6.
> 2. **Cambiar de prototipo** con la misma máscara: **Chebyshev I** da $N\approx 5{,}97\Rightarrow N=6$; el **elíptico** $N\approx 4$.
> 3. Si se mantiene $N$ alto, **es obligatorio realizar el filtro en cascada de biquads (SOS)**; una forma directa de orden 13 es numéricamente inviable.

**Paso 4 — corte y $H_a(s)$:** $\Omega_c = \Omega_p/\varepsilon^{1/N}$ con $\varepsilon = \sqrt{10^{0{,}1}-1} = 0{,}5088$. Con $\Omega_c$ se ubican los 13 polos sobre el semicírculo (SPI) y se arma $H_a(s)$ como producto de secciones de 2.º orden (más un polo real, por $N$ impar).

**Paso 5 — TBL y $H(z)$:** aplicando $s=\frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$ a cada sección:
$$
H(z) = \prod_i\frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}
$$
= cascada de 6 biquads + 1 sección de 1.er orden. Ecuación por sección:
$$
y_i[n] = b_{0i}x_i[n]+b_{1i}x_i[n-1]+b_{2i}x_i[n-2]-a_{1i}y_i[n-1]-a_{2i}y_i[n-2].
$$
Todos los polos $\lvert d_k\rvert<1$ ⇒ estable (la TBL lo garantiza). En Octave esto es `butter(N,Wn)` con salida `'sos'` (§7.3).

**Notch IIR de red (50 Hz).** Par de **ceros sobre el círculo** en $\omega_0 = 2\pi\cdot50/500 = 0{,}2\pi$ y par de **polos** dentro, mismo ángulo, radio $r\lesssim 1$:
$$
H_{\text{notch}}(z) = \frac{1-2\cos\omega_0\,z^{-1}+z^{-2}}{1-2r\cos\omega_0\,z^{-1}+r^2 z^{-2}}.
$$
El radio $r$ (0.95–0.99) fija el ancho: $r\to1$ ⇒ muesca estrechísima pero transitorio más largo. Coste mínimo (1 biquad, $\approx 5$ MACs/muestra); de ahí que se prefiera IIR para el notch aun cuando el LP principal sea FIR (estrategia mixta del Anexo A). Generable con `butter(2,[...],'stop')` o `iirnotch`.

### 5.7 Estabilidad

Un IIR causal es **estable (BIBO)** si y solo si **todos los polos** están estrictamente dentro del círculo unitario:
$$
\boxed{\;\lvert d_k\rvert<1\quad\forall k\;}
$$
**Verificación:** `roots(a)` y `max(abs(roots(a))) < 1`; visualmente `zplane` (todos los polos `×` dentro). El criterio de **Jury** lo comprueba algebraicamente sin factorizar. **Margen práctico:** polos muy cerca de $\lvert z\rvert=1$ (banda estrecha, notch con $r\to1$) son estables en teoría pero frágiles ante **cuantización de coeficientes** — importa la **sensibilidad** (§5.8, §6.5). Un FIR tiene $A(z)=1$ (polos en $z=0$) → siempre estable.

### 5.8 Estructuras de realización

Una misma $H(z)$ admite varias topologías, equivalentes en aritmética exacta pero muy distintas en punto fijo:

- **Forma Directa I (DF-I):** implementa literalmente la ecuación en diferencias; usa $M+N$ retardos; robusta pero con más memoria.
- **Forma Directa II (DF-II) y traspuesta (DF-II-T):** comparte la línea de retardo → solo $\max(M,N)$ retardos (mínima memoria, "canónica"). La traspuesta es la preferida en aritmética finita (menos error de redondeo) y la que usa por defecto `filter`. Inconveniente: en orden alto, nodos internos pueden **desbordar**.
- **Cascada SOS / biquads:**
$$
H(z) = g\prod_{i=1}^{\lceil N/2\rceil}\frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}.
$$
**Por qué mejora la estabilidad numérica:** la cuantización de coeficientes desplaza las raíces; en un polinomio de grado $N$ alto las raíces son **extremadamente sensibles** (problema de Wilkinson) y un polo casi en $\lvert z\rvert=1$ puede salir del círculo. Al partir en biquads, **cada par polo/cero se cuantiza por separado**: el error de un coeficiente solo afecta a su sección. Además permite escalar la ganancia sección a sección (controla el rango dinámico en punto fijo). **El formato `sos` es el estándar para IIR de orden $\ge 3$** y la recomendación por defecto del agente cuando "estabilidad numérica crítica sin DSP float".
- **Lattice:** parametrizada por coeficientes de reflexión $k_i$; estabilidad trivial ($\lvert k_i\rvert<1$) y baja sensibilidad; más operaciones por muestra (usada en adaptativos y predicción lineal de voz).

---

<a id="6-criterios-de-ingenieria"></a>
## 6. Criterios de ingeniería para diseño y selección

> Síntesis fiel de `../_kb/04-criterios-diseno.md`. El *porqué* de las decisiones; alimenta directamente al agente (§8).

### 6.1 Tabla de decisión FIR vs IIR

Para una **misma especificación** ($f_p,f_r,R_p,A_s$):

| Criterio | **FIR** | **IIR** | Gana |
|----------|---------|---------|------|
| Estabilidad | Siempre estable (solo ceros) | Condicional ($\lvert z\rvert<1$) | FIR |
| Fase | **Lineal exacta** (simetría) | No lineal | FIR |
| Orden para igual $A_s$ | Alto ($N$ 50–300) | Bajo ($N$ 2–10) | IIR |
| Coste (MACs/muestra) | $\approx N+1$ | $\approx 5\cdot S$ (SOS) | IIR |
| Memoria de coeficientes | $N+1$ | $6\cdot S$ | IIR |
| Sensibilidad a cuantización | Baja | Alta (polos cerca de $\lvert z\rvert=1$) | FIR |
| Latencia / retardo de grupo | Constante $=N/2$ (grande) | Variable, menor en promedio | IIR |
| Facilidad de diseño | Directo, siempre converge | Prototipo + bilineal + prewarp | FIR |
| Réplica de filtros analógicos | Pobre | Excelente | IIR |

**Conclusión:** **gana FIR** con fase lineal estricta (ECG, EMG), estabilidad crítica, o cómputo/memoria de sobra (ESP32/STM32 con FPU). **Gana IIR** con recursos escasos (Arduino UNO, RAM < 2 kB), transición muy abrupta con orden mínimo, o réplica de filtro analógico sin exigencia de fase.

### 6.2 Elección de ventana (FIR)

La ventana fija el piso de $A_s$ alcanzable. Regla: la ventana **más simple** cuya atenuación supere el $A_s$ requerido.

| Ventana | $A_s$ máx | $N$ aprox. | Cuándo |
|---------|-----------|------------|--------|
| Rectangular | ~21 dB | $0{,}9\,f_s/\Delta f$ | Solo si $A_s\le 20$ dB |
| Hann | ~44 dB | $3{,}1\,f_s/\Delta f$ | Atenuación media |
| **Hamming** | ~53 dB | $3{,}3\,f_s/\Delta f$ | **Defecto biomédico** (40–50 dB) |
| Blackman | ~74 dB | $5{,}5\,f_s/\Delta f$ | Alta atenuación |
| Kaiser | ajustable | fórmula | Cuando $A_s$ no encaja en las fijas |

**Kaiser vs equiripple:** ventana fija si su $A_s$ supera lo pedido por margen; **Kaiser** si hay que ajustar fino (paramétrica, rápida); **equiripple (`firpm`)** si el orden debe ser mínimo o se requieren rizados independientes en paso/rechazo.

### 6.3 Elección de prototipo IIR

Trade-off: abruptez de transición vs calidad de fase vs rizado.

| Prototipo | Orden $N$ típico | MACs (SOS) | Comentario |
|-----------|------------------|------------|------------|
| Butterworth | 8 | $5\cdot4 = 20$ | Más secciones, fase limpia |
| Chebyshev I/II | 5 | $5\cdot3 = 15$ | Compromiso |
| Elíptico | **4** | $5\cdot2 = 10$ | Mínimo cómputo, fase fea |

(Órdenes relativos de referencia para una máscara con $f_p,f_r$ cercanos y $A_s\approx 40$ dB.) **Butterworth** → fase y planitud importan y sobra orden; **Chebyshev** → compromiso; **Elíptico** → orden/cómputo mínimo y fase no crítica.

> **Nota de reconciliación (importante).** El ejemplo numérico autoritativo de §5.6 (de `03-iir.md`) usa la máscara concreta $f_p=40$, $f_r=60$, $R_p=1$, $A_s=40$, $f_s=500$ y obtiene **Butterworth $N=13$**, lo que motiva pasar a **Chebyshev I $N\approx6$** o **elíptico $N\approx4$** y a SOS. Esa es la versión coherente que se adopta en todo este documento. Los "órdenes típicos" de la tabla anterior (Butterworth $\approx8$) son una referencia genérica de `04-criterios-diseno.md` para una máscara distinta y más relajada; **no** deben confundirse con el caso canónico, donde Butterworth requiere $N=13$.

### 6.4 Coste computacional y de memoria

$$
\text{MACs}_{\text{FIR}}\approx N+1,\qquad \text{MACs}_{\text{IIR(SOS)}}\approx 5S,\qquad S=\lceil N/2\rceil.
$$
$$
\text{Coef}_{\text{FIR}} = N+1,\qquad \text{Coef}_{\text{IIR}} = 6S.
$$

**Ejemplo ECG** (LP $f_c=40$ Hz, $f_s=500$ Hz, $A_s\approx 40$ dB):

| Métrica | **FIR Hamming** | **IIR Butterworth** |
|---------|-----------------|---------------------|
| Orden $N$ | ~165 | ~6 |
| MACs/muestra | 166 | $5\cdot3 = 15$ |
| Coeficientes | 166 | 18 |
| Estados | 166 | 6 |
| Memoria float32 | $\approx 1{,}3$ kB | $\approx 96$ B |
| Carga a 500 Hz | 83 kMAC/s | 7.5 kMAC/s |

> El IIR es **~11× más barato en cómputo** y **~14× en memoria**. Como en ECG importa preservar la morfología P-QRS-T, se acepta el coste del FIR — o se usa IIR con filtrado *forward-backward* (`filtfilt`) **offline** para anular la fase.

### 6.5 Punto fijo vs punto flotante

**Formato Q$m.n$:** $m$ bits enteros + $n$ fraccionarios; $x_{\text{real}} = x_{\text{int}}\cdot2^{-n}$.

| Formato | Bits | Rango | Resolución | Uso |
|---------|------|-------|------------|-----|
| Q1.14 | 16 | $[-2,2)$ | $6{,}1\times10^{-5}$ | Coef. normalizados |
| Q1.15 | 16 | $[-1,1)$ | $3{,}05\times10^{-5}$ | Muestras ADC/audio |
| Q15.16 | 32 | $[-32768,32768)$ | $1{,}5\times10^{-5}$ | Acumuladores |

**Escalado y overflow:** coeficientes a $[-1,1)$ → Q15/Q14; el **acumulador** debe ser más ancho (32/64 bits) — un producto Q15×Q15 = Q30, y sumar $N$ productos exige $\lceil\log_2 N\rceil$ bits de guarda. Prevenir overflow con escalado o aritmética **saturante**. **Ruido de cuantización:** $\sigma_q^2 = \Delta^2/12$, $\Delta = 2^{-n}$; dos fuentes — cuantización de coeficientes (desplaza polos, puede **desestabilizar un IIR**) y de productos/acumulador (ruido aditivo). **Regla:** *IIR de orden > 2 en punto fijo ⇒ siempre SOS en cascada.*

| Plataforma | FPU | Float32 viable | Recomendación |
|------------|-----|----------------|---------------|
| Arduino UNO (AVR) | No | No (emulación ~100× lenta) | **Punto fijo Q15** |
| STM32F4/F7, ESP32 | **Sí (HW)** | **Sí** | **Float32** directo |
| STM32 Cortex-M0/M3 | No | Marginal | Punto fijo |

### 6.6 Restricciones por plataforma y presupuesto de ciclos

| Plataforma | Reloj | RAM | FPU | Aritmética | Filtro recomendado |
|------------|-------|-----|-----|------------|--------------------|
| **Arduino UNO** | 16 MHz | 2 kB | No | Q15 | **IIR orden bajo (SOS)**; FIR solo $N\lesssim 20$ |
| **ESP32** | 160–240 MHz | 320 kB+ | Sí | Float32 | **FIR orden alto** o IIR libre |
| **STM32F4** | 168 MHz | 128–192 kB | Sí | Float32 | FIR/IIR sin restricción práctica |

A $f_s = 500$ Hz hay $T = 2$ ms/muestra ⇒ ciclos disponibles $= f_{\text{clk}}\cdot T$: Arduino 32 000, ESP32 480 000, STM32F4 336 000. **Regla de presupuesto:** $\text{MACs}_{\text{filtro}}\cdot f_s \ll$ MAC/s disponibles, dejando margen ($\ge 50\%$) para ADC, ISR y jitter. En Arduino esto empuja hacia **IIR de orden bajo en punto fijo**.

Coste FIR $\approx N+1$ MACs/muestra; IIR (SOS) $\approx 5\cdot$secciones. Adquisición: **interrupción por timer** (recomendada, $f_s$ exacto) o **DMA** (máximo determinismo); buffer **circular** como línea de retardo natural. Latencia: $t_{\text{lat}}\approx \frac{N/2}{f_s} + \frac{L_{\text{bloque}}}{f_s} + t_{\text{cómputo}}$ (en FIR domina el retardo de grupo $N/2$).

### 6.7 Reglas atómicas accionables (entrada para el agente §8)

1. `fase_lineal == estricta` → **FIR** (regla dominante).
2. `RAM < 2 kB AND orden_FIR > 50` → **IIR**.
3. `estabilidad_numérica_crítica AND sin_FPU_float` → **SOS** (obligatorio).
4. `transición_estrecha AND cómputo_suficiente` → **IIR** de orden adecuado (Elíptico/Cheby).
5. `sin_FPU` → **punto fijo Q15**; `con_FPU` → **float32**.
6. `orden_IIR > 2` → **SOS en cascada**.
7. `tiempo_real_estricto` → timer-ISR + buffer circular.

| Si tu prioridad es… | Elige | Porque |
|---------------------|-------|--------|
| Preservar morfología (fase) | **FIR** | Única con fase lineal exacta |
| Mínimo cómputo/memoria | **IIR (SOS)** | Orden muy inferior |
| Estabilidad garantizada | **FIR** | No tiene polos |
| Transición abruptísima | **IIR Elíptico** | Orden mínimo |
| µC sin FPU | **IIR-SOS Q15** | Cabe en RAM y ciclos |

---

<a id="7-herramientas-octave-matlab"></a>
## 7. Herramientas Octave/MATLAB (núcleo de esta entrega)

> Síntesis de alta profundidad de `../_kb/06-octave.md`. Referencia con propósito, sintaxis, parámetros, salida y ejemplo de cada función. Las firmas siguen el **paquete `signal`** de Octave (compatible en su mayoría con la *Signal Processing Toolbox* de MATLAB).

### 7.1 Entorno

**Octave** es libre y mayormente compatible con MATLAB. Las funciones de PDS NO están en el núcleo: viven en el paquete **`signal`** (Octave Forge), que depende de **`control`**. En **MATLAB** pertenecen a la *Signal Processing Toolbox* (no se usa `pkg load`).

```matlab
pkg load signal      % carga el paquete (cada arranque de Octave)
% pkg install -forge signal   % instalación única (NO ejecutar aquí; solo documentado)
pkg list             % verifica paquetes cargados
```
Para scripts portables MATLAB/Octave:
```matlab
if exist('OCTAVE_VERSION','builtin'); pkg load signal; end
```
> **Regla de normalización clave:** `Wn` (frecuencia normalizada) $= f_c/(f_s/2)$, fracción de la Nyquist, en $(0,1)$.

### 7.2 Diseño FIR

#### 7.2.1 Ventanas

| Función | Firma | Devuelve |
|---|---|---|
| `hamming` | `w = hamming(L)` | ventana de Hamming, longitud `L` |
| `hanning` | `w = hanning(L)` | ventana de Hann |
| `blackman` | `w = blackman(L)` | ventana de Blackman |
| `rectwin` | `w = rectwin(L)` | ventana rectangular |
| `kaiser` | `w = kaiser(L, beta)` | ventana de Kaiser (parámetro `beta`) |

`L` = longitud = **orden + 1**. `beta` controla el compromiso lóbulo-principal/laterales (mayor β ⇒ más atenuación y transición más ancha).
```matlab
w = hamming(101);     % ventana para un FIR de orden 100
```

#### 7.2.2 `fir1` — FIR por método de ventanas
**Propósito:** diseñar FIR de fase lineal por ventaneo. **Salida:** coeficientes `b` (con `a=1` implícito).
```matlab
b = fir1(N, Wn)                 % LP por defecto, ventana Hamming
b = fir1(N, Wn, 'high')         % HP
b = fir1(N, [W1 W2])            % BP
b = fir1(N, [W1 W2], 'stop')    % BR / band-stop
b = fir1(N, Wn, window)         % ventana explícita (vector de longitud N+1)
```
- `N`: orden (devuelve `N+1` coeficientes). `Wn = fc/(fs/2)`. `window`: p. ej. `hamming(N+1)` o `kaiser(N+1,beta)`.

**Ejemplo — LP Hamming $f_c=40$ Hz, $f_s=500$ Hz (ECG):**
```matlab
fs = 500;  fc = 40;
Wn = fc/(fs/2);                 % = 0.16
N  = 100;                       % orden par => Tipo I, fase lineal, simétrico
b  = fir1(N, Wn, hamming(N+1)); % ventana Hamming explícita
```

#### 7.2.3 `fir2` — FIR con respuesta arbitraria (muestreo en frecuencia)
```matlab
b = fir2(N, f, m)               % f: frecuencias norm. (0->1, monótono); m: magnitud deseada
b = fir2(80, [0 0.1 0.16 1], [1 1 0 0]);  % LP con transición a mano
```
Útil para respuestas no estándar (rampas, multibanda con forma).

#### 7.2.4 `firls` — FIR óptimo por mínimos cuadrados
```matlab
b = firls(N, f, a)              % minimiza el error cuadrático con la respuesta deseada por bandas
b = firls(100, [0 0.14 0.18 1], [1 1 0 0]);  % LP paso/rechazo
```

#### 7.2.5 `firpm` — Parks-McClellan (Remez, equiripple)
**Propósito:** FIR equiripple óptimo (minimiza el error máximo). En Octave clásico el equivalente histórico es `remez`; `firpm` es el alias compatible con MATLAB.
```matlab
b = firpm(N, f, a)
b = firpm(N, f, a, w)           % w: pesos relativos por banda
b = firpm(60, [0 0.14 0.18 1], [1 1 0 0], [1 10]);  % rechazo 10x más penalizado
```

#### 7.2.6 `kaiserord` — estimar orden y β de Kaiser
**Propósito:** dado el requisito de transición y desviaciones, devuelve el orden mínimo, las cortes, `beta` y `ftype`, listos para `fir1`.
```matlab
[N, Wn, beta, ftype] = kaiserord(f, a, dev)
[N, Wn, beta, ftype] = kaiserord(f, a, dev, fs)   % f en Hz si se pasa fs
```
- `f`: bordes de banda. `a`: amplitudes por banda (1/0). `dev`: desviación máxima por banda (lineal, no dB). Conversión dB→lineal: `dev_paso = (10^(Rp/20)-1)/(10^(Rp/20)+1)`, `dev_rechazo = 10^(-As/20)`.

**Ejemplo (ECG, transición 40→50 Hz, $R_p=1$ dB, $A_s=40$ dB):**
```matlab
fs = 500;
dev = [(10^(1/20)-1)/(10^(1/20)+1), 10^(-40/20)];   % desviaciones de paso y rechazo
[N, Wn, beta, ftype] = kaiserord([40 50], [1 0], dev, fs);
b = fir1(N, Wn, ftype, kaiser(N+1, beta), 'noscale');
```

### 7.3 Diseño IIR

> Convención: frecuencias **normalizadas a Nyquist** salvo con la opción `'s'` (analógico, en rad/s).

#### 7.3.1 Prototipos

| Función | Firma básica | Característica |
|---|---|---|
| `butter` | `[b,a] = butter(N, Wn)` | Butterworth: plano en paso, sin rizado |
| `cheby1` | `[b,a] = cheby1(N, Rp, Wn)` | Cheby I: rizado `Rp` dB en paso |
| `cheby2` | `[b,a] = cheby2(N, Rs, Wn)` | Cheby II: rizado en rechazo (`Rs` dB) |
| `ellip` | `[b,a] = ellip(N, Rp, Rs, Wn)` | Elíptico: rizado en ambas bandas, transición mínima |

Opciones comunes a las cuatro:
```matlab
[b,a]    = butter(N, Wn)             % LP digital, coeficientes de transferencia
[b,a]    = butter(N, Wn, 'high')     % HP
[b,a]    = butter(N, [W1 W2])        % BP
[b,a]    = butter(N, [W1 W2],'stop') % BR
[z,p,k]  = butter(N, Wn)             % cero-polo-ganancia (recomendado para estabilidad)
[A,B,C,D]= butter(N, Wn)             % espacio de estados
[b,a]    = butter(N, Wn, 's')        % prototipo ANALÓGICO Ha(s) (Wn en rad/s)
```
- `Wn` digital $= f_c/(f_s/2)$. `'s'` ⇒ diseño analógico (útil para mostrar el prototipo antes de la bilineal).
- Para **SOS** combinar con `zp2sos`: `[z,p,k]=butter(N,Wn); sos=zp2sos(z,p,k);`

#### 7.3.2 Estimadores de orden
```matlab
[N, Wn] = buttord(Wp, Ws, Rp, Rs)    % Rp = rizado máx. paso (dB), Rs = atenuación mín. rechazo (dB)
[N, Wn] = cheb1ord(Wp, Ws, Rp, Rs)
[N, Wn] = cheb2ord(Wp, Ws, Rp, Rs)
[N, Wn] = ellipord(Wp, Ws, Rp, Rs)
```
Devuelven el **orden mínimo** y la(s) frecuencia(s) natural(es) que cumplen las specs.

**Ejemplo — Butterworth LP (ECG): $f_p=40$, $f_r=60$, $R_p=1$, $A_s=40$, $f_s=500$:**
```matlab
fs = 500;
Wp = 40/(fs/2);          % 0.16
Ws = 60/(fs/2);          % 0.24
Rp = 1;   As = 40;
[N, Wn] = buttord(Wp, Ws, Rp, As);   % aquí N resulta = 13 (coherente con §5.6)
[b, a]  = butter(N, Wn);
% Robusto: [z,p,k] = butter(N, Wn);  sos = zp2sos(z,p,k);
```
> Como $N=13$ es alto (§5.6), en la práctica se usa `cheb1ord`/`ellipord` con la misma máscara (orden $\approx6$ / $\approx4$) y **siempre** salida SOS.

#### 7.3.3 `iirnotch` — notch (rechazo de banda estrecho)
```matlab
[b, a] = iirnotch(w0, bw)            % filtro IIR de 2.º orden
[b, a] = iirnotch(w0, bw, ab)        % ab: profundidad del notch en dB (def. -3 dB)
```
- `w0 = f0/(fs/2)` (frecuencia central normalizada). `bw`: ancho a -3 dB normalizado; `bw = w0/Q`.

**Ejemplo — Notch 50 Hz, $f_s=500$ (ECG):**
```matlab
fs = 500;  f0 = 50;  Q = 35;
w0 = f0/(fs/2);          % = 0.20
bw = w0/Q;
[b, a] = iirnotch(w0, bw);
```
> Si `iirnotch` no estuviera disponible en Octave, un notch equivalente se arma con `ellip`/`butter` en modo `'stop'` con banda estrecha.

### 7.4 Análisis del filtro

#### 7.4.1 `freqz` — respuesta en frecuencia
```matlab
[H, w] = freqz(b, a, n)          % w en rad/muestra (0..pi)
[H, f] = freqz(b, a, n, fs)      % f en Hz (0..fs/2)
freqz(b, a)                      % sin salidas: dibuja módulo (dB) y fase
```
Módulo en dB: `20*log10(abs(H))`; fase en grados: `unwrap(angle(H))*180/pi`. Para FIR usar `a=1`.
```matlab
fs = 500;
[H, f] = freqz(b, a, 1024, fs);
subplot(2,1,1); plot(f, 20*log10(abs(H))); grid on; xlabel('Hz'); ylabel('|H| [dB]');
subplot(2,1,2); plot(f, unwrap(angle(H))*180/pi); grid on; xlabel('Hz'); ylabel('Fase [°]');
```

#### 7.4.2 `grpdelay` — retardo de grupo
```matlab
[gd, w] = grpdelay(b, a, n)
[gd, f] = grpdelay(b, a, n, fs)
```
Devuelve el retardo de grupo en **muestras**. Para un FIR de fase lineal de orden `N` es constante `= N/2`.

#### 7.4.3 `phasez` — respuesta de fase (desenrollada)
```matlab
[phi, w] = phasez(b, a, n)       % fase (rad), útil para inspeccionar linealidad
```

#### 7.4.4 `zplane` — diagrama polos-ceros
```matlab
zplane(b, a)                     % desde coeficientes de transferencia
zplane(z, p)                     % desde ceros y polos
```
Dibuja ceros (`o`) y polos (`x`) con el círculo unitario. **Estabilidad IIR:** todos los polos dentro (`abs(p) < 1`).

#### 7.4.5 `impz` — respuesta al impulso
```matlab
[h, t] = impz(b, a, n)
[h, t] = impz(b, a, n, fs)
```
Devuelve las `n` primeras muestras de `h[n]`. Para FIR, `impz(b,1)` reproduce los propios coeficientes.

### 7.5 Aplicación del filtro

#### 7.5.1 `filter` — forma directa (IIR y FIR)
```matlab
y = filter(b, a, x)
[y, zf] = filter(b, a, x, zi)    % zi/zf: estado inicial/final (procesado por bloques)
```
Implementa la ecuación en diferencias (DF-II traspuesta). Para FIR usar `a=1`. Introduce **retardo y fase no nula** (causal, apto tiempo real).

#### 7.5.2 `filtfilt` — filtrado de fase cero
```matlab
y = filtfilt(b, a, x)
```
Filtra **hacia adelante y hacia atrás** ⇒ **fase cero** y orden efectivo duplicado (atenuación al cuadrado). Ideal para no distorsionar la morfología P-QRS-T. **No** usar en tiempo real (no causal). Es la técnica que permite usar un IIR sin distorsión de fase en procesamiento **offline**.

#### 7.5.3 `fftfilt` — FIR por bloques vía FFT (overlap-add)
```matlab
y = fftfilt(b, x)                % solo FIR; eficiente para b y x largos
y = fftfilt(b, x, nfft)
```
Equivalente a `filter(b,1,x)` pero más rápido en FIR de orden alto.

#### 7.5.4 `conv` — convolución
```matlab
y = conv(x, h)                   % longitud length(x)+length(h)-1 ('full')
y = conv(x, h, 'same')           % misma longitud que x
```
Filtrado FIR "manual" (`y = conv(x,b)`); didáctico, sin manejo de estado.

#### 7.5.5 Estructuras SOS

| Función | Firma | Uso |
|---|---|---|
| `zp2sos` | `sos = zp2sos(z, p, k)` | cero-polo-ganancia → matriz SOS (`Nsec×6`) |
| `tf2sos` | `sos = tf2sos(b, a)` | transferencia → SOS |
| `sos2tf` | `[b, a] = sos2tf(sos)` | SOS → transferencia |
| `sosfilt`| `y = sosfilt(sos, x)` | aplica la cascada SOS a `x` |

```matlab
[z,p,k] = ellip(6, 1, 40, Wn);
sos = zp2sos(z, p, k);           % cascada de 3 biquads (mejor condicionamiento)
y   = sosfilt(sos, x);           % aplicación numéricamente estable
```
> SOS es la estructura recomendada para IIR de orden alto y para implementación en µC ("estabilidad numérica crítica sin DSP float → SOS", §8).

### 7.6 Análisis espectral

#### 7.6.1 FFT y eje de frecuencias
```matlab
X  = fft(x)                      % FFT de N puntos
X  = fft(x, N)                   % con zero-padding/truncado
Xs = fftshift(X)                 % centra el espectro en 0 Hz (eje bilateral)
```
Eje unilateral (0..fs): `f = (0:N-1)*fs/N;`, graficar la mitad `1:floor(N/2)`.
```matlab
N = length(x);
X = fft(x);
f = (0:N-1)*fs/N;
plot(f(1:floor(N/2)), abs(X(1:floor(N/2)))/N);   % magnitud unilateral
xlabel('Hz'); ylabel('|X(f)|'); grid on
```
Para reducir fuga espectral, ventanear antes: `X = fft(x .* hamming(N));`.

#### 7.6.2 `pwelch` — densidad espectral de potencia (PSD)
```matlab
[Pxx, f] = pwelch(x)                                 % defaults
[Pxx, f] = pwelch(x, window, noverlap, nfft, fs)     % forma completa
```
Estima la PSD por **Welch** (promediado de periodogramas con solape ⇒ menos varianza que `abs(fft).^2`).
```matlab
[Pxx, f] = pwelch(x, hamming(256), 128, 512, fs);
plot(f, 10*log10(Pxx)); xlabel('Hz'); ylabel('PSD [dB/Hz]'); grid on
```

### 7.7 Métricas (SNR, RMSE)

```matlab
% snr (si el paquete lo provee):
r = snr(signal, noise)           % SNR en dB a partir de señal y ruido separados
r = snr(x, fs)                   % estima SNR de un tono respecto a armónicos+ruido

% Cálculo manual (portátil, siempre funciona):
ruido_res = y - ref;                                 % error/ruido residual
SNR_dB = 10*log10(sum(ref.^2) / sum(ruido_res.^2));  % potencia señal / potencia ruido
RMSE   = sqrt(mean((y - ref).^2));                   % en unidades de la señal

% Mejora de SNR entrada->salida:
SNR_in  = 10*log10(sum(ref.^2)/sum((x - ref).^2));
SNR_out = 10*log10(sum(ref.^2)/sum((y - ref).^2));
mejora_dB = SNR_out - SNR_in;
```

### 7.8 Plantilla de script integradora (esqueleto comentado)

> Integra diseño → `freqz` → filtrado → FFT → métricas para el caso ECG. Adaptar la señal de entrada al dataset real. En MATLAB usar `fprintf` en lugar de `printf`.

```matlab
% --- APUNTES_OCTAVE: diseño -> análisis -> filtrado -> FFT -> métricas (ECG) ---
if exist('OCTAVE_VERSION','builtin'); pkg load signal; end
fs = 500;                                  % Hz (ECG, Anexo I-A)

% x  = señal contaminada (cargar del CSV/dataset);  ref = señal limpia de referencia.
% Ejemplo sintético autocontenido:
t   = (0:1/fs:5-1/fs).';  ref = sin(2*pi*1.2*t);        % ~72 lpm
x   = ref + 0.3*sin(2*pi*50*t) + 0.1*randn(size(t));    % + 50 Hz + ruido de banda ancha

% 1) NOTCH 50 Hz (IIR de 2.º orden)
w0 = 50/(fs/2);  [bn, an] = iirnotch(w0, w0/35);

% 2) LP FIR fc=40 Hz, fase lineal (ventana Hamming)
Wn = 40/(fs/2);  N = 100;  blp = fir1(N, Wn, hamming(N+1));

% 3) Respuesta en frecuencia del LP
[H,f] = freqz(blp, 1, 1024, fs);
figure; plot(f, 20*log10(abs(H))); grid on; xlabel('Hz'); ylabel('|H| dB');

% 4) Filtrado en cascada (filtfilt = fase cero para preservar P-QRS-T)
y = filtfilt(bn, an, x);          % quita 50 Hz
y = filtfilt(blp, 1, y);          % quita HF > 40 Hz

% 5) FFT antes/después
M = length(x);  fa = (0:M-1)*fs/M;
Xx = abs(fft(x))/M;  Yy = abs(fft(y))/M;
figure; plot(fa(1:M/2), Xx(1:M/2), fa(1:M/2), Yy(1:M/2)); legend('x','y'); xlabel('Hz');

% 6) Métricas
SNR_dB = 10*log10(sum(ref.^2)/sum((y-ref).^2));
RMSE   = sqrt(mean((y-ref).^2));
printf('SNR = %.2f dB | RMSE = %.4f\n', SNR_dB, RMSE);   % MATLAB: fprintf
```

---

<a id="8-agente-de-decision-ia"></a>
## 8. Agente de decisión IA — enfoque Octave/MATLAB

> Síntesis de `../_kb/05-agente-ia.md`, centrada en la implementación como **sistema experto de reglas IF-THEN en `.m`** (la estrategia idónea para esta entrega). Las otras cuatro estrategias se resumen y se remiten a `../entrega_python/APUNTES_PYTHON.md`.

### 8.1 Definición y variables E/S

Un **agente de decisión / sistema experto** mapea un conjunto de restricciones de ingeniería a una recomendación de diseño de filtro, emulando a un especialista en PDS. No diseña el filtro (eso es el Paso 2); **decide la familia (FIR/IIR) y la estructura** y **justifica** la elección:
$$
\text{Agente}: \mathbf{x}\in\mathcal{X} \longrightarrow \mathbf{y}\in\mathcal{Y}.
$$

**Entradas $\mathbf{x}$:**

| Variable | Símbolo | Tipo / rango | Origen |
|----------|---------|--------------|--------|
| Frecuencia de muestreo | `fs` | Hz (10…5000) | Paso 1 |
| Memoria del µC | `RAM`, `Flash` | kB (2…512) | plataforma |
| Cómputo disponible | `MHz`/`MIPS`, `FPU` | 16…240 MHz, con/sin FPU | plataforma |
| Fase lineal requerida | `fase_lineal` | booleano | Paso 1 |
| Ruido / SNR entrada | `SNR_in` | dB (0…40) | Paso 1 |
| Latencia admisible | `latencia` | {baja, media, alta} | aplicación |
| Pendiente de transición | `transicion` | {estrecha, amplia} | Paso 1 |
| Orden FIR estimado | `ordenFIR` | entero | §4.4 |

**Salidas $\mathbf{y}$:** recomendación `{FIR, IIR}`; estructura `{DF I, DF II, SOS, lattice}`; justificación (reglas activadas); confianza $[0,1]$ (opcional).

### 8.2 Sistema experto de reglas IF-THEN

Consta de **base de hechos** (las variables de entrada), **base de reglas** (`IF <condición> THEN <conclusión>`) y **motor de inferencia** (encadenamiento hacia adelante: de los hechos se disparan reglas hasta obtener la recomendación). **No hay entrenamiento**: se construye a mano por **elicitación de conocimiento experto** (la bibliografía y los criterios de §6), asignando a cada regla una **prioridad** y opcionalmente un **peso de confianza**.

**Tabla de reglas** (R1–R4 son las **reglas de referencia del enunciado**; R5–R7 las extienden):

| # | Prioridad | SI (condición) | ENTONCES | Confianza |
|---|-----------|----------------|----------|-----------|
| R1 | alta | `fase_lineal == sí` (estricta) | **FIR**, estructura DF | 0.95 |
| R2 | alta | `RAM < 2 kB` Y `ordenFIR > 50` | **IIR**, **SOS** | 0.90 |
| R3 | alta | estabilidad crítica Y sin FPU/float | **IIR** en **SOS** | 0.90 |
| R4 | media | `transicion == estrecha` Y cómputo suficiente | **IIR** (Elíptico, orden adecuado) | 0.85 |
| R5 | media | `latencia == baja` Y orden FIR alto inviable | **IIR** (menor retardo de grupo) | 0.70 |
| R6 | baja | FPU Y `transicion == amplia` Y fase lineal deseada | **FIR** (ventana/Parks-McClellan) | 0.80 |
| R7 | baja | ninguna anterior disparada | **FIR** por defecto | 0.50 |

**Motor de inferencia (pseudocódigo):** recorre las reglas ordenadas por prioridad; la **primera que dispara fija la familia/estructura/confianza**; acumula todas las reglas activadas para trazabilidad; si ninguna dispara, cae a R7 (red de seguridad → FIR, DF, 0.5).

### 8.3 Implementación en `.m` (struct de reglas + motor)

**Versión completa con motor genérico y trazabilidad** (agente embebible/portátil, sin dependencias de ML):

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
  % R4: transición estrecha + cómputo suficiente -> IIR (elíptico)
  if strcmp(h.transicion,'estrecha') && (h.FPU || h.MHz >= 80)
    fijar('R4','IIR','SOS',0.85);
  end
  % R5: latencia baja + FIR inviable -> IIR
  if strcmp(h.latencia,'baja') && h.ordenFIR > 64, fijar('R5','IIR','DFII',0.70); end
  % R6: FPU + transición amplia + fase lineal deseada -> FIR
  if h.FPU && strcmp(h.transicion,'amplia'),       fijar('R6','FIR','DF',0.80); end
  % R7: por defecto
  if isempty(rec), fijar('R7','FIR','DF',0.50); end
end
```

**Variante mínima compacta** (cadena `if/elseif`, devuelve recomendación + estructura + justificación textual):

```matlab
function rec = agente_filtro(in)
  % in: struct con fase_lineal(bool), ram_kB, mips, snr_in_dB, transicion
  rec.tipo = '';  rec.estructura = '';  rec.motivo = '';
  if in.fase_lineal                       % fase lineal estricta -> FIR
    rec.tipo = 'FIR';  rec.estructura = 'Direct-Form (DF) simétrico';
    rec.motivo = 'Fase lineal requerida (preserva morfología P-QRS-T del ECG).';
  elseif in.ram_kB < 2                    % RAM escasa -> IIR
    rec.tipo = 'IIR';  rec.estructura = 'SOS (biquads en cascada)';
    rec.motivo = 'RAM < 2 kB: FIR de orden alto inviable; IIR/SOS por estabilidad.';
  elseif strcmp(in.transicion,'estrecha') && in.mips > 50
    rec.tipo = 'IIR';  rec.estructura = 'SOS';
    rec.motivo = 'Transición exigente con cómputo suficiente -> IIR de orden adecuado.';
  else
    rec.tipo = 'FIR';  rec.estructura = 'Direct-Form';
    rec.motivo = 'Caso general sin restricción crítica.';
  end
end
% Llamada:
% r = agente_filtro(struct('fase_lineal',true,'ram_kB',8,'mips',80,'snr_in_dB',10,'transicion','amplia'));
```

### 8.4 Escenarios de validación (≥3)

Coherentes con §6 y con los Pasos 1–3.

| Escenario | Entrada clave | Salida esperada | Regla |
|-----------|---------------|-----------------|-------|
| **(a) ECG diagnóstico** | `fase_lineal = sí`, $f_s=500$, transición amplia, FPU (ESP32/STM32) | **FIR** / DF | R1 |
| **(b) Arduino UNO** | RAM 2 kB, `ordenFIR > 50`, sin FPU, fase no estricta | **IIR** / SOS | R2, R3 |
| **(c) Transición exigente** | `transicion = estrecha`, ESP32 con FPU ≥160 MHz, fase no requerida | **IIR (Elíptico)** / SOS | R4 |

- **(a):** la morfología clínica exige fase lineal exacta; FIR la garantiza por simetría de `h[n]` (R1); el cómputo con FPU absorbe el orden mayor.
- **(b):** FIR de orden > 50 es inviable con 2 kB; IIR logra la misma selectividad con orden bajo (R2); sin float ⇒ SOS por estabilidad numérica (R3); punto fijo Q15.
- **(c):** transición estrecha + cómputo suficiente ⇒ IIR de orden adecuado (R4); el elíptico da la pendiente más abrupta con menor orden; SOS asegura estabilidad.

> Llamada de ejemplo para (a): `[rec,est,reglas,conf] = agente_reglas(struct('fs',500,'RAM',320,'Flash',4096,'MHz',240,'FPU',true,'fase_lineal',true,'SNR_in',15,'latencia','media','transicion','amplia','ordenFIR',166));` → `rec='FIR'`, `est='DF'`, `reglas={'R1'}`, `conf=0.95`.

### 8.5 Las otras 4 estrategias (resumen) y remisión a Python

El enunciado pide **elegir y justificar una** estrategia. Para esta entrega se elige **reglas IF-THEN** (interpretable, determinista, ligera, embebible). Las otras cuatro se resumen y se detallan en la entrega Python:

| Estrategia | Cómo se "genera" | Datos | Determinismo | Idoneidad embebida | Implementación |
|-----------|------------------|-------|--------------|--------------------|----------------|
| **1. Reglas IF-THEN** | Elicitación manual de reglas | Ninguno | Total | **Excelente** | **Octave `.m` (esta entrega, §8.3)** |
| 2. Árbol de decisión | Entrenamiento `fit` (Gini/entropía) sobre dataset sintético | Dataset | Total (tras `fit`) | Buena (exporta a `if/else`) | Python — `sklearn` |
| 3. Lógica difusa | MF + reglas Mamdani (manual) | Ninguno | Total | Media (coste defuzz.) | Python — `scikit-fuzzy` |
| 4. API IA generativa | Prompt engineering + salida JSON validada | Ninguno | **No** | **Nula** (online) | Python — SDK `anthropic` |
| 5. Red neuronal MLP | Backpropagation (entropía cruzada) | Dataset (más) | Total (tras `fit`) | Baja | Python — `sklearn` MLP |

- **Árbol:** parte recursivamente el espacio por umbrales que minimizan la impureza; etiquetado sintético por las reglas de ingeniería; interpretable (`export_text`); riesgo de overfitting controlado con `max_depth`.
- **Fuzzy:** sustituye fronteras duras por grados de pertenencia $\mu\in[0,1]$; etapas fuzzificación → inferencia Mamdani → defuzzificación (centroide); aporta confianza continua.
- **LLM (Claude/GPT):** delega la decisión a un modelo de lenguaje vía API con *system prompt* (rol + criterios + JSON estricto) y validación de la salida; justificación rica pero no determinista, con latencia/coste y necesidad de conexión → útil en **fase de diseño**, no embebido.
- **MLP:** red de capas con backprop; para FIR/IIR (pocas variables, fronteras explicables) es **sobre-ingeniería** (caja negra, requiere más datos); se incluye por completitud.

> **Recomendación de cierre:** para entregar y embeber, **reglas IF-THEN** (Octave, §8.3); las variantes 2–5 enriquecen el documento Python. Detalle completo de cada una en `../entrega_python/APUNTES_PYTHON.md` y `../_kb/05-agente-ia.md`.

---

<a id="9-flujo-de-trabajo"></a>
## 9. Flujo de trabajo recomendado en Octave

Orden de pasos para resolver el examen (combina §3–§8):

1. **Cargar el entorno:** `if exist('OCTAVE_VERSION','builtin'); pkg load signal; end`.
2. **Paso 1 — Especificar** ($f_s$ justificado por Nyquist, §3.2): definir tipo (LP/HP/BP/notch), $f_p$, $f_r$, $R_p$, $A_s$, y si se exige fase lineal. Para ECG: $f_s=500$, notch 50 Hz + LP 40 Hz, fase lineal sí.
3. **Paso 4 — Consultar el agente** (`agente_reglas`/`agente_filtro`, §8.3) para decidir **FIR vs IIR** y la estructura según las restricciones de plataforma.
4. **Paso 2 — Diseñar:**
   - **FIR:** estimar orden (`kaiserord` o regla de ventana, §4.4), `b = fir1(N,Wn,window)` o `firpm` (equiripple); verificar simetría (fase lineal).
   - **IIR:** `[N,Wn] = buttord/cheb1ord/ellipord(...)`; `[z,p,k] = butter/cheby1/ellip(...)`; `sos = zp2sos(z,p,k)` (obligatorio si $N\ge3$); notch con `iirnotch`.
5. **Paso 3 — Analizar** (verificación de §4.7 / §5.7): `freqz` (magnitud dB + fase), `grpdelay` (retardo de grupo), `zplane` (polos-ceros / estabilidad), `impz` ($h[n]$).
6. **Filtrar:** tiempo real → `filter`/`sosfilt`; offline sin distorsión de fase → `filtfilt`.
7. **Espectro y métricas:** `fft`/`pwelch` antes vs después; SNR y RMSE (§7.7).
8. **Tabla comparativa FIR vs IIR** (orden, MACs/muestra, retardo, estabilidad, memoria, calidad — §6.1/§6.4).
9. **Paso 5 — Embebido:** elegir aritmética (§6.5: Q15 sin FPU / float32 con FPU), estructura SOS, buffer circular + timer-ISR; estimar presupuesto de ciclos (§6.6).

---

<a id="10-glosario-y-referencias"></a>
## 10. Glosario de símbolos y referencias

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
| $\varepsilon$ | Factor de ondulación $=\sqrt{10^{R_p/10}-1}$ | — |
| $N$ | Orden del filtro (o nº de puntos de la DFT) | — |
| $M$ | Longitud de $h[n]$ FIR ($M=N+1$ taps) | muestras |
| $h[n]$ | Respuesta al impulso | — |
| $H(z)$ | Función de transferencia (dominio Z) | — |
| $H_a(s)$ | Función de transferencia analógica (prototipo) | — |
| $H(e^{j\omega})$ | Respuesta en frecuencia | — |
| $\phi(\omega)$ | Fase de la respuesta en frecuencia | rad |
| $\tau_g(\omega)$ | Retardo de grupo $=-d\phi/d\omega$ | muestras |
| $\Delta f = f_s/N$ | Resolución frecuencial de la DFT | Hz/bin |
| $b_k, a_k$ | Coeficientes de numerador/denominador de $H(z)$ | — |
| $c_m, d_k$ | Ceros y polos de $H(z)$ | — |
| $\beta$ | Parámetro de la ventana de Kaiser | — |
| SOS | Cascada de secciones de 2.º orden (biquads) | — |
| MAC | Multiply-accumulate (operación por muestra) | — |
| Q$m.n$ | Formato de punto fijo ($m$ enteros, $n$ fraccionarios) | — |

### 10.2 Referencias (formato IEEE)

[1] A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*, 3rd ed. Upper Saddle River, NJ, USA: Pearson/Prentice Hall, 2010.

[2] J. G. Proakis and D. G. Manolakis, *Digital Signal Processing: Principles, Algorithms, and Applications*, 4th ed. Upper Saddle River, NJ, USA: Pearson Prentice Hall, 2007.

[3] S. K. Mitra, *Digital Signal Processing: A Computer-Based Approach*, 4th ed. New York, NY, USA: McGraw-Hill, 2011.

[4] T. W. Parks and C. S. Burrus, *Digital Filter Design*. New York, NY, USA: Wiley-Interscience, 1987.

[5] L. R. Rabiner and B. Gold, *Theory and Application of Digital Signal Processing*. Englewood Cliffs, NJ, USA: Prentice-Hall, 1975.

[6] J. F. Kaiser, "Nonrecursive digital filter design using the I0-sinh window function," in *Proc. IEEE Int. Symp. Circuits and Systems (ISCAS)*, San Francisco, CA, USA, 1974, pp. 20–23.

[7] J. W. Eaton, D. Bateman, S. Hauberg, and R. Wehbring, *GNU Octave Manual* (Octave Forge `signal` package documentation), version 8.x, 2024. [En línea]. Disponible: https://octave.org/doc/

[8] The MathWorks, Inc., *Signal Processing Toolbox User's Guide*, Natick, MA, USA, R2021b+. [En línea]. Disponible: https://www.mathworks.com/help/signal/

### 10.3 Ampliaciones (Knowledge Base)

- Contexto del examen, 5 pasos, anexos: `../_kb/00-enunciado.md`
- Fundamentos de PDS: `../_kb/01-fundamentos-pds.md`
- Diseño FIR: `../_kb/02-fir.md`
- Diseño IIR: `../_kb/03-iir.md`
- Criterios de diseño: `../_kb/04-criterios-diseno.md`
- Agente de decisión (5 estrategias): `../_kb/05-agente-ia.md`
- Herramientas Octave: `../_kb/06-octave.md`
- Entrega Python (variantes ML/fuzzy/LLM del agente): `../entrega_python/APUNTES_PYTHON.md`
