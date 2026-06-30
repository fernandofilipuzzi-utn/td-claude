# 04 · Criterios de diseño y selección de filtros digitales

> **Rol de este módulo:** el *porqué* de las decisiones. Mientras [[02-fir]] y [[03-iir]]
> desarrollan la **teoría** (cómo se calcula un FIR o un IIR), aquí se justifica **cuál
> elegir, con qué estructura, qué aritmética y sobre qué plataforma**, todo orientado a
> números y reglas accionables. Las tablas finales alimentan directamente a [[05-agente-ia]].

---

## 1. Tabla de decisión FIR vs IIR

La decisión raíz de todo el sistema. Para una **misma especificación**
($f_p$, $f_r$, $R_p$, $A_s$) los dos enfoques difieren radicalmente en coste y propiedades.

| Criterio | **FIR** | **IIR** | Gana |
|----------|---------|---------|------|
| **Estabilidad** | Siempre estable (sin polos, solo ceros) | Condicional: polos deben estar en $\|z\|<1$ | FIR |
| **Fase** | **Lineal exacta** si $h[n]$ es simétrica/antisimétrica | No lineal (salvo correcciones offline) | FIR |
| **Orden para igual $A_s$** | Alto ($N$ típico 50–300) | Bajo ($N$ típico 2–10) | IIR |
| **Coste (MACs/muestra)** | $\approx N+1$ | $\approx 5\cdot S$ (SOS, $S$ secciones) | IIR |
| **Memoria de coeficientes** | $N+1$ valores | $6\cdot S$ (b0,b1,b2,a1,a2 + escala) | IIR |
| **Sensibilidad a cuantización** | Baja (ceros tolerantes) | Alta (polos cerca de $\|z\|=1$ se desestabilizan) | FIR |
| **Latencia / retardo de grupo** | Constante $= N/2$ muestras (grande) | Variable, menor en promedio | IIR |
| **Facilidad de diseño** | Directo (ventanas, firpm); siempre converge | Requiere prototipo analógico + bilineal + prewarp | FIR |
| **Réplica de filtros analógicos** | Pobre | Excelente (Butter/Cheby/Elíptico) | IIR |

**Conclusión accionable:**

- **Gana FIR** cuando se exige **fase lineal estricta** (señales biomédicas con morfología:
  ECG P-QRS-T, EMG), cuando la **estabilidad numérica** es crítica o cuando hay
  cómputo/memoria de sobra (ESP32/STM32 con FPU).
- **Gana IIR** cuando los recursos son **escasos** (Arduino UNO, RAM < 2 kB), cuando se
  necesita una **transición muy abrupta con orden mínimo**, o cuando se replica un filtro
  analógico conocido y la fase no es crítica.

---

## 2. Criterios de elección de ventana (FIR)

La ventana fija el **piso de atenuación** $A_s$ alcanzable. Regla práctica: elegir la
ventana **más simple** cuya atenuación supere el $A_s$ requerido. El orden se estima por
el ancho de transición $\Delta\omega = 2\pi\,\Delta f / f_s$.

| Ventana | $A_s$ máx (dB) | Ancho lóbulo principal | $N$ aprox. para $\Delta f$ | Cuándo usarla |
|---------|---------------|------------------------|----------------------------|---------------|
| **Rectangular** | ~21 | $4\pi/N$ | $N\approx 0.9 f_s/\Delta f$ | Solo si $A_s\le 20$ dB |
| **Hann** | ~44 | $8\pi/N$ | $N\approx 3.1 f_s/\Delta f$ | Atenuación media, suave |
| **Hamming** | ~53 | $8\pi/N$ | $N\approx 3.3 f_s/\Delta f$ | **Defecto** biomédico (40–50 dB) |
| **Blackman** | ~74 | $12\pi/N$ | $N\approx 5.5 f_s/\Delta f$ | Alta atenuación, banda ancha |
| **Kaiser** | **ajustable** | $\propto \beta$ | fórmula de Kaiser (abajo) | Cuando $A_s$ no encaja en las fijas |

