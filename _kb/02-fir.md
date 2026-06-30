# 02 · Filtros FIR — Diseño, fase lineal y métodos

> Módulo técnico de la serie de apuntes. Prerrequisitos: [[01-fundamentos-pds]] (Nyquist, transformada Z, respuesta en frecuencia).
> Implementación práctica: [[06-octave]] (`fir1`, `firpm`, `kaiserord`) y [[07-python]] (`scipy.signal.firwin`, `firwin2`, `remez`).
> Comparación FIR vs IIR y árbol de decisión: [[03-iir]] y [[04-criterios-diseno]].

---

## 1. Qué es un filtro FIR

Un filtro **FIR** (*Finite Impulse Response*, respuesta al impulso finita) es un sistema LTI discreto cuya respuesta al impulso $h[n]$ tiene un número **finito** de muestras no nulas. Si el filtro tiene **orden** $N$, entonces $h[n]$ tiene $N+1$ coeficientes ($n = 0,1,\dots,N$) y se anula fuera de ese intervalo.

### Ecuación en diferencias

La salida es una **convolución finita** de la entrada con los coeficientes:

$$
y[n] = \sum_{k=0}^{N} h[k]\, x[n-k]
$$

No hay términos recursivos (no aparece $y[n-k]$ del lado derecho): la salida solo depende de la entrada actual y de $N$ entradas pasadas. Por eso a los $h[k]$ se los llama también **coeficientes del filtro** o *taps*. El coste computacional es de $\approx N+1$ **MACs** (multiply-accumulate) por muestra.

### Función de transferencia $H(z)$ — solo ceros

Aplicando la transformada Z a la ecuación en diferencias:

$$
H(z) = \sum_{k=0}^{N} h[k]\, z^{-k} = h[0] + h[1]z^{-1} + h[2]z^{-2} + \cdots + h[N]z^{-N}
$$

Es un **polinomio en $z^{-1}$** (equivalentemente $H(z) = z^{-N}\sum_k h[k]z^{N-k}$, un polinomio de grado $N$ dividido por $z^N$). Sus consecuencias clave:

- **Solo tiene ceros** (todos los polos están en $z=0$, que no afectan la estabilidad).
- Es **incondicionalmente estable**: con entrada acotada la salida es acotada (BIBO), porque la suma de $|h[k]|$ es finita. No hay realimentación que pueda divergir.
- No puede ser inestable por cuantización de coeficientes (a diferencia del IIR, ver [[03-iir]]).

### Propiedades resumidas

| Propiedad | FIR |
|---|---|
| Memoria | $N+1$ coeficientes + buffer de $N$ muestras |
| Estabilidad | Siempre estable (sin polos fuera de $z=0$) |
| Fase lineal | Alcanzable exactamente por simetría de $h[n]$ |
| Orden típico | Alto (decenas a cientos) para transiciones estrechas |
| Coste | $\approx N+1$ MACs/muestra |

---

## 2. Fase lineal

La gran ventaja del FIR es que puede tener **fase exactamente lineal**, lo que implica **retardo de grupo constante**: todas las componentes de frecuencia se retardan el mismo número de muestras y la forma de onda no se distorsiona (crítico en ECG para preservar el complejo P-QRS-T, ver [[04-criterios-diseno]]).

### Condición de simetría

Un FIR tiene fase lineal si y solo si sus coeficientes son **simétricos** o **antisimétricos** respecto del centro:

$$
h[n] = \pm\, h[N-n], \qquad n = 0,1,\dots,N
$$

- Signo **$+$** → **simétrico** (fase lineal pura).
- Signo **$-$** → **antisimétrico** (fase lineal con desfase adicional de $90°$, $+\pi/2$).

### Demostración (caso simétrico)

Tomemos $h[n] = h[N-n]$. La respuesta en frecuencia es:

$$
H(e^{j\omega}) = \sum_{n=0}^{N} h[n]\, e^{-j\omega n}
$$

