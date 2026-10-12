"""Genera un motivo MIDI y tres renderizados WAV con tempo controlado."""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pretty_midi
from scipy.io import wavfile


ROOT = Path(__file__).resolve().parent
SAMPLE_RATE = 44_100  # Mismo número de muestras por segundo en todos los WAV.
BASE_TEMPO = 100.0  # BPM del motivo original.
TARGET_TEMPOS = (80, 100, 120)  # BPM que se van a probar.
MOTIF_PATH = ROOT / "Motif.mid"
FIXED_GAIN = 0.22


def build_motif() -> pretty_midi.PrettyMIDI:
    """Crea un motivo original de ocho compases en 4/4 a 100 BPM."""
    # MIDI guarda notas y tiempos, no sonido. Así podemos cambiar el tempo
    # antes de crear el WAV y comprobar después qué ocurrió en el audio.
    midi = pretty_midi.PrettyMIDI(initial_tempo=BASE_TEMPO)

    # La melodía hace reconocible el motivo y los pulsos graves ayudan a medir
    # el tempo después. Ocho compases en 4/4 dan una estructura sencilla.
    melody = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program("Acoustic Grand Piano"))
    bass = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program("Acoustic Bass"))
    drums = pretty_midi.Instrument(program=0, is_drum=True, name="Pulse")

    # Convertimos BPM a segundos por pulso para colocar cada nota en el tiempo.
    quarter = 60.0 / BASE_TEMPO
    scale = [60, 62, 64, 67, 69, 67, 64, 62]
    chords = [(48, 52, 55), (53, 57, 60), (55, 59, 62), (50, 53, 57)]

    # Cada nota tiene un inicio y un final. La duración menor que un pulso
    # deja un pequeño espacio entre notas y hace más claros los ataques.
    for step in range(32):
        start = step * quarter
        pitch = scale[step % len(scale)] + (12 if step // 8 % 2 else 0)
        melody.notes.append(pretty_midi.Note(velocity=92, pitch=pitch, start=start, end=start + quarter * 0.78))

    for bar in range(8):
        bar_start = bar * quarter * 4
        chord = chords[bar % len(chords)]
        for pitch in chord:
            bass.notes.append(pretty_midi.Note(velocity=62, pitch=pitch, start=bar_start, end=bar_start + quarter * 3.8))
        for beat in range(4):
            start = bar_start + beat * quarter
            drums.notes.append(pretty_midi.Note(velocity=118, pitch=36, start=start, end=start + 0.06))

    midi.instruments.extend([melody, bass, drums])
    return midi


def scale_midi_tempo(source: pretty_midi.PrettyMIDI, target_bpm: float) -> pretty_midi.PrettyMIDI:
    """Cambia los tiempos de las notas para usar otro BPM."""
    result = pretty_midi.PrettyMIDI(initial_tempo=target_bpm)
    # Si el nuevo tempo es más rápido, los tiempos deben ser menores. Este
    # factor mantiene las mismas proporciones musicales en cada variante.
    time_scale = BASE_TEMPO / target_bpm
    for source_instrument in source.instruments:
        instrument = copy.deepcopy(source_instrument)
        for note in instrument.notes:
            # Cambiamos inicio y final; cambiar solo uno deformaría la duración
            # de la nota y modificaría la estructura musical.
            note.start *= time_scale
            note.end *= time_scale
        for pitch_bend in instrument.pitch_bends:
            pitch_bend.time *= time_scale
        for control_change in instrument.control_changes:
            control_change.time *= time_scale
        result.instruments.append(instrument)
    return result


def _envelope(length: int, attack: int, release: int) -> np.ndarray:
    """Crea el inicio y el final suave de una nota."""
    envelope = np.ones(length, dtype=np.float32)
    if attack:
        envelope[:attack] = np.linspace(0.0, 1.0, attack, endpoint=False, dtype=np.float32)
    if release:
        envelope[-release:] = np.linspace(1.0, 0.0, release, endpoint=True, dtype=np.float32)
    return envelope


def synthesize(midi_path: Path, wav_path: Path) -> None:
    """Convierte las notas MIDI en audio WAV.

    Todos los archivos usan la misma ganancia para poder compararlos.
    """
    # El MIDI contiene instrucciones. Aquí las convertimos en muestras de
    # audio, porque el WAV sí contiene el sonido que luego vamos a medir.
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    duration = midi.get_end_time() + 0.35  # Margen de silencio final constante.
    # 44 100 muestras por segundo es la frecuencia usada en los tres WAV.
    audio = np.zeros(int(np.ceil(duration * SAMPLE_RATE)), dtype=np.float32)

    for instrument in midi.instruments:
        for note in instrument.notes:
            start_index = int(round(note.start * SAMPLE_RATE))
            end_index = min(len(audio), int(round(note.end * SAMPLE_RATE)))
            # Convertimos el tiempo de la nota a posiciones del audio.
            if end_index <= start_index:
                continue
            count = end_index - start_index
            time = np.arange(count, dtype=np.float32) / SAMPLE_RATE
            if instrument.is_drum:
                decay = np.exp(-time * 34.0)
                tone = np.sin(2.0 * np.pi * (120.0 - 55.0 * time) * time) * decay
                signal = tone * (note.velocity / 127.0) * 0.75
            else:
                # La fórmula convierte el número de nota MIDI en frecuencia.
                # Se mezclan una onda seno y dos armónicos para crear el timbre.
                frequency = 440.0 * 2.0 ** ((note.pitch - 69) / 12.0)
                phase = 2.0 * np.pi * frequency * time
                tone = 0.78 * np.sin(phase) + 0.16 * np.sin(2.0 * phase) + 0.06 * np.sin(3.0 * phase)
                # Convertimos el número MIDI en una frecuencia.
                attack = min(int(0.012 * SAMPLE_RATE), count // 3)
                release = min(int(0.06 * SAMPLE_RATE), count // 3)
                signal = tone * _envelope(count, attack, release) * (note.velocity / 127.0) * 0.20

            # Las notas de las tres capas se suman en el mismo arreglo de audio.
            audio[start_index:end_index] += signal.astype(np.float32)

    # Una ganancia común permite comparar amplitudes. No normalizamos cada WAV
    # por separado porque eso ocultaría diferencias entre condiciones.
    audio *= FIXED_GAIN
    audio = np.clip(audio, -1.0, 1.0)
    # PCM de 16 bits convierte amplitudes entre -1 y 1 en muestras enteras.
    wavfile.write(wav_path, SAMPLE_RATE, np.asarray(audio * 32767.0, dtype=np.int16))


def main() -> None:
    """Crea el motivo base, sus variantes temporales y sus WAV correspondientes."""
    source = build_motif()
    source.write(str(MOTIF_PATH))
    for tempo in TARGET_TEMPOS:
        variation = scale_midi_tempo(source, tempo)
        variation_path = ROOT / f"Motif_{tempo}.mid"
        variation_path.unlink(missing_ok=True)
        variation.write(str(variation_path))
        synthesize(variation_path, ROOT / f"Tempo_{tempo}.wav")
        print(f"Generado: Tempo_{tempo}.wav ({variation.get_end_time():.3f} s)")


if __name__ == "__main__":
    main()