**Estimación de orden Kaiser** (la más usada por ser paramétrica):

$$
N \approx \frac{A_s - 7.95}{2.285\,\Delta\omega}, \qquad
\beta =
\begin{cases}
0.1102\,(A_s-8.7) & A_s>50 \\
0.5842\,(A_s-21)^{0.4}+0.07886\,(A_s-21) & 21\le A_s\le 50 \\
0 & A_s<21
\end{cases}
$$

**Cuándo Kaiser vs equiripple (Parks-McClellan / `firpm`):**

| Situación | Recomendación |
|-----------|---------------|
| $A_s$ no encaja en ventana fija; banda única | **Kaiser** (rápido, predecible) |
| Mínimo orden para una especificación dada | **Equiripple (firpm)** — reparte el error |
| Rizado de banda de paso y rechazo independientes | **Equiripple** (pesos $\delta_p,\delta_s$) |
| Multibanda / respuestas arbitrarias | **Equiripple** o `firls` |
| Diseño simple, sin toolbox de optimización | **Ventana** (Hamming/Kaiser) |

> Regla: *ventana fija* si su $A_s$ supera lo pedido por margen; *Kaiser* si hay que
> ajustar fino; *equiripple* si el coste (orden) debe ser mínimo. Detalle en [[02-fir]].

---

## 3. Criterios de elección de prototipo IIR

Trade-off central: **abruptez de transición** vs **calidad de fase** vs **rizado**.

| Prototipo | Banda paso | Banda rechazo | Fase / retardo grupo | Transición | Orden relativo |
|-----------|-----------|---------------|----------------------|------------|----------------|
| **Butterworth** | Plana (maximally flat) | Monótona | La más suave | Lenta | **Mayor** |
| **Chebyshev I** | Rizado $R_p$ | Monótona | Media (peor cerca de $f_p$) | Media-rápida | Medio |
| **Chebyshev II** | Plana | Rizado en rechazo | Media | Media-rápida | Medio |
| **Elíptico (Cauer)** | Rizado $R_p$ | Rizado $A_s$ | **La peor** (no lineal marcada) | **La más rápida** | **Mínimo** |

**Tabla de orden relativo** (misma especificación: $f_p$, $f_r$ cercanos, $A_s\approx 40$ dB):

| Prototipo | Orden $N$ típico | MACs (SOS) | Comentario |
|-----------|------------------|------------|------------|
| Butterworth | 8 | $5\cdot 4 = 20$ | Más secciones, fase limpia |
| Chebyshev I/II | 5 | $5\cdot 3 = 15$ | Compromiso |
| Elíptico | **4** | $5\cdot 2 = 10$ | Mínimo cómputo, fase fea |

**Conclusión:**

- **Butterworth** → cuando la **fase y la planitud** importan y sobra orden (PT100, EMA,
  ECG notch suave). Transición lenta es aceptable.
- **Chebyshev** → compromiso intermedio; Cheby II si molesta el rizado en banda de paso.
- **Elíptico** → cuando el **orden/cómputo debe ser mínimo** y la distorsión de fase no
  afecta la aplicación (filtrado de potencia, anti-aliasing duro).

Desarrollo de polos/ceros, bilineal y prewarping en [[03-iir]].

---

## 4. Estimación de coste computacional y de memoria

Fórmulas base por muestra de salida:

$$
\text{MACs}_{\text{FIR}} \approx N+1, \qquad
\text{Coef}_{\text{FIR}} = N+1
$$
$$
\text{MACs}_{\text{IIR (SOS)}} \approx 5\,S, \qquad
\text{Coef}_{\text{IIR}} = 6\,S \;\;(S=\lceil N/2\rceil \text{ secciones})
$$

**Memoria total** = coeficientes + **línea de retardo** (estados):

