"""mma 启动检查:验证 <工作区>/题目 和 <工作区>/数据 是否就位。

用法:
    python check_input.py <工作区路径>

退出码:
    0 = 通过
    1 = 缺 题目/ 或 空
    2 = 缺 数据/ 或 空(可能是无数据题,允许通过并提示)
    3 = 工作区路径不存在
"""
import sys
import os
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python check_input.py <工作区路径>")
        return 3

    workspace = Path(sys.argv[1])
    if not workspace.exists():
        print(f"❌ 工作区不存在: {workspace}")
        return 3

    print(f"📂 工作区: {workspace}")

    # 检查 题目/
    problem_dir = workspace / "题目"
    if not problem_dir.exists():
        print(f"❌ 缺少 题目/ 目录")
        return 1
    problems = list(problem_dir.glob("*"))
    problems = [p for p in problems if p.is_file() and p.suffix.lower() in {".pdf", ".docx", ".doc"}]
    if not problems:
        print(f"❌ 题目/ 目录为空(需要 PDF/DOCX/DOC)")
        return 1
    print(f"✅ 题目/ 找到 {len(problems)} 个文件:")
    for p in problems:
        print(f"   - {p.name} ({p.stat().st_size} bytes)")

    # 检查 数据/(可选)
    data_dir = workspace / "数据"
    if not data_dir.exists():
        print(f"⚠️  缺少 数据/ 目录(可能是无附件题,继续)")
        return 0
    data_files = [p for p in data_dir.iterdir() if p.is_file()]
    if not data_files:
        print(f"⚠️  数据/ 目录为空(无附件题,继续)")
        return 0
    print(f"✅ 数据/ 找到 {len(data_files)} 个文件:")
    for p in data_files:
        print(f"   - {p.name} ({p.stat().st_size} bytes)")

    print("\n✅ 输入检查通过,可以启动 Stage 1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