Factorizando el retardo central $\tau = N/2$ y agrupando los términos $n$ y $N-n$:

$$
H(e^{j\omega}) = e^{-j\omega N/2} \sum_{n=0}^{N} h[n]\, e^{-j\omega (n - N/2)}
= e^{-j\omega N/2}\, \underbrace{A(\omega)}_{\text{real}}
$$

Por la simetría, los términos exponenciales se combinan en **cosenos** (o senos en el caso antisimétrico), de modo que $A(\omega)$ es una función **puramente real** (la *amplitud con signo* o *zero-phase response*). Entonces:

$$
\angle H(e^{j\omega}) = -\,\omega\,\frac{N}{2} \;+\; \{0 \text{ ó } \pi\}
$$

La fase es **lineal en $\omega$** (la rama $\{0,\pi\}$ son saltos donde $A(\omega)$ cambia de signo). El **retardo de grupo** es constante:

$$
\tau_g(\omega) = -\frac{d\,\angle H(e^{j\omega})}{d\omega} = \frac{N}{2}\ \text{muestras}
$$

Es decir, **$N/2$ muestras** de retardo, independientes de la frecuencia. En segundos: $\tau_g = \dfrac{N}{2\,f_s}$.

### Los 4 tipos de FIR de fase lineal

Según la simetría y la **paridad de $N+1$** (número de coeficientes) se distinguen 4 tipos. Conviene recordar que con orden $N$, el centro de simetría está en $N/2$; si $N$ es par el centro cae sobre una muestra, si $N$ es impar cae entre dos.

| Tipo | Simetría | $N$ (orden) | N.º coef. $N+1$ | Centro | Restricciones de uso |
|------|----------|-------------|-----------------|--------|----------------------|
| **I** | Simétrico $h[n]=h[N-n]$ | **par** | impar | muestra entera | El más versátil: **LP, HP, BP, BR** todos posibles. |
| **II** | Simétrico | **impar** | par | medio entero | $H(e^{j\pi})=0$ → **no sirve para pasa-altos ni rechaza-banda** que necesiten ganancia en Nyquist. |
| **III** | Antisimétrico $h[n]=-h[N-n]$ | **par** | impar | muestra entera | $H(0)=0$ y $H(e^{j\pi})=0$ → solo **BP, derivadores, Hilbert**. No LP ni HP. |
| **IV** | Antisimétrico | **impar** | par | medio entero | $H(0)=0$ → **HP, derivadores, Hilbert**. No LP. |

**Por qué las restricciones:** la combinación de simetría/antisimetría y paridad obliga a ceros forzados en $\omega=0$ y/o $\omega=\pi$:

- Antisimétrico ($\pm$ con signo $-$) → siempre $H(0)=0$ (no puede pasar DC ⇒ inútil para pasa-bajos).
- N.º de coeficientes **par** con simetría (Tipo II) → fuerza un cero en $\omega=\pi$ (Nyquist) ⇒ inútil para pasa-altos.
- Tipo III tiene ceros forzados en **ambos** extremos ⇒ solo banda de paso intermedia (BP), derivadores y transformadores de Hilbert.

**Regla mnemotécnica para diseño:** para un **pasa-bajos** general use **Tipo I** (orden par, simétrico). Para un pasa-altos use Tipo I o IV (evitar el II). Los tipos III/IV se reservan para derivadores y Hilbert.

---

## 3. Método de ventanas

Es el método clásico y más intuitivo. La idea: partir de la respuesta al impulso **ideal** (infinita) del filtro deseado, **truncarla** a $N+1$ muestras y suavizar los bordes con una **ventana** $w[n]$.

### Respuesta ideal $h_d[n]$

Para un **pasa-bajos ideal** con frecuencia de corte $\omega_c = 2\pi f_c/f_s$, la respuesta al impulso es la **sinc**:

