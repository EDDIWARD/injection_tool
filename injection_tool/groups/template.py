"""基于模板：结构、语言、编码或任务包装。"""

DEFINITION = {
    "id": "template", "name": "基于模板",
    "description": "以固定结构、任务包装、编码或语言改写组织目标，包括代码、文言文和诗歌等形式。",
}
CONTENT_TAGS = {
    "encoded_base64", "encoded_rot13", "unicode_escape", "split_payload",
    "reverse_payload", "code_completion", "semantic_obfuscation",
    "classical_chinese", "poetry", "translation_laundering", "language_switch",
    "structured_spoof",
}
CONTENT_SOURCES = {"codeattack", "codechameleon", "flipattack", "ccbos", "babelbench"}
REFERENCE_SOURCES = {
    "agentdojo", "agentdyn", "aiinfra", "arth_templates", "artprompt", "asb",
    "babelbench", "bipia", "ccbos", "ccbos_community", "cipherchat", "codeattack",
    "codechameleon", "deepteam", "defenses", "easyjailbreak", "everywhere",
    "flipattack", "garak", "hackaprompt", "harmbench", "injecagent", "injecguard",
    "jailbench", "jailbreakbench", "jbb_artifacts", "libertas", "llmail",
    "llmail_analysis", "llmsecurity", "manyshot", "mlcommons", "openpromptinjection",
    "pap", "piarena", "pint", "promptfoo", "promptinject", "purplellama", "pyrit",
    "rebuff", "renellm", "safety_prompts", "tasktamper", "tensortrust", "wasp",
}


def match(tags, sources):
    if sources & CONTENT_SOURCES:
        return "source_content_form"
    if tags & CONTENT_TAGS:
        return "content_form_tag"
    return None
