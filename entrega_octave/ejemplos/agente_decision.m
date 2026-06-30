% =========================================================================
% agente_decision.m
% -------------------------------------------------------------------------
% PROPOSITO:
%   Sistema experto IF-THEN (Paso 4 del examen) que recomienda FIR o IIR y la
%   estructura de realizacion (DF-II / SOS / DF simetrico) a partir de las
%   restricciones de la aplicacion. Implementa >= 6 reglas, incluidas las de
%   referencia del enunciado:
%       R1  Fase lineal estricta              -> FIR (DF simetrico)
%       R2  RAM < 2 kB y orden FIR > 50        -> IIR (SOS)
%       R3  Estabilidad critica sin FPU        -> IIR (SOS)
%       R4  Transicion estrecha + computo alto -> IIR (SOS / DF-II)
%       R5  SNR muy baja (necesita rechazo)    -> IIR de orden adecuado
%       R6  Caso general (recursos holgados)   -> FIR (DF simetrico)
%
% USO:
%   1) Como FUNCION:
%        specs = struct('fs',500,'ram_kb',8,'mips',80,'fase_lineal',true, ...
%                       'snr_db',10,'latencia','baja','pendiente','estrecha');
%        rec = agente_decision(specs)
%   2) Como DRIVER de validacion (3 escenarios del KB):
%        agente_decision        % sin argumentos -> ejecuta y muestra la demo
%
% ENTRADA  specs (struct):
%   .fs           frecuencia de muestreo [Hz]
%   .ram_kb       RAM disponible [kB]
%   .mips         capacidad de computo [MIPS]
%   .fase_lineal  logico (true => se exige fase lineal estricta)
%   .snr_db       SNR de entrada [dB]
%   .latencia     'baja' | 'media' | 'alta'
%   .pendiente    'estrecha' | 'amplia'   (transicion exigida)
%
% SALIDA   rec (struct):
%   .tipo          'FIR' | 'IIR'
%   .estructura    'DF-II' | 'SOS' | 'DF simetrico' | ...
%   .justificacion texto en lenguaje natural (regla activada)
%   .confianza     nivel de confianza en [0,1]
%
% AUTOR:  Material de referencia PDS - Filtrado Digital FIR/IIR
% =========================================================================

function rec = agente_decision(specs)

  % --- Si se llama SIN argumentos: ejecutar el driver de validacion ---
  if nargin == 0
    ejecutar_validacion();
    rec = struct();           % retorno vacio (modo demo)
    return;
  end

  % --- Carga del paquete signal (no imprescindible aqui, pero homogeneo) ---
  if exist('OCTAVE_VERSION', 'builtin')
    try, pkg load signal; catch, end
  end

  % --- Valores por defecto para campos ausentes (robustez) ---
  specs = aplicar_defaults(specs);

  % --- Estimacion auxiliar: orden FIR aproximado para la transicion pedida ---
  %   Regla de Harris (ventana Hamming): N ~ 3.3 * fs / df,  df = ancho transicion.
  if strcmp(specs.pendiente, 'estrecha')
    df = 0.04 * (specs.fs/2);     % transicion estrecha ~ 4% de Nyquist
  else
    df = 0.15 * (specs.fs/2);     % transicion amplia    ~ 15% de Nyquist
  end
  orden_fir_est = ceil(3.3 * specs.fs / max(df, eps));

  % --- Heuristica: "sin FPU" se asume cuando hay poco computo (uC tipo AVR) ---
  sin_fpu = specs.mips < 20;

  % --- Inicializacion de la salida ---
  rec.tipo          = '';
  rec.estructura    = '';
  rec.justificacion = '';
  rec.confianza     = 0;
  rec.orden_fir_est = orden_fir_est;

  % =====================================================================
  % CADENA DE REGLAS IF-THEN  (orden = prioridad)
  % =====================================================================

  % R1: Fase lineal estricta -> FIR (preserva morfologia, p.ej. P-QRS-T)
  if specs.fase_lineal
    rec.tipo       = 'FIR';
    rec.estructura = 'DF simetrico';
    rec.justificacion = sprintf(['R1: Fase lineal estricta requerida => FIR ' ...
        'simetrico (preserva la morfologia de la senal, p.ej. P-QRS-T del ECG). ' ...
        'Orden FIR estimado ~ %d coef.'], orden_fir_est);
    rec.confianza = 0.95;

    % Excepcion dentro de R1: si la fase lineal es deseable pero la RAM no
    % alcanza para el FIR necesario, se advierte el conflicto de restricciones.
    if specs.ram_kb < 2 && orden_fir_est > 50
      rec.justificacion = [rec.justificacion ...
        ' AVISO: RAM < 2 kB insuficiente para este orden FIR; ' ...
        'evaluar relajar la fase lineal o aumentar memoria.'];
      rec.confianza = 0.60;
    end
    return;
  end

  % R2: RAM < 2 kB y orden FIR > 50 -> IIR (SOS) por memoria
  if specs.ram_kb < 2 && orden_fir_est > 50
    rec.tipo       = 'IIR';
    rec.estructura = 'SOS';
    rec.justificacion = sprintf(['R2: RAM < 2 kB y orden FIR estimado (%d) > 50 ' ...
        '=> FIR inviable en memoria; se usa IIR en cascada de biquads (SOS).'], ...
        orden_fir_est);
    rec.confianza = 0.90;
    return;
  end

  % R3: Estabilidad numerica critica sin FPU -> IIR en SOS
  if sin_fpu
    rec.tipo       = 'IIR';
    rec.estructura = 'SOS';
    rec.justificacion = ['R3: Plataforma sin FPU (computo muy bajo): la ' ...
        'estabilidad numerica es critica => IIR realizado en SOS (cada biquad ' ...
        'se cuantiza por separado, baja sensibilidad de coeficientes).'];
    rec.confianza = 0.85;
    return;
  end

  % R4: Transicion estrecha con computo suficiente -> IIR de orden adecuado
  if strcmp(specs.pendiente, 'estrecha') && specs.mips > 50
    rec.tipo       = 'IIR';
    rec.estructura = 'SOS';
    rec.justificacion = ['R4: Transicion estrecha (pendiente exigente) con ' ...
        'computo suficiente => IIR de orden adecuado en SOS; alcanza la ' ...
        'mascara con muchos menos coeficientes que un FIR.'];
    rec.confianza = 0.85;
    return;
  end

  % R5: SNR de entrada muy baja -> se prioriza rechazo fuerte con IIR
  if specs.snr_db < 0
    rec.tipo       = 'IIR';
    rec.estructura = 'DF-II';
    rec.justificacion = sprintf(['R5: SNR de entrada muy baja (%.1f dB): se ' ...
        'prioriza rechazo agresivo con IIR (forma directa DF-II canonica, ' ...
        'minima memoria) para orden moderado.'], specs.snr_db);
    rec.confianza = 0.70;
    return;
  end

  % R6: Caso general con recursos holgados -> FIR (DF simetrico)
  rec.tipo       = 'FIR';
  rec.estructura = 'DF simetrico';
  rec.justificacion = ['R6: Caso general sin restriccion critica y con ' ...
      'recursos holgados => FIR de fase lineal (robusto, siempre estable).'];
  rec.confianza = 0.65;

