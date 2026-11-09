"""Fetch public repository metadata and selected text artifacts; never execute upstream code."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = [
    ("bipia", "microsoft/BIPIA", "indirect_benchmark"),
    ("injecagent", "uiuc-kang-lab/InjecAgent", "agent_benchmark"),
    ("agentdojo", "ethz-spylab/agentdojo", "agent_benchmark"),
    ("tensortrust", "HumanCompatibleAI/tensor-trust-data", "human_dataset"),
    ("openpromptinjection", "liu00222/Open-Prompt-Injection", "injection_framework"),
    ("llmail", "microsoft/llmail-inject-challenge", "email_benchmark"),
    ("pyrit", "microsoft/PyRIT", "redteam_framework"),
    ("garak", "NVIDIA/garak", "redteam_framework"),
    ("promptfoo", "promptfoo/promptfoo", "redteam_framework"),
    ("gptfuzz", "hubertyoo/GPTFuzz", "jailbreak_templates"),
    ("asb", "agiresearch/ASB", "agent_benchmark"),
    ("wasp", "facebookresearch/wasp", "web_agent_benchmark"),
    ("purplellama", "meta-llama/PurpleLlama", "security_benchmark"),
    ("injecguard", "InjecGuard/InjecGuard", "detector_and_dataset"),
    ("promptinject", "agencyenterprise/PromptInject", "injection_framework"),
    ("llmsecurity", "greshake/llm-security", "indirect_examples"),
    ("everywhere", "TakSec/Prompt-Injection-Everywhere", "carrier_catalog"),
    ("jailbreakchat", "verazuo/jailbreak_llms", "jailbreak_dataset"),
    ("hackaprompt", "LearnPrompting/HackAPrompt", "human_dataset"),
    ("jailbreakbench", "JailbreakBench/jailbreakbench", "jailbreak_benchmark"),
    ("llmattacks", "llm-attacks/llm-attacks", "jailbreak_method"),
    ("tap", "RICommunity/TAP", "jailbreak_method"),
    ("pair", "patrickrchao/JailbreakingLLMs", "jailbreak_method"),
    ("artprompt", "uw-nsl/ArtPrompt", "jailbreak_method"),
    ("manyshot", "anthropics/many-shot-jailbreaking", "jailbreak_method"),
    ("pint", "lakeraai/pint-benchmark", "detector_benchmark"),
    ("rebuff", "protectai/rebuff", "defense_reference"),
    ("defenses", "tldrsec/prompt-injection-defenses", "reference_catalog"),
    ("easyjailbreak", "EasyJailbreak/EasyJailbreak", "jailbreak_framework"),
    ("arth_templates", "Arth-Singh/Arth-Jailbreak-Templates", "jailbreak_templates"),
    ("dan_collection", "0xk1h0/ChatGPT_DAN", "reference_catalog"),
    ("libertas", "elder-plinius/L1B3RT4S", "jailbreak_collection"),
    ("autodan", "SheltonLiu-N/AutoDAN", "jailbreak_method"),
    ("autodan_turbo", "SaFoLab-WISC/AutoDAN-Turbo", "jailbreak_method"),
    ("flipattack", "yueliu1999/FlipAttack", "jailbreak_method"),
    ("deepinception", "tmlr-group/DeepInception", "jailbreak_method"),
    ("cipherchat", "RobustNLP/CipherChat", "jailbreak_method"),
    ("codechameleon", "huizhang-L/CodeChameleon", "jailbreak_method"),
    ("renellm", "NJUNLP/ReNeLLM", "jailbreak_method"),
    ("codeattack", "renqibing/CodeAttack", "jailbreak_method"),
    ("jailbench", "STAIR-BUPT/JailBench", "chinese_benchmark"),
    ("safety_prompts", "thu-coai/Safety-Prompts", "chinese_dataset"),
    ("pap", "CHATS-lab/persuasive_jailbreaker", "persuasion_taxonomy"),
    ("harmbench", "centerforaisafety/HarmBench", "jailbreak_benchmark"),
    ("jbb_artifacts", "JailbreakBench/artifacts", "jailbreak_dataset"),
    ("agentdyn", "SaFo-Lab/AgentDyn", "agent_benchmark"),
    ("piarena", "sleeepeer/PIArena", "injection_framework"),
    ("tasktamper", "amazon-science/task-tampering-prompt-injection", "indirect_benchmark"),
    ("deepteam", "confident-ai/deepteam", "redteam_framework"),
    ("aiinfra", "Tencent/AI-Infra-Guard", "security_framework"),
    ("llmail_analysis", "microsoft/llmail-inject-challenge-analysis", "email_benchmark"),
    ("mlcommons", "mlcommons/jailbreak-taxonomy", "research_taxonomy"),
    ("ccbos_community", "xaoLiu1222/cc-bos", "community_reimplementation"),
    ("ccbos", "xunhuang123/CC-BOS", "classical_chinese_method"),
    ("babelbench", "MARUCIE/babel-bench", "community_language_benchmark"),
]

def get(url, limit=30_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": "injection-template-catalog/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Artifact exceeds {limit} bytes: {url}")
    return data

def fetch_file(source, path):
    parts = PurePosixPath(path).parts
    if not parts or PurePosixPath(path).is_absolute() or ".." in parts or any(":" in p or "\\" in p for p in parts):
        raise ValueError("Unsafe artifact path")
    url = f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/{path}"
    dest = ROOT / "data" / "upstream" / source["id"] / path
    cached = next((a for a in source.get("artifacts", []) if a["path"] == path and a["url"] == url), None)
    if not dest.exists() or not cached or hashlib.sha256(dest.read_bytes()).hexdigest() != cached["sha256"]:
        content = get(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    content = dest.read_bytes()
    return {"path": path, "url": url, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}

def discover(entry, refresh=False):
    sid, repo, kind = entry
    cache = ROOT / "data" / "source_metadata" / f"{sid}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    record = {"id": sid, "repository": repo, "url": f"https://github.com/{repo}", "kind": kind,
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "artifacts": []}
    try:
        html = get(record["url"]).decode("utf-8")
        oid = re.search(r'"currentOid":"([0-9a-f]{40})"', html)
        stars = re.search(r'"stargazerCount":(\d+)', html)
        if stars:
            record["stars"] = int(stars.group(1))
            record["stars_checked_at"] = record["retrieved_at"]
        if oid:
            record["commit"] = oid.group(1)
        else:
            head = json.loads(get(f"https://api.github.com/repos/{repo}/commits/HEAD"))
            record["commit"] = head["sha"]
        tree = json.loads(get(f"https://api.github.com/repos/{repo}/git/trees/{record['commit']}?recursive=1"))
        record["tree_truncated"] = bool(tree.get("truncated"))
        record["files"] = [{"path": f["path"], "size": f.get("size", 0)} for f in tree["tree"] if f["type"] == "blob"]
        record["status"] = "verified"
        for file in record["files"]:
            path = file["path"]
            if "/" not in path and re.match(r"^(readme(?:\.md|\.rst)?|licen[cs]e[^/]*|notice[^/]*)$", path, re.I):
                try:
                    record["artifacts"].append(fetch_file(record, path))
                except Exception as exc:
                    record.setdefault("warnings", []).append(str(exc))
        record["license_files"] = [a["path"] for a in record["artifacts"] if re.match(r"licen[cs]e", a["path"], re.I)]
    except Exception as exc:
        record["status"] = "unavailable"
        record["error"] = str(exc)
        # Raw artifacts remain available when the unauthenticated metadata API is limited.
        try:
            html = get(record["url"]).decode("utf-8")
            match = re.search(r'"currentOid":"([0-9a-f]{40})"', html)
            if not match:
                raise ValueError("Default branch revision not found")
            record["commit"] = match.group(1)
            record["verification_method"] = "repository_page_and_raw_readme"
            record["files"] = []
            for path in ("README.md", "LICENSE", "LICENSE.md", "LICENSE.txt"):
                try:
                    record["artifacts"].append(fetch_file(record, path))
                except Exception:
                    pass
            if not record["artifacts"]:
                raise ValueError("No readable repository artifacts")
            record["status"] = "verified_readme_only"
            record["license_files"] = [a["path"] for a in record["artifacts"] if a["path"].startswith("LICENSE")]
        except Exception as fallback:
            record["fallback_error"] = str(fallback)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--source", action="append")
    args = p.parse_args()
    entries = [e for e in REPOSITORIES if not args.source or e[0] in args.source]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(discover, e, args.refresh) for e in entries]
        for f in as_completed(futures):
            s = f.result()
            print(s["id"], s["status"], len(s.get("files", [])), s.get("error", ""), flush=True)

if __name__ == "__main__":
    main()
