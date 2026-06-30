# 🫀 Guía de Estudio — Filtrado Digital FIR/IIR Asistido por IA (ECG)

> **Qué es esto.** Una guía de estudio **autocontenida** para entender —y poder **explicar** a otra persona— la resolución del *Examen Parcial Integrador de Procesamiento Digital de Señales (PDS) 2026*, **Opción A: ECG**. Está pensada para alguien que **parte de cero**: cada término se define la primera vez que aparece, cada idea va acompañada de una analogía, un ejemplo numérico real del proyecto, un procedimiento para ponerlo en práctica y preguntas de autoevaluación.
>
> **El problema en una línea.** Tomar la señal eléctrica del corazón (ECG), que llega contaminada por la red eléctrica de 50 Hz y por ruido muscular, y **limpiarla con filtros digitales sin deformar su forma** (porque esa forma es el diagnóstico), para finalmente **correr el filtro en un microcontrolador ESP32** en tiempo real.

---

## Cómo usar esta guía

**¿Para quién es?** Para un estudiante que nunca vio procesamiento de señales y necesita comprender qué se hizo en el proyecto, por qué, y cómo reproducirlo o defenderlo en una exposición oral.

**¿Cómo está organizada?** En **12 secciones jerárquicas**. Las secciones **1 a 7** siguen el hilo natural del problema (fundamentos → diseño FIR → diseño IIR → criterios → simulación → agente IA → embebido). Las secciones **8 a 12** son material de repaso transversal (mapeo al examen, glosario, autoevaluación, checklist y referencias).

**Cada sección 1–7 tiene la misma estructura**, para que sepas siempre dónde mirar:

| Bloque | Para qué sirve |
|--------|----------------|
| **En una frase** | La idea central, antes de cualquier detalle. |
| **Definiciones clave** | El vocabulario mínimo, en lenguaje simple y con analogías. |
| **Desarrollo** | La explicación progresiva, de lo intuitivo a lo formal (con matemática). |
| **Ejemplo concreto (proyecto ECG)** | Todo aplicado al caso real, con los números del proyecto y código verdadero. |
| **Procedimiento práctico** | Pasos numerados para reproducir lo hecho con tus propias manos. |
| **Preguntas guía** | Para comprobar que entendiste (ideal antes de un examen oral). |

**Rutas de lectura sugeridas:**
- **Lectura completa (recomendada para principiantes):** del 1 al 12 en orden.
- **Repaso rápido antes de defender:** Sección 8 (mapeo a los pasos) → preguntas guía de cada sección → Sección 10 (autoevaluación).
- **Solo la parte matemática:** Secciones 2 y 3. **Solo la parte de ingeniería/decisión:** Secciones 4 y 6. **Solo la parte práctica:** Secciones 5 y 7.

**Convenciones:** la matemática va en LaTeX ($\dots$); el código en bloques con su lenguaje (`matlab`, `python`, `cpp`); las referencias cruzadas se indican como "ver Sección N". Los **números canónicos del proyecto** (fs = 500 Hz, FIR Hamming N = 166, etc.) son los mismos en toda la guía.

---

## El proyecto de un vistazo

| Dato | Valor |
|------|-------|
| **Aplicación** | ECG (electrocardiograma) — Opción A del examen |
| **Frecuencia de muestreo** | $f_s = 500$ Hz ($T = 2$ ms entre muestras) |
| **Banda útil de la señal** | 0.5 – 40 Hz (ondas P-QRS-T) |
| **Ruidos a eliminar** | Red eléctrica 50 Hz · ruido muscular EMG (alta frecuencia) · deriva de línea de base (baja frecuencia) |
| **Solución de filtrado** | **Notch IIR 50 Hz** (rechaza-banda) **+ Pasa-bajos FIR fc = 40 Hz** (ventana Hamming) |
| **Ejemplo numérico canónico** | FIR Hamming **N = 166** · IIR Butterworth N = 13 → motiva **Chebyshev I N≈6** / **Elíptico N≈4** en **SOS** |
| **Decisión asistida por IA** | Agente que recomienda FIR vs IIR + estructura, según restricciones (5 estrategias posibles) |
| **Plataforma embebida** | **ESP32** (con FPU, usa float32); Arduino UNO como contraste (sin FPU, punto fijo Q15) |

**Mapa de archivos del proyecto** (dónde está cada cosa que esta guía explica):

```
preuba-ia2/
├── EXAMEN PARCIAL INTEGRADOR PDS 2026.docx  ← el enunciado
├── informe/INFORME.md                        ← informe final académico
├── presentacion/PRESENTACION.md              ← slides (defensa oral)
├── entrega_octave/ejemplos/                  ← diseno_filtros.m · procesar_senal.m · agente_decision.m
├── entrega_python/ejemplos/                  ← diseno_filtros.py · procesar_senal.py · agente_decision.py · agente_llm.py
├── entrega_embebido/                         ← filtro_ecg_esp32.ino · coeficientes.h
└── _kb/                                       ← base de conocimiento modular (fundamentos, FIR, IIR, criterios, agente, herramientas)
```

---

## Índice

