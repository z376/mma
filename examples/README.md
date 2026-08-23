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

## mma v3 6 阶段执行(伪代码)

### Stage 1(建模手):读题

```bash
# 准备
mkdir <工作区> && cd <工作区>
cp <mma>/题目/零售销售.pdf 题目/
cp <mma>/examples/data/retail_sales.csv 数据/

# 启动检查(可选)
py -3 <mma>/references/scripts/check_input.py  # 验证 题目/数据/ 是否就位

# Agent 任务
# 读题目 + 读数据 → 打印 4 个问题 + 数据 shape (730, 8)
# 确认问题分类:问题1=机理归因, 问题2=预测, 问题3=评价+优化, 问题4=策略
```

### Stage 2(建模手):8 段建模思路 + 求解计划

```markdown
# 写到 <工作区>/建模思路.md(8 段)
1. 整题建模主线
2. 跨问题联动链(Mermaid 图)
3. 全文统一建模口径
4. 分问题求解思路(每问 4 段)
5. 全文技术路线
6. 多模型对比与验证设计
7. 论文落地清单
8. 完整性与断链检查

# 用户拍板后,写到 <工作区>/求解/求解计划.md
# 包含每个问题的:选定模型 + 关键参数 + 输入/输出 + 依赖关系
```

### Stage 3(代码手):求解

```python
# <工作区>/求解/
# ├── 预处理数据.py        # 问题 1 用,输出 预处理数据.csv
# ├── 问题1/问题1_影响因素.py + 图片/ + 结果/
# ├── 问题2/问题2_销售额预测.py
# ├── 问题3/问题3_模型评估与优化.py
# └── 问题4/问题4_策略建议.py
```

### Stage 4(论文手):写论文(v3 11 章)

从 mma skill `论文/` 模板复制后,按 `references/paper-spec.md` 写:

```latex
0.摘要.tex
1.问题重述.tex
2.问题分析.tex           % 加 1.1/1.2/1.3/1.4 + 整体思路图
3.模型假设.tex
4.符号说明.tex
5.模型的建立与求解.tex   % 4 个 \subsection(问题 1/2/3/4)
6.模型检验.tex           % 6.1 误差 / 6.2 灵敏度 / 6.3 稳健性
7.模型优缺点评价.tex     % 7.1 优点 / 7.2 缺点 / 7.3 改进
0.AI声明.tex             % 放 9.参考文献 之前
9.参考文献.tex           % 含 AI 工具条目
10.附录.tex              % 附录 1 文件列表 / 附录 2 源代码 / 附录 3 其他

% 每问 5 个子节
5.1.1.数据预处理.tex         % 仅问题 1
5.1.2.XXX模型的建立.tex
5.1.3.XXX模型的求解.tex
5.1.4.XXX模型的检验.tex
5.1.5.XXX结果的分析.tex
% 5.2.x / 5.3.x / 5.4.x 同样 5 个
```

### Stage 5(验收手):验收

```bash
# 自动机械检查
py -3 <mma>/references/scripts/auto_verify.py

# 手动检查 + 编译
py -3 <mma>/references/scripts/build.ps1   # 编译两份 PDF

# 按 references/eval-checklist.md 38+ 项,逐项 PASS/FAIL
# 全部 PASS 才进 Stage 6
```

### Stage 6:出 PDF

```bash
# build.ps1 已经编译了,直接验证
Test-Path <工作区>/论文/论文.pdf    # 必须 True
Test-Path <工作区>/论文/电子版.pdf  # 必须 True
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
│   ├── 建模思路.md              # Stage 2 输出
│   ├── 求解计划.md
│   ├── 预处理数据.py
│   ├── 预处理数据.csv
│   ├── 问题1/问题1_影响因素.py   + 图片/ + 结果/
│   ├── 问题2/问题2_销售额预测.py
│   ├── 问题3/问题3_模型评估与优化.py
│   └── 问题4/问题4_策略建议.py
└── 论文/
    ├── 论文.tex
    ├── 电子版.tex
    ├── format.cls
    ├── 0.摘要.tex
    ├── 1.问题重述.tex
    ├── 2.问题分析.tex
    ├── 3.模型假设.tex
    ├── 4.符号说明.tex
    ├── 5.模型的建立与求解.tex
    ├── 5.1.1.数据预处理.tex
    ├── 5.1.2.XXX模型的建立.tex
    ├── 5.1.3.XXX模型的求解.tex
    ├── 5.1.4.XXX模型的检验.tex
    ├── 5.1.5.XXX结果的分析.tex
    ├── 5.2.x ~ 5.4.x            # 问题 2/3/4
    ├── 6.模型检验.tex
    ├── 7.模型优缺点评价.tex
    ├── 0.AI声明.tex
    ├── 9.参考文献.tex
    ├── 10.附录.tex
    ├── fonts/
    ├── 论文.pdf                  ← 最终交付
    └── 电子版.pdf                ← 最终交付
```

## 快速模式(跳级)

| 用户说 | 跳到 | 说明 |
|--------|------|------|
| "只写论文" / "跳过求解" | Stage 4 | 假设 求解/ 已就绪 |
| "只跑代码" / "求解" | Stage 3 | 假设 求解计划.md 已就绪 |
| "只验收" / "检查" | Stage 5 | 假设 论文.tex 已就绪 |
| "只出 PDF" / "编译" | Stage 6 | 跑 build.ps1 编译两份 |
| "改 XX" / "改这一章" | 局部修改 + Stage 6 | 改 .tex + 跑 build.ps1 |
