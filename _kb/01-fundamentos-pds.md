# 01 · Fundamentos de Procesamiento Digital de Señales (PDS)

> **Uso:** módulo de fundamentos transversales. Contexto del examen y los 5 pasos evaluables en [[00-enunciado]] (no se repite aquí). El diseño detallado de filtros se trata en [[02-fir]] (FIR) y [[03-iir]] (IIR); este documento aporta la base teórica que ambos asumen.

---

## 1. Señal analógica vs digital

Una **señal analógica** $x_a(t)$ es una función de variable continua en tiempo y en amplitud. Una **señal digital** $x[n]$ es discreta en ambos ejes: discreta en tiempo (índice entero $n$) y discreta en amplitud (cuantizada a un número finito de niveles). El paso de una a otra ocurre en dos etapas independientes:

1. **Muestreo** (discretización temporal): se toman valores de $x_a(t)$ en instantes equiespaciados $t = nT$.
2. **Cuantización** (discretización de amplitud): cada muestra se aproxima al nivel más cercano de una rejilla de $2^B$ valores ($B$ = bits del ADC).

### 1.1 Muestreo, periodo $T$ y frecuencia $f_s$

El muestreo ideal produce
$$
x[n] = x_a(nT), \qquad n \in \mathbb{Z},
$$
donde $T$ es el **periodo de muestreo** (s) y
$$
f_s = \frac{1}{T} \quad [\text{Hz}], \qquad \omega_s = 2\pi f_s \quad [\text{rad/s}].
$$

La **frecuencia digital** (normalizada) se define como
$$
\omega = \Omega T = \frac{2\pi f}{f_s} \quad [\text{rad/muestra}], \qquad \omega \in (-\pi, \pi],
$$
donde $\Omega = 2\pi f$ es la frecuencia angular analógica. El valor $\omega = \pi$ corresponde exactamente a $f = f_s/2$. Toda la teoría de filtros digitales se expresa en $\omega$, lo que la hace independiente de $f_s$.

### 1.2 Cuantización

Con $B$ bits y rango de entrada de pico a pico $V_{pp}$, el paso de cuantización (LSB) es
$$
\Delta = \frac{V_{pp}}{2^{B}}.
$$
Modelando el error de cuantización como ruido uniforme en $[-\Delta/2, \Delta/2]$, su potencia es $\sigma_q^2 = \Delta^2/12$, lo que da la cota clásica de relación señal-ruido de cuantización:
$$
\mathrm{SQNR}_{\max} \approx 6{,}02\,B + 1{,}76 \quad [\text{dB}].
$$
Cada bit añade $\approx 6$ dB. La cuantización introduce un piso de ruido irreducible y es una de las fuentes de error en la implementación embebida (ver [[00-enunciado]], Paso 5: punto fijo Q vs float).

---

## 2. Teorema de Nyquist-Shannon

### 2.1 Enunciado formal

> Si una señal $x_a(t)$ es de **banda limitada**, es decir su transformada de Fourier $X_a(f) = 0$ para $|f| \ge f_B$, entonces queda **completamente determinada** por sus muestras $x[n] = x_a(nT)$ tomadas a una tasa
> $$
> f_s > 2 f_B,
> $$
> y puede reconstruirse exactamente mediante interpolación con sinc:
> $$
> x_a(t) = \sum_{n=-\infty}^{\infty} x[n]\, \operatorname{sinc}\!\left(\frac{t - nT}{T}\right), \qquad \operatorname{sinc}(u) = \frac{\sin(\pi u)}{\pi u}.
> $$

La cantidad $2 f_B$ es la **tasa de Nyquist** (la mínima tasa de muestreo admisible). Su mitad,
$$
f_N = \frac{f_s}{2},
$$
es la **frecuencia de Nyquist**: la máxima frecuencia representable sin ambigüedad a una tasa $f_s$ dada.

### 2.2 Aliasing

Si $f_s \le 2 f_B$ (o si existen componentes por encima de $f_s/2$), las réplicas espectrales centradas en múltiplos de $f_s$ se solapan. Una componente de frecuencia real $f_0 > f_s/2$ aparece tras el muestreo como una frecuencia **aliada** (plegada hacia la banda base):
$$
f_{\text{alias}} = \left| f_0 - f_s \cdot \operatorname{round}\!\left(\frac{f_0}{f_s}\right) \right|.
$$
El aliasing es **irreversible** una vez muestreada la señal: no hay filtro digital posterior que separe el alias de la señal legítima que cayó en la misma frecuencia. Por eso se usa un **filtro anti-aliasing analógico** (paso bajo, antes del ADC) que atenúe todo lo que esté por encima de $f_s/2$.

