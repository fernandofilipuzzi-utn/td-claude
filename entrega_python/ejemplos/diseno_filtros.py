#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diseno_filtros.py — Diseño y caracterización de filtros FIR e IIR (caso ECG).

Propósito
---------
Script de REFERENCIA del Paso 2/3 del examen (PDS / Filtrado Digital). Diseña y
caracteriza los dos filtros del caso ECG (Anexo I-A, fs = 500 Hz) con
``scipy.signal`` y los grafica con ``matplotlib``:

  * FIR pasa-bajos de fase lineal (ventana Hamming, fc = 40 Hz, numtaps ≈ 167).
  * IIR pasa-bajos Chebyshev I diseñado en formato SOS (fp = 40, fr = 60,
    Rp = 1 dB, As = 40 dB). Se comenta por qué NO se usa Butterworth (N = 13).
  * Notch IIR de 50 Hz (red eléctrica) con ``iirnotch``.

Para cada filtro se grafica: respuesta en frecuencia (|H| en dB y fase),
retardo de grupo, diagrama de polos-ceros (zplane casero) y respuesta al
impulso. Además se imprimen los primeros/últimos coeficientes del FIR y se
verifica su simetría (condición de fase lineal).

Coherencia numérica con el KB (03-iir.md, 07-python.md):
  * FIR Hamming: numtaps ≈ 167 (orden N ≈ 166).
  * Butterworth para esta máscara daría N = 13 (inviable en forma directa)
    -> se elige Chebyshev I (N ≈ 6) o elíptico (N ≈ 4) en SOS.
  * Notch 50 Hz, Q = 30.

