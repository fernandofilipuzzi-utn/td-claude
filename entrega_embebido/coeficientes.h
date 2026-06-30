/* ============================================================================
 *  coeficientes.h
 * ----------------------------------------------------------------------------
 *  Coeficientes de los filtros del sistema de filtrado de ECG.
 *
 *  Origen de los coeficientes:
 *    - FIR pasa-bajos : ventana de Hamming, frecuencia de corte fc = 40 Hz,
 *                       fs = 500 Hz. Generado con el diseno de referencia del
 *                       trabajo (`diseno_filtros.m` en Octave/MATLAB:
 *                         h = fir1(N, 40/(500/2), hamming(N+1));
 *                       o equivalente en Python con scipy.signal.firwin).
 *
 *                       NOTA SOBRE EL ORDEN:
 *                       El diseno completo del Paso 2/3 usa N = 166 taps
 *                       (orden 165) para alcanzar As ~ 40 dB con transicion
 *                       40->60 Hz. Ese filtro CABE y CORRE de sobra en ESP32
 *                       (166 MACs/muestra * 500 Hz = 83 kMAC/s << capacidad
 *                       con FPU; memoria ~166*4 = 0.66 kB de coeficientes).
 *                       Aqui se incluye una version DEMO de 32 taps para que
 *                       el array sea legible y verificable a mano. Para usar el
 *                       filtro completo, basta con reemplazar este array por los
 *                       166 coeficientes generados por `diseno_filtros.m` y
 *                       ajustar FIR_NUM_TAPS.
 *
 *    - Notch IIR 50 Hz: biquad de 2.o orden (rechaza-banda) de la red electrica.
 *                       Generado con `iirnotch` (MATLAB/Octave) o el diseno
 *                       analitico clasico del cookbook de Audio-EQ (RBJ):
 *                         [b,a] = iirnotch(50/(500/2), 50/(500/2)/Q);   % Q=30
 *                       Coeficientes ya normalizados con a0 = 1.
 * ============================================================================
 */

#ifndef COEFICIENTES_H
#define COEFICIENTES_H

/* ---------------------------------------------------------------------------
 *  FIR pasa-bajos (ventana de Hamming, fc = 40 Hz, fs = 500 Hz)
 *  - Coeficientes simetricos  h[n] = h[N-1-n]  -> FASE LINEAL EXACTA.
 *  - Ganancia DC normalizada a 1 (suma de coeficientes = 1.0).
 *  - DEMO de 32 taps (orden 31). Diseno completo: N = 166.
 * ------------------------------------------------------------------------- */
#define FIR_NUM_TAPS 32

static const float FIR_COEFS[FIR_NUM_TAPS] = {
  +1.63443436e-03f, +1.65206265e-03f, +1.32794488e-03f, +0.00000000e+00f,
  -2.96514230e-03f, -7.56958558e-03f, -1.26748525e-02f, -1.58865123e-02f,
  -1.40075806e-02f, -4.00922275e-03f, +1.57704153e-02f, +4.46353072e-02f,
  +7.91686580e-02f, +1.13730299e-01f, +1.41748747e-01f, +1.57445027e-01f,
  +1.57445027e-01f, +1.41748747e-01f, +1.13730299e-01f, +7.91686580e-02f,
  +4.46353072e-02f, +1.57704153e-02f, -4.00922275e-03f, -1.40075806e-02f,
  -1.58865123e-02f, -1.26748525e-02f, -7.56958558e-03f, -2.96514230e-03f,
  +0.00000000e+00f, +1.32794488e-03f, +1.65206265e-03f, +1.63443436e-03f
};

/* ---------------------------------------------------------------------------
 *  Notch IIR biquad a 50 Hz (fs = 500 Hz, Q ~ 30)
 *  H(z) = (b0 + b1 z^-1 + b2 z^-2) / (1 + a1 z^-1 + a2 z^-2)
 *  Ceros sobre el circulo unitario en w0 = 2*pi*50/500 = 0.2*pi (muesca exacta
 *  en 50 Hz); polos en el mismo angulo con radio r<1 (ancho fijado por Q).
 *  Coeficientes normalizados con a0 = 1.
 * ------------------------------------------------------------------------- */
#define NOTCH_B0   0.9902986180f
#define NOTCH_B1  -1.6023368229f
#define NOTCH_B2   0.9902986180f
#define NOTCH_A1  -1.6023368229f
#define NOTCH_A2   0.9805972359f

#endif /* COEFICIENTES_H */