### 2.3 Ejemplo numérico de aliasing

Sea $f_s = 500$ Hz (frecuencia de Nyquist $f_N = 250$ Hz). Supongamos una interferencia de **80 Hz** (legítima, dentro de banda) y un armónico parásito de **480 Hz**:

- 80 Hz $<$ 250 Hz → se representa correctamente como 80 Hz.
- 480 Hz $>$ 250 Hz → se pliega:
$$
f_{\text{alias}} = |480 - 500 \cdot \operatorname{round}(480/500)| = |480 - 500| = 20 \ \text{Hz}.
$$

El componente de 480 Hz **se disfraza de 20 Hz** y contamina la banda útil sin posibilidad de remoción digital. Conclusión práctica: si el hardware puede producir energía a 480 Hz, el filtro anti-aliasing analógico debe atenuarla antes del ADC.

### 2.4 Justificación de la elección de $f_s$ (caso canónico ECG)

En el caso A del enunciado (ECG, ver [[00-enunciado]]): banda útil **0.5–40 Hz**, interferencia de **red 50 Hz**, y se elige $f_s = 500$ Hz. Análisis de márgenes:

| Magnitud | Valor | Comentario |
|---|---|---|
| Banda útil $f_B$ | 40 Hz | Contenido diagnóstico del complejo P-QRS-T |
| Tasa de Nyquist mínima | $2 \times 40 = 80$ Hz | Cota teórica estricta |
| Interferencia de red | 50 Hz | Debe quedar representada sin alias para poder **filtrarla** (notch) |
| $f_s$ elegida | 500 Hz | $f_N = 250$ Hz |
| Factor de sobremuestreo | $500 / 80 \approx 6{,}25\times$ | Margen para roll-off del anti-aliasing y diseño de filtros |

El factor $\approx 6\times$ sobre Nyquist no es arbitrario: (i) deja banda de transición amplia al filtro anti-aliasing analógico (un filtro analógico de orden bajo no corta abruptamente en $f_B$); (ii) la red de 50 Hz queda muy por debajo de $f_N = 250$ Hz, así que se muestrea sin aliasing y luego se elimina con un **notch IIR** (ver [[03-iir]]); (iii) un $f_s$ holgado mejora la resolución temporal de eventos rápidos (QRS) y da margen para el paso bajo FIR de $f_c = 40$ Hz (ver [[02-fir]]).

---

## 3. Representaciones tiempo ↔ frecuencia

### 3.1 DTFT (Discrete-Time Fourier Transform)

Para una secuencia $x[n]$, la DTFT es función **continua y periódica** ($2\pi$) de $\omega$:
$$
X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n]\, e^{-j\omega n}, \qquad
x[n] = \frac{1}{2\pi}\int_{-\pi}^{\pi} X(e^{j\omega})\, e^{j\omega n}\, d\omega.
$$
Existe si $x[n]$ es absolutamente sumable. Es la herramienta teórica para la **respuesta en frecuencia** de un sistema (sección 5).

### 3.2 DFT y FFT

La **DFT** muestrea la DTFT en $N$ puntos equiespaciados del círculo, $\omega_k = 2\pi k/N$:
$$
X[k] = \sum_{n=0}^{N-1} x[n]\, e^{-j 2\pi k n / N}, \qquad k = 0, 1, \dots, N-1,
$$
$$
x[n] = \frac{1}{N}\sum_{k=0}^{N-1} X[k]\, e^{j 2\pi k n / N}.
$$
La **FFT** es un algoritmo de cómputo de la DFT en $O(N \log N)$ en lugar de $O(N^2)$; produce **exactamente** los mismos valores. Relación con la DTFT: $X[k] = X(e^{j\omega})\big|_{\omega = 2\pi k/N}$ (la DFT son muestras de la DTFT sobre el círculo unitario).

**Resolución frecuencial.** Con $N$ muestras a tasa $f_s$:
$$
\boxed{\;\Delta f = \frac{f_s}{N}\;} \quad [\text{Hz/bin}].
$$
El bin $k$ corresponde a la frecuencia física $f_k = k \cdot f_s / N$. Para distinguir dos tonos próximos se necesita $\Delta f$ menor que su separación → más muestras (ventana temporal más larga $N/f_s$). Ejemplo ECG: con $f_s = 500$ Hz y $N = 5000$ muestras (10 s de registro), $\Delta f = 0{,}1$ Hz — suficiente para resolver el pico de 50 Hz frente a la banda diagnóstica.

