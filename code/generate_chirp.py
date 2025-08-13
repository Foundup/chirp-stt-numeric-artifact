import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile


def generate_chirp(out_path: Path, sample_rate: int, duration: float, start_freq: float, end_freq: float) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(sample_rate * duration)
    t = np.linspace(0.0, duration, num_samples, endpoint=False)
    k = (end_freq - start_freq) / duration
    # Phase for linear chirp: 2π (f0 t + 0.5 k t^2)
    phase = 2.0 * np.pi * (start_freq * t + 0.5 * k * t * t)
    signal_float = np.sin(phase)
    # Convert to 16-bit PCM
    signal_int16 = np.int16(np.clip(signal_float, -1.0, 1.0) * 32767)
    wavfile.write(str(out_path), sample_rate, signal_int16)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a linear chirp WAV file")
    parser.add_argument("--out", default=str(Path("audio") / "chirp.wav"), help="Output WAV file path")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Samples per second")
    parser.add_argument("--duration", type=float, default=1.0, help="Duration in seconds")
    parser.add_argument("--start-freq", type=float, default=500.0, help="Start frequency (Hz)")
    parser.add_argument("--end-freq", type=float, default=1500.0, help="End frequency (Hz)")
    args = parser.parse_args()

    out_path = Path(args.out)
    generate_chirp(out_path, args.sample_rate, args.duration, args.start_freq, args.end_freq)
    print(f"Successfully generated '{out_path}'")


if __name__ == "__main__":
    main()
