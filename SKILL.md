---
name: mma
description: |
  数学建模竞赛端到端 agent skill —— 自用版. Use this skill when the user says
  "开始建模"、"求解数模题"、"做这道数模题"、"生成建模论文"、"出论文 PDF"、
  "国赛/美赛/MCM/ICM/CUMCM 求解" or pastes a math modeling problem and asks
  to solve it. Triggers on phrases like "出论文"、"跑代码写论文"、"帮我做这道
  数模题"、"完整解题"。

  6 阶段工作流 + 4 角色分工(建模手/代码手/论文手/验收手)。LaTeX 模板已对齐
  **2026 年全国大学生数学建模竞赛论文格式规范** + **AI 工具使用规定**(2026 试行):
  承诺书 + 编号专用页(纸质版) / 跳过(电子版) / AI 工具使用声明(在参考文献前)
  / 附录含程序使用说明 + 支撑材料说明。

  Do NOT use for: general data analysis, one-off Python scripts, or research
  questions that don't lead to a 论文.pdf deliverable.
metadata:
  version: "3.0"  # v3:统一 6 阶段编号 + 快速模式 + 局部修改 + 新章节结构
  category: competition-workflow
  scope: user
  spec:
    paper: 2026 年《全国大学生数学建模竞赛论文格式规范》
    ai: 2026 年《全国大学生数学建模竞赛人工智能工具使用规定》(试行)
    rules: 2026 年《全国大学生数学建模竞赛参赛规则》(修订稿)
  extends:
    - workflow: references/workflow.md
    - paper-spec: references/paper-spec.md
    - role-prompts: references/role-prompts.md
    - decision-tree: references/model-decision-tree.md
    - code-template: references/code-template.py
    - eval-checklist: references/eval-checklist.md
    - ai-declaration-template: 论文/0.AI声明.tex
    - ai-detail-md-template: references/AI工具使用详情-template.md
    - ai-detail-tex-template: 论文/AI工具使用详情-template.tex
    - scripts: references/scripts/
  related-skills:
    - bzd-modeling-ideas: Stage 2 已升级到 bzd 的 8 段结构(整题主线 + 跨问题联动链)
    - scipilot-figure-skill: 代码手 Stage 3 绘图原则已集成(15 条避坑 + setup_style 配环境)
---

# Math Modeling Agent (mma) — v3

数学建模竞赛端到端解题 + 论文写作 agent。自用版,设计目标:
**跑出来能交、能得分的论文。**

---

## ⚡ 快速模式(单次任务直接走)

跳过完整 6 阶段,直接进入指定阶段或局部修改:

| 用户说 | 跳到 | 说明 |
|--------|------|------|
| "开始建模" / "求解这道题" | Stage 1 | 完整流程(默认) |
| "**只写论文**" / "跳过求解" | Stage 4 | 假设 求解/ 已就绪,直接写 LaTeX |
| "**只跑代码**" / "求解" | Stage 3 | 假设 求解计划.md 已就绪,只跑 py |
| "**只验收**" / "检查" | Stage 5 | 假设 论文.tex 已就绪,跑 eval-checklist |
| "**只出 PDF**" / "编译" | Stage 6 | 跑 build.ps1 编译两份 PDF |
| "**改这一章**" / "改 XX" | 局部修改 | 改单个 .tex(7.优缺点评价 等) |
| "**改格式**" / "改排版" | 局部修改 + 编译 | 调 format.cls 后跑 build.ps1 |
| "**加一条参考文献**" | 局部修改 | 改 9.参考文献.tex + 加 \cite |
| "**加一张图**" / "换图" | 局部修改 + 编译 | 改 .tex 的 \includegraphics + 跑 build.ps1 |
| "**重出 PDF**" | Stage 6 | 同 "只出 PDF" |

> 快速模式 = 跳到对应阶段 + 跳过上一阶段产物检查(用户自担保)。

---

## 4 个角色(内部分工)

mma 不真正启多进程,而是在每个阶段**以一个角色视角**去执行,
角色 prompt 模板见 `references/role-prompts.md`:

