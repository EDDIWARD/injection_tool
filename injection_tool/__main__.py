from __future__ import annotations
import argparse
import gzip
from collections import Counter
import json
from pathlib import Path
import sys
from datetime import datetime
from .core import CARRIERS, ROOT, generate, load_catalog, serialize, write_result, write_payload_files

def parser():
    p = argparse.ArgumentParser(description="输入一个目标，离线生成分类后的 prompt injection / jailbreak 测试样例。")
    sub = p.add_subparsers(dest="command")
    g = sub.add_parser("generate", help="生成全部或筛选后的模板")
    target = g.add_mutually_exclusive_group(required=True)
    target.add_argument("--goal", help="目标文本")
    target.add_argument("--goal-file", type=Path, help="从 UTF-8 文本文件读取目标")
    g.add_argument("--category", action="append", help="按分类筛选，可重复")
    g.add_argument("--source", action="append", help="按来源筛选，可重复")
    g.add_argument("--language", choices=["all", "zh", "en", "mixed", "und"], default="all")
    g.add_argument("--scope", choices=["all", "injection", "jailbreak"], default="all")
    g.add_argument("--carrier", choices=[*CARRIERS, "all"], action="append")
    g.add_argument("--format", choices=["json", "jsonl", "txt", "payloads"], default="json")
    g.add_argument("--out", type=Path)
    g.add_argument("--payload-dir", type=Path, help="逐条导出纯文本，每个文件仅含一条 payload；目录须不存在")
    sub.add_parser("stats", help="来源、分类、模板和固定样例统计")
    sub.add_parser("categories", help="列出分类")
    sub.add_parser("sources", help="列出来源和实际导入数量")
    sub.add_parser("research", help="查看论文、年份与实际接入范围")
    examples = sub.add_parser("examples", help="检索固定样例（不会把旧目标冒充成新目标）")
    examples.add_argument("--source")
    examples.add_argument("--search", default="")
    examples.add_argument("--limit", type=int, default=10)
    return p

def interactive():
    cat = load_catalog()
    print(f"Prompt Injection 模板整合器 | {len(cat['templates'])} 个可用模板\n")
    goal = input("输入目标（多行目标可使用 --goal-file）：\n> ")
    result = generate(goal, catalog=cat)
    output = ROOT / "outputs" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    for fmt in ("json", "jsonl", "txt"):
        write_result(result, output / f"results.{fmt}", fmt)
    write_result(result, output / "payloads.json", "payloads")
    write_payload_files(result, output / "payloads")
    print(f"\n已生成 {result['count']} 条，保存至：{output}")

def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        if args.command is None:
            interactive()
            return 0
        cat = load_catalog()
        if args.command == "generate":
            goal = args.goal_file.read_text(encoding="utf-8-sig") if args.goal_file else args.goal
            carriers = list(CARRIERS) if "all" in (args.carrier or []) else args.carrier
            result = generate(goal, catalog=cat, categories=args.category, sources=args.source,
                              language=args.language, scope=args.scope, carriers=carriers)
            if not result["count"]:
                raise ValueError("筛选条件没有匹配到可用模板")
            if args.payload_dir:
                path = write_payload_files(result, args.payload_dir)
                print(f"已逐条导出 {result['count']} 个纯文本文件：{path}")
            if args.out:
                path = write_result(result, args.out, args.format)
                print(f"已生成 {result['count']} 条：{path}")
            elif not args.payload_dir:
                print(serialize(result, args.format), end="")
        elif args.command == "stats":
            print(json.dumps(cat["stats"], ensure_ascii=False, indent=2))
        elif args.command == "categories":
            counts = Counter(c for t in cat["templates"] for c in t["categories"])
            for c in cat["categories"]:
                print(f"{c['id']:26} {c['name']:12} {counts[c['id']]} 模板")
        elif args.command == "sources":
            for s in cat["sources"]:
                print(f"{s['id']:22} {s['status']:22} 模板={s['template_count']:4} 样例={s['example_count']:4} {s['url']}")
        elif args.command == "research":
            research = json.loads((ROOT / "data/research.json").read_text(encoding="utf-8"))
            for paper in research["papers"]:
                print(f"{paper['year']} | {paper['name']}\n  {paper['url']}\n  {paper['integration']}\n")
        elif args.command == "examples":
            if args.limit < 1:
                raise ValueError("limit 必须大于零")
            if args.source and args.source not in {s['id'] for s in cat['sources']}:
                raise ValueError("未知来源")
            count = 0
            example_path = ROOT / "data/examples.jsonl.gz"
            stream = gzip.open(example_path, "rt", encoding="utf-8") if example_path.exists() else (ROOT / "data/examples.jsonl").open(encoding="utf-8")
            with stream as f:
                for line in f:
                    row = json.loads(line)
                    if args.source and not any(x['source_id'] == args.source for x in row['provenance']):
                        continue
                    if args.search.casefold() not in row["text"].casefold():
                        continue
                    print(json.dumps(row, ensure_ascii=False))
                    count += 1
                    if count >= args.limit:
                        break
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
