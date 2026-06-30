# 06 · Octave/MATLAB para PDS — Referencia de herramientas (paquete `signal`)

> **Tipo:** referencia práctica de funciones con firmas, parámetros y ejemplos cortos.
> **Caso de hilo conductor:** ECG con `fs = 500 Hz` (Notch 50 Hz IIR + LP FIR fc = 40 Hz, fase lineal para preservar P-QRS-T).
> Enlaces: [[01-fundamentos-pds]] · [[02-fir]] · [[03-iir]] · [[05-agente-ia]]

Las firmas siguen la documentación estándar del **paquete `signal` de Octave** (compatible en su mayoría con la *Signal Processing Toolbox* de MATLAB). Cuando hay diferencias relevantes MATLAB/Octave se indican explícitamente.

---

## 1. Entorno

### Octave vs MATLAB
- **Octave** es libre y mayormente compatible a nivel de sintaxis con MATLAB. Las funciones de PDS NO vienen en el núcleo: están en el paquete **`signal`** (de *Octave Forge*), que a su vez depende del paquete **`control`**.
- En **MATLAB**, las mismas funciones pertenecen a la *Signal Processing Toolbox* (no hace falta `pkg load`; basta que la toolbox esté instalada).

### Carga del paquete (solo Octave)
```matlab
pkg load signal     % carga el paquete en la sesión actual (necesario cada arranque)
% pkg install -forge signal   % instalación única (NO ejecutar aquí; solo documentado)
pkg list                       % verifica qué paquetes están cargados/instalados
```
> En MATLAB **no** se usa `pkg load`; si se escribe, da error. Proteger scripts portables con:
> ```matlab
> if exist('OCTAVE_VERSION', 'builtin'); pkg load signal; end
> ```

### Compatibilidad
- Probado conceptualmente con **Octave 7.x / 8.x** (paquete `signal` ≥ 1.4) y **MATLAB R2021b+**.
- Diferencias típicas: en Octave algunos diseños IIR devuelven por defecto `[b,a]`; el formato `sos` y la salida `[z,p,k]` se obtienen pidiendo el nº de argumentos de salida correspondiente. `iirnotch`, `phasez` y `pwelch` existen en ambos con firmas casi idénticas (ver notas puntuales abajo).

---

## 2. Diseño FIR

> Concepto y elección de método en [[02-fir]]. Regla práctica: `Wn` (frecuencia normalizada) = `fc / (fs/2)`, es decir, fracción de la frecuencia de Nyquist, en el rango `(0,1)`.

### 2.1 Ventanas
| Función | Firma | Devuelve |
|---|---|---|
| `hamming` | `w = hamming(L)` | vector ventana de Hamming, longitud `L` |
| `hanning` | `w = hanning(L)` | ventana de Hann (von Hann) |
| `blackman` | `w = blackman(L)` | ventana de Blackman |
| `rectwin` | `w = rectwin(L)` | ventana rectangular (todo unos) |
| `kaiser` | `w = kaiser(L, beta)` | ventana de Kaiser con parámetro `beta` (β) |

- `L` = longitud = **orden + 1** (un FIR de orden `N` tiene `N+1` coeficientes).
- `beta` controla el compromiso lóbulo-principal / lóbulos-laterales (atenuación). Mayor β ⇒ más atenuación y transición más ancha.

```matlab
w = hamming(101);     % ventana para un FIR de orden 100
```

### 2.2 `fir1` — FIR por método de ventanas
```matlab
b = fir1(N, Wn)                 % LP por defecto, ventana Hamming
b = fir1(N, Wn, 'high')         % HP
b = fir1(N, [W1 W2])            % BP (Wn vector de 2)
b = fir1(N, [W1 W2], 'stop')    % BR / band-stop
b = fir1(N, Wn, window)         % especifica ventana (vector de longitud N+1)
```
- **`N`**: orden del filtro (devuelve `N+1` coeficientes `b`).
- **`Wn`**: frecuencia(s) de corte normalizada(s) a Nyquist, `Wn = fc/(fs/2)`.
- **`window`**: vector ventana (p. ej. `hamming(N+1)`, `kaiser(N+1,beta)`).
- **Devuelve** `b` (coeficientes FIR, `a = 1` implícito). Fase lineal por simetría de `b`.

