"""Verify/restore pinned upstream code without importing or executing it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="仅验证，不下载")
    parser.add_argument("--source", action="append")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/optimizer_sources.json").read_text(encoding="utf-8"))
    known = {source["id"] for source in manifest["sources"]}
    if set(args.source or []) - known:
        parser.error("未知源码来源")
    count = 0
    for source in manifest["sources"]:
        if args.source and source["id"] not in args.source:
            continue
        folder = (ROOT / source["directory"]).resolve()
        if not folder.is_relative_to((ROOT / "third_party/optimizers").resolve()):
            raise ValueError("源码目录超出预期范围")
        for record in source["files"]:
            relative = PurePosixPath(record["path"])
            target = (folder / relative).resolve()
            if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(folder):
                raise ValueError("非法源码路径")
            if target.exists():
                content = target.read_bytes()
            elif args.check:
                raise ValueError(f"缺少源码：{source['id']}/{record['path']}")
            else:
                expected = f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/{record['path']}"
                if record["url"] != expected:
                    raise ValueError("下载地址与固定来源不符")
                with urllib.request.urlopen(expected, timeout=40) as response:
                    content = response.read(record["size"] + 1)
            if len(content) != record["size"] or hashlib.sha256(content).hexdigest() != record["sha256"]:
                raise ValueError(f"源码校验失败，保留现有文件：{source['id']}/{record['path']}")
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            count += 1
    print(f"已核验 {count} 个源码文件；未运行上游代码。")


if __name__ == "__main__":
    main()
