"""mma 自动机械验收:跑 eval-checklist 的 A(编译层)+ C(硬规则)+ D(完整性) 部分。

用法:
    python auto_verify.py <工作区路径>

退出码:
    0 = 全 PASS
    1 = 有 FAIL
    2 = 工作区或论文/ 目录不存在
"""
import sys
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field

# Windows GBK stdout 不支持 emoji,强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    results: list = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = ""):
        self.results.append(CheckResult(name, passed, detail))

    def print(self):
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n{'='*60}")
        print(f"mma 自动验收报告: {passed}/{total} PASS")
        print(f"{'='*60}")
        for r in self.results:
            mark = "✅" if r.passed else "❌"
            print(f"{mark} {r.name}: {r.detail}")
        print(f"{'='*60}")
        if passed < total:
            print(f"\n❌ {total - passed} 项 FAIL,需要人工检查")
        else:
            print(f"\n✅ 全部 PASS,建议再人工跑 eval-checklist.md 完整版")


def check_compile(workspace: Path, report: Report):
    """A 编译层:xelatex 两次 + 错误计数。"""
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        report.add("A 编译", False, "论文/ 目录不存在")
        return

    for tex_name in ["论文.tex", "电子版.tex"]:
        log_name = tex_name.replace(".tex", ".log")
        try:
            for _ in range(2):
                subprocess.run(
                    ["xelatex", "-interaction=nonstopmode", tex_name],
                    cwd=paper_dir,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    text=True,
                    timeout=120,
                )
            log_path = paper_dir / log_name
            if not log_path.exists():
                report.add(f"A 编译 {tex_name}", False, "日志不存在")
                continue
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
            errors = log_text.count("Error")
            report.add(
                f"A 编译 {tex_name}",
                errors == 0,
                f"Error 计数 = {errors}",
            )
        except FileNotFoundError:
            report.add(f"A 编译 {tex_name}", False, "xelatex 未安装或不在 PATH")
        except subprocess.TimeoutExpired:
            report.add(f"A 编译 {tex_name}", False, "编译超时(120s)")


def check_pdf_exists(workspace: Path, report: Report):
    """A PDF 存在性。"""
    paper_dir = workspace / "论文"
    for pdf in ["论文.pdf", "电子版.pdf"]:
        p = paper_dir / pdf
        report.add(
            f"A PDF 存在 {pdf}",
            p.exists(),
            "存在" if p.exists() else f"缺失:{p}",
        )


