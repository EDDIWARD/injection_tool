"""GPTFuzzer-inspired single-goal seed-pool mutation (not upstream MCTS)."""
import math

OPERATIONS = ("paraphrase", "shorten", "expand_context", "combine_two_candidates")


def run(context, roots):
    pool = sorted(roots, key=lambda row: row["score"], reverse=True)[:context.pool_size]
    visits, rewards = {}, {}
    for round_number in range(1, context.rounds + 1):
        def priority(node):
            n = visits.get(node["id"], 0)
            if not n:
                return float("inf")
            return rewards[node["id"]] / n + math.sqrt(2 * math.log(round_number + 1) / n)
        parent = max(pool, key=priority)
        visits[parent["id"]] = visits.get(parent["id"], 0) + 1
        operation = OPERATIONS[(round_number - 1) % len(OPERATIONS)]
        other = next((row["payload"] for row in pool if row["id"] != parent["id"]), None)
        node = context.propose(parent, round_number, operation, other if operation == OPERATIONS[-1] else None)
        reward = 0
        if node is not None:
            context.evaluate(node)
            reward = node["score"] / 10
            if node["score"] >= parent["score"]:
                pool.append(node)
                pool = sorted(pool, key=lambda row: row["score"], reverse=True)[:context.pool_size]
            if context.success:
                return "success"
        rewards[parent["id"]] = rewards.get(parent["id"], 0) + reward
        context.emit("selection", round=round_number, retained_ids=[row["id"] for row in pool])
    return "round_limit"
