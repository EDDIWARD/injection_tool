# 三类资料、项目来源与第三方归属

资料核验日期：2026-11-09。当前收录 53 个已核验 GitHub 项目入口、1,046 个默认模板、16,504 条固定样例和 15 项论文说明。

模板数量按清理与去重后的实际内容统计；同一文本可能关联多个来源，表中来源数量相加可能高于总数。固定样例保留原始目标，单独检索，不参与新目标的模板拼装。

另有 68 个本地编写的模式模板，以 locally_authored 标记，包括 4 条文言文语境模板。需要模型搜索、多轮交互或额外参数的方法单独记录，不计入默认 payload。

## 三类约定与前端字段

这是本项目的导航分类，并非互斥的学术分类体系。每条模板、固定样例、方法和论文只有一个 `group`；原有 `categories` 保留为可重叠的细分类标签。一个项目可关联多类。

| 主分类 | 固定标识 | 分类代码 | 模板 | 固定样例 | 方法记录 | 论文 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 基于模板 | `template` | [template.py](../injection_tool/groups/template.py) | 359 | 5798 | 54 | 12 |
| 基于前后缀优化 | `prefix_suffix` | [prefix_suffix.py](../injection_tool/groups/prefix_suffix.py) | 87 | 1179 | 7 | 2 |
| 基于角色扮演 | `roleplay` | [roleplay.py](../injection_tool/groups/roleplay.py) | 600 | 9527 | 1 | 1 |

归类规则按顺序执行：已指定的优化方法来源（如 AutoDAN）→ 编码、语言或结构形式 → 角色与模拟场景 → 控制性前后缀 → 其余固定模板。重叠条目取先匹配的一类，保留全部原标签；`group_assignment` 记录规则和版本，便于核对。来源关联表包含参考入口，不代表已实现这些项目的全部算法。

- 前端读取 [data/groups.json](../data/groups.json) 的 `groups` 数组，使用 `id` 作为页签值、`name` 作为显示文字；也可运行 `python app.py groups --format json`。
- 模板库为 `schema_version: 3`；每条 `templates[]` 带 `group`。生成 JSON 为 `schema_version: 2`，每条 `results[]` 带同样的 `group`；`group_counts` 是本次输出的数量，三类相加等于 `count`。
- Python 接口：`generate(goal, groups=['roleplay'])`；命令行：`--group roleplay`。重复 `--group` 表示取并集，与 `--category`、来源、语言等条件组合时取交集。
- JSONL 每行、逐条 TXT 的 `manifest.json` 均带 `group`；纯 TXT 文件和 `payloads.json` 仍只含文本，前端需要分类时使用完整结果或 manifest。
- `methods.json` 和 `research.json` 的记录也带 `group`，仅供参考；固定样例保持原目标，不参与新目标生成。

前端分组示例（`result` 为生成接口返回的 JSON）：

```javascript
const tabs = result.groups.map(group => ({
  id: group.id,
  title: group.name,
  count: result.group_counts[group.id],
  items: result.results.filter(item => item.group === group.id)
}));
```

下表 Stars 为采集时的快照，不代表当前值或攻击效果。“版本记录”包含固定提交、下载地址、SHA-256 和来源状态。项目可在多类出现，数量仅统计该类；0 表示参考入口或该类暂无导入内容。

## 1. 基于模板（`template`）

以固定结构、任务包装、编码或语言改写组织目标，包括代码、文言文和诗歌等形式。

对应代码：[injection_tool/groups/template.py](../injection_tool/groups/template.py)。筛选：`python app.py generate --goal "输出 TEST_OK" --group template`。

### 项目来源

