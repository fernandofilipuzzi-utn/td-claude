# Paso 5 — Implementación en microcontrolador: filtrado de ECG en ESP32

Entregable de código embebido del sistema de filtrado digital de ECG
(Aplicación A del enunciado). Cadena de procesamiento en tiempo real a
**fs = 500 Hz**:

```
Notch IIR 50 Hz (red eléctrica)  ->  FIR pasa-bajos 40 Hz (fase lineal)
```

El **notch IIR** (1 biquad, ~5 MACs/muestra) elimina la interferencia de red de
50 Hz al mínimo coste. El **FIR Hamming** limita la banda útil del ECG
(~0.5–40 Hz) preservando la **morfología P-QRS-T** gracias a su **fase lineal
exacta** (coeficientes simétricos). Es la *estrategia mixta* recomendada en el KB
(notch IIR + LP FIR).

**Archivos:**
- `filtro_ecg_esp32.ino` — firmware Arduino/C++ para ESP32.
- `coeficientes.h` — coeficientes FIR (32 taps demo) y biquad notch.
- `README.md` — este documento (Sección 5 del enunciado).

---

## 5.1 Descripción del hardware

### Plataforma elegida: ESP32

| Característica | Valor | Relevancia para el filtrado |
|---------------|-------|------------------------------|
| Núcleo | Xtensa LX6/LX7 (1–2 cores) | Cómputo de sobra para FIR de orden alto |
| Reloj | 160–240 MHz | A 240 MHz hay ~480.000 ciclos por muestra (T = 2 ms) |
| **FPU** | **Sí (hardware)** | Permite **float32**: cada MAC ~1 ciclo, sin escalado/overflow |
| RAM | 320 kB+ (SRAM) | El FIR completo (N=166) ocupa < 1.3 kB; trivial |
| Flash | 4 MB típico | Coeficientes y programa caben holgados |
| ADC | SAR **12 bits** (0–4095) | Adquisición de la señal de ECG acondicionada |
| Timer | `hw_timer_t` (base APB 80 MHz) | Muestreo determinista a 500 Hz exactos |

**Presupuesto de cómputo (ESP32 @ 240 MHz):**
FIR N=166 → 166 MACs/muestra × 500 Hz = **83 kMAC/s**, frente a decenas de miles
de MAC disponibles por muestra con FPU. Holgura > 95 %, suficiente para ADC, ISR
y la lógica de aplicación.

### Nota sobre Arduino UNO (contraste)

| Característica | Arduino UNO (AVR) | Consecuencia |
|---------------|-------------------|--------------|
| Reloj | 16 MHz | ~32.000 ciclos por muestra |
| RAM | 2 kB | El FIR N=166 (≈1.3 kB solo coef. + estados) **no entra cómodo** |
| FPU | **No** | float32 se emula (~100× lento) → **inviable** a 500 Hz |

En UNO se usa **IIR de orden bajo (SOS) en punto fijo Q15**: ~5 MACs por sección,
cabe en RAM y ciclos. Se pierde la fase lineal exacta (compensable offline con
`filtfilt` si la morfología es crítica). El `.ino` documenta esta alternativa en
sus comentarios de cabecera.

---

## 5.2 Arquitectura del sistema

### Diagrama de bloques

```
   SEÑAL ECG                 ADQUISICIÓN                  FILTRADO                       SALIDA
   (electrodos)         (timer-ISR @ 500 Hz)         (cadena DSP)               (Serial Plotter)

  +-----------+      +----------------------+      +------------------+      +-----------------+
  | Front-end |      |  Timer HW 500 Hz     |      | NOTCH IIR 50 Hz  |      |  Serial 115200  |
  | analógico | ---> |  ISR: lee ADC 12 bit | ---> | (biquad DF-II-T) | ---> |  "crudo\filtr." | --> PC
  | (amp+filt)|      |  -> muestra_cruda    |      +--------+---------+      +-----------------+
  +-----------+      |  -> flag hay_muestra |               |
                     +----------------------+               v
                                |                  +------------------+
                          (modo demo SW:           | FIR LP 40 Hz     |
                           seno 10+50 Hz+ruido)    | (buffer circular)|
                                                   +------------------+
```

### Estrategia de muestreo: timer / ISR

- **Interrupción de timer hardware a 500 Hz exactos** (`hw_timer_t`,
  `timerBegin`/`timerAlarmWrite`). Es la opción de mayor determinismo: el jitter
  de un muestreo por *polling* introduce ruido equivalente a aliasing.
