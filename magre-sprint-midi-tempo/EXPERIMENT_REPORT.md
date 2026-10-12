# Informe experimental

## Pregunta

¿La modificación de tempo de un mismo motivo MIDI se conserva en el WAV y qué
otras métricas acústicas cambian?

## Método

Se creó un motivo original de ocho compases en 4/4 a 100 BPM con 32 notas de
melodía, 24 notas de bajo y 32 pulsos graves. Para cada condición se copiaron
los eventos, se multiplicaron sus tiempos por `100 / BPM_objetivo` y se escribió
un nuevo archivo MIDI con el tempo correspondiente. El WAV se sintetizó leyendo
esos MIDI derivados, con frecuencia de muestreo 44 100 Hz y ganancia fija común.

El analizador abrió únicamente cada WAV. Para estimar el tempo filtró la señal
por debajo de 180 Hz, calculó una envolvente de energía y obtuvo la mediana de
los intervalos entre pulsos detectados. No usó el BPM solicitado para encontrar
los pulsos. El BPM solicitado se incorporó únicamente después, para calcular
los errores definidos en el protocolo.

## Resultados reales

| Condición | BPM medido | Error absoluto | Error porcentual | RMS | Peak | Centroide Hz |
|---:|---:|---:|---:|---:|---:|---:|
| 80 | 79.9976 | 0.0024 | 0.0030 % | 0.029412 | 0.182251 | 413.34 |
| 100 | 99.9887 | 0.0113 | 0.0113 % | 0.030034 | 0.176514 | 383.57 |
| 120 | 120.0000 | 0.0000 | 0.0000 % | 0.030842 | 0.181641 | 441.23 |

El nivel RMS relativo fue -30.6296 dBFS, -30.4477 dBFS y -30.2170 dBFS para
80, 100 y 120 BPM, respectivamente. Esta métrica se calcula como
`20 * log10(RMS)` y no debe interpretarse como LUFS. La tasa reportada en el
CSV es `low_frequency_pulse_rate_hz`: pulsos detectados en la envolvente grave,
no una detección general de onsets.

No se detectaron muestras con clipping. Las duraciones fueron 24.20, 19.43 y
16.25 segundos, respectivamente.

## Interpretación

El tempo es controlable y fiel en las tres condiciones dentro de este
experimento. RMS y peak no permanecen idénticos, aunque la síntesis mantiene
una configuración de ganancia común. El centroide cambia entre condiciones;
esto puede reflejar la interacción entre la duración de las envolventes, la
ventana espectral y el número de eventos presentes por unidad de tiempo.

En consecuencia, la modificación de tempo sí tuvo efectos acústicos
secundarios observables. Estos resultados describen este motivo, sintetizador y
analizador. No prueban una relación general para cualquier música ni prueban
regulación emocional.

## Reproducibilidad

La generación es determinista: no utiliza aleatoriedad, conserva una ganancia
fija y mantiene la frecuencia de muestreo. Ejecutar dos veces `Generate.py` y
`Analyze.py` produce los mismos archivos y mediciones. Las pruebas verifican
existencia, frecuencia de muestreo, orden de duración, estructura MIDI y
mediciones válidas.

## Limitaciones y trabajo posterior

La detección de tempo funciona porque el motivo contiene un pulso grave por
beat. En música sin transitorios claros podrían aparecer estimaciones a mitad o
doble de tempo. Conviene evaluar posteriormente varios motivos, comparar con
una segunda técnica de detección y registrar incertidumbre de medición.