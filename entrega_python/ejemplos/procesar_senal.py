#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""procesar_senal.py — Pipeline de filtrado sobre ECG sintético (Paso 3).

Propósito
---------
Script de REFERENCIA del Paso 3 (simulación). Es AUTÓNOMO: genera una señal de
ECG sintética (no descarga nada) contaminada con interferencia de red (50 Hz) y
ruido blanco, fs = 500 Hz, ~5 s, y aplica el pipeline de filtrado del caso A:

  * Notch IIR 50 Hz (red eléctrica) -> elimina la interferencia.
  * FIR LP 40 Hz (fase lineal Hamming) e IIR LP Chebyshev I (SOS) -> limitan
    la banda útil del ECG (≈ 0.5–40 Hz).

Compara filtrado CAUSAL (``lfilter`` / ``sosfilt``, lo que ocurre en el µC) con
filtrado de FASE CERO (``filtfilt`` / ``sosfiltfilt``, offline, no deforma la
morfología P-QRS-T). Grafica tiempo antes/después y espectro (FFT y Welch), e
imprime una tabla comparativa FIR vs IIR con métricas SNR y RMSE.

Ejecutar:  python procesar_senal.py
"""

from __future__ import annotations

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

FS = 500.0          # frecuencia de muestreo [Hz]
DUR = 5.0           # duración [s]
F_NOTCH = 50.0      # interferencia de red [Hz]
FP = 40.0           # corte LP [Hz]
FR = 60.0           # borde de rechazo IIR [Hz]
RP = 1.0
AS = 40.0


# ----------------------------------------------------------------------------
# Generación de ECG sintético
# ----------------------------------------------------------------------------
def _gauss(t: np.ndarray, centro: float, amp: float, ancho: float) -> np.ndarray:
    """Pulso gaussiano centrado en `centro` (s), amplitud `amp`, sigma `ancho`."""
    return amp * np.exp(-0.5 * ((t - centro) / ancho) ** 2)


def generar_ecg(fs: float = FS, dur: float = DUR, fc_card: float = 1.2,
                seed: int = 0):
    """Genera un ECG sintético P-QRS-T como suma de gaussianas por latido.

    Devuelve (t, ecg_limpio, ecg_ruidoso). El latido se modela con ondas
    P, Q, R, S, T (gaussianas) repetidas según la frecuencia cardíaca fc_card.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(0, dur, 1.0 / fs)
    periodo = 1.0 / fc_card                          # s entre latidos
    ecg_limpio = np.zeros_like(t)

    # Plantilla de un latido (offsets en s respecto al inicio del latido).
    # (offset, amplitud, sigma)
    ondas = [
        (-0.20, 0.10, 0.025),   # onda P
        (-0.025, -0.15, 0.007),  # onda Q
        (0.00, 1.00, 0.009),     # onda R (pico QRS)
        (0.025, -0.25, 0.007),   # onda S
        (0.16, 0.30, 0.030),     # onda T
    ]
    n_latidos = int(np.ceil(dur / periodo)) + 1
    for k in range(n_latidos):
        centro_latido = k * periodo + 0.30           # primer latido a 0.30 s
        for off, amp, sig in ondas:
            ecg_limpio += _gauss(t, centro_latido + off, amp, sig)

    # Contaminación: interferencia de red 50 Hz + ruido blanco gaussiano.
    interf = 0.30 * np.sin(2 * np.pi * F_NOTCH * t)
    ruido = 0.05 * rng.standard_normal(t.size)
    ecg_ruidoso = ecg_limpio + interf + ruido
    return t, ecg_limpio, ecg_ruidoso


# ----------------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------------
def snr(clean: np.ndarray, x: np.ndarray) -> float:
    """SNR en dB tomando (clean - x) como ruido/error residual."""
    noise = clean - x
    return float(10 * np.log10(np.sum(clean ** 2) / (np.sum(noise ** 2) + 1e-12)))


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    """Raíz del error cuadrático medio entre dos señales."""
    return float(np.sqrt(np.mean((a - b) ** 2)))


