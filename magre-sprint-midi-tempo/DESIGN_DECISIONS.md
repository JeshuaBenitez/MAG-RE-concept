# Decisiones de diseño

## Renderizado sin FluidSynth

Se eligió un sintetizador mínimo con NumPy y SciPy. FluidSynth requeriría un
SoundFont, una dependencia del sistema y documentación adicional de licencia.
El sintetizador propio es suficiente para responder la pregunta experimental y
lee efectivamente los eventos de cada MIDI derivado.

## Uso de pretty_midi

`pretty_midi` reduce el riesgo de errores al escribir y leer eventos MIDI,
permite conservar instrumentos y velocidades, y escribe el tempo MIDI de cada
condición. Se fija `setuptools<81` porque la versión usada por
`pretty_midi` todavía importa `pkg_resources`.

## Control de comparabilidad

Se mantienen constantes el motivo, las velocidades, la instrumentación, la frecuencia de muestreo, los osciladores, las envolventes y la ganancia. No se
normaliza cada WAV por separado, porque eso ocultaría diferencias de amplitud.

## Medición independiente

`Analyze.py` no abre los MIDI ni importa funciones de `Generate.py`. Lee las muestras WAV, calcula la envolvente grave y mide intervalos de pulsos. El BPM solicitado solo se utiliza en la resta del error después de obtener el BPM
medido.

## Ambigüedad mitad/doble

Los detectores generales de onset pueden identificar subdivisiones en lugar del beat. Por eso se usa una capa grave de pulso y una distancia mínima de 0.40 s.
Esta elección no consulta los tres BPM objetivo; expresa una hipótesis sobre la señal musical observable. Su limitación es que no generaliza automáticamente a
motivos sin un pulso grave claro.

## Nivel RMS y pulsos detectados

El CSV incluye `rms_level_dbfs`, calculado como `20 * log10(RMS)`. Es un nivel
RMS relativo a escala completa y no una medición de loudness LUFS conforme a
EBU R128. El campo `low_frequency_pulse_rate_hz` cuenta pulsos detectados en la
envolvente de energía por debajo de 180 Hz; no representa una tasa general de
onsets espectrales.