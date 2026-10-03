#!/usr/bin/env python3
#
# test_transcribe.py
# 2026-10-03
# Version: v1.0.0
#
# PURPOSE:
# Tests for Captions From Narration (transcribe.py and whisper_worker.py).
# Most tests use a stand-in for faster-whisper that returns known sentences,
# so they check the real audio extraction, worker process, caption matching,
# and output files without downloading a speech model. One opt-in test runs
# the real model on a real speech sample: set SCREENCAP_TEST_WHISPER=1,
# SCREENCAP_TEST_SPEECH to a WAV file of speech, and SCREENCAP_WHISPER_PYTHON
# to a Python with faster-whisper (the CI workflow does this).

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import FFMPEG, FFPROBE, fake_whisper, make_video  # noqa: E402

import screencap as sc  # noqa: E402
import transcribe  # noqa: E402


def step(t, still_from, caption=""):
    return {"time": t, "still_from": still_from, "still_to": None, "caption": caption}


class MatchingTests(unittest.TestCase):
    """Which step a spoken sentence belongs to."""

    def test_sentences_go_to_the_screen_they_were_spoken_on(self):
        doc = {"steps": [step(3.7, 0.0), step(7.7, 4.0), step(11.7, 8.0, "Typed by hand")]}
        segments = [{"start": 1.0, "end": 2.0, "text": "Run the installer."},
                    {"start": 3.5, "end": 4.3, "text": "Click Next."},   # middle 3.9: first screen
                    {"start": 5.0, "end": 6.0, "text": "Accept the license."},
                    {"start": 9.0, "end": 10.0, "text": "Click Install."}]
        filled = transcribe.apply(doc, segments)
        self.assertEqual(filled, 2)
        first, second, third = doc["steps"]
        self.assertEqual(first["caption"], "Run the installer. Click Next.")
        self.assertEqual(second["caption"], "Accept the license.")
        self.assertEqual(third["caption"], "Typed by hand")          # never replaced
        self.assertEqual(third["narration"], "Click Install.")      # but kept for reference

    def test_reordered_steps_still_match_by_time(self):
        doc = {"steps": [step(7.7, 4.0), step(3.7, 0.0)]}            # user moved step 2 up
        transcribe.apply(doc, [{"start": 5.0, "end": 6.0, "text": "Second screen."}])
        self.assertEqual(doc["steps"][0]["caption"], "Second screen.")
        self.assertEqual(doc["steps"][1]["caption"], "")

    def test_capture_at_start_uses_the_step_time(self):
        doc = {"steps": [step(0.5, None), step(4.5, None)]}
        transcribe.apply(doc, [{"start": 5.0, "end": 6.0, "text": "Later."}])
        self.assertEqual(doc["steps"][1]["caption"], "Later.")


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg not installed")
class NarrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_narration_"))
        cls.source = cls.tmp / "source"
        cls.source.mkdir()
        make_video(cls.source / "Demo.mp4", audio="tone")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_tool(self, *extra, source=None, output):
        return sc.main(["-s", str(source or self.source), "-o", str(output), "--no-redact",
                        *extra])

    def test_fills_empty_captions_and_writes_transcript(self):
        out = self.tmp / "out"
        self.assertEqual(self.run_tool(output=out), 0)
        doc_dir = out / "Demo"
        steps = json.loads((doc_dir / "steps.json").read_text(encoding="utf-8"))["steps"]
        self.assertGreaterEqual(len(steps), 3)
        # A sentence in the middle of each of the first two screens
        appeared = [s["still_from"] if s["still_from"] is not None else s["time"] for s in steps]
        segments = [{"start": appeared[0] + 0.5, "end": appeared[0] + 1.0,
                     "text": "Open the installer."},
                    {"start": appeared[1] + 0.5, "end": appeared[1] + 1.0,
                     "text": "Choose the install folder."}]
        with fake_whisper(self.tmp, segments):
            # Already processed: --transcribe works on the existing output
            self.assertEqual(self.run_tool("--transcribe", "--export", "html", output=out), 0)
        doc = json.loads((doc_dir / "steps.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["steps"][0]["caption"], "Open the installer.")
        self.assertEqual(doc["steps"][1]["caption"], "Choose the install folder.")
        self.assertEqual(doc["narration"]["segments"], 2)
        transcript = (doc_dir / transcribe.TRANSCRIPT_NAME).read_text(encoding="utf-8")
        self.assertIn("Choose the install folder.", transcript)
        self.assertIn("Choose the install folder.", (doc_dir / "steps.md").read_text(encoding="utf-8"))
        html = next((doc_dir / "export").glob("*.html")).read_text(encoding="utf-8")
        self.assertIn("Open the installer.", html)

        # A second run leaves the captions alone (they may have been edited)
        doc["steps"][0]["caption"] = "Edited by hand"
        (doc_dir / "steps.json").write_text(json.dumps(doc), encoding="utf-8")
        with fake_whisper(self.tmp, [{"start": 0.1, "end": 0.2, "text": "Different"}]):
            self.assertEqual(self.run_tool("--transcribe", output=out), 0)
        doc = json.loads((doc_dir / "steps.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["steps"][0]["caption"], "Edited by hand")

    def test_recording_without_audio(self):
        silent = self.tmp / "silent"
        silent.mkdir()
        make_video(silent / "Quiet.mp4", duration=8)
        out = self.tmp / "silent_out"
        with fake_whisper(self.tmp, [{"start": 1.0, "end": 2.0, "text": "Never used"}]):
            self.assertEqual(self.run_tool("--transcribe", source=silent, output=out), 0)
        doc = json.loads((out / "Quiet" / "steps.json").read_text(encoding="utf-8"))
        self.assertFalse(doc["narration"]["audio"])
        self.assertTrue(all(not s["caption"] for s in doc["steps"]))

    def test_missing_speech_recognition_is_a_setup_error(self):
        saved = os.environ.get("SCREENCAP_WHISPER_PYTHON")
        os.environ["SCREENCAP_WHISPER_PYTHON"] = str(self.tmp / "no-such-python")
        try:
            self.assertEqual(self.run_tool("--transcribe", output=self.tmp / "missing"),
                             sc.EXIT_SETUP_ERROR)
        finally:
            if saved is None:
                os.environ.pop("SCREENCAP_WHISPER_PYTHON", None)
            else:
                os.environ["SCREENCAP_WHISPER_PYTHON"] = saved

    def test_worker_without_faster_whisper_explains_how_to_install(self):
        doc = {"source_video": "Demo.mp4", "steps": [step(1.0, 0.0)]}
        with fake_whisper(self.tmp, [], installed=False):
            with self.assertRaises(transcribe.TranscribeError) as ctx:
                transcribe.transcribe(self.source / "Demo.mp4", self.tmp, doc, FFMPEG)
        self.assertIn("WithWhisper", str(ctx.exception))

    @unittest.skipUnless(os.environ.get("SCREENCAP_TEST_WHISPER") == "1",
                         "set SCREENCAP_TEST_WHISPER=1 to run the real speech model")
    def test_real_speech_model(self):
        speech = Path(os.environ["SCREENCAP_TEST_SPEECH"])
        src = self.tmp / "speech"
        src.mkdir()
        # The sample talks for about 11 s, starting 1 s into the recording
        make_video(src / "Talk.mp4", audio=speech, audio_delay=1.0)
        out = self.tmp / "speech_out"
        model = os.environ.get("SCREENCAP_TEST_WHISPER_MODEL", "tiny.en")
        self.assertEqual(self.run_tool("--transcribe", "--whisper-model", model,
                                       source=src, output=out), 0)
        doc_dir = out / "Talk"
        transcript = (doc_dir / transcribe.TRANSCRIPT_NAME).read_text(encoding="utf-8")
        print(transcript)
        self.assertIn("country", transcript.lower())
        doc = json.loads((doc_dir / "steps.json").read_text(encoding="utf-8"))
        self.assertTrue(any("country" in s["caption"].lower() for s in doc["steps"]))


if __name__ == "__main__":
    unittest.main()