| 角色 | 职责 | 触发阶段 |
|------|------|---------|
| **建模手** | 读题、问题分类、模型比选、出求解计划 | Stage 1-2 |
| **代码手** | 实现求解、画图、灵敏度分析 | Stage 3 |
| **论文手** | LaTeX 写作、严格遵守硬规则 | Stage 4 |
| **验收手** | 编译验证、数值一致性、文本泄漏 | Stage 5-6 |

这样分的好处:每阶段 prompt 边界清晰,失败时容易定位是哪个角色没做好。

---

## 6 阶段流程(完整模式)

详细步骤见 `references/workflow.md`。

| Stage | 角色 | 关键产物 | 退出条件 |
|-------|------|---------|---------|
| 1. 读题 | 建模手 | 问题列表 N、数据概览(每个文件 shape/dtypes/缺失率) | N 个问题 + 类型分类确认 |
| 2. 建模 | 建模手 | **8 段建模思路**(bzd 风格) → 用户拍板 → 求解计划 | 建模思路.md + 求解计划.md + 用户确认 |
| 3. 求解 | 代码手 | 每个问题一个 py + 4-6 张图 + 结果 csv + 预处理数据.csv | 所有 py 运行无错 + 图够数 |
| 4. 写作 | 论文手 | 11 个 .tex(0.摘要 + 1.问题重述 + 2.问题分析 + 3.假设 + 4.符号 + 5.建立求解 + 6.检验 + 7.优缺点 + 0.AI声明 + 9.参考文献 + 10.附录) | 全部 .tex 写完 + 自检通过 |
| 5. 验收 | 验收手 | 编译通过 + 数值一致 + 硬规则全过 | eval-checklist 全过(38+ 项) |
| 6. 出 PDF | 验收手 | `论文/论文.pdf` + `论文/电子版.pdf` | 两份 PDF 存在且能打开 |

---

## 触发

用户说以下任一即启动(自动识别快速模式/完整模式):

**完整流程触发词**:
- "开始建模" / "求解数模题" / "做这道数模题" / "出论文"
- "生成建模论文" / "出论文 PDF"
- "国赛/美赛/MCM/ICM/CUMCM 求解"
- 粘贴赛题 PDF + 让我做

**快速模式触发词**(见上节"快速模式")。

---

## 必要输入(启动前确认)

1. `题目/` 目录有 PDF/DOCX
2. `数据/` 目录有 xlsx/csv(如果有附件)
3. 建模类型(优化/评价/预测/分类/机理)用户是否已知

**自动检查**:跑 `references/scripts/check_input.ps1` 一键检查前两项。

**缺任一就停下等用户补齐**,不要瞎猜。

---

## 论文结构(v3 章节命名,2026 Word 模板对齐)

```
论文/
├── 0.摘要.tex              ← Stage 4 第 1 个写
├── 1.问题重述.tex          ← (1.引言 已重命名)
├── 2.问题分析.tex          ← (2.总体分析 已重命名,加 1.1/1.2/1.3 + 整体思路图)
├── 3.模型假设.tex
├── 4.符号说明.tex
├── 5.模型的建立与求解.tex  ← 4 个 \subsection(问题 1/2/3/4)
│   ├── 5.1.1.数据预处理.tex         ← 5.x.1:数据预处理
│   ├── 5.1.2.XXX模型的建立.tex      ← 5.x.2:建模
│   ├── 5.1.3.XXX模型的求解.tex      ← 5.x.3:求解
│   ├── 5.1.4.XXX模型的检验.tex      ← 5.x.4:检验
│   ├── 5.1.5.XXX结果的分析.tex      ← 5.x.5:分析
│   ├── 5.2.x ~ 5.4.x                ← 同结构,问题 2/3/4
├── 6.模型检验.tex          ← 6.1 误差 / 6.2 灵敏度 / 6.3 稳健性
├── 7.模型优缺点评价.tex    ← (7.模型评价 已重命名)
│                              7.1 优点 / 7.2 缺点 / 7.3 改进
├── 0.AI声明.tex            ← AI 工具使用声明(放 9.参考文献 之前)
├── 9.参考文献.tex
├── 10.附录.tex             ← 附录 1 文件列表 / 附录 2 源代码 / 附录 3 其他
├── 论文.tex                ← 纸质版入口
├── 电子版.tex              ← 电子版入口(跳过承诺书+编号页)
├── format.cls              ← 2026 规范
└── fonts/                  ← SourceHanSerifCN
```

