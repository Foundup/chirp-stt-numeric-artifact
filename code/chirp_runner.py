import argparse
import json
from pathlib import Path
from typing import List


def ensure_directories(audio_dir: Path, json_dir: Path) -> None:
    audio_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)


def list_audio_files(audio_dir: Path) -> List[Path]:
    patterns = ["*.wav", "*.mp3", "*.flac", "*.m4a", "*.ogg"]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(audio_dir.glob(pattern))
    return sorted(files)


def write_stub_log(json_dir: Path, audio_file: Path) -> None:
    stub = {
        "audio_file": str(audio_file),
        "status": "pending",
        "note": "Extend chirp_runner.py with STT transcription and write real outputs here.",
    }
    out_path = json_dir / f"{audio_file.stem}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(stub, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal Chirp STT runner scaffold")
    parser.add_argument("--audio-dir", default="audio", help="Directory containing input audio files")
    parser.add_argument("--json-dir", default="json", help="Directory to write transcript JSON outputs")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    json_dir = Path(args.json_dir)
    ensure_directories(audio_dir, json_dir)

    audio_files = list_audio_files(audio_dir)
    if not audio_files:
        print(f"No audio found in {audio_dir}. Add WAV/MP3 and re-run.")
        return

    for af in audio_files:
        write_stub_log(json_dir, af)

    print(f"Prepared {len(audio_files)} stub JSON outputs in {json_dir}.")
    print("TODO: Implement STT transcription and replace stubs with real results.")


if __name__ == "__main__":
    main()
