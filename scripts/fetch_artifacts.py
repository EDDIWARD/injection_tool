"""Download an explicit selection of data/text files from the verified revisions."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from collect_sources import ROOT, fetch_file

SELECTION = {
    "bipia": [f"benchmark/{kind}_attack_{split}.json" for kind in ("text", "code") for split in ("train", "test")],
    "injecagent": [f"data/test_cases_{kind}_{mode}.json" for kind in ("dh", "ds") for mode in ("base", "enhanced")],
    "tensortrust": ["benchmarks/extraction-robustness/v1/extraction_robustness_dataset.jsonl", "benchmarks/hijacking-robustness/v1/hijacking_robustness_dataset.jsonl"],
    "gptfuzz": ["datasets/prompts/GPTFuzzer.csv", "datasets/prompts/README.md"],
    "agentdojo": ["src/agentdojo/attacks/important_instructions_attacks.py", "src/agentdojo/attacks/baseline_attacks.py"],
    "openpromptinjection": [f"OpenPromptInjection/attackers/{n}Attacker.py" for n in ("Combine", "EscapeChar", "FakeComp", "Ignore", "Naive")],
    "asb": ["data/all_attack_tools.jsonl"],
    "garak": ["garak/probes/latentinjection.py", "garak/data/sysprompt_extraction/attacks.json", "garak/resources/promptinject/prompt_data.py"],
    "promptinject": ["promptinject/prompt_data.py"],
    "purplellama": ["CybersecurityBenchmarks/datasets/prompt_injection/prompt_injection.json", "CybersecurityBenchmarks/LICENSE"],
    "wasp": ["webarena_prompt_injections/constants.py", "webarena_prompt_injections/configs/experiment_config.raw.json"],
    "promptfoo": ["src/redteam/strategies/promptInjections/data.ts", "src/redteam/strategies/promptInjections/README.md"],
    "easyjailbreak": ["easyjailbreak/seed/seed_template.json", "easyjailbreak/attacker/AutoDAN_Liu_2023.py"],
    "autodan": ["assets/autodan_initial_prompt.txt"],
    "autodan_turbo": ["logs_r/warm_up_strategy_library.json"],
    "flipattack": ["src/flip_attack.py"],
    "cipherchat": ["prompts_and_demonstrations.py"],
    "codechameleon": ["template.py"],
    "jailbench": ["JailBench-seed.csv", "JailBench.csv"],
    "safety_prompts": ["augmentation_prompts.json"],
    "pap": ["persuasion_taxonomy.jsonl"],
    "piarena": ["piarena/attacks/heuristic.py", "piarena/attacks/strategy_search/init_strategies.py"],
    "aiinfra": ["AIG-PromptSecurity/LICENSE.md", "NOTICE"],
    "ccbos": ["code/gen.py", "code/translate.py", "data/data.md"],
    "renellm": ["utils/scenario_nest_utils.py"],
    "codeattack": ["src/codeattack/data_preparation.py"],
    "libertas": ["OPENAI.mkd", "ANTHROPIC.mkd", "GOOGLE.mkd", "META.mkd", "DEEPSEEK.mkd"],
}

def main():
    records = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data/source_metadata").glob("*.json")}
    pyrit = records["pyrit"]
    SELECTION["pyrit"] = [f["path"] for f in pyrit["files"] if f["path"].startswith("pyrit/datasets/jailbreak/templates/") and f["path"].endswith(".yaml")]
    selectors = {
        "arth_templates": lambda p: p.startswith("templates/") and p.endswith(".yaml"),
        "codeattack": lambda p: p.startswith("src/codeattack/prompt_templates/") and p.endswith(".txt"),
        "deepinception": lambda p: p.startswith("res/") and p.endswith(".json"),
        "tasktamper": lambda p: p.startswith("data/test_cases/") and p.endswith(".json"),
        "deepteam": lambda p: p.startswith("deepteam/attacks/single_turn/") and p.endswith("template.py"),
        "aiinfra": lambda p: "/attacks/single_turn/" in p and p.endswith("template.py"),
        "babelbench": lambda p: p.startswith("data/prompts/") and p.endswith(".jsonl"),
        "ccbos_community": lambda p: p in ("strategy.py", "prompt_gen.py"),
        "renellm": lambda p: p in ("renellm.py", "utils.py"),
    }
    for sid, predicate in selectors.items():
        SELECTION.setdefault(sid, []).extend(f["path"] for f in records.get(sid, {}).get("files", []) if predicate(f["path"]))
    # Restore pinned artifacts, including README/license files used at build time.
    for sid, source in records.items():
        SELECTION[sid] = list(dict.fromkeys(SELECTION.get(sid, []) + [a['path'] for a in source.get('artifacts', [])]))
    tasks = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for sid, paths in SELECTION.items():
            source = records[sid]
            if not source["status"].startswith("verified"):
                continue
            for path in paths:
                tasks.append((sid, path, pool.submit(fetch_file, source, path)))
        for sid, path, future in tasks:
            try:
                artifact = future.result()
                artifacts = records[sid]["artifacts"]
                artifacts[:] = [a for a in artifacts if a["path"] != path]
                artifacts.append(artifact)
            except Exception as exc:
                records[sid].setdefault("artifact_errors", []).append({"path": path, "error": str(exc)})
                print("FAILED", sid, path, str(exc), flush=True)
    for sid in SELECTION:
        source = records[sid]
        (ROOT / "data/source_metadata" / f"{sid}.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
        print(sid, len(source["artifacts"]), "artifacts", flush=True)

if __name__ == "__main__":
    main()
