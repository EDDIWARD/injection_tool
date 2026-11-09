"""Build offline data using explicit, auditable adapters. Requires PyYAML only here."""
from __future__ import annotations
import ast
from collections import Counter
import csv
import hashlib
import gzip
import json
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from injection_tool.core import validate_template
from injection_tool.quality import prepare_catalog
from expanded_adapters import import_expansion

UP = ROOT / "data/upstream"
SOURCE_CACHE = {}
RULES = {
    "direct_override": r"ignore.{0,60}(previous|prior|above|instruction)|disregard.{0,40}instruction",
    "authority_spoof": r"administrator|system administrator|authorized by|developer mode|root access",
    "role_spoof": r"\[system\]|<\|im_start\|>system|system.message|\[inst\]",
    "conversation_spoof": r"user:.*|human:.*|assistant:",
    "task_dependency": r"before you|first.{0,40}(must|need)|prerequisite",
    "urgency": r"urgent|emergency|immediately|time.sensitive",
    "evaluation_pressure": r"benchmark|evaluation|points|reward|score|tokens left",
    "answer_contamination": r"final answer|incorrect answer|wrong answer",
    "output_format": r"json|output format|response format|format your",
    "encoded_base64": r"base64|base-64",
    "encoded_rot13": r"rot13|rot-13",
    "unicode_escape": r"unicode|\\u[0-9a-f]{4}",
    "split_payload": r"concatenate|split.{0,30}(word|part|piece)|reconstruct",
    "reverse_payload": r"reverse.{0,25}(text|character|string|order)",
    "few_shot": r"example 1|example #1|few.shot|example input",
    "roleplay": r"role.?play|pretend|act as|you are now|in character|扮演|模仿|角色",
    "simulation": r"hypothetical|fictional|simulation|imaginary|story|novel",
    "translation_laundering": r"translat(e|or|ion)",
    "refusal_suppression": r"do not.{0,40}(refuse|apolog|sorry)|never.{0,25}(refuse|sorry)|without.{0,20}(warning|disclaimer)",
    "dual_response": r"two responses|two answers|unaligned:|antigpt|normal.*unfiltered",
    "policy_forgery": r"policy update|new policy|policies have|rules.{0,20}(replaced|updated)",
    "tool_guidance": r"tool call|tool usage|function call",
    "memory_poison": r"remember.{0,25}(future|always)|memory|preference record",
    "reasoning_redirection": r"step.by.step|think step|reasoning|chain.of.thought",
    "code_completion": r"complete.{0,30}code|finish.{0,30}(class|code)|补全.{0,10}代码|ProblemSolver|Solver class",
    "semantic_obfuscation": r"semantic ambiguity|semantic manipulation|语义混淆|语义歧义",
    "poetry": r"\bpoem\b|\bpoetry\b|诗歌|诗赋|藏头诗",
    "historical_framing": r"historical (context|analysis)|historian|ancient manuscript|古籍|史官|史家",
}

def classify(text):
    hits = [name for name, pattern in RULES.items() if re.search(pattern, text, re.I)]
    return hits or ["unclassified"]

def read(sid, path):
    source = SOURCE_CACHE.get(sid)
    if source is None:
        source = json.loads((ROOT / "data/source_metadata" / f"{sid}.json").read_text(encoding="utf-8"))
        SOURCE_CACHE[sid] = source
    artifact = next((a for a in source["artifacts"] if a["path"] == path), None)
    if artifact is None:
        raise ValueError(f"Missing verified artifact: {sid}/{path}. Run fetch_artifacts.py first.")
    content = (UP / sid / path).read_bytes()
    expected_url = f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/{path}"
    if artifact["url"] != expected_url or hashlib.sha256(content).hexdigest() != artifact["sha256"]:
        raise ValueError(f"Artifact revision or hash mismatch: {sid}/{path}")
    return content.decode("utf-8-sig")

