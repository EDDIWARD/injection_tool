"""Generate the single source, paper and attribution document from pinned data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
    research = json.loads((ROOT / "data/research.json").read_text(encoding="utf-8"))
    methods = json.loads((ROOT / "data/methods.json").read_text(encoding="utf-8"))
    sources = [s for s in catalog["sources"] if s["id"] != "local"]
    metadata = {s["id"]: json.loads((ROOT / "data/source_metadata" / f"{s['id']}.json").read_text(encoding="utf-8")) for s in sources}
    stats = catalog["stats"]
    status = {"verified": "已核验", "verified_readme_only": "说明已核验", "unavailable": "未获取成功"}
    local_count = next(s["template_count"] for s in catalog["sources"] if s["id"] == "local")
    lines = [
        "# 三类资料、项目来源与第三方归属", "",
        f"资料核验日期：{research['checked_at']}。当前收录 {stats['verified_repositories']} 个已核验 GitHub 项目入口、{stats['templates']:,} 个默认模板、{stats['examples']:,} 条固定样例和 {stats['research_papers']} 项论文说明。", "",
        "模板数量按清理与去重后的实际内容统计；同一文本可能关联多个来源，表中来源数量相加可能高于总数。固定样例保留原始目标，单独检索，不参与新目标的模板拼装。", "",
        f"另有 {local_count} 个本地编写的模式模板，以 locally_authored 标记，包括 4 条文言文语境模板。需要模型搜索、多轮交互或额外参数的方法单独记录，不计入默认 payload。", "",
        "## 三类约定与前端字段", "",
        "这是本项目的导航分类，并非互斥的学术分类体系。每条模板、固定样例、方法和论文只有一个 `group`；原有 `categories` 保留为可重叠的细分类标签。一个项目可关联多类。", "",
        "| 主分类 | 固定标识 | 分类代码 | 模板 | 固定样例 | 方法记录 | 论文 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for group in catalog["groups"]:
        gid = group["id"]
        lines.append(f"| {group['name']} | `{gid}` | [{gid}.py](../injection_tool/groups/{gid}.py) | {group['template_count']} | {group['example_count']} | {group['method_count']} | {group['paper_count']} |")
    lines += ["",
              "归类规则按顺序执行：已指定的优化方法来源（如 AutoDAN）→ 编码、语言或结构形式 → 角色与模拟场景 → 控制性前后缀 → 其余固定模板。重叠条目取先匹配的一类，保留全部原标签；`group_assignment` 记录规则和版本，便于核对。来源关联表包含参考入口，不代表已实现这些项目的全部算法。", "",
              "- 前端读取 [data/groups.json](../data/groups.json) 的 `groups` 数组，使用 `id` 作为页签值、`name` 作为显示文字；也可运行 `python app.py groups --format json`。",
              "- 模板库为 `schema_version: 3`；每条 `templates[]` 带 `group`。生成 JSON 为 `schema_version: 2`，每条 `results[]` 带同样的 `group`；`group_counts` 是本次输出的数量，三类相加等于 `count`。",
              "- Python 接口：`generate(goal, groups=['roleplay'])`；命令行：`--group roleplay`。重复 `--group` 表示取并集，与 `--category`、来源、语言等条件组合时取交集。",
              "- JSONL 每行、逐条 TXT 的 `manifest.json` 均带 `group`；纯 TXT 文件和 `payloads.json` 仍只含文本，前端需要分类时使用完整结果或 manifest。",
              "- `methods.json` 和 `research.json` 的记录也带 `group`，仅供参考；固定样例保持原目标，不参与新目标生成。", "",
              "前端分组示例（`result` 为生成接口返回的 JSON）：", "",
              "```javascript",
              "const tabs = result.groups.map(group => ({",
              "  id: group.id,",
              "  title: group.name,",
              "  count: result.group_counts[group.id],",
              "  items: result.results.filter(item => item.group === group.id)",
              "}));",
              "```", "",
              "下表 Stars 为采集时的快照，不代表当前值或攻击效果。“版本记录”包含固定提交、下载地址、SHA-256 和来源状态。项目可在多类出现，数量仅统计该类；0 表示参考入口或该类暂无导入内容。", ""]

    for number, group in enumerate(catalog["groups"], 1):
        gid = group["id"]
        lines += [f"## {number}. {group['name']}（`{gid}`）", "", group["description"], "",
                  f"对应代码：[injection_tool/groups/{gid}.py](../injection_tool/groups/{gid}.py)。筛选：`python app.py generate --goal \"输出 TEST_OK\" --group {gid}`。", "",
                  "### 项目来源", "", "| 项目 | Stars | 本类模板 | 本类固定样例 | 核验 / 版本记录 |",
                  "| --- | ---: | ---: | ---: | --- |"]
        for s in sorted(sources, key=lambda s: (-s.get("stars", -1), s["id"])):
            if gid in s["groups"]:
                lines.append(f"| [{s['repository']}]({s['url']}) | {s.get('stars', '—')} | {s['templates_by_group'][gid]} | {s['examples_by_group'][gid]} | [{status[s['status']]}](../data/source_metadata/{s['id']}.json) |")
        lines += ["", "### 论文与实际接入范围", "", "| 论文 | 年份 / 版本 | 本地接入内容 |", "| --- | --- | --- |"]
        for paper in research["papers"]:
            if paper["group"] == gid:
                lines.append(f"| [{paper['name']}]({paper['url']}) | {paper['venue_or_version']} | {paper['integration']} |")
        lines += ["", "### 方法记录", "", "以下为方法说明，不直接参与 payload 生成；详细定义及原文件定位见 [methods.json](../data/methods.json)。", "",
                  "| 方法 | 原始记录 |", "| --- | --- |"]
        for method in methods:
            if method["group"] == gid:
                p = method["provenance"]
                lines.append(f"| {method['name']} | [{p['source_id']}]({p['url']}) |")
        lines.append("")
    lines += ["## 其他论文入口", "", "CC-BOS 的官方实现为 [xunhuang123/CC-BOS](https://github.com/xunhuang123/CC-BOS)。xaoLiu1222/cc-bos 与 MARUCIE/babel-bench 按社区项目归属；社区样例对论文来源的声明保留原文，未经逐项验证。", "",
              "### 上游说明中的其他论文链接", "", "以下保留来源 README 的论文入口，可能包含该项目引用的相关工作，并非都由该项目作者提出。", "", "| 项目 | 论文入口 |", "| --- | --- |"]
    def canonical(url):
        return url.replace("/pdf/", "/abs/").removesuffix(".pdf")
    known = {canonical(p["url"]) for p in research["papers"]}
    for s in sources:
        urls = [u for u in metadata[s["id"]].get("paper_urls", []) if canonical(u) not in known]
        if urls:
            links = "、".join(f"[论文 {i+1}]({url})" for i, url in enumerate(urls))
            lines.append(f"| {s['repository']} | {links} |")

    lines += ["", "## 许可与归属", "",
              "第三方模板、样例和方法资料保留各自原有许可；本仓库不将它们统一重新授权。每条内容的来源与处理记录保存在数据中。仓库级许可不自动覆盖其中转载的数据，未找到许可的来源如实记录。", "",
              "Based on Tencent Zhuque Lab AI-Infra-Guard: [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard)。其 [NOTICE](../licenses/aiinfra/NOTICE) 与 [组件许可](../licenses/aiinfra/AIG-PromptSecurity/LICENSE.md) 随本仓库保留。", "",
              "| 项目 | 许可记录 | 原始许可文件 |", "| --- | --- | --- |"]
    for s in sources:
        folder = ROOT / "licenses" / s["id"]
        files = sorted(p for p in folder.rglob("*") if p.is_file()) if folder.exists() else []
        links = "、".join(f"[{p.name}](../{p.relative_to(ROOT).as_posix()})" for p in files) or "未获取到许可文本"
        lines.append(f"| [{s['repository']}]({s['url']}) | {s['license']} | {links} |")

    lines += ["", "## 数据与追溯", "",
              "- [三类索引](../data/groups.json)：前端名称、固定标识与各类数量。",
              "- [模板库](../data/catalog.json)：模板、分类、来源与处理记录。",
              "- [固定样例库](../data/examples.jsonl.gz)：压缩 JSONL，可用 `python app.py examples` 检索。",
              "- [论文记录](../data/research.json)与[方法记录](../data/methods.json)：保留实际接入范围。",
              "- [来源版本清单](../data/source_metadata/)与[许可原文](../licenses/)：用于核对来源和固定版本。",
              "- 原始下载快照和构建报告仅在本地生成；维护与重建命令见[首页](../README.md)。", ""]
    output = ROOT / "docs/SOURCES.md"
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote docs/SOURCES.md")


if __name__ == "__main__":
    main()