| Filtro | Coeficientes | Estados (delay line) | Total (float32) |
|--------|--------------|----------------------|-----------------|
| FIR orden $N$ | $N+1$ | $N+1$ (o $N$) | $\approx 8(N+1)$ bytes |
| IIR SOS, $S$ secciones | $6S$ | $2S$ (DF II transp.) | $\approx 4(8S)$ bytes |

### Ejemplo ECG (aplicación A): LP $f_c=40$ Hz, $f_s=500$ Hz, $A_s\approx 40$ dB

| Métrica | **FIR Hamming** | **IIR Butterworth** |
|---------|-----------------|---------------------|
| Orden $N$ | **~165** | **~6** |
| Secciones SOS | — | 3 |
| MACs/muestra | $166$ | $5\cdot 3 = 15$ |
| Coeficientes | $166$ | $18$ |
| Estados | $166$ | $6$ |
| Memoria float32 | $\approx 166\cdot 8 = 1.3$ kB | $\approx (18+6)\cdot 4 = 96$ B |
| Carga a $f_s=500$ Hz | $166\cdot 500 = 83$ kMAC/s | $15\cdot 500 = 7.5$ kMAC/s |

> **Lectura:** el IIR es **~11× más barato en cómputo** y **~14× en memoria**. Si la fase
> lineal no fuera obligatoria, el IIR ganaría holgadamente. Como en ECG **sí** importa
> preservar la morfología P-QRS-T, se acepta el coste del FIR — o se usa IIR con
> filtrado *forward-backward* (`filtfilt`) **offline** para anular la fase.

---

## 5. Punto fijo vs punto flotante

### 5.1 Formato Q (Qm.n)

Un número en **Q$m.n$** usa $m$ bits enteros (con signo) y $n$ bits fraccionarios sobre
un entero de $m+n+1$ bits. El valor real es $x_{\text{real}} = x_{\text{int}}\cdot 2^{-n}$.

| Formato | Bits | Rango | Resolución $2^{-n}$ | Uso típico |
|---------|------|-------|---------------------|-----------|
| Q1.14 | 16 | $[-2, 2)$ | $6.1\times10^{-5}$ | Coef. normalizados |
| Q1.15 | 16 | $[-1, 1)$ | $3.05\times10^{-5}$ | Muestras de audio/ADC |
| Q15.16 | 32 | $[-32768, 32768)$ | $1.5\times10^{-5}$ | Acumuladores |

### 5.2 Escalado de coeficientes y overflow

- Los coeficientes FIR/IIR suelen normalizarse a $[-1,1)$ → **Q15** o **Q14** (margen).
- El **acumulador** debe ser más ancho (p. ej. 32 o 64 bits) para sumar $N$ productos sin
  desbordar: un producto Q15×Q15 = Q30; sumar $N$ exige $\lceil\log_2 N\rceil$ bits de
  guarda extra.
- **Overflow:** prevenir con escalado de entrada o aritmética **saturante** (clamp) en vez
  de *wrap-around* (que produce discontinuidades catastróficas).
- **Underflow / ruido de cuantización:** redondear (no truncar) reduce el sesgo; el ruido
  de cuantización de coeficientes desplaza polos/ceros.

### 5.3 Ruido de cuantización

$$
\sigma_q^2 = \frac{\Delta^2}{12}, \qquad \Delta = 2^{-n}
$$

Dos fuentes: (a) **cuantización de coeficientes** (desplaza polos → puede **desestabilizar
un IIR**), y (b) **cuantización de productos/acumulador** (ruido aditivo a la salida).

### 5.4 Por qué SOS es preferible en punto fijo

En forma **directa de orden alto** los polos son extremadamente sensibles: un pequeño
error de coeficiente mueve mucho la raíz. Al **factorizar en secciones de 2.º orden (SOS)**
cada par de polos se cuantiza de forma aislada → la sensibilidad cae drásticamente y se
evita la inestabilidad. **Regla:** *IIR de orden > 2 en punto fijo ⇒ siempre SOS en cascada.*

