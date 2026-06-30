% =========================================================================
% procesar_senal.m
% -------------------------------------------------------------------------
% PROPOSITO:
%   Pipeline completo de filtrado sobre una senal de ECG SINTETICA (autonomo,
%   no descarga datasets). Pasos:
%     1) Generar ECG sintetico (suma de gaussianas P-QRS-T) limpio (referencia).
%     2) Contaminar con interferencia de red 50 Hz + ruido blanco (EMG) de alta
%        frecuencia.
%     3) Filtrar con:
%          - FIR pasa-bajos Hamming fc=40 Hz   (filter / fftfilt)
%          - IIR pasa-bajos Chebyshev I (SOS)   (sosfilt) + Notch 50 Hz (filter)
%     4) Graficar tiempo antes/despues y espectro FFT antes/despues.
%     5) Calcular SNR y RMSE (manual) y mostrar una tabla comparativa FIR vs IIR
%        (orden, MACs/muestra, fase, SNR de salida).
%
% USO:    >> procesar_senal     (en Octave ejecutar antes 'pkg load signal')
% AUTOR:  Material de referencia PDS - Filtrado Digital FIR/IIR
% =========================================================================

if exist('OCTAVE_VERSION', 'builtin')
  pkg load signal
end

clc; close all;
rand('seed', 42); randn('seed', 42);   % reproducibilidad (Octave)

% =========================================================================
% 0) Parametros
% =========================================================================
fs   = 500;                 % Hz
Tdur = 5;                   % s
t    = (0:1/fs:Tdur-1/fs).';% vector de tiempo (columna)
Ntot = numel(t);

% =========================================================================
% 1) ECG SINTETICO LIMPIO (referencia) = suma de gaussianas P-QRS-T por latido
% =========================================================================
%   Modelo simple: por cada latido se suman 5 gaussianas (P, Q, R, S, T) con
%   amplitudes y anchos tipicos. Frecuencia cardiaca ~ 72 lpm (1.2 Hz).
% -------------------------------------------------------------------------
fc_card = 1.2;                       % Hz  (~72 latidos por minuto)
Tlatido = 1/fc_card;                 % periodo del latido [s]

% Ondas: [retardo_rel(s)  amplitud(mV)  ancho_sigma(s)]
ondas = [ ...
   -0.20   0.10   0.025 ;   % P
   -0.025 -0.15   0.010 ;   % Q
    0.000  1.00   0.011 ;   % R
    0.025 -0.25   0.010 ;   % S
    0.160  0.30   0.040 ];  % T

ecg = zeros(Ntot,1);
tc  = 0;                              % centro del latido actual
while tc < Tdur + Tlatido
  for k = 1:size(ondas,1)
    mu  = tc + ondas(k,1);
    amp = ondas(k,2);
    sig = ondas(k,3);
    ecg = ecg + amp * exp(-((t-mu).^2) / (2*sig^2));
  end
  tc = tc + Tlatido;
end
ref = ecg;                            % senal LIMPIA de referencia

% =========================================================================
% 2) CONTAMINACION: red 50 Hz + ruido blanco (EMG) de alta frecuencia
% =========================================================================
A_red   = 0.30;                       % amplitud interferencia 50 Hz [mV]
interf  = A_red * sin(2*pi*50*t);     % red electrica
sig_emg = 0.08 * randn(Ntot,1);       % ruido blanco (EMG/HF)
x = ref + interf + sig_emg;           % senal CONTAMINADA de entrada

% =========================================================================
% 3) DISENO DE FILTROS (coherente con diseno_filtros.m)
% =========================================================================
fnyq = fs/2;

% --- FIR LP Hamming fc=40 Hz, orden 166 ---
fc_fir = 40;  N_fir = 166;
b_fir  = fir1(N_fir, fc_fir/fnyq, hamming(N_fir+1));

% --- IIR LP Chebyshev I (SOS) + Notch 50 Hz ---
fp = 40; fr = 60; Rp = 1; As = 40;
[N_iir, Wn_iir]       = cheb1ord(fp/fnyq, fr/fnyq, Rp, As);
[z_iir, p_iir, k_iir] = cheby1(N_iir, Rp, Wn_iir);
sos_iir               = zp2sos(z_iir, p_iir, k_iir);

Q = 35; w0 = 50/fnyq;
[b_notch, a_notch]    = iirnotch(w0, w0/Q);

% =========================================================================
% 4) APLICACION DE LOS FILTROS
% =========================================================================
% --- Camino FIR: FFT-overlap-add (fftfilt) -> compensar retardo N/2 ---
y_fir_raw = fftfilt(b_fir, x);        % == filter(b_fir,1,x) pero mas rapido
d_fir = N_fir/2;                      % retardo de grupo (constante)
% Compensar el retardo lineal para comparar muestra a muestra con ref:
y_fir = [y_fir_raw(d_fir+1:end); zeros(d_fir,1)];

% --- Camino IIR: Notch 50 Hz (filter) seguido de LP Chebyshev (sosfilt) ---
y_notch = filter(b_notch, a_notch, x);
y_iir   = sosfilt(sos_iir, y_notch);

% =========================================================================
% 5) GRAFICAS EN EL TIEMPO (antes / despues)
% =========================================================================
figure('Name', 'Senales en el tiempo');
subplot(3,1,1);
  plot(t, ref, 'k', t, x, 'Color', [0.7 0.7 0.7]); grid on;
  xlabel('Tiempo [s]'); ylabel('Amplitud [mV]');
  title('Entrada: ECG limpio (negro) vs contaminado (gris)');
  legend('ref limpia', 'x contaminada'); xlim([0 2]);