**Ejemplo — LP Hamming fc = 40 Hz, fs = 500 Hz (caso ECG):**
```matlab
fs = 500;  fc = 40;
Wn = fc / (fs/2);          % = 40/250 = 0.16
N  = 100;                  % orden (par ⇒ Tipo I, fase lineal, simétrico)
b  = fir1(N, Wn, hamming(N+1));   % LP equivalente, ventana Hamming explícita
```

### 2.3 `fir2` — FIR con respuesta arbitraria (por muestreo en frecuencia)
```matlab
b = fir2(N, f, m)
```
- **`f`**: vector de frecuencias normalizadas (0→1, monótono, empieza en 0 y termina en 1).
- **`m`**: magnitud deseada en cada `f`.
- Útil para respuestas no estándar (rampas, multibanda con forma).
```matlab
b = fir2(80, [0 0.1 0.16 1], [1 1 0 0]);   % LP con transición definida a mano
```

### 2.4 `firls` — FIR óptimo por mínimos cuadrados
```matlab
b = firls(N, f, a)
```
- Minimiza el **error cuadrático** entre `H` y la respuesta deseada definida por bandas.
- **`f`**: pares de bordes de banda (normalizados, 0→1). **`a`**: amplitud deseada en cada borde.
```matlab
b = firls(100, [0 0.14 0.18 1], [1 1 0 0]);  % LP, paso/rechazo por mínimos cuadrados
```

### 2.5 `firpm` — Parks-McClellan (Remez, equiripple)
```matlab
b = firpm(N, f, a)
b = firpm(N, f, a, w)        % w: pesos relativos por banda
```
- Diseño **equiripple** (rizado uniforme) óptimo de Chebyshev — minimiza el error **máximo**.
- En Octave clásico la función equivalente histórica es `remez`; `firpm` es el alias compatible con MATLAB.
- **`f`**, **`a`** como en `firls`; **`w`** pondera el peso de cada banda (p. ej. exigir más rechazo).
```matlab
b = firpm(60, [0 0.14 0.18 1], [1 1 0 0], [1 10]);  % rechazo 10x más penalizado
```

### 2.6 `kaiserord` — estimar orden y β de Kaiser
```matlab
[N, Wn, beta, ftype] = kaiserord(f, a, dev)
[N, Wn, beta, ftype] = kaiserord(f, a, dev, fs)   % f en Hz si se pasa fs
```
- **Entradas:** `f` bordes de banda, `a` amplitudes por banda (1/0), `dev` desviación máxima permitida por banda (lineal, no dB).
- **Devuelve** el **orden `N`**, las cortes `Wn`, el **`beta`** y `ftype` listos para pasar a `fir1`.
- Conversión dB→lineal: `dev_paso = (10^(Rp/20)-1)/(10^(Rp/20)+1)`, `dev_rechazo = 10^(-As/20)`.

**Ejemplo (caso ECG, transición 40→50 Hz):**
```matlab
fs = 500;
dev = [(10^(1/20)-1)/(10^(1/20)+1), 10^(-40/20)];  % Rp=1 dB, As=40 dB
[N, Wn, beta, ftype] = kaiserord([40 50], [1 0], dev, fs);
b = fir1(N, Wn, ftype, kaiser(N+1, beta), 'noscale');
```

---

## 3. Diseño IIR

> Prototipos y bilineal con prewarping en [[03-iir]]. Convención general de las funciones de diseño: las frecuencias se dan **normalizadas a Nyquist** salvo que se use la opción `'s'` (analógico), donde son rad/s.

### 3.1 Prototipos
| Función | Firma básica | Característica |
|---|---|---|
| `butter` | `[b,a] = butter(N, Wn)` | Butterworth: plano en banda de paso, sin rizado |
| `cheby1` | `[b,a] = cheby1(N, Rp, Wn)` | Cheby I: rizado `Rp` dB en paso, monótono en rechazo |
| `cheby2` | `[b,a] = cheby2(N, Rs, Wn)` | Cheby II: monótono en paso, rizado en rechazo (`Rs` dB) |
| `ellip` | `[b,a] = ellip(N, Rp, Rs, Wn)` | Elíptico: rizado en ambas bandas, transición mínima |