| 项目 | Stars | 本类模板 | 本类固定样例 | 核验 / 版本记录 |
| --- | ---: | ---: | ---: | --- |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 26980 | 11 | 6 | [已核验](../data/source_metadata/promptfoo.json) |
| [elder-plinius/L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S) | 23222 | 0 | 0 | [已核验](../data/source_metadata/libertas.json) |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | 7442 | 105 | 0 | [已核验](../data/source_metadata/aiinfra.json) |
| [microsoft/PyRIT](https://github.com/microsoft/PyRIT) | 4773 | 102 | 0 | [已核验](../data/source_metadata/pyrit.json) |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | 4471 | 0 | 218 | [说明已核验](../data/source_metadata/purplellama.json) |
| [confident-ai/deepteam](https://github.com/confident-ai/deepteam) | 3092 | 0 | 0 | [已核验](../data/source_metadata/deepteam.json) |
| [greshake/llm-security](https://github.com/greshake/llm-security) | 2152 | 0 | 0 | [说明已核验](../data/source_metadata/llmsecurity.json) |
| [protectai/rebuff](https://github.com/protectai/rebuff) | 1532 | 0 | 0 | [说明已核验](../data/source_metadata/rebuff.json) |
| [thu-coai/Safety-Prompts](https://github.com/thu-coai/Safety-Prompts) | 1232 | 0 | 0 | [已核验](../data/source_metadata/safety_prompts.json) |
| [centerforaisafety/HarmBench](https://github.com/centerforaisafety/HarmBench) | 1116 | 0 | 0 | [已核验](../data/source_metadata/harmbench.json) |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | 943 | 21 | 0 | [已核验](../data/source_metadata/easyjailbreak.json) |
| [JailbreakBench/jailbreakbench](https://github.com/JailbreakBench/jailbreakbench) | 696 | 0 | 0 | [已核验](../data/source_metadata/jailbreakbench.json) |
| [RobustNLP/CipherChat](https://github.com/RobustNLP/CipherChat) | 628 | 0 | 0 | [已核验](../data/source_metadata/cipherchat.json) |
| [agencyenterprise/PromptInject](https://github.com/agencyenterprise/PromptInject) | 528 | 0 | 1 | [说明已核验](../data/source_metadata/promptinject.json) |
| [liu00222/Open-Prompt-Injection](https://github.com/liu00222/Open-Prompt-Injection) | 512 | 0 | 0 | [已核验](../data/source_metadata/openpromptinjection.json) |
| [CHATS-lab/persuasive_jailbreaker](https://github.com/CHATS-lab/persuasive_jailbreaker) | 367 | 0 | 0 | [已核验](../data/source_metadata/pap.json) |
| [xunhuang123/CC-BOS](https://github.com/xunhuang123/CC-BOS) | 259 | 0 | 7 | [已核验](../data/source_metadata/ccbos.json) |
| [lakeraai/pint-benchmark](https://github.com/lakeraai/pint-benchmark) | 200 | 0 | 0 | [说明已核验](../data/source_metadata/pint.json) |
| [STAIR-BUPT/JailBench](https://github.com/STAIR-BUPT/JailBench) | 194 | 3 | 1620 | [已核验](../data/source_metadata/jailbench.json) |
| [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | 186 | 17 | 986 | [已核验](../data/source_metadata/injecagent.json) |
| [yueliu1999/FlipAttack](https://github.com/yueliu1999/FlipAttack) | 182 | 4 | 0 | [已核验](../data/source_metadata/flipattack.json) |
| [NJUNLP/ReNeLLM](https://github.com/NJUNLP/ReNeLLM) | 165 | 2 | 0 | [已核验](../data/source_metadata/renellm.json) |
| [JailbreakBench/artifacts](https://github.com/JailbreakBench/artifacts) | 116 | 0 | 0 | [已核验](../data/source_metadata/jbb_artifacts.json) |
| [uw-nsl/ArtPrompt](https://github.com/uw-nsl/ArtPrompt) | 100 | 0 | 0 | [说明已核验](../data/source_metadata/artprompt.json) |
| [facebookresearch/wasp](https://github.com/facebookresearch/wasp) | 98 | 2 | 0 | [已核验](../data/source_metadata/wasp.json) |
| [SaFo-Lab/AgentDyn](https://github.com/SaFo-Lab/AgentDyn) | 92 | 0 | 0 | [已核验](../data/source_metadata/agentdyn.json) |
| [renqibing/CodeAttack](https://github.com/renqibing/CodeAttack) | 61 | 6 | 0 | [已核验](../data/source_metadata/codeattack.json) |
| [sleeepeer/PIArena](https://github.com/sleeepeer/PIArena) | 57 | 0 | 0 | [已核验](../data/source_metadata/piarena.json) |
| [HumanCompatibleAI/tensor-trust-data](https://github.com/HumanCompatibleAI/tensor-trust-data) | 56 | 0 | 750 | [已核验](../data/source_metadata/tensortrust.json) |
| [xaoLiu1222/cc-bos](https://github.com/xaoLiu1222/cc-bos) | 41 | 0 | 0 | [已核验](../data/source_metadata/ccbos_community.json) |
| [huizhang-L/CodeChameleon](https://github.com/huizhang-L/CodeChameleon) | 30 | 2 | 0 | [已核验](../data/source_metadata/codechameleon.json) |
| [microsoft/llmail-inject-challenge](https://github.com/microsoft/llmail-inject-challenge) | 28 | 0 | 0 | [已核验](../data/source_metadata/llmail.json) |
| [mlcommons/jailbreak-taxonomy](https://github.com/mlcommons/jailbreak-taxonomy) | 27 | 0 | 0 | [已核验](../data/source_metadata/mlcommons.json) |
| [microsoft/llmail-inject-challenge-analysis](https://github.com/microsoft/llmail-inject-challenge-analysis) | 12 | 0 | 0 | [已核验](../data/source_metadata/llmail_analysis.json) |
| [Arth-Singh/Arth-Jailbreak-Templates](https://github.com/Arth-Singh/Arth-Jailbreak-Templates) | 3 | 63 | 0 | [已核验](../data/source_metadata/arth_templates.json) |
| [MARUCIE/babel-bench](https://github.com/MARUCIE/babel-bench) | 3 | 0 | 125 | [已核验](../data/source_metadata/babelbench.json) |
| [InjecGuard/InjecGuard](https://github.com/InjecGuard/InjecGuard) | 1 | 0 | 0 | [说明已核验](../data/source_metadata/injecguard.json) |
| [amazon-science/task-tampering-prompt-injection](https://github.com/amazon-science/task-tampering-prompt-injection) | 0 | 0 | 1454 | [已核验](../data/source_metadata/tasktamper.json) |
| [ethz-spylab/agentdojo](https://github.com/ethz-spylab/agentdojo) | — | 3 | 0 | [已核验](../data/source_metadata/agentdojo.json) |
| [agiresearch/ASB](https://github.com/agiresearch/ASB) | — | 0 | 393 | [已核验](../data/source_metadata/asb.json) |
| [microsoft/BIPIA](https://github.com/microsoft/BIPIA) | — | 0 | 238 | [已核验](../data/source_metadata/bipia.json) |
| [tldrsec/prompt-injection-defenses](https://github.com/tldrsec/prompt-injection-defenses) | — | 0 | 0 | [说明已核验](../data/source_metadata/defenses.json) |
| [TakSec/Prompt-Injection-Everywhere](https://github.com/TakSec/Prompt-Injection-Everywhere) | — | 0 | 0 | [说明已核验](../data/source_metadata/everywhere.json) |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | — | 0 | 1 | [已核验](../data/source_metadata/garak.json) |
| [hubertyoo/GPTFuzz](https://github.com/hubertyoo/GPTFuzz) | — | 12 | 0 | [已核验](../data/source_metadata/gptfuzz.json) |
| [LearnPrompting/HackAPrompt](https://github.com/LearnPrompting/HackAPrompt) | — | 0 | 0 | [未获取成功](../data/source_metadata/hackaprompt.json) |
| [anthropics/many-shot-jailbreaking](https://github.com/anthropics/many-shot-jailbreaking) | — | 0 | 0 | [未获取成功](../data/source_metadata/manyshot.json) |

### 论文与实际接入范围

| 论文 | 年份 / 版本 | 本地接入内容 |
| --- | --- | --- |
| [CC-BOS](https://arxiv.org/abs/2602.22983) | ICLR 2026 | 导入官方仓库中的固定问题示例；完整方法依赖模型改写、翻译和果蝇搜索，不计入默认静态模板。另提供 4 条明确标注为本地编写的文言文包装。 |
| [Task-Tampering Prompt Injection](https://arxiv.org/abs/2611.07640) | 2026-11-05 预印本 | 导入 90 个场景文件中的独立注入文本及变体；需要原任务与工具环境，保存在固定样例库。 |
| [PIArena](https://arxiv.org/abs/2604.08499) | ACL 2026（上游 README） | 提取 heuristic.py 的直接注入文本；去重后进入默认库。搜索、训练与评测流程未运行。 |
| [AgentDyn](https://arxiv.org/abs/2602.03117) | 2026 预印本 | 核验项目与论文入口；动态环境和代理评测方法不作为单目标静态模板。 |
| [Adversarial Poetry](https://arxiv.org/abs/2511.15304) | 2025-11，2026-01 修订 | 收录论文入口；DeepTeam 中的诗歌模块是提示改写器，另记方法，不冒充可直接提交的论文模板。诗歌标签覆盖已有库内文本。 |
| [JailBench](https://arxiv.org/abs/2502.18935) | PAKDD 2025 | 由 540 个原始 seed 与 10,800 条 query 精确匹配，析出 20 个独立中文模板；原始 query 单独保留。 |
| [FlipAttack](https://arxiv.org/abs/2410.02832) | ICML 2025 | 接入 4 个 vanilla 反转模式；原 system/user 消息合并为一段文本并明确标注适配，不等价于完整论文实验。 |
| [EasyJailbreak](https://arxiv.org/abs/2403.12171) | 框架论文 | 导入具有明确目标槽位的种子，包括 AutoDAN、GPTFuzzer、Jailbroken、DeepInception；排除攻击模型和评判模型的提示。 |
| [ReNeLLM](https://arxiv.org/abs/2311.08268) | NAACL 2024 | 接入代码补全、表格填充、故事续写 3 个静态场景；不运行迭代改写。 |
| [CodeAttack](https://arxiv.org/abs/2403.07865) | ACL 2024 | 接入 6 个 Python 文本模板；输入转为带引号的字符串或字符序列，生成内容不执行。 |
| [CodeChameleon](https://arxiv.org/abs/2402.16717) | 2024 论文 | 接入 2 个未加密基线模板；个性化加密方法未实现，未将基线等同于论文全方法。 |
| [Persuasive Adversarial Prompts (PAP)](https://arxiv.org/abs/2401.06373) | 2024 论文 | 公开说服术语、定义单列为方法分类；没有将 taxonomy 描述直接拼成 payload。 |

### 方法记录

以下为方法说明，不直接参与 payload 生成；详细定义及原文件定位见 [methods.json](../data/methods.json)。

| 方法 | 原始记录 |
| --- | --- |
| Evidence-based Persuasion | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Logical Appeal | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Expert Endorsement | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Non-expert Testimonial | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Authority Endorsement | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Social Proof | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Injunctive Norm | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Foot-in-the-door | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Door-in-the-face | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Public Commitment | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Alliance Building | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Complimenting | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Shared Values | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Relationship Leverage | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Loyalty Appeals | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Favor | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Negotiation | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Encouragement | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Affirmation | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Positive Emotion Appeal | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Negative Emotion Appeal | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Storytelling | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Anchoring | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Priming | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Framing | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Confirmation Bias | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Reciprocity | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Compensation | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Supply Scarcity | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Time Pressure | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Reflective Thinking | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Threats | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| False Promises | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Misrepresentation | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| False Information | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Rumors | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Social Punishment | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Creating Dependency | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Exploiting Weakness | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| Discouragement | [pap](https://github.com/CHATS-lab/persuasive_jailbreaker/blob/11f8e8e89e5fcb2aaeb9d05b9570495d004b499d/persuasion_taxonomy.jsonl) |
| DeepTeam adversarial_poetry | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/adversarial_poetry/template.py) |
| DeepTeam authority_escalation | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/authority_escalation/template.py) |
| DeepTeam context_poisoning | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/context_poisoning/template.py) |
| DeepTeam embedded_instruction_json | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/embedded_instruction_json/template.py) |
| DeepTeam emotional_manipulation | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/emotional_manipulation/template.py) |
| DeepTeam goal_redirection | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/goal_redirection/template.py) |
| DeepTeam gray_box | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/gray_box/template.py) |
| DeepTeam math_problem | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/math_problem/template.py) |
| DeepTeam multilingual | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/multilingual/template.py) |
| DeepTeam permission_escalation | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/permission_escalation/template.py) |
| DeepTeam prompt_injection | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/prompt_injection/template.py) |
| DeepTeam prompt_probing | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/prompt_probing/template.py) |
| DeepTeam semantic_manipulation | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/semantic_manipulation/template.py) |
| DeepTeam synthetic_context_injection | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/synthetic_context_injection/template.py) |

## 2. 基于前后缀优化（`prefix_suffix`）

收录静态控制前后缀、优化种子和方法资料；generate 用于离线拼装，optimize 可通过 API 运行 PAIR、TAP、GPTFuzzer 的适配循环，另保留六个项目的上游源码。

对应代码：[injection_tool/groups/prefix_suffix.py](../injection_tool/groups/prefix_suffix.py)。筛选：`python app.py generate --goal "输出 TEST_OK" --group prefix_suffix`。

### 项目来源

| 项目 | Stars | 本类模板 | 本类固定样例 | 核验 / 版本记录 |
| --- | ---: | ---: | ---: | --- |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 26980 | 3 | 0 | [已核验](../data/source_metadata/promptfoo.json) |
| [elder-plinius/L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S) | 23222 | 3 | 0 | [已核验](../data/source_metadata/libertas.json) |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | 7442 | 22 | 0 | [已核验](../data/source_metadata/aiinfra.json) |
| [llm-attacks/llm-attacks](https://github.com/llm-attacks/llm-attacks) | 4855 | 0 | 0 | [说明已核验](../data/source_metadata/llmattacks.json) |
| [microsoft/PyRIT](https://github.com/microsoft/PyRIT) | 4773 | 33 | 0 | [已核验](../data/source_metadata/pyrit.json) |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | 4471 | 0 | 17 | [说明已核验](../data/source_metadata/purplellama.json) |
| [confident-ai/deepteam](https://github.com/confident-ai/deepteam) | 3092 | 0 | 0 | [已核验](../data/source_metadata/deepteam.json) |
| [centerforaisafety/HarmBench](https://github.com/centerforaisafety/HarmBench) | 1116 | 0 | 0 | [已核验](../data/source_metadata/harmbench.json) |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | 943 | 8 | 0 | [已核验](../data/source_metadata/easyjailbreak.json) |
| [patrickrchao/JailbreakingLLMs](https://github.com/patrickrchao/JailbreakingLLMs) | 813 | 0 | 0 | [说明已核验](../data/source_metadata/pair.json) |
| [JailbreakBench/jailbreakbench](https://github.com/JailbreakBench/jailbreakbench) | 696 | 0 | 0 | [已核验](../data/source_metadata/jailbreakbench.json) |
| [agencyenterprise/PromptInject](https://github.com/agencyenterprise/PromptInject) | 528 | 0 | 9 | [说明已核验](../data/source_metadata/promptinject.json) |
| [SheltonLiu-N/AutoDAN](https://github.com/SheltonLiu-N/AutoDAN) | 468 | 1 | 0 | [已核验](../data/source_metadata/autodan.json) |
| [SaFoLab-WISC/AutoDAN-Turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo) | 395 | 0 | 50 | [已核验](../data/source_metadata/autodan_turbo.json) |
| [RICommunity/TAP](https://github.com/RICommunity/TAP) | 253 | 0 | 0 | [说明已核验](../data/source_metadata/tap.json) |
| [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | 186 | 0 | 986 | [已核验](../data/source_metadata/injecagent.json) |
| [JailbreakBench/artifacts](https://github.com/JailbreakBench/artifacts) | 116 | 0 | 0 | [已核验](../data/source_metadata/jbb_artifacts.json) |
| [sleeepeer/PIArena](https://github.com/sleeepeer/PIArena) | 57 | 4 | 0 | [已核验](../data/source_metadata/piarena.json) |
| [HumanCompatibleAI/tensor-trust-data](https://github.com/HumanCompatibleAI/tensor-trust-data) | 56 | 0 | 105 | [已核验](../data/source_metadata/tensortrust.json) |
| [Arth-Singh/Arth-Jailbreak-Templates](https://github.com/Arth-Singh/Arth-Jailbreak-Templates) | 3 | 8 | 0 | [已核验](../data/source_metadata/arth_templates.json) |
| [amazon-science/task-tampering-prompt-injection](https://github.com/amazon-science/task-tampering-prompt-injection) | 0 | 0 | 3 | [已核验](../data/source_metadata/tasktamper.json) |
| [ethz-spylab/agentdojo](https://github.com/ethz-spylab/agentdojo) | — | 2 | 0 | [已核验](../data/source_metadata/agentdojo.json) |
| [microsoft/BIPIA](https://github.com/microsoft/BIPIA) | — | 0 | 9 | [已核验](../data/source_metadata/bipia.json) |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | — | 0 | 9 | [已核验](../data/source_metadata/garak.json) |
| [hubertyoo/GPTFuzz](https://github.com/hubertyoo/GPTFuzz) | — | 3 | 0 | [已核验](../data/source_metadata/gptfuzz.json) |

### 论文与实际接入范围

| 论文 | 年份 / 版本 | 本地接入内容 |
| --- | --- | --- |
| [AutoDAN-Turbo](https://arxiv.org/abs/2410.05295) | ICLR 2025 Spotlight（上游 README） | 导入公开策略库中的固定示例，策略描述单列；不把策略定义作为目标模型 payload。 |
| [AutoDAN](https://arxiv.org/abs/2310.04451) | 2023 预印本 | 导入公开 initial seed；不加载 .pth、不执行遗传搜索。 |

### 方法记录

以下为方法说明，不直接参与 payload 生成；详细定义及原文件定位见 [methods.json](../data/methods.json)。

| 方法 | 原始记录 |
| --- | --- |
| Historical Contextualization with Metaphorical Abstraction | [autodan_turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo/blob/389df844439888fc44ea7f5e8e95fd2b5c82ea64/logs_r/warm_up_strategy_library.json) |
| Defensive Research Simulation Framework | [autodan_turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo/blob/389df844439888fc44ea7f5e8e95fd2b5c82ea64/logs_r/warm_up_strategy_library.json) |
| Fictional Narrative Abstraction | [autodan_turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo/blob/389df844439888fc44ea7f5e8e95fd2b5c82ea64/logs_r/warm_up_strategy_library.json) |
| Defensive Education Justification | [autodan_turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo/blob/389df844439888fc44ea7f5e8e95fd2b5c82ea64/logs_r/warm_up_strategy_library.json) |
| DeepTeam context_flooding | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/context_flooding/template.py) |
| DeepTeam input_bypass | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/input_bypass/template.py) |
| DeepTeam system_override | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/system_override/template.py) |

## 3. 基于角色扮演（`roleplay`）

通过人物身份、虚构情境、模拟环境或多角色回答组织目标。

对应代码：[injection_tool/groups/roleplay.py](../injection_tool/groups/roleplay.py)。筛选：`python app.py generate --goal "输出 TEST_OK" --group roleplay`。

### 项目来源

| 项目 | Stars | 本类模板 | 本类固定样例 | 核验 / 版本记录 |
| --- | ---: | ---: | ---: | --- |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 26980 | 57 | 26 | [已核验](../data/source_metadata/promptfoo.json) |
| [elder-plinius/L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S) | 23222 | 1 | 0 | [已核验](../data/source_metadata/libertas.json) |
| [0xk1h0/ChatGPT_DAN](https://github.com/0xk1h0/ChatGPT_DAN) | 13156 | 0 | 0 | [已核验](../data/source_metadata/dan_collection.json) |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | 7442 | 4 | 0 | [已核验](../data/source_metadata/aiinfra.json) |
| [microsoft/PyRIT](https://github.com/microsoft/PyRIT) | 4773 | 365 | 0 | [已核验](../data/source_metadata/pyrit.json) |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | 4471 | 0 | 10 | [说明已核验](../data/source_metadata/purplellama.json) |
| [verazuo/jailbreak_llms](https://github.com/verazuo/jailbreak_llms) | 3882 | 0 | 0 | [说明已核验](../data/source_metadata/jailbreakchat.json) |
| [confident-ai/deepteam](https://github.com/confident-ai/deepteam) | 3092 | 0 | 0 | [已核验](../data/source_metadata/deepteam.json) |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | 943 | 191 | 0 | [已核验](../data/source_metadata/easyjailbreak.json) |
| [STAIR-BUPT/JailBench](https://github.com/STAIR-BUPT/JailBench) | 194 | 17 | 9180 | [已核验](../data/source_metadata/jailbench.json) |
| [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | 186 | 0 | 136 | [已核验](../data/source_metadata/injecagent.json) |
| [tmlr-group/DeepInception](https://github.com/tmlr-group/DeepInception) | 181 | 0 | 58 | [已核验](../data/source_metadata/deepinception.json) |
| [NJUNLP/ReNeLLM](https://github.com/NJUNLP/ReNeLLM) | 165 | 1 | 0 | [已核验](../data/source_metadata/renellm.json) |
| [HumanCompatibleAI/tensor-trust-data](https://github.com/HumanCompatibleAI/tensor-trust-data) | 56 | 0 | 72 | [已核验](../data/source_metadata/tensortrust.json) |
| [Arth-Singh/Arth-Jailbreak-Templates](https://github.com/Arth-Singh/Arth-Jailbreak-Templates) | 3 | 29 | 0 | [已核验](../data/source_metadata/arth_templates.json) |
| [amazon-science/task-tampering-prompt-injection](https://github.com/amazon-science/task-tampering-prompt-injection) | 0 | 0 | 35 | [已核验](../data/source_metadata/tasktamper.json) |
| [agiresearch/ASB](https://github.com/agiresearch/ASB) | — | 0 | 7 | [已核验](../data/source_metadata/asb.json) |
| [microsoft/BIPIA](https://github.com/microsoft/BIPIA) | — | 0 | 3 | [已核验](../data/source_metadata/bipia.json) |
| [hubertyoo/GPTFuzz](https://github.com/hubertyoo/GPTFuzz) | — | 59 | 0 | [已核验](../data/source_metadata/gptfuzz.json) |

### 论文与实际接入范围

| 论文 | 年份 / 版本 | 本地接入内容 |
| --- | --- | --- |
| [DeepInception](https://arxiv.org/abs/2311.03191) | 2023 论文 | 官方固定示例单列；具有明确目标变量的静态模式从 EasyJailbreak 导入并保留其来源。 |

### 方法记录

以下为方法说明，不直接参与 payload 生成；详细定义及原文件定位见 [methods.json](../data/methods.json)。

| 方法 | 原始记录 |
| --- | --- |
| DeepTeam roleplay | [deepteam](https://github.com/confident-ai/deepteam/blob/6306f0ff319a932955399405af82f78ee91e9370/deepteam/attacks/single_turn/roleplay/template.py) |

## 循环优化源码与 API 适配

以下核心源码保持上游字节与 MIT 许可，固定提交和逐文件校验见 [optimizer_sources.json](../data/optimizer_sources.json)。数据集、模型资源和实验日志等未收录，清单中的 `excluded` 列出缺项；完整原版实验需恢复相应资源并独立配置环境。

本项目另外提供三个统一 API 适配器：PAIR 风格反馈改写、TAP 风格分支剪枝、GPTFuzzer 风格单目标种子池变异。它们使用本项目编写的提示和评判格式，不等同于原论文全部配置；具体差异和运行方式见 [README](../README.md#api-循环优化的配置与运行)。

| 方法 | 固定版本 | 本地原始入口 | API 适配 |
| --- | --- | --- | --- |
| pair | [6379ef705a0f](https://github.com/patrickrchao/JailbreakingLLMs/tree/6379ef705a0fc745530f7d895963510c021b496a) | [入口](../third_party/optimizers/pair/main.py) | [代码](../injection_tool/optimizers/pair.py) |
| tap | [7bcdad30537c](https://github.com/RICommunity/TAP/tree/7bcdad30537c679d00699fac16052dc916c89a6d) | [入口](../third_party/optimizers/tap/main_TAP.py) | [代码](../injection_tool/optimizers/tap.py) |
| gptfuzz | [0c26cccc3b19](https://github.com/hubertyoo/GPTFuzz/tree/0c26cccc3b19cd5eed91d6cb6912431cf2501762) | [入口](../third_party/optimizers/gptfuzz/gptfuzz.py) | [代码](../injection_tool/optimizers/gptfuzz.py) |
| autodan | [34062e964185](https://github.com/SheltonLiu-N/AutoDAN/tree/34062e964185693e81a6775b4f0d00bfd7507612) | [入口](../third_party/optimizers/autodan/autodan_hga_eval.py) | 尚未接入统一 API 层 |
| autodan_turbo | [389df8444398](https://github.com/SaFoLab-WISC/AutoDAN-Turbo/tree/389df844439888fc44ea7f5e8e95fd2b5c82ea64) | [入口](../third_party/optimizers/autodan_turbo/main.py) | 尚未接入统一 API 层 |
| llmattacks | [098262edf85f](https://github.com/llm-attacks/llm-attacks/tree/098262edf85f807224e70ecd87b9d83716bf6b73) | [入口](../third_party/optimizers/llmattacks/experiments/main.py) | 尚未接入统一 API 层 |

## 其他论文入口

CC-BOS 的官方实现为 [xunhuang123/CC-BOS](https://github.com/xunhuang123/CC-BOS)。xaoLiu1222/cc-bos 与 MARUCIE/babel-bench 按社区项目归属；社区样例对论文来源的声明保留原文，未经逐项验证。

### 上游说明中的其他论文链接

以下保留来源 README 的论文入口，可能包含该项目引用的相关工作，并非都由该项目作者提出。

| 项目 | 论文入口 |
| --- | --- |
| ethz-spylab/agentdojo | [论文 1](https://arxiv.org/abs/2406.13352)、[论文 2](https://openreview.net/forum?id=m1YYAQjO3w) |
| SaFo-Lab/AgentDyn | [论文 1](https://aclanthology.org/2025.acl-long.1468.pdf) |
| uw-nsl/ArtPrompt | [论文 1](https://aclanthology.org/2024.acl-long.809)、[论文 2](https://aclanthology.org/2024.acl-long.809/) |
| agiresearch/ASB | [论文 1](https://arxiv.org/abs/2410.02644)、[论文 2](https://openreview.net/forum?id=V4y0CpX4hK) |
| SheltonLiu-N/AutoDAN | [论文 1](https://openreview.net/forum?id=7Jwpw4qKkb) |
| SaFoLab-WISC/AutoDAN-Turbo | [论文 1](https://openreview.net/forum?id=7Jwpw4qKkb) |
| microsoft/BIPIA | [论文 1](https://arxiv.org/abs/1508.00305)、[论文 2](https://arxiv.org/abs/2312.14197) |
| xunhuang123/CC-BOS | [论文 1](https://openreview.net/forum?id=O7fxz7D6vf) |
| RobustNLP/CipherChat | [论文 1](https://openreview.net/forum?id=MbfAK4s61A) |
| tldrsec/prompt-injection-defenses | [论文 1](https://arxiv.org/abs/2306.05499)、[论文 2](https://arxiv.org/abs/2308.01990)、[论文 3](https://arxiv.org/abs/2308.07308)、[论文 4](https://arxiv.org/abs/2308.14132)、[论文 5](https://arxiv.org/abs/2309.00614)、[论文 6](https://arxiv.org/abs/2310.03684)、[论文 7](https://arxiv.org/abs/2310.10501)、[论文 8](https://arxiv.org/abs/2311.00172)、[论文 9](https://arxiv.org/abs/2311.11509)、[论文 10](https://arxiv.org/abs/2311.11538)、[论文 11](https://arxiv.org/abs/2312.06674)、[论文 12](https://arxiv.org/abs/2312.17673)、[论文 13](https://arxiv.org/abs/2401.07612)、[论文 14](https://arxiv.org/abs/2402.00898)、[论文 15](https://arxiv.org/abs/2402.06363)、[论文 16](https://arxiv.org/abs/2402.13494)、[论文 17](https://arxiv.org/abs/2402.15727)、[论文 18](https://arxiv.org/abs/2403.04786)、[论文 19](https://arxiv.org/abs/2403.04957)、[论文 20](https://arxiv.org/abs/2403.14720)、[论文 21](https://arxiv.org/abs/2410.22770)、[论文 22](https://arxiv.org/pdf/2306.04528)、[论文 23](https://arxiv.org/pdf/2310.06387)、[论文 24](https://arxiv.org/pdf/2312.10766)、[论文 25](https://arxiv.org/pdf/2402.16459)、[论文 26](https://arxiv.org/pdf/2404.13968)、[论文 27](https://arxiv.org/pdf/2501.18492)、[论文 28](https://arxiv.org/pdf/2502.05174) |
| NVIDIA/garak | [论文 1](https://arxiv.org/abs/2106.09898)、[论文 2](https://arxiv.org/abs/2303.18190)、[论文 3](https://arxiv.org/abs/2406.11036) |
| hubertyoo/GPTFuzz | [论文 1](https://arxiv.org/pdf/2309.10253.pdf) |
| centerforaisafety/HarmBench | [论文 1](https://arxiv.org/abs/2402.04249) |
| uiuc-kang-lab/InjecAgent | [论文 1](https://arxiv.org/abs/2403.02691) |
| InjecGuard/InjecGuard | [论文 1](https://arxiv.org/pdf/2410.22770) |
| JailbreakBench/jailbreakbench | [论文 1](https://arxiv.org/abs/2307.15043)、[论文 2](https://arxiv.org/abs/2308.01263)、[论文 3](https://arxiv.org/abs/2309.00614)、[论文 4](https://arxiv.org/abs/2310.03684)、[论文 5](https://arxiv.org/abs/2310.08419)、[论文 6](https://arxiv.org/abs/2311.03348)、[论文 7](https://arxiv.org/abs/2404.01318)、[论文 8](https://arxiv.org/abs/2404.02151)、[论文 9](https://arxiv.org/abs/xxxx.xxxxx) |
| verazuo/jailbreak_llms | [论文 1](https://arxiv.org/abs/2308.03825) |
| microsoft/llmail-inject-challenge | [论文 1](https://arxiv.org/abs/2403.14720)、[论文 2](https://arxiv.org/abs/2404.13208)、[论文 3](https://arxiv.org/abs/2406.00799)、[论文 4](https://arxiv.org/abs/2506.09956) |
| microsoft/llmail-inject-challenge-analysis | [论文 1](https://arxiv.org/abs/2506.09956) |
| llm-attacks/llm-attacks | [论文 1](https://arxiv.org/abs/2307.15043) |
| greshake/llm-security | [论文 1](https://arxiv.org/abs/2302.12173)、[论文 2](https://arxiv.org/pdf/2302.12173.pdf) |
| mlcommons/jailbreak-taxonomy | [论文 1](https://arxiv.org/abs/2503.05731) |
| patrickrchao/JailbreakingLLMs | [论文 1](https://arxiv.org/abs/2310.08419)、[论文 2](https://arxiv.org/abs/2404.01318) |
| sleeepeer/PIArena | [论文 1](https://arxiv.org/abs/2211.09527)、[论文 2](https://arxiv.org/abs/2307.15043)、[论文 3](https://arxiv.org/abs/2410.05451)、[论文 4](https://arxiv.org/abs/2410.22770)、[论文 5](https://arxiv.org/abs/2411.00348)、[论文 6](https://arxiv.org/abs/2504.11358)、[论文 7](https://arxiv.org/abs/2507.02735)、[论文 8](https://arxiv.org/abs/2507.15219)、[论文 9](https://arxiv.org/abs/2510.12252)、[论文 10](https://arxiv.org/abs/2510.19207)、[论文 11](https://arxiv.org/abs/2511.10720) |
| agencyenterprise/PromptInject | [论文 1](https://arxiv.org/abs/2211.09527) |
| thu-coai/Safety-Prompts | [论文 1](https://arxiv.org/abs/2304.10436)、[论文 2](https://arxiv.org/abs/2402.16444)、[论文 3](https://arxiv.org/pdf/2309.07045.pdf) |
| HumanCompatibleAI/tensor-trust-data | [论文 1](https://tensortrust.ai/paper) |
| facebookresearch/wasp | [论文 1](https://arxiv.org/abs/2504.18575) |

## 许可与归属

第三方模板、样例和方法资料保留各自原有许可；本仓库不将它们统一重新授权。每条内容的来源与处理记录保存在数据中。仓库级许可不自动覆盖其中转载的数据，未找到许可的来源如实记录。

Based on Tencent Zhuque Lab AI-Infra-Guard: [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard)。其 [NOTICE](../licenses/aiinfra/NOTICE) 与 [组件许可](../licenses/aiinfra/AIG-PromptSecurity/LICENSE.md) 随本仓库保留。

| 项目 | 许可记录 | 原始许可文件 |
| --- | --- | --- |
| [ethz-spylab/agentdojo](https://github.com/ethz-spylab/agentdojo) | MIT | [LICENSE](../licenses/agentdojo/LICENSE) |
| [SaFo-Lab/AgentDyn](https://github.com/SaFo-Lab/AgentDyn) | MIT | [LICENSE](../licenses/agentdyn/LICENSE) |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | Apache-2.0 | [LICENSE.md](../licenses/aiinfra/AIG-PromptSecurity/LICENSE.md)、[LICENSE](../licenses/aiinfra/LICENSE)、[NOTICE](../licenses/aiinfra/NOTICE) |
| [Arth-Singh/Arth-Jailbreak-Templates](https://github.com/Arth-Singh/Arth-Jailbreak-Templates) | Apache-2.0 | [LICENSE](../licenses/arth_templates/LICENSE) |
| [uw-nsl/ArtPrompt](https://github.com/uw-nsl/ArtPrompt) | MIT | [LICENSE](../licenses/artprompt/LICENSE) |
| [agiresearch/ASB](https://github.com/agiresearch/ASB) | MIT | [LICENSE](../licenses/asb/LICENSE) |
| [SheltonLiu-N/AutoDAN](https://github.com/SheltonLiu-N/AutoDAN) | MIT | [LICENSE](../licenses/autodan/LICENSE) |
| [SaFoLab-WISC/AutoDAN-Turbo](https://github.com/SaFoLab-WISC/AutoDAN-Turbo) | MIT | [LICENSE.txt](../licenses/autodan_turbo/LICENSE.txt) |
| [MARUCIE/babel-bench](https://github.com/MARUCIE/babel-bench) | MIT | [LICENSE](../licenses/babelbench/LICENSE) |
| [microsoft/BIPIA](https://github.com/microsoft/BIPIA) | MIT | [LICENSE](../licenses/bipia/LICENSE)、[NOTICE.md](../licenses/bipia/NOTICE.md) |
| [xunhuang123/CC-BOS](https://github.com/xunhuang123/CC-BOS) | not found in fetched root files | 未获取到许可文本 |
| [xaoLiu1222/cc-bos](https://github.com/xaoLiu1222/cc-bos) | not found in fetched root files | 未获取到许可文本 |
| [RobustNLP/CipherChat](https://github.com/RobustNLP/CipherChat) | MIT | [LICENSE](../licenses/cipherchat/LICENSE) |
| [renqibing/CodeAttack](https://github.com/renqibing/CodeAttack) | MIT | [LICENSE](../licenses/codeattack/LICENSE) |
| [huizhang-L/CodeChameleon](https://github.com/huizhang-L/CodeChameleon) | MIT | [LICENSE](../licenses/codechameleon/LICENSE) |
| [0xk1h0/ChatGPT_DAN](https://github.com/0xk1h0/ChatGPT_DAN) | not found in fetched root files | 未获取到许可文本 |
| [tmlr-group/DeepInception](https://github.com/tmlr-group/DeepInception) | MIT | [LICENSE](../licenses/deepinception/LICENSE) |
| [confident-ai/deepteam](https://github.com/confident-ai/deepteam) | Apache-2.0 | [LICENSE.md](../licenses/deepteam/LICENSE.md) |
| [tldrsec/prompt-injection-defenses](https://github.com/tldrsec/prompt-injection-defenses) | not found in fetched root files | 未获取到许可文本 |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | see upstream terms | [LICENSE](../licenses/easyjailbreak/LICENSE) |
| [TakSec/Prompt-Injection-Everywhere](https://github.com/TakSec/Prompt-Injection-Everywhere) | MIT | [LICENSE](../licenses/everywhere/LICENSE) |
| [yueliu1999/FlipAttack](https://github.com/yueliu1999/FlipAttack) | MIT | [LICENSE](../licenses/flipattack/LICENSE) |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | Apache-2.0 | [LICENSE](../licenses/garak/LICENSE) |
| [hubertyoo/GPTFuzz](https://github.com/hubertyoo/GPTFuzz) | MIT | [LICENSE](../licenses/gptfuzz/LICENSE) |
| [LearnPrompting/HackAPrompt](https://github.com/LearnPrompting/HackAPrompt) | not found in fetched root files | 未获取到许可文本 |
| [centerforaisafety/HarmBench](https://github.com/centerforaisafety/HarmBench) | MIT | [LICENSE](../licenses/harmbench/LICENSE) |
| [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | MIT | [LICENCE](../licenses/injecagent/LICENCE) |
| [InjecGuard/InjecGuard](https://github.com/InjecGuard/InjecGuard) | MIT | [LICENSE](../licenses/injecguard/LICENSE) |
| [STAIR-BUPT/JailBench](https://github.com/STAIR-BUPT/JailBench) | MIT | [LICENSE](../licenses/jailbench/LICENSE) |
| [JailbreakBench/jailbreakbench](https://github.com/JailbreakBench/jailbreakbench) | MIT | [LICENSE](../licenses/jailbreakbench/LICENSE) |
| [verazuo/jailbreak_llms](https://github.com/verazuo/jailbreak_llms) | MIT | [LICENSE](../licenses/jailbreakchat/LICENSE) |
| [JailbreakBench/artifacts](https://github.com/JailbreakBench/artifacts) | MIT | [LICENSE](../licenses/jbb_artifacts/LICENSE) |
| [elder-plinius/L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S) | see upstream terms | [LICENSE](../licenses/libertas/LICENSE) |
| [microsoft/llmail-inject-challenge](https://github.com/microsoft/llmail-inject-challenge) | MIT | [LICENSE](../licenses/llmail/LICENSE) |
| [microsoft/llmail-inject-challenge-analysis](https://github.com/microsoft/llmail-inject-challenge-analysis) | MIT | [LICENSE](../licenses/llmail_analysis/LICENSE) |
| [llm-attacks/llm-attacks](https://github.com/llm-attacks/llm-attacks) | MIT | [LICENSE](../licenses/llmattacks/LICENSE) |
| [greshake/llm-security](https://github.com/greshake/llm-security) | MIT | [LICENSE](../licenses/llmsecurity/LICENSE) |
| [anthropics/many-shot-jailbreaking](https://github.com/anthropics/many-shot-jailbreaking) | not found in fetched root files | 未获取到许可文本 |
| [mlcommons/jailbreak-taxonomy](https://github.com/mlcommons/jailbreak-taxonomy) | see upstream terms | [LICENSE](../licenses/mlcommons/LICENSE) |
| [liu00222/Open-Prompt-Injection](https://github.com/liu00222/Open-Prompt-Injection) | MIT | [LICENSE](../licenses/openpromptinjection/LICENSE) |
| [patrickrchao/JailbreakingLLMs](https://github.com/patrickrchao/JailbreakingLLMs) | MIT | [LICENSE](../licenses/pair/LICENSE) |
| [CHATS-lab/persuasive_jailbreaker](https://github.com/CHATS-lab/persuasive_jailbreaker) | Apache-2.0 | [LICENSE](../licenses/pap/LICENSE) |
| [sleeepeer/PIArena](https://github.com/sleeepeer/PIArena) | MIT | [LICENSE](../licenses/piarena/LICENSE) |
| [lakeraai/pint-benchmark](https://github.com/lakeraai/pint-benchmark) | MIT | [LICENSE](../licenses/pint/LICENSE) |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | MIT | [LICENSE](../licenses/promptfoo/LICENSE) |
| [agencyenterprise/PromptInject](https://github.com/agencyenterprise/PromptInject) | MIT | [LICENSE](../licenses/promptinject/LICENSE) |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | MIT (CybersecurityBenchmarks component); repository root has different terms | [LICENSE](../licenses/purplellama/CybersecurityBenchmarks/LICENSE)、[LICENSE](../licenses/purplellama/LICENSE) |
| [microsoft/PyRIT](https://github.com/microsoft/PyRIT) | MIT | [LICENSE](../licenses/pyrit/LICENSE)、[NOTICE.txt](../licenses/pyrit/NOTICE.txt) |
| [protectai/rebuff](https://github.com/protectai/rebuff) | Apache-2.0 | [LICENSE](../licenses/rebuff/LICENSE) |
| [NJUNLP/ReNeLLM](https://github.com/NJUNLP/ReNeLLM) | MIT | [LICENSE](../licenses/renellm/LICENSE) |
| [thu-coai/Safety-Prompts](https://github.com/thu-coai/Safety-Prompts) | Apache-2.0 | [LICENSE](../licenses/safety_prompts/LICENSE) |
| [RICommunity/TAP](https://github.com/RICommunity/TAP) | MIT | [LICENSE](../licenses/tap/LICENSE) |
| [amazon-science/task-tampering-prompt-injection](https://github.com/amazon-science/task-tampering-prompt-injection) | see upstream terms | [LICENSE](../licenses/tasktamper/LICENSE) |
| [HumanCompatibleAI/tensor-trust-data](https://github.com/HumanCompatibleAI/tensor-trust-data) | not found in fetched root files | 未获取到许可文本 |
| [facebookresearch/wasp](https://github.com/facebookresearch/wasp) | CC-BY-NC-4.0 (WASP); incorporated components have separate terms | [LICENSE](../licenses/wasp/LICENSE) |

## 数据与追溯

- [三类索引](../data/groups.json)：前端名称、固定标识与各类数量。
- [模板库](../data/catalog.json)：模板、分类、来源与处理记录。
- [固定样例库](../data/examples.jsonl.gz)：压缩 JSONL，可用 `python app.py examples` 检索。
- [论文记录](../data/research.json)与[方法记录](../data/methods.json)：保留实际接入范围。
- [来源版本清单](../data/source_metadata/)与[许可原文](../licenses/)：用于核对来源和固定版本。
- 原始下载快照和构建报告仅在本地生成；维护与重建命令见[首页](../README.md)。
