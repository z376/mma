# -*- coding: utf-8 -*-
"""
问题X：【问题简述】
方法：【主要方法】

说明：本文件是求解代码模板，复制到 求解/问题X/ 下后，按 TODO 填充。
绘图库不限制（matplotlib / seaborn / plotly / Pillow 均可）。

★ 论文图字号硬要求（已配好,直接用）：
  - 基础字号 14pt(默认 10pt 太小,缩到论文里看不清)
  - 标题 16pt、轴标签 14pt、刻度 12pt
  - 图宽 9 英寸(适合 A4 单栏)
  - DPI 150
  - 中文用 SimHei(标题)/ SimSun(正文)
"""
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

# ==================== 绘图工具（论文友好字号预设） ====================
# 直接启用,无需用户手动改
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 中文字体(SimHei 黑体为标题,SimSun 宋体为正文,西文 DejaVu Sans 兜底)
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False  # 负号正常显示

# ★ 论文图字号（比 matplotlib 默认大 30-50%,确保缩到 A4 论文里能看清）
plt.rcParams['font.size'] = 14              # 基础字号
plt.rcParams['axes.titlesize'] = 16        # 子图标题
plt.rcParams['axes.labelsize'] = 14        # 坐标轴标签
plt.rcParams['xtick.labelsize'] = 12       # X 刻度
plt.rcParams['ytick.labelsize'] = 12       # Y 刻度
plt.rcParams['legend.fontsize'] = 12       # 图例
plt.rcParams['figure.titlesize'] = 18      # 总标题

# 图尺寸和清晰度
plt.rcParams['figure.figsize'] = (9, 6)    # 默认 6.4x4.8 → 改为 9x6(A4 单栏 14.5cm ≈ 5.7 inch 偏小,9 inch 适合双栏宽幅)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

# 线条和点(默认偏细,论文里要粗一点)
plt.rcParams['lines.linewidth'] = 2.0
plt.rcParams['lines.markersize'] = 8
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.linewidth'] = 0.6
plt.rcParams['grid.alpha'] = 0.3

# ==================== 目录配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, '图片')
OUT_DIR = os.path.join(BASE_DIR, '结果')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ==================== 工具函数 ====================
def save_csv(df, name_cn):
    """保存CSV"""
    df.to_csv(os.path.join(OUT_DIR, name_cn), index=False, encoding='utf-8-sig')
    print(f"  [CSV] {name_cn} 已保存")

def print_stats(data, name="数据", cols=None):
    """打印数据统计信息（供论文引用）"""
    if cols is None:
        cols = data.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n{'='*60}")
    print(f"  {name} 统计摘要")
    print(f"{'='*60}")
    for col in cols:
        s = data[col].dropna()
        if len(s) == 0:
            continue
        print(f"  {col}:")
        print(f"    min={s.min():.4f}  max={s.max():.4f}  mean={s.mean():.4f}")
        cv_str = f"cv={s.std()/s.mean()*100:.1f}%" if s.mean() != 0 else "cv=N/A"
        print(f"    std={s.std():.4f}  {cv_str}  amp={s.max()-s.min():.4f}")
    print(f"{'='*60}\n")

# ==================== 第一阶段：数据加载与预处理 ====================
print("=" * 60)
print("  第一阶段：数据加载与预处理")
print("=" * 60)

# TODO: 加载数据
# df = pd.read_excel('../../数据/xxx.xlsx')
# print(f"数据规模：{df.shape}")

# TODO: 数据预处理
# ...

# ==================== 第二阶段：建模与求解 ====================
print("\n" + "=" * 60)
print("  第二阶段：建模与求解")
print("=" * 60)

# TODO: 模型建立
# ...

# TODO: 模型求解
# ...

# ==================== 第三阶段：结果输出与可视化 ====================
print("\n" + "=" * 60)
print("  第三阶段：结果输出与可视化")
print("=" * 60)

# TODO: 打印统计信息
# print_stats(result_df, "求解结果")

# TODO: 画图（自由选择绘图库，图上不设标题）
# 图片保存至 FIG_DIR，文件名用中文
# 论文中通过 \includegraphics{../求解/问题X/图片/xxx.png} 引用

# TODO: 保存结果
# save_csv(result_df, '问题X_结果.csv')

print("\n✅ 问题X求解完成！")
