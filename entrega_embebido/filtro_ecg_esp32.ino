/* ============================================================================
 *  filtro_ecg_esp32.ino
 * ----------------------------------------------------------------------------
 *  PROPOSITO : Filtrado digital en tiempo real de una senal de ECG.
 *              Cadena: NOTCH IIR 50 Hz (red electrica)  ->  FIR pasa-bajos 40 Hz
 *              (limita banda util ~0.5-40 Hz, atenua EMG/HF). El FIR es de fase
 *              lineal exacta, por lo que NO distorsiona la morfologia P-QRS-T.
 *
 *  PLATAFORMA: ESP32 (Xtensa LX6/LX7, 160-240 MHz, FPU hardware, RAM 320 kB+,
 *              ADC SAR 12 bits). Aritmetica en punto flotante float32 (la FPU
 *              hace cada MAC en ~1 ciclo, asi que el escalado/overflow del
 *              punto fijo no es necesario).
 *
 *  fs        : 500 Hz  (T = 2 ms por muestra).
 *  ENTORNO   : Arduino IDE / PlatformIO (framework arduino-esp32).
 *  AUTOR     : <placeholder - completar nombre/grupo>
 *  FECHA     : 2026
 *  LICENCIA  : uso academico (Tecnicas Digitales III - PDS).
 *
 *  ---------------------------------------------------------------------------
 *  ESTRATEGIA DE TIEMPO REAL
 *  ---------------------------------------------------------------------------
 *  - Adquisicion determinista por INTERRUPCION DE TIMER a 500 Hz exactos
 *    (hw_timer_t). La ISR solo marca un flag y guarda la muestra cruda; el
 *    filtrado pesado se hace en loop() para mantener la ISR corta.
 *  - Si se prefiere portabilidad maxima (otros cores/placas) hay un camino
 *    alternativo con micros() seleccionable por #define USAR_TIMER_HW.
 *  - Buffer CIRCULAR como linea de retardo natural del FIR.
 *  - Salida por Serial para visualizar en el Serial Plotter del Arduino IDE.
 *
 *  ---------------------------------------------------------------------------
 *  ALTERNATIVA PUNTO FIJO Q15 (uC SIN FPU, p.ej. Arduino UNO / Cortex-M0)
 *  ---------------------------------------------------------------------------
 *  Sin FPU, float32 se emula por software (~100x mas lento) y es inviable a
 *  500 Hz con FIR largo. La alternativa es aritmetica de punto fijo Q15:
 *    - Muestras y coeficientes -> int16_t en formato Q1.15 (rango [-1, 1)).
 *    - Producto Q15 * Q15 = Q30 -> acumular en int32_t (o int64_t) con bits
 *      de guarda (ceil(log2(N)) extra) para no desbordar la suma de N productos.
 *    - Resultado: acc >> 15  (volver a Q15), con redondeo (sumar 1<<14 antes
 *      de desplazar) y SATURACION (clamp a [-32768, 32767]) en vez de
 *      wrap-around, que produce discontinuidades catastroficas.
 *  Ademas, en un uC asi conviene cambiar el FIR largo por un IIR de orden bajo
 *  (ver mas abajo "ALTERNATIVA IIR PARA ARDUINO UNO").
 *
 *  ---------------------------------------------------------------------------
 *  ALTERNATIVA IIR PARA ARDUINO UNO (16 MHz, 2 kB RAM, sin FPU)
 *  ---------------------------------------------------------------------------
 *  El FIR de orden alto (N=166) NO entra ni en RAM ni en ciclos del UNO. Para
 *  esa plataforma se sustituye el pasa-bajos FIR por un IIR pasa-bajos
 *  Butterworth de orden bajo en cascada de biquads (SOS), aplicado igual que el
 *  notch (misma funcion aplicar_biquad), en aritmetica Q15. Coste ~5 MACs por
 *  seccion frente a los 166 del FIR. Se pierde la fase lineal exacta; si la
 *  morfologia es critica, se compensa offline (filtfilt) o se acepta el
 *  retardo de grupo no constante.
 * ============================================================================
 */

