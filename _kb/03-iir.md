# 03 · Filtros IIR — prototipos analógicos, transformada bilineal y diseño

> **Módulo KB.** Diseño de filtros **IIR** (respuesta al impulso infinita) para el Paso 2 del examen.
> Prerrequisitos en [[01-fundamentos-pds]] (transformada Z, plano $z$, fase/retardo de grupo).
> Comparación de costes y elección de estructura/orden en [[04-criterios-diseno]].
> Implementación: `butter`/`cheby1`/`cheby2`/`ellip` en [[06-octave]] y [[07-python]].
> Contraparte de fase lineal: filtros FIR en [[02-fir]].

---

## 1. Qué es un filtro IIR

Un filtro **IIR** (*Infinite Impulse Response*) es un sistema LTI **recursivo**: la salida depende de las entradas **y** de salidas pasadas (realimentación). Su respuesta al impulso $h[n]$ tiene, en general, **duración infinita** (decae pero nunca se hace exactamente cero), de ahí el nombre.

### 1.1 Ecuación en diferencias

$$
\boxed{\;y[n] \;=\; \sum_{k=0}^{M} b_k\,x[n-k] \;-\; \sum_{k=1}^{N} a_k\,y[n-k]\;}
$$

Los coeficientes $b_k$ forman el numerador (parte **no recursiva**, ceros) y los $a_k$ con $k\ge 1$ la parte **recursiva** (polos). Por convención $a_0=1$ (la ecuación se normaliza dividiendo por $a_0$). El signo "$-$" del sumatorio recursivo proviene de pasar los términos $a_k\,y[n-k]$ al otro miembro:

$$
\sum_{k=0}^{N} a_k\,y[n-k] \;=\; \sum_{k=0}^{M} b_k\,x[n-k].
$$

### 1.2 Función de transferencia

Aplicando la transformada Z y usando la propiedad de desplazamiento $\mathcal{Z}\{x[n-k]\}=z^{-k}X(z)$:

$$
H(z)=\frac{Y(z)}{X(z)}
=\frac{B(z)}{A(z)}
=\frac{\displaystyle\sum_{k=0}^{M} b_k\,z^{-k}}{\displaystyle 1+\sum_{k=1}^{N} a_k\,z^{-k}}
=\frac{b_0+b_1 z^{-1}+\cdots+b_M z^{-M}}{1+a_1 z^{-1}+\cdots+a_N z^{-N}}.
$$

Multiplicando numerador y denominador por $z^{N}$ se obtiene la forma factorizada en **polos y ceros**:

$$
H(z)=b_0\,\frac{\displaystyle\prod_{m=1}^{M}\bigl(1-c_m z^{-1}\bigr)}{\displaystyle\prod_{k=1}^{N}\bigl(1-d_k z^{-1}\bigr)}
\;=\; K\,\frac{\prod_m (z-c_m)}{\prod_k (z-d_k)} \, z^{\,N-M}.
$$

- **Ceros** $c_m$: raíces de $B(z)$ (numerador). Anulan la salida en esas frecuencias → útiles para *notch*.
- **Polos** $d_k$: raíces de $A(z)$ (denominador). Producen resonancias/ganancia. **Su ubicación determina la estabilidad** (§7).

La presencia de polos (denominador no trivial) es lo que distingue al IIR del FIR: introduce **realimentación** y por tanto $h[n]$ infinita.

### 1.3 Comparación conceptual IIR vs FIR

| Aspecto | **IIR** | **FIR** |
|--------|---------|---------|
| Respuesta al impulso | Infinita ($h[n]$ recursiva) | Finita ($N+1$ muestras) |
| Polos | Sí (denominador $A(z)\ne 1$) | No (solo en $z=0$) → siempre estable |
| Realimentación | Sí | No |
| Orden para igual atenuación | **Bajo** (raíz analógica eficiente) | Alto (típ. 5–20× mayor) |
| Fase | **No lineal** (distorsiona la forma de onda) | Lineal exacta si $h[n]$ simétrica |
| Estabilidad | Debe verificarse ($|d_k|<1$) | Garantizada |
| Sensibilidad a cuantización | Alta (polos cerca de $|z|=1$) → usar SOS | Baja |
| Coste por muestra | $\approx 5\cdot(\text{secciones})$ MACs (SOS) | $\approx N+1$ MACs |

