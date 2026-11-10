"""基于角色扮演：人物身份、虚构情境、模拟与多角色回答。"""
import re

DEFINITION = {
    "id": "roleplay", "name": "基于角色扮演",
    "description": "通过人物身份、虚构情境、模拟环境或多角色回答组织目标。",
}
ROLE_TAGS = {"roleplay", "simulation", "dual_response", "historical_framing"}
REFERENCE_SOURCES = {
    "dan_collection", "deepinception", "jailbreakchat", "jailbench", "libertas",
    "gptfuzz", "easyjailbreak", "pyrit", "promptfoo", "aiinfra", "arth_templates", "deepteam",
}
# Complement the older fine tags, which miss some clear persona descriptions.
# Do not treat a generic "you are" instruction as a fictional role.
PERSONA = re.compile(
    r"role[ -]?play|in (?:the )?role of|stay in character|"
    r"(?:pretend|act) (?:to be|as)\b|"
    r"you (?:are|will be) (?:now )?(?:a |an )?(?:character|fictional|evil|unrestricted)|"
    r"simulate (?:a |an )?(?:chatbot|assistant)|developer mode|开发者模式|"
    r"扮演|虚构(?:角色|人物|助手)|角色扮演",
    re.I,
)


def match(tags, sources, text):
    if sources & {"deepinception", "dan_collection", "jailbreakchat"}:
        return "roleplay_source"
    if tags & ROLE_TAGS:
        return "roleplay_tag"
    if PERSONA.search(text):
        return "persona_text"
    return None
