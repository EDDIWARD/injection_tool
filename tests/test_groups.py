import copy
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from injection_tool.core import ROOT, generate, load_catalog, serialize, write_payload_files
from injection_tool.groups import GROUP_IDS, GROUP_NAMES, classify_group, group_counts, organize


class GroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()
        cls.index = json.loads((ROOT / "data/groups.json").read_text(encoding="utf-8"))
        cls.methods = json.loads((ROOT / "data/methods.json").read_text(encoding="utf-8"))
        cls.research = json.loads((ROOT / "data/research.json").read_text(encoding="utf-8"))
        with gzip.open(ROOT / "data/examples.jsonl.gz", "rt", encoding="utf-8") as stream:
            cls.examples = [json.loads(line) for line in stream]

    def test_every_record_has_one_group_and_counts_match(self):
        for kind, rows in (("template", self.catalog["templates"]), ("example", self.examples),
                           ("method", self.methods), ("paper", self.research["papers"])):
            with self.subTest(kind=kind):
                for row in rows:
                    self.assertIn(row["group"], GROUP_IDS)
                    self.assertEqual((row["group"], row["group_assignment"]["rule"]), classify_group(row))
                counts = group_counts(rows)
                self.assertEqual(sum(counts.values()), len(rows))
                self.assertEqual(counts, self.catalog["stats"][kind + "s_by_group"])
                self.assertEqual(counts, {g["id"]: g[kind + "_count"] for g in self.index["groups"]})
        self.assertEqual(self.catalog["groups"], self.index["groups"])

    def test_primary_groups_partition_generation_and_combine_with_tags(self):
        all_rows = generate("TEST_OK")["results"]
        ids = set()
        for gid in GROUP_IDS:
            result = generate("TEST_OK", groups=[gid])
            self.assertTrue(result["count"])
            current = {r["id"] for r in result["results"]}
            self.assertFalse(ids & current)
            ids.update(current)
            self.assertTrue(all(r["group"] == gid for r in result["results"]))
            self.assertEqual(result["group_counts"][gid], result["count"])
            self.assertEqual(sum(result["group_counts"].values()), result["count"])
        self.assertEqual(ids, {r["id"] for r in all_rows})
        multi = generate("TEST_OK", groups=["template", "roleplay", "roleplay"], sources=["local"], language="zh")
        expected = [r for r in all_rows if r["group"] in {"template", "roleplay"}
                    and r["language"] == "zh" and any(p["source_id"] == "local" for p in r["provenance"])]
        self.assertEqual(multi["results"], expected)
        intersection = generate("TEST_OK", groups=["template"], categories=["classical_chinese"])
        self.assertEqual(intersection["count"], 4)
        empty = generate("TEST_OK", groups=["roleplay"], categories=["classical_chinese"])
        self.assertEqual(empty["count"], 0)
        self.assertEqual(empty["group_counts"], dict.fromkeys(GROUP_IDS, 0))
        with self.assertRaises(ValueError):
            generate("TEST_OK", groups=["unknown"])

    def test_overlap_rules_and_representative_records(self):
        rows = {r["id"]: r for r in self.catalog["templates"]}
        for identifier, expected in (("local-classical_chinese-dialogue", "template"),
                                     ("local-roleplay-zh", "roleplay"),
                                     ("local-direct_override-zh", "prefix_suffix"),
                                     ("tpl-a34ee7f069c4e865", "prefix_suffix")):
            self.assertEqual(rows[identifier]["group"], expected)
        self.assertEqual(classify_group({"categories": ["reverse_payload", "refusal_suppression"]})[0], "template")
        self.assertEqual(classify_group({"categories": ["roleplay", "refusal_suppression"]})[0], "roleplay")
        self.assertEqual(classify_group({"text": "You are a helpful assistant. TEST_OK"})[0], "template")
        self.assertEqual(classify_group({"text": "You are a character called Example. TEST_OK"})[0], "roleplay")

    def test_all_exports_keep_group_separate_from_payload(self):
        result = generate("TEST_OK", groups=["prefix_suffix"], categories=["direct_override"], sources=["local"])
        self.assertEqual(json.loads(serialize(result, "payloads")), [r["payload"] for r in result["results"]])
        for line in serialize(result, "jsonl").splitlines():
            self.assertEqual(json.loads(line)["group"], "prefix_suffix")
        self.assertIn(GROUP_NAMES["prefix_suffix"], serialize(result, "txt"))
        with tempfile.TemporaryDirectory() as directory:
            target = write_payload_files(result, Path(directory) / "payloads")
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["group_counts"], result["group_counts"])
            for item, row in zip(manifest["items"], result["results"]):
                self.assertEqual(item["group"], row["group"])
                self.assertEqual((target / item["file"]).read_bytes(), row["payload"].encode("utf-8"))

    def test_cli_frontend_index_generation_and_fixed_example_filter(self):
        def cli(*args):
            p = subprocess.run([sys.executable, str(ROOT / "app.py"), *args], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            return p.stdout.decode("utf-8")
        self.assertEqual(json.loads(cli("groups", "--format", "json")), self.index)
        generated = json.loads(cli("generate", "--goal", "TEST_OK", "--group", "roleplay", "--source", "local"))
        self.assertTrue(generated["count"])
        self.assertTrue(all(r["group"] == "roleplay" for r in generated["results"]))
        sample = json.loads(cli("examples", "--source", "ccbos", "--group", "template", "--limit", "1"))
        self.assertEqual(sample["group"], "template")
        papers = cli("research", "--group", "roleplay")
        self.assertIn("DeepInception", papers)
        self.assertNotIn("AutoDAN", papers)
        invalid = subprocess.run([sys.executable, str(ROOT / "app.py"), "generate", "--goal", "TEST_OK", "--group", "invalid"], capture_output=True)
        self.assertEqual(invalid.returncode, 2)

    def test_rebuild_rules_reproduce_committed_data(self):
        catalog, examples, methods, research = copy.deepcopy((self.catalog, self.examples, self.methods, self.research))
        rebuilt = organize(catalog, examples, methods, research)
        self.assertEqual(rebuilt, self.index)
        self.assertEqual(catalog, self.catalog)
        self.assertEqual(examples, self.examples)
        self.assertEqual(methods, self.methods)
        self.assertEqual(research, self.research)

    def test_source_associations_cover_imports_without_double_counting(self):
        for source in self.catalog["sources"]:
            self.assertTrue(source["groups"])
            self.assertTrue(set(source["groups"]) <= set(GROUP_IDS))
            self.assertEqual(sum(source["templates_by_group"].values()), source["template_count"])
            self.assertEqual(sum(source["examples_by_group"].values()), source["example_count"])
        document = (ROOT / "docs/SOURCES.md").read_text(encoding="utf-8")
        for number, gid in enumerate(GROUP_IDS, 1):
            self.assertIn(f"## {number}. {GROUP_NAMES[gid]}（`{gid}`）", document)


if __name__ == "__main__":
    unittest.main()
