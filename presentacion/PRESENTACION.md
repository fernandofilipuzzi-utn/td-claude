---
marp: true
title: Filtrado Digital FIR/IIR asistido por IA — ECG
paginate: true
---

# Filtrado Digital FIR/IIR asistido por IA
## Aplicación: Electrocardiograma (ECG)

**Técnicas Digitales III — PDS / Filtrado Digital (2026)**
Examen Parcial Integrador — Evaluación Basada en Problemas

- **Grupo:** _[Nombre del grupo]_
- **Integrantes:** _[Apellido, Nombre]_ · _[Apellido, Nombre]_ · _[Apellido, Nombre]_
- **Docente:** _[Nombre]_ — **Fecha:** _[dd/mm/2026]_

---

# Problema: el ECG real está contaminado

- El **ECG** registra la actividad eléctrica cardíaca; el diagnóstico depende del complejo **P-QRS-T** (amplitudes y tiempos relativos).
- Banda diagnóstica útil: **0.5 – 40 Hz**.
- Dos perturbaciones dominantes:
  - **Interferencia de red eléctrica a 50 Hz** (acoplamiento capacitivo) → pico espectral agudo.
  - **Ruido EMG** (actividad muscular) → contaminación de **banda ancha**.

[Figura: ECG limpio vs ECG contaminado con 50 Hz + EMG]

---

# Motivación: por qué importa la morfología

- Filtrar mal **deforma** las ondas y altera la interpretación clínica.
- Requisito crítico: **preservar la morfología** → se exige **fase lineal** en la banda útil (retardo constante, sin distorsión de forma).
- **Estrategia mixta** elegida (Anexo A):
  - **Notch IIR de 50 Hz** → barato, 1 biquad, elimina la red.
  - **Paso-bajos FIR $f_c = 40$ Hz** → fase lineal, preserva P-QRS-T.

> El agente de IA recomienda **FIR por fase lineal** para el LP principal.

---

# Cadena de procesamiento

$$
x[n]\;\rightarrow\;\boxed{\text{Notch IIR } 50\text{ Hz}}\;\rightarrow\;\boxed{\text{LP FIR } f_c=40\text{ Hz}}\;\rightarrow\;\hat s[n]
$$

- **Etapa 1 — Notch IIR (2.º orden):** rechaza la red de 50 Hz sin tocar la banda útil.
- **Etapa 2 — LP FIR fase lineal:** atenúa EMG y todo lo que supera 40 Hz, manteniendo retardo constante.

[Figura: diagrama de bloques de la cadena Notch IIR + LP FIR]

---

# Análisis de la señal y muestreo

- Banda útil $f_B = 40$ Hz → **Nyquist mínima** $2f_B = 80$ Hz.
- Se elige $f_s = 500$ Hz → **sobremuestreo $\approx 6{,}25\times$**:
  - Banda de transición amplia para el anti-aliasing analógico.
  - La red de 50 Hz queda muy por debajo de $f_N = 250$ Hz (se muestrea **sin alias** y se filtra con notch).
  - Mejor resolución temporal del QRS.

$$
\omega = \frac{2\pi f}{f_s}, \qquad f_N = \frac{f_s}{2} = 250\ \text{Hz}, \qquad f_{\text{alias}} = \left| f_0 - f_s\cdot\operatorname{round}\!\tfrac{f_0}{f_s}\right|
$$

---

# Especificaciones técnicas

| Símbolo | Significado | LP FIR | Notch / IIR |
|---|---|---|---|
| $f_s$ | Frecuencia de muestreo | 500 Hz | 500 Hz |
| $f_p$ | Borde de banda de paso | 40 Hz | — |
| $f_r$ | Borde de banda de rechazo | 50 Hz | $f_0=50$ Hz |
| $R_p$ | Rizado de paso | $\le 1$ dB | — |
| $A_s$ | Atenuación de rechazo | $\approx 53$ dB (Hamming) | — |
| Fase | — | **Lineal (exigida)** | No crítica |

> Para el ejemplo IIR comparativo se usa la máscara $f_p=40$, $f_r=60$, $R_p=1$ dB, $A_s=40$ dB.

---

