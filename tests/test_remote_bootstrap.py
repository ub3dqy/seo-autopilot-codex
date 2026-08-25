from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/ub3dqy/seo-autopilot-codex"
RAW_RU = "https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT.md"
RAW_EN = "https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT_EN.md"
RELEASE = "https://github.com/ub3dqy/seo-autopilot-codex/releases/tag/v1.5.0"
ASSET = (
    "https://github.com/ub3dqy/seo-autopilot-codex/releases/download/v1.5.0/"
    "seo-autopilot-codex-user-v1.5.0.zip"
)
SOURCE_COMMIT = "f2b272f8a1bf917470b09378a938fee068e4cf8e"
USER_SHA256 = "012ed6aba0c86f0a558efe6d88aad064dddcbaeeb725070434979bc73cd38589"


class RemoteBootstrapTests(unittest.TestCase):
    def test_readme_exposes_one_link_bootstrap(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(REPOSITORY, text)
        self.assertIn(RAW_RU, text)
        self.assertIn("START_AUTOPILOT.md", text)
        self.assertIn("текущей открытой папке", text)

    def test_russian_bootstrap_pins_verified_distribution_and_target_boundary(self) -> None:
        text = (ROOT / "START_AUTOPILOT.md").read_text(encoding="utf-8")
        for value in (REPOSITORY, RELEASE, ASSET, SOURCE_COMMIT, USER_SHA256):
            self.assertIn(value, text)
        self.assertIn("единственным целевым workspace", text)
        self.assertIn("не merge, не push и не deploy", text)
        self.assertIn("A_AUTO_FIX", text)
        self.assertIn("B_REVIEW_REQUIRED", text)
        self.assertIn("C_ADVISORY_ONLY", text)

    def test_english_bootstrap_pins_the_same_distribution(self) -> None:
        text = (ROOT / "START_AUTOPILOT_EN.md").read_text(encoding="utf-8")
        for value in (RAW_EN, REPOSITORY, RELEASE, ASSET, SOURCE_COMMIT, USER_SHA256):
            self.assertIn(value, text)
        self.assertIn("only target website workspace", text)
        self.assertIn("do not merge, push, or deploy", text)


if __name__ == "__main__":
    unittest.main()
