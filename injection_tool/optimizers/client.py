"""Small synchronous client for the chat/completions JSON protocol."""
import json
import http.client
import math
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROLES = ("attacker", "target", "judge")


class APIError(RuntimeError):
    pass


def load_config(path):
    return validate_config(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def validate_config(config):
    if not isinstance(config, dict) or set(config) != set(ROLES):
        raise ValueError("API 配置必须包含 attacker、target、judge 三个角色")
    result = {}
    for role in ROLES:
        item = config[role]
        if not isinstance(item, dict):
            raise ValueError(f"{role} 配置必须是对象")
        allowed = {"base_url", "model", "api_key_env", "timeout", "max_tokens", "temperature", "system_prompt"}
        if set(item) - allowed:
            raise ValueError(f"{role} 存在未知配置字段；密钥请通过 api_key_env 引用环境变量")
        base = item.get("base_url", "")
        if not isinstance(base, str):
            raise ValueError(f"{role}.base_url 必须是文本")
        url = urllib.parse.urlsplit(base)
        try:
            port = url.port
        except ValueError:
            raise ValueError(f"{role}.base_url 端口无效") from None
        if port is not None and not 1 <= port <= 65535:
            raise ValueError(f"{role}.base_url 端口无效")
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError(f"{role}.base_url 必须是无账号、查询参数的 HTTP(S) 地址")
        if not isinstance(item.get("model"), str) or not item["model"].strip():
            raise ValueError(f"{role}.model 不能为空")
        env = item.get("api_key_env")
        if env is not None and (not isinstance(env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env)):
            raise ValueError(f"{role}.api_key_env 必须是环境变量名或 null")
        if not isinstance(item.get("system_prompt", ""), str):
            raise ValueError(f"{role}.system_prompt 必须是文本")
        if role != "target" and item.get("system_prompt"):
            raise ValueError("system_prompt 只用于 target；生成和评判提示由适配器提供")
        settings = {"timeout": item.get("timeout", 60), "max_tokens": item.get("max_tokens", 1024),
                    "temperature": item.get("temperature", 0.0)}
        for key, value in settings.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{role}.{key} 必须是有限数值")
        if not 0 < settings["timeout"] <= 600 or not 0 <= settings["temperature"] <= 2:
            raise ValueError(f"{role} 的超时或温度不在允许范围内")
        if not isinstance(settings["max_tokens"], int) or not 1 <= settings["max_tokens"] <= 32768:
            raise ValueError(f"{role}.max_tokens 必须是 1–32768 的整数")
        result[role] = {**item, **settings, "base_url": base.rstrip("/"), "api_key_env": env}
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an API key through a redirect to an unexpected endpoint.
        return None


class ChatClient:
    def __init__(self, config):
        self.config = validate_config(config)
        self.opener = urllib.request.build_opener(NoRedirect())

    def preflight(self):
        for role, item in self.config.items():
            env = item["api_key_env"]
            if env and not os.environ.get(env):
                raise ValueError(f"{role} 缺少环境变量 {env}")

    def complete(self, role, messages):
        item = self.config[role]
        headers = {"Content-Type": "application/json", "User-Agent": "injection-tool-api-adapter/1"}
        env = item["api_key_env"]
        if env:
            key = os.environ.get(env)
            if not key:
                raise APIError(f"{role} 的密钥环境变量未设置")
            headers["Authorization"] = "Bearer " + key
        body = {"model": item["model"], "messages": messages, "stream": False,
                "max_tokens": item["max_tokens"], "temperature": item["temperature"]}
        request = urllib.request.Request(item["base_url"] + "/chat/completions",
                                         data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers)
        try:
            with self.opener.open(request, timeout=item["timeout"]) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise APIError(f"{role} 响应超过大小限制")
            data = json.loads(raw)
            message = data["choices"][0]["message"]
            content = message.get("content")
            if isinstance(content, list):
                content = "".join(part.get("text", "") for part in content if part.get("type") == "text")
            if content is None and isinstance(message.get("refusal"), str):
                content = message["refusal"]
            if not isinstance(content, str) or not content.strip():
                raise APIError(f"{role} 未返回可用文本")
            return content
        except urllib.error.HTTPError as exc:
            # Response bodies may echo credentials or private request content.
            status = exc.code
            exc.close()
            raise APIError(f"{role} API 返回 HTTP {status}，请检查服务地址、权限或限额") from None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            raise APIError(f"{role} API 连接失败或超时") from None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise APIError(f"{role} API 响应不符合 chat/completions 格式") from None


def parse_object(text):
    value = text.strip()
    if value.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", value, re.S | re.I)
        if match:
            value = match.group(1)
    try:
        result = json.loads(value)
    except (TypeError, ValueError):
        raise APIError("模型没有返回要求的 JSON 对象；本次记录保留，不自动重试") from None
    if not isinstance(result, dict):
        raise APIError("模型返回的 JSON 必须是对象")
    return result