Detalle del trade-off de selección y del coste embebido en [[04-criterios-diseno]]. Fase lineal y retardo de grupo en [[01-fundamentos-pds]] y [[02-fir]].

---

## 2. Prototipos analógicos

El diseño IIR clásico parte de un **prototipo analógico** $H_a(s)$ bien conocido y lo lleva al dominio digital por **transformada bilineal** (§5). Los cuatro prototipos canónicos se diferencian por **dónde** colocan la ondulación (*ripple*) y por la pendiente de transición que logran a igual orden.

### 2.1 Los cuatro prototipos

- **Butterworth** — *máximamente plano* (*maximally flat*). Sin ondulación ni en banda pasante ni en rechazo; la magnitud decae monótonamente. Es el más "suave" pero el que **más orden** necesita para una transición dada. Módulo:
$$
|H_a(j\Omega)|^2=\frac{1}{1+\bigl(\Omega/\Omega_c\bigr)^{2N}}.
$$

- **Chebyshev tipo I** — *ripple equiondulado en la banda pasante*, monótono en la de rechazo. Transición más abrupta que Butterworth a igual $N$. Módulo con polinomio de Chebyshev $T_N$:
$$
|H_a(j\Omega)|^2=\frac{1}{1+\varepsilon^2\,T_N^2(\Omega/\Omega_p)}.
$$

- **Chebyshev tipo II** (inverso) — banda pasante **plana** (monótona), *ripple en la banda de rechazo*. Introduce **ceros finitos** sobre el eje $j\Omega$ (no tiene en Butterworth/Cheby I). Bueno cuando se exige una banda pasante limpia.

- **Elíptico / Cauer** — *ripple en ambas bandas*. Para una especificación dada alcanza el **orden mínimo** (transición más abrupta posible). El precio es la peor **distorsión de fase** y mayor sensibilidad numérica.

### 2.2 Tabla comparativa

| Prototipo | Ripple banda pasante | Ripple banda rechazo | Pendiente de transición | Fase / retardo grupo | Orden requerido | Ceros finitos |
|-----------|:-------------------:|:--------------------:|:----------------------:|:--------------------:|:---------------:|:-------------:|
| **Butterworth** | No (plano) | No (monótono) | Suave | La mejor (más suave) | **Máximo** | No |
| **Chebyshev I** | Sí ($R_p$) | No (monótono) | Media-alta | Media | Medio | No |
| **Chebyshev II** | No (plano) | Sí ($A_s$) | Media-alta | Media | Medio | Sí ($j\Omega$) |
| **Elíptico (Cauer)** | Sí ($R_p$) | Sí ($A_s$) | **La más abrupta** | La peor | **Mínimo** | Sí ($j\Omega$) |

### 2.3 Cuándo elegir cada uno

- **Butterworth** → cuando interesa **banda pasante limpia y fase lo más benigna posible**, y el orden no es crítico. Es la elección por defecto en biomédica de baja exigencia (ECG, PT100). El examen lo usa para el LP y el *notch* de ECG.
- **Chebyshev I** → cuando se admite **ondulación en la banda útil** a cambio de bajar el orden / afilar la transición. Útil con cómputo limitado.
- **Chebyshev II** → cuando la **banda pasante debe ser plana** pero se tolera ripple en rechazo; preferible a Cheby I si la señal vive en la banda pasante.
- **Elíptico** → cuando manda la **transición estrechísima con el mínimo de coeficientes** (µC con poca RAM) y la fase no es crítica. Es el de **menor orden** para una máscara dada.

> Regla mnemotécnica: *Butterworth paga con orden la suavidad; Elíptico paga con fase la eficiencia.* Selección formal en [[04-criterios-diseno]].

---

## 3. Cálculo del orden $N$

### 3.1 Parámetros de la especificación

- $R_p$ [dB] = ondulación máxima permitida en la **banda pasante** (atenuación en $\Omega_p$).
- $A_s$ [dB] = atenuación mínima exigida en la **banda de rechazo** (en $\Omega_r$).
- $\varepsilon$ = factor de ondulación, ligado a $R_p$:
$$
\varepsilon=\sqrt{10^{R_p/10}-1}.
$$
- $\Omega_p,\ \Omega_r$ = frecuencias angulares **analógicas** de borde de banda pasante y de rechazo (tras *prewarping*, §5.3).