# ----------------------------------------------------------------------------
# Diseño de los filtros (idéntico criterio que diseno_filtros.py)
# ----------------------------------------------------------------------------
def construir_filtros(fs: float = FS):
    """Devuelve (h_fir, sos_lp_iir, sos_notch)."""
    h_fir = signal.firwin(167, cutoff=FP, fs=fs, window="hamming", pass_zero=True)
    n, wn = signal.cheb1ord(wp=FP, ws=FR, gpass=RP, gstop=AS, fs=fs)
    sos_lp = signal.cheby1(n, RP, wn, btype="low", output="sos", fs=fs)
    b_n, a_n = signal.iirnotch(w0=F_NOTCH, Q=30, fs=fs)
    sos_notch = signal.tf2sos(b_n, a_n)
    return h_fir, sos_lp, sos_notch


# ----------------------------------------------------------------------------
# Gráficas
# ----------------------------------------------------------------------------
def graficar_tiempo(t, ecg_limpio, ecg_ruidoso, ecg_fir, ecg_iir):
    """Señal en el tiempo: limpia, ruidosa y filtrada (FIR e IIR, fase cero)."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    fig.suptitle("ECG sintético — tiempo (zoom a 1.5 s)")
    a1.plot(t, ecg_ruidoso, color="0.6", lw=0.8, label="ruidoso (50 Hz + blanco)")
    a1.plot(t, ecg_limpio, "k", lw=1.0, label="limpio (referencia)")
    a1.set_ylabel("Amplitud")
    a1.legend(loc="upper right", fontsize=8)
    a1.grid(alpha=0.3)
    a1.set_xlim(0, 1.5)

    a2.plot(t, ecg_limpio, "k", lw=1.0, label="limpio")
    a2.plot(t, ecg_fir, "b", lw=1.0, label="FIR (filtfilt)")
    a2.plot(t, ecg_iir, "r", lw=1.0, alpha=0.7, label="IIR (sosfiltfilt)")
    a2.set_xlabel("t [s]")
    a2.set_ylabel("Amplitud")
    a2.legend(loc="upper right", fontsize=8)
    a2.grid(alpha=0.3)
    fig.tight_layout()


def graficar_espectro(ecg_ruidoso, ecg_fir, ecg_iir, fs=FS):
    """Espectro antes/después por FFT (rfft) y PSD por Welch."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7))
    fig.suptitle("Espectro — el pico de 50 Hz desaparece tras el notch")

    f = np.fft.rfftfreq(ecg_ruidoso.size, 1.0 / fs)
    mag = lambda x: 20 * np.log10(np.abs(np.fft.rfft(x)) + 1e-12)
    a1.plot(f, mag(ecg_ruidoso), color="0.6", label="ruidoso")
    a1.plot(f, mag(ecg_fir), "b", label="FIR")
    a1.plot(f, mag(ecg_iir), "r", alpha=0.7, label="IIR")
    a1.axvline(F_NOTCH, color="g", ls="--", lw=1, label="50 Hz")
    a1.set_xlabel("f [Hz]")
    a1.set_ylabel("|X| [dB]")
    a1.set_xlim(0, 120)
    a1.legend(fontsize=8)
    a1.grid(alpha=0.3)

    for x, c, lab in [(ecg_ruidoso, "0.6", "ruidoso"),
                      (ecg_fir, "b", "FIR"), (ecg_iir, "r", "IIR")]:
        fw, pxx = signal.welch(x, fs=fs, nperseg=1024)
        a2.semilogy(fw, pxx, color=c, alpha=0.8, label=lab)
    a2.axvline(F_NOTCH, color="g", ls="--", lw=1)
    a2.set_xlabel("f [Hz]")
    a2.set_ylabel("PSD [V²/Hz]")
    a2.set_xlim(0, 120)
    a2.legend(fontsize=8)
    a2.grid(alpha=0.3, which="both")
    fig.tight_layout()


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("PIPELINE DE FILTRADO — ECG sintético, fs = 500 Hz, 5 s")
    print("=" * 70)

    t, ecg_limpio, ecg_ruidoso = generar_ecg()
    h_fir, sos_lp, sos_notch = construir_filtros()

    # --- Pipeline CAUSAL (lo que ocurre en el microcontrolador) ------------
    # Primero el notch, luego el LP. lfilter (FIR) / sosfilt (IIR) son causales.
    fir_causal = signal.lfilter(h_fir, 1, signal.sosfilt(sos_notch, ecg_ruidoso))
    iir_causal = signal.sosfilt(sos_lp, signal.sosfilt(sos_notch, ecg_ruidoso))

    # --- Pipeline FASE CERO (offline, no deforma P-QRS-T) ------------------
    ecg_sin_red = signal.sosfiltfilt(sos_notch, ecg_ruidoso)
    fir_fase0 = signal.filtfilt(h_fir, 1, ecg_sin_red)
    iir_fase0 = signal.sosfiltfilt(sos_lp, ecg_sin_red)

    # --- Métricas (referencia: ecg_limpio) ---------------------------------
    print("\nMétricas (referencia = ECG limpio):")
    print(f"  SNR entrada (ruidoso)           : {snr(ecg_limpio, ecg_ruidoso):6.2f} dB")
    print("\n  {:<28}{:>10}{:>10}".format("Caso", "SNR[dB]", "RMSE"))
    print("  " + "-" * 48)
    filas = [
        ("FIR causal (lfilter)", fir_causal),
        ("IIR causal (sosfilt)", iir_causal),
        ("FIR fase cero (filtfilt)", fir_fase0),
        ("IIR fase cero (sosfiltfilt)", iir_fase0),
    ]
    for nombre, y in filas:
        print(f"  {nombre:<28}{snr(ecg_limpio, y):>10.2f}{rmse(ecg_limpio, y):>10.4f}")

    print("\n  Lectura: la fase cero (filtfilt/sosfiltfilt) sube el SNR y baja el")
    print("  RMSE porque no introduce retardo ni distorsión de fase; el FIR de")
    print("  fase lineal preserva mejor la morfología P-QRS-T en modo causal.")

    # --- Tabla comparativa FIR vs IIR (criterios de ingeniería) ------------
    n_fir = len(h_fir) - 1
    n_sec = sos_lp.shape[0]
    print("\nTabla comparativa FIR vs IIR (LP 40 Hz):")
    print("  {:<22}{:>14}{:>16}".format("Criterio", "FIR (Hamming)", "IIR (Cheby1 SOS)"))
    print("  " + "-" * 52)
    print("  {:<22}{:>14}{:>16}".format("Orden N", n_fir, sos_lp.shape[0] * 2))
    print("  {:<22}{:>14}{:>16}".format("MACs/muestra", f"~{n_fir + 1}", f"~{5 * n_sec}"))
    print("  {:<22}{:>14}{:>16}".format("Fase", "lineal", "no lineal"))
    print("  {:<22}{:>14}{:>16}".format("Retardo grupo", "constante", "variable"))
    print("  {:<22}{:>14}{:>16}".format("Estabilidad", "garantizada", "verificar |p|<1"))
    print("  {:<22}{:>14}{:>16}".format("Estructura", "DF/transversal", "SOS cascada"))

    # --- Gráficas (usamos las versiones de fase cero) ----------------------
    graficar_tiempo(t, ecg_limpio, ecg_ruidoso, fir_fase0, iir_fase0)
    graficar_espectro(ecg_ruidoso, fir_fase0, iir_fase0)

    print("\nMostrando gráficas (cierre las ventanas para terminar)...")
    plt.show()


if __name__ == "__main__":
    main()