Ejecutar:  python diseno_filtros.py
"""

from __future__ import annotations

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Parámetros del caso ECG (Anexo I-A)
# ----------------------------------------------------------------------------
FS = 500.0          # frecuencia de muestreo [Hz]
FP = 40.0           # borde de banda pasante [Hz]
FR = 60.0           # borde de banda de rechazo [Hz]
RP = 1.0            # ondulación máxima en banda pasante [dB]
AS = 40.0           # atenuación mínima en banda de rechazo [dB]
F_NOTCH = 50.0      # frecuencia de red a eliminar [Hz]
Q_NOTCH = 30.0      # factor de calidad del notch


# ----------------------------------------------------------------------------
# Diseño FIR — método de ventanas (Hamming)
# ----------------------------------------------------------------------------
def disenar_fir(fs: float = FS, fc: float = FP, numtaps: int = 167) -> np.ndarray:
    """Diseña un FIR pasa-bajos de fase lineal con ventana Hamming.

    numtaps impar => filtro tipo I (fase lineal exacta por simetría de h[n]).
    El KB fija numtaps ≈ 167 (orden N ≈ 166) para fc = 40 Hz con Hamming.
    """
    if numtaps % 2 == 0:                       # forzamos longitud impar (tipo I)
        numtaps += 1
    # pass_zero=True -> deja pasar DC (LP); scale=True -> ganancia DC unidad.
    h = signal.firwin(numtaps, cutoff=fc, fs=fs, window="hamming", pass_zero=True)
    return h


# ----------------------------------------------------------------------------
# Diseño IIR — Chebyshev I en SOS
# ----------------------------------------------------------------------------
def disenar_iir_cheby1(fs: float = FS, fp: float = FP, fr: float = FR,
                       rp: float = RP, ats: float = AS) -> np.ndarray:
    """Diseña un IIR pasa-bajos Chebyshev I en formato SOS.

    NOTA DE DISEÑO (03-iir.md §6.4):
      Butterworth para esta máscara (40->60 Hz, 1 dB / 40 dB) requiere N = 13,
      inviable en forma directa. Chebyshev I baja el orden a N ≈ 6 (y el
      elíptico a N ≈ 4). Se usa SOS porque es numéricamente estable para
      órdenes >= 4 (cada biquad se cuantiza por separado).
    """
    # cheb1ord estima el orden mínimo y la frecuencia crítica que cumplen el
    # gabarito (gpass = Rp, gstop = As).
    n, wn = signal.cheb1ord(wp=fp, ws=fr, gpass=rp, gstop=ats, fs=fs)
    sos = signal.cheby1(n, rp, wn, btype="low", output="sos", fs=fs)
    return n, sos


def disenar_iir_elliptico(fs: float = FS, fp: float = FP, fr: float = FR,
                          rp: float = RP, ats: float = AS) -> np.ndarray:
    """Diseña un IIR pasa-bajos elíptico en SOS (alternativa de orden mínimo).

    El elíptico (Cauer) da la transición más abrupta para el menor orden
    (N ≈ 4 para esta máscara), a costa de ripple en ambas bandas y peor fase.
    """
    n, wn = signal.ellipord(wp=fp, ws=fr, gpass=rp, gstop=ats, fs=fs)
    sos = signal.ellip(n, rp, ats, wn, btype="low", output="sos", fs=fs)
    return n, sos


# ----------------------------------------------------------------------------
# Diseño Notch IIR 50 Hz
# ----------------------------------------------------------------------------
def disenar_notch(fs: float = FS, f0: float = F_NOTCH, q: float = Q_NOTCH):
    """Diseña un notch IIR de 2.º orden y lo entrega como (b, a) y como SOS."""
    b, a = signal.iirnotch(w0=f0, Q=q, fs=fs)
    sos = signal.tf2sos(b, a)
    return b, a, sos


# ----------------------------------------------------------------------------
# Diagrama de polos-ceros (zplane casero: scipy/matplotlib no tienen zplane)
# ----------------------------------------------------------------------------
def zplane(z: np.ndarray, p: np.ndarray, ax=None, titulo: str = "Polos-ceros"):
    """Dibuja el círculo unitario + ceros (o) y polos (x). Estable ⟺ |p| < 1."""
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), "k--", lw=1)            # círculo unitario
    ax.scatter(np.real(z), np.imag(z), marker="o", facecolors="none",
               edgecolors="b", label="ceros")
    ax.scatter(np.real(p), np.imag(p), marker="x", color="r", label="polos")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("Re")
    ax.set_ylabel("Im")
    ax.set_title(titulo)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    return ax


# ----------------------------------------------------------------------------
# Verificación de simetría del FIR (fase lineal)
# ----------------------------------------------------------------------------
def verificar_simetria(h: np.ndarray) -> bool:
    """Comprueba h[n] == h[N-n] (simetría par => fase lineal tipo I)."""
    simetrico = bool(np.allclose(h, h[::-1], atol=1e-12))
    return simetrico


# ----------------------------------------------------------------------------
# Gráficas de caracterización
# ----------------------------------------------------------------------------
def graficar_fir(h: np.ndarray, fs: float = FS) -> None:
    """Respuesta en frecuencia, retardo de grupo, polos-ceros e impulso (FIR)."""
    w, H = signal.freqz(h, 1, worN=4096, fs=fs)
    mag_db = 20 * np.log10(np.abs(H) + 1e-12)
    fase = np.unwrap(np.angle(H)) * 180 / np.pi
    w_gd, gd = signal.group_delay((h, 1), fs=fs)
    z, p, k = signal.tf2zpk(h, 1)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle("FIR LP Hamming (fc = 40 Hz) — caracterización")

    ax = axes[0, 0]
    ax.plot(w, mag_db)
    ax.axvline(FP, color="r", ls="--", lw=1, label="fc = 40 Hz")
    ax.axhline(-AS, color="g", ls=":", lw=1, label="-40 dB")
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("|H| [dB]")
    ax.set_ylim(-100, 5)
    ax.set_title("Magnitud y fase")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)
    ax_fase = ax.twinx()
    ax_fase.plot(w, fase, color="orange", alpha=0.6)
    ax_fase.set_ylabel("Fase [°]", color="orange")

    ax = axes[0, 1]
    ax.plot(w_gd, gd)
    ax.axhline((len(h) - 1) / 2, color="r", ls="--", lw=1,
               label=f"N/2 = {(len(h) - 1) / 2:.0f}")
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("Retardo de grupo [muestras]")
    ax.set_title("Retardo de grupo (constante => fase lineal)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    zplane(z, p, ax=axes[1, 0], titulo="Polos-ceros (todos los polos en z=0)")

    ax = axes[1, 1]
    ax.stem(np.arange(len(h)), h)
    ax.set_xlabel("n")
    ax.set_ylabel("h[n]")
    ax.set_title("Respuesta al impulso (= coeficientes, simétricos)")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()


def graficar_sos(sos: np.ndarray, fs: float, titulo: str, fc_marca: float) -> None:
    """Respuesta en frecuencia, retardo de grupo, polos-ceros e impulso (IIR SOS)."""
    w, H = signal.sosfreqz(sos, worN=4096, fs=fs)
    mag_db = 20 * np.log10(np.abs(H) + 1e-12)
    fase = np.unwrap(np.angle(H)) * 180 / np.pi
    # group_delay trabaja con (b, a): convertimos la cascada SOS a forma global.
    b, a = signal.sos2tf(sos)
    w_gd, gd = signal.group_delay((b, a), fs=fs)
    z, p, k = signal.sos2zpk(sos)
    # Respuesta al impulso (causal) aplicando el filtro a un delta.
    impulso = np.zeros(64)
    impulso[0] = 1.0
    h_imp = signal.sosfilt(sos, impulso)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle(titulo)

    ax = axes[0, 0]
    ax.plot(w, mag_db)
    ax.axvline(fc_marca, color="r", ls="--", lw=1, label=f"{fc_marca:g} Hz")
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("|H| [dB]")
    ax.set_ylim(-100, 5)
    ax.set_title("Magnitud y fase")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)
    ax_fase = ax.twinx()
    ax_fase.plot(w, fase, color="orange", alpha=0.6)
    ax_fase.set_ylabel("Fase [°]", color="orange")

    ax = axes[0, 1]
    ax.plot(w_gd, gd)
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("Retardo de grupo [muestras]")
    ax.set_title("Retardo de grupo (IIR: NO constante)")
    ax.grid(True, alpha=0.3)

    estable = np.all(np.abs(p) < 1)
    zplane(z, p, ax=axes[1, 0],
           titulo=f"Polos-ceros ({'ESTABLE' if estable else 'INESTABLE'}: |p|<1)")

    ax = axes[1, 1]
    ax.stem(np.arange(len(h_imp)), h_imp)
    ax.set_xlabel("n")
    ax.set_ylabel("h[n]")
    ax.set_title("Respuesta al impulso (infinita, decae)")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("DISEÑO DE FILTROS — caso ECG, fs = 500 Hz")
    print("=" * 70)

    # --- FIR ---------------------------------------------------------------
    h = disenar_fir()
    print(f"\n[FIR] Ventana Hamming, fc = {FP:g} Hz")
    print(f"  numtaps        = {len(h)}  (orden N = {len(h) - 1})")
    print(f"  primeros coef. = {np.array2string(h[:4], precision=6)}")
    print(f"  últimos  coef. = {np.array2string(h[-4:], precision=6)}")
    print(f"  suma coef. (ganancia DC) = {np.sum(h):.6f}  (≈ 1.0)")
    sim = verificar_simetria(h)
    print(f"  ¿h[n] simétrico? {sim}  => fase lineal exacta")
    print(f"  retardo de grupo constante = N/2 = {(len(h) - 1) / 2:.1f} muestras"
          f" ({(len(h) - 1) / 2 / FS * 1000:.1f} ms)")

    # --- IIR Chebyshev I (con nota sobre Butterworth) ----------------------
    # Comprobación didáctica: Butterworth para la misma máscara da N = 13.
    n_butter, _ = signal.buttord(wp=FP, ws=FR, gpass=RP, gstop=AS, fs=FS)
    n_cheb, sos_cheb = disenar_iir_cheby1()
    n_ellip, sos_ellip = disenar_iir_elliptico()
    print(f"\n[IIR] Comparativa de orden para la máscara "
          f"(fp={FP:g}, fr={FR:g}, Rp={RP:g} dB, As={AS:g} dB):")
    print(f"  Butterworth  -> N = {n_butter}  (inviable en forma directa)")
    print(f"  Chebyshev I  -> N = {n_cheb}   (elegido, SOS: {sos_cheb.shape[0]} secciones)")
    print(f"  Elíptico     -> N = {n_ellip}   (orden mínimo, SOS: {sos_ellip.shape[0]} secciones)")
    z_c, p_c, _ = signal.sos2zpk(sos_cheb)
    print(f"  Cheby1 estable (max|polo| = {np.max(np.abs(p_c)):.4f} < 1): "
          f"{np.all(np.abs(p_c) < 1)}")

    # --- Notch 50 Hz -------------------------------------------------------
    b_n, a_n, sos_n = disenar_notch()
    print(f"\n[NOTCH] iirnotch 50 Hz, Q = {Q_NOTCH:g}")
    print(f"  b = {np.array2string(b_n, precision=6)}")
    print(f"  a = {np.array2string(a_n, precision=6)}")

    # --- Gráficas ----------------------------------------------------------
    graficar_fir(h)
    graficar_sos(sos_cheb, FS, f"IIR Chebyshev I N={n_cheb} (LP 40 Hz) — caracterización", FP)
    graficar_sos(sos_n, FS, "Notch IIR 50 Hz — caracterización", F_NOTCH)

    print("\nMostrando gráficas (cierre las ventanas para terminar)...")
    plt.show()


if __name__ == "__main__":
    main()