#include "coeficientes.h"

/* =====================  CONFIGURACION  ===================================== */

#define FS_HZ        500            // Frecuencia de muestreo [Hz]
#define T_US         (1000000UL / FS_HZ)   // Periodo de muestreo [us] = 2000

// --- Fuente de la senal -----------------------------------------------------
// USAR_ADC definido  -> lee del ADC real (pin ECG_PIN).
// USAR_ADC NO definido (por defecto) -> generador de senal de prueba interno
//                                       (seno 10 Hz + 50 Hz + ruido) para
//                                       validar sin hardware.
//#define USAR_ADC

#define ECG_PIN      34            // GPIO34 = ADC1_CH6 (solo-entrada, ideal ADC)

// --- Estrategia de muestreo -------------------------------------------------
// USAR_TIMER_HW definido (por defecto) -> interrupcion de timer ESP32 (preciso).
// USAR_TIMER_HW NO definido             -> muestreo por micros() (portable).
#define USAR_TIMER_HW

/* =====================  ESTADO DEL NOTCH (Direct Form II Transposed)  ======= */
/*  Biquad DF-II-T: solo 2 estados (z1, z2) por seccion; menor ruido de
 *  redondeo que DF-I/DF-II directa. Ecuaciones:
 *      y[n]  = b0*x[n] + z1
 *      z1    = b1*x[n] - a1*y[n] + z2
 *      z2    = b2*x[n] - a2*y[n]
 */
static float notch_z1 = 0.0f;
static float notch_z2 = 0.0f;

/* =====================  ESTADO DEL FIR (buffer circular)  ================== */
static float  fir_buf[FIR_NUM_TAPS] = {0.0f}; // linea de retardo (muestras x[n..n-N+1])
static uint16_t fir_idx = 0;                  // indice de escritura (cabeza del ring)

/* =====================  VARIABLES DE LA ISR / MUESTREO  ==================== */
volatile float  muestra_cruda = 0.0f;  // ultima muestra adquirida (escrita por ISR)
volatile bool   hay_muestra   = false; // flag: hay muestra nueva por procesar

#ifdef USAR_TIMER_HW
hw_timer_t *timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
#endif

/* =====================  GENERADOR DE SENAL DE PRUEBA  ====================== */
/*  Seno util de 10 Hz (en banda de paso) + interferencia de red de 50 Hz
 *  (debe ser eliminada por el notch) + ruido blanco. Permite validar la cadena
 *  completa SIN hardware: tras el filtrado debe quedar ~solo el seno de 10 Hz.
 */
static float generar_muestra_prueba(uint32_t n)
{
  const float two_pi = 6.28318530718f;
  float t = (float)n / (float)FS_HZ;
  float util  = 1.00f * sinf(two_pi * 10.0f * t);   // 10 Hz (banda util)
  float red   = 0.60f * sinf(two_pi * 50.0f * t);   // 50 Hz (interferencia red)
  float ruido = 0.15f * (((float)random(0, 2001) / 1000.0f) - 1.0f); // [-0.15,0.15]
  return util + red + ruido;
}

/* =====================  NOTCH IIR 50 Hz (DF-II-T)  ======================== */
static inline float aplicar_notch(float x)
{
  float y = NOTCH_B0 * x + notch_z1;
  notch_z1 = NOTCH_B1 * x - NOTCH_A1 * y + notch_z2;
  notch_z2 = NOTCH_B2 * x - NOTCH_A2 * y;
  return y;
}

/* =====================  FIR pasa-bajos (buffer circular)  ================= */
/*  Inserta x en el ring y calcula la convolucion sum_{k} h[k]*x[n-k].
 *  El recorrido va desde la muestra mas reciente hacia atras; como el FIR es
 *  simetrico, el orden de emparejamiento no altera el resultado.
 */