### 3.2 Orden Butterworth

Imponiendo $|H_a(j\Omega_p)|^2 \ge 10^{-R_p/10}$ y $|H_a(j\Omega_r)|^2 \le 10^{-A_s/10}$ sobre la respuesta máximamente plana:

$$
\boxed{\;N \;\ge\; \frac{\log_{10}\!\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}{2\,\log_{10}\!\bigl(\Omega_r/\Omega_p\bigr)}\;}
$$

Se redondea **hacia arriba** ($N=\lceil N \rceil$). El numerador mide cuánta atenuación relativa se exige; el denominador, cuán ancha es la transición (relación $\Omega_r/\Omega_p$). Transiciones estrechas ($\Omega_r/\Omega_p\to 1$) disparan $N$.

### 3.3 Orden Chebyshev (I y II) y elíptico

Sustituyendo el comportamiento polinómico por el de Chebyshev, el orden usa el **coseno hiperbólico inverso**:

$$
\boxed{\;N \;\ge\; \frac{\cosh^{-1}\!\sqrt{\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}}{\cosh^{-1}\!\bigl(\Omega_r/\Omega_p\bigr)}\;}
\qquad
\cosh^{-1}(x)=\ln\!\bigl(x+\sqrt{x^2-1}\bigr).
$$

Como $\cosh^{-1}$ crece mucho más rápido que $\log_{10}$ frente al mismo argumento, el orden Chebyshev es **siempre menor o igual** que el Butterworth para idéntica máscara. El orden **elíptico** se obtiene con integrales elípticas completas $K(\cdot)$ (relación de Landen):

$$
N \ge \frac{K(k)\,K\!\bigl(\sqrt{1-k_1^2}\bigr)}{K\!\bigl(\sqrt{1-k^2}\bigr)\,K(k_1)},
\qquad
k=\frac{\Omega_p}{\Omega_r},\quad
k_1=\frac{\varepsilon}{\sqrt{10^{A_s/10}-1}},
$$

y resulta el **mínimo** de los cuatro. En la práctica se delega a `buttord`/`cheb1ord`/`cheb2ord`/`ellipord` (ver [[06-octave]], [[07-python]]), pero conviene mostrar el desarrollo a mano (§6).

---

## 4. $H_a(s)$ — función de transferencia analógica del prototipo

### 4.1 Forma general

$$
H_a(s)=\frac{N(s)}{D(s)}=H_0\,\frac{\prod_{m}\bigl(s-z_m\bigr)}{\prod_{k=1}^{N}\bigl(s-p_k\bigr)}.
$$

Butterworth y Chebyshev I son **todo-polos** ($N(s)=$ cte, sin ceros finitos); Chebyshev II y elíptico añaden **ceros sobre el eje $j\Omega$**.

### 4.2 Polos de Butterworth

El prototipo pasa-bajos Butterworth normalizado ($\Omega_c=1$) tiene sus $N$ polos **equiespaciados sobre una semicircunferencia de radio $\Omega_c$** en el semiplano izquierdo (los del derecho se descartan por estabilidad). Sus ángulos:

$$
p_k=\Omega_c\,\exp\!\left[\,j\,\frac{\pi\,(2k+N-1)}{2N}\,\right],\qquad k=1,2,\dots,N.
$$

Todos sobre $|p_k|=\Omega_c$, $\text{Re}\{p_k\}<0$. Para $N=2$:
$$
H_a(s)=\frac{\Omega_c^{2}}{s^{2}+\sqrt{2}\,\Omega_c\,s+\Omega_c^{2}},
$$
(el factor de amortiguamiento $\sqrt 2$ es la firma del Butterworth de 2º orden, usado en el *notch* y en aplicaciones como PT100 del enunciado). Para $N$ impar hay un polo real en $s=-\Omega_c$; el resto en pares conjugados.

### 4.3 Identificación de polos/ceros por prototipo

| Prototipo | Polos | Ceros finitos |
|-----------|-------|---------------|
| Butterworth | Círculo de radio $\Omega_c$, equiespaciados (SPI) | Ninguno |
| Chebyshev I | Sobre una **elipse** (eje mayor/menor según $\varepsilon$) | Ninguno |
| Chebyshev II | Recíprocos de Cheby I | Sobre el eje $j\Omega$ |
| Elíptico | Dentro de una elipse | Sobre el eje $j\Omega$ |

