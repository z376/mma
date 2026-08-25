# 2025 国赛 C 题 — 完整案例(NIPT 时点选择与胎儿异常判定)

> **用途:** mma skill 端到端实战案例。从空目录到 3 份 PDF 的完整 6 阶段。

---

## 案例信息

- **题目:** 2025 高教社杯全国大学生数学建模竞赛 C 题
- **赛题:** NIPT 时点选择与胎儿异常判定
- **测试版本:** mma skill v3.3 (58b9059)
- **测试时间:** 2026-08-25
- **数据规模:** 男胎 1082 条 + 女胎 605 条 × 31 列(2 sheet)

## 4 个问题 + 选定方案

| # | 题目问题 | 类型 | 主方案 |
|---|---------|------|--------|
| 1 | Y 浓度 与 孕周/BMI 关系模型 | 回归 | OLS(可解释)+ 随机森林(精度) |
| 2 | BMI 分组 + 最佳 NIPT 时点 | 聚类+优化 | 决策树分组 + 风险最小化 |
| 3 | 多因素 + 误差 + 达标比例 | 多目标优化 | 加权求和 + ε-约束(没有 pymoo) |
| 4 | 女胎异常判定 | 分类 | Logistic + 随机森林(Z 值衍生标签) |

## 关键结论

- **问题 1:** OLS R²=0.068(RF 5 折 CV R²=0.222);显著变量:孕周(+)、年龄(-)、体重(-)
- **问题 2:** 决策树自动阈值 [30.5, 34.0];3 组,最佳时点 14 周;±10% 扰动 ±1.5 周
- **问题 3:** 5 组多因素(BMI+年龄+体重)聚类;最佳时点 16.5-24 周
- **问题 4:** Logistic / RF 5 折 CV AUC=1.0(合成标签,可完美还原 |Z|>3 规则)

## 目录结构

```
2025-C题-完整案例/
├── README.md                (本文件)
├── 测试报告.md              (Stage 1-6 完整测试报告)
├── 求解/
│   ├── utils.py              (跨题通用数据工具)
│   ├── 预处理数据.py         (Stage 3 Step 0:数据清洗)
│   ├── 预处理数据.csv         (预处理结果,问题 1-4 共享)
│   ├── 建模思路.md            (Stage 2 8 段 bzd 思路)
│   ├── 问题1/
│   │   ├── 问题1_Y浓度回归.py
│   │   ├── 图片/             (4 张图)
│   │   └── 结果/             (4 个 csv)
│   ├── 问题2/问题2_BMI分组.py + 图片/ + 结果/
│   ├── 问题3/问题3_多目标优化.py + 图片/ + 结果/
│   └── 问题4/问题4_女胎异常判定.py + 图片/ + 结果/
└── 论文/
    └── 5.1.3.XXX模型的求解.tex    (实填示例:展示如何把求解结果写到 .tex)
```

## 复用方式

### 1. 看 mma 流程是怎么跑的
按 `求解/` 目录的 `py` 文件顺序看,每个文件顶部都有:
- 路径计算
- 数据加载
- 模型/算法
- 4-6 张图保存到 `图片/`
- 结果 csv 保存到 `结果/`
- 关键指标 print 出来

### 2. 抄代码到新题
- `utils.py` → 直接 `from utils import read_csv_safe, save_csv, ensure_utf8_stdout`
- `预处理数据.py` → 改数据类型转换 + 特征工程
- 4 个问题的 `py` → 改模型/算法部分

### 3. 抄 .tex 写法
- `论文/5.1.3.XXX模型的求解.tex` → 看如何把 R²/RMSE/特征重要性填到 LaTeX
- 图片引用格式:`\includegraphics[width=0.85\textwidth]{../求解/问题1/图片/1_Y浓度vs孕周_BMI.png}`
- 表格用 `longtable`,数值用 `$R^2 = 0.068$`、`5 折 CV R² = 0.222`

## 复现(在自己工作区)

```powershell
# 1. 准备
$env:PYTHONIOENCODING = "utf-8"
mkdir <新工作区>; cd <新工作区>
# 把 mma 论文模板整个复制过来
Copy-Item -Recurse "<mma>\论文" ".\论文"

# 2. 准备数据
mkdir 题目, 数据
Copy-Item "<题目>.pdf" "题目\"
Copy-Item "<附件>.xlsx" "数据\"

# 3. 跑 Stage 1-2
py -3 "<mma>\references\scripts\check_input.py" "."

# 4. 跑 Stage 3(把 py 文件复制到 求解/ 然后跑)
py -3 求解\预处理数据.py
py -3 求解\问题1\问题1_Y浓度回归.py
py -3 求解\问题2\问题2_BMI分组.py
py -3 求解\问题3\问题3_多目标优化.py
py -3 求解\问题4\问题4_女胎异常判定.py

# 5. Stage 4 写作 + Stage 6 编译
py -3 "<mma>\references\scripts\build.ps1" -WorkSpace "."

# 6. Stage 5 验收
py -3 "<mma>\references\scripts\auto_verify.py" "."
```

## 已知 caveat

- **问题 4 数据泄漏:** 因为 `is_abnormal` 是 Z 值的函数(任一 |Z|>3 → 异常),模型用 Z 值特征直接分类能完美还原规则(AUC=1.0)。在真正的 NIPT 检测中,这套 |Z|>3 判定规则本身已在用,本案例展示了如何用机器学习"还原"已知的医学规则。
- **依赖缺失的库:** `statsmodels` 因网络问题没装,所以问题 1 用 `numpy.linalg.lstsq` 自己算 OLS + 显著性。生产环境建议 `pip install statsmodels`。
- **多次采血数据未完整利用:** 用"首次达标孕周"简化,生产环境应考虑 `statsmodels.mixedlm` 混合效应模型。

## 参考

- `求解/建模思路.md` — Stage 2 8 段建模思路(bzd 风格)
- `测试报告.md` — Stage 1-6 测试报告(8.4 KB,含已知问题清单)
- mma skill SKILL.md — 触发词、6 阶段、目录约定
- mma skill `references/paper-spec.md` — 论文各章详细规范
- mma skill `references/writing-rules.md` — 硬规则 + 硬性数字
- mma skill `论文/README.md` — 5.X 子节工作流
