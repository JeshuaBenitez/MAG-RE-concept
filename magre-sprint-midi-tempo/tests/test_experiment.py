import csv
import math
from pathlib import Path
import wave

import pretty_midi


ROOT = Path(__file__).resolve().parents[1]


def test_required_outputs_exist():
    # Sin estos archivos no se puede reproducir ni revisar el experimento.
    for path in ("Motif.mid", "Tempo_80.wav", "Tempo_100.wav", "Tempo_120.wav", "results.csv"):
        assert (ROOT / path).exists(), path


def test_wavs_are_nonempty_and_same_sample_rate():
    # Comprueba que hay audio real y que las tres condiciones usan el mismo muestreo.
    durations = []
    for tempo in (80, 100, 120):
        with wave.open(str(ROOT / f"Tempo_{tempo}.wav"), "rb") as handle:
            assert handle.getframerate() == 44100
            assert handle.getnframes() > 0
            durations.append(handle.getnframes())
    assert durations[0] > durations[1] > durations[2]


def test_midi_variations_preserve_note_structure():
    # El cambio de tempo debe conservar instrumentos, notas y velocidades.
    source = pretty_midi.PrettyMIDI(str(ROOT / "Motif.mid"))
    source_structure = [(instrument.program, instrument.is_drum, len(instrument.notes)) for instrument in source.instruments]
    source_notes = [(note.pitch, note.velocity) for instrument in source.instruments for note in instrument.notes]
    for tempo in (80, 100, 120):
        midi = pretty_midi.PrettyMIDI(str(ROOT / f"Motif_{tempo}.mid"))
        structure = [(instrument.program, instrument.is_drum, len(instrument.notes)) for instrument in midi.instruments]
        notes = [(note.pitch, note.velocity) for instrument in midi.instruments for note in instrument.notes]
        assert structure == source_structure == [(0, False, 32), (32, False, 24), (0, True, 32)]
        assert notes == source_notes


def test_midi_variations_change_only_timing():
    # Las variantes deben tener el BPM pedido y durar más cuanto más lentas sean.
    durations = []
    for tempo in (80, 100, 120):
        midi = pretty_midi.PrettyMIDI(str(ROOT / f"Motif_{tempo}.mid"))
        durations.append(midi.get_end_time())
        tempo_changes, values = midi.get_tempo_changes()
        assert math.isclose(float(values[0]), tempo, rel_tol=1e-12)
    assert durations[0] > durations[1] > durations[2]


def test_results_have_real_measurements():
    # El CSV debe contener números válidos y aplicar correctamente las fórmulas.
    with (ROOT / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["requested_bpm"]) for row in rows] == [80, 100, 120]
    numeric_fields = ("measured_bpm", "absolute_error_bpm", "percent_error", "rms", "peak_amplitude", "spectral_centroid_hz", "rms_level_dbfs", "low_frequency_pulse_rate_hz", "pulse_interval_seconds")
    for row in rows:
        for field in numeric_fields:
            assert math.isfinite(float(row[field])), field
        requested = float(row["requested_bpm"])
        measured = float(row["measured_bpm"])
        absolute_error = abs(requested - measured)
        assert math.isclose(float(row["absolute_error_bpm"]), absolute_error, rel_tol=1e-12)
        assert math.isclose(float(row["percent_error"]), absolute_error / requested * 100.0, rel_tol=1e-12)
        assert float(row["rms"]) > 0
        assert 0 < float(row["peak_amplitude"]) < 1
        assert float(row["spectral_centroid_hz"]) > 0
        assert math.isclose(float(row["rms_level_dbfs"]), 20 * math.log10(float(row["rms"])), rel_tol=1e-12)