# Ejemplos Octave/MATLAB — Filtrado Digital FIR/IIR (caso ECG)

Scripts de referencia ejecutables para el examen de filtrado digital
(Anexo I-A: ECG, `fs = 500 Hz`, Notch 50 Hz + LP FIR fc = 40 Hz, fase lineal
para preservar la morfología P-QRS-T).

## Requisitos

- **Octave 7.x / 8.x** con el paquete `signal` (Octave Forge), o
- **MATLAB R2021b+** con la *Signal Processing Toolbox*.

En **Octave** hay que cargar el paquete `signal` una vez por sesión:

```matlab
pkg load signal      % cada arranque de Octave
% pkg install -forge signal   % instalación única (solo si no está instalado)
```

> En **MATLAB no** se usa `pkg load`. Todos los scripts traen al inicio la
> guarda portable `if exist('OCTAVE_VERSION','builtin'); pkg load signal; end`,
> así que funcionan en ambos entornos sin tocar nada.

## Orden sugerido de ejecución

```matlab
diseno_filtros      % 1) diseña y caracteriza los filtros (figuras + consola)
procesar_senal      % 2) pipeline completo sobre ECG sintético (figuras + tabla)
agente_decision     % 3) demo del agente experto (3 escenarios por consola)
```

Cada script es **autónomo**: no descarga datasets ni depende de los otros.

## Qué hace cada script

| Archivo | Descripción |
|---|---|
| `diseno_filtros.m` | Diseña el **FIR LP Hamming** (fc = 40 Hz, orden 166), el **IIR LP Chebyshev I** en formato **SOS** (orden ≈ 6; se comenta que Butterworth daría N = 13) y el **Notch IIR 50 Hz**. Grafica `freqz` (módulo dB y fase), `grpdelay`, `zplane` e `impz`. Imprime los primeros/últimos 5 coeficientes FIR y **verifica la simetría** (fase lineal). |
| `procesar_senal.m` | Genera un **ECG sintético** (suma de gaussianas P-QRS-T) + interferencia de **red 50 Hz** + **ruido EMG** de alta frecuencia. Aplica el FIR (`fftfilt`) y el camino IIR (`filter` notch + `sosfilt`). Grafica tiempo y **espectro FFT** antes/después y calcula **SNR / RMSE** manuales, imprimiendo una **tabla comparativa FIR vs IIR** (orden, MACs/muestra, fase, SNR). |
| `agente_decision.m` | Sistema experto **IF-THEN** `agente_decision(specs)`. Devuelve `struct` con `.tipo`, `.estructura`, `.justificacion`, `.confianza`. Implementa ≥ 6 reglas (fase lineal→FIR; RAM<2 kB y orden FIR>50→IIR/SOS; sin FPU→SOS; transición exigente con cómputo→IIR; etc.). Llamado **sin argumentos** ejecuta la validación con 3 escenarios. |

## Notas

- Las **figuras se muestran en pantalla** (ventanas `figure`); no se guardan en disco.
- `procesar_senal.m` fija la semilla del ruido (`randn('seed',42)`) para resultados reproducibles.
- Funciones específicas de Octave usadas: `printf` (en MATLAB equivale a `fprintf`).
  Los scripts funcionan igual en MATLAB porque `printf` también existe como
  builtin en él; si su versión no lo tuviera, reemplazar `printf` por `fprintf`.

## Coherencia numérica (KB)

- FIR: `Wn = 40/250 = 0.16`, orden **N = 166** (167 coeficientes), retardo de
  grupo constante = 83 muestras.
- IIR Chebyshev I: orden **N ≈ 6** (`cheb1ord`), realizado en **SOS**.
  El **elíptico** daría **N ≈ 4** (orden mínimo). **Butterworth** exigiría
  **N = 13** con la misma máscara (`fp=40, fr=60, Rp=1, As=40`), de ahí el
  cambio de prototipo y el uso de SOS.
- Notch IIR de 2.º orden centrado en **50 Hz** (`w0 = 0.20`, Q = 35).