---

## 5. Transformada bilineal (TBL)

### 5.1 Mapeo $s \leftrightarrow z$

$$
\boxed{\;s=\frac{2}{T}\cdot\frac{1-z^{-1}}{1+z^{-1}}\;}
\qquad\Longleftrightarrow\qquad
z=\frac{1+(T/2)s}{1-(T/2)s},
$$

donde $T=1/f_s$. Sustituyendo esta $s$ en $H_a(s)$ se obtiene directamente $H(z)$ — un cociente de polinomios en $z^{-1}$, listo para la ecuación en diferencias.

### 5.2 Propiedad de mapeo

La TBL es una transformación conforme que mapea:

- el **semiplano izquierdo** del plano $s$ ($\text{Re}\{s\}<0$) → **interior del círculo unitario** del plano $z$ ($|z|<1$). Por eso **un prototipo analógico estable produce un IIR digital estable** (§7).
- el **eje $j\Omega$** completo ($-\infty<\Omega<\infty$) → **círculo unitario** $|z|=1$ una sola vez (relación uno-a-uno, sin *aliasing*, a diferencia de la transformada invariante al impulso).

### 5.3 *Warping* y *prewarping*

Evaluando en $s=j\Omega$ y $z=e^{j\omega}$:

$$
j\Omega=\frac{2}{T}\cdot\frac{1-e^{-j\omega}}{1+e^{-j\omega}}
=\frac{2}{T}\,j\tan\!\left(\frac{\omega}{2}\right)
\;\Longrightarrow\;
\boxed{\;\Omega=\frac{2}{T}\tan\!\left(\frac{\omega}{2}\right)\;}
$$

Esta relación **no es lineal**: comprime todo el eje $\Omega\in(0,\infty)$ dentro de $\omega\in(0,\pi)$. La distorsión se llama **warping** (alabeo de frecuencia). Para que las frecuencias críticas digitales caigan **exactamente** donde se quiere, se **predistorsiona** (*prewarping*) cada frecuencia analógica de diseño antes de calcular $H_a(s)$:

$$
\Omega_{\text{diseño}}=\frac{2}{T}\tan\!\left(\frac{\omega_{\text{deseado}}}{2}\right),
\qquad \omega_{\text{deseado}}=\frac{2\pi f}{f_s}.
$$

Tras la TBL, esa $\Omega$ vuelve a mapearse a $\omega_{\text{deseado}}$ con error nulo. **Conclusión práctica:** *prewarpear* $\Omega_p$ y $\Omega_r$, diseñar $H_a(s)$ con esos valores, aplicar la TBL.

### 5.4 Desarrollo algebraico $H_a(s)\to H(z)$ (un paso)

Tomemos un prototipo de **primer orden** $H_a(s)=\dfrac{\Omega_c}{s+\Omega_c}$ y apliquemos la TBL. Sustituyendo $s=\frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$:

$$
H(z)=\frac{\Omega_c}{\dfrac{2}{T}\dfrac{1-z^{-1}}{1+z^{-1}}+\Omega_c}.
$$

Multiplicando numerador y denominador por $(1+z^{-1})$:

$$
H(z)=\frac{\Omega_c\,(1+z^{-1})}{\dfrac{2}{T}\,(1-z^{-1})+\Omega_c\,(1+z^{-1})}.
$$

Definiendo $\alpha=\dfrac{2}{T}$ y agrupando potencias de $z^{-1}$:

$$
H(z)=\frac{\Omega_c\,(1+z^{-1})}{(\alpha+\Omega_c)+(\Omega_c-\alpha)\,z^{-1}}
=\underbrace{\frac{\Omega_c}{\alpha+\Omega_c}}_{b_0}\cdot
\frac{1+z^{-1}}{\,1+\dfrac{\Omega_c-\alpha}{\Omega_c+\alpha}\,z^{-1}}.
$$

Se lee directamente $b_0=b_1=\dfrac{\Omega_c}{\alpha+\Omega_c}$ y $a_1=\dfrac{\Omega_c-\alpha}{\Omega_c+\alpha}$, con $a_0=1$. La ecuación en diferencias queda

$$
y[n]=b_0\,x[n]+b_1\,x[n-1]-a_1\,y[n-1].
$$