> **Nota de ventaneo:** al truncar a $N$ muestras se aplica implícitamente una ventana rectangular, que produce *fuga espectral* (leakage). Ventanas (Hann, Hamming, Blackman) reducen los lóbulos laterales a costa de ensanchar el lóbulo principal. El mismo concepto de ventana reaparece en el diseño FIR por ventaneo (ver [[02-fir]]), pero allí su rol es distinto (conformar $h[n]$, no analizar el espectro).

### 3.3 Transformada Z

Generaliza la DTFT a todo el plano complejo:
$$
X(z) = \sum_{n=-\infty}^{\infty} x[n]\, z^{-n}, \qquad z = r e^{j\omega} \in \mathbb{C}.
$$

**Región de convergencia (ROC):** conjunto de $z$ para los que la serie converge. La ROC es un anillo $r_1 < |z| < r_2$ y **no incluye polos**. Propiedades clave:

- Para una señal **causal**, la ROC es el exterior de un círculo ($|z| > r_{\max}$).
- Un sistema LTI causal es **estable (BIBO)** si y solo si su ROC **incluye el círculo unitario** $|z| = 1$, lo que equivale a que **todos los polos estén dentro** del círculo unitario. Este es el criterio de estabilidad central del diseño IIR (ver [[03-iir]]).

**Relación con la DTFT:** evaluando $X(z)$ sobre el círculo unitario ($r = 1$, $z = e^{j\omega}$) se recupera la DTFT,
$$
X(e^{j\omega}) = X(z)\big|_{z = e^{j\omega}},
$$
siempre que el círculo unitario pertenezca a la ROC.

### 3.4 Plano z y círculo unitario

El **círculo unitario** $|z| = 1$ es el eje de frecuencias del mundo discreto. Recorrerlo de $z = 1$ ($\omega = 0$, DC) a $z = -1$ ($\omega = \pi$, $f_s/2$) barre todas las frecuencias representables. La geometría polos/ceros respecto al círculo determina la respuesta en frecuencia: un **cero** cerca del círculo en $\omega_0$ crea una muesca (base del notch); un **polo** cerca del círculo crea un realce resonante. Estabilidad ⇔ polos en el interior. El mapa $z = e^{sT}$ vincula plano $s$ (analógico) y plano $z$ (digital) y es la base de la transformada bilineal usada en IIR (ver [[03-iir]]).

---

## 4. Convolución lineal y filtrado

Un sistema LTI queda completamente caracterizado por su **respuesta al impulso** $h[n]$ (su salida cuando la entrada es $\delta[n]$). La salida para cualquier entrada es la **convolución lineal**:
$$
y[n] = x[n] * h[n] = \sum_{k=-\infty}^{\infty} x[k]\, h[n-k].
$$
**Filtrar es convolucionar** la señal con la respuesta al impulso del filtro. Para un filtro **FIR** de longitud $M$, $h[n]$ tiene soporte finito y la suma es directa (ver [[02-fir]]). Para un filtro **IIR**, $h[n]$ es de longitud infinita y conviene la forma recursiva de **ecuación en diferencias** (ver [[03-iir]]):
$$
y[n] = \sum_{k=0}^{M} b_k\, x[n-k] - \sum_{k=1}^{N} a_k\, y[n-k].
$$

**En el dominio Z**, la convolución se vuelve producto:
$$
Y(z) = H(z)\, X(z), \qquad H(z) = \frac{Y(z)}{X(z)} = \frac{\sum_{k=0}^{M} b_k z^{-k}}{1 + \sum_{k=1}^{N} a_k z^{-k}}.
$$
$H(z)$ es la **función de transferencia**; sus raíces del numerador son los **ceros** y las del denominador, los **polos**. La **respuesta en frecuencia** se obtiene evaluando sobre el círculo unitario:
$$
H(e^{j\omega}) = H(z)\big|_{z = e^{j\omega}} = \big|H(e^{j\omega})\big|\, e^{j\phi(\omega)}.
$$

---

## 5. Magnitud, fase, fase lineal y retardo de grupo

### 5.1 Magnitud en dB

$$
|H(e^{j\omega})|_{\text{dB}} = 20 \log_{10} |H(e^{j\omega})|.
$$
La banda de paso ideal tiene $|H| \approx 1$ (0 dB) y la banda de rechazo $|H| \approx 0$ ($\to -\infty$ dB). Las especificaciones $R_p$ (rizado de banda de paso) y $A_s$ (atenuación de banda de rechazo) se expresan en dB (ver glosario y [[00-enunciado]] Paso 1).