# Tipo de filtro y decisión preliminar

- **Tipo:** paso-bajos (LP) para EMG + rechaza-banda (notch) para la red.
- **Fase lineal: SÍ** (diagnóstico). → favorece **FIR**.
- Plataforma objetivo **ESP32** (FPU, RAM abundante) → admite **FIR de orden alto en float32**.

$$
\mathrm{SNR_{dB}} = 10\log_{10}\frac{\sum_n s^2[n]}{\sum_n (\hat s[n]-s[n])^2}, \qquad
\mathrm{RMSE}=\sqrt{\tfrac1N\textstyle\sum_n(\hat s[n]-s[n])^2}
$$

Ejemplo: $\mathrm{SNR_{in}}\approx 6$ dB → $\mathrm{SNR_{out}}\approx 20$ dB ($\Delta\mathrm{SNR}\approx \mathbf{14}$ dB).

---

# Diseño FIR (1/4) — Fundamento

- FIR = respuesta al impulso **finita**; $N+1$ taps, **solo ceros**, **incondicionalmente estable**.
$$
y[n]=\sum_{k=0}^{N} h[k]\,x[n-k], \qquad H(z)=\sum_{k=0}^{N} h[k]\,z^{-k}
$$
- **Fase lineal** ⇔ coeficientes **simétricos** $h[n]=h[N-n]$ (Tipo I, $N$ par).
$$
H(e^{j\omega}) = e^{-j\omega N/2}A(\omega),\quad A(\omega)\in\mathbb{R}\;\Rightarrow\;\tau_g=\frac{N}{2}\ \text{(constante)}
$$

---

# Diseño FIR (2/4) — Método de ventanas

- Sinc ideal truncada y suavizada con ventana → reduce el **fenómeno de Gibbs**.
$$
h[n]=\underbrace{\frac{\sin\!\big(\omega_c(n-\tfrac N2)\big)}{\pi(n-\tfrac N2)}}_{\text{sinc ideal}}\cdot\underbrace{\Big(0{,}54-0{,}46\cos\tfrac{2\pi n}{N}\Big)}_{\text{Hamming}}
$$
- **Hamming** elegida: $A_s\approx 53$ dB (defecto biomédico, supera los 40–50 dB requeridos).
- Compromiso: atenuación de lóbulos laterales ↔ ancho de transición.

---

# Diseño FIR (3/4) — Orden y coeficientes (ECG)

- Transición $40\to50$ Hz ⇒ $\Delta f = 10$ Hz. Regla de Hamming:
$$
N \approx \frac{3{,}3\,f_s}{\Delta f}=\frac{3{,}3\times500}{10}=165\;\Rightarrow\; \boxed{N=166}\ \text{(par, Tipo I)},\ \ 167\ \text{coef.}
$$
- Corte de diseño centrado: $f_c' = 45$ Hz ⇒ $\omega_c = 0{,}18\pi$; pico central $h[83]\approx 0{,}18$.
- **Retardo de grupo:** $\tau_g = N/2 = 83$ muestras $= \mathbf{166\ ms}$, constante.
- Verificación cruzada Kaiser ($A_s=53$): $N\approx157$ (mismo orden de magnitud).

---

# Diseño FIR (4/4) — Respuesta y verificación

- $\sum_k h[k]=H(e^{j0})\approx 1$ (ganancia DC unitaria).
- Polos en $z=0$; ceros en **cuádruplas recíprocas conjugadas**.
- **Coste:** $\approx 167$ MACs/muestra $= 83{,}5$ kMAC/s a 500 Hz → viable en ESP32, **inviable en Arduino UNO** en punto fijo.

[Figura: respuesta en frecuencia FIR — magnitud dB + fase lineal]
[Figura: respuesta al impulso $h[n]$ simétrica y retardo de grupo plano]

---

# Diseño IIR (1/4) — Fundamento

- IIR = **recursivo**, $h[n]$ infinita; orden bajo pero **fase no lineal**.
$$
y[n]=\sum_{k=0}^{M} b_k\,x[n-k]-\sum_{k=1}^{N} a_k\,y[n-k], \qquad H(z)=\frac{B(z)}{A(z)}
$$
- Se parte de un **prototipo analógico** $H_a(s)$ y se aplica la **transformada bilineal**.
- **Estabilidad:** todos los polos dentro del círculo unitario, $|d_k|<1$.