1. [El problema en palabras simples y fundamentos de PDS](#1-el-problema-en-palabras-simples-y-fundamentos-de-pds)
2. [Diseño de filtros FIR](#2-diseño-de-filtros-fir)
3. [Diseño de filtros IIR](#3-diseño-de-filtros-iir)
4. [Criterios de ingeniería: cómo elegir FIR vs IIR](#4-criterios-de-ingeniería-cómo-elegir-fir-vs-iir)
5. [Simulación y validación (Octave y Python)](#5-simulación-y-validación-octave-y-python)
6. [El agente de decisión asistido por IA](#6-el-agente-de-decisión-asistido-por-ia)
7. [Implementación embebida en ESP32](#7-implementación-embebida-en-esp32)
8. [Cómo se resolvió cada paso del examen (mapeo)](#8-cómo-se-resolvió-cada-paso-del-examen-mapeo)
9. [Glosario de términos](#9-glosario-de-términos)
10. [Autoevaluación global (preguntas integradoras)](#10-autoevaluación-global-preguntas-integradoras)
11. [Procedimiento general de extremo a extremo (checklist)](#11-procedimiento-general-de-extremo-a-extremo-checklist)
12. [Referencias y recursos del proyecto](#12-referencias-y-recursos-del-proyecto)

---

## 1. El problema en palabras simples y fundamentos de PDS

### En una frase

Vamos a tomar la señal eléctrica del corazón (ECG), que llega "ensuciada" por interferencia de la red eléctrica y por ruido muscular, y vamos a limpiarla con filtros digitales **sin deformar su forma**, porque esa forma es justamente lo que el médico lee; esta sección explica desde cero todos los conceptos de Procesamiento Digital de Señales (PDS) que necesitás para entender cómo y por qué se hace.

### Definiciones clave

- **Señal:** una magnitud que cambia y que lleva información. En nuestro caso, el voltaje del corazón medido en la piel a lo largo del tiempo. Analogía: una canción es una señal (el aire vibra y cambia de presión con el tiempo).
- **ECG (electrocardiograma):** registro del voltaje generado por los latidos del corazón. Su "dibujo" característico tiene tres ondas con nombre: **P**, **QRS** y **T** (juntas: el complejo **P-QRS-T**). La forma, la altura y los tiempos de esas ondas son el diagnóstico.
- **Muestra:** un único valor de la señal, tomado en un instante concreto. Analogía: una foto. Una película es una secuencia de fotos; una señal digital es una secuencia de muestras.
- **Muestreo:** el acto de "sacar fotos" de la señal a intervalos regulares. La señal pasa de continua (analógica) a una lista de números (digital).
- **Frecuencia de muestreo $f_s$:** cuántas muestras por segundo tomamos. Se mide en hertz (Hz = muestras/segundo). En ECG usamos $f_s = 500$ Hz: 500 fotos por segundo.
- **Frecuencia:** cuántas veces por segundo se repite algo. Un tono grave tiene frecuencia baja; uno agudo, alta. Se mide en Hz.
- **Filtro digital:** un programa (o circuito) que recibe la señal número a número y deja pasar las frecuencias que querés conservar mientras atenúa (baja) las que querés eliminar. Analogía: un colador que deja pasar el agua y retiene los fideos.
- **Banda útil:** el rango de frecuencias donde vive la información que SÍ querés. En ECG: **0.5 a 40 Hz**.
- **Banda de ruido:** las frecuencias donde vive lo que querés sacar (red eléctrica de 50 Hz, ruido muscular de alta frecuencia, deriva lenta de la línea de base).
- **Dominio del tiempo:** ver la señal como "valor en función del tiempo" (el dibujo del ECG).
- **Dominio de la frecuencia:** ver la misma señal como "cuánta energía hay en cada frecuencia" (su espectro).
- **Espectro:** la "receta de frecuencias" de la señal. Dice qué tonos la componen y con qué intensidad.
- **SNR (relación señal-ruido):** una nota que mide cuánta señal buena hay comparada con cuánto ruido. Más alta = más limpia.
- **RMSE (error cuadrático medio raíz):** cuánto se aleja, en promedio, la señal filtrada de la señal limpia ideal. Más bajo = mejor.
- **Fase lineal:** propiedad de un filtro que retrasa **todas** las frecuencias exactamente lo mismo, así no deforma la forma de onda. Es esencial en ECG.

### Desarrollo

#### Qué es la señal ECG y por qué hay que filtrarla

El corazón, al latir, produce pequeñas corrientes eléctricas. Con electrodos sobre la piel medimos un voltaje que sube y baja siguiendo cada latido: ese registro es el **ECG**. Cada latido tiene una forma reconocible (las ondas **P-QRS-T**), y el médico diagnostica mirando esa forma: ¿el complejo QRS es ancho o angosto?, ¿la onda T está donde debe?, ¿los tiempos entre ondas son normales? El diagnóstico vive en la **morfología** (la forma) y en los **tiempos**.

El problema es que la señal que captamos no llega limpia. Tres "suciedades" típicas la contaminan (hechos del proyecto, ver el [enunciado del examen](_kb/00-enunciado.md)):

1. **Interferencia de red eléctrica (50 Hz):** todo lo que enchufamos a la pared irradia un tono de 50 Hz que se mete en la medición. Es un pico **estrecho y muy concreto** en frecuencia.
2. **Ruido muscular (EMG):** si el paciente tensa músculos, agrega ruido de **alta frecuencia** que se superpone al ECG.
3. **Deriva de línea de base:** la respiración y el movimiento hacen que la línea de referencia "flote" lentamente; es ruido de **muy baja frecuencia**.

La señal útil (0.5–40 Hz) y los ruidos ocupan zonas distintas del espectro. Esa separación es lo que hace posible **filtrar**: dejamos pasar 0.5–40 Hz y atacamos lo demás.

#### Qué pide el examen (los 5 pasos, como hoja de ruta de esta guía)

El examen (ver el [enunciado del examen](_kb/00-enunciado.md)) pide resolver el problema en **5 pasos**. Esta guía completa los desarrolla; acá te doy el mapa para que sepas adónde vas:

1. **Análisis y especificaciones** — caracterizar la señal, justificar $f_s$ por Nyquist, separar banda útil de ruido, elegir el tipo de filtro y fijar los números de diseño ($f_p$, $f_r$, $R_p$, $A_s$, fase lineal sí/no). *Esta Sección 1 te da los fundamentos para entender este paso.*
2. **Diseño matemático** — calcular los filtros: el **FIR** pasa-bajos (ver **Sección 2**) y el **IIR** notch (ver **Sección 3**).
3. **Simulación** — comprobar en Octave/Python que los filtros cumplen, y medir calidad (SNR, RMSE) (ver **Sección 5**).
4. **Agente de IA** — un sistema que recomienda FIR o IIR según las restricciones (ver **Sección 6**).
5. **Implementación embebida** — correr el filtro en un microcontrolador ESP32 (ver **Sección 7**).

#### Señal, muestra y muestreo

Una señal del mundo real es **continua**: tiene un valor en cada instante, sin huecos. Una computadora no puede guardar infinitos valores, así que toma **muestras** a intervalos regulares. Si $x_a(t)$ es la señal continua, la versión digital es

$$
x[n] = x_a(nT), \qquad n = 0, 1, 2, \dots
$$

donde $T$ es el **periodo de muestreo** (segundos entre muestra y muestra) y $n$ es un índice entero (la muestra número $n$). La frecuencia de muestreo es simplemente cuántas muestras por segundo:

$$
f_s = \frac{1}{T} \quad [\text{Hz}].
$$

Con $f_s = 500$ Hz, $T = 1/500 = 0{,}002$ s = 2 ms: tomamos una muestra cada 2 milisegundos.

#### El Teorema de Nyquist-Shannon: por qué $f_s = 500$ Hz

Acá aparece la pregunta clave: **¿cada cuánto hay que tomar muestras para no perder información?** La respuesta es el **Teorema de Nyquist-Shannon**:

> Si la señal no contiene frecuencias por encima de $f_B$, entonces muestreando a una tasa $f_s > 2 f_B$ se la puede **reconstruir exactamente** a partir de las muestras.

La mitad de $f_s$ se llama **frecuencia de Nyquist**:

$$
f_N = \frac{f_s}{2}.
$$

Es la frecuencia más alta que el muestreo puede representar sin confusión. Analogía: si filmás una rueda que gira con muy pocos cuadros por segundo, en el video la rueda parece girar al revés o detenida. Eso es **aliasing**: una frecuencia demasiado alta se "disfraza" de otra más baja, y una vez muestreada **ya no se puede separar** (ver detalle y ejemplo numérico en los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md)). Por eso, antes del muestreo, se usa un **filtro anti-aliasing analógico** que recorta lo que esté por encima de $f_N$.

¿Por qué entonces $f_s = 500$ Hz para un ECG cuya banda útil llega solo a 40 Hz? El mínimo teórico sería $2 \times 40 = 80$ Hz. Pero se elige mucho más, por buenas razones (ver tabla de márgenes en los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md)):

- **Margen de sobremuestreo:** $500/80 \approx 6{,}25\times$. Ese colchón le da banda de transición amplia al anti-aliasing analógico (un filtro analógico simple no corta de golpe en 40 Hz).
- **La red de 50 Hz queda bien representada:** 50 Hz $\ll f_N = 250$ Hz, así que se muestrea sin aliasing y recién después la eliminamos con el notch.
- **Mejor resolución temporal:** eventos rápidos como el QRS se capturan con más detalle.

#### Dominio del tiempo vs dominio de la frecuencia

La **misma** señal se puede mirar de dos formas. En el **dominio del tiempo** ves el dibujo del ECG (cómo varía el voltaje con el tiempo): ahí reconocés las ondas P-QRS-T. En el **dominio de la frecuencia** ves el **espectro**: una barra de energía por cada frecuencia presente. En el espectro de un ECG ruidoso verías un lomo entre 0.5 y 40 Hz (la señal útil), un **pico agudo en 50 Hz** (la red) y un piso de ruido de alta frecuencia (músculo/ADC). El espectro es la "prueba visual" de qué hay que filtrar y dónde.

Pasar del tiempo a la frecuencia se hace con la **Transformada de Fourier**.

#### Transformada de Fourier, DTFT, DFT/FFT y transformada Z (intuición)

La idea de Fourier es: **cualquier señal se puede escribir como suma de tonos puros (senos y cosenos) de distintas frecuencias y amplitudes**. La transformada nos da, para cada frecuencia, cuánta de ella hay. Hay varias versiones según el contexto:

- **DTFT** (Transformada de Fourier de Tiempo Discreto): el espectro "teórico" y continuo de una secuencia $x[n]$. Es la herramienta para describir la **respuesta en frecuencia** de un filtro (ver fórmula en los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md)).
- **DFT / FFT:** la versión que SÍ corre una computadora. La **DFT** toma $N$ muestras y devuelve $N$ valores de espectro; la **FFT** es solo un algoritmo rápido para calcular la DFT (da exactamente los mismos números, pero mucho más rápido). Con $N$ muestras a tasa $f_s$, la **resolución frecuencial** es $\Delta f = f_s/N$ (cuántos Hz separa cada "casillero" del espectro). Más muestras → poder distinguir frecuencias más cercanas.
- **Transformada Z:** una generalización de la DTFT a todo el plano complejo. Donde Fourier evalúa solo sobre tonos puros, la transformada Z usa una variable compleja $z = re^{j\omega}$. Su gran utilidad: convierte un filtro en una **función de transferencia** $H(z)$, una fracción cuyas raíces (polos y ceros) describen completamente al filtro. El **círculo unitario** ($|z| = 1$) en ese plano es justamente el eje de las frecuencias, y la posición de polos y ceros respecto a él determina la forma del filtro y su **estabilidad** (todos los polos adentro del círculo = filtro estable). Esto es la base del diseño IIR (ver **Sección 3** y los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md)).

No necesitás dominar estas transformadas para entender la guía; alcanza con la intuición: **Fourier/DTFT** = ver el espectro; **transformada Z** = describir el filtro con polos y ceros.

#### Convolución: la operación que hace el filtrado

Un filtro queda totalmente descrito por su **respuesta al impulso** $h[n]$: lo que sale si a la entrada le metés un único "pulso" $\delta[n]$. Y la regla mágica es: **filtrar es convolucionar** la señal de entrada con $h[n]$:

$$
y[n] = x[n] * h[n] = \sum_{k} x[k]\, h[n-k].
$$

En palabras: cada muestra de salida es un **promedio ponderado** de muestras de entrada vecinas, donde los pesos son los coeficientes $h[n]$ del filtro. Analogía: para suavizar una foto, reemplazás cada píxel por una mezcla de él y sus vecinos; los pesos de esa mezcla son $h[n]$. En un filtro **FIR** la lista de pesos es finita (ver **Sección 2**); en un **IIR** es infinita y se calcula de forma recursiva con una **ecuación en diferencias** (ver **Sección 3**). En el dominio Z, la convolución se vuelve un simple producto: $Y(z) = H(z)\,X(z)$.

#### Decibeles (dB)

La atenuación de un filtro abarca rangos enormes (de "deja pasar todo" a "deja pasar una millonésima"). Para manejarlos cómodamente se usa una escala logarítmica, el **decibel**:

$$
|H|_{\text{dB}} = 20 \log_{10}|H|.
$$

Guía rápida: ganancia $1$ (deja pasar todo) = **0 dB**; $0{,}5$ = $-6$ dB; $0{,}1$ = $-20$ dB; $0{,}01$ = $-40$ dB. Cada $-20$ dB es "diez veces más chico". La banda de paso ideal está en $\approx 0$ dB y la banda de rechazo, lo más negativa posible.

#### Métricas de calidad: SNR y RMSE

Para saber si el filtro funcionó, comparamos tres señales alineadas: la **limpia** $s[n]$ (la ideal de referencia), la **ruidosa** $x[n]$ y la **filtrada** $\hat s[n]$.

- **SNR (relación señal-ruido), en dB:** mide cuánta señal hay frente a cuánto error.
$$
\mathrm{SNR}_{\text{dB}} = 10 \log_{10} \frac{\sum_n s^2[n]}{\sum_n (\hat s[n] - s[n])^2}.
$$
Cuanto más alta, mejor. La **mejora** se reporta como $\Delta\mathrm{SNR} = \mathrm{SNR}_{\text{salida}} - \mathrm{SNR}_{\text{entrada}}$.

- **RMSE (error cuadrático medio raíz):** la distancia promedio entre la filtrada y la limpia.
$$
\mathrm{RMSE} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1}\big(\hat s[n] - s[n]\big)^2}.
$$
Cuanto más bajo, mejor. (El detalle y un ejemplo numérico completo están en los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md).)

#### Fase lineal y retardo de grupo: por qué son críticos en ECG

Todo filtro retrasa la señal un poquito. La pregunta es: **¿retrasa todas las frecuencias lo mismo, o unas más que otras?**

- La **fase** $\phi(\omega)$ es el corrimiento que el filtro le aplica a cada frecuencia.
- Un filtro tiene **fase lineal** si $\phi(\omega) = -\alpha\,\omega$ (una recta). Eso equivale a **retrasar todas las frecuencias exactamente $\alpha$ muestras**.
- El **retardo de grupo** $\tau_g(\omega) = -\,d\phi/d\omega$ mide ese retraso para cada frecuencia. Con fase lineal, $\tau_g$ es **constante**.

¿Por qué importa tanto en ECG? Si todas las frecuencias se atrasan lo mismo, la onda solo se **corre en el tiempo, sin deformarse**: la forma del P-QRS-T se conserva. Pero si el filtro atrasa unas frecuencias más que otras (fase **no** lineal), las distintas partes de la onda se desalinean y la forma se **distorsiona**: el QRS puede ensancharse o el segmento ST desplazarse, y eso lleva a un **diagnóstico equivocado**. Por eso el pasa-bajos de 40 Hz se hace **FIR de fase lineal** (los FIR simétricos la garantizan exactamente; ver **Sección 2**). En cambio, para el notch de 50 Hz —que está fuera de la banda diagnóstica— se acepta un **IIR** aunque no tenga fase lineal, porque su ventaja es lograr lo mismo con muchísimo menos cómputo (ver **Sección 3**).

#### Especificaciones de diseño ($R_p$, $A_s$, $f_p$, $f_r$): qué significan

Para encargar un filtro hay que decir "cuán bien" debe hacer su trabajo. Cuatro números lo definen (su cálculo concreto va en las Secciones 2 y 3):

- **$f_p$ (frecuencia de paso, *passband edge*):** hasta dónde el filtro debe dejar pasar la señal casi intacta.
- **$f_r$ (frecuencia de rechazo, *stopband edge*):** desde dónde el filtro ya debe estar atenuando fuerte. Entre $f_p$ y $f_r$ está la **banda de transición** (cuanto más angosta, más difícil y costoso el filtro).
- **$R_p$ (rizado de banda de paso, en dB):** cuánta "ondulación" se tolera en la zona que debería pasar intacta. Chico = banda de paso más plana.
- **$A_s$ (atenuación de banda de rechazo, en dB):** cuánto hay que tirar abajo lo que se quiere eliminar. Grande = ruido más suprimido (p. ej. $A_s = 40$ dB = atenuar 100 veces).

### Ejemplo concreto (proyecto ECG)

Apliquemos todo a nuestro caso canónico (números fijos del proyecto, ver el [enunciado del examen](_kb/00-enunciado.md)):

- **Señal:** ECG, banda útil **0.5–40 Hz** (las ondas P-QRS-T).
- **Frecuencia de muestreo:** $f_s = 500$ Hz, es decir $T = 2$ ms entre muestras. Justificación Nyquist: la banda útil llega a 40 Hz, el mínimo teórico es 80 Hz, y 500 Hz da un margen de $\approx 6{,}25\times$, suficiente para el anti-aliasing y para representar bien la red de 50 Hz ($\ll f_N = 250$ Hz).
- **Ruidos a eliminar:** red **50 Hz** (pico estrecho), EMG muscular (alta frecuencia) y deriva de línea de base (baja frecuencia).
- **Solución de filtrado (dos etapas):**
  - **Notch IIR a 50 Hz** (Butterworth orden 2, banda-eliminada): borra el pico de red. No necesita fase lineal porque está fuera de la banda diagnóstica (ver **Sección 3**).
  - **Pasa-bajos FIR con $f_c = 40$ Hz** (ventana **Hamming**): corta el ruido de alta frecuencia y **preserva la morfología** gracias a su fase lineal. En el ejemplo canónico este FIR resulta de orden alto, **$N = 166$ taps** (ver **Sección 2**).

Imaginemos la verificación con los números de ejemplo de los [apuntes de fundamentos de PDS](_kb/01-fundamentos-pds.md). Antes de filtrar, con potencia de señal $P_s = 1000$ y ruido $P_r = 250$:

$$
\mathrm{SNR}_{\text{in}} = 10\log_{10}\frac{1000}{250} = 6{,}02 \ \text{dB}.
$$

Tras el notch + pasa-bajos, el error residual baja a $10$:

$$
\mathrm{SNR}_{\text{out}} = 10\log_{10}\frac{1000}{10} = 20 \ \text{dB}, \qquad \Delta\mathrm{SNR} \approx \mathbf{14 \ dB} \ \text{de mejora}.
$$

Y como el pasa-bajos es FIR de fase lineal, el ECG filtrado conserva la forma del P-QRS-T: la mejora en SNR no se paga con distorsión morfológica.

### Procedimiento práctico

Pasos conceptuales para encarar el problema (los cálculos detallados están en las secciones referenciadas):

1. **Caracterizá la señal.** Anotá qué es (ECG), su banda útil (0.5–40 Hz) y sus ruidos (50 Hz, EMG, deriva).
2. **Elegí y justificá $f_s$.** Verificá Nyquist: $f_s > 2 f_B$. Con $f_B = 40$ Hz y red en 50 Hz, $f_s = 500$ Hz cumple con margen ($f_N = 250$ Hz).
3. **Separá banda útil de banda de ruido en el espectro.** Mentalmente (o con una FFT/PSD, ver **Sección 5**) ubicá: señal en 0.5–40 Hz, pico en 50 Hz, ruido alto por encima.
4. **Decidí el tipo de filtro para cada ruido.** Pico estrecho de red → **notch** (IIR, **Sección 3**). Ruido de alta frecuencia → **pasa-bajos** (FIR, **Sección 2**).
5. **Fijá las especificaciones** $f_p$, $f_r$, $R_p$, $A_s$ y si hace falta **fase lineal** (sí, para el pasa-bajos, por la morfología; no estricta para el notch).
6. **Verificá con métricas.** Tras filtrar (en simulación), calculá **SNR** y **RMSE** contra la señal limpia y mirá el **retardo de grupo** para confirmar que la fase no distorsiona (ver **Sección 5**).

### Preguntas guía

1. ¿Por qué la **forma** de la onda P-QRS-T es clínicamente importante, y qué tipo de ruido amenaza cada parte del espectro del ECG?
2. ¿Qué diferencia hay entre una **señal continua** y una **muestra**, y qué significan exactamente $f_s = 500$ Hz y $T = 2$ ms?
3. Enunciá el **Teorema de Nyquist-Shannon**. Si la banda útil llega a 40 Hz, ¿cuál es el $f_s$ mínimo teórico y por qué el proyecto usa 500 Hz?
4. ¿Qué es el **aliasing**, por qué es **irreversible** y para qué sirve el filtro anti-aliasing analógico?
5. ¿Qué información distinta te dan el **dominio del tiempo** y el **dominio de la frecuencia** de un mismo ECG?
6. En la escala de **decibeles**, ¿a qué ganancia equivalen 0 dB, $-20$ dB y $-40$ dB?
7. ¿Por qué **filtrar es convolucionar**, y qué representan los coeficientes $h[n]$?
8. ¿Qué es la **fase lineal**, cómo se relaciona con el **retardo de grupo**, y por qué es crítica para el pasa-bajos del ECG pero no para el notch de 50 Hz?


---

## 2. Diseño de filtros FIR

### En una frase

Un filtro **FIR** (respuesta finita al impulso) es un filtro digital que produce su salida sumando solo la entrada actual y unas pocas entradas pasadas multiplicadas por coeficientes fijos; con esos coeficientes ordenados de forma **simétrica** consigue **fase lineal**, lo que preserva la forma temporal de la señal (clave para no deformar el ECG).

### Definiciones clave

- **Filtro digital:** sistema que recibe una señal muestreada $x[n]$ y entrega otra $y[n]$ atenuando o realzando ciertas frecuencias. Como un ecualizador, pero hecho con números.
- **FIR (Finite Impulse Response):** filtro cuya respuesta al impulso $h[n]$ tiene un número **finito** de muestras no nulas. Si le metés un único "1" seguido de ceros, la salida se apaga después de $N+1$ muestras. No hay realimentación (no usa salidas pasadas), por eso "se le acaba la memoria".
- **Respuesta al impulso $h[n]$:** lo que sale del filtro cuando entra un impulso unitario $\delta[n]$ (un "1" aislado). En un FIR, $h[n]$ **son directamente los coeficientes** del filtro.
- **Coeficientes / taps:** los números $h[0], h[1], \dots, h[N]$ que multiplican a las muestras. "Tap" = derivación; un FIR de orden $N$ tiene $N+1$ taps.
- **Orden $N$:** cuántas muestras de retardo usa el filtro. A más orden, transición más afilada, pero más cálculo y más retardo.
- **Fase lineal:** propiedad por la cual todas las frecuencias se retrasan el **mismo tiempo**. Resultado: la onda no se deforma, solo llega un poco más tarde. Es la gran virtud del FIR.
- **Banda de paso / banda de rechazo:** rango de frecuencias que el filtro deja pasar / el rango que elimina. Entre ambas hay una **banda de transición**.
- **Ventana $w[n]$:** función suave (Hamming, Hann, etc.) con la que se "recorta" la respuesta ideal infinita para volverla finita sin que aparezcan ondulaciones feas.
- **MAC (multiply-accumulate):** una multiplicación seguida de una suma. Es la operación básica que cuesta el filtro; un FIR gasta $\approx N+1$ MACs por muestra.

### Desarrollo

#### Qué hace un FIR, intuitivamente

Imaginá que tenés una cinta con las últimas $N+1$ muestras de la señal. El FIR multiplica cada muestra por su coeficiente $h[k]$ y suma todo. Esa suma es la salida del instante actual. Formalmente es una **convolución finita**:

$$
y[n] = \sum_{k=0}^{N} h[k]\, x[n-k]
$$

Fijate que del lado derecho **solo aparece la entrada** $x$ (la actual y $N$ pasadas), nunca la salida $y$. Esto se llama "no recursivo". Por eso, cuando la entrada deja de cambiar, la salida deja de cambiar al cabo de $N+1$ muestras: la respuesta al impulso es **finita**.

#### Función de transferencia $H(z)$ — solo ceros

Aplicando la transformada Z a la ecuación en diferencias se obtiene un polinomio:

$$
H(z) = \sum_{k=0}^{N} h[k]\, z^{-k} = h[0] + h[1]z^{-1} + h[2]z^{-2} + \cdots + h[N]z^{-N}
$$

Consecuencias importantes:

- **Solo tiene ceros.** Los únicos polos están en $z=0$, que no afectan la estabilidad.
- Es **siempre estable** (BIBO: entrada acotada → salida acotada), porque la suma de los $|h[k]|$ es finita y no hay realimentación que pueda divergir.
- **No se puede volver inestable** al redondear los coeficientes (a diferencia del IIR; comparación completa en la Sección 4).

#### Simetría de los coeficientes → fase lineal (la idea central)

La gran ventaja del FIR es que puede tener fase **exactamente lineal**. Eso ocurre si y solo si los coeficientes son **simétricos** (o antisimétricos) respecto del centro:

$$
h[n] = \pm\, h[N-n], \qquad n = 0,1,\dots,N
$$

Con signo $+$ (simétrico) la fase es lineal pura. Veamos **por qué** la simetría produce fase lineal. La respuesta en frecuencia es:

$$
H(e^{j\omega}) = \sum_{n=0}^{N} h[n]\, e^{-j\omega n}
$$

Sacamos como factor común el retardo del centro $\tau = N/2$:

$$
H(e^{j\omega}) = e^{-j\omega N/2}\sum_{n=0}^{N} h[n]\, e^{-j\omega (n - N/2)}
$$

Ahora agrupamos el término $n$ con su pareja $N-n$. Como $h[n]=h[N-n]$, sus dos exponenciales $e^{-j\omega(n-N/2)}$ y $e^{+j\omega(n-N/2)}$ se **combinan en un coseno** (recordá $e^{j\theta}+e^{-j\theta}=2\cos\theta$). Por lo tanto toda la suma se vuelve una función **puramente real**, llamémosla $A(\omega)$:

$$
H(e^{j\omega}) = e^{-j\omega N/2}\, \underbrace{A(\omega)}_{\text{real}}
$$

Entonces la fase es simplemente:

$$
\angle H(e^{j\omega}) = -\,\omega\,\frac{N}{2} \;+\; \{0 \text{ ó } \pi\}
$$

es decir una **recta** en función de $\omega$ (los saltos de $\pi$ ocurren solo donde $A(\omega)$ cambia de signo). El **retardo de grupo** (cuánto se retrasa cada frecuencia) es la derivada de la fase con signo cambiado:

$$
\tau_g(\omega) = -\frac{d\,\angle H(e^{j\omega})}{d\omega} = \frac{N}{2}\ \text{muestras (constante)}
$$

**Constante para todas las frecuencias.** Esa es la traducción matemática de "no deforma la onda": todas las componentes llegan retrasadas exactamente $N/2$ muestras, ni una más ni una menos. En segundos: $\tau_g = N/(2 f_s)$.

> Existen 4 tipos de FIR de fase lineal según la simetría (par/impar) y la paridad de $N$. Para un **pasa-bajos** se usa el **Tipo I** (orden $N$ **par**, coeficientes simétricos): es el más versátil y el único sin ceros forzados en DC ni en Nyquist. Los antisimétricos (Tipos III/IV) fuerzan $H(0)=0$ y por eso no sirven para pasa-bajos.

#### Método de ventanas (el más intuitivo)

Receta en tres pasos:

1. **Partir de la respuesta ideal.** Un pasa-bajos ideal con corte $\omega_c = 2\pi f_c/f_s$ tiene como respuesta al impulso la función **sinc**, centrada en $N/2$:

$$
h_d[n] = \frac{\sin\!\big(\omega_c (n-\tfrac{N}{2})\big)}{\pi\,(n-\tfrac{N}{2})}, \qquad h_d\!\left[\tfrac{N}{2}\right] = \frac{\omega_c}{\pi}
$$

Esta sinc es **infinita** (se extiende para siempre): no se puede implementar tal cual.

2. **Truncar y suavizar.** Multiplicamos la sinc por una ventana $w[n]$ que vale cero fuera de $0..N$:

$$
h[n] = h_d[n]\cdot w[n], \qquad n=0,\dots,N
$$

3. **Listo:** esos $h[n]$ son los coeficientes finales, y por construcción quedan simétricos (fase lineal).

**¿Por qué no truncar de golpe?** Cortar la sinc abruptamente equivale a usar una **ventana rectangular**, lo que provoca el **fenómeno de Gibbs**: ondulaciones (*ripple*) y un sobreimpulso fijo de ~9% que **no desaparece** por más que aumentes $N$. Las ventanas suaves matan esas ondulaciones a cambio de **ensanchar la banda de transición**. Ese es el compromiso fundamental: **menos lóbulos laterales ↔ transición más ancha**.

Comparativa de ventanas (de menos a más suave):

| Ventana | Atenuación de banda de rechazo $A_s$ lograble | Orden $N$ estimado |
|---------|-----------------------------------------------|--------------------|
| **Rectangular** | $\approx 21$ dB | $N \approx 0{,}9\, f_s/\Delta f$ |
| **Hann** | $\approx 44$ dB | $N \approx 3{,}1\, f_s/\Delta f$ |
| **Hamming** | $\approx 53$ dB | $N \approx 3{,}3\, f_s/\Delta f$ |
| **Blackman** | $\approx 74$ dB | $N \approx 5{,}5\, f_s/\Delta f$ |
| **Kaiser** ($\beta$ ajustable) | **a pedido** (paramétrica) | fórmula con $A$ y $\Delta\omega$ |

Las tres clásicas se definen así ($0\le n\le N$, $M=N$):

$$
w_{\text{Hann}}[n] = 0{,}5 - 0{,}5\cos\!\frac{2\pi n}{M}, \qquad
w_{\text{Hamming}}[n] = 0{,}54 - 0{,}46\cos\!\frac{2\pi n}{M}
$$

$$
w_{\text{Blackman}}[n] = 0{,}42 - 0{,}5\cos\!\frac{2\pi n}{M} + 0{,}08\cos\!\frac{4\pi n}{M}
$$

#### Cómo se calcula el orden $N$

El orden depende de cuán **estrecha** sea la banda de transición $\Delta f = f_r - f_p$ (en Hz). En radianes normalizados: $\Delta\omega = 2\pi\,\Delta f / f_s$. Cada ventana fija tiene su **regla práctica** (columna derecha de la tabla anterior). Por ejemplo, la **regla de Hamming**:

$$
N \approx \frac{3{,}3\, f_s}{\Delta f}
$$

La **ventana de Kaiser** es especial porque es **paramétrica**: vos pedís una atenuación $A=A_s$ (en dB) y la fórmula te devuelve el parámetro $\beta$ y el orden directamente:

$$
\beta =
\begin{cases}
0{,}1102\,(A - 8{,}7), & A > 50 \\[3pt]
0{,}5842\,(A-21)^{0{,}4} + 0{,}07886\,(A-21), & 21 \le A \le 50 \\[3pt]
0, & A < 21
\end{cases}
\qquad
N \approx \frac{A - 8}{2{,}285\,\Delta\omega}
$$

En software estas cuentas las hace `kaiserord` (tanto en Octave como en SciPy).

#### Parks-McClellan / Remez (diseño óptimo equiripple)

El método de ventanas reparte el error de forma desigual (mayor cerca del corte). El algoritmo **Parks-McClellan** (que internamente usa el **intercambio de Remez**) diseña el FIR **óptimo en sentido minimax**: minimiza el **error máximo**, repartiéndolo de forma **uniforme** en cada banda (respuesta *equiripple*, ondulaciones todas del mismo tamaño):

$$
\min_{h}\ \max_{\omega\in\text{bandas}}\ \big|\,W(\omega)\,[\,A(\omega) - D(\omega)\,]\,\big|
$$

donde $D(\omega)$ es la respuesta deseada (1 en paso, 0 en rechazo) y $W(\omega)$ un peso que permite pedir **distinto ripple** en paso y en rechazo. Su ventaja: logra el **menor orden posible** para una especificación dada → ideal cuando la memoria o el cómputo del microcontrolador están ajustados. En software: `firpm`/`remez` (Octave) y `scipy.signal.remez` (Python).

#### Cuándo conviene FIR

- Cuando la **fase lineal es obligatoria** (ECG, audio, datos): no deformar la forma de onda.
- Cuando se necesita **estabilidad garantizada** sin riesgo de inestabilidad por cuantización.
- **Evitar FIR** cuando la transición es muy estrecha y la plataforma es muy limitada (p. ej. Arduino UNO): el orden $N$ se dispara y conviene IIR. La comparación detallada **FIR vs IIR** está en la **Sección 4**.

### Ejemplo concreto (proyecto ECG)

**Objetivo:** pasa-bajos FIR para quedarnos con la banda útil del ECG (0.5–40 Hz) y atenuar el ruido muscular EMG de alta frecuencia, **sin deformar** el complejo P-QRS-T (por eso FIR de fase lineal).

| Parámetro | Valor |
|-----------|-------|
| Tipo | Pasa-bajos FIR, fase lineal (Tipo I) |
| Frecuencia de muestreo $f_s$ | $500$ Hz |
| Frecuencia de corte $f_c$ | $40$ Hz |
| Banda de transición | $40 \to 50$ Hz ⇒ $\Delta f = 10$ Hz |
| Ventana | Hamming ($A_s \approx 53$ dB) |

**Paso 1 — Orden por la regla de Hamming.** De dónde sale el famoso $N=166$:

$$
N \approx \frac{3{,}3\, f_s}{\Delta f} = \frac{3{,}3 \times 500}{10} = \frac{1650}{10} = 165
$$

Como el pasa-bajos Tipo I exige orden **par**, se redondea hacia arriba a $\mathbf{N = 166}$, que da $N+1 = \mathbf{167}$ coeficientes.

> Verificación cruzada con Kaiser para $A_s=53$ dB: $\Delta\omega = 2\pi\cdot 10/500 = 0{,}1257$ rad y $N\approx(53-8)/(2{,}285\cdot 0{,}1257)\approx 157$. Mismo orden de magnitud (Hamming es algo más conservadora) → el número es coherente.

**Paso 2 — Coeficientes $h[n]$ (sinc enventanado):**

$$
h[n] = \underbrace{\frac{\sin\!\big(\omega_c(n-\tfrac{N}{2})\big)}{\pi\,(n-\tfrac{N}{2})}}_{\text{sinc ideal}} \cdot \underbrace{\Big(0{,}54 - 0{,}46\cos\tfrac{2\pi n}{N}\Big)}_{\text{ventana Hamming}}, \quad n=0,\dots,166
$$

- El **pico** está en el centro $n=N/2=83$: $h[83]=\omega_c/\pi$, el coeficiente más grande.
- **Simetría exacta:** $h[n]=h[166-n]$, o sea $h[0]=h[166]$, $h[1]=h[165]$, etc. → fase lineal garantizada.
- Los coeficientes de los extremos son casi cero, crecen oscilando hacia el centro y decrecen simétricamente; la envolvente Hamming suprime el ripple de Gibbs.

**Paso 3 — Retardo de grupo (constante):**

$$
\tau_g = \frac{N}{2} = \frac{166}{2} = 83\ \text{muestras} = \frac{83}{500} = 0{,}166\ \text{s} = \mathbf{166\ ms}
$$

Igual para todas las frecuencias: por eso la morfología P-QRS-T no se distorsiona, solo se retrasa 166 ms.

**Paso 4 — Coste:** $\approx N+1 = 167$ MACs por muestra. A $f_s=500$ Hz son $\approx 83{,}5$ kMAC/s, perfectamente viable en una **ESP32** con FPU (ver Sección 7), pero pesado para un Arduino UNO.

**Código real — Octave** (`entrega_octave/ejemplos/diseno_filtros.m`):

```matlab
fs   = 500;  fnyq = fs/2;  fc = 40;
Wn_fir = fc / fnyq;            % = 40/250 = 0.16  (fracción de Nyquist)
N_fir  = 166;                  % orden par => Tipo I, 167 coeficientes
b_fir  = fir1(N_fir, Wn_fir, hamming(N_fir+1));   % LP, ventana Hamming
a_fir  = 1;                    % FIR: denominador trivial

% Verificación de simetría  b[n] == b[N-n]  (=> fase lineal exacta)
err_sim = max(abs(b_fir - fliplr(b_fir)));   % debe dar ~0
```

**Código real — Python / SciPy** (`entrega_python/ejemplos/diseno_filtros.py`):

```python
from scipy import signal
# numtaps impar (167) => filtro tipo I, fase lineal exacta por simetría
h = signal.firwin(167, cutoff=40.0, fs=500.0, window="hamming", pass_zero=True)
# pass_zero=True -> deja pasar DC (es pasa-bajos); ganancia DC ≈ 1
print(len(h), len(h) - 1)          # 167 taps, orden N = 166
print(np.allclose(h, h[::-1]))     # True => simétrico => fase lineal
print(np.sum(h))                   # ≈ 1.0  (ganancia unitaria en DC)
```

> **Nota práctica sobre la frecuencia de corte.** El KB centra el corte en mitad de la transición ($f_c'=45$ Hz → normalizado $0{,}18$) para que el flanco de $-6$ dB caiga centrado. El código de entrega, en cambio, pasa el corte directo en $f_c=40$ Hz (`Wn = 40/250 = 0{,}16`). Ambas son decisiones válidas: con `fir1`/`firwin` el argumento de corte es la frecuencia de $-6$ dB; elegir 40 o 45 Hz solo desplaza un poco el flanco dentro de la banda de transición $40\text{–}50$ Hz. El orden $N=166$ y la fase lineal no cambian.

### Procedimiento práctico

1. **Definir las especificaciones:** $f_s$, frecuencia de corte $f_c$, borde de banda de rechazo $f_r$ (de ahí $\Delta f = f_r - f_c$) y atenuación deseada $A_s$.
2. **Elegir la ventana** según el $A_s$ requerido: Hamming para $\approx 53$ dB (caso ECG), Blackman si necesitás más atenuación, Kaiser si querés fijar $A_s$ exacto.
3. **Calcular el orden** con la regla de la ventana, p. ej. Hamming $N\approx 3{,}3\,f_s/\Delta f$. **Redondear hacia arriba** y, para pasa-bajos Tipo I, ajustar $N$ a **par**.
4. **Calcular la frecuencia normalizada:** `Wn = fc/(fs/2)` (en Octave, fracción de Nyquist) o pasar `fc` y `fs` directamente (en `firwin` con `fs=...`).
5. **Generar los coeficientes:** `b = fir1(N, Wn, hamming(N+1))` (Octave) o `h = firwin(N+1, cutoff=fc, fs=fs, window="hamming")` (Python).
6. **Verificar la simetría:** comprobar que $h[n]=h[N-n]$ (`max|b - fliplr(b)| ≈ 0` / `np.allclose(h, h[::-1])`). Si es simétrico → fase lineal exacta.
7. **Verificar la ganancia DC:** $\sum_k h[k] = H(e^{j0}) \approx 1$ para un pasa-bajos.
8. **Caracterizar:** graficar $|H|$ en dB (chequear $f_c$ y $A_s$), la fase (debe ser una recta), el retardo de grupo (constante $=N/2$), el diagrama de polos-ceros (`zplane`: todos los polos en $z=0$) y la respuesta al impulso (debe reproducir $h[n]$). Para la simulación completa ver Sección 5.

### Preguntas guía

1. ¿Por qué un filtro FIR es **siempre estable**, y qué tienen de particular sus polos en $H(z)$?
2. ¿Qué condición deben cumplir los coeficientes $h[n]$ para que el filtro tenga **fase lineal**, y por qué esa simetría convierte la fase en una recta?
3. ¿Cuánto vale el **retardo de grupo** de un FIR de fase lineal de orden $N$, y por qué es importante que sea **constante** en el caso del ECG?
4. En el caso ECG, mostrá de dónde sale el orden $N=166$ a partir de $f_s=500$ Hz, $\Delta f = 10$ Hz y la regla de Hamming. ¿Por qué se redondea a un número par?
5. ¿Qué es el **fenómeno de Gibbs** y cómo lo combate el método de ventanas? ¿Qué se "paga" a cambio?
6. ¿Qué diferencia a la ventana de **Kaiser** de las clásicas (Hamming, Hann, Blackman), y qué ventaja tiene ser "paramétrica"?
7. ¿En qué se diferencia el diseño por **Parks-McClellan/Remez** (equiripple) del método de ventanas, y cuándo conviene usarlo?
8. Escribí la llamada a `fir1` (Octave) o `firwin` (Python) que genera el FIR del ECG, e indicá cómo verificarías que quedó simétrico y con ganancia DC unitaria.


---

## 3. Diseño de filtros IIR

### En una frase

Un filtro **IIR** se diseña tomando un filtro analógico clásico ya conocido (Butterworth, Chebyshev, Elíptico), eligiendo su orden $N$ y transformándolo al mundo digital con la **transformada bilineal**, lo que produce un filtro **recursivo** (con realimentación) de **orden bajo** pero **fase no lineal**, que conviene implementar como **cascada de secciones de 2.º orden (SOS)** para que sea numéricamente estable.

### Definiciones clave

- **IIR (Infinite Impulse Response, respuesta al impulso infinita):** filtro **recursivo** cuya salida $y[n]$ depende de las entradas pasadas **y** de salidas anteriores. Por esa **realimentación**, su respuesta al impulso $h[n]$ dura, en teoría, para siempre (decae pero nunca llega a cero exacto). Analogía: un eco en una sala — golpeás una vez (impulso) y el sonido sigue rebotando, cada vez más débil, mucho después del golpe.
- **Realimentación:** parte de lo ya calculado (la salida) se reinyecta para calcular lo siguiente. Es lo que distingue al IIR del FIR (ver Sección 2) y la fuente tanto de su eficiencia como de sus riesgos (puede volverse inestable).
- **Prototipo analógico $H_a(s)$:** filtro continuo (en el plano $s$ de Laplace) bien estudiado que se usa como **molde de partida**. Hay cuatro clásicos: Butterworth, Chebyshev I, Chebyshev II y Elíptico.
- **Polos y ceros:** los **ceros** anulan la salida en ciertas frecuencias (sirven para *notch*); los **polos** producen resonancias y, sobre todo, **deciden la estabilidad**.
- **Transformada bilineal (TBL):** receta algebraica que convierte el filtro analógico $H_a(s)$ en uno digital $H(z)$ reemplazando $s$ por una expresión en $z^{-1}$.
- **Prewarping (predistorsión de frecuencia):** corrección que se aplica a las frecuencias de diseño **antes** de la TBL para que los bordes de banda caigan exactamente donde queremos.
- **Ecuación en diferencias:** la fórmula con la que el filtro se calcula muestra a muestra en código (la receta ejecutable).
- **Estabilidad:** un IIR es estable si y solo si **todos sus polos están dentro del círculo unitario** ($|d_k|<1$).
- **SOS (Second-Order Sections, secciones de 2.º orden) / biquad:** forma de implementar el filtro como **producto en cascada** de bloques de 2.º orden. Es el estándar para IIR de orden $\ge 3$.
- **Orden $N$:** "tamaño" del filtro. En IIR cuenta el número de polos; a mayor $N$, transición más abrupta, pero más coeficientes y más sensibilidad numérica.

### Desarrollo

#### 3.1 Qué es un IIR y por qué tiene realimentación

Un FIR (Sección 2) calcula la salida usando **solo** muestras de entrada. Un IIR agrega un ingrediente nuevo: **reutiliza salidas que ya calculó**. Esa realimentación es la magia y el peligro del IIR:

- **Ventaja:** con muy pocos coeficientes logra transiciones muy filosas. Para una misma exigencia, un IIR suele necesitar un orden 5 a 20 veces menor que un FIR.
- **Precios:** (1) la **fase no es lineal** (distorsiona la forma temporal de la señal — crítico en ECG, ver Sección 4); (2) **puede volverse inestable** si los polos se ubican mal; (3) es **sensible a la cuantización** de coeficientes.

La **ecuación en diferencias** que define un IIR es:

$$
y[n] \;=\; \sum_{k=0}^{M} b_k\,x[n-k] \;-\; \sum_{k=1}^{N} a_k\,y[n-k].
$$

Los $b_k$ (numerador) son la parte **no recursiva** (generan **ceros**); los $a_k$ con $k\ge1$ (denominador) son la parte **recursiva** (generan **polos**). Por convención $a_0=1$. El término $-\sum a_k y[n-k]$ es precisamente la realimentación.

#### 3.2 De la ecuación a la función de transferencia $H(z)$

Aplicando la transformada Z (que convierte un retardo de $k$ muestras en un factor $z^{-k}$) se obtiene $H(z)$ como **cociente de dos polinomios**:

$$
H(z)=\frac{Y(z)}{X(z)}=\frac{B(z)}{A(z)}
=\frac{b_0+b_1 z^{-1}+\cdots+b_M z^{-M}}{1+a_1 z^{-1}+\cdots+a_N z^{-N}}.
$$

Factorizando, aparecen explícitos los **ceros** $c_m$ (raíces del numerador) y los **polos** $d_k$ (raíces del denominador). Tener denominador no trivial ($A(z)\ne1$) es lo que distingue al IIR del FIR.

#### 3.3 Los cuatro prototipos analógicos y cuándo usar cada uno

El diseño parte de un prototipo $H_a(s)$. Los cuatro se diferencian por **dónde colocan la ondulación** (*ripple*) y por cuán abrupta es la transición que logran a igual orden.

| Prototipo | Ripple banda pasante | Ripple banda rechazo | Transición | Fase | Orden requerido | Ceros finitos |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Butterworth** | No (plano) | No (monótono) | Suave | La mejor | **Máximo** | No |
| **Chebyshev I** | Sí ($R_p$) | No (monótono) | Media-alta | Media | Medio | No |
| **Chebyshev II** | No (plano) | Sí ($A_s$) | Media-alta | Media | Medio | Sí |
| **Elíptico (Cauer)** | Sí ($R_p$) | Sí ($A_s$) | **La más abrupta** | La peor | **Mínimo** | Sí |

- **Butterworth** — *máximamente plano*: sin ondulación en ninguna banda, magnitud monótona. El más "suave" y con mejor fase, pero el que **más orden** pide. Elección por defecto en biomédica. Su módulo:
$$|H_a(j\Omega)|^2=\frac{1}{1+\bigl(\Omega/\Omega_c\bigr)^{2N}}.$$
- **Chebyshev I** — *ripple equiondulado en la banda pasante*, monótono en rechazo. Transición más filosa que Butterworth a igual $N$. Útil cuando se tolera ondulación en la banda útil a cambio de bajar el orden:
$$|H_a(j\Omega)|^2=\frac{1}{1+\varepsilon^2\,T_N^2(\Omega/\Omega_p)}.$$
- **Chebyshev II** (inverso) — banda pasante **plana**, ripple en rechazo; introduce **ceros** sobre el eje $j\Omega$. Bueno cuando la banda pasante debe quedar limpia.
- **Elíptico / Cauer** — *ripple en ambas bandas*; alcanza el **orden mínimo** posible (transición más abrupta) a cambio de la **peor fase** y mayor sensibilidad numérica.

> Regla mnemotécnica: *Butterworth paga con orden la suavidad; Elíptico paga con fase la eficiencia.* La comparación detallada FIR vs IIR y los criterios formales de selección están en la **Sección 4**.

#### 3.4 Cálculo del orden $N$

El orden surge de la **especificación**: $R_p$ (ondulación máxima en banda pasante, dB), $A_s$ (atenuación mínima en rechazo, dB) y las frecuencias **analógicas** de borde $\Omega_p,\Omega_r$ (ya *prewarpeadas*, §3.5). Para **Butterworth**:

$$
N \;\ge\; \frac{\log_{10}\!\dfrac{10^{A_s/10}-1}{10^{R_p/10}-1}}{2\,\log_{10}\!\bigl(\Omega_r/\Omega_p\bigr)},
$$

redondeando **hacia arriba**. El numerador mide la atenuación exigida; el denominador, cuán ancha es la transición. Si la transición es estrecha ($\Omega_r/\Omega_p \to 1$), el orden se dispara. Para **Chebyshev** la misma idea usa $\cosh^{-1}$ en vez de $\log_{10}$, lo que da un orden **siempre menor o igual** que Butterworth; el **Elíptico** usa integrales elípticas y da el **mínimo** de los cuatro. En la práctica esto lo calculan `buttord` / `cheb1ord` / `ellipord`.

#### 3.5 Transformada bilineal y prewarping (el paso clave)

Para llevar $H_a(s)$ al dominio digital se reemplaza:

$$
s=\frac{2}{T}\cdot\frac{1-z^{-1}}{1+z^{-1}},\qquad T=\frac{1}{f_s}.
$$

Esta TBL tiene dos propiedades valiosas: mapea el **semiplano izquierdo** de $s$ al **interior del círculo unitario** de $z$ (por eso **un prototipo analógico estable produce un IIR digital estable**), y mapea el eje $j\Omega$ entero al círculo $|z|=1$ **sin aliasing**.

**El paso algebraico clave — la distorsión de frecuencia.** Si evaluamos la TBL sobre el círculo unitario ($s=j\Omega$, $z=e^{j\omega}$):

$$
j\Omega=\frac{2}{T}\cdot\frac{1-e^{-j\omega}}{1+e^{-j\omega}}
=\frac{2}{T}\,j\tan\!\left(\frac{\omega}{2}\right)
\;\Longrightarrow\;
\Omega=\frac{2}{T}\tan\!\left(\frac{\omega}{2}\right).
$$

Esta relación **no es lineal**: comprime todo el eje analógico $\Omega\in(0,\infty)$ dentro de $\omega\in(0,\pi)$. Ese alabeo se llama **warping**. Para que las frecuencias críticas caigan **exactamente** donde las queremos, se **predistorsionan** (*prewarping*) antes de diseñar $H_a(s)$:

$$
\Omega_a=\frac{2}{T}\tan\!\left(\frac{\omega_d}{2}\right),
\qquad \omega_d=\frac{2\pi f}{f_s}.
$$

Es decir: *prewarpear* $\Omega_p,\Omega_r$, diseñar el prototipo con esos valores, aplicar la TBL — y los bordes vuelven a caer en las frecuencias deseadas con error nulo.

**Mini-desarrollo $H_a(s)\to H(z)$ (un caso de 1.er orden).** Tomemos $H_a(s)=\dfrac{\Omega_c}{s+\Omega_c}$ y sustituyamos $s$. Multiplicando arriba y abajo por $(1+z^{-1})$ y llamando $\alpha=\frac{2}{T}$:

$$
H(z)=\underbrace{\frac{\Omega_c}{\alpha+\Omega_c}}_{b_0}\cdot
\frac{1+z^{-1}}{\,1+\dfrac{\Omega_c-\alpha}{\Omega_c+\alpha}\,z^{-1}},
$$

de donde se leen directamente $b_0=b_1=\frac{\Omega_c}{\alpha+\Omega_c}$ y $a_1=\frac{\Omega_c-\alpha}{\Omega_c+\alpha}$. La **ecuación en diferencias** ejecutable es:

$$
y[n]=b_0\,x[n]+b_1\,x[n-1]-a_1\,y[n-1].
$$

Para órdenes altos se hace lo mismo **sección por sección** (biquads), nunca expandiendo el polinomio completo.

#### 3.6 Estabilidad

Un IIR causal es **estable (BIBO)** si y solo si **todos los polos** están estrictamente dentro del círculo unitario:

$$
|d_k|<1\quad\forall k.
$$

Se verifica calculando las raíces de $A(z)$ y comprobando `max(abs(roots(a))) < 1` (o visualmente con `zplane`). Cuidado: polos muy pegados a $|z|=1$ (filtros de banda estrecha, *notch* agresivos) son estables en teoría pero **frágiles ante la cuantización**: un pequeño error de coeficiente puede empujarlos afuera. Un FIR, en cambio, tiene $A(z)=1$ (todos los polos en $z=0$): por eso es **siempre estable** (ver Sección 4).

#### 3.7 Estructura SOS y por qué se usa

Una misma $H(z)$ se puede calcular de varias formas equivalentes en aritmética exacta pero **muy distintas en aritmética finita**. La preferida para IIR es la **cascada de secciones de 2.º orden (SOS / biquads)**:

$$
H(z)=g\prod_{i=1}^{\lceil N/2\rceil}\frac{b_{0i}+b_{1i}z^{-1}+b_{2i}z^{-2}}{1+a_{1i}z^{-1}+a_{2i}z^{-2}}.
$$

Por qué SOS y no la "forma directa" de orden alto:

- Cuando se **cuantizan los coeficientes** de un polinomio de grado $N$ alto, sus raíces (los polos) son **extremadamente sensibles** a esa perturbación (problema de Wilkinson): un polo casi en $|z|=1$ puede salirse del círculo y volver **inestable** el filtro.
- Al partir en biquads, **cada par de polos/ceros se cuantiza por separado**; el error de un coeficiente afecta **solo a su sección**, no a todas las raíces a la vez. La sensibilidad cae drásticamente.
- Permite **escalar la ganancia sección a sección** para controlar el rango dinámico y evitar desbordes (clave en punto fijo del microcontrolador, Sección 7).

Por eso **el formato `sos` es el estándar para IIR de orden $\ge 3$**. Coste $\approx 5$ MACs por biquad.

### Ejemplo concreto (proyecto ECG)

**Caso A — ECG, $f_s=500$ Hz** (banda útil 0.5–40 Hz; ruidos: red 50 Hz, EMG de alta frecuencia y deriva de línea de base).

#### El pasa-bajos IIR: por qué Butterworth N=13 motiva cambiar de prototipo

Especificación: $f_p=40$ Hz, $f_r=60$ Hz, $R_p=1$ dB, $A_s=40$ dB. La transición $40\!\to\!60$ Hz (relación $1{,}54$) con 40 dB de atenuación es **muy exigente para Butterworth**. Aplicando la fórmula del orden (§3.4) con las frecuencias prewarpeadas se obtiene:

$$
N\ge\frac{4{,}5868}{2\cdot0{,}1881}=12{,}19 \;\Longrightarrow\; \boxed{N=13}.
$$

Un IIR de **orden 13** en forma directa es **numéricamente inviable** (sus polos serían demasiado sensibles a la cuantización). Esto motiva las decisiones reales del examen:

1. **Cambiar de prototipo:** con la misma máscara, **Chebyshev I** da $N\approx6$ y el **Elíptico** $N\approx4$ (orden mínimo).
2. **Realizar en SOS** (cascada de biquads), no en forma directa.

Así, el script elige **Chebyshev I N≈6 en SOS** (y menciona el **Elíptico N≈4** como alternativa de orden mínimo). Código real (Octave):

```matlab
Wp = fp / fnyq;        % 40/250 = 0.16  (banda de paso normalizada)
Ws = fr / fnyq;        % 60/250 = 0.24  (banda de rechazo normalizada)

% Orden minimo Chebyshev I y frecuencia natural
[N_iir, Wn_iir] = cheb1ord(Wp, Ws, Rp, As);

% Diseno en cero-polo-ganancia -> SOS (numericamente robusto)
[z_iir, p_iir, k_iir] = cheby1(N_iir, Rp, Wn_iir);
sos_iir = zp2sos(z_iir, p_iir, k_iir);

% Alternativa eliptico (orden minimo de los cuatro)
[N_ell, Wn_ell] = ellipord(Wp, Ws, Rp, As);
```

Y la versión Python (scipy), con la comprobación didáctica de que Butterworth daría $N=13$:

```python
# Butterworth para la misma mascara -> N = 13 (inviable en forma directa)
n_butter, _ = signal.buttord(wp=FP, ws=FR, gpass=RP, gstop=AS, fs=FS)

# Chebyshev I en SOS (elegido)
n, wn = signal.cheb1ord(wp=FP, ws=FR, gpass=RP, gstop=AS, fs=FS)
sos_cheb = signal.cheby1(n, RP, wn, btype="low", output="sos", fs=FS)

# Eliptico en SOS (orden minimo, N ~ 4)
n_e, wn_e = signal.ellipord(wp=FP, ws=FR, gpass=RP, gstop=AS, fs=FS)
sos_ellip = signal.ellip(n_e, RP, AS, wn_e, btype="low", output="sos", fs=FS)
```

La estabilidad se verifica directamente sobre los polos de la cascada: `np.all(np.abs(p) < 1)` (todos dentro del círculo unitario).

#### El notch IIR de 50 Hz (interferencia de red)

El ECG arrastra interferencia de **red eléctrica** a 50 Hz. Se elimina con un **rechaza-banda (notch) IIR de orden 2**: un par de **ceros sobre el círculo unitario** justo en $\omega_0=2\pi f_0/f_s$ (con $f_0=50$, $f_s=500 \Rightarrow \omega_0=0{,}2\pi$) y un par de **polos** en el mismo ángulo, apenas dentro del círculo (radio $r\lesssim1$):

$$
H_{\text{notch}}(z)=\frac{1-2\cos\omega_0\,z^{-1}+z^{-2}}{1-2r\cos\omega_0\,z^{-1}+r^{2}z^{-2}}.
$$

El radio $r$ (o el factor $Q$) fija el ancho del notch: $r\to1$ da una muesca estrechísima (poca distorsión de la banda útil) pero transitorio más largo. Es un solo biquad ($\approx5$ MACs/muestra), baratísimo. Código real:

```matlab
Q  = 35;                 % factor de calidad (notch estrecho)
w0 = f0 / fnyq;          % 50/250 = 0.20  (centro normalizado)
bw = w0 / Q;             % ancho de banda a -3 dB
[b_notch, a_notch] = iirnotch(w0, bw);
```

```python
b, a = signal.iirnotch(w0=F_NOTCH, Q=Q_NOTCH, fs=FS)  # 50 Hz, Q = 30
sos  = signal.tf2sos(b, a)                            # a cascada de biquads
```

> La solución de filtrado completa del proyecto es **Notch IIR 50 Hz + Pasa-bajos FIR fc=40 Hz (Hamming)** — una estrategia **mixta**: IIR barato para la muesca, FIR de fase lineal para no distorsionar la morfología P-QRS-T. El porqué de esa mezcla se argumenta en la Sección 4.

### Procedimiento práctico

1. **Especificar** la máscara: $f_s$, $f_p$, $f_r$, $R_p$, $A_s$ y el tipo (LP/HP/BP/notch). En ECG: $f_s=500$, $f_p=40$, $f_r=60$, $R_p=1$ dB, $A_s=40$ dB.
2. **Normalizar** las frecuencias a fracción de Nyquist: `Wp = fp/(fs/2)`, `Ws = fr/(fs/2)` (o pasar `fs=...` directamente en scipy, que normaliza internamente).
3. **Elegir prototipo** (§3.3): Butterworth por defecto; si el orden o la transición aprietan, Chebyshev I o Elíptico.
4. **Calcular el orden** con `buttord` / `cheb1ord` / `ellipord`. Si Butterworth da un orden enorme (aquí $N=13$), cambiar de prototipo (Cheby I $N\approx6$, Elíptico $N\approx4$).
5. **Diseñar en formato SOS** (no en forma directa): `cheby1(N,Rp,Wn,'low',output='sos')` o vía `zp2sos`/`tf2sos`. El *prewarping* lo hace la función por dentro.
6. **Verificar estabilidad:** `max(abs(roots(a))) < 1` o `np.all(np.abs(p) < 1)`; inspeccionar con `zplane` que todos los polos estén dentro del círculo.
7. **Caracterizar:** `freqz`/`sosfreqz` para $|H|$ en dB y fase, `grpdelay`/`group_delay` para el retardo de grupo (verás que **no es constante** — fase no lineal), e `impz`/aplicar un delta para ver $h[n]$ infinita decayendo.
8. **Para el notch 50 Hz:** usar `iirnotch(w0, bw)` (Octave) o `iirnotch(w0=50, Q=30, fs=500)` (scipy) y pasarlo a SOS con `tf2sos`.
9. **Escribir la ecuación en diferencias por sección** (cada biquad) para llevarla a código C en el microcontrolador (Sección 7).

### Preguntas guía

1. ¿Por qué la respuesta al impulso de un IIR es "infinita" y qué término de la ecuación en diferencias lo causa?
2. ¿Qué generan los coeficientes $b_k$ y qué generan los $a_k$ en términos de ceros y polos? ¿Cuáles deciden la estabilidad?
3. ¿Cuándo elegirías Butterworth, Chebyshev I, Chebyshev II y Elíptico? Justificá con el trade-off ripple/fase/orden.
4. Deducí $\Omega=\frac{2}{T}\tan(\omega/2)$ a partir de la transformada bilineal. ¿Qué problema corrige el *prewarping* y cuándo se aplica?
5. Para la máscara del ECG (40→60 Hz, 1/40 dB), ¿por qué Butterworth da $N=13$ y por qué eso obliga a cambiar de prototipo y a usar SOS?
6. ¿Cuál es el criterio exacto de estabilidad de un IIR y cómo lo verificás en Octave/Python?
7. ¿Por qué la cascada SOS es numéricamente superior a una forma directa de orden 13? Relacionalo con la sensibilidad de las raíces a la cuantización.
8. ¿Cómo se construye un *notch* de 50 Hz con ceros y polos, y qué controla el radio $r$ (o el $Q$) del filtro?


---

## 4. Criterios de ingeniería: cómo elegir FIR vs IIR

### En una frase

Elegir un filtro digital es **negociar entre tres cosas que tiran en direcciones opuestas** —calidad de fase, coste de cómputo/memoria y dificultad de diseño— y este capítulo te da las reglas numéricas para decidir, en cada caso, si conviene un **FIR** (fase perfecta pero caro) o un **IIR** (barato pero con fase distorsionada), con qué estructura implementarlo y sobre qué microcontrolador.

### Definiciones clave

- **FIR (Finite Impulse Response, respuesta al impulso finita):** filtro cuya salida es solo una suma ponderada de las **entradas** pasadas. No tiene realimentación, por eso su "eco" se apaga en un número finito de muestras. Su diseño detallado está en la **Sección 2**.
- **IIR (Infinite Impulse Response, respuesta al impulso infinita):** filtro que **realimenta** sus salidas anteriores. Eso lo hace muy eficiente, pero su "eco" puede durar para siempre y puede volverse inestable. Su diseño detallado está en la **Sección 3**.
- **Orden ($N$):** cantidad de coeficientes (memoria del filtro) menos uno. Intuición: a mayor orden, "pendiente" más abrupta entre lo que pasa y lo que se bloquea, pero más cómputo.
- **MAC (Multiply-Accumulate, multiplicar-y-acumular):** la operación básica del filtrado: tomar una muestra, multiplicarla por un coeficiente y sumarla a un acumulador. Es la "moneda" con la que medimos el coste: **MACs por muestra de salida**.
- **Fase lineal:** propiedad por la cual **todas las frecuencias se retrasan el mismo tiempo**. Analogía: una orquesta que se atrasa entera mantiene la melodía; si cada instrumento se atrasa distinto, la música se deforma. En un ECG, "deformar" significa cambiar la forma de las ondas P-QRS-T y arruinar el diagnóstico. El FIR la garantiza por **simetría de $h[n]$**; el IIR no.
- **Retardo de grupo:** cuánto tiempo (en muestras) tarda la señal en salir del filtro. En un FIR de fase lineal vale exactamente $N/2$ muestras.
- **SOS (Second-Order Sections, secciones de segundo orden):** forma de implementar un IIR como una **cascada de filtritos de orden 2**. Es la manera robusta de implementar IIR de orden alto (ver Sección 3).
- **Punto fijo (formato Q) vs punto flotante (float):** dos maneras de representar números en un micro. Float es cómodo pero necesita hardware especial (FPU); punto fijo (Q) usa enteros y corre en cualquier lado, pero hay que cuidar el escalado.
- **FPU (Floating Point Unit):** circuito que hace cuentas con decimales en hardware. El ESP32 la tiene; el Arduino UNO no.
- **Plataforma embebida:** el microcontrolador donde finalmente corre el filtro (Arduino UNO, ESP32, STM32). Sus límites de reloj, RAM y FPU condicionan toda la elección.

### Desarrollo

#### La decisión raíz: una sola especificación, dos caminos muy distintos

Cuando definimos lo que queremos —frecuencia de paso $f_p$, frecuencia de rechazo $f_r$, rizado en banda de paso $R_p$ y atenuación mínima $A_s$— **no estamos eligiendo todavía el filtro**. Esa misma especificación se puede cumplir con un FIR o con un IIR, y la diferencia entre ambos es enorme. La regla mental es:

> El FIR paga **mucho cómputo y memoria** a cambio de **fase perfecta y estabilidad garantizada**. El IIR paga **fase distorsionada** a cambio de **orden bajísimo y poco cómputo**.

Toda la decisión gira alrededor de una pregunta: **¿la aplicación necesita fase lineal estricta?** Si la respuesta es sí (señales biomédicas con morfología, como el ECG), el FIR casi siempre gana aunque cueste más. Si es no (filtrado de potencia, anti-aliasing), el IIR suele ganar por barato.

#### Tabla comparativa FIR vs IIR

Esta es la tabla maestra de la decisión. Para una **misma especificación** ($f_p$, $f_r$, $R_p$, $A_s$):

| Criterio | **FIR** | **IIR** | Gana |
|----------|---------|---------|------|
| **Estabilidad** | Siempre estable (sin polos, solo ceros) | Condicional: los polos deben estar en $\lvert z\rvert<1$ | **FIR** |
| **Fase** | **Lineal exacta** si $h[n]$ es simétrica/antisimétrica | No lineal (salvo corrección offline) | **FIR** |
| **Orden para igual $A_s$** | Alto ($N\sim 50$–$300$) | Bajo ($N\sim 2$–$10$) | **IIR** |
| **Coste (MACs/muestra)** | $\approx N+1$ | $\approx 5\cdot S$ (SOS, $S$ secciones) | **IIR** |
| **Memoria de coeficientes** | $N+1$ valores | $6\cdot S$ valores | **IIR** |
| **Sensibilidad a cuantización** | Baja (ceros tolerantes) | Alta (polos cerca de $\lvert z\rvert=1$ se desestabilizan) | **FIR** |
| **Latencia / retardo de grupo** | Constante $=N/2$ muestras (grande) | Variable, menor en promedio | **IIR** |
| **Facilidad de diseño** | Directo (ventanas, `firpm`); siempre converge | Requiere prototipo analógico + bilineal + prewarp | **FIR** |
| **Réplica de filtros analógicos** | Pobre | Excelente (Butter/Cheby/Elíptico) | **IIR** |

**Cómo leerla:** ni FIR ni IIR "ganan" en general; cada uno gana en columnas distintas. El arte de la ingeniería es saber **qué columna pesa más en tu aplicación**.

- **Elegí FIR** cuando se exige **fase lineal estricta** (ECG, EMG), cuando la **estabilidad numérica** es crítica, o cuando hay cómputo/memoria de sobra (ESP32/STM32 con FPU).
- **Elegí IIR** cuando los recursos son **escasos** (Arduino UNO, RAM < 2 kB), cuando se necesita una **transición muy abrupta con orden mínimo**, o cuando se replica un filtro analógico conocido y la fase no es crítica.

#### Cómo elegir la VENTANA (caso FIR)

Si vas por FIR con el método de ventanas (ver Sección 2), la **ventana** fija el "piso" de atenuación $A_s$ que vas a poder alcanzar, y el **ancho de transición** que pidas fija el orden $N$. Regla práctica: elegí la ventana **más simple cuya atenuación supere** el $A_s$ requerido (con margen).

| Ventana | $A_s$ máx (dB) | $N$ aprox. para $\Delta f$ | Cuándo usarla |
|---------|---------------|----------------------------|---------------|
| **Rectangular** | ~21 | $N\approx 0.9\,f_s/\Delta f$ | Solo si $A_s\le 20$ dB |
| **Hann** | ~44 | $N\approx 3.1\,f_s/\Delta f$ | Atenuación media, suave |
| **Hamming** | ~53 | $N\approx 3.3\,f_s/\Delta f$ | **Defecto biomédico** (40–50 dB) |
| **Blackman** | ~74 | $N\approx 5.5\,f_s/\Delta f$ | Alta atenuación |
| **Kaiser** | **ajustable** | fórmula de Kaiser | Cuando $A_s$ no encaja en las fijas |

Para la **Kaiser** (la más usada por ser paramétrica), el orden se estima como:

$$
N \approx \frac{A_s - 7.95}{2.285\,\Delta\omega}, \qquad
\Delta\omega = \frac{2\pi\,\Delta f}{f_s}
$$

Y si necesitás **mínimo orden** para una especificación dura, conviene **equiripple** (Parks-McClellan, `firpm`), que reparte el error de forma óptima:

| Situación | Recomendación |
|-----------|---------------|
| $A_s$ no encaja en ventana fija; banda única | **Kaiser** (rápido, predecible) |
| Mínimo orden para una especificación dada | **Equiripple (`firpm`)** |
| Multibanda / respuestas arbitrarias | **Equiripple** o `firls` |
| Diseño simple, sin toolbox de optimización | **Ventana** (Hamming/Kaiser) |

#### Cómo elegir el PROTOTIPO (caso IIR)

Si vas por IIR, primero elegís un **prototipo analógico** (la "familia" del filtro) y después lo digitalizás (ver Sección 3). El trade-off central es **abruptez de transición vs calidad de fase vs rizado**:

| Prototipo | Banda paso | Banda rechazo | Fase / retardo | Transición | Orden |
|-----------|-----------|---------------|----------------|------------|-------|
| **Butterworth** | Plana | Monótona | La más suave | Lenta | **Mayor** |
| **Chebyshev I** | Rizado $R_p$ | Monótona | Media | Media-rápida | Medio |
| **Chebyshev II** | Plana | Rizado | Media | Media-rápida | Medio |
| **Elíptico (Cauer)** | Rizado $R_p$ | Rizado $A_s$ | **La peor** | **La más rápida** | **Mínimo** |

Para una misma especificación ($A_s\approx 40$ dB) el orden requerido baja drásticamente al cambiar de familia —este es exactamente el camino que recorre el proyecto ECG:

| Prototipo | Orden $N$ típico | MACs (SOS) |
|-----------|------------------|------------|
| Butterworth | 8 | $5\cdot 4 = 20$ |
| Chebyshev I/II | 5 | $5\cdot 3 = 15$ |
| Elíptico | **4** | $5\cdot 2 = 10$ |

- **Butterworth** → cuando la **fase y la planitud** importan y sobra orden (por eso el **notch del ECG es Butterworth**: transición lenta aceptable, fase limpia).
- **Chebyshev** → compromiso intermedio.
- **Elíptico** → cuando el **orden/cómputo debe ser mínimo** y la distorsión de fase no molesta.

#### Coste computacional y de memoria (la parte que decide en el micro)

Las fórmulas base, por cada muestra de salida, son:

$$
\text{MACs}_{\text{FIR}} \approx N+1, \qquad
\text{MACs}_{\text{IIR (SOS)}} \approx 5\,S, \qquad S=\Big\lceil \tfrac{N}{2}\Big\rceil
$$

Para la memoria sumás **coeficientes + línea de retardo** (los estados que el filtro recuerda):

| Filtro | Coeficientes | Estados | Total (float32) |
|--------|--------------|---------|-----------------|
| FIR orden $N$ | $N+1$ | $N+1$ | $\approx 8(N+1)$ bytes |
| IIR SOS, $S$ secciones | $6S$ | $2S$ | $\approx 32\,S$ bytes |

La idea de fondo: como el IIR necesita un **orden mucho menor** para la misma atenuación, gana tanto en MACs como en memoria, a menudo por un factor de **10× o más**. El verdadero precio del FIR no es solo la cuenta: es que **necesitás guardar muchísimos coeficientes**, y eso es lo que no entra en un micro chico.

#### Punto fijo (Q) vs punto flotante

- **Float32:** cómodo, rango enorme, casi no hay que pensar en escalado. Pero si el micro **no tiene FPU**, cada operación float se **emula por software** (~100× más lento) → inviable en tiempo real.
- **Punto fijo (Q$m.n$):** se trabaja con enteros y se interpreta el punto decimal "a mano": $x_{\text{real}} = x_{\text{int}}\cdot 2^{-n}$. Corre rápido en cualquier micro, pero hay que **escalar los coeficientes** (típicamente a $[-1,1)$ → **Q15**) y usar un **acumulador más ancho** (32/64 bits) para no desbordar al sumar muchos productos.

| Plataforma | FPU | Float32 viable | Recomendación |
|------------|-----|----------------|---------------|
| Arduino UNO (AVR) | No | No (emulación ~100× lenta) | **Punto fijo Q15** |
| STM32F4/F7, **ESP32** | **Sí (hardware)** | **Sí** | **Float32 directo** |
| STM32 Cortex-M0/M3 | No | Marginal | Punto fijo |

Dos consecuencias clave del punto fijo:

1. **Overflow:** prevenirlo con escalado de entrada o **aritmética saturante** (clamp) en vez de *wrap-around* (que produce saltos catastróficos).
2. **SOS obligatorio para IIR de orden alto:** en forma directa, un pequeño error al cuantizar un coeficiente **mueve mucho los polos** y puede **desestabilizar** el filtro. Factorizando en secciones de 2.º orden (SOS), cada par de polos se cuantiza aislado y la sensibilidad cae drásticamente. **Regla: IIR de orden > 2 en punto fijo ⇒ siempre SOS en cascada** (la implementación está en la Sección 3).

#### Restricciones de plataforma: el cómputo es un presupuesto

A $f_s = 500$ Hz hay $T = 1/f_s = 2$ ms para procesar cada muestra. Los ciclos disponibles son $f_{\text{clk}}\cdot T$:

| Plataforma | Reloj | RAM | FPU | Ciclos por muestra ($\times 2$ ms) | Filtro recomendado |
|------------|-------|-----|-----|------------------------------------|--------------------|
| **Arduino UNO** | 16 MHz | 2 kB | No | $\approx 32\,000$ | **IIR orden bajo (SOS) Q15**; FIR solo $N\lesssim 20$ |
| **ESP32** | 160–240 MHz | 320 kB+ | **Sí** | $\approx 480\,000$ | **FIR orden alto** o IIR libre (float32) |
| **STM32F4** | 168 MHz | 128–192 kB | **Sí** | $\approx 336\,000$ | FIR/IIR sin restricción práctica |

> **Regla de presupuesto:** $\text{MACs}_{\text{filtro}}\cdot f_s$ debe ser **mucho menor** que los MAC/s disponibles, dejando margen (≥50%) para el ADC, la interrupción, la lógica de aplicación y el jitter. En Arduino esto empuja casi siempre hacia **IIR de orden bajo en punto fijo**.

### Ejemplo concreto (proyecto ECG)

El sistema ECG usa **$f_s = 500$ Hz**, banda útil **0.5–40 Hz**, y debe limpiar tres ruidos: interferencia de red de **50 Hz** (armónico estrecho), ruido muscular EMG (alta frecuencia) y deriva de línea de base (baja frecuencia). La solución combina **dos filtros distintos**, y la razón de elegir uno u otro es exactamente este capítulo:

**1) Pasa-bajos FIR, $f_c = 40$ Hz, ventana Hamming → $N = 166$.**
Aplicando la tabla comparativa: el ECG necesita **fase lineal estricta** para no deformar las ondas P-QRS-T (diagnóstico), así que la columna "Fase" pesa más que el coste. Por eso se acepta un FIR de orden alto. Comparado con un IIR Butterworth equivalente:

| Métrica | **FIR Hamming** | **IIR Butterworth** |
|---------|-----------------|---------------------|
| Orden $N$ | **~166** | **~6** |
| Secciones SOS | — | 3 |
| MACs/muestra | $166$ | $5\cdot 3 = 15$ |
| Coeficientes | $166$ | $18$ |
| Estados | $166$ | $6$ |
| Memoria float32 | $\approx 166\cdot 8 = 1.3$ kB | $\approx (18+6)\cdot 4 = 96$ B |
| Carga a $f_s=500$ Hz | $166\cdot 500 = 83$ kMAC/s | $15\cdot 500 = 7.5$ kMAC/s |

El IIR sería **~11× más barato en cómputo y ~14× en memoria**, pero distorsionaría la fase. Como en ECG la morfología es clínica, se paga el FIR.

**Por qué el FIR $N=166$ es viable en ESP32 pero no en Arduino UNO:**
- En **ESP32**: $83$ kMAC/s contra ~decenas de miles de MAC disponibles por muestra con FPU; y $1.3$ kB de coeficientes entran cómodos en sus 320 kB de RAM. **Holgado.**
- En **Arduino UNO**: solo $2$ kB de RAM total —los $1.3$ kB de coeficientes float ya casi la llenan, sin contar buffers ni variables— y **sin FPU**, así que cada MAC float se emula. El FIR $N=166$ **no entra**. Por eso, en un UNO, este mismo pasa-bajos se reimplementaría como **IIR de orden bajo en SOS Q15** (o se baja el orden del FIR drásticamente).

**2) Notch IIR (Butterworth orden 2, banda-eliminada) a 50 Hz, implementado como SOS.**
Para borrar el tono de red de 50 Hz se necesita una muesca muy localizada. Hacerla con FIR exigiría un orden enorme; con **IIR basta orden 2**. Aquí la fase localizada importa menos que el costo, así que **gana el IIR**, y se implementa como **SOS** por robustez numérica (la regla "orden > 2 ⇒ SOS" y, en punto fijo, siempre SOS). El prototipo Butterworth se elige por su transición suave y fase limpia alrededor de la muesca.

> **Moraleja del caso ECG:** un mismo sistema usa **FIR para el pasa-bajos** (fase manda) e **IIR/SOS para el notch** (coste manda). No hay "el mejor filtro"; hay el mejor filtro **para cada tarea y cada plataforma**.

### Procedimiento práctico

Para decidir un filtro siguiendo el criterio de ingeniería, en este orden:

1. **Escribí la especificación** completa: $f_s$, banda útil, $f_p$, $f_r$, $R_p$, $A_s$ y —crucial— **si la fase lineal es estricta o no**. (En ECG: sí, estricta.)
2. **Aplicá la regla dominante:** si la fase lineal es estricta y hay recursos → **FIR**. Si no → seguí al paso 3.
3. **Mirá el presupuesto de plataforma:** calculá los MACs del candidato ($N+1$ para FIR, $5S$ para IIR-SOS) y multiplicalos por $f_s$. Compará contra los MAC/s del micro y contra la RAM (coeficientes + estados). Si el FIR no entra en RAM → **IIR**.
4. **Elegí el método/familia:**
   - FIR → **ventana** (Hamming por defecto biomédico; Kaiser si $A_s$ no encaja; equiripple si el orden debe ser mínimo). Estimá $N$ con la fórmula de la ventana. (Detalle en Sección 2.)
   - IIR → **prototipo** (Butterworth si fase/planitud manda; Elíptico si el orden debe ser mínimo). (Detalle en Sección 3.)
5. **Elegí la aritmética:** ¿el micro tiene FPU? Sí → **float32**. No → **punto fijo Q15** (escalá coeficientes a $[-1,1)$ y usá acumulador ancho + saturación).
6. **Elegí la estructura:** IIR de orden > 2 → **SOS en cascada** (obligatorio en punto fijo). FIR → forma directa.
7. **Verificá el margen:** confirmá que $\text{MACs}\cdot f_s$ deja ≥50% de CPU libre para ADC, ISR y aplicación; y que la **latencia** ($\approx N/(2 f_s)$ para FIR) es tolerable.

> Esta secuencia es justamente la que automatiza el **agente de decisión IA de la Sección 6** mediante reglas IF-THEN del tipo: *"si fase lineal estricta → FIR"*, *"si RAM < 2 kB y orden FIR > 50 → IIR"*, *"si sin FPU → punto fijo Q15"*, *"si orden IIR > 2 → SOS"*. No las desarrollamos aquí; la base de conocimiento del agente sale de estas tablas.

### Preguntas guía

1. Para una **misma especificación** ($f_p$, $f_r$, $R_p$, $A_s$), ¿en qué se diferencian radicalmente un FIR y un IIR? Nombrá al menos tres criterios y decí cuál gana cada uno.
2. ¿Por qué la **fase lineal** es la regla dominante en el ECG, y qué propiedad del FIR la garantiza?
3. Calculá los **MACs/muestra** de un FIR $N=166$ y de un IIR-SOS de 3 secciones. ¿Cuántas veces más barato es el IIR?
4. ¿Por qué el FIR $N=166$ corre **holgado en ESP32** pero **no entra en Arduino UNO**? Mencioná RAM y FPU.
5. ¿Por qué en el ECG el **pasa-bajos es FIR** pero el **notch de 50 Hz es IIR/SOS**? ¿Qué criterio domina en cada uno?
6. ¿Cuándo elegirías **float32** y cuándo **punto fijo Q15**? ¿Qué cuidados extra exige el punto fijo (overflow, acumulador)?
7. ¿Por qué un IIR de orden > 2 en punto fijo se implementa **siempre como SOS** y no en forma directa?
8. Si tuvieras que elegir una **ventana FIR** para $A_s\approx 45$ dB y otra para $A_s\approx 70$ dB, ¿cuáles propondrías y por qué?


---

## 5. Simulación y validación (Octave y Python)

### En una frase

Antes de programar el filtro en el microcontrolador, lo **simulamos en la computadora** (Octave/MATLAB o Python) para *ver* y *medir* si realmente limpia el ECG sin deformarlo: graficamos su respuesta, lo aplicamos a una señal de prueba y calculamos métricas objetivas como SNR y RMSE.

### Definiciones clave

- **Simulación:** ejecutar el diseño del filtro en una PC con datos de prueba para comprobar que funciona, *antes* de gastar tiempo y dinero implementándolo en hardware. Es como probar una receta en casa antes de cocinarla en un restaurante.
- **Validación:** demostrar con *evidencia objetiva* (gráficos + números) que el filtro cumple las especificaciones (ver tabla de requerimientos del Paso 1, Sección 1).
- **Respuesta en frecuencia $H$:** función que dice cuánto deja pasar el filtro en cada frecuencia. Se grafica su **magnitud** (en decibelios, dB) y su **fase**.
- **Decibelio (dB):** escala logarítmica para la magnitud: $|H|_{\text{dB}} = 20\log_{10}|H|$. $0$ dB = pasa entero; $-40$ dB = lo reduce 100 veces; $-\infty$ = lo elimina.
- **Respuesta al impulso $h[n]$:** la "huella digital" del filtro en el tiempo. En un FIR son directamente sus coeficientes; su simetría garantiza la fase lineal (ver Sección 2).
- **Retardo de grupo:** cuántas muestras se atrasa cada frecuencia al pasar por el filtro. Si es **constante** (caso FIR de fase lineal), todas las partes de la onda se atrasan lo mismo y la forma del ECG no se distorsiona.
- **Diagrama polos-ceros (`zplane`):** mapa en el plano complejo $z$ con el círculo unitario. Los **ceros** (`o`) marcan frecuencias que el filtro anula; los **polos** (`x`) marcan resonancias. Regla de estabilidad IIR: **todos los polos dentro del círculo** ($|p|<1$).
- **FFT (Transformada Rápida de Fourier):** algoritmo que descompone una señal del **dominio del tiempo** al **dominio de la frecuencia**, mostrando qué frecuencias la componen (el "espectro").
- **PSD (densidad espectral de potencia):** cómo se reparte la potencia de la señal por frecuencia. La calculamos con el método de **Welch** (`pwelch`/`welch`), que promedia tramos y da un espectro más suave que la FFT cruda.
- **SNR (relación señal-ruido):** cuánta señal útil hay frente a cuánto ruido, en dB. Más alto = más limpio.
- **RMSE (raíz del error cuadrático medio):** error promedio entre la señal filtrada y la referencia limpia. Más bajo = más fiel.
- **Filtrado causal (`filter`/`lfilter`):** una sola pasada hacia adelante; es lo que ocurre en tiempo real (en el micro). Introduce retardo.
- **Filtrado de fase cero (`filtfilt`):** pasa el filtro hacia adelante y hacia atrás; cancela el retardo (fase cero) pero solo sirve *offline* (no en tiempo real).

### Desarrollo

#### ¿Para qué simular antes de implementar?

Implementar un filtro directamente en un microcontrolador (Sección 7) y descubrir recién ahí que distorsiona el QRS es caro y lento. La simulación nos deja **ver** el comportamiento del filtro y **medirlo** con números, todo en la PC y en segundos. Responde tres preguntas:

1. **¿El filtro hace lo que diseñé?** → respuesta en frecuencia, $h[n]$, polos-ceros.
2. **¿Limpia la señal sin romperla?** → ECG antes/después en el tiempo y su espectro.
3. **¿Cuánto mejora, objetivamente?** → métricas SNR y RMSE.

El diseño teórico (cómo se obtienen los coeficientes FIR e IIR) ya está en las Secciones 2 y 3. Aquí solo lo **probamos**.

#### Las herramientas

En **Octave/MATLAB** las funciones de PDS viven en el paquete `signal` (en Octave hay que cargarlo con `pkg load signal`; en MATLAB ya viene en la *Signal Processing Toolbox*). En **Python** usamos `numpy` (arrays y FFT), `scipy.signal` (filtros) y `matplotlib` (gráficos). Son casi un espejo:

| Tarea | Octave/MATLAB (`signal`) | Python (`scipy.signal` / `numpy`) |
|---|---|---|
| FIR por ventanas | `fir1` | `firwin` |
| FIR equiripple | `firpm` | `remez` |
| Dimensionar Kaiser | `kaiserord` | `kaiserord` |
| IIR prototipos | `butter`, `cheby1`, `cheby2`, `ellip` | `butter`, `cheby1`, `cheby2`, `ellip` |
| Orden IIR mínimo | `buttord`, `cheb1ord`… | `buttord`, `cheb1ord`… |
| Notch 50 Hz | `iirnotch` | `iirnotch` |
| Respuesta en frecuencia | `freqz` | `freqz` / `sosfreqz` |
| Retardo de grupo | `grpdelay` | `group_delay` |
| Polos-ceros | `zplane` | (a mano con `matplotlib`) |
| Filtrar causal | `filter`, `sosfilt` | `lfilter`, `sosfilt` |
| Filtrar fase cero | `filtfilt` | `filtfilt`, `sosfiltfilt` |
| FFT | `fft` | `numpy.fft.rfft` |
| PSD (Welch) | `pwelch` | `welch` |

#### Qué se grafica y cómo se interpreta

**1) Respuesta en frecuencia $|H|$ (dB) y fase.** Con `freqz` obtenemos un número complejo $H$ por cada frecuencia. La magnitud en dB dice cuánto atenúa; la fase dice cuánto desplaza. Qué buscar:
- En la **banda de paso** (0.5–40 Hz del ECG) la magnitud debe ser ≈ 0 dB (no toca la señal útil).
- En la **banda de rechazo** (≥ 50 Hz) debe caer al menos $A_s$ dB (en nuestro caso 40 dB).
- La **fase del FIR** debe verse como una **recta** (fase lineal); la del IIR es curva.

```matlab
fs = 500;
[H, f] = freqz(b_fir, 1, 1024, fs);        % FIR -> a = 1
subplot(2,1,1); plot(f, 20*log10(abs(H))); grid on;
  xlabel('Hz'); ylabel('|H| [dB]'); title('Magnitud');
subplot(2,1,2); plot(f, unwrap(angle(H))*180/pi); grid on;
  xlabel('Hz'); ylabel('Fase [°]');
```
```python
w, H = signal.freqz(h_fir, 1, worN=2048, fs=fs)
mag_db = 20*np.log10(np.abs(H) + 1e-12)    # +eps evita log10(0)
fase   = np.unwrap(np.angle(H)) * 180/np.pi
```

**2) Respuesta al impulso $h[n]$.** Con `impz(b,a)` (Octave) vemos las muestras de $h[n]$. En un FIR son sus propios coeficientes y se ven **simétricos** → esa simetría es la prueba visual de la fase lineal.

**3) Retardo de grupo.** Con `grpdelay`/`group_delay`. Para un FIR de fase lineal de orden $N$ es **constante e igual a $N/2$ muestras**: una línea horizontal. En el IIR es una curva (varía con la frecuencia), lo que deforma la morfología P-QRS-T.

```matlab
[gd, f] = grpdelay(b_fir, 1, 1024, fs);    % FIR -> recta horizontal en N/2
```
```python
w, gd = signal.group_delay((h_fir, 1), fs=fs)
```

**4) Diagrama polos-ceros (`zplane`).** Confirma la estabilidad del IIR: si algún polo cae fuera del círculo unitario ($|p|\ge 1$) el filtro es inestable. Octave tiene `zplane` nativo; en Python se dibuja a mano el círculo y se hace `scatter` de ceros y polos.

