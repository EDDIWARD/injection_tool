# 第二轮扩充记录

核验日期：2026-11-09。只统计实际下载、转换和去重的内容。

| 项目 | 扩充前 | 当前 |
| --- | ---: | ---: |
| 已核验 GitHub 项目入口 | 26 | 53 |
| 默认可生成模板 | 651 | 1046 |
| 固定样例 | 3,972 | 16,504 |
| 具名分类（另有未归类） | 32 | 37 |

另整理 15 项论文入口与接入说明，以及 62 项方法/术语记录。后两项不计入 payload 数量。

## 本轮实际接入的模板来源

| 来源 | Stars 快照 | 默认模板来源关联数 | 处理方式 |
| --- | ---: | ---: | --- |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | 7442 | 131 | 逐个提取单输入的中英文静态函数；不执行源代码，不导入生成器或评判器提示。 |
| [EasyJailbreak/EasyJailbreak](https://github.com/EasyJailbreak/EasyJailbreak) | 943 | 220 | 仅提取有明确槽位的目标模型种子；与旧库去重。 |
| [Arth-Singh/Arth-Jailbreak-Templates](https://github.com/Arth-Singh/Arth-Jailbreak-Templates) | 3 | 100 | 逐个 YAML 导入，并沿用前次人工清理规则；与 PyRIT 的转载合并。 |
| [STAIR-BUPT/JailBench](https://github.com/STAIR-BUPT/JailBench) | 194 | 20 | 10,800 条 query 与 540 个 seed 精确匹配，仅得到 20 种独立模板。 |
| [elder-plinius/L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S) | 23222 | 4 | 人工选定 4 个独立章节；绑定目标、移除作者水印，保留源章节位置。 |
| [renqibing/CodeAttack](https://github.com/renqibing/CodeAttack) | 61 | 6 | 6 个 Python 文本模板；输入按字面量编码，保留引号、换行与 Unicode。 |
| [NJUNLP/ReNeLLM](https://github.com/NJUNLP/ReNeLLM) | 165 | 3 | 3 个静态嵌套场景；不运行模型改写。 |
| [yueliu1999/FlipAttack](https://github.com/yueliu1999/FlipAttack) | 182 | 4 | 4 个 vanilla 模式的一段文本适配；不声称等价于 system/user 双消息实验。 |
| [huizhang-L/CodeChameleon](https://github.com/huizhang-L/CodeChameleon) | 30 | 2 | 2 个未加密基线；不声称复现个性化加密方法。 |
| [sleeepeer/PIArena](https://github.com/sleeepeer/PIArena) | 57 | 4 | 直接、忽略、伪完成等静态注入；按实际文本去重。 |
| [SheltonLiu-N/AutoDAN](https://github.com/SheltonLiu-N/AutoDAN) | 468 | 1 | 公开初始种子；不加载模型或搜索。 |

表内是来源关联数，不是净增数；同一文本可能被多个项目转载。新增默认模板的净变化以表首为准。高星但需要额外交互、没有可用槽位或仅为方法框架的项目，仍保留资料入口，不强行算入默认库。

Based on Tencent Zhuque Lab AI-Infra-Guard: [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard)。原始 LICENSE、NOTICE 及归属信息随本地快照保留。

## 文言文

论文是 [CC-BOS](https://arxiv.org/abs/2602.22983)，其最新版论文页链接到作者的 [官方仓库](https://github.com/xunhuang123/CC-BOS)。

- 官方仓库中的固定问题逐项提取，去重后 7 条，保存在样例库。没有把改写器的整段提示或示例答案放进默认 payload。
- 文言文默认分类新增 4 条本地编写的注疏、学宫问答、奏对、工匠手札模板，明确标注来源；输入目标保持原样，不自动翻译成古文。
- 完整 CC-BOS 需要模型改写、翻译和搜索，本程序没有执行或复现这些步骤。
- xaoLiu1222/cc-bos 与 MARUCIE/babel-bench 按社区项目记录。BabelBench 自称来自论文的样例归属未经逐项验证，保留原声明但不升级成官方来源。

```powershell
python app.py generate --goal "输出 TEST_OK" --category classical_chinese --payload-dir outputs/classical_new
python app.py examples --source ccbos --limit 7
python app.py research
```

## 论文与接入范围

| 论文 | 年份/版本 | 本地处理 |
| --- | --- | --- |
| [CC-BOS](https://arxiv.org/abs/2602.22983) | ICLR 2026 | 导入官方仓库中的固定问题示例；完整方法依赖模型改写、翻译和果蝇搜索，不计入默认静态模板。另提供 4 条明确标注为本地编写的文言文包装。 |
| [Task-Tampering Prompt Injection](https://arxiv.org/abs/2611.07640) | 2026-11-05 预印本 | 导入 90 个场景文件中的独立注入文本及变体；需要原任务与工具环境，保存在固定样例库。 |
| [PIArena](https://arxiv.org/abs/2604.08499) | ACL 2026（上游 README） | 提取 heuristic.py 的直接注入文本；去重后进入默认库。搜索、训练与评测流程未运行。 |
| [AgentDyn](https://arxiv.org/abs/2602.03117) | 2026 预印本 | 核验项目与论文入口；动态环境和代理评测方法不作为单目标静态模板。 |
| [Adversarial Poetry](https://arxiv.org/abs/2511.15304) | 2025-11，2026-01 修订 | 收录论文入口；DeepTeam 中的诗歌模块是提示改写器，另记方法，不冒充可直接提交的论文模板。诗歌标签覆盖已有库内文本。 |
| [JailBench](https://arxiv.org/abs/2502.18935) | PAKDD 2025 | 由 540 个原始 seed 与 10,800 条 query 精确匹配，析出 20 个独立中文模板；原始 query 单独保留。 |
| [FlipAttack](https://arxiv.org/abs/2410.02832) | ICML 2025 | 接入 4 个 vanilla 反转模式；原 system/user 消息合并为一段文本并明确标注适配，不等价于完整论文实验。 |
| [AutoDAN-Turbo](https://arxiv.org/abs/2410.05295) | ICLR 2025 Spotlight（上游 README） | 导入公开策略库中的固定示例，策略描述单列；不把策略定义作为目标模型 payload。 |
| [EasyJailbreak](https://arxiv.org/abs/2403.12171) | 框架论文 | 导入具有明确目标槽位的种子，包括 AutoDAN、GPTFuzzer、Jailbroken、DeepInception；排除攻击模型和评判模型的提示。 |
| [ReNeLLM](https://arxiv.org/abs/2311.08268) | NAACL 2024 | 接入代码补全、表格填充、故事续写 3 个静态场景；不运行迭代改写。 |
| [CodeAttack](https://arxiv.org/abs/2403.07865) | ACL 2024 | 接入 6 个 Python 文本模板；输入转为带引号的字符串或字符序列，生成内容不执行。 |
| [CodeChameleon](https://arxiv.org/abs/2402.16717) | 2024 论文 | 接入 2 个未加密基线模板；个性化加密方法未实现，未将基线等同于论文全方法。 |
| [Persuasive Adversarial Prompts (PAP)](https://arxiv.org/abs/2401.06373) | 2024 论文 | 公开说服术语、定义单列为方法分类；没有将 taxonomy 描述直接拼成 payload。 |
| [DeepInception](https://arxiv.org/abs/2311.03191) | 2023 论文 | 官方固定示例单列；具有明确目标变量的静态模式从 EasyJailbreak 导入并保留其来源。 |
| [AutoDAN](https://arxiv.org/abs/2310.04451) | 2023 预印本 | 导入公开 initial seed；不加载 .pth、不执行遗传搜索。 |

## 输出与检查

历史生成结果未打包进仓库。运行首页命令可重新生成：`payloads.json` 为纯字符串数组，`payloads/` 一条一个 TXT；索引与来源保存在单独的 manifest。

25 项测试覆盖前次清理回归、全库填入、精确目标抽取、拒绝执行源代码表达式、Unicode/引号编码、来源清单、压缩样例读取与逐条导出。测试通过不表示攻击成功率；本轮没有对外部模型发起攻击或复现论文成功率。

固定样例保存在 `data/examples.jsonl.gz`；方法记录在 `data/methods.json`。原始清理样本保存在压缩测试数据中；下载快照可按固定来源清单恢复。不同来源的许可单独保存在 licenses/；完整来源表见 [SOURCES.md](SOURCES.md)。
