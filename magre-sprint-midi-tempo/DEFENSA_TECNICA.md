# Defensa técnica

## Explicación breve

MIDI es una descripción de eventos musicales, no audio. Contiene notas,
duraciones, tiempos, velocidades e instrumentos. WAV contiene muestras de una
señal sonora. El experimento modifica los tiempos de los eventos MIDI, lee los
MIDI derivados y los convierte a muestras mediante un sintetizador determinista.

El analizador no consulta los archivos MIDI. Detecta pulsos en el WAV filtrando
la energía grave, mide los intervalos entre transitorios y calcula:

```text
BPM medido = 60 / intervalo mediano entre pulsos
error absoluto = |BPM solicitado - BPM medido|
error porcentual = error absoluto / BPM solicitado * 100
```

## Métricas acústicas

- **RMS:** energía media de la señal; ayuda a comparar amplitud global.
- **Peak amplitude:** mayor amplitud absoluta; ayuda a detectar picos y riesgo
  de clipping.
- **Centroide espectral:** centro de masa del espectro en Hz; suele asociarse
  con brillo, aunque no equivale por sí solo a una percepción concreta.
- **Nivel RMS en dBFS relativos:** `20 * log10(RMS)`. Describe amplitud RMS
  respecto a escala completa; no es loudness LUFS.
- **Tasa de pulsos graves:** cantidad de pulsos detectados por segundo después
  de filtrar la energía por debajo de 180 Hz. No es una tasa general de onsets.

## Controlabilidad, fidelidad y cross-talk

Controlabilidad es poder variar sistemáticamente el tempo. Fidelidad es cuánto
coincide el tempo medido con el solicitado. Cross-talk es que el cambio de
tempo modifique también RMS, peak o centroide. Un cambio secundario no es
automáticamente un error: puede ser esperado por la síntesis, pero debe
medirse y documentarse.

## Demostración de 2–3 minutos

1. Mostrar `Motif.mid` como la misma estructura de referencia.
2. Ejecutar `python Generate.py` y señalar que aparecen tres WAV y tres MIDI
   derivados.
3. Reproducir brevemente `Tempo_80.wav`, `Tempo_100.wav` y `Tempo_120.wav`.
4. Ejecutar `python Analyze.py`.
5. Mostrar `results.csv` y explicar que el BPM medido proviene de las muestras.
6. Comparar `bpm_comparison.png` con `acoustic_metrics.png`.
7. Concluir que el tempo fue controlable en este caso, pero que no se estudió
   regulación emocional.

## Preguntas probables

### 1. ¿Por qué usar MIDI?

Porque separa la intención musical de las muestras de audio y permite modificar
el tiempo de los eventos conservando notas, velocidades e instrumentación.

### 2. ¿Cómo se modifica el tempo?

Cada tiempo de evento se multiplica por `100 / BPM_objetivo`. Además, el archivo
MIDI derivado contiene el tempo objetivo. Por eso cambia la duración temporal
real de notas y pulsos, no solo una etiqueta.

### 3. ¿Cómo se evita circularidad en la medición?

El analizador abre los WAV sin leer los MIDI ni las variables internas del
generador. El BPM solicitado solo participa en el cálculo posterior del error.

### 4. ¿Qué significa un error pequeño?

Significa que este motivo y este sintetizador produjeron intervalos de pulsos
compatibles con la condición solicitada. No significa que cualquier música,
renderizador o detector tendrá el mismo resultado.

### 5. ¿Los cambios de RMS y centroide prueban cross-talk?

Muestran cambios secundarios observables, compatibles con cross-talk, pero no
prueban por sí solos su causa. Habría que repetir con más motivos, controles y
un protocolo de análisis más amplio.

## Resumen de los scripts

`Generate.py` construye ocho compases, escala tiempos, escribe MIDI derivados,
lee cada derivado y sintetiza WAV con configuración constante.

`Analyze.py` lee cada WAV, mide pulsos graves, calcula errores, RMS, peak,
centroide, nivel RMS en dBFS relativos, duración, tasa de pulsos graves y
clipping, y escribe el CSV y las gráficas.

## Tabla para la diapositiva 8

| BPM solicitado | BPM medido | Error BPM | Error % | RMS | Peak | Centroide Hz |
|---:|---:|---:|---:|---:|---:|---:|
| 80 | 79.9976 | 0.0024 | 0.0030 | 0.029412 | 0.182251 | 413.34 |
| 100 | 99.9887 | 0.0113 | 0.0113 | 0.030034 | 0.176514 | 383.57 |
| 120 | 120.0000 | 0.0000 | 0.0000 | 0.030842 | 0.181641 | 441.23 |

## Conclusión defendible

La cadena MIDI–WAV–medición demuestra control temporal y permite observar
cambios acústicos secundarios en un caso reproducible. No demuestra regulación
emocional, causalidad afectiva, eficacia clínica ni un sistema closed-loop.