```matlab
zplane(b_iir, a_iir);    % o zplane(z, p) desde ceros/polos
```
```python
z, p, k = signal.sos2zpk(sos_iir)
# estable  <=>  todos los |p| < 1  (dentro del círculo unitario)
```

**5) ECG contaminado antes/después en el tiempo.** Graficamos la señal limpia de referencia, la contaminada y la filtrada superpuestas (con zoom a 1–2 s para ver los latidos). Qué buscar: que la salida filtrada se **superponga** a la referencia limpia y que el QRS conserve su forma puntiaguda.

**6) FFT / PSD del espectro.** Llevamos la señal al dominio de la frecuencia para *ver* el ruido. Antes de filtrar aparece un **pico claro en 50 Hz** (la red eléctrica) y energía en alta frecuencia (EMG). Después del filtro el pico de 50 Hz debe **desaparecer** y la energía > 40 Hz quedar muy reducida.

```matlab
N = numel(x);  faxis = (0:N-1)*fs/N;  half = 1:floor(N/2);
Xx = abs(fft(x))/N;  Xf = abs(fft(y_fir))/N;
plot(faxis(half), Xx(half), faxis(half), Xf(half));
xlabel('Hz'); ylabel('|X(f)|'); legend('contaminada','FIR');
```
```python
f  = np.fft.rfftfreq(x.size, 1/fs)
Xx = 20*np.log10(np.abs(np.fft.rfft(x)) + 1e-12)
# PSD suave por Welch:
fw, pxx = signal.welch(x, fs=fs, nperseg=1024)
```