### 5.2 Fase y fase lineal

La **fase** es $\phi(\omega) = \arg H(e^{j\omega})$. Un filtro tiene **fase lineal** si
$$
\phi(\omega) = -\alpha\,\omega \quad (+\,\beta),
$$
es decir, la fase es una recta en $\omega$. Esto equivale a un **retardo constante** de $\alpha$ muestras para **todas** las frecuencias.

**Por qué importa el retardo constante.** Si todas las componentes espectrales se retrasan lo mismo, la forma de onda se traslada en el tiempo **sin deformarse**. Si el retardo depende de la frecuencia (fase no lineal), unas componentes se atrasan más que otras y la **morfología se distorsiona**. En ECG esto es crítico: el diagnóstico depende de las amplitudes y tiempos relativos de las ondas **P-QRS-T**; un filtro de fase no lineal puede ensanchar el QRS o desplazar el segmento ST y producir lecturas erróneas. Por eso el enunciado exige el LP de 40 Hz como **FIR de fase lineal** (ver [[02-fir]]). Los FIR simétricos ($h[n] = \pm h[M-1-n]$) garantizan fase lineal exacta con retardo constante $\alpha = (M-1)/2$ muestras. Los IIR **no** tienen fase lineal en general (su ventaja es menor orden; ver [[03-iir]]); cuando la fase no es crítica (p. ej. un notch de 50 Hz fuera de la banda diagnóstica) el IIR es aceptable.

### 5.3 Retardo de grupo

El **retardo de grupo** mide cuánto se retrasa la envolvente de un grupo estrecho de frecuencias:
$$
\boxed{\;\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}\;} \quad [\text{muestras}].
$$
Interpretación:

- **Fase lineal** $\phi = -\alpha\omega$ ⇒ $\tau_g(\omega) = \alpha = \text{constante}$: todas las frecuencias se retrasan igual, sin distorsión de forma. Para un FIR simétrico de $M$ taps, $\tau_g = (M-1)/2$.
- **Fase no lineal** ⇒ $\tau_g(\omega)$ varía con $\omega$: las distintas bandas llegan desfasadas en el tiempo → distorsión morfológica. La **variación** de $\tau_g$ en la banda útil (no su valor absoluto) es la que cuantifica esa distorsión.

El retardo de grupo se grafica en el Paso 3 de simulación (ver [[00-enunciado]]) como criterio comparativo FIR vs IIR.

---

## 6. Densidad espectral de potencia (PSD)

La **PSD** $S_x(f)$ describe cómo se reparte la potencia de la señal a lo largo de la frecuencia (unidades: potencia/Hz). Para una señal aleatoria estacionaria es la transformada de Fourier de la autocorrelación $r_x[m]$ (teorema de Wiener-Khinchin):
$$
S_x(e^{j\omega}) = \sum_{m=-\infty}^{\infty} r_x[m]\, e^{-j\omega m}, \qquad r_x[m] = E\{x[n]\,x[n+m]\}.
$$
**Estimación práctica.** A partir de un registro finito se usa el **periodograma**, $\hat S_x[k] = \tfrac{1}{N}|X[k]|^2$, o el método de **Welch** (promedio de periodogramas de segmentos solapados y ventaneados), que reduce la varianza del estimador a costa de resolución.

**Espectro de una señal contaminada.** En la PSD de un ECG ruidoso típicamente se ven: (i) el lóbulo de banda diagnóstica 0.5–40 Hz; (ii) un **pico agudo en 50 Hz** (red eléctrica); (iii) un piso de ruido de banda ancha (ADC, EMG muscular). La PSD es la evidencia visual de qué filtrar y dónde: justifica el notch en 50 Hz y el corte en 40 Hz. Comparar PSD **antes vs después** del filtrado es la forma directa de mostrar la eficacia del filtro (Paso 3).

---

## 7. Métricas de calidad del filtrado

Se calculan a partir de tres señales alineadas en el tiempo: la **limpia** $s[n]$ (referencia/ground truth), la **ruidosa/contaminada** $x[n] = s[n] + r[n]$ y la **filtrada** $\hat s[n] = (x * h)[n]$.

### 7.1 SNR (relación señal-ruido)

$$
\boxed{\;\mathrm{SNR}_{\text{dB}} = 10 \log_{10} \frac{P_{\text{señal}}}{P_{\text{ruido}}} = 10 \log_{10} \frac{\sum_n s^2[n]}{\sum_n (\hat s[n] - s[n])^2}\;}
$$
La **mejora** del filtro se reporta como $\Delta\mathrm{SNR} = \mathrm{SNR}_{\text{salida}} - \mathrm{SNR}_{\text{entrada}}$, donde la SNR de entrada usa $(x[n]-s[n]) = r[n]$ en el denominador.