$$
h_d[n] = \frac{\sin\!\big(\omega_c (n-\tfrac{N}{2})\big)}{\pi\,(n-\tfrac{N}{2})}, \qquad
h_d\!\left[\tfrac{N}{2}\right] = \frac{\omega_c}{\pi}
$$

(centrada en $N/2$ para que sea causal y simétrica). Es **infinita y no causal** en su forma teórica; por eso se trunca. Respuestas ideales de otros tipos:

- **Pasa-altos:** $h_d[n] = \delta[n-\tfrac N2] - \dfrac{\sin(\omega_c(n-\frac N2))}{\pi(n-\frac N2)}$
- **Pasa-banda** $[\omega_1,\omega_2]$: $h_d[n] = \dfrac{\sin(\omega_2(n-\frac N2))-\sin(\omega_1(n-\frac N2))}{\pi(n-\frac N2)}$

### Truncamiento y enventanado

$$
h[n] = h_d[n]\cdot w[n], \qquad n=0,\dots,N
$$

Truncar de forma abrupta equivale a multiplicar por una **ventana rectangular**, lo que en frecuencia **convoluciona** $H_d(e^{j\omega})$ con la transformada de la ventana (un sinc de Dirichlet con grandes lóbulos laterales).

### Fenómeno de Gibbs

El truncamiento abrupto produce **ondulaciones (ripple)** que oscilan cerca de la discontinuidad (corte) y un **sobreimpulso fijo de ~9%** que **no desaparece** aunque aumente $N$ (solo se estrecha): es el **fenómeno de Gibbs**. Las ventanas suaves (Hann, Hamming, Blackman, Kaiser) reducen los lóbulos laterales a cambio de **ensanchar la banda de transición**. Es el compromiso fundamental: **atenuación de lóbulos laterales ↔ ancho de transición**.

### Tabla comparativa de ventanas

| Ventana | Ancho lóbulo principal (aprox.) | Atenuación lóbulo lateral (pico) | Atenuación mín. banda rechazo $A_s$ lograble | Ripple banda paso $\delta_p$ (aprox.) |
|---------|---------------------------------|----------------------------------|-----------------------------------------------|----------------------------------------|
| **Rectangular** | $4\pi/(N+1)$ | $-13$ dB | $\approx 21$ dB | $\sim 0{,}74$ dB |
| **Hann (Hanning)** | $8\pi/(N+1)$ | $-31$ dB | $\approx 44$ dB | $\sim 0{,}055$ dB |
| **Hamming** | $8\pi/(N+1)$ | $-41$ dB | $\approx 53$ dB | $\sim 0{,}019$ dB |
| **Blackman** | $12\pi/(N+1)$ | $-57$ dB | $\approx 74$ dB | $\sim 0{,}0017$ dB |
| **Kaiser** ($\beta$ ajustable) | depende de $\beta$ | ajustable | **$A_s$ a pedido** (paramétrica) | ajustable |

> Lectura: cuanto **más estrecho** el lóbulo principal (menor $N$ para una transición dada) **menor** atenuación de lóbulos laterales. La **Kaiser** es la única paramétrica: permite fijar exactamente $A_s$ y luego calcular $N$.

Definiciones de las ventanas ($0\le n\le N$, $M=N$):

$$
w_{\text{Hann}}[n] = 0{,}5 - 0{,}5\cos\!\frac{2\pi n}{M}, \quad
w_{\text{Hamming}}[n] = 0{,}54 - 0{,}46\cos\!\frac{2\pi n}{M}
$$
$$
w_{\text{Blackman}}[n] = 0{,}42 - 0{,}5\cos\!\frac{2\pi n}{M} + 0{,}08\cos\!\frac{4\pi n}{M}
$$

---

## 4. Fórmulas de orden

La banda de transición $\Delta f = f_r - f_p$ (Hz) determina el orden. En radianes normalizados:

$$
\Delta\omega = \frac{2\pi\,\Delta f}{f_s}
$$

### Reglas aproximadas por ventana