**7) Métricas SNR y RMSE.** Convierten la inspección visual en números. Usamos la señal limpia de referencia `ref`/`clean` y tomamos su diferencia con la filtrada como "ruido residual":

$$
\mathrm{SNR_{dB}} = 10\log_{10}\!\frac{\sum \text{ref}^2}{\sum (\text{ref}-y)^2},
\qquad
\mathrm{RMSE} = \sqrt{\frac{1}{N}\sum (\text{ref}-y)^2}
$$

Un buen filtro **sube el SNR** y **baja el RMSE** respecto a la entrada.

#### `filter`/`lfilter` (causal) vs `filtfilt` (fase cero)

Hay dos formas de aplicar el filtro, y elegir bien es clave:

- **Causal — `filter` (Octave) / `lfilter` (Python), y `sosfilt` para IIR en SOS:** procesa muestra a muestra usando solo el pasado. Es **lo que realmente ocurre en el microcontrolador** (Sección 7) y en cualquier sistema en tiempo real. Introduce **retardo** (el FIR, $N/2$ muestras; el IIR, retardo variable por su fase no lineal). Para comparar muestra a muestra contra la referencia hay que **compensar** ese retardo.
- **Fase cero — `filtfilt` (FIR/IIR `ba`) / `sosfiltfilt` (IIR SOS):** aplica el filtro **hacia adelante y luego hacia atrás**. El retardo de ida se cancela con el de vuelta → **fase cero** (no desplaza la señal) y la atenuación se duplica ($|H|^2$). **No deforma la morfología P-QRS-T**, pero **no es causal**: necesita la señal completa, así que solo sirve para análisis *offline*, nunca en el micro.

