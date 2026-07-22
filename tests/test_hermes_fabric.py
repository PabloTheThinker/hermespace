from __future__ import annotations
import os, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hermespace.hermes_fabric import rank_skills_for_goal, snapshot_fabric, skill_load_hints
from hermespace.engine import HermespaceEngine
from hermespace.memory_db import HermespaceMemory
from hermespace.workflow import Workflow
from hermespace.io_contract import HermespaceInput

class TestHermesFabric(unittest.TestCase):
    def test_rank_and_turn(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            hh = root / "hermes"
            sk = hh / "skills" / "telegram-ops"
            sk.mkdir(parents=True)
            (sk / "SKILL.md").write_text(
                "---\nname: telegram-ops\ndescription: Telegram gateway formatting and delivery\n---\n# Telegram ops\nPlain-first messages.\n"
            )
            sk2 = hh / "skills" / "baking"
            sk2.mkdir(parents=True)
            (sk2 / "SKILL.md").write_text(
                "---\nname: baking\ndescription: Sourdough bread recipes\n---\n# Baking\n"
            )
            (hh / "memories").mkdir()
            (hh / "memories" / "USER.md").write_text("User prefers concise replies.\n")
            (hh / "memories" / "MEMORY.md").write_text("Gateway uses hermes-gateway only.\n")
            os.environ["HERMES_HOME"] = str(hh)
            os.environ["HERMESPACE_NEURAL_VERBALIZE"] = "0"
            hits = rank_skills_for_goal("fix telegram gateway formatting", message="plain text")
            self.assertTrue(hits)
            # telegram should beat baking
            names = [h.name for h in hits]
            self.assertIn("telegram-ops", names)
            snap = snapshot_fabric(goal="telegram gateway", message="format")
            self.assertIn("concise", snap.user_excerpt.lower())
            self.assertTrue(snap.memory_excerpt)
            md = snap.inject_markdown()
            self.assertIn("Hermes fabric", md)
            self.assertTrue(skill_load_hints(hits))

            wf = Workflow(
                HermespaceEngine(desk_path=root / "ACTIVE.md"),
                HermespaceMemory(root=root),
            )
            wf.neural.config.verbalize = False
            out = wf.run(
                HermespaceInput(
                    message="fix telegram plain formatting",
                    goal="Fix telegram formatting",
                    decision="A",
                    plan=["patch"],
                    say="Fixing telegram formatting.",
                    force=True,
                )
            )
            self.assertIn("fabric", out.meta)
            self.assertIn("skill", out.context.lower() or "fabric")
            # context should mention skills or MEMORY
            ctx = out.context.lower()
            self.assertTrue("fabric" in ctx or "skill" in ctx or "memory" in ctx)

if __name__ == "__main__":
    unittest.main()