Para órdenes altos se procede igual sección por sección (biquads, §8), evitando expandir el polinomio completo.

---

## 6. Ejemplo numérico canónico — IIR pasa-bajos Butterworth para ECG

**Aplicación A del enunciado** (ECG, $f_s=500$ Hz). Limitar la banda útil del ECG ($\sim$0.5–40 Hz) atenuando ruido EMG y de alta frecuencia.

### 6.1 Especificación

| Parámetro | Valor |
|-----------|-------|
| Frecuencia de muestreo $f_s$ | 500 Hz ($T=2\text{ ms}$) |
| Borde banda pasante $f_p$ | 40 Hz |
| Borde banda rechazo $f_r$ | 60 Hz |
| Ondulación pasante $R_p$ | 1 dB |
| Atenuación rechazo $A_s$ | 40 dB |
| Prototipo | Butterworth (LP) |

### 6.2 Paso 1 — frecuencias digitales normalizadas

$$
\omega_p=\frac{2\pi f_p}{f_s}=\frac{2\pi\cdot40}{500}=0{,}5027\text{ rad}=0{,}16\pi,
\qquad
\omega_r=\frac{2\pi\cdot60}{500}=0{,}7540\text{ rad}=0{,}24\pi.
$$

### 6.3 Paso 2 — *prewarping* (predistorsión)

$$
\Omega_p=\frac{2}{T}\tan\!\Big(\frac{\omega_p}{2}\Big)
=1000\cdot\tan(0{,}2513)=\mathbf{256{,}76\text{ rad/s}}\;(\approx 40{,}86\text{ Hz}),
$$
$$
\Omega_r=\frac{2}{T}\tan\!\Big(\frac{\omega_r}{2}\Big)
=1000\cdot\tan(0{,}3770)=\mathbf{395{,}93\text{ rad/s}}\;(\approx 63{,}01\text{ Hz}).
$$

(Con $2/T=2\cdot500=1000$.) Nótese cómo el *prewarping* desplaza ligeramente las frecuencias hacia arriba; sin él, los bordes caerían corridos respecto a 40/60 Hz.

### 6.4 Paso 3 — orden $N$ (Butterworth)

$$
10^{A_s/10}-1=10^{4}-1=9999,\qquad
10^{R_p/10}-1=10^{0{,}1}-1=0{,}2589.
$$
$$
\frac{9999}{0{,}2589}=38\,617,\qquad \log_{10}(38\,617)=4{,}5868.
$$
$$
\frac{\Omega_r}{\Omega_p}=\frac{395{,}93}{256{,}76}=1{,}5420,\qquad
\log_{10}(1{,}5420)=0{,}1881.
$$
$$
N\ge\frac{4{,}5868}{2\cdot0{,}1881}=\frac{4{,}5868}{0{,}3762}=12{,}19
\;\Longrightarrow\; \boxed{N=13}.
$$

> **Lectura de ingeniería.** Un $N=13$ es altísimo: la transición $40\!\to\!60$ Hz (relación $1{,}54$) con 40 dB es **muy exigente para Butterworth**. Esto motiva tres decisiones reales del examen:
> 1. **Relajar la máscara** (p. ej. $A_s=20$–$30$ dB, o ensanchar $f_r$), bajando $N$ a 4–6.
> 2. **Cambiar de prototipo**: con la fórmula $\cosh^{-1}$ (§3.3) y la **misma** máscara, **Chebyshev I** da $N\!\approx\!5{,}97\Rightarrow N=6$, y el **elíptico** $N\approx4$. Compromiso: ripple/fase (§2.3).
> 3. Si se mantiene $N$ alto, **es obligatorio realizar el filtro en cascada de biquards (SOS)** (§8); una forma directa de orden 13 es numéricamente inviable.

### 6.5 Paso 4 — frecuencia de corte y $H_a(s)$

Para que la banda pasante toque exactamente $R_p$ en $\Omega_p$ se fija
$$
\Omega_c=\frac{\Omega_p}{\varepsilon^{1/N}},\qquad \varepsilon=\sqrt{10^{0{,}1}-1}=0{,}5088,
$$
lo que sitúa $\Omega_c$ algo por encima de $\Omega_p$. Con $\Omega_c$ se ubican los 13 polos sobre el semicírculo de radio $\Omega_c$ en el SPI (§4.2) y se arma $H_a(s)$ como producto de secciones de 2º orden (más un polo real, por ser $N$ impar).

