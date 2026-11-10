"""Single registry and reproducible primary grouping for code, data and docs.

These are project navigation groups, not a mutually exclusive academic taxonomy.
Keep the original multi-label categories and provenance unchanged.
"""
from collections import Counter
from . import template, prefix_suffix, roleplay

RULE_VERSION = 1
MODULES = (template, prefix_suffix, roleplay)
GROUPS = tuple(module.DEFINITION for module in MODULES)
GROUP_IDS = tuple(group["id"] for group in GROUPS)
GROUP_NAMES = {group["id"]: group["name"] for group in GROUPS}


def source_ids(row):
    provenance = row.get("provenance", [])
    if isinstance(provenance, dict):
        provenance = [provenance]
    return {p["source_id"] for p in provenance} | ({row["source_id"]} if row.get("source_id") else set())


def classify_group(row):
    """Return one primary group and an auditable rule; never alter content."""
    sources = source_ids(row)
    tags = set(row.get("categories", []))
    text = "\n".join(str(row.get(key, "")) for key in ("name", "template", "text"))
    reason = prefix_suffix.optimization_match(sources)
    if reason:
        return "prefix_suffix", reason
    reason = template.match(tags, sources)
    if reason:
        return "template", reason
    reason = roleplay.match(tags, sources, text)
    if reason:
        return "roleplay", reason
    reason = prefix_suffix.match(tags, row.get("name", ""))
    if reason:
        return "prefix_suffix", reason
    return "template", "template_fallback"


def annotate(row):
    row["group"], reason = classify_group(row)
    row["group_assignment"] = {"version": RULE_VERSION, "rule": reason}


def group_counts(rows):
    counts = Counter(row["group"] for row in rows)
    return {gid: counts[gid] for gid in GROUP_IDS}


def organize(catalog, examples, methods, research):
    """Annotate collections in place and return the small frontend index."""
    collections = {"template": catalog["templates"], "example": examples,
                   "method": methods, "paper": research["papers"]}
    for rows in collections.values():
        for row in rows:
            annotate(row)
    definitions = []
    for definition in GROUPS:
        gid = definition["id"]
        definitions.append({**definition, **{
            kind + "_count": sum(row["group"] == gid for row in rows)
            for kind, rows in collections.items()
        }})
    # A repository can contain several mechanisms. Count each item once per source.
    source_counts = {}
    for kind, rows in collections.items():
        counts = Counter((sid, row["group"]) for row in rows for sid in source_ids(row))
        source_counts[kind] = counts
    for source in catalog["sources"]:
        sid = source["id"]
        associated = set()
        for kind, counts in source_counts.items():
            source[kind + "s_by_group"] = {gid: counts[sid, gid] for gid in GROUP_IDS}
            associated.update(gid for gid in GROUP_IDS if counts[sid, gid])
        associated.update(module.DEFINITION["id"] for module in MODULES if sid in module.REFERENCE_SOURCES)
        source["groups"] = [gid for gid in GROUP_IDS if gid in associated]
        if not source["groups"]:
            source["groups"] = ["template"]
    catalog["schema_version"] = 3
    catalog["groups"] = definitions
    catalog["group_rule_version"] = RULE_VERSION
    catalog["stats"]["groups"] = len(GROUPS)
    for kind, rows in collections.items():
        catalog["stats"][kind + "s_by_group"] = group_counts(rows)
    return {"schema_version": 1, "group_rule_version": RULE_VERSION, "groups": definitions}