**Opciones comunes a las cuatro:**
```matlab
[b,a]   = butter(N, Wn)            % LP digital, salida coef. transferencia
[b,a]   = butter(N, Wn, 'high')    % HP
[b,a]   = butter(N, [W1 W2])       % BP
[b,a]   = butter(N, [W1 W2],'stop')% BR
[z,p,k] = butter(N, Wn)            % salida cero-polo-ganancia (recomendado para estabilidad)
[A,B,C,D]= butter(N, Wn)           % espacio de estados
[b,a]   = butter(N, Wn, 's')       % prototipo ANALÓGICO (Wn en rad/s)
```
- **`Wn`** digital = `fc/(fs/2)`. **`'s'`** ⇒ diseño analógico `Ha(s)` (Wn en rad/s), útil para mostrar el prototipo antes de la bilineal.
- Para **SOS** (segundas secciones, mejor condicionamiento numérico) combinar con `zp2sos` (ver §5.3):
  ```matlab
  [z,p,k] = butter(N, Wn);  sos = zp2sos(z,p,k);
  ```

### 3.2 Estimadores de orden
```matlab
[N, Wn] = buttord(Wp, Ws, Rp, Rs)        % Rp = rizado máx. paso (dB), Rs = atenuación mín. rechazo (dB)
[N, Wn] = cheb1ord(Wp, Ws, Rp, Rs)
[N, Wn] = cheb2ord(Wp, Ws, Rp, Rs)
[N, Wn] = ellipord(Wp, Ws, Rp, Rs)
```
- **`Wp`/`Ws`**: bordes de banda de **paso** y de **rechazo** normalizados (o en rad/s con opción `'s'`).
- **Devuelven** el **orden mínimo `N`** y la(s) frecuencia(s) natural(es) `Wn` que cumplen las specs; se pasan tal cual al diseñador.

**Ejemplo — Butterworth LP (caso ECG): fp = 40, fr = 60, Rp = 1, As = 40, fs = 500:**
```matlab
fs = 500;
Wp = 40/(fs/2);          % 0.16  (banda de paso)
Ws = 60/(fs/2);          % 0.24  (banda de rechazo)
Rp = 1;   As = 40;       % dB
[N, Wn] = buttord(Wp, Ws, Rp, As);   % orden mínimo + corte
[b, a]  = butter(N, Wn);             % filtro digital [b,a]
% Alternativa numéricamente robusta:
[z,p,k] = butter(N, Wn);  sos = zp2sos(z,p,k);
```

### 3.3 `iirnotch` — filtro notch (rechazo de banda estrecho), p. ej. 50 Hz
```matlab
[b, a] = iirnotch(w0, bw)
[b, a] = iirnotch(w0, bw, ab)     % ab = profundidad del notch en dB (def. -3 dB)
```
- **`w0`**: frecuencia central normalizada a Nyquist = `f0/(fs/2)`.
- **`bw`**: ancho de banda a -3 dB, normalizado. Relación con el factor Q: `bw = w0/Q`.
- **Devuelve** un filtro IIR de **2.º orden** (`b`, `a` de 3 coeficientes).

**Ejemplo — Notch 50 Hz, fs = 500 (caso ECG):**
```matlab
fs = 500;  f0 = 50;  Q = 35;
w0 = f0/(fs/2);           % = 0.20
bw = w0/Q;                % ancho proporcional a Q
[b, a] = iirnotch(w0, bw);
```
> En Octave puede llamarse desde el paquete `signal`. Si no estuviera disponible, un notch equivalente se arma con `ellip`/`butter` en modo `'stop'` con banda estrecha.

---

## 4. Análisis del filtro

> Graficado conceptual en [[01-fundamentos-pds]] y [[02-fir]]/[[03-iir]]. Todas aceptan `fs` para devolver el eje en Hz.