---

# Diseño IIR (2/4) — Bilineal y prewarping

$$
s=\frac{2}{T}\cdot\frac{1-z^{-1}}{1+z^{-1}}, \qquad
\Omega_{\text{diseño}}=\frac{2}{T}\tan\!\Big(\frac{\omega_{\text{deseado}}}{2}\Big)
$$

- La bilineal mapea el semiplano izquierdo al interior del círculo → **prototipo estable ⇒ IIR estable**.
- El **warping** es no lineal → se **predistorsionan** las frecuencias críticas antes de diseñar.
- Ejemplo: $\Omega_p = 256{,}76$ rad/s ($\approx 40{,}86$ Hz), $\Omega_r = 395{,}93$ rad/s ($\approx 63{,}01$ Hz).

---

# Diseño IIR (3/4) — Orden y cambio de prototipo

Máscara $f_p=40$, $f_r=60$, $R_p=1$, $A_s=40$ dB. Butterworth:
$$
N\ge\frac{\log_{10}\!\frac{10^{A_s/10}-1}{10^{R_p/10}-1}}{2\log_{10}(\Omega_r/\Omega_p)}=\frac{4{,}5868}{0{,}3762}=12{,}19\;\Rightarrow\;\boxed{N=13}
$$

- $N=13$ es **altísimo** (transición exigente para Butterworth). Decisiones:
  - **Chebyshev I** → $N\approx 6$ · **Elíptico** → $N\approx 4$ (misma máscara).
  - Orden alto ⇒ **obligatorio SOS** (cascada de biquads).

---

# Diseño IIR (4/4) — SOS, notch y estabilidad

$$
H(z)=g\prod_i\frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}
$$

- **SOS:** cada par polo/cero se cuantiza por separado → baja sensibilidad (problema de Wilkinson).
- **Notch 50 Hz** ($\omega_0=0{,}2\pi$): ceros en el círculo, polos a radio $r\in[0{,}95;0{,}99]$.
$$
H_{\text{notch}}(z)=\frac{1-2\cos\omega_0\,z^{-1}+z^{-2}}{1-2r\cos\omega_0\,z^{-1}+r^2 z^{-2}}
$$

[Figura: respuesta en frecuencia IIR + diagrama polos-ceros (zplane)]

---

# Comparación FIR vs IIR (caso ECG)

| Métrica | **FIR (Hamming)** | **IIR (SOS)** |
|---|---|---|
| Orden $N$ | ~166 | 4–6 (Butterworth=13) |
| MACs/muestra | ~167 | ~10–15 ($5S$) |
| Fase | **Lineal exacta** | No lineal |
| Retardo de grupo | Constante $=83$ muestras (166 ms) | Variable, menor en promedio |
| Memoria (float32) | $\approx 1{,}3$ kB | $\approx 100$ B |
| Estabilidad | Siempre | Condicional ($|z|<1$) |

---

# Comparación FIR vs IIR — Conclusión

- **IIR** es ~11× más barato en cómputo y ~14× en memoria.
- **FIR** es el único con **fase lineal exacta** → preserva la morfología P-QRS-T.
- **Decisión:** en ECG se **acepta el coste del FIR** para el LP; el notch sí se hace **IIR** (barato y la fase no es crítica ahí).
- Offline se puede usar IIR con `filtfilt`/`sosfiltfilt` (fase cero).

[Figura: SNR/RMSE antes vs después + PSD con el pico de 50 Hz eliminado]

---

# Agente de IA — Variables y reglas

**Entradas:** `fs`, `RAM`, `MHz`/`FPU`, `fase_lineal`, `SNR_in`, `latencia`, `transicion`.
**Salidas:** familia `{FIR, IIR}` + estructura `{DF, SOS, ...}` + reglas activadas + confianza.

