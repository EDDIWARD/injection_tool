"""Refresh the three groups from committed data, without upstream downloads."""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from injection_tool.groups import organize


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    data = ROOT / "data"
    catalog = json.loads((data / "catalog.json").read_text(encoding="utf-8"))
    methods = json.loads((data / "methods.json").read_text(encoding="utf-8"))
    research = json.loads((data / "research.json").read_text(encoding="utf-8"))
    with gzip.open(data / "examples.jsonl.gz", "rt", encoding="utf-8") as stream:
        examples = [json.loads(line) for line in stream]
    index = organize(catalog, examples, methods, research)
    for name, value in (("catalog", catalog), ("methods", methods), ("research", research), ("groups", index)):
        write_json(data / (name + ".json"), value)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in examples)
    (data / "examples.jsonl.gz").write_bytes(gzip.compress(content.encode("utf-8"), mtime=0))
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
