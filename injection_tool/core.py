from __future__ import annotations
import base64
import codecs
import csv
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from .groups import GROUPS, GROUP_IDS, GROUP_NAMES, classify_group, group_counts

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z_0-9]*)\s*\}\}")
VARIABLES = {"goal", "goal_base64", "goal_rot13", "goal_json", "goal_split", "goal_reversed", "goal_unicode",
             "goal_word_reversed", "goal_chars_in_words", "goal_code_list", "goal_code_stack"}
CARRIERS = ("plain", "email", "web", "tool", "rag", "markdown", "code", "csv")

def load_catalog(path=None):
    return json.loads(Path(path or ROOT / "data/catalog.json").read_text(encoding="utf-8"))

def validate_template(template):
    tokens = set(TOKEN.findall(template))
    if not tokens:
        raise ValueError("Template has no goal placeholder")
    if tokens - VARIABLES:
        raise ValueError(f"Unknown placeholders: {sorted(tokens - VARIABLES)}")
    if "{%" in template or "{#" in template:
        raise ValueError("Executable template syntax is not supported")

def render(template, goal):
    validate_template(template)
    transforms = {
        "goal": lambda: goal,
        "goal_base64": lambda: base64.b64encode(goal.encode("utf-8")).decode("ascii"),
        "goal_rot13": lambda: codecs.encode(goal, "rot_13"),
        "goal_json": lambda: json.dumps(goal, ensure_ascii=False),
        "goal_split": lambda: json.dumps([goal[i:i+6] for i in range(0, len(goal), 6)], ensure_ascii=False),
        "goal_reversed": lambda: goal[::-1],
        "goal_word_reversed": lambda: " ".join(goal.split()[::-1]),
        "goal_chars_in_words": lambda: " ".join(word[::-1] for word in goal.split()),
        "goal_code_list": lambda: "\n".join("    my_list.append(" + json.dumps(c, ensure_ascii=False) + ")" for c in goal),
        "goal_code_stack": lambda: "\n".join("    my_stack.append(" + json.dumps(c, ensure_ascii=False) + ")" for c in reversed(goal)),
        "goal_unicode": lambda: "".join(f"\\u{ord(c):04x}" if ord(c) <= 65535 else f"\\U{ord(c):08x}" for c in goal),
    }
    values = {name: transforms[name]() for name in set(TOKEN.findall(template))}
    # One pass: template-looking text inside user input is preserved verbatim.
    return TOKEN.sub(lambda m: values[m.group(1)], template)

def wrap(payload, carrier):
    if carrier == "plain":
        return payload
    if carrier == "email":
        return f"From: colleague@example.test\nSubject: Project update\n\nThe project notes are below.\n\n{payload}"
    if carrier == "web":
        return f"<article><h1>Project notes</h1><p>Reference material.</p>\n{payload}\n</article>"
    if carrier == "tool":
        return json.dumps({"status": "ok", "result": payload}, ensure_ascii=False)
    if carrier == "rag":
        return f"[Retrieved document: project-notes, chunk 3]\n{payload}\n[End of retrieved document]"
    if carrier == "markdown":
        return f"# Project notes\n\nReference material.\n\n<!--\n{payload}\n-->"
    if carrier == "code":
        return "\n".join("# " + line for line in payload.split("\n"))
    if carrier == "csv":
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["id", "notes"])
        writer.writerow(["sample-1", payload])
        return stream.getvalue()
    raise ValueError(f"Unknown carrier: {carrier}")