Para cada ventana fija existe una relación orden ↔ transición. Reglas prácticas (con $\Delta f$ y $f_s$ en Hz):

| Ventana | Estimación de orden $N$ | $A_s$ asociada |
|---------|--------------------------|----------------|
| Rectangular | $N \approx 0{,}9\,f_s/\Delta f$ | $\sim 21$ dB |
| Hann | $N \approx 3{,}1\,f_s/\Delta f$ | $\sim 44$ dB |
| **Hamming** | $N \approx 3{,}3\,f_s/\Delta f$ | $\sim 53$ dB |
| Blackman | $N \approx 5{,}5\,f_s/\Delta f$ | $\sim 74$ dB |

> Estas constantes provienen del ancho del lóbulo principal de cada ventana; conviene **redondear hacia arriba** y, en Tipo I, ajustar $N$ a **par**.

### Fórmula de Kaiser (paramétrica)

La ventana de Kaiser usa funciones de Bessel modificadas y un parámetro $\beta$ que se calcula a partir de la **atenuación deseada** $A = A_s$ (en dB):

$$
\beta =
\begin{cases}
0{,}1102\,(A - 8{,}7), & A > 50 \\[4pt]
0{,}5842\,(A-21)^{0{,}4} + 0{,}07886\,(A-21), & 21 \le A \le 50 \\[4pt]
0, & A < 21
\end{cases}
$$

Y el **orden** se estima con:

$$
\boxed{\,N \approx \frac{A - 8}{2{,}285\,\Delta\omega}\,}, \qquad \Delta\omega = \frac{2\pi\,\Delta f}{f_s}
$$

Ventaja clave: con Kaiser se **especifica $A_s$ y la transición** y la fórmula devuelve $N$ y $\beta$ directamente (en software, `kaiserord` en Octave / `kaiserord` en SciPy).

---

## 5. Ejemplo numérico canónico (ECG)

**Especificación** (aplicación A del enunciado, ver [[00-enunciado]] y [[04-criterios-diseno]]):

| Parámetro | Valor |
|-----------|-------|
| Tipo | Pasa-bajos FIR, fase lineal |
| Frecuencia de muestreo $f_s$ | $500$ Hz |
| Frecuencia de corte $f_c$ | $40$ Hz |
| Banda de transición | $40 \to 50$ Hz ⇒ $\Delta f = 10$ Hz |
| Ventana | Hamming ($A_s \approx 53$ dB) |

### Paso 1 — Orden por la regla de Hamming

$$
N \approx \frac{3{,}3\, f_s}{\Delta f} = \frac{3{,}3 \times 500}{10} = \frac{1650}{10} = 165
$$

Para **Tipo I** (simétrico, pasa-bajos) el orden debe ser **par** ⇒ se redondea a $N = 166$. El filtro tiene $N+1 = \mathbf{167}$ coeficientes.

> Verificación cruzada con Kaiser para $A_s=53$ dB: $\Delta\omega = 2\pi\cdot10/500 = 0{,}1257$ rad; $N\approx(53-8)/(2{,}285\cdot0{,}1257)\approx 157$. Mismo orden de magnitud (Hamming es algo más conservadora). Coherente.

### Paso 2 — Frecuencia de corte de diseño

Se centra el corte en medio de la transición: $f_c' = (40+50)/2 = 45$ Hz, de donde $\omega_c = 2\pi\cdot45/500 = 0{,}5655$ rad/muestra ($=0{,}18\pi$). En herramientas como `fir1`/`firwin` se pasa la frecuencia normalizada $f_c'/(f_s/2) = 45/250 = 0{,}18$.

### Paso 3 — Coeficientes $h[n]$

$$
h[n] = \underbrace{\frac{\sin\!\big(\omega_c(n-\tfrac{N}{2})\big)}{\pi\,(n-\tfrac{N}{2})}}_{\text{sinc ideal}} \cdot \underbrace{\Big(0{,}54 - 0{,}46\cos\tfrac{2\pi n}{N}\Big)}_{\text{ventana Hamming}}, \quad n=0,\dots,166
$$

