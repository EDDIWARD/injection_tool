"""Regenerate the collection-pass report from the actual local catalog."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cat = json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))
research = json.loads((ROOT / 'data/research.json').read_text(encoding='utf-8'))
stats = cat['stats']
sources = {s['id']: s for s in cat['sources']}
lines = [
    '# 第二轮扩充记录', '', '核验日期：2026-11-09。只统计实际下载、转换和去重的内容。', '',
    '| 项目 | 扩充前 | 当前 |', '| --- | ---: | ---: |',
    f"| 已核验 GitHub 项目入口 | 26 | {stats['verified_repositories']} |",
    f"| 默认可生成模板 | 651 | {stats['templates']} |",
    f"| 固定样例 | 3,972 | {stats['examples']:,} |",
    f"| 具名分类（另有未归类） | 32 | {stats['categories'] - 1} |", '',
    f"另整理 {stats['research_papers']} 项论文入口与接入说明，以及 {stats['method_references']} 项方法/术语记录。后两项不计入 payload 数量。", '',
    '## 本轮实际接入的模板来源', '',
    '| 来源 | Stars 快照 | 默认模板来源关联数 | 处理方式 |', '| --- | ---: | ---: | --- |',
]
descriptions = {
    'aiinfra': '逐个提取单输入的中英文静态函数；不执行源代码，不导入生成器或评判器提示。',
    'easyjailbreak': '仅提取有明确槽位的目标模型种子；与旧库去重。',
    'arth_templates': '逐个 YAML 导入，并沿用前次人工清理规则；与 PyRIT 的转载合并。',
    'jailbench': '10,800 条 query 与 540 个 seed 精确匹配，仅得到 20 种独立模板。',
    'libertas': '人工选定 4 个独立章节；绑定目标、移除作者水印，保留源章节位置。',
    'codeattack': '6 个 Python 文本模板；输入按字面量编码，保留引号、换行与 Unicode。',
    'renellm': '3 个静态嵌套场景；不运行模型改写。',
    'flipattack': '4 个 vanilla 模式的一段文本适配；不声称等价于 system/user 双消息实验。',
    'codechameleon': '2 个未加密基线；不声称复现个性化加密方法。',
    'piarena': '直接、忽略、伪完成等静态注入；按实际文本去重。',
    'autodan': '公开初始种子；不加载模型或搜索。',
}
for sid, note in descriptions.items():
    s = sources[sid]
    lines.append(f"| [{s['repository']}]({s['url']}) | {s.get('stars', '—')} | {s['template_count']} | {note} |")
lines += ['', '表内是来源关联数，不是净增数；同一文本可能被多个项目转载。新增默认模板的净变化以表首为准。高星但需要额外交互、没有可用槽位或仅为方法框架的项目，仍保留资料入口，不强行算入默认库。', '',
          'Based on Tencent Zhuque Lab AI-Infra-Guard: [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard)。原始 LICENSE、NOTICE 及归属信息随本地快照保留。', '',
          '## 文言文', '',
          '论文是 [CC-BOS](https://arxiv.org/abs/2602.22983)，其最新版论文页链接到作者的 [官方仓库](https://github.com/xunhuang123/CC-BOS)。', '',
          '- 官方仓库中的固定问题逐项提取，去重后 7 条，保存在样例库。没有把改写器的整段提示或示例答案放进默认 payload。',
          '- 文言文默认分类新增 4 条本地编写的注疏、学宫问答、奏对、工匠手札模板，明确标注来源；输入目标保持原样，不自动翻译成古文。',
          '- 完整 CC-BOS 需要模型改写、翻译和搜索，本程序没有执行或复现这些步骤。',
          '- xaoLiu1222/cc-bos 与 MARUCIE/babel-bench 按社区项目记录。BabelBench 自称来自论文的样例归属未经逐项验证，保留原声明但不升级成官方来源。', '',
          '```powershell',
          'python app.py generate --goal "输出 TEST_OK" --category classical_chinese --payload-dir outputs/classical_new',
          'python app.py examples --source ccbos --limit 7',
          'python app.py research', '```', '',
          '## 论文与接入范围', '', '| 论文 | 年份/版本 | 本地处理 |', '| --- | --- | --- |']
for p in research['papers']:
    lines.append(f"| [{p['name']}]({p['url']}) | {p['venue_or_version']} | {p['integration']} |")
lines += ['', '## 输出与检查', '',
          '历史生成结果未打包进仓库。运行首页命令可重新生成：`payloads.json` 为纯字符串数组，`payloads/` 一条一个 TXT；索引与来源保存在单独的 manifest。', '',
          '25 项测试覆盖前次清理回归、全库填入、精确目标抽取、拒绝执行源代码表达式、Unicode/引号编码、来源清单、压缩样例读取与逐条导出。测试通过不表示攻击成功率；本轮没有对外部模型发起攻击或复现论文成功率。', '',
          '固定样例保存在 `data/examples.jsonl.gz`；方法记录在 `data/methods.json`。原始清理样本保存在压缩测试数据中；下载快照可按固定来源清单恢复。不同来源的许可单独保存在 licenses/；完整来源表见 [SOURCES.md](SOURCES.md)。', '']
(ROOT / 'docs/EXPANSION.md').write_text('\n'.join(lines), encoding='utf-8')
print('Wrote docs/EXPANSION.md')