### 4.1 `freqz` — respuesta en frecuencia
```matlab
[H, w] = freqz(b, a, n)          % w en rad/muestra (0..pi), n puntos
[H, f] = freqz(b, a, n, fs)      % f en Hz (0..fs/2)
freqz(b, a)                      % sin salidas: dibuja módulo (dB) y fase
```
- **Devuelve** `H` (complejo) y el eje `w`/`f`. Para FIR usar `a = 1`.
- **Módulo en dB:** `20*log10(abs(H))`. **Fase (grados):** `angle(H)*180/pi` (usar `unwrap` para desenrollar).

```matlab
fs = 500;
[H, f] = freqz(b, a, 1024, fs);
subplot(2,1,1); plot(f, 20*log10(abs(H)));  grid on
  xlabel('Hz'); ylabel('|H| [dB]'); title('Magnitud');
subplot(2,1,2); plot(f, unwrap(angle(H))*180/pi); grid on
  xlabel('Hz'); ylabel('Fase [°]');
```

### 4.2 `grpdelay` — retardo de grupo
```matlab
[gd, w] = grpdelay(b, a, n)
[gd, f] = grpdelay(b, a, n, fs)
```
- **Devuelve** el retardo de grupo (en **muestras**) vs frecuencia. Para un FIR de fase lineal de orden `N` es constante `= N/2`.

### 4.3 `phasez` — respuesta de fase (desenrollada)
```matlab
[phi, w] = phasez(b, a, n)
[phi, f] = phasez(b, a, n, fs)
```
- Devuelve la **fase** (rad) directamente, ya útil para inspeccionar linealidad de fase.

### 4.4 `zplane` — diagrama polos-ceros
```matlab
zplane(b, a)          % desde coeficientes de transferencia
zplane(z, p)          % desde ceros y polos (vectores columna)
```
- Dibuja ceros (`o`) y polos (`x`) con el círculo unitario. **Estabilidad IIR:** todos los polos dentro del círculo (`abs(p) < 1`).

### 4.5 `impz` — respuesta al impulso
```matlab
[h, t] = impz(b, a, n)
[h, t] = impz(b, a, n, fs)
```
- **Devuelve** las `n` primeras muestras de `h[n]`. Para FIR, `impz(b,1)` reproduce los propios coeficientes.

---

## 5. Aplicación del filtro

### 5.1 `filter` — forma directa (IIR y FIR)
```matlab
y = filter(b, a, x)
[y, zf] = filter(b, a, x, zi)    % zi/zf: estado inicial/final (procesado por bloques)
```
- Implementa la ecuación en diferencias (Direct-Form II transpuesta). Para FIR usar `a = 1`. Introduce **retardo y fase no nula**.

### 5.2 `filtfilt` — filtrado de fase cero
```matlab
y = filtfilt(b, a, x)
```
- Filtra **hacia adelante y hacia atrás** ⇒ **fase cero** y orden efectivo duplicado (atenuación al cuadrado). Ideal para no distorsionar morfología (P-QRS-T del ECG). No usar en tiempo real (no causal).

### 5.3 `fftfilt` — FIR por bloques vía FFT (overlap-add)
```matlab
y = fftfilt(b, x)
y = fftfilt(b, x, nfft)
```
- Solo **FIR** (`b`). Eficiente para `b` largo y `x` largo. Equivalente a `filter(b,1,x)` pero más rápido en FIR de orden alto.

### 5.4 `conv` — convolución
```matlab
y = conv(x, h)            % longitud length(x)+length(h)-1 ('full')
y = conv(x, h, 'same')    % misma longitud que x
```
- Filtrado FIR "manual": `y = conv(x, b)`. Útil didácticamente; sin manejo de estado.

### 5.5 Estructuras SOS (segundas secciones de orden 2)
| Función | Firma | Uso |
|---|---|---|
| `zp2sos` | `sos = zp2sos(z, p, k)` | de cero-polo-ganancia → matriz SOS (`Nsec×6`) |
| `tf2sos` | `sos = tf2sos(b, a)` | de transferencia → SOS |
| `sos2tf` | `[b, a] = sos2tf(sos)` | de SOS → transferencia |
| `sosfilt`| `y = sosfilt(sos, x)` | aplica la cascada de secciones SOS a `x` |

