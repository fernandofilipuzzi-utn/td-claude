% =========================================================================
% diseno_filtros.m
% -------------------------------------------------------------------------
% PROPOSITO:
%   Disenar y caracterizar los filtros del caso ECG (fs = 500 Hz, Anexo I-A):
%     (1) FIR pasa-bajos Hamming, fc = 40 Hz  -> fase lineal (preserva P-QRS-T)
%     (2) IIR pasa-bajos Chebyshev I (con SOS) -> bajo orden, estable
%     (3) Notch IIR 50 Hz                      -> elimina red electrica
%
%   Para cada filtro se grafican:  respuesta en frecuencia (|H| en dB y fase),
%   retardo de grupo (grpdelay), polos-ceros (zplane) y respuesta al impulso
%   (impz). Ademas se imprimen los primeros/ultimos coeficientes del FIR y se
%   verifica su simetria (condicion de fase lineal).
%
% USO:    >> diseno_filtros      (en Octave: ejecutar antes 'pkg load signal')
% AUTOR:  Material de referencia PDS - Filtrado Digital FIR/IIR
% =========================================================================

% --- Carga del paquete signal (solo Octave; en MATLAB no es necesario) ---
if exist('OCTAVE_VERSION', 'builtin')
  pkg load signal
end

clc; close all;

% =========================================================================
% 0) Especificacion comun (caso ECG, Anexo I-A)
% =========================================================================
fs = 500;              % Frecuencia de muestreo [Hz]
fnyq = fs/2;           % Frecuencia de Nyquist  [Hz] = 250
fc  = 40;              % Frecuencia de corte LP [Hz]  (banda util del ECG ~0.5-40)
fp  = 40;              % Borde banda de paso    [Hz]  (IIR)
fr  = 60;              % Borde banda de rechazo [Hz]  (IIR)
Rp  = 1;               % Ondulacion maxima en banda de paso  [dB]
As  = 40;              % Atenuacion minima en banda de rechazo [dB]
f0  = 50;              % Frecuencia de la red electrica (notch) [Hz]
Nfreq = 2048;          % Puntos de evaluacion para freqz

printf('========================================================\n');
printf(' DISENO DE FILTROS - CASO ECG  (fs = %d Hz)\n', fs);
printf('========================================================\n\n');

% =========================================================================
% 1) FIR PASA-BAJOS HAMMING  (fc = 40 Hz)
% =========================================================================
%   Wn = fc/(fs/2) = 40/250 = 0.16  (fraccion de Nyquist, en (0,1))
%   Orden N ~ 166 (par => filtro Tipo I, simetrico, fase lineal exacta).
%   El orden alto del FIR es el precio de la fase lineal: la transicion
%   estrecha 40->~50 Hz con ventana Hamming exige ~166 coeficientes.
% -------------------------------------------------------------------------
Wn_fir = fc / fnyq;            % = 0.16
N_fir  = 166;                  % orden FIR (par)  => N_fir+1 = 167 coeficientes
b_fir  = fir1(N_fir, Wn_fir, hamming(N_fir+1));   % LP, ventana Hamming explicita
a_fir  = 1;                    % FIR: denominador trivial

printf('--- FIR pasa-bajos Hamming ---\n');
printf('  Wn = fc/(fs/2) = %d/%d = %.4f\n', fc, fnyq, Wn_fir);
printf('  Orden N = %d  =>  %d coeficientes\n', N_fir, N_fir+1);
printf('  Retardo de grupo (constante) = N/2 = %.1f muestras = %.2f ms\n', ...
        N_fir/2, 1000*(N_fir/2)/fs);

% Primeros y ultimos 5 coeficientes
printf('\n  Primeros 5 coeficientes b[0..4]:\n');
for k = 1:5
  printf('    b[%3d] = %+.6e\n', k-1, b_fir(k));
end
printf('  Ultimos 5 coeficientes b[N-4..N]:\n');
for k = N_fir-3:N_fir+1
  printf('    b[%3d] = %+.6e\n', k-1, b_fir(k));
end

% Verificacion de simetria  b[n] == b[N-n]  (=> fase lineal)
err_sim = max(abs(b_fir - fliplr(b_fir)));
printf('\n  Verificacion de simetria  max|b[n]-b[N-n]| = %.3e\n', err_sim);
if err_sim < 1e-12
  printf('  -> SIMETRICO: el FIR tiene FASE LINEAL EXACTA.\n\n');