### 7.2 RMSE (error cuadrático medio raíz)

$$
\mathrm{RMSE} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1}\big(\hat s[n] - s[n]\big)^2}.
$$
Mide la desviación absoluta promedio respecto a la señal limpia (mismas unidades que la señal). Un buen filtro reduce el RMSE; conviene normalizarlo (NRMSE = RMSE / rango de $s$) para comparar entre señales.

### 7.3 Distorsión de fase

Cuantifica cuánto altera el filtro la **forma** de la señal más allá de un simple retardo. Dos enfoques habituales:

- **Variación del retardo de grupo** en la banda útil: $\max_\omega \tau_g(\omega) - \min_\omega \tau_g(\omega)$ (en muestras o ms). Cero ⇒ fase lineal perfecta.
- **Error tras compensar el retardo**: se desplaza $\hat s[n]$ por el retardo nominal y se mide el residuo (p. ej. RMSE residual o correlación cruzada máxima con $s[n]$). Un FIR de fase lineal deja residuo $\approx 0$; un IIR deja residuo no nulo por su retardo dependiente de frecuencia.

### 7.4 Ejemplo numérico de SNR

ECG limpio con potencia $P_{\text{señal}} = \sum_n s^2[n] = 1000$ (u. arb.). Antes de filtrar, el ruido de red + ADC aporta potencia $P_{r} = 250$:
$$
\mathrm{SNR}_{\text{in}} = 10\log_{10}\frac{1000}{250} = 10\log_{10} 4 = 6{,}02 \ \text{dB}.
$$
Tras aplicar el notch de 50 Hz + LP de 40 Hz, el ruido residual baja a $P_{e} = \sum_n(\hat s - s)^2 = 10$:
$$
\mathrm{SNR}_{\text{out}} = 10\log_{10}\frac{1000}{10} = 10\log_{10} 100 = 20 \ \text{dB}.
$$
$$
\Delta\mathrm{SNR} = 20 - 6{,}02 = 13{,}98 \approx \mathbf{14 \ dB} \ \text{de mejora}.
$$

---

## 8. Mini-glosario de símbolos

| Símbolo | Significado | Unidad |
|---|---|---|
| $f_s$ | Frecuencia de muestreo | Hz |
| $T = 1/f_s$ | Periodo de muestreo | s |
| $f_N = f_s/2$ | Frecuencia de Nyquist | Hz |
| $\omega = 2\pi f/f_s$ | Frecuencia digital normalizada | rad/muestra |
| $f_p$ | Frecuencia de borde de banda de paso (passband edge) | Hz |
| $f_r$ | Frecuencia de borde de banda de rechazo (stopband edge) | Hz |
| $\omega_c$ | Frecuencia de corte (normalizada) | rad/muestra |
| $R_p$ | Rizado máximo en banda de paso | dB |
| $A_s$ | Atenuación mínima en banda de rechazo | dB |
| $N$ | Orden del filtro (o nº de puntos de la DFT, según contexto) | — |
| $M$ | Longitud de la respuesta al impulso FIR ($M = N+1$ taps) | muestras |
| $h[n]$ | Respuesta al impulso | — |
| $H(z)$ | Función de transferencia (dominio Z) | — |
| $H(e^{j\omega})$ | Respuesta en frecuencia | — |
| $\phi(\omega)$ | Fase de la respuesta en frecuencia | rad |
| $\tau_g(\omega)$ | Retardo de grupo $-d\phi/d\omega$ | muestras |
| $\Delta f = f_s/N$ | Resolución frecuencial de la DFT | Hz/bin |
| $b_k, a_k$ | Coeficientes de numerador/denominador de $H(z)$ | — |

> **Convención:** $f_p$ y $f_r$ aquí usan la nomenclatura del enunciado (paso = *passband*, rechazo = *stopband*). En literatura anglosajona aparecen como $f_{\text{pass}}$ y $f_{\text{stop}}$. La traducción de estas especificaciones a coeficientes concretos se desarrolla en [[02-fir]] y [[03-iir]].

---

### Enlaces de módulos
- [[00-enunciado]] — contexto del examen, 5 pasos, anexos.
- [[02-fir]] — diseño FIR (ventanas, Parks-McClellan, fase lineal exacta).
- [[03-iir]] — diseño IIR (prototipos analógicos, transformada bilineal, estabilidad).