**Regla práctica:** usá `filtfilt`/`sosfiltfilt` para el **análisis de validación** (no distorsiona el ECG) y `filter`/`lfilter`/`sosfilt` para **simular lo que hará el embebido** (causal, con retardo real). Requisito de `filtfilt`: la señal debe ser bastante más larga que el orden del filtro (`len(x) > 3*orden`).

### Ejemplo concreto (proyecto ECG)

El proyecto tiene dos scripts de referencia equivalentes (no se ejecutan aquí, solo se leen): `entrega_octave/ejemplos/procesar_senal.m` y `entrega_python/ejemplos/procesar_senal.py`. Ambos son **autónomos**: generan un ECG sintético, lo contaminan, lo filtran y miden. Datos canónicos: **fs = 500 Hz**, **5 s**, ruido de **50 Hz** + ruido blanco (EMG).

#### 1) Generar el ECG sintético con ruido de 50 Hz

El latido se modela como suma de cinco gaussianas (ondas P, Q, R, S, T) repetidas a ~1.2 Hz (≈ 72 lpm). Luego se le suma la interferencia de red y ruido blanco:

```matlab
fs = 500;  Tdur = 5;  t = (0:1/fs:Tdur-1/fs).';
% ... ecg = suma de gaussianas P-QRS-T por latido ...
ref     = ecg;                            % señal LIMPIA de referencia
interf  = 0.30 * sin(2*pi*50*t);          % interferencia de red 50 Hz
sig_emg = 0.08 * randn(numel(t),1);       % ruido blanco (EMG/HF)
x = ref + interf + sig_emg;               % señal CONTAMINADA de entrada
```
```python
def generar_ecg(fs=500, dur=5.0, fc_card=1.2, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(0, dur, 1/fs)
    # ecg_limpio = suma de gaussianas P-QRS-T por latido ...
    interf = 0.30 * np.sin(2*np.pi*50*t)          # red eléctrica 50 Hz
    ruido  = 0.05 * rng.standard_normal(t.size)   # ruido blanco
    ecg_ruidoso = ecg_limpio + interf + ruido
    return t, ecg_limpio, ecg_ruidoso
```

#### 2) Diseñar los filtros (coherente con Secciones 2 y 3)

Pipeline canónico: **Notch IIR 50 Hz** + **LP FIR Hamming fc = 40 Hz** (y, para comparar, un **LP IIR Chebyshev I en SOS**). El FIR sale de **orden 166** (Hamming), el IIR Chebyshev I de orden mucho menor:

```matlab
fnyq = fs/2;
% FIR LP Hamming fc=40, orden 166
N_fir = 166;  b_fir = fir1(N_fir, 40/fnyq, hamming(N_fir+1));
% IIR LP Chebyshev I como SOS
[N_iir, Wn] = cheb1ord(40/fnyq, 60/fnyq, 1, 40);
[z,p,k]     = cheby1(N_iir, 1, Wn);   sos_iir = zp2sos(z,p,k);
% Notch 50 Hz (biquad de 2.º orden)
Q = 35;  w0 = 50/fnyq;  [b_notch, a_notch] = iirnotch(w0, w0/Q);
```
```python
h_fir = signal.firwin(167, cutoff=40, fs=fs, window="hamming")  # 167 taps -> N=166
n, wn = signal.cheb1ord(wp=40, ws=60, gpass=1, gstop=40, fs=fs)
sos_lp = signal.cheby1(n, 1, wn, btype="low", output="sos", fs=fs)
b_n, a_n = signal.iirnotch(w0=50, Q=30, fs=fs)
sos_notch = signal.tf2sos(b_n, a_n)
```

#### 3) Aplicar los filtros — causal vs fase cero

El script de Octave usa `fftfilt` (equivale a `filter(b_fir,1,x)` pero más rápido) y compensa el retardo $N/2$; el de Python muestra *ambos* caminos en paralelo:

```matlab
% FIR por overlap-add y compensación del retardo lineal N/2:
y_fir_raw = fftfilt(b_fir, x);  d = N_fir/2;
y_fir = [y_fir_raw(d+1:end); zeros(d,1)];
% IIR: Notch (filter) seguido de LP Chebyshev (sosfilt):
y_notch = filter(b_notch, a_notch, x);
y_iir   = sosfilt(sos_iir, y_notch);
```
```python
# CAUSAL (lo que ocurre en el micro): lfilter / sosfilt
fir_causal = signal.lfilter(h_fir, 1, signal.sosfilt(sos_notch, ecg_ruidoso))
iir_causal = signal.sosfilt(sos_lp,  signal.sosfilt(sos_notch, ecg_ruidoso))
# FASE CERO (offline, no deforma P-QRS-T): filtfilt / sosfiltfilt
ecg_sin_red = signal.sosfiltfilt(sos_notch, ecg_ruidoso)
fir_fase0   = signal.filtfilt(h_fir, 1, ecg_sin_red)
iir_fase0   = signal.sosfiltfilt(sos_lp,  ecg_sin_red)
```

#### 4) Medir SNR y RMSE (descartando los bordes/transitorio)

```matlab
g = (round(0.3*fs)+1):(Ntot-round(0.3*fs));     % zona útil sin transitorios
snr_db = @(y) 10*log10( sum(ref(g).^2) / sum((y(g)-ref(g)).^2) );
rmse   = @(y) sqrt( mean((y(g)-ref(g)).^2) );
SNR_in = snr_db(x);  SNR_fir = snr_db(y_fir);  SNR_iir = snr_db(y_iir);
```
```python
def snr(clean, x):
    noise = clean - x
    return 10*np.log10(np.sum(clean**2) / (np.sum(noise**2) + 1e-12))
def rmse(a, b):
    return np.sqrt(np.mean((a - b)**2))
```

Ambos scripts imprimen una **tabla comparativa FIR vs IIR** con: orden, MACs/muestra (FIR ≈ $N+1 = 167$; IIR-SOS ≈ $5\times$secciones), fase (lineal vs no lineal), retardo de grupo (constante $N/2$ vs variable), estabilidad y el SNR/RMSE de salida. La lectura canónica: **el FIR conserva la morfología P-QRS-T** (fase lineal) a costa de muchos MACs; **el IIR logra un resultado similar con muchísimos menos MACs**, pero introduce distorsión de fase (criterios completos en la Sección 4).

> Nota: los valores numéricos exactos de SNR/RMSE los produce el script al correr (no se ejecuta aquí). Cualitativamente: el SNR de salida sube respecto al de entrada y el RMSE baja; la fase cero da mejores números que el modo causal.

### Procedimiento práctico

1. **Preparar el entorno.** En Octave: `pkg load signal` (protegido con `if exist('OCTAVE_VERSION','builtin')`). En Python: `import numpy as np`, `from scipy import signal`, `import matplotlib.pyplot as plt` (en un *venv*, sin instalar nada aquí).
2. **Generar la señal de prueba.** Crear `ref`/`ecg_limpio` (ECG sintético P-QRS-T) y contaminarla: `x = ref + 0.30*sin(2*pi*50*t) + ruido_blanco`. Fijar la semilla del aleatorio para reproducibilidad.
3. **Diseñar los filtros** (con los métodos de las Secciones 2 y 3): FIR LP Hamming (`fir1`/`firwin`, orden 166), IIR Chebyshev I en SOS (`cheb1ord` → `cheby1` → `zp2sos`/`output='sos'`) y notch 50 Hz (`iirnotch`).
4. **Analizar cada filtro antes de aplicarlo:** `freqz` (magnitud dB + fase), `grpdelay`/`group_delay` (verificar retardo constante en el FIR), `zplane`/polos-ceros (verificar $|p|<1$ en el IIR), `impz` (ver $h[n]$ simétrico).
5. **Aplicar los filtros** en ambos modos: causal (`filter`/`lfilter`/`sosfilt`) compensando el retardo $N/2$ del FIR, y fase cero (`filtfilt`/`sosfiltfilt`) para el análisis que no debe deformar.
6. **Graficar el tiempo antes/después** (referencia + contaminada + filtrada, con zoom a 1–2 s) y comprobar que el QRS se conserva.
7. **Graficar el espectro antes/después** con `fft` y `pwelch`/`welch`; verificar que el **pico de 50 Hz desaparece** y la energía > 40 Hz cae.
8. **Calcular SNR y RMSE** sobre la zona útil (descartando los bordes/transitorio) y armar la **tabla comparativa FIR vs IIR**. Confirmar que el SNR sube y el RMSE baja.

### Preguntas guía

1. ¿Por qué conviene simular y validar el filtro en la PC antes de implementarlo en el ESP32? Nombrá tres cosas concretas que se verifican.
2. ¿Qué función usás para obtener la respuesta en frecuencia y cómo pasás su magnitud a decibelios? ¿Qué esperás ver en la banda 0.5–40 Hz y en 50 Hz?
3. ¿Qué es el retardo de grupo y por qué para un FIR de fase lineal de orden $N$ vale $N/2$ y es constante? ¿Por qué eso importa en un ECG?
4. En el diagrama polos-ceros, ¿cómo se reconoce que un filtro IIR es estable?
5. ¿Qué diferencia hay entre `filter`/`lfilter` y `filtfilt`/`sosfiltfilt`? ¿Cuál representa lo que ocurre en el microcontrolador y cuál usarías para no deformar la morfología P-QRS-T?
6. ¿Cómo se ve la interferencia de red de 50 Hz en el espectro (FFT/PSD) antes y después del notch?
7. Escribí las fórmulas de SNR (dB) y RMSE. ¿Qué le pasa a cada métrica cuando el filtrado es bueno?
8. ¿Por qué el ejemplo descarta los bordes de la señal antes de calcular las métricas?


