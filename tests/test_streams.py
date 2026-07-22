from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hermespace.streams import encode_stimulus, decode_to_report, production_stages
from hermespace.desk import Desk
from hermespace.engine import HermespaceEngine
import tempfile

class TestStreams(unittest.TestCase):
    def test_encode_multimodal(self):
        b = encode_stimulus(
            "look at this screenshot https://example.com/x.png and voice.ogg then say the answer about brain language"
        )
        self.assertTrue(b.text)
        self.assertTrue(b.audio)
        self.assertTrue(b.visual)
        self.assertTrue(b.production)

    def test_decode(self):
        s = decode_to_report(goal="Ship Meta reverse", decision="A", focus_texts=["lang"], load_level="mid")
        self.assertIn("Ship", s)

    def test_desk_streams_meta(self):
        d = Desk(goal="g", decision="A", say="s", concepts=[])
        d.recompute_cognition("research Meta brain language fMRI and voice message please")
        self.assertIn("streams", d.meta)
        self.assertGreater(d.meta["streams"].get("text", 0), 0)

    def test_enter_decode_say(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ACTIVE.md"
            eng = HermespaceEngine(desk_path=path)
            desk = eng.enter(
                goal="Test decode",
                decision="A — go",
                say="",
                concepts=[],
                auto_load=False,
                user_message="build hermespace streams",
            )
            self.assertTrue(desk.say.strip())

if __name__ == "__main__":
    unittest.main()