```matlab
[z,p,k] = ellip(6, 1, 40, Wn);
sos = zp2sos(z, p, k);       % cascada de 3 biquads (mejor condicionamiento)
y   = sosfilt(sos, x);       % aplicación numéricamente estable
```
> SOS es la estructura recomendada para IIR de orden alto y para implementación en µC (ver [[05-agente-ia]]: "estabilidad numérica crítica sin DSP float → SOS").

---

## 6. Análisis espectral

### 6.1 FFT y eje de frecuencias
```matlab
X = fft(x)             % FFT de N puntos (N = length(x))
X = fft(x, N)          % con zero-padding/truncado a N
Xs = fftshift(X)       % centra el espectro en 0 Hz (para eje bilateral)
mag = abs(X);          % módulo
```
- **Eje unilateral** (0 .. fs): `f = (0:N-1)*fs/N;` y graficar la mitad `1:floor(N/2)`.
- **Eje bilateral** con `fftshift`: `f = (-N/2:N/2-1)*fs/N;`
```matlab
N = length(x);
X = fft(x);
f = (0:N-1)*fs/N;                    % eje de frecuencias
plot(f(1:floor(N/2)), abs(X(1:floor(N/2)))/N);   % espectro de magnitud unilateral
xlabel('Hz'); ylabel('|X(f)|'); grid on
```
- Para reducir fuga espectral, ventanear antes de la FFT: `X = fft(x .* hamming(N));`.

### 6.2 `pwelch` — densidad espectral de potencia (PSD)
```matlab
[Pxx, f] = pwelch(x)                                   % defaults
[Pxx, f] = pwelch(x, window, noverlap, nfft, fs)       % forma completa
```
- Estima la **PSD** por el método de Welch (promediado de periodogramas con solape ⇒ menos varianza que `abs(fft).^2`).
- **`window`**: nº de muestras por segmento o vector ventana; **`noverlap`**: solape; **`nfft`**: puntos FFT; **`fs`**: frecuencia de muestreo (devuelve `f` en Hz).
```matlab
[Pxx, f] = pwelch(x, hamming(256), 128, 512, fs);
plot(f, 10*log10(Pxx)); xlabel('Hz'); ylabel('PSD [dB/Hz]'); grid on
```
> Nota MATLAB/Octave: el orden de los argumentos de `pwelch` coincide; en Octave algunos extras (`'onesided'`, etc.) se pasan como strings finales. Verificar con `help pwelch`.

---

## 7. Métricas (SNR, RMSE)

### 7.1 `snr` (si el paquete lo provee)
```matlab
r = snr(signal, noise)        % SNR en dB a partir de señal y ruido separados
r = snr(x, fs)                % estima SNR de un tono respecto a armónicos+ruido
```
- Disponible en la *Signal Processing Toolbox* de MATLAB y en versiones recientes del paquete `signal` de Octave. Si no existe, calcular manualmente (abajo).

### 7.2 Cálculo manual (portátil, siempre funciona)
```matlab
% SNR comparando señal limpia de referencia (ref) contra la filtrada (y):
ruido_res = y - ref;                                  % error/ruido residual
SNR_dB = 10*log10(sum(ref.^2) / sum(ruido_res.^2));   % potencia señal / potencia ruido

% RMSE entre filtrada y referencia:
RMSE = sqrt(mean((y - ref).^2));

% (opcional) mejora de SNR entrada→salida:
SNR_in  = 10*log10(sum(ref.^2)/sum((x   - ref).^2));
SNR_out = 10*log10(sum(ref.^2)/sum((y   - ref).^2));
mejora_dB = SNR_out - SNR_in;
```
> Definición usada: SNR = 10·log10(Σ señal² / Σ ruido²). RMSE en las mismas unidades de la señal.

---

## 8. Plantilla de script (esqueleto de referencia)

> **Esqueleto de referencia** — pseudocompleto y comentado, ~25 líneas. Integra: diseño → `freqz` → filtrado → FFT → métricas. Adaptar nombres de variables y la señal de entrada al dataset real (ver [[01-fundamentos-pds]]).