---

## 6. El agente de decisión asistido por IA

### En una frase

Un **agente de decisión** es un pequeño programa que recibe las restricciones de tu proyecto (memoria, velocidad del micro, si hace falta fase lineal, etc.) y te **recomienda automáticamente** si conviene un filtro **FIR o IIR** y con qué **estructura** implementarlo (DF I, DF II, **SOS** o lattice), explicando por qué.

### Definiciones clave

- **Agente de decisión / sistema experto:** componente de software que **mapea restricciones de ingeniería a una recomendación de diseño**, imitando el razonamiento de un especialista. Importante: **no diseña** el filtro (eso es el Paso 2, ver Secciones 2 y 3); solo **decide la familia y la estructura** y **justifica** la elección.
- **FIR (Finite Impulse Response):** filtro de respuesta al impulso finita; garantiza **fase lineal** si su `h[n]` es simétrico, y es **siempre estable**, pero suele necesitar **orden alto** (ver Sección 2).
- **IIR (Infinite Impulse Response):** filtro de respuesta al impulso infinita; logra la misma selectividad con **orden mucho menor**, pero su fase no es lineal y hay que cuidar la **estabilidad** (ver Sección 3).
- **Estructura de realización:** la "forma" concreta de implementar el filtro en código. `DF I`/`DF II` (formas directas), **`SOS`** (*Second-Order Sections*: cascada de secciones de 2.º orden o *biquads*) y `lattice` son las opciones. SOS es la recomendada para IIR cuando la precisión numérica importa (ver Sección 4).
- **Variable lingüística / grado de pertenencia:** en lógica difusa, un valor borroso (p. ej. "ruido alto") con un número $\mu \in [0,1]$ que indica **cuánto** pertenece a esa categoría, en lugar de un sí/no rígido.
- **MLP (perceptrón multicapa):** una **red neuronal** simple con capas de neuronas; aprende a clasificar a partir de ejemplos.
- **LLM (modelo de lenguaje grande):** modelo de IA generativa (como Claude o GPT) al que se le pide la decisión "en lenguaje natural" mediante un *prompt* y se valida su respuesta.
- **Confianza:** número en $[0,1]$ que acompaña a la recomendación e indica cuán segura es.

### Desarrollo

#### 6.1 ¿Qué problema resuelve el agente?

Elegir entre FIR e IIR (y su estructura) implica balancear varios factores a la vez: ¿hay memoria suficiente?, ¿el micro tiene unidad de punto flotante (**FPU**)?, ¿la aplicación exige preservar la forma exacta de la señal (fase lineal)?, ¿la banda de transición es estrecha? Un experto lo resuelve "de cabeza" con reglas aprendidas. El **agente automatiza ese razonamiento**: recibe las restricciones y entrega una recomendación trazable. Esto corresponde al **Paso 4** del examen.

Formalmente es una función que toma un vector de entrada $\mathbf{x}$ y produce una salida $\mathbf{y}$:

$$
\text{Agente}: \mathbf{x} \in \mathcal{X} \;\longrightarrow\; \mathbf{y} \in \mathcal{Y}
$$

#### 6.2 Variables de entrada $\mathbf{x}$

| Variable | Símbolo | Tipo / rango típico | De dónde sale |
|----------|---------|---------------------|---------------|
| Frecuencia de muestreo | `fs` | Hz (10 … 5000) | Paso 1 (Nyquist) |
| Memoria del micro | `RAM`, `Flash` | kB (2 … 512) | plataforma |
| Cómputo disponible | `MIPS` / `MHz` (con/sin FPU) | 16 … 240 MHz | plataforma |
| Fase lineal requerida | `fase_lineal` | booleano (sí/no) | Paso 1 |
| Nivel de ruido / SNR de entrada | `SNR_in` | dB (0 … 40) | Paso 1 |
| Latencia admisible | `latencia` | {baja, media, alta} | requisito |
| Pendiente de transición | `transicion` | {estrecha, amplia} → $\Delta f$ | Paso 1 |

A veces se añade `orden_fir_est`, una **estimación del orden FIR** necesario para cumplir la máscara (en Octave se calcula con una regla práctica tipo Harris, $N \approx 3.3\,f_s/\Delta f$).

#### 6.3 Salidas $\mathbf{y}$

| Salida | Dominio | Comentario |
|--------|---------|------------|
| Recomendación | `{FIR, IIR}` | la decisión principal |
| Estructura | `{DF I, DF II, SOS, lattice}` | cómo realizarlo |
| Justificación | texto / reglas activadas | trazabilidad |
| Confianza | $[0,1]$ | cuán segura es |

#### 6.4 El "reglero" de referencia

Todas las estrategias se apoyan en el **mismo conjunto de criterios de ingeniería** (ver Sección 4). Las cuatro reglas centrales que pide el enunciado son:

- **Fase lineal estricta** (preservar morfología, p. ej. ECG) → **FIR**.
- **RAM < 2 kB** y **orden FIR estimado > 50** → **IIR** (en **SOS**).
- **Estabilidad numérica crítica sin float/FPU** → **IIR** en **SOS** (cada *biquad* se cuantiza por separado, baja sensibilidad de coeficientes).
- **Transición exigente (estrecha) con cómputo suficiente** → **IIR** (p. ej. prototipo **Elíptico**) de orden adecuado.

La idea clave: estas reglas son la **"fuente de verdad"**. Algunas estrategias las escriben a mano (reglas, fuzzy, LLM); otras las **aprenden** de datos generados con esas mismas reglas (árbol, MLP).

#### 6.5 Las 5 estrategias para construir el agente

El enunciado pide **elegir y justificar una** estrategia. Las cinco difieren en **cómo se genera** el agente:

```
                ┌──────────── conocimiento experto escrito a mano
1. Reglas IF-THEN  ── el experto escribe las reglas
3. Lógica difusa   ── reglas + grados de pertenencia
                ├──────────── aprendizaje a partir de datos
2. Árbol decisión  ── se entrena (fit) sobre un dataset
5. Red neuronal MLP── se entrena por backpropagation
                └──────────── delegación a un modelo de lenguaje
4. API IA generativa ── prompt + validación de la respuesta
```

**(1) Reglas IF-THEN (sistema experto).** Se construye **a mano**: el especialista traduce cada criterio a una sentencia `SI <condición> ENTONCES <conclusión>`, con prioridad y confianza. Un **motor de inferencia** recorre las reglas por prioridad (encadenamiento hacia adelante) y la primera que dispara fija la familia/estructura.
*Ventajas:* totalmente **interpretable**, **determinista**, no necesita datos, **ligero** (se puede embeber en el micro). *Desventajas:* no generaliza fuera de lo previsto; fronteras "duras" (todo-o-nada); mantenimiento manual si crece.

**(2) Árbol de decisión (scikit-learn).** Un clasificador que parte el espacio en nodos eligiendo, en cada uno, la variable y el umbral que mejor separan FIR de IIR (según impureza **Gini** $G = 1 - \sum_k p_k^2$ o **entropía**). Se **entrena** (`fit`) sobre un dataset etiquetado; como no hay datos reales, se **etiqueta sintéticamente con las reglas** y el árbol las "destila" y suaviza.
*Ventajas:* interpretable (se exporta a reglas `if/else`), captura interacciones, inferencia rapidísima. *Desventajas:* necesita dataset; riesgo de **overfitting** si no se limita `max_depth`; fronteras "en escalera".

**(3) Lógica difusa (fuzzy).** Sustituye las fronteras duras por **grados de pertenencia** $\mu \in [0,1]$. Variables lingüísticas (ruido bajo/medio/alto) descritas por funciones de pertenencia (triangulares/trapezoidales); un motor **Mamdani** combina reglas difusas y **defuzzifica** (centroide) para dar una preferencia continua hacia IIR. Etapas: **fuzzificación → inferencia → defuzzificación**.
*Ventajas:* decisiones **suaves** y confianza continua; robusto a entradas ambiguas; sin datos. *Desventajas:* diseñar las funciones de pertenencia es **artesanal**; más parámetros; coste de defuzzificación.

**(4) IA generativa vía API / LLM (Claude / GPT).** Se **delega** la decisión a un modelo de lenguaje accedido por API. No se programan reglas: se hace ***prompt engineering*** (un *system prompt* con rol + criterios + formato de salida JSON) y se **valida** la respuesta.
*Ventajas:* **justificación rica** en lenguaje natural; maneja casos poco previstos; rápido de prototipar. *Desventajas:* **no determinista** (misma entrada, salida variable), tiene **latencia y coste**, **requiere conexión** ⇒ **no apto para tiempo real embebido**; hay que **validar** la salida (alucinaciones).

**(5) MLP (red neuronal entrenada con datos sintéticos).** Una red con capa de entrada (8 variables), 1–2 capas ocultas (ReLU) y salida softmax que da $P(\text{FIR}), P(\text{IIR})$. Se **entrena por backpropagation** minimizando la entropía cruzada, sobre el **mismo dataset sintético** del árbol.
*Ventajas:* aprende fronteras no lineales suaves; confianza continua (softmax). *Desventajas:* **caja negra** (no interpretable), necesita más datos, difícil de justificar. Para este problema (pocas variables, reglas claras) el MLP es **sobre-ingeniería**: se incluye por completitud.

> **Conclusión de uso:** para **entregar y embeber**, la estrategia **1 (reglas)** es la mejor (interpretable, determinista, ligera). El **árbol** y la **fuzzy** enriquecen el documento; el **LLM** sirve en **fase de diseño** (explorar/justificar/documentar), no en el micro; el **MLP** es referencia.

### Ejemplo concreto (proyecto ECG)

Recordá los hechos canónicos del proyecto ECG (ver Sección 1): **fs = 500 Hz**, banda útil 0.5–40 Hz, se usa **Notch IIR 50 Hz + Pasa-bajos FIR** (Hamming, **N = 166**). La fase lineal **importa** porque preserva la morfología P-QRS-T (diagnóstico).

#### 6.6 Agente IF-THEN (Python, real del proyecto)

Este es el núcleo embebible, escrito **solo con la biblioteca estándar** (sin numpy/sklearn). El motor recorre las reglas por prioridad y la primera que dispara fija la salida:

```python
def recomendar_reglas(specs: dict) -> dict:
    ram = float(specs.get("ram_kB", 256))
    mhz = float(specs.get("mhz", 240))
    fpu = bool(specs.get("fpu", True))
    fase_lineal = bool(specs.get("fase_lineal", False))
    transicion = str(specs.get("transicion", "amplia")).lower()
    orden_fir = int(specs.get("orden_fir_est", 0))

    res = Resultado()
    def fijar(regla, tipo, estructura, conf, just):
        res.reglas_activadas.append(regla)
        if res.tipo == "INDEFINIDO":          # la 1.ª que dispara fija la familia
            res.tipo, res.estructura = tipo, estructura
            res.confianza, res.justificacion = conf, just

    computo_suficiente = fpu or mhz >= 80

    # R1 — fase lineal estricta -> FIR (preserva P-QRS-T)
    if fase_lineal and not (ram < 2 and orden_fir > 50):
        fijar("R1", "FIR", "DF", 0.95, "Fase lineal estricta: solo el FIR ...")
    # R2 — poca RAM + FIR de orden alto -> IIR SOS
    if ram < 2 and orden_fir > 50:
        fijar("R2", "IIR", "SOS", 0.90, "RAM < 2 kB con orden FIR > 50 ...")
    # R3 — estabilidad crítica sin float -> IIR SOS
    if (not fpu) and orden_fir > 30:
        fijar("R3", "IIR", "SOS", 0.90, "Sin FPU/float y orden FIR alto ...")
    # R4 — transición estrecha + cómputo suficiente -> IIR (elíptico) SOS
    if transicion == "estrecha" and computo_suficiente:
        fijar("R4", "IIR", "SOS", 0.85, "Transición estrecha con cómputo ...")
    # ... R5, R6 ...
    # R7 — red de seguridad
    if res.tipo == "INDEFINIDO":
        fijar("R7", "FIR", "DF", 0.50, "Ninguna regla específica disparó ...")
    return res.as_dict()
```

El mismo agente existe en **Octave/MATLAB** (`agente_decision.m`), con encadenamiento por `if ... return` y una estimación interna del orden FIR ($N \approx 3.3\,f_s/\Delta f$). Para el caso ECG (`fase_lineal = true`) dispara **R1** y devuelve:

```matlab
% R1: Fase lineal estricta -> FIR (preserva morfologia, p.ej. P-QRS-T)
if specs.fase_lineal
  rec.tipo       = 'FIR';
  rec.estructura = 'DF simetrico';
  rec.confianza  = 0.95;
  return;
end
```

#### 6.7 Agente LLM (Python) — solo en fase de diseño

> **MUY IMPORTANTE:** este código **NO se debe ejecutar aquí**: no llames a ninguna API real, no necesitás clave ni conexión para estudiarlo. Se muestra para **entender la estrategia 4**. En producción requiere `ANTHROPIC_API_KEY` en el entorno (nunca se escribe la clave en el código) y, por su latencia/coste/no-determinismo, **no sirve para el micro en tiempo real**.

El *system prompt* fija el rol y **los mismos criterios** del reglero; el *user prompt* inyecta las variables del caso; se pide **JSON estricto** y se valida:

```python
SYSTEM_PROMPT = (
    "Eres un especialista en PDS. Recomiendas FIR o IIR y una estructura "
    "(DF I, DF II, SOS o lattice).\n"
    "Criterios: fase lineal estricta => FIR; RAM<2kB y ordenFIR>50 => IIR; "
    "estabilidad critica sin FPU => IIR en SOS; transicion estrecha con "
    "computo suficiente => IIR. Devuelve UNICAMENTE JSON: "
    "{recomendacion, estructura, justificacion, confianza}."
)

def recomendar_llm(specs: dict, modelo: str = "claude-opus-4-8") -> dict:
    client = Anthropic()                 # toma la clave de ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=modelo, max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": construir_user_prompt(specs)}],
    )
    texto = next((b.text for b in msg.content if b.type == "text"), "")
    return validar_salida(texto)         # parsea y valida el JSON (anti-alucinación)
```

La **validación** comprueba que `recomendacion ∈ {FIR, IIR}`, que la estructura es texto y que la confianza está en $[0,1]$; si algo falla, se reintenta o se **cae al agente de reglas** (*fallback*). La salida esperada para un caso ECG sería:

```json
{
  "recomendacion": "FIR",
  "estructura": "DF",
  "justificacion": "Fase lineal estricta para preservar P-QRS-T; FIR por simetria de h[n].",
  "confianza": 0.92
}
```

#### 6.8 Datos sintéticos (para árbol y MLP)

Como no hay un dataset real de decisiones FIR/IIR, se **fabrica**: se muestrean combinaciones de variables y se **etiquetan con las reglas** de ingeniería. El clasificador "destila" esas reglas y generaliza a casos intermedios. Conviene **balancear** clases, agregar algo de ruido y separar train/test.

### Procedimiento práctico

1. **Definí las entradas** del caso en un diccionario `specs`: `fs`, `ram_kB`, `mhz`, `fpu`, `fase_lineal`, `snr_in_dB`, `latencia`, `transicion` y, si lo usás, `orden_fir_est`.
2. **Elegí una estrategia** y justificala. Para entregar/embeber: **reglas IF-THEN** (estrategia 1). Para enriquecer el informe: agregá árbol + fuzzy + LLM.
3. **Reglas (estrategia 1):** llamá a `recomendar_reglas(specs)` en Python (o `agente_decision(specs)` en Octave). Leé `tipo`, `estructura`, `confianza`, `justificacion` y `reglas_activadas` para **trazar** la decisión.
4. **Árbol (estrategia 2):** generá el dataset con `generar_dataset(n=4000)`, entrená con `entrenar_arbol()` y mirá las reglas aprendidas con `export_text`. Comprobá `accuracy` ≈ 1 en datos limpios; limitá `max_depth` (4–6) para evitar overfitting.
5. **LLM (estrategia 4) — solo lectura aquí:** entendé el flujo *system prompt → user prompt → JSON → validación*. **No ejecutes** la llamada en este entorno.
6. **Validá con ≥ 3 escenarios** (siguiente bloque) y verificá que cada salida coincide con lo esperado por el reglero (Sección 4) y con los Pasos 1–3.
7. **Coherencia final:** si una estrategia de aprendizaje (árbol/MLP) **no** reproduce los escenarios, es señal de **dataset mal balanceado** o **overfitting**: revisá el balanceo y `max_depth`.

#### 6.9 Validación con los 3 escenarios del enunciado

La validación es obligatoria: con al menos **3 escenarios de restricciones distintas**, las salidas deben ser **coherentes** con los criterios (Sección 4) y con los Pasos 1–3 (Secciones 1–3). Todas las estrategias bien construidas deben dar la **misma recomendación**.

| Escenario | Entrada clave | Salida esperada | Regla |
|-----------|---------------|-----------------|-------|
| **(a) ECG diagnóstico** | `fase_lineal = sí` (preservar P-QRS-T), FPU disponible | **FIR / DF** (fase lineal por simetría de `h[n]`) | R1 |
| **(b) Arduino UNO** | 2 kB RAM, `orden_fir > 50`, **sin FPU** | **IIR / SOS** (FIR inviable; SOS por estabilidad en punto fijo) | R2, R3 |
| **(c) Transición exigente** | `transicion = estrecha`, ESP32 con FPU ≥ 160 MHz | **IIR (Elíptico) / SOS** (pendiente abrupta con orden bajo) | R4 |

**Por qué debe ser coherente con los Pasos 1–3:** la recomendación del agente no es arbitraria. El escenario (a) reproduce exactamente la elección FIR del proyecto ECG (fase lineal preserva la morfología clínica → coherente con el Paso 1 y el diseño FIR del Paso 2). Los escenarios (b) y (c) muestran cuándo el mismo criterio **inclina la balanza hacia IIR** (memoria/cómputo limitados o transición muy exigente), lo que coincide con la comparación FIR vs IIR de la simulación (Paso 3, Sección 5). Si el agente recomendara algo distinto a lo que dictan esos pasos, **estaría mal**.

### Preguntas guía

1. ¿Qué hace exactamente un agente de decisión y qué **NO** hace (frente al diseño del filtro de los Pasos 2 y 3)?
2. Enumerá las **variables de entrada** y las **salidas** del agente. ¿De dónde sale cada entrada?
3. Para el caso ECG (`fase_lineal = sí`), ¿qué regla se dispara y qué recomienda el agente? ¿Por qué la fase lineal lleva a FIR?
4. Explicá las **5 estrategias** y, para cada una, una ventaja y una desventaja. ¿Cuál elegirías para **embeber** en el micro y por qué?
5. ¿Por qué el árbol y el MLP necesitan un **dataset sintético** y cómo se **etiqueta**? ¿Qué riesgo aparece si no se limita `max_depth`?
6. ¿Por qué el agente **LLM no es apto para tiempo real** en el micro? ¿Qué validaciones se hacen sobre su salida JSON y qué *fallback* se usa?
7. ¿Cuándo conviene **IIR en SOS** en lugar de FIR? Citá los escenarios (b) y (c).
8. ¿Por qué la salida del agente debe ser **coherente con los Pasos 1–3**? ¿Qué indicaría que un árbol/MLP no reproduce los 3 escenarios?


---

## 7. Implementación embebida en ESP32

### En una frase

Tomamos los filtros diseñados y simulados en una computadora (notch IIR 50 Hz + pasa-bajos FIR 40 Hz) y los **hacemos correr en tiempo real dentro de un microcontrolador ESP32**, que adquiere la señal de ECG muestra a muestra a 500 Hz, la filtra al vuelo y entrega la salida limpia, todo con apenas unos kilobytes de memoria y un reloj de cientos de MHz.

### Definiciones clave

- **Microcontrolador (µC):** una computadora completa en un solo chip (procesador + memoria + periféricos) pensada para tareas dedicadas. A diferencia de una PC, tiene recursos muy limitados y corre **un solo programa** sin sistema operativo (o uno mínimo).
- **ESP32:** el microcontrolador que usamos. Tiene núcleo Xtensa LX6/LX7 a 160–240 MHz, **FPU** (ver abajo), 320 kB+ de RAM, 4 MB de Flash y un **ADC** de 12 bits. Es "grande" para los estándares embebidos.
- **Arduino UNO:** µC de contraste, mucho más modesto: 16 MHz, 2 kB de RAM, **sin FPU**. Sirve para ver qué cambia cuando los recursos escasean.
- **FPU (Floating Point Unit):** unidad de hardware que hace cuentas con números decimales (*float*) en ~1 ciclo de reloj. Si el µC **no** tiene FPU, esas cuentas se "emulan" por software y son ~100× más lentas.
- **ADC (Analog-to-Digital Converter):** circuito que convierte un voltaje analógico (la señal del ECG saliendo del amplificador) en un número entero. El del ESP32 es de **12 bits**, o sea entrega valores de 0 a 4095.
- **fs (frecuencia de muestreo):** cuántas muestras por segundo tomamos. Aquí **fs = 500 Hz**, fijada en el diseño (Secciones 2–4). Eso obliga a tomar una muestra cada **T = 1/fs = 2 ms = 2000 µs**.
- **Período de muestreo (T):** el tiempo entre dos muestras consecutivas. Es la "cita" que el µC debe cumplir con precisión: cada 2 ms, sí o sí, una muestra nueva.
- **MAC (Multiply-Accumulate):** la operación básica del filtrado, "multiplicar y sumar" ($acc \mathrel{+}= h \cdot x$). El coste de un filtro se mide en MACs por muestra.
- **Punto flotante (float32):** representación de números decimales con coma "que flota" (IEEE-754, 32 bits). Rango dinámico enorme; casi nunca se desborda.
- **Punto fijo / formato Q (Qm.n):** representar decimales usando **enteros**. Se reservan $m$ bits para la parte entera y $n$ bits para la fraccionaria; el valor real es $x_{\text{real}} = x_{\text{int}} \cdot 2^{-n}$. Se usa cuando no hay FPU (ver Sección 4, §5).
- **Buffer circular (ring buffer):** un array que se reusa "en círculo": al llenarse, la escritura vuelve al principio. Es la forma natural de guardar las últimas $N$ muestras que necesita un FIR (su *línea de retardo*).
- **ISR (Interrupt Service Routine):** una función que el hardware dispara automáticamente cuando ocurre un evento (aquí, el "tic" de un timer cada 2 ms). Interrumpe lo que el µC esté haciendo, corre, y devuelve el control.
- **Aliasing:** distorsión que aparece cuando una señal contiene frecuencias mayores a fs/2 (aquí 250 Hz) y se muestrea igual: esas frecuencias se "disfrazan" de otras más bajas y contaminan la señal. Se evita con un filtro analógico **antes** del ADC.