static float aplicar_fir(float x)
{
  // Escribir la nueva muestra en la cabeza del buffer circular.
  fir_buf[fir_idx] = x;

  float acc = 0.0f;
  uint16_t idx = fir_idx;        // empieza en la muestra mas nueva: x[n]
  for (uint16_t k = 0; k < FIR_NUM_TAPS; k++) {
    acc += FIR_COEFS[k] * fir_buf[idx];
    // retroceder en el ring (x[n-k]); con wrap manual (sin %, mas rapido)
    idx = (idx == 0) ? (FIR_NUM_TAPS - 1) : (idx - 1);
  }

  // Avanzar la cabeza para la proxima muestra.
  fir_idx = (fir_idx + 1) % FIR_NUM_TAPS;
  return acc;
}

/* =====================  CADENA DE PROCESAMIENTO  ========================== */
static inline float procesar(float x)
{
  float xn = aplicar_notch(x);   // 1) elimina 50 Hz
  float yn = aplicar_fir(xn);    // 2) pasa-bajos 40 Hz (fase lineal)
  return yn;
}

/* =====================  ISR DE TIMER (500 Hz)  ============================ */
#ifdef USAR_TIMER_HW
void IRAM_ATTR isr_muestreo()
{
  portENTER_CRITICAL_ISR(&timerMux);
  // ISR CORTA: solo adquiere la muestra cruda y marca el flag.
#ifdef USAR_ADC
  // analogRead es seguro desde ISR en arduino-esp32; se normaliza a +/-1 aprox.
  // ADC 12 bits -> [0,4095]; centrar en ~Vref/2 y escalar a [-1, 1].
  int raw = analogRead(ECG_PIN);
  muestra_cruda = ((float)raw - 2048.0f) / 2048.0f;
#else
  static uint32_t n_isr = 0;
  muestra_cruda = generar_muestra_prueba(n_isr++);
#endif
  hay_muestra = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}
#endif

/* =====================  SETUP  =========================================== */
void setup()
{
  Serial.begin(115200);
  delay(200);
  Serial.println("# Filtro ECG ESP32: notch 50 Hz + FIR LP 40 Hz @ fs=500 Hz");
  Serial.println("# crudo\tfiltrado   (para Serial Plotter)");

#ifdef USAR_ADC
  analogReadResolution(12);                 // ADC a 12 bits
  analogSetPinAttenuation(ECG_PIN, ADC_11db); // rango ~0..3.3 V
#endif

#ifdef USAR_TIMER_HW
  // Timer hardware del ESP32:
  //   - timerBegin(timer_num, prescaler, count_up)
  //   - reloj base APB = 80 MHz; prescaler 80 -> 1 tick = 1 us.
  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &isr_muestreo, true);
  //   - alarma cada T_US ticks (= 2000 us = 2 ms), con auto-recarga.
  timerAlarmWrite(timer, T_US, true);
  timerAlarmEnable(timer);
#endif
}

/* =====================  LOOP  ============================================ */
void loop()
{
#ifdef USAR_TIMER_HW
  /* --- Camino con TIMER/ISR: procesar cuando la ISR deja una muestra --- */
  if (hay_muestra) {
    float x;
    portENTER_CRITICAL(&timerMux);
    x = muestra_cruda;
    hay_muestra = false;
    portEXIT_CRITICAL(&timerMux);

    float y = procesar(x);

    // Salida para Serial Plotter: dos trazas (crudo y filtrado).
    Serial.print(x, 4);
    Serial.print('\t');
    Serial.println(y, 4);
  }
#else
  /* --- Camino PORTABLE con micros(): muestreo por espera no bloqueante --- */
  static uint32_t t_prev = 0;
  static uint32_t n = 0;
  uint32_t ahora = micros();
  if ((ahora - t_prev) >= T_US) {
    t_prev += T_US;   // avanzar el instante objetivo (evita deriva acumulada)

  #ifdef USAR_ADC
    int raw = analogRead(ECG_PIN);
    float x = ((float)raw - 2048.0f) / 2048.0f;
  #else
    float x = generar_muestra_prueba(n);
  #endif
    n++;

    float y = procesar(x);

    Serial.print(x, 4);
    Serial.print('\t');
    Serial.println(y, 4);
  }
#endif
}