### 5.5 Cuándo float32 es viable

| Plataforma | FPU | Float32 viable | Recomendación |
|------------|-----|----------------|---------------|
| Arduino UNO (AVR) | No | No (emulación ~100× lenta) | **Punto fijo Q15** |
| STM32F4/F7, ESP32 | **Sí (hardware)** | **Sí** | **Float32** directo |
| STM32 Cortex-M0/M3 | No | Marginal | Punto fijo |

> Con FPU hardware, float32 elimina el problema de escalado/overflow casi por completo y
> simplifica el diseño: úsese siempre que esté disponible.

---

## 6. Restricciones por plataforma

| Plataforma | Reloj | RAM | FPU | Aritmética | Filtro recomendado |
|------------|-------|-----|-----|------------|--------------------|
| **Arduino UNO** | 16 MHz | 2 kB | No | **Punto fijo Q15** | **IIR orden bajo (SOS)**; FIR solo $N\lesssim 20$ |
| **ESP32** | 160–240 MHz | 320 kB+ | **Sí** | **Float32** | **FIR orden alto** o IIR libre |
| **STM32F4** | 168 MHz | 128–192 kB | **Sí** | Float32 | FIR/IIR sin restricción práctica |

### Presupuesto de ciclos por muestra

A **$f_s = 500$ Hz** hay $T = 1/f_s = 2$ ms por muestra.

$$
\text{Ciclos disponibles} = f_{\text{clk}}\cdot T
$$

| Plataforma | $f_{\text{clk}}\cdot 2\text{ms}$ | MACs aprox. disponibles | ¿FIR $N=165$? ¿IIR SOS×3? |
|------------|----------------------------------|-------------------------|----------------------------|
| Arduino UNO | $16\text{M}\cdot 2\text{m} = 32\,000$ ciclos | ~hundreds (MAC fijo ~5–10 cic) | FIR **no** (∼165 MAC ok en cic. pero sin FPU + ADC + overhead → ajustado); **IIR sí** |
| ESP32 | $240\text{M}\cdot 2\text{m} = 480\,000$ | decenas de miles (FPU 1 cic/MAC) | **Ambos holgados** |
| STM32F4 | $168\text{M}\cdot 2\text{m} = 336\,000$ | ~330k | **Ambos holgados** |

> **Regla de presupuesto:** $\text{MACs}_{\text{filtro}}\cdot f_s \ll$ MAC/s disponibles,
> dejando margen (≥50%) para ADC, ISR, lógica de aplicación y jitter. En Arduino esto
> empuja casi siempre hacia **IIR de orden bajo en punto fijo**.

---

## 7. Criterios de muestreo y buffers en embebido

La adquisición determinista es tan importante como el filtro: un $f_s$ con jitter introduce
ruido equivalente a aliasing.

### 7.1 Estrategia de muestreo

| Método | Determinismo | CPU | Cuándo |
|--------|--------------|-----|--------|
| **Polling** (`analogRead` en `loop`) | Bajo (jitter alto) | Bloquea | Prototipos, $f_s$ baja no crítica |
| **Interrupción por timer** | **Alto** ($f_s$ exacto) | Eficiente | **Recomendado** para filtrado en tiempo real |
| **DMA** (ADC→buffer sin CPU) | **Máximo** | Mínima (CPU libre) | $f_s$ alta, STM32/ESP32, procesamiento por bloques |

### 7.2 Tipo de buffer

| Buffer | Latencia | Memoria | Uso |
|--------|----------|---------|-----|
| **Circular (ring)** | Baja, muestra a muestra | $N$ palabras | **Línea de retardo FIR/IIR** natural |
| **Lineal** | Media | bloque | Procesamiento por lotes simple |
| **Doble buffer (ping-pong)** | 1 bloque | $2\times$ bloque | DMA: llena uno mientras se procesa el otro |

