from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/ub3dqy/seo-autopilot-codex"
RAW_RU = "https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT.md"
RAW_EN = "https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT_EN.md"
RELEASE = "https://github.com/ub3dqy/seo-autopilot-codex/releases/tag/v1.5.3"
ASSET = (
    "https://github.com/ub3dqy/seo-autopilot-codex/releases/download/v1.5.3/"
    "seo-autopilot-codex-engineering-v1.5.3.zip"
)
SOURCE_COMMIT = "f1afdce4393aa221f93a1dd45d04b9d082b10a2a"
SOURCE_TREE = "ca30c0acc00c768367c0519878115869cf53ad5b"
ASSET_SHA256 = "44502f8468ea5973f87ac21ce29f10b6f682f0db2eed044d719b7bdfefeca747"
VERSION = "1.5.3"


class RemoteBootstrapTests(unittest.TestCase):
    def test_readme_exposes_one_link_bootstrap(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for value in (REPOSITORY, RAW_RU, RELEASE, ASSET, SOURCE_COMMIT, SOURCE_TREE, ASSET_SHA256, VERSION):
            self.assertIn(value, text)
        self.assertIn("текущей открытой папке", text)
        self.assertIn("START_AUTOPILOT.md", text)

    def test_russian_bootstrap_pins_verified_runtime_and_target_boundary(self) -> None:
        text = (ROOT / "START_AUTOPILOT.md").read_text(encoding="utf-8")
        for value in (REPOSITORY, RELEASE, ASSET, SOURCE_COMMIT, SOURCE_TREE, ASSET_SHA256, VERSION):
            self.assertIn(value, text)
        self.assertIn("единственным целевым workspace", text)
        self.assertIn("PYTHONNOUSERSITE=1", text)
        self.assertIn("-S -m seo_autopilot --version", text)
        self.assertIn("не выполняй постоянную установку", text)
        self.assertIn("не merge, не push и не deploy", text)
        self.assertIn("A_AUTO_FIX", text)
        self.assertIn("B_REVIEW_REQUIRED", text)
        self.assertIn("C_ADVISORY_ONLY", text)

    def test_english_bootstrap_pins_the_same_runtime(self) -> None:
        text = (ROOT / "START_AUTOPILOT_EN.md").read_text(encoding="utf-8")
        for value in (RAW_EN, REPOSITORY, RELEASE, ASSET, SOURCE_COMMIT, SOURCE_TREE, ASSET_SHA256, VERSION):
            self.assertIn(value, text)
        self.assertIn("only target website workspace", text)
        self.assertIn("PYTHONNOUSERSITE=1", text)
        self.assertIn("-S -m seo_autopilot --version", text)
        self.assertIn("do not perform a persistent installation", text)
        self.assertIn("do not merge, push, or deploy", text)

    def test_v150_broken_bootstrap_pins_are_absent(self) -> None:
        combined = "\n".join(
            (ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "START_AUTOPILOT.md", "START_AUTOPILOT_EN.md")
        )
        self.assertNotIn("seo-autopilot-codex-engineering-v1.5.0.zip", combined)
        self.assertNotIn("f2b272f8a1bf917470b09378a938fee068e4cf8e", combined)
        self.assertNotIn("7fa55a6ace25a59b2d4ede821182365a233932f2", combined)
        self.assertNotIn("df7bec3c84c30b8b56c97dced52a384c1e9cbdeef424f6a474eaa746e46ed6e9", combined)


if __name__ == "__main__":
    unittest.main()
