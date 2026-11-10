"""PAIR-style independent iterative refinement, using a shared API protocol."""


def run(context, roots):
    seeds = sorted(roots, key=lambda row: row["score"], reverse=True)
    states = [seeds[i % len(seeds)] for i in range(context.streams)]
    for round_number in range(1, context.rounds + 1):
        next_states = []
        for stream, parent in enumerate(states, 1):
            node = context.propose(parent, round_number, f"refine_using_feedback_stream_{stream}")
            if node is None:
                next_states.append(parent)
                continue
            context.evaluate(node)
            next_states.append(node)
            if context.success:
                return "success"
        states = next_states
    return "round_limit"
