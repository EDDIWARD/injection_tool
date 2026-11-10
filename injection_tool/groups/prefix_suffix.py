"""基于前后缀优化：优化方法资料、种子与静态控制前后缀。"""
import re

DEFINITION = {
    "id": "prefix_suffix", "name": "基于前后缀优化",
    "description": "收录优化方法资料及其种子，并归入目标前后的控制性前后缀；当前仅渲染已收录文本，不运行优化搜索。",
}
OPTIMIZATION_SOURCES = {"autodan", "autodan_turbo", "llmattacks"}
CONTROL_TAGS = {"direct_override", "delimiter_escape", "fake_completion",
                "refusal_suppression", "repetition", "output_format"}
REFERENCE_SOURCES = {
    "autodan", "autodan_turbo", "llmattacks", "gptfuzz", "pair", "tap",
    "easyjailbreak", "garak", "promptfoo", "pyrit", "deepteam", "aiinfra",
    "jailbreakbench", "jbb_artifacts", "harmbench",
}
METHOD_PATTERN = re.compile(r"context_flooding|system_override|input_bypass", re.I)


def optimization_match(sources):
    return "optimization_source" if sources & OPTIMIZATION_SOURCES else None


def match(tags, name):
    if tags & CONTROL_TAGS:
        return "control_prefix_suffix_tag"
    if METHOD_PATTERN.search(name):
        return "control_method_name"
    return None
