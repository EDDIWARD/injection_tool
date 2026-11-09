# Prompt Injection 模板整合器

输入一个目标，离线生成分类好的 prompt injection / jailbreak 测试文本。**不需要 API Key，也不调用模型。**

当前包含 **1,046 个可生成模板、37 个具名分类、16,504 条固定样例**。每条输出保留来源，固定样例不会混进新目标的生成结果。

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

# 从 UTF-8 文件读取多行目标
python app.py generate --goal-file goal.txt --out outputs/results.json

# 查看分类、来源、统计和论文
python app.py categories
python app.py sources
python app.py stats
python app.py research

# 检索固定样例
python app.py examples --source ccbos --limit 7
```

可用 `--category`、`--source`、`--language zh`、`--scope injection` 筛选；更多参数见 `python app.py generate --help`。语言筛选不会翻译输入目标。文言文分类的 4 条默认模板为本地编写，CC-BOS 官方固定样例另存于样例库。

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
```

来源清单保留固定提交、文件地址与 SHA-256；下载程序不执行上游代码。构建报告、原始快照与生成结果仅保存在本地，不提交 GitHub。

</details>

模板通过静态完整性检查，不保证目标模型执行或攻击有效。第三方内容保留各自许可，不以统一许可重新授权。

Based on Tencent Zhuque Lab AI-Infra-Guard: [原项目](https://github.com/Tencent/AI-Infra-Guard)。
