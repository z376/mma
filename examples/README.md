# mma 示例:零售销售额预测(简化版)

> 这是 mma 端到端流程的最小可运行示例,演示从空目录到 论文.pdf 的完整 6 阶段。
> 数据是 mock 的(只用来演示流程,不能拿真比赛用)。

## 题目

某连锁零售企业过去 730 天的日销售额数据,字段包括:

- date(日期)
- sales(销售额,目标变量)
- traffic(客流量)
- promotion(促销力度,0-1)
- avg_price(客单价)
- online_ratio(线上销售占比)
- is_weekend(是否周末)
- is_holiday(是否节假日)

要求:

1. **问题 1**:识别影响销售额的关键因素并量化贡献
2. **问题 2**:基于历史数据预测未来 30 天销售额
3. **问题 3**:评估模型的稳定性和泛化能力,优化超参数
4. **问题 4**:基于分析结果给出经营策略建议

## mma 6 阶段执行(伪代码)

### Stage 1(建模手):读题

```bash
# 准备
mkdir <工作区> && cd <工作区>
cp <mma>/题目/零售销售.pdf 题目/
cp <mma>/examples/data/retail_sales.csv 数据/

# Agent 任务
# 读题目 + 读数据 → 打印 4 个问题 + 数据 shape (730, 8)
# 确认问题分类:问题1=机理归因, 问题2=预测, 问题3=评价+优化, 问题4=策略
```

### Stage 2(建模手):模型比选

```markdown
问题1:机理归因
| 方案 | 核心方法 | 优点 | 缺点 | 适用条件 |
| ... | ... | ... | ... | ... |
推荐: Pearson+Spearman+RF 组合(可解释+非线性)

问题2:预测
| 方案 | 核心方法 | 优点 | 缺点 |
| ... | ... | ... | ... |
推荐: GBR(基线) + Prophet(对比)

问题3:评价+优化
推荐: 5 折时序 CV + 网格搜索 + 灵敏度分析

问题4:策略
推荐: 弹性分析 → 4 个维度建议
```

### Stage 3(代码手):求解

```python
# 求解/问题1/问题1_影响因素.py
# 求解/问题2/问题2_销售额预测.py
# 求解/问题3/问题3_模型评估与优化.py
# 求解/问题4/问题4_策略建议.py
# 求解/预处理数据.csv
```

### Stage 4(论文手):写论文

按 `references/paper-spec.md` 10 章规范,逐章写 .tex。

### Stage 5(验收手):验收

按 `references/eval-checklist.md` 38 项,逐项 PASS/FAIL。

### Stage 6:出 PDF

```bash
cd 论文
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex
# → 论文.pdf
```

## 数据生成(为了复现)

```python
import numpy as np
import pandas as pd
np.random.seed(42)
n = 730
date = pd.date_range('2022-01-01', periods=n)
traffic = np.random.normal(1000, 200, n)
promotion = np.random.uniform(0, 1, n)
avg_price = np.random.normal(50, 10, n)
online_ratio = np.random.uniform(0.1, 0.5, n)
is_weekend = (date.weekday >= 5).astype(int)
is_holiday = np.random.binomial(1, 0.05, n)
sales = (traffic * 0.3
         + promotion * 5000
         + avg_price * 100
         + is_weekend * 2000
         + is_holiday * 3000
         + np.random.normal(0, 1000, n))
df = pd.DataFrame({
    'date': date,
    'sales': sales,
    'traffic': traffic,
    'promotion': promotion,
    'avg_price': avg_price,
    'online_ratio': online_ratio,
    'is_weekend': is_weekend,
    'is_holiday': is_holiday,
})
df.to_csv('retail_sales.csv', index=False, encoding='utf-8-sig')
```

## 期望产出

```
<工作区>/
├── 题目/零售销售.pdf            # 假题
├── 数据/retail_sales.csv         # mock 数据
├── 求解/
│   ├── 求解计划.md
│   ├── 预处理数据.csv
│   ├── 问题1/问题1_影响因素.py   + 图片/ + 结果/
│   ├── 问题2/问题2_销售额预测.py
│   ├── 问题3/问题3_模型评估与优化.py
│   └── 问题4/问题4_策略建议.py
└── 论文/
    ├── 论文.tex
    ├── format.cls
    ├── 0-10 章.tex
    ├── fonts/
    └── 论文.pdf                  ← 最终交付
```
