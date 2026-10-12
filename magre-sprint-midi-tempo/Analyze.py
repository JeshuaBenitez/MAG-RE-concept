"""Mide los WAV sin consultar los parámetros internos del generador."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, find_peaks, get_window, sosfiltfilt


ROOT = Path(__file__).resolve().parent
SAMPLE_RATE = 44_100
TARGET_TEMPOS = (80, 100, 120)
RESULTS_PATH = ROOT / "results.csv"


def read_audio(path: Path) -> tuple[int, np.ndarray]:
    """Lee un WAV y convierte sus muestras a números comparables."""
    # El WAV contiene la frecuencia de muestreo y las muestras del audio final.
    # Medir este archivo, y no el MIDI, mantiene independiente la evaluación.
    sample_rate, data = wavfile.read(path)
    audio = data.astype(np.float64)
    # Así todas las medidas usan la misma escala.
    if data.dtype == np.int16:
        audio /= 32768.0
    elif np.issubdtype(data.dtype, np.integer):
        audio /= float(np.iinfo(data.dtype).max)
    if audio.ndim == 2:
        # El análisis usa un solo canal para que todas las métricas sean iguales.
        audio = np.mean(audio, axis=1)
    return sample_rate, audio


def onset_envelope(audio: np.ndarray, sample_rate: int, frame_size: int = 2048, hop: int = 256) -> np.ndarray:
    """Busca cambios rápidos en el sonido.

    No se usa para el BPM final porque puede contar subdivisiones como pulsos.
    """
    # Se compara la energía de ventanas consecutivas para encontrar ataques.
    padded = np.pad(audio, (0, frame_size))
    frames = np.lib.stride_tricks.sliding_window_view(padded, frame_size)[::hop]
    spectrum = np.abs(np.fft.rfft(frames * get_window("hann", frame_size), axis=1))
    flux = np.maximum(
        0.0, 
        np.diff(spectrum, axis=0)
    ).sum(axis=1)
    return np.pad(flux, (1, 0))


def estimate_bpm(audio: np.ndarray, sample_rate: int) -> tuple[float, float, float]:
    """Estima el BPM midiendo los intervalos entre pulsos graves del WAV.

    El motivo tiene un pulso grave por tiempo, lo que ayuda a no contar el
    doble de pulsos.
    """
    # El límite de 180 Hz conserva el pulso grave de este motivo y reduce la
    # influencia de la melodía. No se obtiene del BPM solicitado.
    low_frequency = sosfiltfilt(
        butter(
            4, 
            180.0, 
            btype="lowpass", 
            fs=sample_rate, output="sos"
        ), 
        audio
    )
    # Dejamos principalmente el pulso grave del motivo.
    # La envolvente muestra cómo cambia la amplitud del pulso a lo largo del tiempo.
    smoothing_window = max(1, int(0.05 * sample_rate))
    envelope = np.convolve(np.abs(low_frequency), np.ones(smoothing_window) / smoothing_window, mode="same")
    # Solo aceptamos picos claramente separados; así evitamos contar ruido.
    prominence = max(np.median(envelope) * 0.05, np.std(envelope) * 0.1)
    peaks, _ = find_peaks(envelope, distance=int(0.40 * sample_rate), prominence=prominence)
    if len(peaks) < 3:
        return float("nan"), 0.0, float("nan")
    # Las diferencias entre picos están en muestras; al dividir por la
    # frecuencia de muestreo obtenemos segundos entre pulsos.
    intervals = np.diff(peaks) / sample_rate
    intervals = intervals[(intervals >= 0.40) & (intervals <= 1.50)]
    if len(intervals) == 0:
        return float("nan"), len(peaks) / (len(audio) / sample_rate), float("nan")
    # La mediana reduce el efecto de un intervalo aislado mal detectado.
    median_interval = float(np.median(intervals))
    # Un minuto tiene 60 segundos: BPM = 60 / segundos por pulso.
    bpm = 60.0 / median_interval
    return bpm, len(peaks) / (len(audio) / sample_rate), median_interval


def spectral_centroid(audio: np.ndarray, sample_rate: int, frame_size: int = 2048, hop: int = 1024) -> float:
    """Calcula el centro de las frecuencias del WAV, en Hz."""
    padded = np.pad(audio, (0, frame_size))
    frames = np.lib.stride_tricks.sliding_window_view(padded, frame_size)[::hop]
    magnitudes = np.abs(np.fft.rfft(frames * get_window("hann", frame_size), axis=1))
    frequencies = np.fft.rfftfreq(frame_size, 1.0 / sample_rate)
    # Es un promedio ponderado de las frecuencias presentes. Un valor alto
    # suele indicar más brillo, pero no demuestra una emoción concreta.
    denominator = magnitudes.sum(axis=1)
    centroids = np.divide((magnitudes * frequencies).sum(axis=1), denominator, out=np.zeros_like(denominator), where=denominator > 0)
    return float(np.mean(centroids))


def measure(path: Path, requested_bpm: int) -> dict[str, float | int | str]:
    """Calcula las medidas del WAV y el error respecto al BPM pedido."""
    sample_rate, audio = read_audio(path)
    measured_bpm, pulse_rate, interval = estimate_bpm(audio, sample_rate)
    # El BPM pedido solo sirve como referencia. Nunca se usa para encontrar
    # los pulsos ni para corregir el valor medido.
    error = abs(requested_bpm - measured_bpm)
    rms = float(np.sqrt(np.mean(audio**2)))
    peak = float(np.max(np.abs(audio)))
    return {
        "file": path.name,
        "requested_bpm": requested_bpm,
        "measured_bpm": measured_bpm,
        # Estas son las fórmulas definidas para comparar control y fidelidad.
        "absolute_error_bpm": error,
        "percent_error": error / requested_bpm * 100.0,
        "sample_rate_hz": sample_rate,
        "duration_seconds": len(audio) / sample_rate,
        # RMS resume la amplitud media; peak muestra el valor máximo alcanzado.
        "rms": rms,
        "peak_amplitude": peak,
        "spectral_centroid_hz": spectral_centroid(audio, sample_rate),
        # Es un nivel basado en RMS, no una medida LUFS.
        "rms_level_dbfs": 20.0 * np.log10(max(rms, 1e-12)),
        "low_frequency_pulse_rate_hz": pulse_rate,
        "pulse_interval_seconds": interval,
        "tempo_detection_method": "envolvente de energía grave y mediana de intervalos",
        "clipping_samples": int(np.count_nonzero(np.abs(audio) >= 0.999)),
    }


def make_figures(rows: list[dict[str, float | int | str]]) -> None:
    """Genera las gráficas comparativas a partir de las filas ya medidas."""
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    x = [row["requested_bpm"] for row in rows]
    measured = [row["measured_bpm"] for row in rows]
    # La primera figura compara directamente el tempo pedido con el medido.
    plt.figure(figsize=(7, 4))
    plt.plot(x, x, "k--", label="Referencia")
    plt.plot(x, measured, "o-", label="BPM medido")
    plt.xlabel("BPM solicitado")
    plt.ylabel("BPM")
    plt.title("Control y medición independiente del tempo")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "bpm_comparison.png", dpi=150)
    plt.close()

    # La segunda figura ayuda a observar posibles cambios secundarios entre
    # condiciones, sin afirmar que sean necesariamente errores.
    plt.figure(figsize=(8, 4))
    for key, label in (("rms", "RMS"), ("peak_amplitude", "Peak"), ("spectral_centroid_hz", "Centroide / 1000")):
        values = [row[key] / 1000.0 if key == "spectral_centroid_hz" else row[key] for row in rows]
        plt.plot(x, values, "o-", label=label)
    plt.xlabel("BPM solicitado")
    plt.ylabel("Valor medido; centroide en kHz")
    plt.title("Métricas acústicas secundarias")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures / "acoustic_metrics.png", dpi=150)
    plt.close()


def main() -> None:
    """Analiza las tres condiciones y escribe el CSV y las figuras."""
    rows = [measure(ROOT / f"Tempo_{tempo}.wav", tempo) for tempo in TARGET_TEMPOS]
    with RESULTS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    make_figures(rows)
    for row in rows:
        print(f"{row['file']}: solicitado={row['requested_bpm']} medido={row['measured_bpm']:.3f} error={row['percent_error']:.3f}%")


if __name__ == "__main__":
    main()