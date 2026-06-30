# 00 · Resumen del enunciado (contexto compartido)

> **Uso:** archivo de contexto canónico. Todo subagente debe leerlo antes de redactar.
> Fuente: *EXAMEN PARCIAL INTEGRADOR — Técnicas Digitales III — PDS / Filtrado Digital (2026)*.

## Proyecto
Diseño, simulación e implementación de un **sistema de filtrado digital FIR/IIR asistido por IA** para una aplicación de ingeniería. Modalidad grupal, Evaluación Basada en Problemas (EBP). Herramientas permitidas: MATLAB/Octave, Python, IA generativa, plataformas embebidas, simuladores.

## Los 5 pasos evaluables
| Paso | Título | Núcleo técnico |
|------|--------|----------------|
| **1** | Análisis del problema y especificaciones | Caracterizar señal; `fs` justificado por Nyquist-Shannon; banda útil vs ruido; tipo de filtro (LP/HP/BP/BR-notch); `fp`, `fr`, `Rp` (dB), `As` (dB); fase lineal sí/no; tabla de requerimientos |
| **2** | Desarrollo matemático del diseño | **FIR:** método (ventanas Rect/Hann/Hamming/Blackman/Kaiser o Parks-McClellan), orden `N`, coeficientes `h[n]`, simetría → fase lineal, `H(z)`. **IIR:** prototipo (Butterworth/Cheby I/Cheby II/Elíptico), orden `N`, `Ha(s)` polos/ceros, **Transformada Bilineal** con pre-distorsión (prewarping), `H(z)`, ecuación en diferencias, estabilidad (polos dentro del círculo unitario) |
| **3** | Simulación en MATLAB/Octave | Respuesta en frecuencia (\|H\| dB y fase), respuesta al impulso `h[n]`, retardo de grupo, polos-ceros (zplane); señal contaminada antes/después; FFT/PSD; métricas SNR/RMSE/distorsión de fase; **tabla comparativa FIR vs IIR** (orden, MACs/muestra, fase/retardo, estabilidad, memoria, calidad) |
| **4** | **Agente de decisión asistido por IA** | Sistema que recomienda **FIR o IIR** + estructura (DF I, DF II, SOS, lattice) según restricciones. Ver detalle abajo |
| **5** | Implementación en microcontrolador | Arduino/STM32/ESP32; punto fijo (Q) vs float; buffers; pseudocódigo + código C/MicroPython; validación vs simulación; fuentes de error (cuantización, truncamiento, aliasing, latencia) |

## Paso 4 — Agente de IA (detalle clave para los documentos)
**Variables de entrada** (mín.): `fs` (Hz); memoria µC (kB RAM/Flash); cómputo (MIPS/MHz); fase lineal (sí/no); nivel de ruido / SNR entrada (dB); latencia (baja/media/alta); pendiente de transición (estrecha/amplia).

**Salidas:** recomendación FIR/IIR; estructura sugerida (DF I/II, SOS cascada, lattice); justificación en lenguaje natural o tabla de reglas activadas; nivel de confianza (opcional).

**Estrategias de implementación (elegir y justificar una):**
1. Reglas IF-THEN (sistema experto).
2. Árbol de decisión (scikit-learn u otro).
3. Lógica difusa (grados de pertenencia).
4. IA generativa vía API (prompts estructurados a GPT/Claude).
5. Red neuronal simple (MLP) entrenada con datos sintéticos.

**Reglas de referencia (no exhaustivas):** fase lineal estricta → FIR · RAM < 2 kB y orden FIR > 50 → IIR · estabilidad numérica crítica sin DSP float → SOS · transición exigente con cómputo suficiente → IIR de orden adecuado.

**Validación:** ≥3 escenarios de restricciones distintos; coherencia con Pasos 1–3.

## Opciones de aplicación (Anexo I) — referencia rápida
A: ECG (fs 500 Hz, Notch 50/60 IIR + LP FIR fc 40, fase lineal preserva P-QRS-T). B: Acelerómetro MEMS rodamiento (fs 1 kHz, BP FIR 10–200 + LP IIR). C: PPG cardíaco (fs 100–250 Hz, BP FIR 0.5–4 Hz Kaiser). D: EMG (fs 1 kHz, BP FIR 20–500 + rectificación + LP IIR envolvente). E: Temperatura PT100 (fs 10–50 Hz, mediana + Butterworth orden 2). F: Presión bomba (fs 500 Hz, notch ajustable + LP FIR). G: Nivel ultrasónico (fs 50–100 Hz, mediana + EMA). H: Corriente/armónicos (fs 2–5 kHz, banco BP + THD). I: Encoder/velocidad (fs 0.5–1 kHz, derivador + LP IIR). J: SpO₂/CGM (fs 1–10 Hz, LP FIR + HP IIR deriva).

## Datasets públicos (Anexo II)
PhysioNet (MIT-BIH NSTDB ECG+ruido `nstdb`, MIT-BIH Arrhythmia `mitdb`, BIDMC PPG, EMG), CWRU Bearing, NASA IMS Bearing, Mendeley PPG. Conversión a CSV con `wfdb` (Python).

## Restricciones de plataforma (síntesis Anexo I)
- **Arduino UNO** (16 MHz, 2 kB RAM, sin FPU): favorece **IIR** de orden bajo / punto fijo; FIR de orden alto inviable.
- **ESP32 / STM32** (decenas-cientos MHz, FPU): admiten **FIR** de orden alto y float.
- Coste FIR ≈ `N+1` MACs/muestra; IIR (SOS) ≈ `5·(secciones)` MACs/muestra.

## Restricciones operativas de este trabajo
No ejecutar acciones externas (correo, git commit/push/PR). No instalar paquetes sin consultar. Los documentos son **apuntes técnicos** (Markdown, español): explican fundamentos, herramientas, ejemplos de uso, generación del agente y criterios de diseño de filtros.