### 7.3 Impacto en latencia

$$
t_{\text{lat}} \approx \underbrace{\frac{N/2}{f_s}}_{\text{retardo grupo FIR}} +
\underbrace{\frac{L_{\text{bloque}}}{f_s}}_{\text{buffering}} + t_{\text{cómputo}}
$$

- **FIR**: el grupo $N/2$ domina (ej.: $N=165$, $f_s=500 \Rightarrow 165$ ms — alto).
- **Procesamiento por bloques (DMA)**: añade $L_{\text{bloque}}/f_s$; bloque pequeño =
  menos latencia pero más overhead de ISR.
- **Tiempo real estricto** (control, audio): timer-ISR + buffer circular + IIR (bajo grupo).

---

## 8. Tabla resumen de criterios de decisión (entrada para [[05-agente-ia]])

Mapeo directo de restricciones → recomendación. El agente del Paso 4 puede implementar
esto como reglas **IF-THEN**, árbol de decisión o pesos difusos.

| Fase lineal | RAM | Cómputo (MIPS) | Ruido/SNR | Latencia | Pendiente transición | → **Recomendación** | Estructura |
|:-----------:|:---:|:--------------:|:---------:|:--------:|:--------------------:|---------------------|-----------|
| **Sí (estricta)** | alta | alto | cualquiera | tolerante | cualquiera | **FIR** | DF directa / lineal |
| Sí | baja (<2 kB) | bajo | medio | cualquiera | amplia | **IIR** + compensación o FIR corto | SOS |
| No | baja (<2 kB) | bajo | cualquiera | baja | estrecha | **IIR** | **SOS** (punto fijo) |
| No | alta | alto | cualquiera | cualquiera | estrecha | **IIR Elíptico/Cheby** | SOS |
| No | alta | alto | alto (mucho ruido) | tolerante | amplia | **FIR** orden alto | DF directa |
| No | media | medio | medio | baja | media | **IIR Butterworth** | SOS |
| Indiferente | crítica | crítico | — | — | — | **IIR orden mínimo** | SOS punto fijo |

**Reglas atómicas accionables** (las que el agente activa y reporta):

1. `fase_lineal == estricta` → **FIR** (regla dominante, gana sobre las demás).
2. `RAM < 2 kB AND orden_FIR > 50` → **IIR** (FIR no entra en memoria).
3. `estabilidad_numérica_crítica AND sin_FPU_float` → **SOS** (obligatorio).
4. `transición_estrecha AND cómputo_suficiente` → **IIR** de orden adecuado (Elíptico/Cheby).
5. `sin_FPU` → **punto fijo Q15**; `con_FPU` → **float32**.
6. `orden_IIR > 2` → **SOS en cascada** (nunca forma directa de orden alto).
7. `tiempo_real_estricto` → timer-ISR + buffer circular; `bloques/DMA` si $f_s$ alta.

---

## 9. Síntesis

| Si tu prioridad es… | Elige | Porque |
|---------------------|-------|--------|
| Preservar morfología (fase) | **FIR** | Única con fase lineal exacta |
| Mínimo cómputo/memoria | **IIR (SOS)** | Orden muy inferior para igual $A_s$ |
| Estabilidad garantizada | **FIR** | No tiene polos |
| Transición abruptísima | **IIR Elíptico** | Orden mínimo |
| Robustez en punto fijo | **FIR** o **IIR-SOS** | Baja sensibilidad de coeficientes |
| Microcontrolador sin FPU | **IIR-SOS Q15** | Cabe en RAM y ciclos |

> **Relación con el resto del KB:** la *teoría de cálculo* está en [[02-fir]] (ventanas,
> equiripple, $h[n]$) y [[03-iir]] (prototipos, bilineal, prewarping, polos-ceros). Este
> módulo aporta el **criterio de ingeniería**; las tablas de §8 son la base de conocimiento
> del **agente de decisión** descrito en [[05-agente-ia]].