### 6.6 Paso 5 — TBL y $H(z)$

Aplicando $s=\frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$ a cada sección de $H_a(s)$ (como en §5.4, pero de 2º orden) se obtiene
$$
H(z)=\prod_{i} \frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}},
$$
un IIR pasa-bajos de orden 13 = cascada de 6 biquads + 1 sección de 1.er orden. La forma directa global tendría 14 coeficientes $b$ y 13 coeficientes $a$. La **ecuación en diferencias** de cada sección:
$$
y_i[n]=b_{0i}x_i[n]+b_{1i}x_i[n-1]+b_{2i}x_i[n-2]-a_{1i}y_i[n-1]-a_{2i}y_i[n-2],
$$
con la salida de una sección alimentando a la siguiente. Todos los polos $|d_k|<1$ ⇒ estable (la TBL lo garantiza si $H_a(s)$ es estable, §7).

> En Octave/Python esto es una línea: `butter(N, Wn)` con `Wn` prewarpeada internamente y salida en formato `'sos'`. Detalle de firmas en [[06-octave]] / [[07-python]].

### 6.7 *Notch* IIR de la red eléctrica (50 Hz)

El ECG arrastra interferencia de **red eléctrica** (50 Hz en Argentina/Europa; 60 Hz en otras regiones). El examen usa un **rechaza-banda (notch) IIR de orden 2** para eliminarla:

- Estructura: par de **ceros sobre el círculo unitario** exactamente en $\omega_0=2\pi f_0/f_s$ (con $f_0=50$ Hz, $f_s=500$ Hz $\Rightarrow \omega_0=0{,}2\pi$) y un par de **polos** justo dentro del círculo, en el mismo ángulo y radio $r\lesssim 1$:
$$
H_{\text{notch}}(z)=\frac{(1-e^{j\omega_0}z^{-1})(1-e^{-j\omega_0}z^{-1})}{(1-re^{j\omega_0}z^{-1})(1-re^{-j\omega_0}z^{-1})}
=\frac{1-2\cos\omega_0\,z^{-1}+z^{-2}}{1-2r\cos\omega_0\,z^{-1}+r^{2}z^{-2}}.
$$
- El radio $r$ (p. ej. $0{,}95$–$0{,}99$) fija el **ancho del *notch***: $r\to1$ ⇒ muesca estrechísima (menos distorsión de banda útil) pero transitorio más largo. Es un **Butterworth pasa-banda invertido de orden 2**, generable con `butter(2,[...],'stop')` o `iirnotch`.
- Coste mínimo (1 biquad, $\approx5$ MACs/muestra), de ahí que se prefiera IIR para el *notch* aun cuando el LP principal sea FIR de fase lineal (estrategia mixta del Anexo A).

---

## 7. Estabilidad

### 7.1 Criterio

Un IIR causal es **estable** (BIBO) si y solo si **todos los polos** $d_k$ (raíces de $A(z)$) están **estrictamente dentro del círculo unitario**:

$$
\boxed{\;|d_k|<1\quad\forall k\;}
$$

Equivale a que la región de convergencia incluya $|z|=1$ y a que $\sum_n |h[n]|<\infty$.

### 7.2 Cómo se verifica

1. **Raíces de $A(z)$**: calcular `roots(a)` y comprobar `max(abs(roots(a))) < 1`. Visualmente, `zplane` (todos los polos $\times$ dentro del círculo).
2. **Criterio de Jury** (algebraico, sin factorizar) sobre los coeficientes $a_k$ — útil en análisis simbólico.
3. **Margen práctico**: polos muy cerca de $|z|=1$ (filtros de banda estrecha, *notch* con $r\to1$) son estables *en teoría* pero frágiles ante **cuantización de coeficientes**; un pequeño error puede empujarlos fuera. Por eso, además de estabilidad, importa la **sensibilidad** (§8 y [[04-criterios-diseno]]).

### 7.3 Por qué FIR es siempre estable

Un FIR tiene $A(z)=1$: todos sus polos están en $z=0$ (origen), por tanto $|d_k|=0<1$ trivialmente. No hay realimentación → no puede divergir. Es la contrapartida de su mayor orden y coste (ver [[02-fir]]).

---

## 8. Estructuras de realización