- La **ISR es corta**: solo adquiere la muestra cruda (ADC o generador) y marca
  el flag `hay_muestra`. El filtrado pesado se hace en `loop()`, no en la ISR.
- **Alternativa portátil**: muestreo por `micros()` (seleccionable con
  `#define USAR_TIMER_HW`), que avanza el instante objetivo `t_prev += T_US` para
  no acumular deriva. Útil para portar a otras placas.
- **Fuente conmutable** (`#define USAR_ADC`): ADC real o generador de prueba por
  software (seno 10 Hz + 50 Hz + ruido) para validar sin hardware.

### Manejo del buffer circular

El FIR usa un **buffer circular (ring)** de `FIR_NUM_TAPS` posiciones como
**línea de retardo natural**:
- Se escribe la muestra nueva en la cabeza `fir_idx`.
- La convolución recorre el ring hacia atrás (`x[n], x[n-1], ... x[n-N+1]`) con
  *wrap* manual (sin operador `%` en el lazo interno, más rápido).
- La cabeza avanza módulo `FIR_NUM_TAPS`.
- Ventaja: latencia muestra a muestra y memoria mínima (N palabras), sin
  desplazar el array en cada muestra.

El notch IIR usa **Direct Form II Transposed**, que requiere solo **2 estados**
(`z1`, `z2`) por sección y acumula menos error de redondeo que las formas
directas.

---

## 5.3 Implementación

### Representación numérica: float32 (ESP32) vs Q15 (sin FPU)

| Aspecto | **float32 (ESP32, este código)** | **Q15 (Arduino UNO / sin FPU)** |
|---------|----------------------------------|----------------------------------|
| Tipo | `float` (IEEE-754, 32 bits) | `int16_t` en formato Q1.15, rango [-1, 1) |
| MAC | FPU hardware, ~1 ciclo | Entero: `int32_t acc += (int32_t)h * x` |
| Escalado | **No necesario** (rango dinámico amplio) | Coeficientes y muestras normalizados a [-1, 1) |
| Overflow | Prácticamente inexistente | Riesgo real: gestionar (ver abajo) |
| Esfuerzo | Bajo (diseño directo) | Alto (escalado, guarda, saturación) |

### Escalado y overflow (camino Q15)

- Producto **Q15 × Q15 = Q30** → acumular en `int32_t` (o `int64_t`) con
  **bits de guarda** (`ceil(log2(N))` extra) para sumar N productos sin desbordar.
- Volver a Q15: `acc >> 15`, con **redondeo** (sumar `1<<14` antes de desplazar)
  para reducir el sesgo.
- **Saturación (clamp)** a `[-32768, 32767]` en vez de *wrap-around*: el
  *wrap-around* produce discontinuidades catastróficas en la señal.
- Ruido de cuantización: σ²_q = Δ²/12 con Δ = 2⁻ⁿ. La cuantización de
  **coeficientes** desplaza polos/ceros (puede desestabilizar un IIR → usar
  **SOS** para órdenes > 2); la cuantización del **acumulador** añade ruido a la
  salida.

En ESP32 con FPU, float32 elimina casi por completo estos problemas, por eso es
la representación elegida.

---

## 5.4 Prueba y validación

### Señal de prueba conocida

Con `USAR_ADC` **sin definir**, el firmware genera por software:

```
x[n] = 1.0·sin(2π·10·t)  +  0.6·sin(2π·50·t)  +  ruido(±0.15)
       \__ banda útil __/    \__ red 50 Hz __/    \__ blanco __/
```

**Comportamiento esperado tras el filtrado:**
- El componente de **50 Hz desaparece** (lo elimina el notch).
- El **ruido de alta frecuencia se atenúa** (lo elimina el FIR LP 40 Hz).
- Queda esencialmente el **seno de 10 Hz** (está en la banda de paso), con un
  retardo de grupo constante (fase lineal del FIR).

### Captura por Serial Plotter

1. Abrir el **Serial Plotter** del Arduino IDE a **115200 baud**.
2. Se grafican dos trazas por línea: `crudo` (TAB) `filtrado`.
3. Verificar visualmente que la traza filtrada pierde la oscilación de 50 Hz y
   el ruido, conservando la onda de 10 Hz.

### Comparación con la simulación