**8.章已删除**(并入 7.3 改进)。

---

## 关键引用(按需读)

- **完整工作流** → `references/workflow.md`
- **论文硬规则** → `references/paper-spec.md`
- **角色 prompt 模板** → `references/role-prompts.md`
- **模型选择决策树** → `references/model-decision-tree.md`
- **验收清单** → `references/eval-checklist.md`(已含 2026 规范检查项)
- **求解代码模板** → `references/code-template.py`
- **AI 工具使用声明模板** → `论文/0.AI声明.tex`(放在 9.参考文献.tex 之前)
- **AI 工具使用详情模板**(Markdown 版) → `references/AI工具使用详情-template.md`
- **AI 工具使用详情模板**(LaTeX 版,直接编译) → `论文/AI工具使用详情-template.tex`
- **AI 详情 PDF 编译脚本** → `references/scripts/build_ai_detail.ps1`(xelatex 编译,输出到 支撑材料/)
- **辅助脚本** → `references/scripts/`(check_input / build / auto_verify / build_ai_detail)

---

## 目录约定(项目工作区)

每个赛题建一个工作区,根目录结构:

```
<工作区>/
├── 题目/                    # 赛题 PDF/DOCX
├── 数据/                    # 附件 xlsx/csv
├── 求解/
│   ├── 求解计划.md
│   ├── 建模思路.md          # Stage 2 输出
│   ├── 预处理数据.csv       # 问题1 输出,后续共用
│   ├── 预处理数据.py
│   └── 问题X/
│       ├── 问题X_xxx.py     # 中文命名
│       ├── 图片/
│       └── 结果/
├── 论文/                    # 从 mma skill 论文/ 模板复制
│   ├── 论文.tex              # 纸质版入口(含承诺书+编号页)
│   ├── 电子版.tex            # 电子版入口(跳过前两页)
│   ├── format.cls
│   ├── 0-10 章.tex
│   ├── 0.AI声明.tex          # AI 工具使用声明(放 9.参考文献.tex 之前)
│   └── fonts/                # 已自带,无需配置
└── 支撑材料/                 # 单独提交的压缩包(2026 规范第十一条)
    ├── AI工具使用详情.pdf    # 必须(2026 AI 规定第 4 条)
    ├── 附件.xlsx
    ├── 求解/                # 全部源代码
    └── 论文/AI工具使用详情.pdf
```

**LaTeX 编译必须用 xelatex**(format.cls 依赖 ctex + SourceHanSerif)。

**两套编译配置**(2026 规范第十条):
- `xelatex 论文.tex` → `论文.pdf`(纸质版提交,含承诺书+编号页)
- `xelatex 电子版.tex` → `电子版.pdf`(电子版提交,跳过承诺书+编号页)
- `xelatex AI工具使用详情.tex` → `AI工具使用详情.pdf`(放 支撑材料/,2026 AI 规定第 4 条)

**自动编译**:跑 `references/scripts/build.ps1` 一键编译**三份 PDF**(论文版 + 电子版 + AI 详情,如果 AI 详情 .tex 存在)。

**AI 详情 PDF 单独编译**:`pwsh references/scripts/build_ai_detail.ps1 -WorkSpace <工作区>`。

---

## Windows (win32) 平台注意