### Desarrollo

#### 7.1 ¿Por qué llevar el filtro al microcontrolador? ¿Qué cambia respecto de la simulación?

En la simulación (Sección 5, Octave/Python) el filtro vive cómodo: hay toda la señal grabada en memoria, RAM de sobra, números *double* de 64 bits y nadie corre contra el reloj. Llamamos a `filter`/`lfilter` con la señal completa y obtenemos el resultado de golpe (procesamiento *offline*, "fuera de línea").

En un equipo real de ECG eso no sirve: la señal **llega muestra a muestra, ahora mismo**, y hay que filtrarla en tiempo real con recursos minúsculos. Lo que cambia al pasar de la simulación al embebido:

1. **De offline a tiempo real (streaming):** ya no tenemos la señal entera. Procesamos cada muestra apenas llega, sin ver el futuro. El filtro debe ser **causal** (solo usa muestras presentes y pasadas) y terminar su cuenta **antes** de que llegue la siguiente (en menos de 2 ms).
2. **De double a float (o a entero):** la PC usa 64 bits; el µC usa *float32* de 32 bits (ESP32) o incluso enteros (µC sin FPU). Aparecen **errores de cuantización** que en la PC eran despreciables.
3. **Adquisición real:** la señal entra por un **ADC** con ruido y resolución finita (12 bits), no es un vector perfecto generado por software.
4. **Determinismo del muestreo:** hay que garantizar que las muestras se tomen **exactamente** cada 2 ms. Si el instante varía (*jitter*), eso mete ruido equivalente a aliasing.
5. **Presupuesto de cómputo y memoria:** todo entra en kilobytes y en un reloj limitado. Hay que elegir filtro y estructura con eso en mente (Sección 4).

#### 7.2 El hardware: ESP32 vs Arduino UNO

El diseño teórico de la Sección 2 nos dio un **FIR Hamming de N = 166 taps** (orden 165) — un filtro "largo". ¿Cabe y corre en el µC? Depende de la placa.

| Característica | **ESP32** | **Arduino UNO** | Consecuencia |
|---|---|---|---|
| Reloj | 160–240 MHz | 16 MHz | A 240 MHz hay ~480.000 ciclos por muestra (2 ms); en UNO solo ~32.000 |
| RAM | 320 kB+ | 2 kB | El FIR N=166 (~1.3 kB entre coef. y estados) es trivial en ESP32; en UNO **no entra cómodo** |
| Flash (programa) | 4 MB | 32 kB | Coeficientes y código caben holgados en ambos, pero ESP32 sobra |
| **FPU** | **Sí (hardware)** | **No** | ESP32 usa **float32** (1 ciclo/MAC); UNO debe emular float (~100× lento) → inviable a 500 Hz |
| ADC | SAR 12 bits (0–4095) | SAR 10 bits (0–1023) | Más bits = menos ruido de cuantización |
| Timer | `hw_timer_t` (base APB 80 MHz) | Timer de 8/16 bits | Muestreo determinista a 500 Hz exactos |

**Presupuesto de cómputo (regla de la Sección 4):** debe cumplirse $\text{MACs}_{\text{filtro}} \cdot f_s \ll$ MAC/s disponibles, dejando margen. Para el FIR N=166:

$$
166 \text{ MACs/muestra} \times 500 \text{ Hz} = 83\,000 \text{ MAC/s} = 83 \text{ kMAC/s}
$$

El ESP32 con FPU tiene **decenas de miles de MACs disponibles por muestra**, así que usa menos del 5 % de su capacidad: queda holgura > 95 % para el ADC, la ISR y la lógica. Por eso el ESP32 **admite FIR de orden alto y aritmética float** sin sudar.

En **Arduino UNO**, en cambio, el FIR largo no entra en RAM y, sin FPU, el float es inviable. Allí la estrategia (Sección 4) es **IIR de orden bajo en cascada de secciones de 2.º orden (SOS) y punto fijo Q15**: ~5 MACs por sección, cabe en memoria y ciclos. Se pierde la fase lineal exacta del FIR (compensable *offline* con `filtfilt` si hace falta).

> **Conexión con la Sección 4:** esto es exactamente la regla `sin_FPU → punto fijo Q15` y `RAM < 2 kB AND orden_FIR > 50 → IIR`. El criterio de plataforma sale de allí; aquí lo materializamos en código.

#### 7.3 Adquisición: ADC, muestreo por timer/ISR, y por qué fs=500 Hz fija el período

La señal de ECG sale del *front-end* analógico (amplificador + filtro) y entra al **ADC** del ESP32, que la convierte en números de 12 bits (0–4095). Pero el **cuándo** muestreamos importa tanto como el qué.

**fs = 500 Hz fija el período:** como tomamos 500 muestras por segundo, el tiempo entre muestras es $T = 1/500 = 2$ ms exactos. El µC debe presentarse a esa cita con máxima puntualidad. ¿Por qué tanta exigencia? Porque el diseño del filtro (Secciones 2–3) supone que las muestras están **uniformemente espaciadas** a 2 ms. Si llegan a destiempo, el filtro "cree" que la señal es otra.

Hay dos formas de cumplir la cita:

- **Polling (sondeo):** preguntar en el `loop()` "¿ya pasaron 2 ms?" una y otra vez. Es simple, pero el instante exacto **varía** según lo que el programa esté haciendo (jitter alto). Solo sirve para prototipos o fs bajas no críticas.
- **Interrupción por timer (lo recomendado):** se configura un **timer de hardware** para que cada 2 ms dispare una **ISR**. La ISR corre con prioridad, independientemente de lo que el `loop()` haga → muestreo **determinista**, a 500 Hz exactos. El jitter casi desaparece.

> **Por qué importa el jitter:** un muestreo a destiempo equivale a ruido y a aliasing (Sección 4, §7). Por eso elegimos timer-ISR, no polling.

**Regla de oro de la ISR: que sea corta.** La ISR **solo** adquiere la muestra cruda (lee el ADC) y marca un *flag* (`hay_muestra = true`). El filtrado pesado (la convolución FIR de 166 multiplicaciones) se hace **fuera** de la ISR, en el `loop()`. Si pusiéramos el filtro dentro de la ISR, esta tardaría demasiado y podríamos perder la siguiente interrupción.

El código además ofrece dos interruptores de compilación (`#define`) para flexibilidad:
- `USAR_TIMER_HW`: timer de hardware (preciso) **o** muestreo por `micros()` (portable a otras placas).
- `USAR_ADC`: leer el ADC real **o** usar un generador de señal de prueba por software (para validar sin hardware).

#### 7.4 Buffers: el buffer circular como línea de retardo del FIR

Un filtro **FIR** necesita, para cada salida, las últimas $N$ muestras de entrada: $x[n], x[n-1], \dots, x[n-N+1]$. A esa "memoria de muestras pasadas" se la llama **línea de retardo** (*delay line*).

La forma ingenua sería: guardar las muestras en un array y, en cada paso, **desplazar** todo el array una posición (tirar la más vieja, meter la nueva). Pero desplazar $N$ elementos cada 2 ms es un desperdicio.

La forma elegante es el **buffer circular (ring)**: un array de $N$ posiciones donde:
- se **escribe** la muestra nueva en una posición "cabeza" (`fir_idx`),
- la cabeza **avanza** módulo $N$ (al llegar al final, vuelve a 0),
- la convolución **recorre el ring hacia atrás** desde la cabeza para emparejar $x[n-k]$ con $h[k]$.

Así nunca se desplaza nada: solo se sobrescribe una celda y se mueve un índice. Memoria mínima ($N$ palabras), latencia muestra a muestra. (Otros tipos de buffer en la Sección 4, §7.2: lineal para lotes, ping-pong para DMA.)

El **notch IIR**, en cambio, no usa buffer circular sino solo **2 estados** (`z1`, `z2`) por sección, gracias a la estructura **Direct Form II Transposed** (ver abajo).

#### 7.5 Cómo se implementan los filtros en C

**FIR — convolución.** La salida es la suma de productos coeficiente × muestra:

$$
y[n] = \sum_{k=0}^{N-1} h[k]\,x[n-k]
$$

En C, recorriendo el buffer circular hacia atrás. Como los coeficientes del FIR son **simétricos** ($h[k] = h[N-1-k]$, lo que garantiza la **fase lineal** — ver Sección 2), el orden de emparejamiento no altera el resultado.

**IIR notch — ecuación en diferencias (biquad SOS).** Un IIR usa salidas pasadas (realimentación). Una **sección de 2.º orden (biquad)** tiene la forma:

$$
y[n] = b_0\,x[n] + b_1\,x[n-1] + b_2\,x[n-2] - a_1\,y[n-1] - a_2\,y[n-2]
$$

Pero no se implementa "literal": se usa **Direct Form II Transposed (DF-II-T)**, que necesita solo **2 estados** y acumula **menos error de redondeo** que las formas directas. Sus ecuaciones (con $a_0 = 1$):

$$
\begin{aligned}
y[n] &= b_0\,x[n] + z_1 \\
z_1 &= b_1\,x[n] - a_1\,y[n] + z_2 \\
z_2 &= b_2\,x[n] - a_2\,y[n]
\end{aligned}
$$

> **Por qué SOS y no forma directa de orden alto:** un IIR de orden > 2 implementado "de una" es muy sensible a los errores de coeficientes (los polos se desplazan y puede **desestabilizarse**). Factorizándolo en biquads (SOS) cada par de polos se aísla y el filtro se mantiene estable. Aquí el notch es de orden 2 → un solo biquad basta. Detalle del criterio en Sección 4, §5.4.

#### 7.6 Punto fijo (Q) vs float, y por qué en ESP32 se usa float

**El problema:** los µC sin FPU no pueden hacer cuentas con decimales rápido. La solución clásica es el **punto fijo / formato Q**: representar los decimales como **enteros escalados**.

**¿Qué es Q?** En **Q1.15** (16 bits con signo: 1 bit entero + 15 fraccionarios), el rango es $[-1, 1)$ y la resolución es $2^{-15} \approx 3{,}05\times10^{-5}$. El número real es $x_{\text{real}} = x_{\text{int}}\cdot 2^{-15}$. Como los coeficientes de filtro suelen estar en $[-1,1)$, se normalizan a Q15 (a veces Q14 para tener margen). Ver la tabla de formatos en Sección 4, §5.1.

**Escalado y los peligros del punto fijo:**
- Un producto **Q15 × Q15 = Q30**. Para sumar $N$ productos sin desbordar, hay que **acumular en `int32_t` (o `int64_t`)** y reservar **bits de guarda** ($\lceil\log_2 N\rceil$ extra).
- Para volver a Q15: `acc >> 15`, **con redondeo** (sumar `1<<14` antes de desplazar) para no sesgar.
- **Overflow:** si el resultado se sale del rango, hay que **saturar (clamp)** a `[-32768, 32767]`, nunca dejar que dé la vuelta (*wrap-around*), porque eso produce discontinuidades catastróficas en la señal.
- **Underflow / ruido de cuantización:** $\sigma_q^2 = \Delta^2/12$ con $\Delta = 2^{-n}$. Cuantizar los **coeficientes** desplaza polos/ceros (peligroso en IIR → usar SOS); cuantizar el **acumulador** añade ruido a la salida.

**Por qué en ESP32 usamos float (y nos olvidamos de todo lo anterior):** el ESP32 **tiene FPU**. Con float32, cada MAC cuesta ~1 ciclo, el rango dinámico es enorme y el overflow es prácticamente inexistente. **No hace falta escalar, ni gestionar guarda, ni saturar.** El diseño es directo: copiar los coeficientes tal cual y multiplicar. Por eso este firmware usa float; el camino Q15 queda documentado para portar a un µC sin FPU (Arduino UNO). Regla de la Sección 4: `con_FPU → float32`, `sin_FPU → punto fijo Q15`.

### Ejemplo concreto (proyecto ECG)

Aplicación A — ECG. Señal útil 0.5–40 Hz; ruidos: red de **50 Hz**, EMG de alta frecuencia y deriva de línea de base. Cadena de filtrado (decidida en Secciones 2–4):

```
Notch IIR 50 Hz  ->  FIR pasa-bajos 40 Hz (fase lineal)
```

El notch (1 biquad, ~5 MACs/muestra) borra la interferencia de red al mínimo coste; el FIR Hamming limita la banda y **preserva la morfología P-QRS-T** por su fase lineal exacta (coeficientes simétricos). Esta es la *estrategia mixta* recomendada.

**Los coeficientes (de `coeficientes.h`).** El notch a 50 Hz, generado con `iirnotch` (Q ≈ 30), con sus ceros sobre el círculo unitario en $\omega_0 = 2\pi\cdot 50/500 = 0{,}2\pi$:

```cpp
// Notch IIR 50 Hz: H(z) = (b0 + b1 z^-1 + b2 z^-2)/(1 + a1 z^-1 + a2 z^-2)
#define NOTCH_B0   0.9902986180f
#define NOTCH_B1  -1.6023368229f
#define NOTCH_B2   0.9902986180f
#define NOTCH_A1  -1.6023368229f
#define NOTCH_A2   0.9805972359f
```

El FIR Hamming (`fc = 40 Hz`, `fs = 500 Hz`). Nótese la **simetría** del array (`h[0]==h[31]`, etc.), que garantiza la fase lineal:

```cpp
#define FIR_NUM_TAPS 32   // DEMO de 32 taps; el diseno completo usa N = 166
static const float FIR_COEFS[FIR_NUM_TAPS] = {
  +1.63443436e-03f, +1.65206265e-03f, /* ... */ +1.57445027e-01f,
  +1.57445027e-01f, /* ... simetrico ... */ +1.65206265e-03f, +1.63443436e-03f
};
```

> **Importante (coherencia con Sección 0):** el array de `coeficientes.h` es una **versión DEMO de 32 taps**, legible y verificable a mano. El **diseño completo del Paso 2/3 usa N = 166**, que el ESP32 soporta de sobra (166·4 ≈ 0.66 kB de coeficientes, 83 kMAC/s). Para usar el filtro completo, basta reemplazar el array por los 166 coeficientes y ajustar `FIR_NUM_TAPS`.

**Pseudocódigo del lazo principal** (la lógica, sin detalles de ESP32):

```
CONSTANTES: FS=500, T_US=2000, FIR_COEFS[N], NOTCH_B0..A2
ESTADO:     notch_z1=notch_z2=0;  fir_buf[N]={0};  fir_idx=0

FUNCION aplicar_notch(x):              # biquad DF-II-Transpuesta
    y  = NOTCH_B0*x + notch_z1
    notch_z1 = NOTCH_B1*x - NOTCH_A1*y + notch_z2
    notch_z2 = NOTCH_B2*x - NOTCH_A2*y
    devolver y

FUNCION aplicar_fir(x):                # FIR con buffer circular
    fir_buf[fir_idx] = x
    acc = 0;  idx = fir_idx
    PARA k = 0..N-1:
        acc += FIR_COEFS[k] * fir_buf[idx]
        idx = (idx==0) ? N-1 : idx-1   # retroceder en el ring
    fir_idx = (fir_idx + 1) mod N
    devolver acc

ISR_timer (cada 2 ms, 500 Hz):         # adquisicion determinista, CORTA
    muestra_cruda = leer_ADC()         # o generador de prueba
    hay_muestra = verdadero

BUCLE principal:
    SI hay_muestra:
        x = muestra_cruda;  hay_muestra = falso
        xn = aplicar_notch(x)          # 1) quita 50 Hz
        y  = aplicar_fir(xn)           # 2) pasa-bajos 40 Hz (fase lineal)
        enviar_por_Serial(x, y)
```

**El código C/.ino real** (extractos comentados de `filtro_ecg_esp32.ino`).

Notch IIR en Direct Form II Transposed — apenas 3 líneas y 2 estados:

```cpp
static inline float aplicar_notch(float x)
{
  float y = NOTCH_B0 * x + notch_z1;
  notch_z1 = NOTCH_B1 * x - NOTCH_A1 * y + notch_z2;
  notch_z2 = NOTCH_B2 * x - NOTCH_A2 * y;
  return y;
}
```

FIR con buffer circular — la convolución recorre el ring hacia atrás con *wrap* manual (sin el operador `%` en el lazo interno, más rápido):

```cpp
static float aplicar_fir(float x)
{
  fir_buf[fir_idx] = x;            // muestra nueva en la cabeza del ring
  float acc = 0.0f;
  uint16_t idx = fir_idx;          // empieza en x[n] (la mas nueva)
  for (uint16_t k = 0; k < FIR_NUM_TAPS; k++) {
    acc += FIR_COEFS[k] * fir_buf[idx];
    idx = (idx == 0) ? (FIR_NUM_TAPS - 1) : (idx - 1);  // x[n-k]
  }
  fir_idx = (fir_idx + 1) % FIR_NUM_TAPS;   // avanzar la cabeza
  return acc;
}
```

La cadena completa (primero notch, después FIR):

```cpp
static inline float procesar(float x)
{
  float xn = aplicar_notch(x);   // 1) elimina 50 Hz
  float yn = aplicar_fir(xn);    // 2) pasa-bajos 40 Hz (fase lineal)
  return yn;
}
```

La ISR del timer a 500 Hz — corta: solo adquiere y marca el flag (el ADC de 12 bits se centra y normaliza a $\pm 1$):

```cpp
void IRAM_ATTR isr_muestreo()
{
  portENTER_CRITICAL_ISR(&timerMux);
#ifdef USAR_ADC
  int raw = analogRead(ECG_PIN);                       // 0..4095 (12 bits)
  muestra_cruda = ((float)raw - 2048.0f) / 2048.0f;    // centrar y normalizar a +/-1
#else
  static uint32_t n_isr = 0;
  muestra_cruda = generar_muestra_prueba(n_isr++);     // seno 10+50 Hz + ruido
#endif
  hay_muestra = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}
```

Configuración del timer en `setup()` (reloj base APB 80 MHz, prescaler 80 → 1 tick = 1 µs, alarma cada 2000 µs):

```cpp
timer = timerBegin(0, 80, true);              // 1 tick = 1 us
timerAttachInterrupt(timer, &isr_muestreo, true);
timerAlarmWrite(timer, T_US, true);           // T_US = 2000 us, auto-recarga
timerAlarmEnable(timer);
```

El `loop()` procesa solo cuando la ISR dejó una muestra (entra y sale de la sección crítica para leer el flag sin condiciones de carrera):

```cpp
if (hay_muestra) {
  float x;
  portENTER_CRITICAL(&timerMux);
  x = muestra_cruda;  hay_muestra = false;
  portEXIT_CRITICAL(&timerMux);

  float y = procesar(x);
  Serial.print(x, 4); Serial.print('\t'); Serial.println(y, 4);  // crudo + filtrado
}
```

**Validación: salida embebida vs simulación.** Con `USAR_ADC` **sin definir**, el firmware genera por software una señal conocida:

$$
x[n] = \underbrace{1{,}0\,\sin(2\pi\,10\,t)}_{\text{banda útil}} + \underbrace{0{,}6\,\sin(2\pi\,50\,t)}_{\text{red 50 Hz}} + \underbrace{\text{ruido}(\pm 0{,}15)}_{\text{blanco}}
$$

Tras filtrar, **debe** ocurrir: el componente de **50 Hz desaparece** (lo quita el notch), el **ruido de alta frecuencia se atenúa** (lo quita el FIR LP 40 Hz) y queda esencialmente el **seno de 10 Hz** (está en la banda de paso), con un retardo constante (fase lineal). Procedimiento de comparación:

1. Abrir el **Serial Plotter** del Arduino IDE a **115200 baud**; se grafican dos trazas por línea: `crudo` (TAB) `filtrado`.
2. Verificar visualmente que la traza filtrada pierde el rizado de 50 Hz y el ruido, conservando la onda de 10 Hz.
3. Capturar la salida por Serial a **CSV** y compararla con la simulación del Paso 3 (Octave/Python `filter`/`lfilter` con los **mismos coeficientes**).
4. Calcular **SNR** y **RMSE** entre la salida embebida y la simulada. El error debe ser pequeño, idealmente del orden del ruido de cuantización del ADC/float32.

**Fuentes de error a tener en cuenta:**

