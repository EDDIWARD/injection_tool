"""Write a readable source/coverage index from the verified local manifest."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
cat = json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))
lines = ['# 来源与覆盖情况', '', '整理日期：2026-11-09。数量以本地实际下载和解析结果为准，不使用论文宣称的总量代替导入数量。模板数量为清理后的默认可生成条目；原始数量、拆分和待处理记录见 QUALITY.md 与 data/quality_report.json。', '',
         '“完整目录已核验”表示取得仓库目录和固定提交；“README 已核验”表示核对仓库默认提交并下载说明，可能没有完整目录。只要模板/样例数量为 0，就没有把该来源算进生成库。', '',
         'Stars 为采集时的快照，精确时间见各来源元数据；未取得则显示 —。热度不表示对某个模型的攻击效果。论文与实际接入范围见 [EXPANSION.md](EXPANSION.md)。', '',
         '| 来源 | Stars | 类型 | 核验状态 | 模板来源关联数 | 样例来源关联数 | 已下载文件 |',
         '| --- | ---: | --- | --- | ---: | ---: | ---: |']
status = {'verified': '完整目录已核验', 'verified_readme_only': 'README 已核验', 'unavailable': '本次未获取成功', 'local': '本地编写'}
for source in sorted(cat['sources'], key=lambda s: (-s.get('stars', -1), s['id'])):
    if source['id'] == 'local':
        continue
    lines.append(f"| [{source['repository']}]({source['url']}) | {source.get('stars', '—')} | {source['kind']} | {status[source['status']]} | {source['template_count']} | {source['example_count']} | {source.get('artifact_count', 0)} |")
local_count = next(s['template_count'] for s in cat['sources'] if s['id'] == 'local')
lines += ['', f'同一模板若出现在多个项目中，会合并并保留多个来源。因此表内来源关联数相加可能大于去重后的模板/样例总数。{local_count} 个本地模板明确标记 locally_authored，只参考公开模式，没有冒充论文原文。', '',
          '## 版本、许可与论文入口', '', '仓库许可不自动覆盖其转载数据。本地保留已下载的 LICENSE/NOTICE、上游作者和引用字段；未找到许可的内容明确记录为未找到。这里没有对全部第三方数据作再分发许可判断。', '']
for source in cat['sources']:
    sid = source['id']
    if sid == 'local':
        continue
    lines += [f"### {sid}", '', f"- 仓库：[{source['repository']}]({source['url']})", f"- 状态：{status[source['status']]}", f"- 固定提交：`{source.get('commit', '未获得')}`", f"- 许可记录：{source['license']}", f"- 元数据：[来源清单](../data/source_metadata/{sid}.json)"]
    for license_path in source.get('license_files', []):
        lines.append(f"- 许可文件：[{license_path}](../licenses/{sid}/{license_path})")
    readme = ROOT/'data/upstream'/sid/'README.md'
    urls = json.loads((ROOT/'data/source_metadata'/f'{sid}.json').read_text(encoding='utf-8')).get('paper_urls', [])
    if readme.exists():
        urls = sorted(set(re.findall(r'https?://(?:arxiv\.org/(?:abs|pdf)/[\w.\-]+|aclanthology\.org/[\w.\-/]+|openreview\.net/(?:forum|pdf)\?id=[\w-]+|tensortrust\.ai/paper)', readme.read_text(encoding='utf-8'))))
    if urls:
        lines.append('- 论文入口（来自上游 README）：' + '、'.join(f'[论文 {i+1}]({u})' for i,u in enumerate(urls[:8])))
    lines.append('')
lines += ['## 尚未导入或不适合单目标拼装的内容', '',
          '- 完整 Tensor Trust 原始游戏转储、LLMail 比赛大文件和其他外部托管数据未全量下载。这里只统计实际取得的文件。',
          '- 需要模型搜索的 GCG、PAIR、TAP，以及多轮、图像、音频攻击，仅记录项目入口；没有把方法名称当作可用的静态模板。',
          '- WASP 的 URL 模板需要具体场景地址；不计入单目标模板。两个文本模板使用明确标注的通用场景改写。',
          '- PyRIT 有额外参数或未支持语法的条目列在 [导入报告](import_report.json)。',
          '- CC-BOS 官方示例与 BabelBench 社区示例分开归属；未验证社区样例自称来自论文的声明。4 条本地文言文包装不是 CC-BOS 算法复现。',
          '- CodeChameleon 仅接入未加密基线；FlipAttack 仅接入 4 个 vanilla 模式的一段文本适配；ReNeLLM 仅接入静态场景。',
          '- Based on Tencent Zhuque Lab AI-Infra-Guard: https://github.com/Tencent/AI-Infra-Guard 。该组件的 LICENSE 与 NOTICE 保存在 licenses/，作者归属位于元数据中。',
          '- HackAPrompt 和 many-shot 候选仓库本次未成功读取，保留失败信息，不计入已核验来源。', '']
(ROOT/'docs/SOURCES.md').write_text('\n'.join(lines).replace('data/quality_report.json', 'docs/quality_report.json'), encoding='utf-8')
print('Wrote docs/SOURCES.md')
