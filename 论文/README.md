# 论文/ 目录工作流

> **从 mma skill 论文模板到完整论文的 5 步走法**(Stage 4)

---

## 1. 复制模板到新工作区

每个新题建一个工作区,目录结构见 `SKILL.md` 的"目录约定"。

```powershell
# 把 mma skill 论文模板整个复制到新工作区
Copy-Item -Recurse "C:\...\mma\论文" "<新工作区>\论文"
```

---

## 2. 5.x 子节命名约定(11 个 .tex + 20 个 5.X.Y)

```
论文/
├── 0.摘要.tex
├── 1.问题重述.tex
├── 2.问题分析.tex
├── 3.模型假设.tex
├── 4.符号说明.tex
├── 5.模型的建立与求解.tex        ← 4 个 \subsection(问题 1/2/3/4)
│   ├── 5.1.1.数据预处理.tex         ← 5.x.1:数据预处理(仅问题 1 必填)
│   ├── 5.1.2.XXX模型的建立.tex      ← 5.x.2:建模
│   ├── 5.1.3.XXX模型的求解.tex      ← 5.x.3:求解 + 4 张图
│   ├── 5.1.4.XXX模型的检验.tex      ← 5.x.4:检验
│   ├── 5.1.5.XXX结果的分析.tex      ← 5.x.5:分析
│   ├── 5.2.1 ~ 5.2.5               ← 同结构,问题 2
│   ├── 5.3.1 ~ 5.3.5               ← 问题 3
│   └── 5.4.1 ~ 5.4.5               ← 问题 4
├── 6.模型检验.tex                   ← 6.1/6.2/6.3
├── 7.模型优缺点评价.tex             ← 7.1/7.2/7.3
├── 0.AI声明.tex                     ← 在 9.参考文献.tex 之前
├── 9.参考文献.tex
├── 10.附录.tex                      ← 附录 1/2/3
├── 论文.tex / 电子版.tex / format.cls
└── fonts/SourceHanSerifCN-*.otf    ← 字体(在 fonts/ 子目录)
```

**图片命名约定**(与 python 输出对齐,见 `references/code-template.py` 顶部):

| 文件名 | 用途 |
|--------|------|
| `1_*.png` | 散点图 / 拟合图 |
| `2_*.png` | 预测 vs 实际图 |
| `3_*.png` | 残差图 |
| `4_*.png` | 系数 + 特征重要性图 |
| `5_*.png` | 误差分析图(可选) |
| `6_*.png` | 多目标 Pareto 前沿(可选) |

---

## 3. 5.X 子节工作流(每个问题)

以问题 1 为例,问题 2/3/4 同理:

### Step 1:数据预处理(仅问题 1)
- 改 `5.1.1.数据预处理.tex`
- 缺失/异常处理 + 标准化公式 + 处理结果统计表
- 参考 `references/paper-spec.md` 的"5.X.1 数据预处理"段

### Step 2:模型建立
- 改 `5.1.2.XXX模型的建立.tex`(【XXX】改为你的模型名,如"多元线性回归")
- 流程图(TikZ 9 框模板已就绪)+ 算法对比表 + 步骤 1-4 推导
- 参考 `references/paper-spec.md` 的"5.X.2 建模"段

### Step 3:模型求解
- 改 `5.1.3.XXX模型的求解.tex`
- 引用 4 张图(`1_Y浓度vs孕周_BMI.png` / `2_预测vs实际.png` / `3_残差图.png` / `4_系数_特征重要性.png`)
- 填结果表(指标 / 主方法 / 对比方法 / 说明)
- 参考 `references/paper-spec.md` 的"5.X.3 求解"段

### Step 4:模型检验
- 改 `5.1.4.XXX模型的检验.tex`
- 5 折 CV + 误差 + 灵敏度 + 稳健性
- 参考 `references/paper-spec.md` 的"5.X.4 检验"段

### Step 5:结果分析
- 改 `5.1.5.XXX结果的分析.tex`
- 关键发现 + 与对比方法对比 + 总结
- 参考 `references/paper-spec.md` 的"5.X.5 分析"段

---

## 4. 5.2/5.3/5.4 stub 工作流

`5.2.x ~ 5.4.x` 共 15 个 .tex 是 stub 模板(几百字节提示)。

最快做法:**复制 5.1.x → 5.X.x,然后改模型名/数据/图表**。

```powershell
# 例:复制问题 1 模板到问题 2
Copy-Item "论文/5.1.1.数据预处理.tex" "论文/5.2.1.数据预处理.tex"
Copy-Item "论文/5.1.2.XXX模型的建立.tex" "论文/5.2.2.XXX模型的建立.tex"
# ... 然后用编辑器替换 5.1 → 5.2,问题 1 → 问题 2,【XXX】→ 你的模型名
```

---

## 5. 编译

```powershell
# 必备:设 PYTHONIOENCODING 避免 pandas 乱码
$env:PYTHONIOENCODING = "utf-8"

# 一键编译(论文版 + 电子版 + AI 详情)
py -3 "..\mma\references\scripts\build.ps1" -WorkSpace "."
```

产出 3 份 PDF:
- `论文/论文.pdf`(纸质版)
- `论文/电子版.pdf`(电子版)
- `支撑材料/AI工具使用详情.pdf`

---

## 6. 验收

```powershell
py -3 "..\mma\references\scripts\auto_verify.py" "."
# 看 38+ 项 PASS/FAIL,失败项照文件:行提示
```

---

## 7. 常见坑

| 坑 | 解决 |
|---|------|
| pandas 读 utf-8 CSV 列名乱码 | 用 `data_utils.read_csv_safe()`,不要直接 `pd.read_csv()` |
| PowerShell 打印 emoji/中文乱码 | 脚本顶部 `from data_utils import ensure_utf8_stdout; ensure_utf8_stdout()` |
| xelatex 找不到字体 | 字体必须在 `fonts/SourceHanSerifCN-*.otf`(不是论文/ 根目录) |
| .tex 引用图片找不到 | 用"图片命名约定"段规定的命名(见上) |
| 编译有 `\@newl@bel` 错误但 PDF 生成 | 可能是某处 \label 用法错,但 xelatex 已恢复,看 PDF 确认 |
| AI 工具使用详情 .tex 编译失败 | 必须用 `\setCJKfamilyfont{song}` 不用 `\setCJKmainfont`(见 `AI工具使用详情-template.tex`) |

---

## 8. 强制规范(v3,v3 必填)

- 论文**无目录**(`\tableofcontents` 不允许)
- 8.章已删除(并入 7.3 改进)
- 5.X 子节共 5 个,不是 2 个
- 摘要 ≤ 900 字,1 页
- AI 工具使用声明在参考文献前
- 附录 1 文件列表 / 附录 2 源代码 / 附录 3 其他

详细:见 `references/writing-rules.md` 和 `references/chapter-structure.md`。
