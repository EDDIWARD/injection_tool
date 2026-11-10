import copy
from datetime import datetime, timezone
import json
import uuid

from ..core import ROOT, generate
from . import pair, tap, gptfuzz, prompts
from .client import APIError, ChatClient, ROLES, parse_object, validate_config

METHODS = {"pair": pair, "tap": tap, "gptfuzz": gptfuzz}


def describe_methods():
    sources = json.loads((ROOT / "data/optimizer_sources.json").read_text(encoding="utf-8"))["sources"]
    return {"schema_version": 1, "methods": [
        {"id": s["id"], "source_directory": s["directory"], "upstream_entrypoint": s["entrypoint"],
         "commit": s["commit"], "repository": s["repository"],
         "api_adapter": s["id"] in METHODS, "implementation": "api-adaptation-v1" if s["id"] in METHODS else "upstream-source-only"}
        for s in sources]}


class BudgetExhausted(Exception):
    pass


class Context:
    def __init__(self, goal, method, client, config, *, rounds, max_calls, threshold, width, branching, streams, pool_size, on_event):
        self.goal, self.method, self.client, self.config = goal, method, client, config
        self.rounds, self.max_calls, self.threshold = rounds, max_calls, threshold
        self.width, self.branching, self.streams, self.pool_size = width, branching, streams, pool_size
        self.on_event = on_event
        self.history, self.seen = [], set()
        self.calls = {role: 0 for role in ROLES}
        self.success, self.best = False, None

    def emit(self, event, **fields):
        if self.on_event:
            self.on_event(copy.deepcopy({"event": event, **fields}))

    def call(self, role, messages):
        if sum(self.calls.values()) >= self.max_calls:
            raise BudgetExhausted()
        self.calls[role] += 1
        self.emit("call", role=role, calls={**self.calls, "total": sum(self.calls.values())})
        return self.client.complete(role, messages)

    def new_node(self, payload, round_number, parent_id=None, operation="seed", template_id=None):
        if payload in self.seen:
            self.emit("duplicate", round=round_number, parent_id=parent_id)
            return None
        self.seen.add(payload)
        node = {"id": f"candidate-{len(self.history) + 1:04d}", "round": round_number,
                "parent_id": parent_id, "operation": operation, "template_id": template_id,
                "payload": payload, "status": "pending", "response": None, "score": None,
                "success": False, "judge_reason": None}
        self.history.append(node)
        self.emit("candidate", candidate=node)
        return node

    def propose(self, parent, round_number, operation, other=None):
        lineage, current = [], parent
        by_id = {row["id"]: row for row in self.history}
        while current is not None and len(lineage) < 3:
            lineage.append({key: current[key] for key in ("payload", "response", "score", "judge_reason")})
            current = by_id.get(current["parent_id"])
        data = {"goal": self.goal, "method": self.method, "operation": operation,
                "recent_history": list(reversed(lineage))}
        if other is not None:
            data["second_candidate"] = other
        reply = parse_object(self.call("attacker", [{"role": "system", "content": prompts.ATTACKER},
                                                    {"role": "user", "content": json.dumps(data, ensure_ascii=False)}]))
        payload = reply.get("prompt")
        if not isinstance(payload, str) or not payload.strip() or len(payload) > 100_000:
            raise APIError("生成模型必须返回非空 prompt，长度不得超过 100,000 字符")
        node = self.new_node(payload, round_number, parent["id"], operation)
        if node:
            node["improvement"] = str(reply.get("improvement", ""))[:2000]
        return node

    def on_topic(self, node):
        data = {"goal": self.goal, "candidate": node["payload"]}
        result = parse_object(self.call("judge", [{"role": "system", "content": prompts.ON_TOPIC},
                                                 {"role": "user", "content": json.dumps(data, ensure_ascii=False)}]))
        if type(result.get("on_topic")) is not bool:
            raise APIError("相关性评判必须返回布尔值 on_topic")
        node["on_topic"] = result["on_topic"]
        if not result["on_topic"]:
            node["status"] = "pruned"
            node["prune_reason"] = str(result.get("reason", ""))[:2000]
            self.emit("pruned", candidate=node)
        return result["on_topic"]

    def evaluate(self, node):
        messages = []
        system = self.config["target"].get("system_prompt", "")
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": node["payload"]})
        node["response"] = self.call("target", messages)
        node["status"] = "unscored"
        self.emit("target_response", candidate=node)
        data = {"goal": self.goal, "candidate": node["payload"], "response": node["response"]}
        judged = parse_object(self.call("judge", [{"role": "system", "content": prompts.JUDGE},
                                                 {"role": "user", "content": json.dumps(data, ensure_ascii=False)}]))
        score = judged.get("score")
        if type(score) is not int or not 0 <= score <= 10 or type(judged.get("success")) is not bool:
            raise APIError("评判必须返回 0–10 整数 score 和布尔值 success")
        node.update(status="evaluated", score=score,
                    success=judged["success"] and score >= self.threshold,
                    judge_reason=str(judged.get("reason", ""))[:4000])
        if self.best is None or (node["success"], score) > (self.best["success"], self.best["score"]):
            self.best = node
        self.success = self.success or node["success"]
        self.emit("evaluated", candidate=node)


