import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple

from gtts import gTTS
from google.protobuf.json_format import MessageToJson


BASE = Path(__file__).resolve().parent
AUDIO_DIR = BASE / "audio"
RESULTS_DIR = BASE / "results"
PHRASES_FILE = BASE / "data" / "test_phrases.txt"


def ensure_dirs() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_phrases() -> List[str]:
    with PHRASES_FILE.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def synthesize_gtts(phrase: str, out_path: Path) -> None:
    tts = gTTS(text=phrase, lang="en", slow=False)
    tts.save(str(out_path))


def load_bytes(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read()


def try_transcribe_v2(content: bytes, recognizer: str) -> Tuple[str, float, dict]:
    from google.cloud import speech_v2

    client = speech_v2.SpeechClient()
    config = speech_v2.RecognitionConfig(
        auto_decoding_config=speech_v2.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
    )
    request = speech_v2.RecognizeRequest(
        recognizer=recognizer,
        config=config,
        content=content,
    )
    response = client.recognize(request=request)
    payload = json.loads(MessageToJson(response._pb))

    transcript = ""
    confidence = 0.0
    if response.results:
        alts = response.results[0].alternatives
        if alts:
            transcript = alts[0].transcript
            confidence = alts[0].confidence or 0.0

    return transcript, confidence, payload


def transcribe_v1(content: bytes) -> Tuple[str, float, dict]:
    from google.cloud import speech_v1 as speech

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        language_code="en-US",
    )
    audio = speech.RecognitionAudio(content=content)
    response = client.recognize(config=config, audio=audio)
    payload = json.loads(MessageToJson(response._pb))

    transcript = ""
    confidence = 0.0
    if response.results:
        alts = response.results[0].alternatives
        if alts:
            transcript = alts[0].transcript
            confidence = alts[0].confidence or 0.0

    return transcript, confidence, payload


def main() -> None:
    ensure_dirs()
    phrases = read_phrases()

    recognizer = os.getenv("GCP_RECOGNIZER", "").strip()

    rows: List[List[str]] = []
    # Generate audio and transcribe
    for idx, phrase in enumerate(phrases):
        mp3_path = AUDIO_DIR / f"{idx:02d}.mp3"
        synthesize_gtts(phrase, mp3_path)
        content = load_bytes(mp3_path)

        used_v2 = False
        transcript = ""
        confidence = 0.0
        payload: dict = {}
        if recognizer:
            try:
                transcript, confidence, payload = try_transcribe_v2(content, recognizer)
                used_v2 = True
            except Exception as e:
                used_v2 = False
                print(f"v2 failed for {mp3_path.name}: {e}. Falling back to v1.")

        if not used_v2:
            transcript, confidence, payload = transcribe_v1(content)

        rows.append([phrase, transcript, f"{confidence:.3f}", "v2" if used_v2 else "v1"])
        # Save raw JSON
        variant = "v2" if used_v2 else "v1"
        with (RESULTS_DIR / f"{idx:02d}.{variant}.json").open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # Write CSV table
    with (RESULTS_DIR / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["input_phrase", "transcript", "confidence", "api"])
        writer.writerows(rows)

    # Pretty print
    print("\nResults:\n")
    print(f"{'Input':40s} | {'Transcript':40s} | Conf  | API")
    print("-" * 100)
    for r in rows:
        print(f"{r[0][:40]:40s} | {r[1][:40]:40s} | {r[2]:5s} | {r[3]}")


if __name__ == "__main__":
    main()