| # | SI | ENTONCES | Conf. |
|---|---|---|---|
| R1 | `fase_lineal == sí` | **FIR**, DF | 0.95 |
| R2 | `RAM<2 kB` Y `ordenFIR>50` | **IIR**, SOS | 0.90 |
| R3 | estabilidad crítica Y sin FPU | **IIR**, SOS | 0.90 |
| R4 | `transicion` estrecha Y cómputo OK | **IIR** (Elíptico) | 0.85 |

> Estrategia elegida: **reglas IF-THEN** (interpretable, determinista, embebible).

---

# Agente de IA — Motor y validación (3 escenarios)

```python
def agente_reglas(h):
    rec, est, reglas, conf = None, None, [], 0.0
    if h["fase_lineal"]:                       fijar("R1","FIR","DF",  0.95)
    if h["RAM"]<2 and h["ordenFIR"]>50:        fijar("R2","IIR","SOS", 0.90)
    if not h["FPU"] and h["ordenFIR"]>30:      fijar("R3","IIR","SOS", 0.90)
    if h["transicion"]=="estrecha" and h["FPU"]: fijar("R4","IIR","SOS",0.85)
    return rec or "FIR", est or "DF", reglas, conf
```

| Escenario | Entrada clave | Salida | Regla |
|---|---|---|---|
| (a) ECG diagnóstico | fase lineal, FPU, transición amplia | **FIR / DF** | R1 |
| (b) Arduino UNO | 2 kB RAM, FIR>50, sin FPU | **IIR / SOS (Q15)** | R2, R3 |
| (c) ESP32 transición exigente | transición estrecha, FPU ≥160 MHz | **IIR (Elíptico) / SOS** | R4 |

---

# Agente de IA — Otras estrategias (panorama)

| Estrategia | Generación | Datos | Embebible |
|---|---|---|---|
| **Reglas IF-THEN** (elegida) | Elicitación manual | No | **Excelente** |
| Árbol de decisión | `fit` (Gini/entropía) | Sí | Buena (→ if/else) |
| Lógica difusa | MF + Mamdani | No | Media |
| API LLM (Claude) | Prompt + JSON validado | No | Nula (online) |
| MLP | Backprop | Sí (más) | Baja |

> Las cuatro restantes se detallan en la entrega Python; el LLM es útil **en fase de diseño**, no en el micro.

---

# Implementación embebida — Plataforma ESP32

- **ESP32:** 160–240 MHz, RAM 320 kB+, **FPU por hardware** → **float32** directo.
- A $f_s=500$ Hz hay $T=2$ ms/muestra ⇒ $\approx 480\,000$ ciclos disponibles.
- Presupuesto: $\text{MACs}\cdot f_s \ll$ MAC/s, dejando $\ge 50\%$ de margen para ADC/ISR/jitter.
  - FIR 167 MACs → 83,5 kMAC/s · Notch IIR ~5 MACs → holgura amplia.

| Plataforma | FPU | Aritmética | Filtro recomendado |
|---|---|---|---|
| Arduino UNO | No | Q15 | IIR orden bajo (SOS) |
| **ESP32 / STM32F4** | **Sí** | **Float32** | **FIR alto** o IIR libre |

---

# Implementación embebida — Diagrama de bloques

$$
\text{ADC} \xrightarrow{\text{timer-ISR } f_s} \text{buffer circular} \rightarrow \boxed{\text{Notch IIR}} \rightarrow \boxed{\text{LP FIR}} \rightarrow \text{salida}
$$

- **Adquisición:** interrupción por **timer** (garantiza $f_s$ exacto) o DMA (máximo determinismo).
- **Buffer circular:** línea de retardo natural para la convolución FIR.
- **Latencia:** $t_{\text{lat}} \approx \frac{N/2}{f_s} + t_{\text{cómputo}}$ (en FIR domina el retardo de grupo).

[Figura: diagrama de bloques ESP32 — ADC → ISR → buffer → filtros → DAC/UART]

---

# Implementación embebida — Código (núcleo float32)

