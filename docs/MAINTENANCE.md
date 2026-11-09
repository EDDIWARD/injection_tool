# 维护说明

日常生成只需要 Python 标准库，不必安装额外依赖。仓库保留可直接使用的数据、必要的来源清单和测试；下载快照、旧输出和构建中间文件不提交。

## 检查

```bash
python -m pip install -r requirements-maintainer.txt
python -m unittest discover -s tests -v
```

测试从 `tests/fixtures/` 的压缩原始样本读取清理回归数据；校验来源清单与固定提交。若本地已有下载快照，还会验证文件的 SHA-256。

## 从固定版本重建

```bash
python scripts/fetch_artifacts.py
python scripts/build_catalog.py
python scripts/write_source_index.py
python scripts/write_expansion_report.py
```

`data/source_metadata/` 保留已采用文件的地址、固定提交和校验值，省去未使用的完整仓库目录树。`fetch_artifacts.py` 按清单恢复 `data/upstream/`，不执行上游代码。构建需要下载成功的完整快照；运行生成器不需要这些快照。

重建会生成 `data/catalog_raw.json`、`data/templates_held.json` 等中间文件，它们已被 Git 忽略。固定样例以 `data/examples.jsonl.gz` 保存，程序直接读取。人工清理规则保存在 `data/template_reviews.json`，与原文哈希绑定。

`scripts/collect_sources.py --refresh --source 来源ID` 会更新指定来源的版本；更新后需重新下载、检查导入规则并重建。修改库后，应检查相应测试样本与文档中的数量。

## 目录

```text
app.py / start.bat       命令行与 Windows 入口
injection_tool/          拼装、筛选、导出和清理逻辑
data/                   模板、压缩样例、来源与论文记录
docs/                   来源、清理、扩充和维护文档
licenses/               上游 LICENSE / NOTICE
scripts/                收集与构建工具
tests/                  自动检查和压缩回归样本
```

历史输出与原始下载快照已在本地备份，未上传 GitHub。使用程序后新生成的 `outputs/` 同样不会被提交。
