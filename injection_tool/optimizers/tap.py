"""TAP-style branching, on-topic pruning, and score-based beam selection."""


def run(context, roots):
    frontier = sorted(roots, key=lambda row: row["score"], reverse=True)[:context.width]
    for round_number in range(1, context.rounds + 1):
        children = []
        for parent in frontier:
            for branch in range(context.branching):
                node = context.propose(parent, round_number, f"explore_alternative_branch_{branch + 1}")
                if node is None or not context.on_topic(node):
                    continue
                context.evaluate(node)
                children.append(node)
                if context.success:
                    return "success"
        if not children:
            return "no_candidates"
        frontier = sorted(children, key=lambda row: row["score"], reverse=True)[:context.width]
        context.emit("selection", round=round_number, retained_ids=[row["id"] for row in frontier])
    return "round_limit"