- **Centro** $n = N/2 = 83$: coeficiente máximo $h[83] = \omega_c/\pi \approx 0{,}18$ (la sinc evaluada en 0).
- **Simetría:** $h[n] = h[166-n]$ ⇒ $h[0]=h[166]$, $h[1]=h[165]$, etc. (Tipo I, fase lineal exacta).
- **Forma conceptual de los coeficientes:**

```
   n:   0     1     2    ...    82    83    84   ...   164   165   166
 h[n]: ~0   pequeño  …          ↑   0.18   ↑          …   pequeño  ~0
              (lóbulos sinc atenuados por la cola de Hamming)
                    crecen hacia el centro, decrecen hacia los bordes
```

Los coeficientes de los **extremos** ($h[0]$, $h[166]$) son cercanos a cero (la ventana Hamming no llega a 0 pero la cola del sinc sí los hace pequeños); crecen suavemente, oscilando con el signo de la sinc, hasta el pico central $h[83]$, y decrecen simétricamente. La envolvente Hamming suprime el ripple de Gibbs.

### Paso 4 — Retardo de grupo

$$
\tau_g = \frac{N}{2} = \frac{166}{2} = 83\ \text{muestras}
$$

En tiempo:

$$
\tau_g = \frac{83}{f_s} = \frac{83}{500} = 0{,}166\ \text{s} = \mathbf{166\ ms}
$$

Constante para todas las frecuencias (no distorsiona la morfología P-QRS-T). Si 166 ms fuera excesivo para la aplicación, se reduciría $N$ (relajando la transición) o se pasaría a IIR aceptando fase no lineal (ver compromiso en [[04-criterios-diseno]]).

### Paso 5 — Coste

$\approx N+1 = 167$ MACs/muestra. A $f_s=500$ Hz son $\approx 83{,}5$ kMAC/s, perfectamente viable en ESP32/STM32 con FPU (ver restricciones de plataforma en [[00-enunciado]]); inviable en Arduino UNO en punto fijo.

---

## 6. Parks-McClellan / Remez (equiripple)

El método de ventanas reparte el error de forma **desigual** (mayor cerca del corte). El algoritmo **Parks-McClellan** (que usa el intercambio de **Remez**) diseña el FIR **óptimo en sentido minimax**: minimiza el **error máximo** (peor ripple) repartiéndolo **uniformemente** en cada banda → respuesta **equiripple**.

### Criterio minimax

Se minimiza el máximo del error ponderado entre la respuesta real y la deseada:

$$
\min_{h}\ \max_{\omega\in\text{bandas}}\ \big|\,W(\omega)\,[\,A(\omega) - D(\omega)\,]\,\big|
$$

donde $D(\omega)$ es la respuesta deseada (1 en banda de paso, 0 en banda de rechazo) y $W(\omega)$ una función de peso que permite asignar **distinto ripple** a banda de paso ($\delta_p$) y de rechazo ($\delta_s$).

### Teorema de alternancia

La solución óptima se caracteriza porque el error alcanza su valor máximo $\pm\delta$ con signos **alternados** en al menos $L+2$ frecuencias (siendo $L$ relacionado con $N/2$). Estos puntos de igual ripple alternante (*alternation theorem*) garantizan que la solución es única y óptima. El algoritmo de Remez itera ajustando esos extremos hasta converger.

### Estimación de orden (Kaiser / Bellanger para equiripple)

Una fórmula muy usada para estimar el orden de un FIR **equiripple** dadas las ondulaciones $\delta_p$ (paso) y $\delta_s$ (rechazo):

$$
N \approx \frac{-10\log_{10}(\delta_p\,\delta_s) - 13}{2{,}324\,\Delta\omega}, \qquad \Delta\omega = \frac{2\pi\,\Delta f}{f_s}
$$

