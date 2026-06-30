# Proyecto PDS — Filtrado Digital FIR/IIR asistido por IA (ECG)

Resolución del *Examen Parcial Integrador — Técnicas Digitales III — Procesamiento Digital de Señales / Filtrado Digital (2026)*.
**Aplicación elegida:** Opción A — ECG (fs = 500 Hz): Notch IIR 50 Hz + Pasa-bajos FIR fc = 40 Hz + agente de decisión IA + implementación embebida en ESP32.

## Estructura del proyecto
```
preuba-ia2/
├── informe/INFORME.md                 ← Informe Final (estructura académica, 12 secciones)
├── presentacion/PRESENTACION.md       ← Slides Marp (27 diapositivas)
├── entrega_octave/
│   ├── APUNTES_OCTAVE.md              ← apuntes teóricos enfoque Octave
│   └── ejemplos/                       diseno_filtros.m · procesar_senal.m · agente_decision.m
├── entrega_python/
│   ├── APUNTES_PYTHON.md              ← apuntes teóricos enfoque Python
│   └── ejemplos/                       diseno_filtros.py · procesar_senal.py · agente_decision.py · agente_llm.py
├── entrega_embebido/                   filtro_ecg_esp32.ino · coeficientes.h · README.md
├── _kb/                                base de conocimiento modular (INDEX + 8 módulos)
└── EXAMEN PARCIAL INTEGRADOR PDS 2026.docx
```

## Mapeo a los 8 entregables de la consigna (Sección 6)
| # | Entregable exigido | Formato pedido | En este proyecto | Estado |
|---|--------------------|----------------|------------------|--------|
| 1 | Informe Final | PDF, máx. 50 pág., Arial 11 | [informe/INFORME.md](informe/INFORME.md) → [INFORME.docx](informe/INFORME.docx) | ✅ DOCX con Arial 11 / 1.15 / 2.5 cm y ecuaciones nativas (PDF: *Guardar como* desde Word) |
| 2 | Scripts MATLAB/Octave | `.m` ejecutable | [entrega_octave/ejemplos/](entrega_octave/ejemplos/) | ✅ |
| 3 | Documentación del Agente de IA | `.py`/`.ipynb`/`.m`/pseudocódigo | [entrega_python/ejemplos/agente_decision.py](entrega_python/ejemplos/agente_decision.py), [agente_llm.py](entrega_python/ejemplos/agente_llm.py) | ✅ |
| 4 | Código fuente embebido | C/C++/`.ino` | [entrega_embebido/](entrega_embebido/) | ✅ (ESP32) |
| 5 | Gráficos de simulación | PDF/PNG ≥150 dpi | se generan al correr `diseno_filtros.*`/`procesar_senal.*` | ⚠️ requiere ejecutar los scripts |
| 6 | Dataset (opcional) | `.csv`/`.mat`/`.wav` | señal ECG sintética generada en los scripts | ✅ (sintético) |
| 7 | Video demostración | MP4/enlace, 5–10 min | — | ⛔ a cargo del grupo |
| 8 | Presentación | PPTX/PDF, máx. 30 slides | [presentacion/PRESENTACION.md](presentacion/PRESENTACION.md) → [PRESENTACION.pptx](presentacion/PRESENTACION.pptx) | ✅ PPTX de 27 diapositivas (≤30) |

## Material teórico y de apoyo
- **Apuntes** (insumo del marco teórico): [APUNTES_OCTAVE.md](entrega_octave/APUNTES_OCTAVE.md) · [APUNTES_PYTHON.md](entrega_python/APUNTES_PYTHON.md)
- **Knowledge base** modular: [_kb/INDEX.md](_kb/INDEX.md) (fundamentos PDS, FIR, IIR, criterios, agente IA, herramientas Octave/Python)

## Formatos generados y pasos restantes
- **Informe:** `informe/INFORME.docx` generado con pandoc (Arial 11, interlineado 1.15, A4 márgenes 2.5 cm, ecuaciones nativas de Word). Para el **PDF**: abrir en Word → *Guardar como PDF* (o `pandoc INFORME.md -o INFORME.pdf` si se instala un motor LaTeX).
- **Presentación:** `presentacion/PRESENTACION.pptx` generado con pandoc (27 diapositivas). El `.md` sigue siendo Marp válido por si se prefiere ese render.
- **Figuras ≥150 dpi** (entregable #5): ejecutar los scripts `.m`/`.py` (necesitan Octave / Python con numpy-scipy-matplotlib).

## Notas
- Ejemplo numérico canónico en todo el proyecto: FIR Hamming **N=166**; IIR Butterworth **N=13** → motiva Chebyshev I **N≈6** / elíptico **N≈4** con estructura **SOS**; notch 50 Hz.
- Falta a cargo del grupo: completar datos de carátula, generar el video (#7) y, opcionalmente, ejecutar scripts para exportar figuras y convertir informe/slides a sus formatos finales.
