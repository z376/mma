# mma Skill 更新日志

## v3.0(2026-08-23) — 流程升级 + 2026 Word 模板对齐

### 重大变化

#### 1. 流程编号统一
- 之前:SKILL.md 6 阶段(1-6)+ workflow.md 5 步(Step 0-5),编号对不上
- 现在:**6 阶段统一 1-6**(Stage 1 读题 / Stage 2 建模 / Stage 3 求解 / Stage 4 写作 / Stage 5 验收 / Stage 6 出 PDF)

#### 2. 快速模式(单次任务直接走)
- "只写论文" → 跳 Stage 4
- "只跑代码" → 跳 Stage 3
- "只验收" → 跳 Stage 5
- "只出 PDF" / "编译" → 跳 Stage 6
- "改 XX" / "改这一章" → 局部修改 + Stage 6
- "改格式" / "改排版" → 局部修改 + Stage 6

#### 3. 论文章节重命名(2026 Word 模板对齐)
- `1.引言.tex` → `1.问题重述.tex`
- `2.总体分析.tex` → `2.问题分析.tex`(加 1.1/1.2/1.3/1.4 + 整体思路图)
- `6.模型检验.tex` → 6.1 误差 / 6.2 灵敏度 / 6.3 稳健性
- `7.模型评价.tex` → `7.模型优缺点评价.tex`(7.1 优点 / 7.2 缺点 / 7.3 改进)
- `8.模型改进推广.tex` → **删除**(并入 7.3 改进)

#### 4. 5.x 子节拆分
- 之前:每问 2 个子节(5.X.1.分析与准备 + 5.X.2.建模与求解)
- 现在:每问 **5 个子节**:
  - `5.X.1.数据预处理.tex`(仅问题 1)
  - `5.X.2.XXX 模型的建立.tex`
  - `5.X.3.XXX 模型的求解.tex`
  - `5.X.4.XXX 模型的检验.tex`
  - `5.X.5.XXX 结果的分析.tex`
- 5.2.x / 5.3.x / 5.4.x 同步

#### 5. 附录结构调整
- 之前:`\subsubsection*{一、程序使用说明}` + `\subsubsection*{二、支撑材料说明}` + `\subsubsection*{三、运行环境}`
- 现在:附录 1(文件列表)/ 附录 2(源代码 + AI 工具标注)/ 附录 3(其他)+ 支撑材料说明 + 运行环境

#### 6. format.cls 调整
- 行距 1.38 → 1.5(贴近 2026 Word 模板观感)

### 新增

- `references/scripts/check_input.py` — 启动前自动检查 题目/数据/ 是否就位
- `references/scripts/build.ps1` — 一键编译论文.tex(纸质版)+ 电子版.tex(电子版) + AI工具使用详情.tex
- `references/scripts/build_ai_detail.ps1` — 单独编译 AI 工具使用详情 PDF(放 支撑材料/)
- `references/scripts/auto_verify.py` — 自动跑 eval-checklist 机械部分(A 编译 + C 硬规则 + D 完整性 + F2.1 AI 声明)
- `论文/AI工具使用详情-template.tex` — AI 详情 LaTeX 模板(对应 .md 版,直接 xelatex 编译,无需 pandoc)
- `CHANGELOG.md` — 本文件

### 修改

- `SKILL.md` — 重写,添加"快速模式"表 + v3 章节结构 + scripts 引用
- `references/workflow.md` — 重写,Stage 1-6 编号 + 快速模式分支 + v3 章节名 + Stage 间回退/并行规则
- `references/role-prompts.md` — Stage 4/5 prompt 模板更新(v3 11 章 + 5.x 子节)
- `references/eval-checklist.md` — D 节 / F.1 节更新(对应 v3 必填项 + 附录 1/2/3 命名)
- `examples/README.md` — 同步 v3 结构 + 快速模式 + scripts 引用

### 不破坏向后兼容

- 老章节名(1.引言/2.总体分析/7.模型评价)在文档中作为"重命名自"提示保留
- 老 5.X.1 + 5.X.2 结构已替换为 5.X.1-5.X.5
- 8.章已删除,代码 .tex 移除(并入 7.3)

---

## v2.0(2024 模板)

- 4 角色分工(建模手/代码手/论文手/验收手)
- 5 步流程(读题 → 建模 → 求解 → 写作 → 出 PDF)
- 6 阶段流程(Stage 1-6 引入)
- 8 段建模思路(bzd 风格)
- eval-checklist 38+ 项
- 2024 章节结构(1.引言 + 2.总体分析 + 5.X.1+5.X.2 + 7.模型评价 + 8.模型改进推广)