def check_no_toc(workspace: Path, report: Report):
    """A11 / F1.5: 无 \\tableofcontents。"""
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        return
    count = 0
    for tex in paper_dir.glob("[0-9]*.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        count += text.count(r"\tableofcontents")
    for tex in paper_dir.glob("论文.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        count += text.count(r"\tableofcontents")
    report.add(
        "C/F1.5 无目录",
        count == 0,
        f"\\tableofcontents 出现 {count} 次(应为 0)",
    )


def check_symbols(workspace: Path, report: Report):
    """C 硬规则:正文无 ①②③、\\textbf(除摘要/假设/优缺点外)。"""
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        return
    allow_textbf = {"0.摘要.tex", "3.模型假设.tex", "7.模型优缺点评价.tex", "0.AI声明.tex"}
    bullets = 0
    textbf_violations = []
    for tex in paper_dir.glob("[0-9]*.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        bullets += len(re.findall(r"[①②③④⑤●○]", text))
        if tex.name not in allow_textbf:
            if r"\textbf" in text:
                textbf_violations.append(tex.name)
    report.add(
        "C1.1 无分点符号",
        bullets == 0,
        f"①②③等出现 {bullets} 次",
    )
    report.add(
        "C1.3 正文无 \\textbf",
        not textbf_violations,
        f"违规文件:{textbf_violations}" if textbf_violations else "通过",
    )


def check_ai_declaration(workspace: Path, report: Report):
    """F2.1: 0.AI声明.tex 存在且被论文.tex 引用。"""
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        return
    ai_file = paper_dir / "0.AI声明.tex"
    if not ai_file.exists():
        report.add("F2.1 AI 声明存在", False, "0.AI声明.tex 不存在")
        return
    # 验证被论文.tex 引用
    for entry in ["论文.tex", "电子版.tex"]:
        tex_path = paper_dir / entry
        if not tex_path.exists():
            continue
        text = tex_path.read_text(encoding="utf-8", errors="ignore")
        if r"0.AI声明.tex" not in text:
            report.add(f"F2.1 {entry} 引用 AI 声明", False, "未 \\input{0.AI声明.tex}")
        else:
            # 验证在 9.参考文献.tex 之前
            ai_pos = text.find(r"0.AI声明.tex")
            ref_pos = text.find(r"9.参考文献.tex")
            if ref_pos == -1 or ai_pos < ref_pos:
                report.add(f"F2.1 {entry} AI 声明在参考文献前", True, "OK")
            else:
                report.add(
                    f"F2.1 {entry} AI 声明在参考文献前",
                    False,
                    f"AI 声明在参考文献之后(ai={ai_pos}, ref={ref_pos})",
                )


def check_chapter_files(workspace: Path, report: Report):
    """D1/D2/D3: 11 个 .tex + 5.x 子节 + 8.章已删。"""
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        return
    required = [
        "0.摘要.tex",
        "1.问题重述.tex",
        "2.问题分析.tex",
        "3.模型假设.tex",
        "4.符号说明.tex",
        "5.模型的建立与求解.tex",
        "6.模型检验.tex",
        "7.模型优缺点评价.tex",
        "0.AI声明.tex",
        "9.参考文献.tex",
        "10.附录.tex",
    ]
    missing = [r for r in required if not (paper_dir / r).exists()]
    report.add(
        "D1 11 个 .tex 全部存在(v3)",
        not missing,
        f"缺失:{missing}" if missing else "OK",
    )

    # 5.x 子节
    for q in [1, 2, 3, 4]:
        for s in [
            f"5.{q}.1.数据预处理.tex",
            f"5.{q}.2.XXX模型的建立.tex",
            f"5.{q}.3.XXX模型的求解.tex",
            f"5.{q}.4.XXX模型的检验.tex",
            f"5.{q}.5.XXX结果的分析.tex",
        ]:
            if not (paper_dir / s).exists():
                report.add(f"D2 5.{q}.x 子节 {s}", False, "缺失")

    # 8.章已删
    eight_chapters = list(paper_dir.glob("8.*.tex"))
    report.add(
        "D3.4 8.章已删除",
        not eight_chapters,
        f"残留:{eight_chapters}" if eight_chapters else "OK",
    )


def check_figures(workspace: Path, report: Report):
    """D4: 每题 ≥ 4 张图。"""
    solve_dir = workspace / "求解"
    if not solve_dir.exists():
        return
    for q_dir in solve_dir.glob("问题*"):
        if not q_dir.is_dir():
            continue
        fig_dir = q_dir / "图片"
        if not fig_dir.exists():
            report.add(f"D4 {q_dir.name} ≥ 4 张图", False, "无 图片/ 目录")
            continue
        figs = [p for p in fig_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf"}]
        report.add(
            f"D4 {q_dir.name} ≥ 4 张图",
            len(figs) >= 4,
            f"找到 {len(figs)} 张",
        )


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python auto_verify.py <工作区路径>")
        return 2

    workspace = Path(sys.argv[1])
    if not workspace.exists():
        print(f"❌ 工作区不存在: {workspace}")
        return 2

    report = Report()
    print("🔍 mma 自动机械验收(对应 eval-checklist 的 A/C/D + F2.1)")
    print(f"📂 工作区: {workspace}\n")

    check_compile(workspace, report)
    check_pdf_exists(workspace, report)
    check_no_toc(workspace, report)
    check_symbols(workspace, report)
    check_ai_declaration(workspace, report)
    check_chapter_files(workspace, report)
    check_figures(workspace, report)

    report.print()
    return 0 if all(r.passed for r in report.results) else 1


if __name__ == "__main__":
    sys.exit(main())