- Capturar la salida por Serial a CSV y compararla con la simulación del Paso 3
  (MATLAB/Octave `filter`/`lfilter` con los mismos coeficientes).
- Métricas: **SNR** y **RMSE** entre salida embebida y salida simulada; el error
  debe ser pequeño (idealmente cercano al ruido de cuantización del ADC/float32).

### Fuentes de error a considerar

| Fuente | Causa | Mitigación |
|--------|-------|------------|
| **Cuantización** | ADC 12 bits y (en Q15) coeficientes/acumulador | Más bits efectivos; redondeo; en IIR usar SOS |
| **Truncamiento** | Descartar bits al volver de Q30 a Q15 | Redondear (no truncar); float32 lo evita |
| **Aliasing** | Componentes > fs/2 = 250 Hz mal muestreados | Filtro anti-aliasing analógico antes del ADC; fs adecuado |
| **Latencia** | Retardo de grupo FIR = N/2 muestras + ISR + cómputo | FIR N=166 → 83 ms; reducir N o usar IIR si la latencia aprieta |
| **Jitter de muestreo** | Variación del instante de muestreo | Timer-ISR (no polling); ISR corta |

---

## Pseudocódigo del algoritmo principal

```
CONSTANTES:
    FS = 500                      # Hz
    T_US = 1e6 / FS               # 2000 us
    FIR_COEFS[N]                  # coeficientes FIR (simetricos, ganancia DC = 1)
    NOTCH_B0,B1,B2, NOTCH_A1,A2   # biquad notch 50 Hz (a0 = 1)

ESTADO:
    notch_z1 = notch_z2 = 0       # estados DF-II-T del notch
    fir_buf[N] = {0}              # buffer circular (linea de retardo FIR)
    fir_idx = 0

FUNCION aplicar_notch(x):         # IIR biquad, Direct Form II Transposed
    y  = NOTCH_B0*x + notch_z1
    notch_z1 = NOTCH_B1*x - NOTCH_A1*y + notch_z2
    notch_z2 = NOTCH_B2*x - NOTCH_A2*y
    devolver y

FUNCION aplicar_fir(x):           # FIR con buffer circular
    fir_buf[fir_idx] = x
    acc = 0
    idx = fir_idx
    PARA k = 0 .. N-1:
        acc += FIR_COEFS[k] * fir_buf[idx]
        idx = (idx == 0) ? N-1 : idx-1     # retroceder en el ring
    fir_idx = (fir_idx + 1) mod N
    devolver acc

# --- adquisicion determinista ---
ISR_timer (cada T_US):            # 500 Hz exactos
    muestra_cruda = leer_ADC()   # o generador de prueba (seno 10+50 Hz + ruido)
    hay_muestra = verdadero

# --- procesamiento (no en la ISR) ---
BUCLE principal:
    SI hay_muestra:
        x = muestra_cruda;  hay_muestra = falso
        xn = aplicar_notch(x)     # 1) quita 50 Hz
        y  = aplicar_fir(xn)      # 2) pasa-bajos 40 Hz (fase lineal)
        enviar_por_Serial(x, y)   # crudo y filtrado -> Serial Plotter
```

> La implementación completa, con detalles de ESP32 (`hw_timer_t`, ADC, ISR),
> los modos conmutables (`USAR_ADC`, `USAR_TIMER_HW`) y las notas de punto fijo
> Q15, está en **`filtro_ecg_esp32.ino`**.

---

## Notas de diseño y coherencia con el KB

- **Notch 50 Hz**: ceros sobre el círculo unitario en ω₀ = 2π·50/500 = 0.2π
  (muesca exacta en 50 Hz), polos en el mismo ángulo con radio r < 1 (ancho
  fijado por Q ≈ 30). Generado con `iirnotch`. Coste mínimo (1 biquad).
- **FIR Hamming, fc = 40 Hz, fs = 500 Hz**: la ventana de Hamming es el defecto
  biomédico (As ~ 53 dB). El array de `coeficientes.h` es la **versión demo de
  32 taps** (legible y simétrica); el diseño completo del Paso 2/3 usa
  **N = 166**, que el ESP32 soporta sin problemas (basta reemplazar el array y
  `FIR_NUM_TAPS`).
- **Estructuras**: notch en DF-II Transpuesta (mínimos estados, menos ruido);
  FIR transversal con buffer circular (línea de retardo natural, fase lineal).