end  % function agente_decision

% =========================================================================
% Subfuncion: completa campos faltantes con valores por defecto razonables
% =========================================================================
function s = aplicar_defaults(s)
  if ~isfield(s,'fs')          || isempty(s.fs),          s.fs = 500;          end
  if ~isfield(s,'ram_kb')      || isempty(s.ram_kb),      s.ram_kb = 8;        end
  if ~isfield(s,'mips')        || isempty(s.mips),        s.mips = 50;         end
  if ~isfield(s,'fase_lineal') || isempty(s.fase_lineal), s.fase_lineal = false;end
  if ~isfield(s,'snr_db')      || isempty(s.snr_db),      s.snr_db = 10;       end
  if ~isfield(s,'latencia')    || isempty(s.latencia),    s.latencia = 'media';end
  if ~isfield(s,'pendiente')   || isempty(s.pendiente),   s.pendiente = 'amplia';end
end

% =========================================================================
% Subfuncion: DRIVER DE VALIDACION con los 3 escenarios del KB
% =========================================================================
function ejecutar_validacion()
  printf('================================================================\n');
  printf('  AGENTE DE DECISION FIR/IIR - Validacion (3 escenarios)\n');
  printf('================================================================\n\n');

  % --- Escenario 1: ECG en ESP32/STM32 (FPU, RAM holgada, fase lineal) ---
  e1 = struct('fs',500,'ram_kb',320,'mips',240,'fase_lineal',true, ...
              'snr_db',10,'latencia','media','pendiente','amplia');
  % Esperado: FIR (fase lineal preserva P-QRS-T)  -> activa R1

  % --- Escenario 2: Arduino UNO (2 kB RAM, 16 MHz, sin FPU) ---
  e2 = struct('fs',1000,'ram_kb',2,'mips',16,'fase_lineal',false, ...
              'snr_db',5,'latencia','baja','pendiente','estrecha');
  % Esperado: IIR/SOS (RAM escasa + sin FPU)      -> activa R2/R3

  % --- Escenario 3: instrumento con transicion exigente y computo alto ---
  e3 = struct('fs',2000,'ram_kb',64,'mips',120,'fase_lineal',false, ...
              'snr_db',8,'latencia','media','pendiente','estrecha');
  % Esperado: IIR de orden adecuado (SOS)          -> activa R4

  escenarios = {e1, e2, e3};
  nombres = {'ESP32/STM32 - ECG fase lineal', ...
             'Arduino UNO - RAM 2kB sin FPU', ...
             'Transicion exigente + computo alto'};

  for i = 1:numel(escenarios)
    s = escenarios{i};
    r = agente_decision(s);
    printf('----------------------------------------------------------------\n');
    printf('  Escenario %d: %s\n', i, nombres{i});
    printf('    Entrada: fs=%d Hz, RAM=%g kB, MIPS=%g, fase_lineal=%d,\n', ...
           s.fs, s.ram_kb, s.mips, s.fase_lineal);
    printf('             SNR=%g dB, latencia=%s, pendiente=%s\n', ...
           s.snr_db, s.latencia, s.pendiente);
    printf('    -> RECOMENDACION: %s   (estructura: %s)\n', r.tipo, r.estructura);
    printf('    -> Confianza: %.2f\n', r.confianza);
    printf('    -> Justificacion: %s\n', r.justificacion);
    printf('\n');
  end
  printf('================================================================\n');
  printf('  Validacion completada (coherente con Pasos 1-3 y Anexo I).\n');
  printf('================================================================\n');
end
