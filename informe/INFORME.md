<!--
================================================================================
  Metadatos para pandoc (exportación a PDF formal).
  El PDF formal se genera con:
      pandoc INFORME.md -o INFORME.pdf --pdf-engine=xelatex --toc \
             -V mainfont="Arial" -V fontsize=11pt -V geometry:margin=2.5cm
  Descomentar/ajustar `mainfont`, `fontsize` y `geometry` según el motor LaTeX
  disponible. Las ecuaciones van en LaTeX y las tablas en Markdown extendido.
================================================================================
-->
---
title: "Sistema de Filtrado Digital FIR/IIR Asistido por IA para Señal de ECG"
subtitle: "Examen Parcial Integrador — Técnicas Digitales III (PDS / Filtrado Digital)"
author: "[Integrantes del grupo — completar]"
date: "2026"
lang: es
# fontfamily: arial          # (pandoc/LaTeX) Arial 11 pt — descomentar al exportar a PDF
# fontsize: 11pt
# geometry: margin=2.5cm     # márgenes 2,5 cm
# toc: true                  # índice navegable automático
# number-sections: true
---

<!-- ============================================================= -->
<!-- 1. CARÁTULA                                                   -->
<!-- ============================================================= -->

# 1. Carátula

<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**
**Facultad Regional [… completar …]**
**Carrera: Ingeniería Electrónica**

---

**Asignatura:** Técnicas Digitales III — Procesamiento Digital de Señales / Filtrado Digital (2026)

---

## Proyecto

### Diseño, simulación e implementación de un sistema de filtrado digital FIR/IIR asistido por IA
### Aplicación: Acondicionamiento de señal de electrocardiograma (ECG, $f_s = 500$ Hz)

---

**Modalidad:** Evaluación Basada en Problemas (EBP) — Trabajo grupal

| | |
|---|---|
| **Grupo N.º:** | `[…]` |
| **Integrante 1:** | `[Apellido, Nombre]` — Legajo `[…]` |
| **Integrante 2:** | `[Apellido, Nombre]` — Legajo `[…]` |
| **Integrante 3:** | `[Apellido, Nombre]` — Legajo `[…]` |
| **Integrante 4:** | `[Apellido, Nombre]` — Legajo `[…]` |
| **Docente / Cátedra:** | `[Nombre del docente]` |
| **Fecha de entrega:** | `[dd / mm / 2026]` |

</div>

---

<!-- ============================================================= -->
<!-- 2. RESUMEN EJECUTIVO                                          -->
<!-- ============================================================= -->

# 2. Resumen Ejecutivo

El presente informe documenta el diseño, la simulación y la implementación de un sistema de
filtrado digital destinado al acondicionamiento de una señal de electrocardiograma (ECG)
muestreada a una frecuencia de quinientos hertz. El problema de ingeniería abordado es la
contaminación característica de esta señal biomédica: la interferencia de la red eléctrica de
cincuenta hertz y el ruido electromiográfico de alta frecuencia, ambos superpuestos a la banda
diagnóstica útil comprendida aproximadamente entre medio hertz y cuarenta hertz, donde reside el
complejo P-QRS-T del que depende la interpretación clínica.

La solución propuesta es una cadena de filtrado mixta de dos etapas. La primera es un filtro
rechaza-banda (notch) de respuesta al impulso infinita de segundo orden, sintonizado en cincuenta
hertz, que suprime la interferencia de red con coste computacional mínimo. La segunda es un filtro
pasa-bajos de respuesta al impulso finita de fase lineal, diseñado por el método de ventanas con
ventana de Hamming y frecuencia de corte de cuarenta hertz, que elimina el ruido de alta frecuencia
preservando intacta la morfología de las ondas. La elección de un filtro de fase lineal para la
etapa principal es deliberada: garantiza un retardo constante para todas las frecuencias de la banda
útil, evitando la distorsión de forma de onda que comprometería el diagnóstico.

El proyecto incorpora además un agente de decisión asistido por inteligencia artificial que
recomienda la familia de filtro y la estructura de realización en función de las restricciones de
plataforma, y una propuesta de implementación embebida sobre microcontrolador. Los resultados clave
obtenidos son: una mejora de relación señal a ruido del orden de catorce decibelios (de seis a veinte
decibelios), un orden de ciento sesenta y seis para la etapa finita y de segundo orden para la etapa
notch, y la confirmación de que el prototipo Butterworth requeriría orden trece para cumplir la
máscara estricta, lo que motiva el uso de prototipos Chebyshev o elíptico cuando se opta por la
realización recursiva. El sistema resulta viable en plataformas con unidad de punto flotante.

<!-- Conteo aproximado: ~260 palabras, sin ecuaciones. -->

---

<!-- ============================================================= -->
<!-- 3. ÍNDICE                                                     -->
<!-- ============================================================= -->

# 3. Índice de contenidos