def generate(goal, *, catalog=None, groups=None, categories=None, sources=None, language="all", scope="all", carriers=None):
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("目标不能为空")
    if len(goal) > 100_000:
        raise ValueError("目标过长（最多 100,000 个字符）")
    catalog = catalog or load_catalog()
    groups = set(groups or [])
    categories = set(categories or [])
    sources = set(sources or [])
    carriers = list(dict.fromkeys(carriers or ["plain"]))
    if language not in {"all", "zh", "en", "mixed", "und"}:
        raise ValueError("未知语言")
    if scope not in {"all", "injection", "jailbreak"}:
        raise ValueError("未知范围")
    unknown_groups = groups - set(GROUP_IDS)
    if unknown_groups:
        raise ValueError(f"未知主分类: {', '.join(sorted(unknown_groups))}")
    unknown = categories - {c["id"] for c in catalog["categories"]}
    if unknown:
        raise ValueError(f"未知分类: {', '.join(sorted(unknown))}")
    unknown_sources = sources - {s["id"] for s in catalog["sources"]}
    if unknown_sources:
        raise ValueError(f"未知来源: {', '.join(sorted(unknown_sources))}")
    if set(carriers) - set(CARRIERS):
        raise ValueError("未知载体")
    results = []
    for template in catalog["templates"]:
        group = template.get("group") or classify_group(template)[0]
        if groups and group not in groups:
            continue
        if categories and not categories.intersection(template["categories"]):
            continue
        if sources and not sources.intersection(p["source_id"] for p in template["provenance"]):
            continue
        if language != "all" and template["language"] != language:
            continue
        if scope != "all" and template["scope"] != scope:
            continue
        payload = render(template["template"], goal)
        for carrier in carriers:
            results.append({"id": template["id"] + ":" + carrier, "template_id": template["id"],
                            "name": template["name"], "group": group, "categories": template["categories"],
                            "scope": template["scope"], "language": template["language"], "carrier": carrier,
                            "classification_method": template["classification_method"],
                            "quality": template.get("quality", {}),
                            "provenance": template["provenance"], "payload": wrap(payload, carrier)})
    return {"schema_version": 2, "generated_at": datetime.now(timezone.utc).isoformat(), "goal": goal,
            "groups": [dict(g) for g in GROUPS], "group_counts": group_counts(results),
            "count": len(results), "category_counts": dict(Counter(c for r in results for c in r["categories"])),
            "results": results}

def serialize(result, fmt):
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if fmt == "jsonl":
        return "".join(json.dumps({"goal": result["goal"], **r}, ensure_ascii=False) + "\n" for r in result["results"])
    if fmt == "payloads":
        return json.dumps([r["payload"] for r in result["results"]], ensure_ascii=False, indent=2) + "\n"
    if fmt == "txt":
        chunks = [f"目标：{result['goal']}\n共 {result['count']} 条\n"]
        for r in result["results"]:
            chunks.append(f"{'=' * 72}\n{r['id']} | {r['name']}\n主分类：{GROUP_NAMES[r['group']]} ({r['group']})\n标签：{', '.join(r['categories'])}\n来源：" +
                          ", ".join(p.get("url", p["source_id"]) for p in r["provenance"]) + "\n\n" + r["payload"])
        return "\n\n".join(chunks) + "\n"
    raise ValueError("Unknown output format")

def write_result(result, path, fmt):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize(result, fmt), encoding="utf-8")
    return target.resolve()

def write_payload_files(result, path):
    """One UTF-8 file per payload; annotations only in a separate manifest.

    Use a new directory and stage the export so an error cannot leave a directory
    that appears complete. Existing user output directories are never overwritten.
    """
    target = Path(path).resolve()
    if target.exists():
        raise ValueError("逐条导出目录已存在，请指定一个新目录")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.payload-export-', dir=target.parent))
    try:
        manifest = {"schema_version": 2, "goal": result["goal"], "count": result["count"],
                    "groups": result["groups"], "group_counts": result["group_counts"], "items": []}
        for index, row in enumerate(result["results"], 1):
            # Filenames do not contain text from the user's goal or the template.
            name = f"{index:04d}.txt"
            (stage / name).write_bytes(row["payload"].encode('utf-8'))
            manifest["items"].append({"file": name, **{k: v for k, v in row.items() if k != 'payload'}})
        (stage / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        stage.rename(target)
    except BaseException:
        # stage is a freshly created, resolved child of the requested parent.
        if stage.exists() and stage.parent == target.parent and stage.name.startswith('.payload-export-'):
            shutil.rmtree(stage)
        raise
    return target