- LaTeX:`xelatex -interaction=nonstopmode 论文.tex`
- Python:`python`(不是 `python3`),用 `py -3` 调用本地 Python
- 字体:`论文/fonts/SourceHanSerifCN-*.otf`(已自带)
- 路径分隔符:`\`(Windows),LaTeX 用 `/`(跨平台)
- 文件校验:`Test-Path 论文/论文.pdf`

---

## 与 li-mrite / li-mtrie / bzd-modeling-ideas 的关系

mma 继承自 li-mrite(早期 2024 模板,硬规则一致),已升级到 **2026 全国数模规范**:

- ✅ 显式 4 角色分工(prompt 层面,不是进程层面)
- ✅ 独立"验收"阶段 + 结构化验收清单
- ✅ 模型选择决策树(快速匹配候选模型)
- ✅ **2026 规范升级**:format.cls 来自 li-mtrie(2026),支持 `withpreface` / `electronic` 双模式
- ✅ **2026 规范第 3 条**:AI 工具使用声明模板(`论文/0.AI声明.tex`)
- ✅ **2026 规范第 4 条**:AI 工具使用详情模板(`references/AI工具使用详情-template.md`)
- ✅ **2026 规范第 5/11 条**:附录含「程序使用说明」+「支撑材料说明」两段固定说明
- ✅ **v3 章节重命名**:1.引言→1.问题重述、2.总体分析→2.问题分析、7.模型评价→7.模型优缺点评价
- ✅ **v3 5.x 子节拆分**:每个问题 5 个子节(数据预处理/建模/求解/检验/结果分析)
- ✅ **v3 删 8 章**:并入 7.3 改进
- ⏸ 暂不引入:HIL、RAG、多模型 fallback(自用不需要)
- ⏸ 暂不引入:Typst 替代 LaTeX(自用,稳优先)

---

## 失败处理(常见)

| 情况 | 处理 |
|------|------|
| 数据缺失>20% | KNN 插补或删除,不静默丢 |
| 模型过拟合 | 降低 max_depth/增加正则化 |
| 预测值异常 | 检查数据泄露 |
| 交叉验证方差大 | 增加折数或重复 CV |
| xelatex Error | grep 看具体错;连续 2 次失败切换策略(看 build.log) |
| Overfull/Underfull | 调列宽/换行;2 次修不好允许 `\\newline` |
| py 脚本报错 | 修 → 重跑,通过再下一问 |
| 用户拍板耗时 | 给"默认方案"提示,用户不选就按默认走 |
| 局部改 .tex 编译失败 | 回到 git HEAD 看 diff,回滚后重试 |

---

## ⚠️ 参赛规则合规(2026 修订稿)

mma 同样**仅用于赛后整理论文**,不参与竞赛期间的赛题解答。用户在竞赛期间必须遵守:

| 条款 | 含义 |
|------|------|
| 第 3 条 | 指导教师竞赛期间不得指导(包括解释赛题/选题/解题建议/参考资料/修改论文) |
| 第 4 条 | 引用必须规范,**不得大篇幅照抄** |
| 第 5 条 | 严禁与队外交流;**不得在贴吧/QQ群/微信群/知乎/小红书/CSDN/GitHub 等平台讨论赛题** |
| 第 6 条 | AI 工具可用作辅助,但**参赛队对作品负全部责任** |

**违规后果**:取消评奖 + 指导教师两年禁赛 + 通报批评 + 赛区缩减送全国评阅论文数量。

完整 4 角色 prompt + Stage 5 验收清单(已含 F.4 参赛规则检查项)见 `references/`。

---

## Examples

**Input**: 用户说"开始建模",工作区已放 2024 国赛 B 题 PDF + 附件 xlsx。

**Output**: 启动 Stage 1 → 跑 check_input.ps1 验证输入 → 读题读数据 → 打印"识别到 4 个问题..." → 列出每问候选模型对比表 → 等待用户选 → 按选定方案求解 → 写论文 → 跑 auto_verify.ps1 验收 → 跑 build.ps1 出 PDF。

**Input**: 用户说"只写论文"(题和数据已就位,求解已完成)。

**Output**: 跳到 Stage 4,按 `references/paper-spec.md` 11 章规范逐章写 LaTeX → Stage 5 验收 → Stage 6 跑 build.ps1 出 PDF。

**Input**: 用户说"改一下 7.优缺点评价"。

**Output**: 改 7.模型优缺点评价.tex → 跑 build.ps1 重出 PDF → 展示 diff。