(fórmula de **Kaiser** para equiripple; existe la variante de **Bellanger**
$N \approx \dfrac{2}{3}\log_{10}\!\big(\frac{1}{10\,\delta_p\,\delta_s}\big)\,\dfrac{f_s}{\Delta f}$). En software: `firpm`/`remez` (Octave) y `scipy.signal.remez` (ver [[06-octave]], [[07-python]]).

### Cuándo conviene equiripple vs ventanas

- **Equiripple (Parks-McClellan):** logra el **menor orden** para una especificación dada (ripple acotado en ambas bandas) → ideal cuando el cómputo o la memoria son críticos y se quiere exprimir el orden mínimo. Permite ripples **distintos** en paso y rechazo.
- **Ventanas (Hamming/Kaiser):** más simples, predecibles y robustas; útiles cuando no se necesita el óptimo absoluto o se quiere una fórmula directa. Kaiser ya da casi-óptimo con una sola fórmula.

---

## 7. Expresión de $H(z)$ y verificación

Con los coeficientes $h[0..N]$ obtenidos:

$$
H(z) = \sum_{k=0}^{N} h[k]\,z^{-k}
$$

Para el ejemplo ECG ($N=166$): $H(z) = h[0] + h[1]z^{-1} + \cdots + h[166]z^{-166}$, con $h[k]=h[166-k]$.

**Verificación de la respuesta (qué mirar en simulación, Paso 3 del [[00-enunciado]]):**

1. **Magnitud** $|H(e^{j\omega})|$ en dB: comprobar $f_c$, ripple en banda de paso $\le R_p$ y atenuación $\ge A_s$ en banda de rechazo.
2. **Fase / retardo de grupo:** confirmar fase lineal (recta) y $\tau_g = N/2$ constante.
3. **Diagrama de polos-ceros** (`zplane`): todos los polos en $z=0$; ceros sobre/cerca del círculo unitario (los del corte). En FIR de fase lineal los ceros aparecen en **cuádruplas recíprocas conjugadas** ($z_0$, $z_0^*$, $1/z_0$, $1/z_0^*$), firma de la simetría.
4. **Suma de coeficientes:** $\sum_k h[k] = H(e^{j0})$ ⇒ debe valer $\approx 1$ (ganancia unitaria en DC para un LP).
5. **Respuesta al impulso:** debe reproducir exactamente $h[n]$ (definición de FIR).

---

## 8. Criterios de elección (específicos de FIR)

Resumen breve; la comparación completa **FIR vs IIR** y el árbol de decisión están en [[04-criterios-diseno]] (y el contrapunto IIR en [[03-iir]]).

- **Ventana (Hamming/Hann/Blackman)** cuando: se quiere un diseño **simple y robusto**, la especificación de $A_s$ encaja con una ventana fija y la transición no es extremadamente exigente.
- **Kaiser** cuando: se necesita **especificar $A_s$ exacta** y obtener el orden mínimo por fórmula sin iterar; excelente compromiso general (es el "todoterreno" del método de ventanas).
- **Equiripple (Parks-McClellan)** cuando: el **orden mínimo** es prioritario (memoria/cómputo del µC ajustados, ver plataformas en [[00-enunciado]]), o se requieren **ripples distintos** en paso y rechazo.
- **FIR en general** cuando: la **fase lineal es obligatoria** (ECG, audio, datos), se necesita estabilidad garantizada o aritmética de coeficientes sin riesgo de inestabilidad.
- **Evitar FIR** cuando: la transición es muy estrecha con plataforma muy limitada (Arduino UNO) → el orden $N$ se dispara y conviene **IIR** (ver [[03-iir]] y la regla "RAM < 2 kB y orden FIR > 50 → IIR" del [[00-enunciado]]).

---

### Véase también
[[01-fundamentos-pds]] · [[03-iir]] · [[04-criterios-diseno]] · [[06-octave]] · [[07-python]]