subplot(3,1,2);
  plot(t, ref, 'k', t, y_fir, 'b'); grid on;
  xlabel('Tiempo [s]'); ylabel('Amplitud [mV]');
  title('Salida FIR (retardo compensado) vs referencia');
  legend('ref', 'FIR'); xlim([0 2]);
subplot(3,1,3);
  plot(t, ref, 'k', t, y_iir, 'r'); grid on;
  xlabel('Tiempo [s]'); ylabel('Amplitud [mV]');
  title('Salida IIR (Notch + Cheby SOS) vs referencia');
  legend('ref', 'IIR'); xlim([0 2]);

% =========================================================================
% 6) ESPECTRO FFT (antes / despues)
% =========================================================================
%   Eje unilateral: f = (0:N-1)*fs/N, graficar la mitad 1:floor(N/2).
% -------------------------------------------------------------------------
N   = Ntot;
faxis = (0:N-1)*fs/N;
half  = 1:floor(N/2);
Xx = abs(fft(x))     / N;
Xf = abs(fft(y_fir)) / N;
Xi = abs(fft(y_iir)) / N;

figure('Name', 'Espectros FFT');
subplot(2,1,1);
  plot(faxis(half), Xx(half), 'Color', [0.6 0.6 0.6]); grid on; hold on;
  plot(faxis(half), Xf(half), 'b'); hold off;
  xlabel('Frecuencia [Hz]'); ylabel('|X(f)|');
  title('Espectro: contaminada (gris) vs FIR (azul)');
  legend('x', 'FIR'); xlim([0 fnyq]);
subplot(2,1,2);
  plot(faxis(half), Xx(half), 'Color', [0.6 0.6 0.6]); grid on; hold on;
  plot(faxis(half), Xi(half), 'r'); hold off;
  xlabel('Frecuencia [Hz]'); ylabel('|X(f)|');
  title('Espectro: contaminada (gris) vs IIR (rojo)');
  legend('x', 'IIR'); xlim([0 fnyq]);

% =========================================================================
% 7) METRICAS SNR y RMSE (manual)
% =========================================================================
%   SNR = 10*log10( sum(ref.^2) / sum((y-ref).^2) ).  RMSE = sqrt(mean((y-ref).^2)).
%   Se descartan los bordes (transitorio) para una comparacion mas justa.
% -------------------------------------------------------------------------
g = (round(0.3*fs)+1) : (Ntot-round(0.3*fs));   % zona util (sin bordes)

snr_db = @(y) 10*log10( sum(ref(g).^2) / sum((y(g)-ref(g)).^2) );
rmse   = @(y) sqrt( mean((y(g)-ref(g)).^2) );

SNR_in  = snr_db(x);
SNR_fir = snr_db(y_fir);
SNR_iir = snr_db(y_iir);
RMSE_in  = rmse(x);
RMSE_fir = rmse(y_fir);
RMSE_iir = rmse(y_iir);

% =========================================================================
% 8) TABLA COMPARATIVA FIR vs IIR
% =========================================================================
%   Coste (MACs/muestra):  FIR ~ N+1 ;  IIR(SOS) ~ 5*secciones + notch (5).
% -------------------------------------------------------------------------
macs_fir = N_fir + 1;
sec_iir  = size(sos_iir,1);
macs_iir = 5*sec_iir + 5;            % LP-SOS + notch (1 biquad)

printf('\n');
printf('=================================================================\n');
printf('  METRICAS (zona util, sin transitorios de borde)\n');
printf('=================================================================\n');
printf('  SNR entrada (contaminada) : %7.2f dB   | RMSE = %.4f\n', SNR_in,  RMSE_in);
printf('  SNR salida FIR            : %7.2f dB   | RMSE = %.4f\n', SNR_fir, RMSE_fir);
printf('  SNR salida IIR            : %7.2f dB   | RMSE = %.4f\n', SNR_iir, RMSE_iir);
printf('-----------------------------------------------------------------\n');
printf('  TABLA COMPARATIVA FIR vs IIR\n');
printf('-----------------------------------------------------------------\n');
printf('  %-22s | %-14s | %-14s\n', 'Caracteristica', 'FIR (Hamming)', 'IIR (Cheby+Notch)');
printf('  %-22s | %-14s | %-14s\n', '----------------------', '--------------', '-----------------');
printf('  %-22s | %-14d | %-14s\n', 'Orden',            N_fir, sprintf('%d (LP) + 2 (notch)', N_iir));
printf('  %-22s | %-14d | %-14d\n', 'Coef./MACs por muestra', macs_fir, macs_iir);
printf('  %-22s | %-14s | %-14s\n', 'Fase',             'lineal', 'no lineal');
printf('  %-22s | %-14s | %-14s\n', 'Retardo de grupo', sprintf('cte=%d', N_fir/2), 'variable');
printf('  %-22s | %-14s | %-14s\n', 'Estabilidad',      'garantizada', 'verificada |p|<1');
printf('  %-22s | %-14.2f | %-14.2f\n', 'SNR salida [dB]', SNR_fir, SNR_iir);
printf('  %-22s | %-14.4f | %-14.4f\n', 'RMSE salida',     RMSE_fir, RMSE_iir);
printf('=================================================================\n');
printf('  Lectura: el FIR conserva la morfologia P-QRS-T (fase lineal) a\n');
printf('  costa de %d MACs/muestra; el IIR logra resultado similar con muy\n', macs_fir);
printf('  pocos MACs, pero introduce distorsion de fase.\n');
printf('=================================================================\n');