def main():
    sources = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data/source_metadata").glob("*.json"))}
    curated = json.loads((ROOT / "data/curated.json").read_text(encoding="utf-8"))
    templates, examples, skipped = {}, {}, []

    def provenance(sid, path, locator, method, **extra):
        s = sources[sid]
        return {"source_id": sid, "path": path, "locator": locator, "commit": s["commit"],
                "url": f"{s['url']}/blob/{s['commit']}/{path}", "method": method, **extra}

    def add_template(text, name, prov, scope="jailbreak", categories=None, language="und", **extra):
        try:
            validate_template(text)
            # Do not silently ship Jinja expressions or forgotten upstream parameters.
            residue = re.sub(r"\{\{\s*[a-zA-Z_][a-zA-Z_0-9]*\s*\}\}", "", text)
            if "{{" in residue:
                raise ValueError("Unsupported or unresolved template syntax")
        except ValueError as exc:
            skipped.append({"provenance": prov, "reason": str(exc)})
            return
        digest = hashlib.sha256(text.replace("\r\n", "\n").strip().encode()).hexdigest()
        if digest in templates:
            templates[digest]["provenance"].append(prov)
            return
        templates[digest] = {"id": "tpl-" + digest[:16], "name": name, "template": text,
                             "categories": categories or classify(text), "scope": scope, "language": language,
                             "classification_method": "adapter" if categories else "keyword_heuristic",
                             "provenance": [prov], **extra}

    def add_example(text, sid, path, locator, original_category=None, kind="fixed_attack", **extra):
        if not isinstance(text, str) or not text.strip():
            return
        digest = hashlib.sha256(text.replace("\r\n", "\n").strip().encode()).hexdigest()
        prov = provenance(sid, path, locator, "original_example", original_category=original_category)
        if digest in examples:
            examples[digest]["provenance"].append(prov)
            return
        examples[digest] = {"id": "ex-" + digest[:16], "text": text, "kind": kind,
                            "categories": classify(text), "classification_method": "keyword_heuristic",
                            "provenance": [prov], **extra}

    for t in curated["templates"]:
        key = hashlib.sha256(t["template"].strip().encode()).hexdigest()
        templates[key] = t

    path = "datasets/prompts/GPTFuzzer.csv"
    for i, row in enumerate(csv.DictReader(read("gptfuzz", path).splitlines(keepends=True)), 1):
        original = row["text"]
        prov = provenance("gptfuzz", path, f"row:{i};id:{row['id']}", "placeholder_normalized",
                          replacement={"[INSERT PROMPT HERE]": "{{goal}}"})
        add_template(original.replace("[INSERT PROMPT HERE]", "{{goal}}"), f"GPTFuzzer {row['id']}", prov, language="en")

    pyrit_paths = sorted(a["path"] for a in sources["pyrit"]["artifacts"] if a["path"].startswith("pyrit/datasets/jailbreak/templates/") and a["path"].endswith(".yaml"))
    if not pyrit_paths:
        raise ValueError("No verified PyRIT template artifacts; fetch a complete snapshot before rebuilding")
    for path in pyrit_paths:
        file = Path(path)
        row = yaml.safe_load(read("pyrit", path))
        prov = provenance("pyrit", path, "value", "placeholder_normalized", upstream_source=row.get("source"),
                          upstream_authors=row.get("authors"), replacement={"{{ prompt }}": "{{goal}}"})
        if row.get("parameters") != ["prompt"] or not isinstance(row.get("value"), str):
            skipped.append({"provenance": prov, "reason": "Requires additional parameters or is not a text template"})
            continue
        # PyRIT uses raw blocks to quote literal prose. Removing these delimiters
        # is a fixed textual transformation, not execution of arbitrary Jinja.
        text = row["value"].replace("{% raw %}", "").replace("{% endraw %}", "")
        prov["raw_block_delimiters_removed"] = text != row["value"]
        text = re.sub(r"\{\{\s*prompt\s*\}\}", "{{goal}}", text)
        add_template(text, str(row.get("name") or file.stem), prov)

    path = "src/agentdojo/attacks/baseline_attacks.py"
    tree = ast.parse(read("agentdojo", path))
    # Parse string constants only; no upstream imports or code execution.
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for call in ast.walk(cls):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "__init__" and call.args:
                arg = call.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "{goal}" in arg.value:
                    add_template(arg.value.replace("{goal}", "{{goal}}"), cls.name,
                                 provenance("agentdojo", path, f"line:{arg.lineno}", "placeholder_normalized"), "injection", language="en")
    path = "src/agentdojo/attacks/important_instructions_attacks.py"
    tree = ast.parse(read("agentdojo", path))
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "ImportantInstructionsAttack":
            for assign in cls.body:
                if isinstance(assign, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_JB_STRING" for t in assign.targets):
                    text = ast.literal_eval(assign.value).replace("{goal}", "{{goal}}").replace("{user}", "the user").replace("{model}", "assistant")
                    add_template(text, "AgentDojo important instructions (generic names)", provenance("agentdojo", path,
                        f"line:{assign.lineno}", "adapted", adaptation="User/model names replaced with generic labels; goal placeholder normalized"),
                        "injection", ["authority_spoof", "task_dependency"], language="en")

    for mode in ("base", "enhanced"):
        for attack in ("dh", "ds"):
            path = f"data/test_cases_{attack}_{mode}.json"
            for i, row in enumerate(json.loads(read("injecagent", path))):
                add_example(row["Tool Response"], "injecagent", path, f"index:{i}", row.get("Attack Type"),
                            original_goal=row.get("Attacker Instruction"), scenario=row.get("User Instruction"))
                if mode != "base":
                    continue
                raw = row.get("Tool Response Template", "")
                if "<Attacker Instruction>" not in raw:
                    continue
                # These are original tool-response carrier templates, not invented attack wrappers.
                text = raw.replace("<Attacker Instruction>", "{{goal}}")
                add_template(text, "InjecAgent tool response: " + row.get("User Tool", "unknown"),
                    provenance("injecagent", path, f"index:{i};Tool Response Template", "placeholder_normalized",
                               notes="Textual tool response; original scenario values are retained. Not guaranteed to be valid JSON."),
                    "injection", ["tool_guidance"], language="en", template_kind="tool_response_carrier")

    for split in ("train", "test"):
        for kind in ("text", "code"):
            path = f"benchmark/{kind}_attack_{split}.json"
            for label, entries in json.loads(read("bipia", path)).items():
                for i, text in enumerate(entries):
                    add_example(text, "bipia", path, f"{label}[{i}]", label, kind="benchmark_injection_content")

    path = "src/redteam/strategies/promptInjections/data.ts"
    literal = read("promptfoo", path).strip().removeprefix("export default ").removesuffix(";")
    # This pinned file contains only an array of string literals, valid in both
    # TypeScript and Python. literal_eval rejects calls or executable expressions.
    for i, original in enumerate(ast.literal_eval(literal)):
        original = original.encode("utf-16", "surrogatepass").decode("utf-16")
        if "__PROMPT__" in original:
            add_template(original.replace("__PROMPT__", "{{goal}}"), f"promptfoo prompt injection {i}",
                provenance("promptfoo", path, f"index:{i}", "placeholder_normalized", replacement={"__PROMPT__": "{{goal}}"}))
        else:
            add_example(original, "promptfoo", path, f"index:{i}", kind="fixed_or_manual_edit_example")

    path = "webarena_prompt_injections/constants.py"
    tree = ast.parse(read("wasp", path))
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "PromptInjectionFormat":
            for assign in cls.body:
                if isinstance(assign, ast.Assign) and isinstance(assign.value, ast.Dict):
                    for value in assign.value.values:
                        text = ast.literal_eval(value)
                        if "[this link]" in text:
                            skipped.append({"provenance": provenance("wasp", path, f"line:{value.lineno}", "not_imported"),
                                            "reason": "URL injection requires a real scenario URL and user task; not a single-goal template"})
                            continue
                        text = text.replace("{user_goal_str}", "complete the original task").replace("{instantiated_url_of_action}", "the current page").replace("{instantiated_instruction_text}", "{{goal}}")
                        add_template(text, "WASP plain text (generic scenario)", provenance("wasp", path, f"line:{value.lineno}", "adapted",
                            adaptation="User task generalized; action URL replaced by 'the current page'; objective placeholder normalized"),
                            "injection", ["task_dependency", "urgency"], language="en")

    for benchmark in ("extraction", "hijacking"):
        path = f"benchmarks/{benchmark}-robustness/v1/{benchmark}_robustness_dataset.jsonl"
        for i, line in enumerate(read("tensortrust", path).splitlines(), 1):
            row = json.loads(line)
            add_example(row["attack"], "tensortrust", path, f"line:{i};sample_id:{row.get('sample_id')}", benchmark)

    path = "data/all_attack_tools.jsonl"
    for i, line in enumerate(read("asb", path).splitlines(), 1):
        row = json.loads(line)
        add_example(row["Attacker Instruction"], "asb", path, f"line:{i}", row.get("Attack Type"), kind="attack_objective",
                    original_tool=row.get("Attacker Tool"))

    path = "CybersecurityBenchmarks/datasets/prompt_injection/prompt_injection.json"
    for i, row in enumerate(json.loads(read("purplellama", path))):
        add_example(row["user_input"], "purplellama", path, f"index:{i}", row.get("injection_type"),
                    upstream_tags={k: row.get(k) for k in ("injection_variant", "risk_category", "speaking_language")})

    for sid, path in [("promptinject", "promptinject/prompt_data.py"), ("garak", "garak/resources/promptinject/prompt_data.py")]:
        tree = ast.parse(read(sid, path))
        for assign in tree.body:
            if not isinstance(assign, ast.Assign):
                continue
            for target in assign.targets:
                if isinstance(target, ast.Name) and target.id in {"goal_hikacking_attacks", "goal_hijacking_attacks", "prompt_leaking_attacks"}:
                    try:
                        data = ast.literal_eval(assign.value)
                    except (ValueError, TypeError):
                        continue
                    for key, row in data.items():
                        add_example(row["instruction"], sid, path, target.id + "." + key, target.id, kind="fixed_or_output_string_template")

    methods = import_expansion(sources, read, provenance, add_template, add_example, skipped)
    (ROOT / "data/methods.json").write_text(json.dumps(methods, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = Counter(p["source_id"] for t in templates.values() for p in {p['source_id']: p for p in t['provenance']}.values())
    ecounts = Counter(p["source_id"] for t in examples.values() for p in {p['source_id']: p for p in t['provenance']}.values())
    summaries = []
    for sid, source in sources.items():
        lic = "\n".join(read(sid, p) for p in source.get("license_files", []))
        license_name = "MIT" if "MIT License" in lic or "Permission is hereby granted, free of charge" in lic else "Apache-2.0" if "Apache License" in lic else "see upstream terms" if lic else "not found in fetched root files"
        if sid == "purplellama":
            license_name = "MIT (CybersecurityBenchmarks component); repository root has different terms"
        if sid == "wasp":
            license_name = "CC-BY-NC-4.0 (WASP); incorporated components have separate terms"
        summaries.append({k: source[k] for k in ("id", "repository", "url", "kind", "status", "commit", "retrieved_at", "stars", "stars_checked_at") if k in source} |
                         {"license": license_name, "license_files": source.get("license_files", []),
                          "artifact_count": len(source["artifacts"]), "template_count": counts[sid], "example_count": ecounts[sid],
                          "notes": "Repository-level license is not a determination of every third-party data item's license."})
    summaries.append({"id": "local", "url": "data/curated.json", "kind": "locally_authored", "status": "local",
                      "license": "project-authored", "template_count": counts["local"], "example_count": 0})
    cat = {"schema_version": 1, "categories": curated["categories"], "sources": summaries,
           "templates": sorted(templates.values(), key=lambda t: (t['categories'][0], t['id'])),
           "stats": {"verified_repositories": sum(s['status'].startswith('verified') for s in summaries),
                     "unavailable_repositories": sum(s['status'] == 'unavailable' for s in summaries),
                     "templates": len(templates), "examples": len(examples), "categories": len(curated["categories"]),
                     "research_papers": len(json.loads((ROOT / "data/research.json").read_text(encoding="utf-8"))["papers"]),
                     "method_references": len(methods),
                     "templates_by_scope": dict(Counter(t['scope'] for t in templates.values())),
                     "templates_by_origin": dict(counts), "examples_by_origin": dict(ecounts), "skipped_templates": len(skipped)}}
    (ROOT / "data/catalog_raw.json").write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")
    reviews = json.loads((ROOT / "data/template_reviews.json").read_text(encoding="utf-8"))
    cat, held, quality_report = prepare_catalog(cat, reviews, classify)
    (ROOT / "data/catalog.json").write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data/templates_held.json").write_text(json.dumps(held, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data/quality_report.json").write_text(json.dumps(quality_report, ensure_ascii=False, indent=2), encoding="utf-8")
    example_bytes = "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in examples.values()).encode("utf-8")
    (ROOT / "data/examples.jsonl.gz").write_bytes(gzip.compress(example_bytes, mtime=0))
    (ROOT / "data/import_report.json").write_text(json.dumps({"stats": cat["stats"], "skipped": skipped}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(cat["stats"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