else
  printf('  -> AVISO: no perfectamente simetrico (revisar diseno).\n\n');
end

% --------- Graficas del FIR ---------
[Hf, ff] = freqz(b_fir, a_fir, Nfreq, fs);
figure('Name', 'FIR pasa-bajos Hamming - fc=40 Hz');
subplot(2,2,1);
  plot(ff, 20*log10(abs(Hf)), 'b'); grid on; ylim([-100 5]);
  hold on; xline_compat(fc); hold off;
  xlabel('Frecuencia [Hz]'); ylabel('|H| [dB]');
  title('FIR: Magnitud');
subplot(2,2,2);
  plot(ff, unwrap(angle(Hf))*180/pi, 'b'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Fase [grados]');
  title('FIR: Fase (lineal)');
subplot(2,2,3);
  [gd, fg] = grpdelay(b_fir, a_fir, Nfreq, fs);
  plot(fg, gd, 'b'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Retardo grupo [muestras]');
  title(sprintf('FIR: grpdelay (cte = %d)', N_fir/2));
subplot(2,2,4);
  [hh, th] = impz(b_fir, a_fir);
  stem(th, hh, 'b', 'Marker', 'none'); grid on;
  xlabel('n [muestras]'); ylabel('h[n]');
  title('FIR: Respuesta al impulso');

figure('Name', 'FIR: Polos-Ceros');
  zplane(b_fir, a_fir);
  title('FIR: Diagrama polos-ceros (todos los polos en z=0)');

% =========================================================================
% 2) IIR PASA-BAJOS  (Chebyshev I, salida SOS)
% =========================================================================
%   Especificacion: fp=40, fr=60, Rp=1 dB, As=40 dB.
%   NOTA: con Butterworth esta mascara exige N = 13 (transicion 40->60 Hz,
%   relacion 1.54 con 40 dB es muy exigente). Una forma directa de orden 13
%   es numericamente inviable. Por eso se usa Chebyshev I (N ~ 6) y se realiza
%   en CASCADA DE BIQUADS (SOS), que reduce drasticamente la sensibilidad a la
%   cuantizacion de coeficientes. El eliptico daria N ~ 4 (ver alternativa).
% -------------------------------------------------------------------------
Wp = fp / fnyq;        % = 0.16  (banda de paso normalizada)
Ws = fr / fnyq;        % = 0.24  (banda de rechazo normalizada)

% Orden minimo Chebyshev I y frecuencia natural
[N_iir, Wn_iir] = cheb1ord(Wp, Ws, Rp, As);

% Diseno en cero-polo-ganancia -> SOS (numericamente robusto)
[z_iir, p_iir, k_iir] = cheby1(N_iir, Rp, Wn_iir);
sos_iir = zp2sos(z_iir, p_iir, k_iir);

printf('--- IIR pasa-bajos Chebyshev I (SOS) ---\n');
printf('  Wp = %.4f , Ws = %.4f , Rp = %d dB , As = %d dB\n', Wp, Ws, Rp, As);
printf('  Orden minimo Chebyshev I:  N = %d  (Butterworth daria N = 13)\n', N_iir);
printf('  Frecuencia natural Wn = %.4f\n', Wn_iir);
printf('  Cascada SOS: %d secciones de 2do orden (biquads)\n', size(sos_iir,1));
printf('  Estabilidad: max|polo| = %.4f  (estable si < 1)\n\n', max(abs(p_iir)));

% Alternativa eliptico (solo informativa: orden minimo de los cuatro)
[N_ell, Wn_ell] = ellipord(Wp, Ws, Rp, As);
printf('  [Alternativa] Eliptico (ellipord): N = %d (orden minimo posible)\n\n', N_ell);

% --------- Graficas del IIR ---------
% Coeficientes globales [b,a] desde la cascada SOS (portable para freqz/grpdelay/impz)
[b_iir_tf, a_iir_tf] = sos2tf(sos_iir);
[Hi, fi] = freqz(b_iir_tf, a_iir_tf, Nfreq, fs);
figure('Name', 'IIR pasa-bajos Chebyshev I (SOS)');
subplot(2,2,1);
  plot(fi, 20*log10(abs(Hi)), 'r'); grid on; ylim([-100 5]);
  hold on; xline_compat(fp); xline_compat(fr); hold off;
  xlabel('Frecuencia [Hz]'); ylabel('|H| [dB]');
  title(sprintf('IIR Cheby I (N=%d): Magnitud', N_iir));
subplot(2,2,2);
  plot(fi, unwrap(angle(Hi))*180/pi, 'r'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Fase [grados]');
  title('IIR: Fase (NO lineal)');
subplot(2,2,3);
  [gdi, fgi] = grpdelay(b_iir_tf, a_iir_tf, Nfreq, fs);
  plot(fgi, gdi, 'r'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Retardo grupo [muestras]');
  title('IIR: grpdelay (variable)');
subplot(2,2,4);
  [hhi, thi] = impz(b_iir_tf, a_iir_tf, 200);
  stem(thi, hhi, 'r', 'Marker', 'none'); grid on;
  xlabel('n [muestras]'); ylabel('h[n]');
  title('IIR: Respuesta al impulso (infinita)');

figure('Name', 'IIR: Polos-Ceros');
  zplane(z_iir, p_iir);
  title(sprintf('IIR Cheby I (N=%d): polos dentro del circulo unitario', N_iir));

% =========================================================================
% 3) NOTCH IIR 50 Hz  (rechazo de banda estrecho - red electrica)
% =========================================================================
%   Filtro IIR de 2do orden: ceros sobre el circulo en w0 y polos justo
%   dentro (radio r<1). El ancho lo fija el factor Q (bw = w0/Q).
% -------------------------------------------------------------------------
Q  = 35;                 % factor de calidad (notch estrecho)
w0 = f0 / fnyq;          % = 50/250 = 0.20  (centro normalizado)
bw = w0 / Q;             % ancho de banda a -3 dB normalizado
[b_notch, a_notch] = iirnotch(w0, bw);

printf('--- Notch IIR 50 Hz ---\n');
printf('  w0 = f0/(fs/2) = %d/%d = %.4f ,  Q = %d ,  bw = %.5f\n', f0, fnyq, w0, Q, bw);
printf('  Coeficientes b = [%+.5f %+.5f %+.5f]\n', b_notch(1), b_notch(2), b_notch(3));
printf('  Coeficientes a = [%+.5f %+.5f %+.5f]\n', a_notch(1), a_notch(2), a_notch(3));
printf('  Estabilidad: max|polo| = %.4f\n\n', max(abs(roots(a_notch))));

% --------- Graficas del Notch ---------
[Hn, fn] = freqz(b_notch, a_notch, Nfreq, fs);
figure('Name', 'Notch IIR 50 Hz');
subplot(2,2,1);
  plot(fn, 20*log10(abs(Hn)), 'm'); grid on; ylim([-60 5]);
  hold on; xline_compat(f0); hold off;
  xlabel('Frecuencia [Hz]'); ylabel('|H| [dB]');
  title('Notch 50 Hz: Magnitud');
subplot(2,2,2);
  plot(fn, unwrap(angle(Hn))*180/pi, 'm'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Fase [grados]');
  title('Notch: Fase');
subplot(2,2,3);
  [gdn, fgn] = grpdelay(b_notch, a_notch, Nfreq, fs);
  plot(fgn, gdn, 'm'); grid on;
  xlabel('Frecuencia [Hz]'); ylabel('Retardo grupo [muestras]');
  title('Notch: grpdelay');
subplot(2,2,4);
  [hhn, thn] = impz(b_notch, a_notch, 200);
  stem(thn, hhn, 'm', 'Marker', 'none'); grid on;
  xlabel('n [muestras]'); ylabel('h[n]');
  title('Notch: Respuesta al impulso');

figure('Name', 'Notch: Polos-Ceros');
  zplane(b_notch, a_notch);
  title('Notch 50 Hz: ceros en circulo, polos justo dentro');

printf('========================================================\n');
printf(' Diseno completado. Revise las figuras en pantalla.\n');
printf('========================================================\n');

% =========================================================================
% Funcion auxiliar: linea vertical compatible con versiones sin 'xline'
% =========================================================================
function xline_compat(xpos)
  yl = ylim();
  line([xpos xpos], yl, 'Color', [0.5 0.5 0.5], 'LineStyle', '--');
end