```c
// SOS biquad (Direct-Form II transpuesta) — Notch IIR 50 Hz
float biquad(float x, const float b[3], const float a[3], float z[2]) {
    float y = b[0]*x + z[0];
    z[0] = b[1]*x - a[1]*y + z[1];
    z[1] = b[2]*x - a[2]*y;
    return y;
}

// FIR LP fase lineal con buffer circular (167 taps)
float fir(float x, const float h[N], float buf[N], int *idx) {
    buf[*idx] = x; float acc = 0.0f; int k = *idx;
    for (int i = 0; i < N; i++) { acc += h[i]*buf[k]; k = (k? k-1 : N-1); }
    *idx = (*idx + 1) % N;
    return acc;
}
```

> En Arduino UNO (sin FPU) se usaría **Q15** con acumulador de 32 bits y aritmética saturante.

---

# Implementación embebida — Prueba y errores

- **Validación:** inyectar el ECG simulado, comparar la salida del µC contra la simulación (`scipy`/Octave) → SNR/RMSE coherentes (residuo $\approx 0$ tras compensar el retardo).
- **Fuentes de error:**
  - **Cuantización** del ADC ($\mathrm{SQNR}\approx 6{,}02B+1{,}76$ dB) y de coeficientes.
  - **Truncamiento/redondeo** en punto fijo (usar SOS si IIR > 2).
  - **Aliasing** si falla el anti-aliasing analógico.
  - **Latencia/jitter** del ISR.

[Figura: ECG filtrado en el ESP32 vs simulación de referencia]

---

# Conclusiones

- La cadena **Notch IIR 50 Hz + LP FIR 40 Hz** limpia el ECG preservando P-QRS-T.
- **FIR (Hamming, $N=166$)** elegido para el LP por **fase lineal exacta** ($\tau_g=166$ ms constante).
- **IIR** reservado al notch: mínimo coste y fase no crítica allí.
- El **agente de reglas IF-THEN** reproduce el criterio experto y es **embebible**.
- **ESP32 con float32** ejecuta ambas etapas con amplio margen de cómputo.

---

# Recomendaciones

- **Tiempo real (µC):** filtrado **causal** (`sosfilt` + FIR), asumir el retardo de grupo.
- **Análisis offline:** usar `filtfilt`/`sosfiltfilt` (**fase cero**) para no deformar.
- **Recursos escasos (Arduino):** IIR de orden bajo en **SOS Q15**; FIR solo si $N\lesssim 20$.
- **Transición muy abrupta:** IIR **Elíptico** (orden mínimo) si la fase no es crítica.
- Validar siempre el µC **contra la simulación** antes de desplegar.

---

# Referencias

- Enunciado: *Examen Parcial Integrador — Técnicas Digitales III — PDS / Filtrado Digital (2026)*.
- Apuntes de la entrega: `entrega_octave/APUNTES_OCTAVE.md`, `entrega_python/APUNTES_PYTHON.md`.
- Knowledge Base: `_kb/01-fundamentos-pds.md`, `02-fir.md`, `03-iir.md`, `04-criterios-diseno.md`, `05-agente-ia.md`.
- Oppenheim & Schafer, *Discrete-Time Signal Processing*. Proakis & Manolakis, *Digital Signal Processing*.
- Herramientas: Octave `signal`, Python `scipy.signal`, `scikit-learn`, `scikit-fuzzy`.
- Datasets: PhysioNet (MIT-BIH NSTDB `nstdb`, MIT-BIH Arrhythmia `mitdb`).

<!--
==========================================================================
CÓMO EXPORTAR ESTA PRESENTACIÓN (no ejecutar aquí; solo documentado)
==========================================================================

Marp (recomendado por el encabezado marp: true):
  # A PDF:
  marp PRESENTACION.md --pdf
  # A PPTX:
  marp PRESENTACION.md --pptx
  # A HTML:
  marp PRESENTACION.md --html
  (También con la extensión "Marp for VS Code": Export Slide Deck...)

Pandoc (alternativa, slides separadas por '---'):
  # A PPTX:
  pandoc PRESENTACION.md -o PRESENTACION.pptx
  # A PDF (vía Beamer/LaTeX; requiere una plantilla LaTeX instalada):
  pandoc -t beamer PRESENTACION.md -o PRESENTACION.pdf

Nota: para que las ecuaciones LaTeX rendericen, Marp usa MathJax/KaTeX por
defecto; con Pandoc a Beamer se renderizan vía LaTeX nativo.
==========================================================================
-->
