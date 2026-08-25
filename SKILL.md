---
name: mma
description: |
  数学建模竞赛端到端 agent skill —— 自用版. Use when the user pastes a 数模赛题
  and asks to solve it, says "开始建模" / "出论文" / "改格式" / "只写论文",
  or mentions 国赛/美赛/MCM/ICM/CUMCM.

  6 阶段工作流(读题→建模→求解→写作→验收→出 PDF)+ 4 角色(建模手/代码手/论文手/验收手)。
  LaTeX 模板已对齐 2026 年国赛论文格式规范 + AI 工具使用规定。

  Do NOT use for: general data analysis, one-off Python scripts, or research
  questions that don't lead to a 论文.pdf deliverable.
metadata:
  version: "3.3"  # v3.3:新增 references/求解计划-template.md + examples/2025-C题-完整案例 + data_utils + 写作流程审计瘦身
  category: competition-workflow
  scope: user
  spec:
    paper: 2026 年《全国大学生数学建模竞赛论文格式规范》
    ai: 2026 年《全国大学生数学建模竞赛人工智能工具使用规定》(试行)
    rules: 2026 年《全国大学生数学建模竞赛参赛规则》(修订稿)
  extends:
    - workflow: references/workflow.md
    - chapter-structure: references/chapter-structure.md  # 单一来源:章节命名
    - writing-rules: references/writing-rules.md          # 单一来源:硬规则 + 硬性数字
    - paper-spec: references/paper-spec.md
    - role-prompts: references/role-prompts.md
    - decision-tree: references/model-decision-tree.md
    - code-template: references/code-template.py
    - data-utils: references/scripts/data_utils.py        # 跨题通用数据工具(read_csv_safe 等)
    - solve-plan: references/求解计划-template.md         # 求解计划模板(Stage 2 收尾)
    - eval-checklist: references/eval-checklist.md
    - ai-declaration-template: 论文/0.AI声明.tex
    - ai-detail-md-template: references/AI工具使用详情-template.md
    - ai-detail-tex-template: 论文/AI工具使用详情-template.tex
    - scripts: references/scripts/
  examples:
    - 2025-C题-完整案例: examples/2025-C题-完整案例/(4 个问题端到端:建模思路 + 求解代码 + 15 张图 + 11 个 csv + 实填 .tex)
  related-skills:
    - bzd-modeling-ideas: Stage 2 升级到 bzd 8 段结构
    - scipilot-figure-skill: 代码手 Stage 3 绘图原则已集成
---

# Math Modeling Agent (mma) — v3.1

数学建模竞赛端到端解题 + 论文写作 agent。自用版,设计目标:
**跑出来能交、能得分的论文。**

---

## 触发分支

| 用户说 | 跳到 | 假设 |
|--------|------|------|
| "开始建模" / "做这道题" / 粘贴赛题 | Stage 1 | 完整 6 阶段 |
| "只写论文" / "跳过求解" | Stage 4 | `求解/` 已就绪 |
| "只跑代码" / "求解" | Stage 3 | `求解计划.md` 已就绪 |
| "只验收" / "检查" | Stage 5 | 论文 .tex 已就绪 |
| "只出 PDF" / "改格式" / "改 XX" | Stage 6 | 论文 .tex 已就绪 |

> 跳级 = 用户自担保上一阶段产物。`references/overview.md` 给完整模式分支表。

---

## 6 阶段流程

| Stage | 角色 | 关键产物 | 退出条件 |
|-------|------|---------|---------|
| 1. 读题 | 建模手 | 问题列表 N + 数据概览 | N + 类型分类确认 |
| 2. 建模 | 建模手 | 8 段建模思路(bzd) → 求解计划 | 用户拍板 |
| 3. 求解 | 代码手 | 每问 py + 4-6 图 + 结果 csv | 全部 py 通过 |
| 4. 写作 | 论文手 | 11 个 .tex | 自检通过(eval-checklist D 节) |
| 5. 验收 | 验收手 | 编译 + 数值 + 硬规则全过 | 38+ 项 PASS |
| 6. 出 PDF | 验收手 | `论文.pdf` + `电子版.pdf` + `支撑材料/AI工具使用详情.pdf` | 3 份 PDF 存在 |

---

## 必要准备(运行环境,Windows)

| 工具 | 用途 | 检查 |
|------|------|------|
| **PowerShell 5.1** 或 PowerShell 7+ | 跑 .ps1 脚本 | `$PSVersionTable.PSVersion` |
| **Python 3.10+** | 跑求解 .py | `py -3 --version` |
| **xelatex**(MiKTeX / TeX Live) | 编译论文 PDF | `xelatex --version` |
| **Git** | 推送到 GitHub | `git --version` |
| **字体** | 思源宋体 OTF | `论文/fonts/SourceHanSerifCN-*.otf` |

**必设环境变量**(避免 pandas 读 utf-8 CSV 乱码):
```powershell
$env:PYTHONIOENCODING = "utf-8"
```
在每次跑 `py` 之前设(或加到 `$PROFILE` 里)。

**Python 脚本开头必加**(避免 stdout 乱码 + emoji 编码失败):
```python
import sys; sys.path.insert(0, r"<mma>\references\scripts")
from data_utils import ensure_utf8_stdout, read_csv_safe, save_csv
ensure_utf8_stdout()
```

---

## 必要输入(题目材料)

1. `题目/` 有 PDF/DOCX
2. `数据/` 有 xlsx/csv(无附件题可空)
3. 建模类型用户是否已知(可选)

**自动检查**:`py -3 references/scripts/check_input.py <工作区>`

缺任一就停下等用户补齐。

---

## 关键引用

- **章节命名**(v3,单一来源) → `references/chapter-structure.md`
- **硬规则 + 硬性数字**(单一来源) → `references/writing-rules.md`
- **完整工作流** → `references/workflow.md`
- **论文详细规范** → `references/paper-spec.md`
- **角色 prompt** → `references/role-prompts.md`
- **模型决策树** → `references/model-decision-tree.md`
- **求解计划模板**(Stage 2 收尾) → `references/求解计划-template.md`
- **验收清单** → `references/eval-checklist.md`
- **辅助脚本** → `references/scripts/`(check_input / build / build_ai_detail / auto_verify)
- **数据工具** → `references/scripts/data_utils.py`(read_csv_safe / save_csv / ensure_utf8_stdout)
- **完整案例** → `examples/2025-C题-完整案例/`(2025 国赛 C 题 4 个问题端到端,可参考)

---

## 编译(出 PDF)

```powershell
powershell -File references/scripts/build.ps1 -WorkSpace <工作区>
```

**产出 3 份 PDF**(自动):
- `论文/论文.pdf`(纸质版,含承诺书+编号页)
- `论文/电子版.pdf`(电子版,跳过前两页)
- `支撑材料/AI工具使用详情.pdf`(2026 AI 规定第 4 条必交,需先填 `论文/AI工具使用详情.tex`)

详细工作区目录、失败处理、参赛规则合规等内容见 `references/workflow.md`。

---

## ⚠️ 参赛规则合规(2026 修订稿)

mma 仅用于赛后整理论文。竞赛期间必须遵守:

- 第 3 条:指导教师不得指导
- 第 4 条:引用必须规范,不得大篇幅照抄
- 第 5 条:严禁与队外交流(贴吧/QQ群/微信群/知乎/小红书/CSDN/GitHub 等)
- 第 6 条:AI 工具可用作辅助,但**参赛队对作品负全部责任**

**违规后果**:取消评奖 + 指导教师两年禁赛 + 通报批评。