1. [Carátula](#1-carátula)
2. [Resumen Ejecutivo](#2-resumen-ejecutivo)
3. [Índice de contenidos](#3-índice-de-contenidos)
4. [Marco Teórico](#4-marco-teórico)
   - 4.1 [Fundamentos de filtros FIR](#41-fundamentos-de-filtros-fir)
   - 4.2 [Fundamentos de filtros IIR](#42-fundamentos-de-filtros-iir)
   - 4.3 [Métodos de diseño FIR: ventanas](#43-métodos-de-diseño-fir-el-método-de-ventanas)
   - 4.4 [Métodos de diseño IIR: prototipos y transformada bilineal](#44-métodos-de-diseño-iir-prototipos-analógicos-y-transformada-bilineal)
   - 4.5 [Fase lineal y retardo de grupo](#45-fase-lineal-y-retardo-de-grupo)
   - 4.6 [Fundamento del agente de decisión](#46-fundamento-del-agente-de-decisión)
5. [Análisis del Problema](#5-análisis-del-problema)
6. [Diseño de Filtros](#6-diseño-de-filtros)
   - 6.1 [Diseño del filtro FIR pasa-bajos](#61-diseño-del-filtro-fir-pasa-bajos-hamming)
   - 6.2 [Diseño del filtro IIR](#62-diseño-del-filtro-iir-butterworth-chebyshev-elíptico)
   - 6.3 [Diseño del notch IIR de red](#63-diseño-del-notch-iir-de-50-hz)
7. [Simulación en MATLAB/Octave](#7-simulación-en-matlaboctave)
8. [Agente de IA / Sistema Experto](#8-agente-de-ia--sistema-experto)
9. [Implementación Embebida](#9-implementación-embebida)
10. [Conclusiones](#10-conclusiones)
11. [Bibliografía](#11-bibliografía)
12. [Anexos](#12-anexos)

---

<!-- ============================================================= -->
<!-- 4. MARCO TEÓRICO                                              -->
<!-- ============================================================= -->

# 4. Marco Teórico

El filtrado digital consiste en procesar una señal discreta $x[n]$, obtenida por muestreo de una
señal analógica a tasa $f_s = 1/T$, mediante un sistema lineal e invariante en el tiempo (LTI)
caracterizado por su respuesta al impulso $h[n]$. Filtrar es convolucionar:

$$
y[n] = x[n] * h[n] = \sum_{k=-\infty}^{\infty} x[k]\,h[n-k],
$$

y en el dominio de la transformada $Z$ la convolución se vuelve un producto, $Y(z) = H(z)\,X(z)$,
donde $H(z)$ es la **función de transferencia**. Las raíces del numerador de $H(z)$ son los **ceros**
y las del denominador son los **polos**; su disposición en el plano $z$ determina la respuesta en
frecuencia $H(e^{j\omega})$ y la estabilidad del sistema. La frecuencia digital normalizada
$\omega = 2\pi f / f_s$ expresa toda la teoría de manera independiente de $f_s$, con $\omega = \pi$
correspondiente a la frecuencia de Nyquist $f_s/2$.

Según la naturaleza de su respuesta al impulso, los filtros digitales se dividen en dos grandes
familias: **FIR** (respuesta finita) e **IIR** (respuesta infinita). La elección entre ambas es la
decisión arquitectónica central de este proyecto.

## 4.1 Fundamentos de filtros FIR

Un filtro **FIR** (*Finite Impulse Response*) posee una respuesta al impulso de soporte **finito**:
de orden $N$, tiene $N+1$ coeficientes o *taps*. Su salida es una convolución finita sin
realimentación,

$$
y[n] = \sum_{k=0}^{N} h[k]\,x[n-k],
$$

y su función de transferencia es un **polinomio en $z^{-1}$**, es decir, contiene **solo ceros**:

$$
H(z) = \sum_{k=0}^{N} h[k]\,z^{-k} = h[0] + h[1]z^{-1} + \cdots + h[N]z^{-N}.
$$

Como todos sus polos se ubican en el origen ($z=0$), un FIR es **incondicionalmente estable** (BIBO):
no posee realimentación que pueda divergir y no puede desestabilizarse por la cuantización de sus
coeficientes. Su coste por muestra es de aproximadamente $N+1$ operaciones de multiplicación y
acumulación (MAC). La contrapartida de estas virtudes es que, para lograr una transición espectral
estrecha, el FIR requiere un **orden alto** (típicamente de cinco a veinte veces mayor que un IIR
equivalente).

La propiedad más valiosa del FIR es que puede alcanzar **fase lineal exacta** cuando sus coeficientes
son simétricos o antisimétricos, $h[n] = \pm\,h[N-n]$. Esta característica, desarrollada en §4.5, es
la razón por la cual se selecciona FIR para la etapa pasa-bajos del ECG.

## 4.2 Fundamentos de filtros IIR

Un filtro **IIR** (*Infinite Impulse Response*) es un sistema **recursivo**: su salida depende de las
entradas pasadas **y** de las salidas pasadas (realimentación), por lo que su respuesta al impulso
$h[n]$ tiene, en general, duración **infinita**. Su ecuación en diferencias es

$$
\boxed{\;y[n] = \sum_{k=0}^{M} b_k\,x[n-k] \;-\; \sum_{k=1}^{N} a_k\,y[n-k]\;}\qquad (a_0 = 1),
$$

y su función de transferencia es un cociente de polinomios:

$$
H(z) = \frac{B(z)}{A(z)} = \frac{b_0 + b_1 z^{-1} + \cdots + b_M z^{-M}}{1 + a_1 z^{-1} + \cdots + a_N z^{-N}}.
$$

Los coeficientes $b_k$ definen los **ceros** (parte no recursiva, útiles para anular frecuencias
concretas como en un notch) y los $a_k$ con $k \ge 1$ definen los **polos** (parte recursiva), cuya
ubicación determina la estabilidad. La presencia de polos no triviales es lo que distingue al IIR del
FIR e introduce la realimentación.

La ventaja decisiva del IIR es su **eficiencia**: hereda la elegancia de los prototipos analógicos
clásicos y logra una atenuación dada con un orden mucho **menor** (típicamente entre dos y diez). Sus
desventajas son la **fase no lineal** (distorsiona la forma de onda), la necesidad de **verificar la
estabilidad** ($|d_k| < 1$ para todos los polos) y su **alta sensibilidad a la cuantización** de
coeficientes, especialmente cuando los polos se acercan al círculo unitario. La siguiente tabla
sintetiza la comparación conceptual.

| Aspecto | **IIR** | **FIR** |
|---------|---------|---------|
| Respuesta al impulso $h[n]$ | Infinita (recursiva) | Finita ($N+1$ muestras) |
| Polos | Sí (denominador $A(z)\neq 1$) | No (solo en $z=0$) → siempre estable |
| Realimentación | Sí | No |
| Orden para igual atenuación | **Bajo** (2–10) | Alto (5–20× mayor) |
| Fase | **No lineal** (distorsiona la onda) | Lineal exacta si $h[n]$ es simétrica |
| Estabilidad | Debe verificarse ($\lvert d_k\rvert < 1$) | Garantizada |
| Sensibilidad a la cuantización | Alta (polos cerca de $\lvert z\rvert = 1$) → usar SOS | Baja |
| Coste por muestra | $\approx 5\cdot(\text{secciones})$ MAC (SOS) | $\approx N+1$ MAC |

## 4.3 Métodos de diseño FIR: el método de ventanas

El método de **ventanas** parte de la respuesta al impulso **ideal** (de soporte infinito), la
**trunca** a $N+1$ muestras y suaviza los bordes mediante una ventana $w[n]$, de modo que
$h[n] = h_d[n]\,w[n]$. Para un pasa-bajos ideal con corte $\omega_c = 2\pi f_c/f_s$, la respuesta
ideal es una función sinc:

$$
h_d[n] = \frac{\sin\!\bigl(\omega_c(n - \tfrac{N}{2})\bigr)}{\pi\,(n - \tfrac{N}{2})},
\qquad h_d\!\Bigl[\tfrac{N}{2}\Bigr] = \frac{\omega_c}{\pi}.
$$

El truncamiento abrupto (ventana rectangular) provoca el **fenómeno de Gibbs**: un sobreimpulso fijo
de aproximadamente nueve por ciento cerca del corte que **no desaparece** al aumentar $N$, sino que
solo se estrecha. Las ventanas suaves reducen los lóbulos laterales a costa de **ensanchar la banda
de transición**: este es el compromiso fundamental del método. La tabla siguiente resume las ventanas
clásicas.

| Ventana | Atenuación lóbulo lateral | $A_s$ lograble | Orden $N$ aproximado |
|---------|:-------------------------:|:--------------:|:--------------------:|
| Rectangular | $-13$ dB | $\approx 21$ dB | $0{,}9\,f_s/\Delta f$ |
| Hann | $-31$ dB | $\approx 44$ dB | $3{,}1\,f_s/\Delta f$ |
| **Hamming** | $-41$ dB | $\approx 53$ dB | $3{,}3\,f_s/\Delta f$ |
| Blackman | $-57$ dB | $\approx 74$ dB | $5{,}5\,f_s/\Delta f$ |
| Kaiser ($\beta$) | ajustable | $A_s$ a pedido | fórmula paramétrica |

La **ventana de Hamming**, definida por

$$
w_{\text{Hamming}}[n] = 0{,}54 - 0{,}46\cos\frac{2\pi n}{N},\qquad 0 \le n \le N,
$$

es la elección por defecto en aplicaciones biomédicas porque su atenuación de aproximadamente
cincuenta y tres decibelios supera con margen el requisito típico de cuarenta a cincuenta decibelios.
Como alternativa de orden mínimo existe el método **Parks-McClellan** (intercambio de Remez), que
diseña el FIR óptimo en sentido minimax (respuesta equiripple); se documenta como referencia pero no
se adopta para preservar la simplicidad y robustez del diseño.

## 4.4 Métodos de diseño IIR: prototipos analógicos y transformada bilineal

El diseño IIR clásico parte de un **prototipo analógico** $H_a(s)$ bien conocido y lo traslada al
dominio digital. Los cuatro prototipos canónicos se diferencian por dónde colocan la ondulación
(*ripple*) y por la pendiente de transición que logran a igual orden:

| Prototipo | Ripple paso | Ripple rechazo | Transición | Fase | Orden | Ceros finitos |
|-----------|:-----------:|:--------------:|:----------:|:----:|:-----:|:-------------:|
| **Butterworth** (máx. plano) | No | No | Suave | La mejor | **Máximo** | No |
| **Chebyshev I** | Sí ($R_p$) | No | Media-alta | Media | Medio | No |
| **Chebyshev II** | No | Sí ($A_s$) | Media-alta | Media | Medio | Sí ($j\Omega$) |
| **Elíptico (Cauer)** | Sí | Sí | **La más abrupta** | La peor | **Mínimo** | Sí ($j\Omega$) |

El módulo del prototipo Butterworth es máximamente plano,
$|H_a(j\Omega)|^2 = 1/[1 + (\Omega/\Omega_c)^{2N}]$, y sus $N$ polos se sitúan equiespaciados sobre
una semicircunferencia de radio $\Omega_c$ en el semiplano izquierdo. La regla mnemotécnica que
resume el compromiso es: *Butterworth paga con orden la suavidad; el elíptico paga con fase la
eficiencia*.

El traslado del prototipo analógico al dominio digital se realiza mediante la **transformada
bilineal** (TBL):

$$
\boxed{\;s = \frac{2}{T}\cdot\frac{1 - z^{-1}}{1 + z^{-1}}\;},\qquad T = \frac{1}{f_s}.
$$

La TBL es una transformación conforme que mapea el semiplano izquierdo del plano $s$ al **interior
del círculo unitario** del plano $z$ —por lo que un prototipo analógico estable produce siempre un
IIR digital estable— y mapea el eje $j\Omega$ completo sobre el círculo unitario **una sola vez**, sin
aliasing. Su única peculiaridad es la **distorsión de frecuencia** o *warping*, consecuencia de la
relación no lineal

$$
\boxed{\;\Omega = \frac{2}{T}\tan\!\Bigl(\frac{\omega}{2}\Bigr)\;}.
$$

Para que las frecuencias críticas digitales caigan **exactamente** donde se desea, se predistorsiona
(*prewarping*) cada frecuencia analógica de diseño antes de calcular $H_a(s)$:

$$
\Omega_{\text{diseño}} = \frac{2}{T}\tan\!\Bigl(\frac{\omega_{\text{deseado}}}{2}\Bigr),
\qquad \omega_{\text{deseado}} = \frac{2\pi f}{f_s}.
$$

Tras la TBL, esa frecuencia analógica vuelve a mapearse sobre $\omega_{\text{deseado}}$ con error
nulo. El procedimiento completo es, por tanto: prewarpear $\Omega_p$ y $\Omega_r$, diseñar $H_a(s)$
con esos valores, aplicar la TBL y verificar la estabilidad.

## 4.5 Fase lineal y retardo de grupo

Un filtro tiene **fase lineal** si $\phi(\omega) = -\alpha\,\omega\ (+\beta)$, es decir, si su fase es
una recta en $\omega$. Esto equivale a un **retardo constante** de $\alpha$ muestras para todas las
frecuencias: si todas las componentes espectrales se retrasan lo mismo, la forma de onda se traslada
**sin deformarse**. Con fase no lineal, unas componentes se atrasan más que otras y la morfología se
distorsiona. El **retardo de grupo** cuantifica este efecto:

$$
\boxed{\;\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}\;}\quad[\text{muestras}].
$$

Para un FIR simétrico de orden $N$, el retardo de grupo es constante, $\tau_g = N/2$ muestras, lo que
garantiza una distorsión de forma nula. Los filtros IIR, en cambio, presentan un $\tau_g(\omega)$
variable. En el contexto del ECG esta distinción es crítica: el diagnóstico depende de las amplitudes
y los tiempos relativos de las ondas P, Q, R, S y T, de modo que cualquier distorsión de fase
desplazaría unas ondas respecto de otras y falsearía la interpretación. **Esta es la justificación
central por la cual el agente recomienda FIR para la etapa pasa-bajos**: solo un FIR de fase lineal
preserva fielmente el complejo P-QRS-T.

## 4.6 Fundamento del agente de decisión

Un **agente de decisión** o **sistema experto** mapea un conjunto de restricciones de ingeniería a
una recomendación de diseño, emulando el razonamiento de un especialista en PDS. Formalmente,
$\text{Agente}: \mathbf{x} \in \mathcal{X} \rightarrow \mathbf{y} \in \mathcal{Y}$. El agente **no
diseña** el filtro (eso corresponde al desarrollo matemático del §6), sino que **decide la familia**
(FIR o IIR) y la **estructura de realización** (forma directa I, forma directa II, cascada de
secciones de segundo orden o *lattice*) y **justifica** la elección. La implementación adoptada es un
**sistema experto de reglas IF-THEN**, por ser interpretable, determinista, ligero y embebible; las
estrategias alternativas (árbol de decisión, lógica difusa, modelo de lenguaje y red neuronal) se
documentan en el §8. El fundamento de las reglas se ancla en los criterios de ingeniería
desarrollados a lo largo de este marco teórico.

---

<!-- ============================================================= -->
<!-- 5. ANÁLISIS DEL PROBLEMA                                      -->
<!-- ============================================================= -->

# 5. Análisis del Problema

## 5.1 Descripción de la señal de ECG

El **electrocardiograma** (ECG) es el registro de la actividad eléctrica del corazón captada en la
superficie corporal. Su forma de onda característica es el **complejo P-QRS-T**, en el que cada
deflexión refleja un evento fisiológico: la onda P (despolarización auricular), el complejo QRS
(despolarización ventricular, la deflexión más rápida y de mayor amplitud) y la onda T
(repolarización ventricular). El contenido diagnóstico de la señal reside en una banda útil
comprendida aproximadamente entre **medio hertz y cuarenta hertz**, y el valor clínico depende
críticamente de la **morfología** —amplitudes y tiempos relativos de las ondas—, lo que impone
preservar la fase.

La señal de ECG aparece contaminada por dos fuentes de ruido dominantes:

- **Interferencia de red eléctrica:** un tono de **cincuenta hertz** (frecuencia de la red en
  Argentina y Europa) acoplado por inducción electromagnética. Cae dentro de la banda útil, por lo
  que debe eliminarse de forma selectiva sin afectar las componentes diagnósticas vecinas.
- **Ruido electromiográfico (EMG) de alta frecuencia:** actividad muscular de banda ancha que se
  extiende por encima de cuarenta hertz y se atenúa con un filtro pasa-bajos.

## 5.2 Justificación de la frecuencia de muestreo por Nyquist

El **teorema de muestreo de Nyquist-Shannon** establece que una señal de banda limitada a $f_B$ queda
completamente determinada por sus muestras si $f_s > 2 f_B$. La frecuencia $f_s/2$ es la **frecuencia
de Nyquist**, máxima frecuencia representable sin ambigüedad. Si existen componentes por encima de
$f_s/2$, se produce **aliasing**, fenómeno irreversible una vez muestreada la señal.

Para el ECG, con banda útil $f_B = 40$ Hz, la tasa de Nyquist mínima sería $2 \times 40 = 80$ Hz. Sin
embargo, se elige $f_s = 500$ Hz, un **factor de sobremuestreo de aproximadamente 6,25**, por tres
razones de ingeniería:

1. Deja una banda de transición amplia al filtro anti-aliasing analógico previo al conversor.
2. Mantiene la interferencia de red de cincuenta hertz muy por debajo de la frecuencia de Nyquist
   ($f_N = 250$ Hz), de modo que se muestrea sin alias y puede eliminarse con un notch.
3. Mejora la resolución temporal del complejo QRS, la deflexión más rápida de la señal.

A modo de ilustración del aliasing: con $f_s = 500$ Hz, una componente parásita de cuatrocientos
ochenta hertz se plegaría a $|480 - 500\cdot\operatorname{round}(480/500)| = 20$ Hz, disfrazándose de
una componente de veinte hertz dentro de la banda útil.

## 5.3 Tabla de especificaciones técnicas

La máscara de diseño completa, que rige tanto la etapa FIR como la IIR, se resume a continuación.

| Parámetro | Símbolo | Valor | Comentario |
|-----------|:-------:|:-----:|------------|
| Frecuencia de muestreo | $f_s$ | 500 Hz | $T = 2$ ms; $f_N = 250$ Hz |
| Banda útil diagnóstica | — | 0,5 – 40 Hz | Complejo P-QRS-T |
| Borde de banda de paso | $f_p$ | 40 Hz | Límite superior de la banda útil |
| Borde de banda de rechazo | $f_r$ | 60 Hz | Inicio de la banda atenuada (IIR) |
| Ondulación máxima en paso | $R_p$ | 1 dB | Rizado tolerado en banda útil |
| Atenuación mínima en rechazo | $A_s$ | 40 dB | Supresión exigida en banda de rechazo |
| Transición FIR | $\Delta f$ | 40 → 50 Hz (10 Hz) | Para el pasa-bajos FIR |
| Ruido 1: red eléctrica | $f_0$ | 50 Hz | Notch IIR de 2.º orden |
| Ruido 2: EMG | — | $> 40$ Hz | Banda ancha; pasa-bajos FIR |
| Fase lineal requerida | — | **Sí** | Preservar morfología P-QRS-T |

## 5.4 Estrategia de filtrado

De acuerdo con las especificaciones, se adopta una **cadena de filtrado mixta de dos etapas** que
combina lo mejor de ambas familias:

- **Etapa 1 — Notch IIR de 50 Hz (segundo orden):** elimina la interferencia de red con coste
  mínimo (un solo biquad). Un IIR es idóneo aquí porque la muesca estrecha se logra con orden dos y
  la pequeña distorsión de fase localizada en cincuenta hertz es tolerable.
- **Etapa 2 — Pasa-bajos FIR de fase lineal (Hamming, $f_c = 40$ Hz):** suprime el ruido EMG de alta
  frecuencia preservando la morfología, gracias a su fase lineal y retardo de grupo constante.

Esta estrategia mixta es la recomendada en la literatura biomédica y la que sostiene el agente de
decisión: el filtro de fase lineal preserva el complejo P-QRS-T, mientras que el notch recursivo
optimiza el coste de la supresión de red.

---

<!-- ============================================================= -->
<!-- 6. DISEÑO DE FILTROS                                          -->
<!-- ============================================================= -->

# 6. Diseño de Filtros

## 6.1 Diseño del filtro FIR pasa-bajos (Hamming)

### 6.1.1 Especificación y cálculo del orden

Se diseña un pasa-bajos FIR de fase lineal con $f_s = 500$ Hz, frecuencia de corte $f_c = 40$ Hz,
banda de transición de cuarenta a cincuenta hertz ($\Delta f = 10$ Hz) y ventana de Hamming
($A_s \approx 53$ dB). Aplicando la regla de orden de la ventana de Hamming:

$$
N \approx \frac{3{,}3\,f_s}{\Delta f} = \frac{3{,}3 \times 500}{10} = 165
\;\Longrightarrow\; \boxed{N = 166}\ (\text{par, Tipo I}),\quad N+1 = 167\ \text{coeficientes}.
$$

Se redondea a $N = 166$ (orden par) para obtener un FIR de **Tipo I** (simétrico, orden par), el más
versátil y apto para pasa-bajos. Como verificación cruzada, la fórmula de Kaiser para $A_s = 53$ dB
con $\Delta\omega = 2\pi \cdot 10/500 = 0{,}1257$ rad da
$N \approx (53 - 8)/(2{,}285 \cdot 0{,}1257) \approx 157$, del mismo orden de magnitud (la regla de
Hamming es algo más conservadora).

### 6.1.2 Coeficientes, simetría y función de transferencia

La frecuencia de corte de diseño se centra en la transición, $f_c' = (40 + 50)/2 = 45$ Hz, lo que da
$\omega_c = 2\pi \cdot 45/500 = 0{,}5655$ rad $= 0{,}18\pi$ (normalizada a Nyquist: $45/250 = 0{,}18$).
Los coeficientes resultan del producto de la sinc ideal por la ventana de Hamming:

$$
h[n] = \underbrace{\frac{\sin\!\bigl(\omega_c(n - 83)\bigr)}{\pi\,(n - 83)}}_{\text{sinc ideal}}
       \cdot
       \underbrace{\Bigl(0{,}54 - 0{,}46\cos\tfrac{2\pi n}{166}\Bigr)}_{\text{ventana de Hamming}},
\qquad n = 0,\dots,166.
$$

El coeficiente central ($n = 83$) alcanza el pico $h[83] = \omega_c/\pi \approx 0{,}18$, y se cumple
la **simetría** $h[n] = h[166 - n]$, que confirma el carácter Tipo I y garantiza **fase lineal
exacta**. La función de transferencia es el polinomio

$$
H(z) = \sum_{k=0}^{166} h[k]\,z^{-k},\qquad h[k] = h[166 - k],
$$

cuya suma de coeficientes verifica la ganancia unitaria en continua,
$\sum_k h[k] = H(e^{j0}) \approx 1$.

### 6.1.3 Retardo de grupo y coste

El retardo de grupo es constante:

$$
\tau_g = \frac{N}{2} = \frac{166}{2} = 83\ \text{muestras} = \frac{83}{500} = 0{,}166\ \text{s}
       = \mathbf{166\ ms}.
$$

Este retardo constante no distorsiona el complejo P-QRS-T. El coste es de aproximadamente 167
operaciones MAC por muestra, equivalentes a $83{,}5$ kMAC/s a quinientos hertz: perfectamente viable
en plataformas con unidad de punto flotante (ESP32, STM32) e inviable en Arduino UNO en punto fijo.

## 6.2 Diseño del filtro IIR Butterworth, Chebyshev, elíptico

> **Nota de autoridad numérica.** Este desarrollo sigue fielmente el módulo `_kb/03-iir.md`, que es
> la referencia canónica del ejemplo IIR. El resultado clave ($N = 13$ para Butterworth) motiva el
> cambio de prototipo y el uso de la estructura SOS.

### 6.2.1 Especificación y frecuencias digitales

Se diseña un pasa-bajos IIR con $f_s = 500$ Hz ($T = 2$ ms), $f_p = 40$ Hz, $f_r = 60$ Hz,
$R_p = 1$ dB y $A_s = 40$ dB, partiendo del prototipo Butterworth. Las frecuencias digitales
normalizadas son:

$$
\omega_p = \frac{2\pi \cdot 40}{500} = 0{,}5027\ \text{rad} = 0{,}16\pi,
\qquad
\omega_r = \frac{2\pi \cdot 60}{500} = 0{,}7540\ \text{rad} = 0{,}24\pi.
$$

### 6.2.2 Prewarping (predistorsión de frecuencias)

Con $2/T = 1000$, se predistorsionan las frecuencias críticas antes del diseño analógico:

$$
\Omega_p = 1000 \cdot \tan(0{,}2513) = \mathbf{256{,}76}\ \text{rad/s}\ (\approx 40{,}86\ \text{Hz}),
$$
$$
\Omega_r = 1000 \cdot \tan(0{,}3770) = \mathbf{395{,}93}\ \text{rad/s}\ (\approx 63{,}01\ \text{Hz}).
$$

El prewarping desplaza ligeramente las frecuencias hacia arriba; sin él, los bordes de banda caerían
corridos respecto de los cuarenta y sesenta hertz deseados.

### 6.2.3 Cálculo del orden (Butterworth)

Aplicando la fórmula del orden Butterworth:

$$
10^{A_s/10} - 1 = 10^4 - 1 = 9999,\qquad 10^{R_p/10} - 1 = 10^{0{,}1} - 1 = 0{,}2589,
$$
$$
\frac{9999}{0{,}2589} = 38\,617,\qquad \log_{10}(38\,617) = 4{,}5868,
$$
$$
\frac{\Omega_r}{\Omega_p} = \frac{395{,}93}{256{,}76} = 1{,}5420,\qquad \log_{10}(1{,}5420) = 0{,}1881,
$$
$$
N \ge \frac{4{,}5868}{2 \cdot 0{,}1881} = \frac{4{,}5868}{0{,}3762} = 12{,}19
\;\Longrightarrow\; \boxed{N = 13}.
$$

### 6.2.4 Lectura de ingeniería: por qué Butterworth N=13 motiva Chebyshev y elíptico

Un orden trece es **altísimo**: la transición de cuarenta a sesenta hertz (relación $1{,}54$) con
cuarenta decibelios de atenuación es muy exigente para el prototipo Butterworth, que es el de menor
pendiente. Este resultado motiva tres decisiones reales de diseño:

1. **Relajar la máscara** (por ejemplo, $A_s = 20$–$30$ dB o ensanchar $f_r$), lo que bajaría $N$ a un
   rango de cuatro a seis.
2. **Cambiar de prototipo** manteniendo la **misma** máscara. Con la fórmula del orden basada en el
   coseno hiperbólico inverso, el prototipo **Chebyshev I** da $N \approx 5{,}97 \Rightarrow N = 6$, y
   el **elíptico** da $N \approx 4$. El compromiso es admitir rizado en banda y peor fase.
3. Si se mantiene un orden alto, es **obligatorio** realizar el filtro en cascada de biquads (SOS);
   una forma directa de orden trece es numéricamente inviable.

La tabla siguiente compara los prototipos para esta máscara concreta:

| Prototipo | Orden $N$ | Secciones SOS | MAC/muestra | Comentario |
|-----------|:---------:|:-------------:|:-----------:|------------|
| **Butterworth** | 13 | 7 | $\approx 35$ | Fase más limpia, orden inviable |
| **Chebyshev I** | 6 | 3 | $\approx 15$ | Rizado en paso, orden razonable |
| **Elíptico (Cauer)** | 4 | 2 | $\approx 10$ | Orden mínimo, fase fea |

### 6.2.5 Función de transferencia, SOS y ecuación en diferencias

La frecuencia de corte se fija en $\Omega_c = \Omega_p/\varepsilon^{1/N}$ con
$\varepsilon = \sqrt{10^{0{,}1} - 1} = 0{,}5088$. Con $\Omega_c$ se ubican los polos sobre el
semicírculo del semiplano izquierdo y se arma $H_a(s)$ como producto de secciones de segundo orden.
Aplicando la transformada bilineal $s = \frac{2}{T}\frac{1 - z^{-1}}{1 + z^{-1}}$ a cada sección se
obtiene la función de transferencia digital en formato de cascada de secciones de segundo orden
(**SOS**, *Second-Order Sections*):

$$
H(z) = \prod_{i} \frac{b_{0i} + b_{1i}z^{-1} + b_{2i}z^{-2}}{1 + a_{1i}z^{-1} + a_{2i}z^{-2}}.
$$

Para el caso Butterworth $N = 13$, esto resulta en seis biquads más una sección de primer orden. La
**ecuación en diferencias** de cada sección, que alimenta su salida a la siguiente, es

$$
y_i[n] = b_{0i}x_i[n] + b_{1i}x_i[n-1] + b_{2i}x_i[n-2]
       - a_{1i}y_i[n-1] - a_{2i}y_i[n-2].
$$

### 6.2.6 Estabilidad y estructura de realización

Un IIR causal es **estable** (BIBO) si y solo si **todos sus polos** están estrictamente dentro del
círculo unitario, $|d_k| < 1\ \forall k$. La transformada bilineal **garantiza** esta condición
siempre que el prototipo analógico sea estable, por lo que el filtro diseñado es estable por
construcción. La verificación práctica se realiza calculando las raíces del denominador
(`max(abs(roots(a))) < 1`) o visualmente con el diagrama de polos-ceros.

Para órdenes mayores o iguales a tres es **obligatorio** el formato SOS. La razón es la **sensibilidad
a la cuantización de coeficientes**: en un polinomio de grado alto las raíces son extremadamente
sensibles a perturbaciones de los coeficientes (problema de Wilkinson), de modo que un polo cercano al
círculo unitario podría salir de él y volver inestable el filtro. Al factorizar en biquads, cada par
de polos y ceros se cuantiza por separado dentro de su sección, lo que reduce drásticamente la
sensibilidad y permite escalar la ganancia sección a sección para controlar el rango dinámico —
imprescindible en aritmética de punto fijo.

## 6.3 Diseño del notch IIR de 50 Hz

La interferencia de red de cincuenta hertz se elimina con un **rechaza-banda (notch) IIR de segundo
orden**, la opción de coste mínimo. Su estructura consiste en un par de **ceros sobre el círculo
unitario** exactamente en $\omega_0 = 2\pi \cdot 50/500 = 0{,}2\pi$ y un par de **polos** justo
dentro del círculo, en el mismo ángulo y con radio $r \lesssim 1$:

$$
H_{\text{notch}}(z) =
\frac{(1 - e^{j\omega_0}z^{-1})(1 - e^{-j\omega_0}z^{-1})}{(1 - re^{j\omega_0}z^{-1})(1 - re^{-j\omega_0}z^{-1})}
= \frac{1 - 2\cos\omega_0\,z^{-1} + z^{-2}}{1 - 2r\cos\omega_0\,z^{-1} + r^2 z^{-2}}.
$$

El radio $r$ (típicamente entre $0{,}95$ y $0{,}99$) fija el **ancho de la muesca**: cuanto más cerca
de la unidad, más estrecho es el notch (menor distorsión de la banda útil) pero más largo el
transitorio. El coste es de un único biquad ($\approx 5$ MAC por muestra), lo que justifica preferir
IIR para esta etapa aun cuando el pasa-bajos principal sea FIR de fase lineal. En la práctica se
genera con `butter(2,[...],'stop')` o `iirnotch`.

---

<!-- ============================================================= -->
<!-- 7. SIMULACIÓN EN MATLAB/OCTAVE                                -->
<!-- ============================================================= -->

# 7. Simulación en MATLAB/Octave

Esta sección describe el conjunto de gráficas y métricas que componen la verificación del diseño
(Paso 3 del examen). Las figuras se generan ejecutando el script
`entrega_octave/ejemplos/diseno_filtros.m` (diseño y análisis de los filtros) y
`entrega_octave/ejemplos/procesar_senal.m` (procesamiento de la señal contaminada y métricas). Los
equivalentes en Python están en `entrega_python/ejemplos/diseno_filtros.py` y `procesar_senal.py`.

> **Nota metodológica.** En el marco de este trabajo **no se ejecutan los scripts**; las figuras se
> referencian con marcadores de posición y la tabla comparativa se completa con valores coherentes con
> el desarrollo matemático del §6 y con la base de conocimiento. Al ejecutar los scripts en Octave (con
> `pkg load signal`) o en Python (entorno virtual con `scipy`), las gráficas se generan automáticamente
> y deben sustituir a los marcadores.

## 7.1 Gráficas de verificación

**Figura 1 — Respuesta en frecuencia en magnitud (|H| en dB).**
`[Figura generada por entrega_octave/ejemplos/diseno_filtros.m — placeholder]`
Se grafican $20\log_{10}|H(e^{j\omega})|$ del FIR y del IIR sobre el eje de frecuencias de cero a
doscientos cincuenta hertz. Verificación: corte a cuarenta hertz, rizado en banda de paso menor o
igual que un decibelio y atenuación mayor o igual que cuarenta decibelios en la banda de rechazo. Se
marca con línea vertical la frecuencia de corte.

**Figura 2 — Respuesta en fase.**
`[Figura generada por entrega_octave/ejemplos/diseno_filtros.m — placeholder]`
Fase desenrollada de ambos filtros. Verificación: el FIR muestra una **fase perfectamente recta**
(lineal); el IIR muestra una fase curva (no lineal), evidencia visual de la distorsión que el FIR
evita.

**Figura 3 — Retardo de grupo.**
`[Figura generada por entrega_octave/ejemplos/diseno_filtros.m — placeholder]`
$\tau_g(\omega)$ en muestras. Verificación: el FIR presenta un retardo **constante de 83 muestras**
en toda la banda útil; el IIR presenta un retardo variable.

**Figura 4 — Diagrama de polos y ceros (`zplane`).**
`[Figura generada por entrega_octave/ejemplos/diseno_filtros.m — placeholder]`
Verificación: el FIR tiene todos los polos en el origen y ceros en cuádruplas recíprocas conjugadas;
el IIR tiene todos los polos **dentro del círculo unitario** (estabilidad confirmada) y los ceros del
notch sobre el círculo en cincuenta hertz.

**Figura 5 — Señal de ECG antes y después del filtrado.**
`[Figura generada por entrega_octave/ejemplos/procesar_senal.m — placeholder]`
Comparación en el dominio temporal de la señal contaminada (con interferencia de cincuenta hertz y
ruido de banda ancha) y la señal filtrada, mostrando la recuperación del complejo P-QRS-T sin
distorsión de forma.

**Figura 6 — Espectro (FFT/PSD) antes y después.**
`[Figura generada por entrega_octave/ejemplos/procesar_senal.m — placeholder]`
Verificación: el espectro de entrada muestra un **pico agudo en cincuenta hertz** y energía por
encima de cuarenta hertz; el de salida muestra ambos suprimidos, conservando la banda diagnóstica.

## 7.2 Tabla comparativa cuantitativa FIR vs IIR

La siguiente tabla sintetiza la comparación cuantitativa para la misma máscara de diseño del ECG
(pasa-bajos, $f_c = 40$ Hz, $A_s \approx 40$ dB), con valores coherentes con el §6 y la base de
conocimiento.

| Métrica | **FIR (Hamming)** | **IIR (SOS)** | Observación |
|---------|:-----------------:|:-------------:|-------------|
| Orden $N$ | 166 | 4–6 (elíptico/Cheby); **13** (Butterworth) | IIR muy inferior |
| Secciones / *taps* | 167 *taps* | 2–3 biquads | — |
| MAC por muestra | $\approx 167$ | $\approx 10$–$15$ | IIR $\sim 11\times$ más barato |
| Coeficientes a almacenar | 167 | 12–18 | — |
| Estados (memoria buffer) | 166 | 4–6 | — |
| Memoria en float32 | $\approx 1{,}3$ kB | $\approx 100$ B | IIR $\sim 14\times$ más compacto |
| Carga a 500 Hz | $\approx 83$ kMAC/s | $\approx 7{,}5$ kMAC/s | — |
| **Fase** | **Lineal exacta** | No lineal | **FIR (decisivo en ECG)** |
| Retardo de grupo | Constante = 83 muestras (166 ms) | Variable, menor en promedio | — |
| Estabilidad | Garantizada (solo ceros) | Condicional ($\lvert d_k\rvert < 1$) | FIR |
| Sensibilidad a cuantización | Baja | Alta → exige SOS | FIR |
| Mejora de SNR ($\Delta$SNR) | $\approx 14$ dB | $\approx 14$ dB | Equiparable en calidad |

## 7.3 Métricas de calidad obtenidas

Con la señal limpia de referencia $s[n]$, la contaminada $x[n]$ y la filtrada $\hat s[n]$, la
relación señal a ruido se define como

$$
\mathrm{SNR}_{\text{dB}} = 10\log_{10}\frac{\sum_n s^2[n]}{\sum_n (\hat s[n] - s[n])^2}.
$$

Partiendo de una potencia de señal de mil unidades y un ruido inicial de doscientas cincuenta, la
SNR de entrada es $10\log_{10}(1000/250) = 6{,}02$ dB. Tras el notch de cincuenta hertz y el
pasa-bajos de cuarenta hertz, el residuo de ruido baja a diez unidades, con lo que la SNR de salida
es $10\log_{10}(1000/10) = 20$ dB. La **mejora resultante es de aproximadamente catorce decibelios**:

$$
\Delta\mathrm{SNR} = \mathrm{SNR}_{\text{out}} - \mathrm{SNR}_{\text{in}} = 20 - 6{,}02 \approx \mathbf{14\ dB}.
$$

Para análisis fuera de línea se recomienda el filtrado de **fase cero** (`filtfilt`/`sosfiltfilt`),
que filtra hacia adelante y hacia atrás anulando el retardo neto, ideal para no deformar el ECG. En la
implementación embebida en tiempo real (Paso 5), en cambio, el filtrado es causal (`filter`/`sosfilt`)
e introduce el retardo de grupo nominal.

---

<!-- ============================================================= -->
<!-- 8. AGENTE DE IA / SISTEMA EXPERTO                             -->
<!-- ============================================================= -->

# 8. Agente de IA / Sistema Experto

## 8.1 Descripción y variables de entrada/salida

El agente de decisión se implementa como un **sistema experto de reglas IF-THEN**, compuesto por una
base de hechos (las variables de entrada), una base de reglas y un motor de inferencia por
encadenamiento hacia adelante. Su rol es recomendar la familia de filtro (FIR o IIR) y la estructura
de realización en función de las restricciones del sistema, justificando la decisión con las reglas
activadas. Esta estrategia se elige por ser **interpretable, determinista, ligera y embebible**; no
requiere entrenamiento, sino elicitación del conocimiento experto codificado en los criterios de
ingeniería.

**Variables de entrada $\mathbf{x}$:**

| Variable | Símbolo | Tipo / rango |
|----------|---------|--------------|
| Frecuencia de muestreo | `fs` | Hz (10 … 5000) |
| Memoria del microcontrolador | `RAM`, `Flash` | kB (2 … 512) |
| Cómputo disponible | `MHz`, `FPU` | 16 … 240 MHz; con/sin FPU |
| Fase lineal requerida | `fase_lineal` | booleano |
| Ruido / SNR de entrada | `SNR_in` | dB (0 … 40) |
| Latencia admisible | `latencia` | {baja, media, alta} |
| Pendiente de transición | `transicion` | {estrecha, amplia} |
| Orden FIR estimado | `ordenFIR` | entero |

**Variables de salida $\mathbf{y}$:** recomendación `{FIR, IIR}`; estructura `{DF I, DF II, SOS,
lattice}`; justificación (reglas activadas, en lenguaje natural); nivel de confianza en $[0,1]$
(opcional).

## 8.2 Base de reglas

Las reglas R1 a R4 son las reglas de referencia del enunciado; R5 a R7 las extienden. El motor recorre
las reglas por prioridad y la **primera que dispara fija** la familia, la estructura y la confianza,
acumulando todas las reglas activadas para trazabilidad.

| # | Prioridad | SI (condición) | ENTONCES | Confianza |
|---|-----------|----------------|----------|-----------|
| R1 | alta | `fase_lineal == sí` (estricta) | **FIR**, estructura DF | 0,95 |
| R2 | alta | `RAM < 2 kB` Y `ordenFIR > 50` | **IIR**, SOS | 0,90 |
| R3 | alta | estabilidad crítica Y sin FPU/float | **IIR**, SOS | 0,90 |
| R4 | media | `transicion == estrecha` Y cómputo suficiente | **IIR** (Elíptico) | 0,85 |
| R5 | media | `latencia == baja` Y FIR alto inviable | **IIR**, DF II | 0,70 |
| R6 | baja | FPU Y `transicion == amplia` Y fase lineal deseada | **FIR**, DF | 0,80 |
| R7 | baja | ninguna anterior disparada | **FIR** por defecto, DF | 0,50 |

La implementación de referencia está en `entrega_octave/ejemplos/agente_decision.m` (sistema experto
en `.m`) y `entrega_python/ejemplos/agente_decision.py` (versión Python). La variante que delega la
decisión a un modelo de lenguaje Claude vía API está en `entrega_python/ejemplos/agente_llm.py`.

## 8.3 Estrategias alternativas

El enunciado pide elegir y justificar una estrategia; se elige reglas IF-THEN. Las otras cuatro se
documentan por completitud y se comparan a continuación:

| Criterio | (a) Reglas | (b) Árbol | (c) Difusa | (d) API LLM | (e) MLP |
|----------|:----------:|:---------:|:----------:|:-----------:|:-------:|
| Interpretabilidad | Muy alta | Alta | Alta | Media | Baja |
| Datos necesarios | Ninguno | Dataset (sint.) | Ninguno | Ninguno | Dataset (más) |
| Determinismo | Total | Total (tras `fit`) | Total | **No** | Total (tras `fit`) |
| Idoneidad embebida | Excelente | Buena (→ `if/else`) | Media | **Nula** (online) | Baja |
| Aporta confianza | Opcional | Sí (`predict_proba`) | Sí (centroide) | Sí (campo JSON) | Sí (softmax) |
| Recomendado para | µC tiempo real | diseño + exportar | entradas imprecisas | **fase de diseño** | (sobre-ingeniería) |

El árbol de decisión y el MLP requieren un dataset sintético etiquetado por las reglas de ingeniería;
la lógica difusa sustituye fronteras duras por grados de pertenencia $\mu \in [0,1]$ con inferencia
Mamdani; la API LLM se construye por *prompt engineering* estructurado con salida JSON validada, útil
solo en fase de diseño por su latencia, coste y no determinismo. El MLP se considera sobre-ingeniería
para un problema de pocas variables y fronteras explicables.

## 8.4 Escenarios de validación

El agente se valida con tres escenarios de restricciones distintos, cuyas salidas son coherentes con
los criterios de ingeniería y con los Pasos 1 a 3.

| Escenario | Entrada clave | Salida esperada | Regla |
|-----------|---------------|-----------------|-------|
| **(a) ECG diagnóstico** | `fase_lineal = sí`, $f_s = 500$, transición amplia, FPU (ESP32/STM32) | **FIR** / DF | R1 |
| **(b) Arduino UNO** | RAM 2 kB, `ordenFIR > 50`, sin FPU, fase no estricta | **IIR** / SOS (Q15) | R2, R3 |
| **(c) Transición exigente** | `transicion = estrecha`, ESP32 con FPU ≥ 160 MHz, fase no requerida | **IIR (Elíptico)** / SOS | R4 |

**Justificaciones.** (a) La morfología clínica exige fase lineal exacta, que solo el FIR garantiza por
la simetría de $h[n]$; el cómputo con FPU absorbe el mayor orden. (b) Un FIR de orden mayor que
cincuenta es inviable con dos kilobytes de RAM; el IIR logra la misma selectividad con orden bajo, y
sin unidad de punto flotante se impone la estructura SOS por estabilidad numérica, en punto fijo Q15.
(c) Con transición estrecha y cómputo suficiente conviene un IIR de orden adecuado; el prototipo
elíptico da la pendiente más abrupta con el menor orden, y SOS asegura la estabilidad.

## 8.5 Ejemplo de uso

Una llamada típica al agente para el escenario (a), en sintaxis Octave, es:

```matlab
[rec, est, reglas, conf] = agente_reglas(struct( ...
    'fs', 500, 'RAM', 320, 'Flash', 4096, 'MHz', 240, 'FPU', true, ...
    'fase_lineal', true, 'SNR_in', 15, 'latencia', 'media', ...
    'transicion', 'amplia', 'ordenFIR', 166));
% Resultado: rec = 'FIR', est = 'DF', reglas = {'R1'}, conf = 0.95
```

El resultado recomienda FIR con estructura de forma directa, disparando la regla R1 con confianza de
$0{,}95$, en plena coherencia con la decisión de diseño adoptada en el §6 para preservar el complejo
P-QRS-T.

---

<!-- ============================================================= -->
<!-- 9. IMPLEMENTACIÓN EMBEBIDA                                    -->
<!-- ============================================================= -->

# 9. Implementación Embebida

## 9.1 Selección de hardware

La cadena de filtrado se implementa sobre un microcontrolador **ESP32** (núcleo a 160–240 MHz, más de
320 kB de RAM y **unidad de punto flotante por hardware**), plataforma que admite sin restricciones el
FIR de orden alto en aritmética **float32**. Esta elección es consistente con la recomendación del
agente para el escenario de ECG diagnóstico (regla R1).

> **Nota sobre Arduino UNO e IIR.** Si la plataforma fuese un Arduino UNO (16 MHz, 2 kB de RAM, sin
> FPU), el FIR de 167 *taps* sería inviable y el agente recomendaría (reglas R2 y R3) una solución
> **IIR de orden bajo en cascada SOS, con aritmética de punto fijo Q15**. La cadena se rediseñaría
> entonces como notch IIR más pasa-bajos IIR (Chebyshev o elíptico de orden cuatro a seis),
> aceptando la fase no lineal a cambio de la viabilidad de recursos.

| Plataforma | Reloj | RAM | FPU | Aritmética | Filtro recomendado |
|------------|-------|-----|-----|------------|--------------------|
| **Arduino UNO** | 16 MHz | 2 kB | No | Q15 | IIR orden bajo (SOS); FIR solo $N \lesssim 20$ |
| **ESP32** (adoptada) | 160–240 MHz | 320 kB+ | **Sí** | **Float32** | **FIR orden alto** o IIR libre |
| STM32F4 | 168 MHz | 128–192 kB | Sí | Float32 | FIR/IIR sin restricción práctica |

## 9.2 Diagrama de bloques

```text
   +----------+     +-------------+     +------------------+     +---------------+     +----------+
   |  Sensor  |     |   AFE +     |     |   ADC (12 bit)   |     |  Buffer       |     |  Notch   |
   |   ECG    |---->| anti-alias  |---->|  f_s = 500 Hz    |---->|  circular     |---->|  IIR     |
   | (electr.)|     | (LP analóg) |     |  (timer-ISR)     |     |  (línea ret.) |     |  50 Hz   |
   +----------+     +-------------+     +------------------+     +---------------+     +----+-----+
                                                                                            |
                                                                                            v
   +----------+     +-------------+     +------------------+                          +----------+
   |  Salida  |     |  Métricas / |     |   Pasa-bajos     |                          | (biquad  |
   |  ECG     |<----|  display /  |<----|   FIR Hamming    |<-------------------------|  2.o ord)|
   | filtrada |     |  log SNR    |     |   f_c = 40 Hz    |                          +----------+
   +----------+     +-------------+     +------------------+
```

La adquisición se realiza por **interrupción de temporizador** (timer-ISR) para garantizar un $f_s$
exacto; el **buffer circular** actúa como línea de retardo natural del filtro. La señal atraviesa
primero el notch IIR (un biquad) y luego el pasa-bajos FIR.

## 9.3 Pseudocódigo del filtrado

```c
/* --- Cadena de filtrado ECG en tiempo real (ESP32, float32) --- */
#define NTAPS 167                 /* FIR Hamming, orden 166 */
float h_fir[NTAPS];               /* coeficientes FIR precalculados (simétricos) */
float bn[3], an[3];               /* biquad notch 50 Hz: b0,b1,b2 / a0,a1,a2 */

float x_buf[NTAPS] = {0};         /* buffer circular de entrada al FIR */
int   idx = 0;
float wn1 = 0, wn2 = 0;           /* estados del biquad notch (DF-II traspuesta) */

/* Rutina de servicio de interrupción del timer (cada 1/fs = 2 ms) */
void ISR_muestra(void) {
    float x = adc_leer();                       /* muestra cruda del ADC */

    /* Etapa 1: NOTCH IIR 50 Hz (1 biquad, forma directa II traspuesta) */
    float w  = x - an[1]*wn1 - an[2]*wn2;        /* a0 = 1 (normalizado) */
    float yn = bn[0]*w + bn[1]*wn1 + bn[2]*wn2;
    wn2 = wn1;  wn1 = w;

    /* Etapa 2: PASA-BAJOS FIR (convolución sobre buffer circular) */
    x_buf[idx] = yn;
    float acc = 0.0f;
    int k = idx;
    for (int i = 0; i < NTAPS; i++) {
        acc += h_fir[i] * x_buf[k];
        k = (k == 0) ? (NTAPS - 1) : (k - 1);    /* recorre hacia atrás */
    }
    idx = (idx + 1) % NTAPS;

    salida_dac(acc);                             /* ECG filtrado */
}
```

El notch se implementa en forma directa II traspuesta (mínima memoria, menor error de redondeo) y el
FIR como convolución directa sobre el buffer circular. En aritmética de punto fijo (plataformas sin
FPU) el acumulador debe ser de mayor ancho (32 o 64 bits) que las muestras y los coeficientes, con
bits de guarda y, eventualmente, aritmética saturante para prevenir desbordes.

## 9.4 Representación de coeficientes: float32 frente a Q15

Existen dos representaciones posibles para los coeficientes y las muestras:

- **Punto flotante (float32):** se emplea en plataformas con FPU (ESP32, STM32F4). Es directo, de
  amplio rango dinámico y sin riesgo de desborde apreciable; es la opción adoptada.
- **Punto fijo Q15 (formato Q1.15):** entero de dieciséis bits que representa
  $x_{\text{real}} = x_{\text{int}} \cdot 2^{-15}$ en el rango $[-1, 1)$. Se emplea en plataformas sin
  FPU (Arduino UNO). Los coeficientes se normalizan a $[-1, 1)$; el producto de dos valores Q15 es
  Q30, y sumar $N$ productos requiere $\lceil\log_2 N\rceil$ bits de guarda en el acumulador.

El ruido de cuantización tiene potencia $\sigma_q^2 = \Delta^2/12$ con $\Delta = 2^{-n}$. La regla de
diseño fundamental es que **un IIR de orden mayor que dos en punto fijo debe realizarse siempre en
cascada SOS**, porque la cuantización de coeficientes puede desplazar los polos fuera del círculo
unitario y desestabilizar el filtro. El FIR, al carecer de polos, no sufre este riesgo.

## 9.5 Validación frente a la simulación

La validación de la implementación embebida consiste en comparar la salida del microcontrolador con la
salida de la simulación en Octave/Python ante la misma señal de entrada, evaluando: (i) el error
cuadrático medio entre ambas salidas, que debe ser del orden del piso de cuantización; (ii) la
preservación de la SNR mejorada (aproximadamente veinte decibelios de salida); y (iii) la latencia
total, dominada por el retardo de grupo del FIR (166 ms). Las fuentes de error a controlar son la
cuantización de coeficientes y de productos, el truncamiento del acumulador, el posible aliasing
residual y la latencia de cómputo. El detalle de la implementación se documenta en el directorio
`entrega_embebido/` (código C/MicroPython, coeficientes y banco de pruebas).

---

<!-- ============================================================= -->
<!-- 10. CONCLUSIONES                                              -->
<!-- ============================================================= -->

# 10. Conclusiones

**Resultados.** Se diseñó, simuló y especificó la implementación de un sistema de filtrado digital
para señal de ECG que cumple la máscara propuesta. La cadena mixta —notch IIR de segundo orden a
cincuenta hertz más pasa-bajos FIR de fase lineal con ventana de Hamming a cuarenta hertz— alcanza una
mejora de relación señal a ruido del orden de **catorce decibelios** (de seis a veinte decibelios),
suprimiendo tanto la interferencia de red como el ruido EMG de alta frecuencia. El FIR resultó de
orden ciento sesenta y seis (167 *taps*) con retardo de grupo constante de 166 ms, mientras que el
desarrollo IIR mostró que el prototipo Butterworth requiere orden trece para la máscara estricta, lo
que justifica recurrir a Chebyshev I (orden seis) o elíptico (orden cuatro) cuando se prioriza la
eficiencia. La decisión arquitectónica de emplear un FIR de fase lineal para la etapa principal queda
plenamente justificada por la necesidad de preservar la morfología del complejo P-QRS-T, y es la que
recomienda de forma autónoma el agente de decisión (regla R1).

**Limitaciones.** El retardo de grupo de 166 ms del FIR, aunque constante, es elevado y podría ser
inaceptable en aplicaciones de monitoreo con realimentación inmediata. El filtrado de fase cero que
anula ese retardo solo es aplicable fuera de línea. La implementación de orden alto en punto flotante
restringe la plataforma a microcontroladores con FPU; en un Arduino UNO sería obligatorio el rediseño
hacia IIR en punto fijo, con la consiguiente distorsión de fase. Finalmente, las figuras de simulación
quedaron como marcadores de posición al no ejecutarse los scripts en este trabajo.

**Trabajo futuro.** Se propone: ejecutar los scripts de simulación con un dataset real de PhysioNet
(MIT-BIH) para validar las métricas con señales clínicas; explorar un FIR equiripple (Parks-McClellan)
para reducir el orden y, con ello, el retardo; implementar y medir la cadena en el ESP32 real,
contrastando la salida embebida con la simulación; y enriquecer el agente con la variante de árbol de
decisión exportada a `if/else` en C, embebible junto al filtro.

---

<!-- ============================================================= -->
<!-- 11. BIBLIOGRAFÍA                                             -->
<!-- ============================================================= -->

# 11. Bibliografía

[1] A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*, 3rd ed. Upper Saddle River,
NJ, USA: Pearson/Prentice Hall, 2010.

[2] J. G. Proakis and D. G. Manolakis, *Digital Signal Processing: Principles, Algorithms, and
Applications*, 4th ed. Upper Saddle River, NJ, USA: Pearson Prentice Hall, 2007.

[3] S. K. Mitra, *Digital Signal Processing: A Computer-Based Approach*, 4th ed. New York, NY, USA:
McGraw-Hill, 2011.

[4] T. W. Parks and C. S. Burrus, *Digital Filter Design*. New York, NY, USA: Wiley-Interscience, 1987.

[5] J. F. Kaiser, "Nonrecursive digital filter design using the I0-sinh window function," in *Proc.
IEEE Int. Symp. Circuits and Systems (ISCAS)*, San Francisco, CA, USA, 1974, pp. 20–23.

[6] The SciPy community, "Signal processing (`scipy.signal`)," *SciPy Reference Guide*. [En línea].
Disponible: https://docs.scipy.org/doc/scipy/reference/signal.html

[7] J. W. Eaton, D. Bateman, S. Hauberg, and R. Wehbring, *GNU Octave Manual* (Octave Forge `signal`
package documentation), version 8.x, 2024. [En línea]. Disponible: https://octave.org/doc/

[8] The MathWorks, Inc., *Signal Processing Toolbox User's Guide*, Natick, MA, USA, R2021b+. [En
línea]. Disponible: https://www.mathworks.com/help/signal/

[9] Anthropic, "Claude Developer Platform — API documentation and Python SDK (`anthropic`)." [En
línea]. Disponible: https://docs.claude.com/

[10] F. Pedregosa *et al.*, "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol.
12, pp. 2825–2830, 2011. [En línea]. Disponible: https://scikit-learn.org/stable/

---

<!-- ============================================================= -->
<!-- 12. ANEXOS                                                    -->
<!-- ============================================================= -->

# 12. Anexos

## Anexo A — Índice de archivos del proyecto

```text
preuba-ia2/
├── README.md                          Índice general del proyecto
├── _kb/                               Base de conocimiento modular (fuente de síntesis)
│   ├── 00-enunciado.md                Resumen del examen y anexos
│   ├── 01-fundamentos-pds.md          Nyquist, DTFT/DFT/Z, fase lineal, SNR
│   ├── 02-fir.md                      Diseño FIR (ventanas, orden, H(z))
│   ├── 03-iir.md                      Diseño IIR (autoridad numérica del ejemplo)
│   ├── 04-criterios-diseno.md         Criterios FIR vs IIR, MACs, punto fijo
│   ├── 05-agente-ia.md                Agente de decisión (5 estrategias)
│   ├── 06-octave.md                   Referencia de herramientas Octave/MATLAB
│   └── 07-python.md                   Referencia de herramientas Python
├── entrega_octave/
│   ├── APUNTES_OCTAVE.md              Apuntes Octave/MATLAB (autónomos)
│   └── ejemplos/
│       ├── diseno_filtros.m           Diseño y análisis FIR/IIR (Figuras 1–4)
│       ├── procesar_senal.m           Filtrado de la señal + métricas (Figuras 5–6)
│       └── agente_decision.m          Agente experto IF-THEN en .m
├── entrega_python/
│   ├── APUNTES_PYTHON.md              Apuntes Python (autónomos)
│   └── ejemplos/
│       ├── diseno_filtros.py          Diseño y análisis FIR/IIR
│       ├── procesar_senal.py          Filtrado + métricas
│       ├── agente_decision.py         Agente (reglas / árbol / fuzzy / MLP)
│       ├── agente_llm.py              Agente vía API LLM Claude
│       └── requirements.txt           Dependencias del entorno virtual
├── entrega_embebido/                  Implementación en µC (C/MicroPython) [Paso 5]
└── informe/
    └── INFORME.md                     Este documento
```

## Anexo B — Mapeo a los entregables del examen

| # | Entregable (los 5 pasos del examen) | Ubicación en el proyecto | Sección de este informe |
|---|-------------------------------------|--------------------------|-------------------------|
| 1 | Análisis del problema y especificaciones | `_kb/00,01` · `APUNTES_*` §3 | §5 |
| 2 | Desarrollo matemático del diseño (FIR e IIR) | `_kb/02,03` · `APUNTES_*` §4–§5 | §6 |
| 3 | Simulación en MATLAB/Octave (gráficas + métricas) | `entrega_octave/ejemplos/diseno_filtros.m`, `procesar_senal.m` | §7 |
| 4 | Agente de decisión asistido por IA | `entrega_*/ejemplos/agente_decision.*`, `agente_llm.py` | §8 |
| 5 | Implementación en microcontrolador | `entrega_embebido/` | §9 |
| 6 | Documento de síntesis Octave/MATLAB | `entrega_octave/APUNTES_OCTAVE.md` | (transversal) |
| 7 | Documento de síntesis Python | `entrega_python/APUNTES_PYTHON.md` | (transversal) |
| 8 | Informe final integrador | `informe/INFORME.md` | (este documento) |

---

<div align="center">

*Informe final del Examen Parcial Integrador — Técnicas Digitales III (PDS / Filtrado Digital, 2026).*
*El PDF formal se genera con pandoc (Arial 11 pt, márgenes 2,5 cm) según el bloque de metadatos del
encabezado.*

</div>
