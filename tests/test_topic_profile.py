import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_topic_profile import build  # noqa: E402
from validate import validate_document  # noqa: E402


class TopicProfileTests(unittest.TestCase):
    def test_builds_valid_wrapper(self):
        topic = json.loads((ROOT / "examples/drug-delivery/topic.json").read_text())
        profile = build(topic)
        self.assertEqual(profile["format"], "neurodaily.profile")
        self.assertIn("drug delivery", profile["config"]["search"]["query"])
        self.assertIn("AND NOT", profile["config"]["search"]["query"])
        errors, _ = validate_document(profile)
        self.assertEqual(errors, [])

    def test_rejects_empty_topic(self):
        with self.assertRaises(ValueError):
            build({})


if __name__ == "__main__":
    unittest.main()
