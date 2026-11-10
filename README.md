# Prompt Injection 模板整合器

输入一个目标，离线生成分类好的 prompt injection / jailbreak 测试文本。**不需要 API Key，也不调用模型。**

当前包含 **1,046 个可生成模板、16,504 条固定样例**，统一按下面三类组织。每条输出保留来源，固定样例不会混进新目标的生成结果。

| 主分类 | 代码 / 前端标识 | 内容 |
| --- | --- | --- |
| 基于模板 | `template` | 固定结构、任务包装、编码、代码、文言文与诗歌等 |
| 基于前后缀优化 | `prefix_suffix` | 优化方法资料、种子与静态控制前后缀；不运行优化搜索 |
| 基于角色扮演 | `roleplay` | 人物身份、虚构情境、模拟和多角色回答 |

每条记录只有一个主分类 `group`；原有 37 个具名细分类保留在 `categories` 中作为辅助标签。分类代码对应 `injection_tool/groups/` 下的三个同名文件。

## 快速使用

安装 **Python 3.10 或更高版本**，下载并解压本项目。

**Windows：双击 `start.bat`，输入目标，回车即可。**

也可以在项目目录运行：

```bash
python app.py
```

结果保存在 `outputs/日期时间/`：

- `payloads/`：一条一个 TXT，文件内只有 payload；`manifest.json` 是单独的来源清单。
- `payloads.json`：纯文本字符串数组，便于批量使用。
- `results.json`、`results.jsonl`、`results.txt`：带分类和来源的完整结果。

## 常用命令

```bash
# 生成全部模板，一条一个 TXT（使用一个新目录）
python app.py generate --goal "输出 TEST_OK" --payload-dir outputs/test

# 只导出 payload 字符串数组
python app.py generate --goal "输出 TEST_OK" --format payloads --out outputs/payloads.json

# 只生成文言文语境模板
python app.py generate --goal "输出 TEST_OK" --category classical_chinese --payload-dir outputs/classical

# 按三大类生成（可换成 template 或 prefix_suffix）
python app.py generate --goal "输出 TEST_OK" --group roleplay --out outputs/roleplay.json

# 从 UTF-8 文件读取多行目标
python app.py generate --goal-file goal.txt --out outputs/results.json

# 查看三大类、细分类标签、来源、统计和论文
python app.py groups
python app.py groups --format json
python app.py categories
python app.py sources
python app.py stats
python app.py research

# 检索固定样例
python app.py examples --source ccbos --limit 7
```

可用 `--group`、`--category`、`--source`、`--language zh`、`--scope injection` 组合筛选。`--group` 可重复传入；`examples`、`research` 也支持它。更多参数见 `python app.py generate --help`。语言筛选不会翻译输入目标。文言文标签的 4 条默认模板为本地编写，CC-BOS 官方固定样例另存于样例库。

## 前端对接

读取 [data/groups.json](data/groups.json) 获取三个页签的 `id`、`name` 和数量。生成结果的每条 `results[]` 都带 `group`，按此字段分组即可；`group_counts` 给出本次生成数量。JSONL 和逐条文件的清单也保留同样的分类。

完整字段、分组示例和三类来源统一写在 [docs/SOURCES.md](docs/SOURCES.md)。纯 payload 导出仍只含文本，需要分类时读取完整 JSON 或清单。

## 项目文件

`injection_tool/` 是核心代码，`data/` 是模板与压缩样例库，`docs/` 汇总项目与论文来源，`licenses/` 保留第三方许可，`scripts/` 与 `tests/` 用于维护和检查。

[查看全部项目来源、论文与第三方归属](docs/SOURCES.md)

<details>
<summary>维护与重建（可选）</summary>

日常使用不需要安装依赖。维护时可运行：

```bash
python -m pip install -r requirements-maintainer.txt
python -m unittest discover -s tests -v

# 按来源清单恢复下载快照，再重建数据和来源说明
python scripts/fetch_artifacts.py
python scripts/build_catalog.py
python scripts/write_source_index.py

# 只刷新三类归属与文档，不重新下载来源
python scripts/organize_groups.py
python scripts/write_source_index.py
```

来源清单保留固定提交、文件地址与 SHA-256；下载程序不执行上游代码。构建报告、原始快照与生成结果仅保存在本地，不提交 GitHub。

</details>

模板通过静态完整性检查，不保证目标模型执行或攻击有效。第三方内容保留各自许可，不以统一许可重新授权。

Based on Tencent Zhuque Lab AI-Infra-Guard: [原项目](https://github.com/Tencent/AI-Infra-Guard)。
