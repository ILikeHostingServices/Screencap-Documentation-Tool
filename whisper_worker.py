#!/usr/bin/env python3
#
# whisper_worker.py
# 2026-10-03
# Version: v1.0.0
#
# PURPOSE:
# Transcribes one audio file with faster-whisper (an offline version of
# OpenAI's Whisper speech recognition) and writes the timed segments to a
# JSON file. It runs as a separate process in the optional "whisper-env"
# Python environment, so the main tool keeps working with nothing but the
# Python standard library. Called by transcribe.py; not meant to be run by
# hand.
#
# Output JSON: {"language": "en", "duration": 12.3,
#               "segments": [{"start": 0.0, "end": 2.5, "text": "..."}]}
# Progress lines on stdout: "PROGRESS 0.42"
# Exit codes: 0 OK, 2 bad arguments, 3 faster-whisper not installed,
#             4 transcription failed (message on stderr)

import argparse
import json
import sys

EXIT_NOT_INSTALLED = 3
EXIT_FAILED = 4


def main(argv=None):
    p = argparse.ArgumentParser(description="Transcribe audio with faster-whisper.")
    p.add_argument("audio", help="16 kHz mono WAV file")
    p.add_argument("--model", default="base",
                   help="Model name (tiny, base, small, medium, or with .en) or folder")
    p.add_argument("--out", required=True, help="JSON file to write")
    p.add_argument("--language", default=None, help="Language code, e.g. en (default: detect)")
    args = p.parse_args(argv)

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        print(f"faster-whisper is not installed in this Python: {exc}", file=sys.stderr)
        return EXIT_NOT_INSTALLED

    try:
        # int8 on the CPU: works on any PC, no graphics card needed
        model = WhisperModel(args.model, device="cpu", compute_type="int8")
        segments, info = model.transcribe(args.audio, language=args.language,
                                          vad_filter=True)
        duration = float(getattr(info, "duration", 0) or 0)
        result = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                result.append({"start": round(float(seg.start), 2),
                               "end": round(float(seg.end), 2), "text": text})
            if duration:
                print(f"PROGRESS {min(float(seg.end) / duration, 1.0):.3f}", flush=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"language": getattr(info, "language", None),
                       "duration": duration, "segments": result}, fh, indent=2)
    except Exception as exc:  # report any model or decoding problem to the caller
        print(f"Transcription failed: {exc}", file=sys.stderr)
        return EXIT_FAILED
    return 0


if __name__ == "__main__":
    sys.exit(main())