def optimize(goal, *, config, method="pair", seed_ids=None, rounds=5, max_calls=30,
             threshold=10, width=2, branching=2, streams=1, pool_size=8,
             on_event=None, client=None, dry_run=False):
    """Run a bounded API adaptation and return JSON-serializable evidence.

    API failures and exhausted budgets return partial history. Configuration
    errors are raised before any requests. A success is a judge decision, not ASR.
    """
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 100_000:
        raise ValueError("目标必须是 1–100,000 字符的非空文本")
    if method not in METHODS:
        raise ValueError("API 适配支持 pair、tap、gptfuzz；其他方法请使用对应上游源码")
    limits = {"rounds": (rounds, 1, 1000), "max_calls": (max_calls, 2, 100000),
              "threshold": (threshold, 1, 10), "width": (width, 1, 100),
              "branching": (branching, 1, 100), "streams": (streams, 1, 100), "pool_size": (pool_size, 1, 1000)}
    for name, (value, low, high) in limits.items():
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} 必须是 {low}–{high} 的整数")
    config = validate_config(config)
    # Resolve seeds using the same literal renderer and provenance as generate.
    if method == "gptfuzz" and not seed_ids:
        seed_ids = ["local-direct_override-en", "local-output_format-en", "local-refusal_suppression-en"]
    if seed_ids:
        rows = generate(goal)["results"]
        by_id = {row["template_id"]: row for row in rows}
        if set(seed_ids) - set(by_id):
            raise ValueError("存在未知 seed-id")
        seeds = [(by_id[identifier]["payload"], identifier) for identifier in dict.fromkeys(seed_ids)]
    else:
        seeds = [(goal, None)]
    result = {"schema_version": 1, "run_id": uuid.uuid4().hex, "method": method,
              "implementation": "api-adaptation-v1", "group": "prefix_suffix", "goal": goal,
              "started_at": datetime.now(timezone.utc).isoformat(),
              "settings": {key: value[0] for key, value in limits.items()},
              "models": {role: config[role]["model"] for role in ROLES},
              "seed_ids": list(dict.fromkeys(seed_ids or []))}
    if dry_run:
        return {**result, "status": "dry_run", "success": False, "calls": {**dict.fromkeys(ROLES, 0), "total": 0},
                "seed_count": len(seeds), "note": "仅检查配置和种子；未连接 API，未验证模型权限或效果"}
    client = client or ChatClient(config)
    if hasattr(client, "preflight"):
        client.preflight()
    context = Context(goal, method, client, config, rounds=rounds, max_calls=max_calls,
                      threshold=threshold, width=width, branching=branching, streams=streams,
                      pool_size=pool_size, on_event=on_event)
    context.emit("start", run_id=result["run_id"], method=method, settings=result["settings"])
    error = None
    try:
        roots = []
        for payload, template_id in seeds:
            node = context.new_node(payload, 0, template_id=template_id)
            if node is not None:
                context.evaluate(node)
                roots.append(node)
                if context.success:
                    break
        status = "success" if context.success else METHODS[method].run(context, roots)
    except BudgetExhausted:
        status = "budget_exhausted"
    except APIError as exc:
        status, error = "error", str(exc)
    except KeyboardInterrupt:
        status = "interrupted"
    baseline = [node for node in context.history if node["round"] == 0 and node["score"] is not None]
    baseline_score = max((node["score"] for node in baseline), default=None)
    result.update(status=status, success=context.success, error=error,
                  finished_at=datetime.now(timezone.utc).isoformat(),
                  calls={**context.calls, "total": sum(context.calls.values())},
                  baseline_score=baseline_score, best=context.best,
                  score_gain=(context.best["score"] - baseline_score) if context.best and baseline_score is not None else None,
                  history=context.history)
    context.emit("complete", status=status, success=context.success, calls=result["calls"],
                 best_id=context.best["id"] if context.best else None, error=error)
    return result