| Fuente | Causa | Mitigación |
|---|---|---|
| **Cuantización del ADC** | ADC 12 bits, y (en Q15) coeficientes/acumulador | Más bits efectivos; redondeo; en IIR usar SOS |
| **Truncamiento de coeficientes** | Descartar bits al pasar de Q30 a Q15 | Redondear, no truncar; float32 lo evita |
| **Aliasing** | Componentes > fs/2 = 250 Hz mal muestreados | Filtro anti-aliasing **analógico** antes del ADC |
| **Latencia (retardo de grupo)** | $N/2$ muestras del FIR + ISR + cómputo | N=166 → ~83 ms; reducir N o usar IIR si la latencia aprieta |
| **Jitter de muestreo** | Variación del instante de muestreo | Timer-ISR (no polling); ISR corta |

> **Latencia del FIR:** $t_{\text{lat}} \approx \dfrac{N/2}{f_s}$. Con N=166 y fs=500 Hz da unos **83 ms** de retardo de grupo constante. Es el precio de la fase lineal; aceptable para monitoreo de ECG, pero a vigilar en aplicaciones de control estricto (Sección 4, §7.3).

### Procedimiento práctico

Pasos para reproducir y entender la implementación (sin compilar ni flashear nada):

1. **Leer los coeficientes** en `coeficientes.h`: identificar `FIR_COEFS[]` (verificar a ojo la simetría `h[k]==h[N-1-k]`) y las 5 macros del notch (`NOTCH_B0..A2`, con `a0=1` implícito).
2. **Seguir la cadena** en `filtro_ecg_esp32.ino`: `procesar()` → `aplicar_notch()` (biquad DF-II-T, 2 estados) → `aplicar_fir()` (convolución sobre buffer circular).
3. **Entender la adquisición:** la ISR `isr_muestreo()` corre cada 2 ms (timer a 500 Hz), adquiere `muestra_cruda` y marca `hay_muestra`. El `loop()` consume ese flag y filtra **fuera** de la ISR.
4. **Elegir los modos de prueba** con los `#define`: dejar `USAR_ADC` comentado para usar el generador interno (validar sin hardware) y `USAR_TIMER_HW` definido para muestreo determinista.
5. **Mapear el pseudocódigo al .ino:** confirmar que las ecuaciones del notch y el lazo de la convolución del pseudocódigo coinciden línea a línea con el C.
6. **Plan de validación:** prever capturar la salida del Serial a CSV y compararla contra la simulación de la Sección 5 (mismos coeficientes), calculando SNR y RMSE.
7. **Pensar el escalado a N=166:** reemplazar el array demo por los 166 coeficientes del diseño completo y ajustar `FIR_NUM_TAPS`; comprobar que el presupuesto ($83$ kMAC/s y ~1.3 kB) sigue holgado en ESP32.
8. **Esbozar el camino sin FPU (UNO):** anotar qué cambiaría para Q15 (coef. e int16 normalizados, acumulador int32 con guarda, redondeo, saturación) y por qué allí se prefiere IIR-SOS al FIR largo.

### Preguntas guía

1. ¿Qué cambia, concretamente, al pasar de la simulación *offline* (Octave/Python) a la ejecución en tiempo real en el ESP32? Nombrá al menos tres diferencias.
2. ¿Por qué `fs = 500 Hz` obliga a tomar una muestra exactamente cada 2 ms, y qué pasa si el muestreo tiene *jitter*?
3. ¿Por qué la ISR del timer debe ser **corta** y dónde se hace, entonces, el filtrado pesado del FIR?
4. ¿Qué es un **buffer circular** y por qué es mejor que desplazar el array completo en cada muestra para implementar la línea de retardo del FIR?
5. ¿Qué es el formato **Q15**? ¿Por qué un producto Q15×Q15 necesita un acumulador más ancho y bits de guarda, y por qué hay que **saturar** en vez de hacer *wrap-around*?
6. ¿Por qué el ESP32 puede usar **float32** sin preocuparse por el escalado, y por qué el Arduino UNO no? (Relacionalo con la FPU.)
7. ¿Cuántos MACs por muestra cuesta el FIR N=166 y cuántos el notch IIR? ¿Por qué ambos caben holgados en el ESP32?
8. ¿Cómo validarías que la salida del ESP32 coincide con la simulación, y qué métricas usarías? Enumerá las cuatro fuentes de error principales y su mitigación.


---

## 8. Cómo se resolvió cada paso del examen (mapeo)

El examen se estructura en **5 pasos evaluables**. Esta tabla conecta cada paso con lo que pide, cómo se resolvió en el proyecto, los archivos donde está la resolución y la sección de esta guía que lo explica desde cero.

| Paso del examen | Qué pide | Cómo se resolvió (Opción A — ECG) | Archivos del proyecto | Sección de la guía |
|-----------------|----------|-----------------------------------|------------------------|--------------------|
| **1 · Análisis y especificaciones** | Caracterizar la señal; justificar $f_s$ por Nyquist; separar banda útil de ruido; fijar tipo de filtro, $f_p$, $f_r$, $R_p$, $A_s$, fase lineal; tabla de requerimientos | ECG, banda 0.5–40 Hz; $f_s=500$ Hz (margen 6.25× sobre Nyquist); ruidos 50 Hz / EMG / deriva; se eligen **notch** (50 Hz) + **pasa-bajos** (40 Hz); fase lineal **requerida** | `informe/INFORME.md`, `_kb/00-enunciado.md`, `_kb/01-fundamentos-pds.md` | **Sección 1** |
| **2 · Desarrollo matemático** | FIR: método, orden $N$, $h[n]$, simetría→fase lineal, $H(z)$. IIR: prototipo, orden, $H_a(s)$, transformada bilineal + prewarping, $H(z)$, ec. en diferencias, estabilidad | **FIR Hamming** $N=166$ (regla $3.3 f_s/\Delta f$), simétrico → fase lineal, $\tau_g=83$ muestras. **IIR**: Butterworth daría $N=13$ → se usa **Chebyshev I N≈6 / Elíptico N≈4 en SOS**; **notch 50 Hz** por ceros/polos | `entrega_octave/ejemplos/diseno_filtros.m`, `entrega_python/ejemplos/diseno_filtros.py`, `_kb/02-fir.md`, `_kb/03-iir.md` | **Secciones 2 y 3** |
| **3 · Simulación** | $\lvert H\rvert$ dB y fase, $h[n]$, retardo de grupo, polos-ceros, señal antes/después, FFT/PSD, métricas SNR/RMSE, tabla comparativa FIR vs IIR | ECG sintético (gaussianas P-QRS-T) + ruido; `freqz`/`grpdelay`/`zplane`; aplicación causal y fase cero; **SNR sube, RMSE baja**; tabla FIR vs IIR | `entrega_octave/ejemplos/procesar_senal.m`, `entrega_python/ejemplos/procesar_senal.py`, `_kb/06-octave.md`, `_kb/07-python.md` | **Sección 5** |
| **4 · Agente de decisión IA** | Recomendar FIR/IIR + estructura según restricciones; ≥3 escenarios; validación coherente con pasos 1–3 | Agente **IF-THEN** (reglas R1–R7) en Python y Octave; agente **LLM** documentado; 3 escenarios (ECG→FIR, Arduino→IIR/SOS, transición exigente→Elíptico) | `entrega_python/ejemplos/agente_decision.py`, `agente_llm.py`, `entrega_octave/ejemplos/agente_decision.m`, `_kb/05-agente-ia.md` | **Sección 6** |
| **5 · Implementación embebida** | µC; punto fijo vs float; buffers; pseudocódigo + C; validación vs simulación; fuentes de error | **ESP32 + float32**; muestreo timer-ISR a 500 Hz; **buffer circular** para el FIR; **notch DF-II-Transpuesta**; validación por Serial/CSV; tabla de fuentes de error | `entrega_embebido/filtro_ecg_esp32.ino`, `entrega_embebido/coeficientes.h`, `_kb/04-criterios-diseno.md` | **Sección 7** |

> **Criterio de coherencia.** El examen insiste en que todo debe ser consistente: la elección de filtros (Paso 2) responde a las especificaciones (Paso 1); la simulación (Paso 3) confirma que cumplen; el agente (Paso 4) debe recomendar lo mismo que se eligió; y el embebido (Paso 5) debe reproducir la simulación. Si algún eslabón contradice a otro, hay un error de diseño.

---

## 9. Glosario de términos

Definiciones rápidas de consulta. Entre paréntesis, la sección donde el término se explica en profundidad.

**Aliasing** — Frecuencias por encima de $f_s/2$ que, al muestrear, se "disfrazan" de frecuencias más bajas y contaminan la señal de forma **irreversible**. Se evita con un filtro anti-aliasing analógico antes del ADC. (S1, S7)

**ADC (Convertidor Analógico-Digital)** — Circuito que convierte un voltaje en un número entero. El ESP32 tiene uno de 12 bits (0–4095). (S7)

**Banda de paso / rechazo / transición** — Frecuencias que el filtro deja pasar / elimina / la zona intermedia entre ambas. Cuanto más angosta la transición, más caro el filtro. (S1, S2)

**Bilineal (transformada)** — Receta algebraica $s = \frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}$ que convierte un filtro analógico $H_a(s)$ en uno digital $H(z)$. Requiere **prewarping**. (S3)

**Buffer circular (ring)** — Array que se reescribe "en círculo" para guardar las últimas $N$ muestras (la línea de retardo del FIR) sin desplazar datos. (S7)

**Convolución** — Operación que define el filtrado: $y[n]=\sum_k h[k]\,x[n-k]$. Cada salida es un promedio ponderado de entradas vecinas. (S1, S2)

**dB (decibel)** — Escala logarítmica de magnitud: $\lvert H\rvert_{dB}=20\log_{10}\lvert H\rvert$. 0 dB = pasa todo; −20 dB = ÷10; −40 dB = ÷100. (S1, S5)

**Ecuación en diferencias** — Fórmula ejecutable del filtro muestra a muestra: $y[n]=\sum b_k x[n-k] - \sum a_k y[n-k]$. (S3, S7)

**Estabilidad (BIBO)** — Un IIR es estable si y solo si todos sus **polos** están dentro del círculo unitario ($\lvert p\rvert<1$). El FIR es **siempre** estable. (S3, S4)

**Fase lineal** — El filtro retrasa **todas** las frecuencias lo mismo → no deforma la forma de onda (crítico en ECG). La garantiza la **simetría** de $h[n]$ en un FIR. (S1, S2)

**FIR (Finite Impulse Response)** — Filtro no recursivo: la salida solo depende de entradas. Fase lineal exacta y estabilidad garantizada, pero orden alto. (S2)

**FPU (Floating Point Unit)** — Hardware que hace cuentas con decimales en ~1 ciclo. El ESP32 la tiene; el Arduino UNO no. (S4, S7)

**Función de transferencia $H(z)$** — Descripción del filtro en el plano $z$. FIR: solo ceros. IIR: cociente de polinomios (polos y ceros). (S2, S3)

**IIR (Infinite Impulse Response)** — Filtro recursivo (realimenta salidas). Orden bajo y poco cómputo, pero fase no lineal y riesgo de inestabilidad. (S3)

**MAC (Multiply-Accumulate)** — "Multiplicar y acumular", la operación básica del filtrado. Coste: FIR ≈ $N+1$ MACs/muestra; IIR-SOS ≈ $5S$ MACs/muestra. (S4, S7)

**Muestreo / $f_s$ / $T$** — Tomar valores de la señal a intervalos regulares. $f_s$ = muestras por segundo; $T=1/f_s$. En ECG, $f_s=500$ Hz, $T=2$ ms. (S1)

**Notch (rechaza-banda)** — Filtro que elimina una frecuencia muy puntual (aquí, los 50 Hz de la red) con un par de ceros sobre el círculo unitario. (S3)

**Nyquist-Shannon (teorema)** — Para no perder información hay que muestrear a $f_s>2f_B$, donde $f_B$ es la frecuencia máxima de la señal. $f_N=f_s/2$ es la frecuencia de Nyquist. (S1)

**Prewarping (predistorsión)** — Corrección $\Omega_a=\frac{2}{T}\tan(\omega_d/2)$ aplicada a las frecuencias de diseño antes de la bilineal, para que los bordes caigan donde se quiere. (S3)

**Prototipo analógico** — Filtro continuo clásico que sirve de molde para el IIR: Butterworth (plano), Chebyshev I/II (rizado en una banda), Elíptico (mínimo orden). (S3, S4)

**Punto fijo (formato Q)** — Representar decimales con enteros escalados ($x_{real}=x_{int}\cdot2^{-n}$). Q15 ⇒ rango $[-1,1)$. Necesario en µC sin FPU. (S4, S7)

**Retardo de grupo $\tau_g$** — Cuánto se atrasa cada frecuencia: $\tau_g=-d\phi/d\omega$. Constante ($=N/2$) en un FIR de fase lineal. (S1, S5)

**RMSE** — Error cuadrático medio raíz entre la señal filtrada y la limpia ideal. Más bajo = mejor. (S1, S5)

**SNR (relación señal-ruido)** — Cuánta señal útil hay frente al ruido, en dB. Más alto = más limpio. (S1, S5)

**SOS / biquad (Second-Order Sections)** — Implementar un IIR como cascada de secciones de 2.º orden. Estándar para IIR de orden ≥ 3 por su robustez numérica. (S3, S4)

**Ventana ($w[n]$)** — Función suave (Hamming, Hann, Blackman, Kaiser) con la que se recorta la respuesta ideal infinita del FIR, controlando el ripple de Gibbs. (S2)

---

## 10. Autoevaluación global (preguntas integradoras)

Las preguntas de cada sección verifican ese tema puntual. Estas, en cambio, **conectan varias secciones** — son las que más se parecen a una defensa oral. Intentá responderlas en voz alta como si explicaras el proyecto.

**Sobre el hilo completo del proyecto**
1. Contá la historia del proyecto en 5 minutos: del problema (ECG ruidoso) a la solución corriendo en el ESP32, nombrando los 5 pasos. *(S1→S7)*
2. ¿Por qué la solución usa **dos filtros distintos** (un FIR y un IIR) en lugar de uno solo? ¿Qué criterio decide cada uno? *(S3, S4)*
3. Seguí un único valor de muestra del ECG desde que entra por el ADC hasta que sale filtrada: ¿por qué etapas pasa y qué le hace cada una? *(S5, S7)*

**Sobre las decisiones de diseño**
4. La fase lineal aparece como argumento en las Secciones 1, 2, 4, 6 y 7. Explicá la **cadena causal completa**: morfología clínica → fase lineal → simetría de $h[n]$ → FIR → orden alto → ESP32. *(S1, S2, S4, S7)*
5. ¿Por qué un Butterworth de orden 13 es "inviable" y qué dos decisiones lo resuelven (cambiar prototipo y usar SOS)? Relacioná SOS con el punto fijo del microcontrolador. *(S3, S4, S7)*
6. El agente IA recomienda "FIR" para el ECG. ¿Cómo demostrarías que esa recomendación es **coherente** con lo que efectivamente se diseñó y simuló? *(S4, S6)*

**Sobre la práctica**
7. Tenés los coeficientes diseñados en Python. Enumerá todo lo que cambia al llevarlos al ESP32 (causalidad, tipo de dato, adquisición, buffers) y qué nuevas **fuentes de error** aparecen. *(S5, S7)*
8. Si tuvieras que portar el mismo ECG a un **Arduino UNO** (2 kB RAM, sin FPU), ¿qué cambiarías en el filtro, la aritmética y la estructura, y por qué? *(S4, S7)*
9. ¿Qué gráficos y qué métricas presentarías para **convencer** de que el filtro funciona sin deformar el ECG? ¿Qué esperás ver en cada uno? *(S5)*
10. Diseñá un cuarto escenario para el agente IA (distinto de los tres dados) y predecí su recomendación justificándola con las reglas. *(S4, S6)*

---

## 11. Procedimiento general de extremo a extremo (checklist)

El "camino completo" del proyecto, de la especificación al hardware, como lista verificable. Cada paso remite a la sección que lo detalla.

**A. Especificar (Paso 1 — Sección 1)**
- [ ] Caracterizar la señal: tipo (ECG), banda útil (0.5–40 Hz), ruidos (50 Hz, EMG, deriva).
- [ ] Elegir y justificar $f_s$ con Nyquist ($f_s=500$ Hz, margen 6.25×).
- [ ] Fijar para cada filtro: $f_p$, $f_r$, $R_p$, $A_s$ y si requiere fase lineal.
- [ ] Volcar todo en una **tabla de requerimientos**.

**B. Diseñar FIR (Paso 2 — Sección 2)**
- [ ] Elegir ventana según $A_s$ (Hamming para ~53 dB).
- [ ] Calcular el orden ($N\approx 3.3 f_s/\Delta f = 166$, par).
- [ ] Generar $h[n]$ (`fir1`/`firwin`), verificar **simetría** y ganancia DC ≈ 1.

**C. Diseñar IIR (Paso 2 — Sección 3)**
- [ ] Elegir prototipo; calcular orden (`buttord`/`cheb1ord`/`ellipord`).
- [ ] Si el orden es alto, cambiar de prototipo y **diseñar en SOS**.
- [ ] Diseñar el **notch 50 Hz** (`iirnotch`) y verificar estabilidad ($\lvert p\rvert<1$).

**D. Simular y validar (Paso 3 — Sección 5)**
- [ ] Generar ECG sintético + ruido (50 Hz + blanco).
- [ ] Graficar $\lvert H\rvert$ dB, fase, $h[n]$, retardo de grupo, polos-ceros.
- [ ] Aplicar causal (`filter`/`lfilter`) y fase cero (`filtfilt`); graficar tiempo y espectro (FFT/PSD).
- [ ] Calcular **SNR** y **RMSE**; armar **tabla comparativa FIR vs IIR**.

**E. Decidir con el agente (Paso 4 — Sección 6)**
- [ ] Definir `specs` (fs, RAM, MHz, FPU, fase lineal, SNR, latencia, transición).
- [ ] Ejecutar el agente IF-THEN; leer recomendación + estructura + justificación.
- [ ] Validar con **≥3 escenarios** y confirmar coherencia con los Pasos 1–3.

**F. Implementar en el µC (Paso 5 — Sección 7)**
- [ ] Elegir plataforma y aritmética (ESP32 → float32; UNO → Q15).
- [ ] Configurar muestreo **timer-ISR** a 500 Hz (ISR corta).
- [ ] Implementar notch (DF-II-T, 2 estados) + FIR (buffer circular).
- [ ] Validar contra la simulación (Serial → CSV, SNR/RMSE) y analizar fuentes de error.

**G. Documentar y defender**
- [ ] Informe, gráficos ≥150 dpi, presentación, video y defensa oral con todos los integrantes.

---

## 12. Referencias y recursos del proyecto

**Documentos de la resolución**
- **Enunciado original:** `EXAMEN PARCIAL INTEGRADOR PDS 2026.docx` · resumen en [`_kb/00-enunciado.md`](_kb/00-enunciado.md)
- **Informe final académico:** [`informe/INFORME.md`](informe/INFORME.md)
- **Presentación (defensa oral):** [`presentacion/PRESENTACION.md`](presentacion/PRESENTACION.md)

**Base de conocimiento modular (`_kb/`)** — fuente técnica de esta guía
- [`01-fundamentos-pds.md`](_kb/01-fundamentos-pds.md) · [`02-fir.md`](_kb/02-fir.md) · [`03-iir.md`](_kb/03-iir.md) · [`04-criterios-diseno.md`](_kb/04-criterios-diseno.md) · [`05-agente-ia.md`](_kb/05-agente-ia.md) · [`06-octave.md`](_kb/06-octave.md) · [`07-python.md`](_kb/07-python.md)

**Código de la resolución**
- **Diseño de filtros:** `entrega_octave/ejemplos/diseno_filtros.m` · `entrega_python/ejemplos/diseno_filtros.py`
- **Simulación y métricas:** `entrega_octave/ejemplos/procesar_senal.m` · `entrega_python/ejemplos/procesar_senal.py`
- **Agente de decisión:** `entrega_python/ejemplos/agente_decision.py` · `agente_llm.py` · `entrega_octave/ejemplos/agente_decision.m`
- **Firmware embebido:** `entrega_embebido/filtro_ecg_esp32.ino` · `entrega_embebido/coeficientes.h`

**Datasets públicos (señales reales de ECG)**
- **MIT-BIH Noise Stress Test (`nstdb`):** https://physionet.org/content/nstdb/1.0.0/ — ECG con ruido real calibrado.
- **MIT-BIH Arrhythmia (`mitdb`):** https://physionet.org/content/mitdb/1.0.0/ — ECG anotado por cardiólogos.
- **Portal PhysioNet:** https://physionet.org — conversión a CSV con el paquete `wfdb` (Python).

**Herramientas de software** (no se instala nada en este entorno; referencia para reproducir)
- **GNU Octave 7.x** con el paquete `signal`, o **MATLAB R2021b+** (Signal Processing Toolbox).
- **Python 3** con `numpy`, `scipy.signal`, `matplotlib`; opcionalmente `scikit-learn`, `scikit-fuzzy`, SDK `anthropic` (solo para el agente, fase de diseño).
- **Arduino IDE** (o PlatformIO) con soporte ESP32, para el firmware.

---

> *Guía de estudio generada a partir del análisis del enunciado y de la resolución completa del proyecto (informe, scripts Octave/Python, firmware ESP32 y base de conocimiento). Material de estudio; las decisiones técnicas finales y su verificación numérica corresponden a la ejecución de los scripts del proyecto.*
