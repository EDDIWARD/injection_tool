"""Text-only preparation and conservative readiness checks for imported templates.

This module never executes templates. Review decisions refer to content-addressed
raw IDs; ambiguous samples are retained separately rather than silently repaired.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import re

QUALITY_VERSION = 1

def text_hash(text):
    return hashlib.sha256(text.replace("\r\n", "\n").strip().encode("utf-8")).hexdigest()

def flat_layout(text):
    """Remove ornamental Unicode frames, preserving ordinary text and delimiters."""
    lines = []
    for line in text.replace("\r\n", "\n").splitlines():
        if re.fullmatch(r"[\s\u2500-\u257f∞▓▒░█]+", line) and line.strip():
            continue
        line = re.sub(r"^\s*[║│]\s?", "", line)
        line = re.sub(r"\s*[║│]\s*$", "", line)
        if re.match(r"^\s*[∞▓▒░█]", line) and re.search(r"[∞▓▒░█]\s*$", line):
            line = re.sub(r"^\s*[∞▓▒░█]+\s*|\s*[∞▓▒░█]+\s*$", "", line)
        lines.append(line.rstrip())
    return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", "\n".join(lines)).strip()

def clean_editorial(text):
    actions = []
    removed = []
    original = text
    # Explicit publishing preamble, not a fictional persona's self-description.
    if "Prompt is everything below." in text:
        preface, text = text.split("Prompt is everything below.", 1)
        removed.append(preface + "Prompt is everything below.")
        actions.append("removed_publishing_preface")
    rules = [
        (r"//brought to you by[^\n]*?(?=\s*//|\s*IF INPUT|\s*\{\{goal\}\}|$)", "removed_author_credit"),
        (r"//V\d+(?:\.\d+)*\s*(?:beta)?", "removed_version_comment"),
        (r"IF INPUT=\(CREDITS\)=\[[^\]]*\]", "removed_credit_command"),
        (r"(?m)^\s*TIP: to use this prompt[^\n]*\n?", "removed_usage_tip"),
        (r"(?m)^\s*DATE:\s*\[CURRENT_DATE\]\s*$", "removed_unfilled_date_header"),
        (r"(?im)^\s*[^\n:]{0,40}Date:\s*\[CURRENT[ _]DATE(?:\s*[-+]\s*\d+\s*days)?\]\s*$", "removed_unfilled_date_header"),
    ]
    for pattern, label in rules:
        matches = re.findall(pattern, text, re.I)
        if matches:
            removed.extend(matches)
            text = re.sub(pattern, "", text, flags=re.I)
            actions.append(label)
    text = text.replace("[CURRENT_SESSION]", "this session").replace("[UNTITLED]", "Working title")
    if text != original and not actions:
        actions.append("resolved_cosmetic_labels")
    flat = flat_layout(text)
    if flat != text.strip():
        actions.append("flattened_decorative_layout")
    return flat, actions, removed

READINESS_RULES = {
    "requires_followup": r"(?i)wait(?:ing)? for (?:my|your|the (?:user|player)'s)|after my next|following the next message|after (?:you|I) (?:have )?(?:confirm|reply)|do not (?:begin|start).{0,90}(?:next|until)|before (?:we|you) (?:begin|start).{0,60}(?:confirm|ready)|ask one question at a time|character creation|await \[INPUT\]",
    "confirmation_only": r"(?i)confirm.{0,75}(?:by (?:stating|saying|replying)|with the phrase)|respond (?:to (?:this|my) (?:message|prompt) )?(?:only )?with.{0,70}(?:understood|enabled|activated|understand|ready)|(?:if|when) you understand.{0,60}(?:say|reply|respond|write).{0,70}(?:yes|ok\b|ready|understood|activated|short message|hello|starting)|first (?:step is to )?say [\"“']Hello",
    "manual_edit_needed": r"(?i)DELETE THIS COMMENT|REPLACE(?:_|\\_|\s).{0,60}(?:YOUR|VARIABLES)|\[(?:CURRENT_DATE|CURRENT_SESSION|TOPIC)\]|\[(?:INSERT|YOUR) (?:PROMPT|QUESTION|REQUEST|TOPIC)[^\]]*\]|<INSERT[^>]*>|\{user_input\}|\[INSERT PROMPT HERE\]|__PROMPT__|\bINSERT PROMPT HERE\b",
    "editorial_residue": r"(?i)Prompt is everything below|brought to you by|IF INPUT=\(CREDITS\)|do not upload to reddit|copy paste this line|In order to use this right|TIP: to use this prompt|Made by \S+#\d+",
    "unreviewed_bundle": r"(?im)^\s*\*{0,2}(?:prompt|jailbreak)\s*#?\s*[123456789]\b",
    "setup_before_goal": r"(?i)(?:if (?:you )?underst(?:and|ood)|confirm)[^\n]{0,180}(?:\b(?:say|reply|respond|react|write)\b[^.\n]{0,35}[\"“']|introduce yourself|short answer|short message|ready (?:for user input|to receive))|(?:reply|answer|respond)[^\n]{0,30}[\"“'][^\"\n]{1,100}[\"”']\s*if you underst|\bonly say\b|\bsay understood\b|\bsay [\"“'](?:ready|understood)|need to say confirm|first response will be.{0,10}[\"“']Welcome|confirm new instructions.{0,80}greet",
    "additional_interaction": r"(?i)(?:from|after|following) my next message|wait for (?:me|an? input)|ALWAYS ask \d+.{0,35}questions|before.{0,35}ask.{0,25}questions|by typing [\"“']I confirm|reply to the next message|ready to receive my prompts",
    "unbound_goal_alias": r"(?i)\[\*?insert[-_ ]your[-_ ]prompt[-_ ]here\*?\]",
}

def readiness_issues(text):
    return [name for name, pattern in READINESS_RULES.items() if re.search(pattern, text)]

def prepare_catalog(raw_catalog, reviews, classify):
    result = deepcopy(raw_catalog)
    ready = {}
    held = []
    events = []
    seen_reviews = set()
    for original in raw_catalog["templates"]:
        review = reviews.get(original["id"])
        candidates = []
        if review:
            seen_reviews.add(original["id"])
            if review["source_sha256"] != text_hash(original["template"]):
                raise ValueError(f"Stale quality review: {original['id']}")
            if review.get("hold"):
                held.append({"template": original, "reasons": [review["hold"]], "review": "manual"})
                continue
            for index, part in enumerate(review.get("parts", []), 1):
                candidates.append((part["template"], part.get("name", original["name"]),
                                   ["reviewed_split" if len(review["parts"]) > 1 else "reviewed_cleanup"],
                                   {"part": index, "part_count": len(review["parts"]), "note": review["note"],
                                    "source_span": part.get("source_span")}))
        else:
            candidates = [(original["template"], original["name"], [], {})]

        for text, name, actions, details in candidates:
            text, clean_actions, removed = clean_editorial(text)
            actions += clean_actions
            reasons = readiness_issues(text)
            if reasons:
                held.append({"template": original, "candidate_name": name, "reasons": reasons,
                             "review": "structural_check", "prepared_text": text})
                continue
            from .core import validate_template
            validate_template(text)
            row = deepcopy(original)
            row["name"] = name
            row["template"] = text
            if text != original["template"]:
                row["id"] = "tpl-" + text_hash(text)[:16]
                # Changed wording must not retain stale heuristic labels.
                if original["classification_method"] == "keyword_heuristic":
                    row["categories"] = classify(text)
            record = {"original_id": original["id"], "source_sha256": text_hash(original["template"]),
                      "actions": actions, "removed_editorial": removed, **details}
            row["quality"] = {"version": QUALITY_VERSION, "status": "ready", "check": "static_readiness",
                              "lineage": [record]}
            digest = text_hash(text)
            if digest in ready:
                existing = ready[digest]
                existing["quality"]["lineage"].append(record)
                for p in row["provenance"]:
                    if p not in existing["provenance"]:
                        existing["provenance"].append(p)
                existing["categories"] = sorted(set(existing["categories"] + row["categories"]))
            else:
                ready[digest] = row
            if actions:
                events.append({"original_id": original["id"], "output_id": ready[digest]["id"], **record})

    unused = set(reviews) - seen_reviews
    if unused:
        raise ValueError(f"Quality reviews no longer match the import: {sorted(unused)}")
    result["schema_version"] = 2
    result["templates"] = sorted(ready.values(), key=lambda t: (t["categories"][0], t["id"]))
    counts = Counter(p for t in ready.values() for p in {p['source_id'] for p in t['provenance']})
    for s in result["sources"]:
        s["raw_template_count"] = s["template_count"]
        s["template_count"] = counts[s["id"]]
    stats = result["stats"]
    stats["raw_templates"] = len(raw_catalog["templates"])
    stats["templates"] = len(ready)
    stats["templates_by_scope"] = dict(Counter(t["scope"] for t in ready.values()))
    stats["templates_by_origin"] = dict(counts)
    stats["held_original_templates"] = len({h['template']['id'] for h in held})
    stats["cleaned_original_templates"] = len({e['original_id'] for e in events})
    stats["split_original_templates"] = sum(len(r.get('parts', [])) > 1 for r in reviews.values())
    stats["split_parts"] = sum(len(r['parts']) for r in reviews.values() if len(r.get('parts', [])) > 1)
    report = {"version": QUALITY_VERSION, "stats": stats, "changes": events,
              "held": [{k: v for k, v in h.items() if k not in {"template", "prepared_text"}} |
                       {"original_id": h["template"]["id"], "name": h["template"]["name"]} for h in held],
              "limitations": "Static readiness checks and selected manual reviews, not a guarantee of model behavior."}
    return result, held, report