```matlab
% --- 06-octave: esqueleto diseño→análisis→filtrado→FFT→métricas (caso ECG) ---
if exist('OCTAVE_VERSION','builtin'); pkg load signal; end
fs = 500;                                  % Hz (ECG, Anexo I-A)

% x  = señal contaminada (cargar del CSV/dataset);  ref = señal limpia de referencia
% Ejemplo sintético sólo para que el esqueleto sea autocontenido:
t = (0:1/fs:5-1/fs).';  ref = sin(2*pi*1.2*t);          % ~72 lpm
x = ref + 0.3*sin(2*pi*50*t) + 0.1*randn(size(t));      % + 50 Hz + ruido

% 1) NOTCH 50 Hz (IIR de 2.º orden)
w0 = 50/(fs/2);  [bn, an] = iirnotch(w0, w0/35);

% 2) LP FIR fc=40 Hz, fase lineal (ventana Hamming)
Wn = 40/(fs/2);  N = 100;  blp = fir1(N, Wn, hamming(N+1));

% 3) Análisis de respuesta en frecuencia
[H,f] = freqz(blp,1,1024,fs);
figure; plot(f, 20*log10(abs(H))); grid on; xlabel('Hz'); ylabel('|H| dB');

% 4) Filtrado en cascada (filtfilt = fase cero para preservar P-QRS-T)
y = filtfilt(bn, an, x);          % quita 50 Hz
y = filtfilt(blp, 1, y);          % quita HF > 40 Hz

% 5) FFT antes/después
M = length(x);  fa = (0:M-1)*fs/M;
Xx = abs(fft(x))/M;  Yy = abs(fft(y))/M;
figure; plot(fa(1:M/2), Xx(1:M/2), fa(1:M/2), Yy(1:M/2)); legend('x','y'); xlabel('Hz');

% 6) Métricas
SNR_dB = 10*log10(sum(ref.^2)/sum((y-ref).^2));
RMSE   = sqrt(mean((y-ref).^2));
printf('SNR = %.2f dB | RMSE = %.4f\n', SNR_dB, RMSE);   % en MATLAB usar fprintf
```
> `printf` es propio de Octave; en MATLAB usar `fprintf`.

---

## 9. Agente de reglas IF-THEN en Octave/MATLAB

> Implementación del **Paso 4** (ver detalle completo y reglas en [[05-agente-ia]]). Estructura mínima: un `struct` con las restricciones de entrada y una cadena `if/elseif` que devuelve recomendación + estructura + justificación.

```matlab
function rec = agente_filtro(in)
  % in: struct con campos fase_lineal(bool), ram_kB, mips, snr_in_dB, transicion('estrecha'/'amplia')
  rec.tipo = '';  rec.estructura = '';  rec.motivo = '';

  if in.fase_lineal                       % regla: fase lineal estricta -> FIR
    rec.tipo = 'FIR';  rec.estructura = 'Direct-Form (DF) simétrico';
    rec.motivo = 'Fase lineal requerida (preserva morfología, p.ej. P-QRS-T del ECG).';
  elseif in.ram_kB < 2                     % RAM escasa -> IIR
    rec.tipo = 'IIR';  rec.estructura = 'SOS (biquads en cascada)';
    rec.motivo = 'RAM < 2 kB: FIR de orden alto inviable; IIR/SOS por estabilidad.';
  elseif strcmp(in.transicion,'estrecha') && in.mips > 50
    rec.tipo = 'IIR';  rec.estructura = 'SOS';
    rec.motivo = 'Transición exigente con cómputo suficiente -> IIR de orden adecuado.';
  else
    rec.tipo = 'FIR';  rec.estructura = 'Direct-Form';
    rec.motivo = 'Caso general sin restricción crítica.';
  end
end
```
- Llamada: `r = agente_filtro(struct('fase_lineal',true,'ram_kB',8,'mips',80,'snr_in_dB',10,'transicion','amplia'));`
- Para los ≥3 escenarios de validación y la tabla completa de reglas, ver [[05-agente-ia]].

---

### Referencias cruzadas
- Fundamentos (Nyquist, normalización, FFT): [[01-fundamentos-pds]]
- Diseño y teoría FIR (ventanas, fase lineal, Parks-McClellan): [[02-fir]]
- Diseño y teoría IIR (prototipos, bilineal/prewarping, estabilidad): [[03-iir]]
- Agente de decisión FIR/IIR (reglas, estructuras, validación): [[05-agente-ia]]