Una misma $H(z)$ admite varias topologías de cómputo, equivalentes en aritmética exacta pero **muy distintas en punto fijo**.

### 8.1 Forma Directa I (DF-I)

Implementa literalmente la ecuación en diferencias: primero el FIR transversal de los $b_k$ (línea de retardo de la entrada), luego la realimentación de los $a_k$. Usa $M+N$ retardos. Robusta pero con más memoria.

### 8.2 Forma Directa II (DF-II) y traspuesta

Reordena para **compartir la línea de retardo** entre numerador y denominador → solo $\max(M,N)$ retardos (mínima memoria, "canónica"). La variante **traspuesta (DF-II-T)** invierte el grafo de señales; es la preferida en aritmética finita porque acumula menos error de redondeo y es la que usan por defecto `filter`/`lfilter`. Inconveniente: en orden alto, los nodos internos pueden **desbordar** (rango dinámico grande).

### 8.3 Cascada de secciones de 2.º orden (SOS / biquads)

Se factoriza $H(z)$ en producto de **biquads** (secciones de 2.º orden):

$$
H(z)=g\prod_{i=1}^{\lceil N/2\rceil}\frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}.
$$

**Por qué mejora la estabilidad numérica frente a la forma directa de orden alto:**

- La **cuantización de coeficientes** desplaza las raíces. En un polinomio de grado $N$ alto, las raíces son **extremadamente sensibles** a perturbaciones de los coeficientes (raíces agrupadas, problema de Wilkinson): un polo casi en $|z|=1$ puede salir del círculo y volver inestable el filtro.
- Al partir en biquads, **cada par de polos/ceros se cuantiza por separado** dentro de su sección de 2.º orden; el error de un coeficiente solo afecta a *esa* sección, no a todas las raíces a la vez. La sensibilidad cae drásticamente.
- Permite **escalar la ganancia** sección a sección para controlar el rango dinámico y evitar desbordes (importante en punto fijo Q del microcontrolador).
- El orden de las secciones y el emparejamiento polo–cero (*pole–zero pairing*) y el escalado se optimizan para minimizar ruido de cuantización.

Por todo esto, **el formato `sos` es el estándar para IIR de orden $\ge 3$** y la recomendación por defecto del agente cuando "estabilidad numérica crítica sin DSP float" (regla del enunciado, Paso 4). Coste $\approx 5$ MACs por biquad.

### 8.4 Lattice

Estructura en celosía parametrizada por **coeficientes de reflexión** $k_i$. Su atractivo: la estabilidad se verifica trivialmente ($|k_i|<1$) y tiene **baja sensibilidad a la cuantización**, por lo que se emplea en filtros adaptativos y en predicción lineal (voz). A cambio, más operaciones por muestra que la cascada SOS.

### 8.5 Enlace con punto fijo

La elección de estructura impacta de lleno en la **implementación embebida en aritmética Q (punto fijo)**: sensibilidad de coeficientes, ruido de cuantización, ciclos límite y desbordes. El análisis cuantitativo (cuándo SOS, cuándo float, MACs/muestra, RAM) está en **[[04-criterios-diseno]]** y se conecta con el Paso 5 (microcontrolador) del enunciado.

---

## 9. Resumen operativo

1. Especificar $f_s, f_p, f_r, R_p, A_s$ y tipo (LP/HP/BP/notch) → ver [[01-fundamentos-pds]].
2. Elegir prototipo (§2.3): Butterworth por defecto; Cheby/Elíptico si el orden o la transición aprietan.
3. *Prewarpear* $f_p, f_r$ → $\Omega_p,\Omega_r$ (§5.3).
4. Calcular orden $N$ con la fórmula del prototipo (§3) y redondear hacia arriba.
5. Armar $H_a(s)$ (polos en círculo/elipse, §4) y aplicar **TBL** → $H(z)$ (§5).
6. Verificar **estabilidad** $|d_k|<1$ (§7) y pasar a **SOS** si $N\ge3$ (§8).
7. Escribir la **ecuación en diferencias** por sección y validar en simulación → [[06-octave]] / [[07-python]].

> Funciones de apoyo (solo nombres; el detalle vive en 06/07): `butter`, `cheby1`, `cheby2`, `ellip`, y los `*ord` para el orden. **No** se incluye implementación aquí por alcance del módulo.
