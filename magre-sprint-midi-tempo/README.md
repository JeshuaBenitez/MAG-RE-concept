# MAG-RE: Sprint MIDI–WAV de control de tempo

Prueba de concepto independiente para el sprint de incorporación de MAG-RE.
El experimento estudia exclusivamente controlabilidad y medición musical: no
evalúa regulación emocional, percepción afectiva ni efectos fisiológicos.

## Objetivo

Responder con evidencia si un motivo MIDI puede transformarse a 80, 100 y
120 BPM, renderizarse a WAV y medirse después de forma independiente. El
tempo solicitado solo se usa como referencia para calcular el error; el tempo
medido se estima desde las muestras del WAV.

## Alcance

Este directorio no modifica MAG-RE, E0 ni E1. El motivo tiene ocho compases en
4/4, una melodía, una capa de bajo y pulsos graves claramente identificables.
Todas las condiciones conservan las notas, velocidades, instrumentación y
estructura; solo se escalan los tiempos de los eventos y el tempo MIDI.

## MIDI y WAV

MIDI describe eventos musicales: notas, tiempos, duraciones, velocidades e
instrumentos. No contiene por sí mismo el sonido final. WAV contiene muestras
de audio. En este experimento, `pretty_midi` crea y lee los eventos MIDI, y un
sintetizador pequeño de NumPy genera las muestras con osciladores y envolventes
fijas. No se usa un SoundFont ni se depende de FluidSynth.

## Herramientas

- Python 3.11 o superior. La ejecución validada usó Python 3.14.8.
- `pretty_midi` 0.2.10 para estructura y lectura MIDI.
- NumPy 2.5.4 para señales y síntesis.
- SciPy 1.18.1 para WAV y filtrado.
- Matplotlib 3.11.2 para figuras.
- Pytest 8.4.2 para pruebas.
- `setuptools<81` por la dependencia `pkg_resources` de `pretty_midi`.

## Instalación en Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Requirements.txt
```

No se requieren permisos de administrador, FluidSynth, SoundFonts ni servicios
externos.

## Ejecución reproducible

Desde esta carpeta:

```bash
source .venv/bin/activate
python Generate.py
python Analyze.py
pytest -q
```

También puede ejecutarse todo con:

```bash
bash run_all.sh
```

`Generate.py` vuelve a crear `Motif.mid`, los tres MIDI derivados y los tres
WAV. `Analyze.py` vuelve a medir los WAV, escribe `results.csv` y regenera las
figuras.

## Métricas

| Métrica | Unidad | Definición |
|---|---:|---|
| BPM solicitado | BPM | Condición experimental de referencia |
| BPM medido | BPM | 60 dividido por el intervalo mediano entre pulsos graves detectados |
| Error absoluto | BPM | `abs(solicitado - medido)` |
| Error porcentual | % | `error absoluto / solicitado * 100` |
| RMS | amplitud FS | Raíz de la media cuadrática de las muestras |
| Peak amplitude | amplitud FS | Máximo valor absoluto de las muestras |
| Centroide espectral | Hz | Promedio ponderado de frecuencias por magnitud espectral |
| Nivel RMS | dBFS relativos | `20 * log10(RMS)`; no es loudness LUFS ni medición EBU R128 |
| Tasa de pulsos graves | Hz | Pulsos detectados tras filtrar la energía por debajo de 180 Hz; no es una tasa general de onsets |
| Duración | s | Número de muestras dividido por 44 100 |
| Clipping | muestras | Muestras con amplitud igual o superior a 0.999 |

El analizador no recibe ni consulta los archivos MIDI. La condición solicitada
solo entra en el cálculo posterior del error.

## Resultados medidos

| Archivo | Solicitado | Medido | Error BPM | Error % | RMS | Peak | Centroide (Hz) | Duración (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Tempo_80.wav` | 80 | 79.9976 | 0.0024 | 0.0030 | 0.029412 | 0.182251 | 413.34 | 24.20 |
| `Tempo_100.wav` | 100 | 99.9887 | 0.0113 | 0.0113 | 0.030034 | 0.176514 | 383.57 | 19.43 |
| `Tempo_120.wav` | 120 | 120.0000 | 0.0000 | 0.0000 | 0.030842 | 0.181641 | 441.23 | 16.25 |

Los valores completos, incluyendo nivel RMS en dBFS relativos, tasa de pulsos
graves y clipping, están en `results.csv`.

## Interpretación

Las tres condiciones muestran controlabilidad temporal alta en este motivo y
renderizador: el mayor error observado es 0.0113 BPM. También se observa una
variación pequeña en RMS, peak y centroide espectral. Esas diferencias pueden
deberse a la distinta duración temporal de las envolventes, a la relación
entre eventos y ventanas de análisis, y a la distribución de notas que queda
expuesta al cambiar el tempo. Constituyen posibles efectos secundarios o
cross-talk acústico, no una prueba de causalidad perceptual.

La alta fidelidad del tempo no demuestra que todas las propiedades musicales
sean igualmente controlables. Tampoco demuestra regulación emocional.

## Estructura

```text
Generate.py             Generación MIDI, escalado temporal y síntesis WAV
Analyze.py              Medición independiente y generación de CSV/figuras
Motif.mid               Motivo base a 100 BPM
Motif_80.mid            Motivo derivado a 80 BPM
Motif_100.mid           Motivo derivado a 100 BPM
Motif_120.mid           Motivo derivado a 120 BPM
Tempo_80.wav            Audio renderizado a 80 BPM
Tempo_100.wav           Audio renderizado a 100 BPM
Tempo_120.wav           Audio renderizado a 120 BPM
results.csv             Mediciones reales
figures/                Gráficas comparativas
tests/                  Pruebas automatizadas
EXPERIMENT_REPORT.md    Informe de resultados
DESIGN_DECISIONS.md     Decisiones técnicas
DEFENSA_TECNICA.md      Material para presentación
run_all.sh              Ejecución completa
```

## Limitaciones

- El sintetizador es intencionalmente mínimo y no representa un instrumento
  acústico real.
- La estimación de tempo depende de que el motivo tenga pulsos graves claros.
- El nivel RMS en dBFS relativos no sustituye un medidor de loudness conforme a
  una norma de sonoridad.
- No se evalúan percepción, emoción, fisiología ni calidad musical.
- Los cambios acústicos observados no permiten atribuir causalidad universal.
