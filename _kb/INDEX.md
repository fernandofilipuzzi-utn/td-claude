# INDEX · Knowledge Base — Apuntes PDS (Octave + Python)

Índice maestro del repositorio de conocimiento. Cada módulo es un markdown autónomo y enlazable; los documentos finales (`entrega_octave/APUNTES_OCTAVE.md`, `entrega_python/APUNTES_PYTHON.md`) se sintetizan a partir de estos módulos.

## Cómo usar este índice (para subagentes)
1. Leer **siempre** `00-enunciado.md` para el contexto del problema.
2. Redactar **solo** el módulo asignado; no duplicar contenido de otros módulos: enlazarlos con `[[ruta]]`.
3. Español técnico, Markdown. Ecuaciones en LaTeX inline `$...$` o bloque `$$...$$`. Código en bloques con lenguaje.
4. No ejecutar ni instalar nada. Las APIs/firmas de función deben basarse en documentación estándar conocida.

## Módulos (KB)
| Archivo | Tema | Especialidad responsable |
|---------|------|--------------------------|
| `00-enunciado.md` | Resumen del examen (contexto compartido) | — (semilla) |
| `01-fundamentos-pds.md` | Muestreo, Nyquist, espectro, DTFT/Z, convolución, métricas SNR/RMSE, retardo de grupo, fase lineal | Teoría de PDS |
| `02-fir.md` | FIR: ventanas, Parks-McClellan, orden, `h[n]`, simetría/fase lineal, `H(z)`, criterios FIR | Diseño de filtros FIR |
| `03-iir.md` | IIR: prototipos analógicos, orden, `Ha(s)`, transformada bilineal + prewarping, `H(z)`, ec. en diferencias, estabilidad, SOS | Diseño de filtros IIR |
| `04-criterios-diseno.md` | Criterios de ingeniería: FIR vs IIR, elección de ventana/prototipo, orden/memoria/MACs, punto fijo vs flotante, restricciones embebidas | Criterio de ingeniería / selección |
| `05-agente-ia.md` | Agente de decisión: reglas IF-THEN, árbol (sklearn), lógica difusa, API IA generativa, MLP; **cómo se genera** cada uno, variables E/S, validación, ejemplos | IA / sistemas de decisión |
| `06-octave.md` | Herramientas Octave: paquete `signal` (fir1, kaiserord, firpm, butter, cheby1/2, ellip, *ord, freqz, grpdelay, zplane, filter, sosfilt, fft, pwelch); cómo funcionan + ejemplos | Implementación Octave/MATLAB |
| `07-python.md` | Herramientas Python: numpy, scipy.signal (firwin, remez, butter, cheby1/2, ellip, *ord, freqz, sos*, lfilter, filtfilt), matplotlib, scikit-learn, scikit-fuzzy, SDK anthropic; cómo funcionan + ejemplos | Implementación Python científico |

## Documentos finales (síntesis)
| Documento | Fuentes KB | Enfoque |
|-----------|-----------|---------|
| `entrega_octave/APUNTES_OCTAVE.md` | 00,01,02,03,04,05(reglas/IF-THEN),06 | Fundamentos + herramientas Octave + agente como sistema experto en Octave/MATLAB + criterios |
| `entrega_python/APUNTES_PYTHON.md` | 00,01,02,03,04,05(ML/fuzzy/LLM),07 | Fundamentos + herramientas Python + agente con sklearn/fuzzy/LLM + criterios |

## Mapa temas → pasos del examen
- Paso 1 → `01`, `04`
- Paso 2 → `02`, `03`
- Paso 3 → `06` (Octave) · `07` (Python, scipy)
- Paso 4 → `05`
- Paso 5 (embebido) → `04` (punto fijo, MACs, restricciones)
