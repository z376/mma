# -*- coding: utf-8 -*-
"""
问题 2:男胎 BMI 分组 + 最佳 NIPT 时点 + 误差分析
方法:决策树找最佳 BMI 阈值 + 每组平均达标孕周(最佳时点) + 风险最小化
"""
import sys
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import read_csv_safe, save_csv

BASE = Path(__file__).resolve().parent
WS = BASE.parent.parent
DATA = WS / "求解" / "预处理数据.csv"
FIG = BASE / "图片"
OUT = BASE / "结果"
FIG.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Source Han Serif CN", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120

# ========== 1. 加载男胎数据 ==========
print("=" * 60)
print("问题 2:BMI 分组 + 最佳 NIPT 时点")
print("=" * 60)

df = read_csv_safe(DATA)
df = df[df["胎别"] == "男"].copy()
print(f"男胎样本: {len(df)}")

# 每条记录首次达标孕周(若当前已达 4%)
df["达标孕周_当前"] = np.where(df["Y_达标"] == 1, df["孕周_数值"], np.nan)
df_first = df.dropna(subset=["达标孕周_当前"]).groupby("孕妇代码").agg(
    首次达标孕周=("达标孕周_当前", "min"),
    BMI=("孕妇BMI", "first"),
    年龄=("年龄", "first"),
    检测次数=("检测抽血次数", "max"),
).reset_index()
print(f"有首次达标孕周的孕妇: {len(df_first)}")
print(f"首次达标孕周: min={df_first['首次达标孕周'].min():.1f}, "
      f"median={df_first['首次达标孕周'].median():.1f}, max={df_first['首次达标孕周'].max():.1f}")
print(f"BMI: min={df_first['BMI'].min():.1f}, median={df_first['BMI'].median():.1f}, max={df_first['BMI'].max():.1f}")

# ========== 2. 决策树分组(自动找 BMI 阈值) ==========
print()
print("=" * 60)
print("【1. 决策树分组(自动找 BMI 阈值,max_depth=2)】")
print("=" * 60)

X = df_first[["BMI"]].values
y = df_first["首次达标孕周"].values
tree = DecisionTreeRegressor(max_depth=2, min_samples_leaf=50, random_state=42)
tree.fit(X, y)
y_pred_tree = tree.predict(X)
rmse_tree = np.sqrt(mean_squared_error(y, y_pred_tree))
print(f"决策树 RMSE: {rmse_tree:.2f} 周")

# 提取唯一阈值(去重、相邻差 ≥ 1)
tree_thresholds = tree.tree_.threshold[tree.tree_.threshold != -2]
thresh_list = sorted(set(np.round(tree_thresholds, 1).tolist()))
final_thresh = []
for t in thresh_list:
    if not final_thresh or t - final_thresh[-1] >= 1.0:
        final_thresh.append(t)
thresh_list = final_thresh
print(f"决策树自动阈值(BMI): {thresh_list}")

# 根据阈值分组
def assign_bmi_group(bmi, thresholds):
    bins = [20] + thresholds + [50]
    labels = [f"[{bins[i]:.0f},{bins[i+1]:.0f})" for i in range(len(bins) - 1)]
    for i in range(len(bins) - 1):
        if bins[i] <= bmi < bins[i + 1]:
            return labels[i]
    return labels[-1]

df_first["BMI_组_决策树"] = df_first["BMI"].apply(lambda x: assign_bmi_group(x, thresh_list))
group_tree = df_first.groupby("BMI_组_决策树", observed=True).agg(
    孕妇数=("孕妇代码", "count"),
    BMI均值=("BMI", "mean"),
    首次达标孕周均值=("首次达标孕周", "mean"),
    首次达标孕周中位数=("首次达标孕周", "median"),
    首次达标孕周_std=("首次达标孕周", "std"),
).reset_index()
print("\n决策树分组结果:")
print(group_tree.to_string())
group_tree.to_csv(OUT / "BMI分组_决策树.csv", index=False, encoding="utf-8-sig")

# ========== 3. K-Means 聚类(对比) ==========
print()
print("=" * 60)
print("【2. K-Means 聚类(对比,K=4)】")
print("=" * 60)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df_first["BMI_组_KMeans"] = kmeans.fit_predict(df_first[["BMI"]].values)
centers = sorted(kmeans.cluster_centers_.flatten())
print(f"K-Means 聚类中心(BMI 升序): {np.round(centers, 1)}")

df_first["BMI_组_KMeans_有序"] = df_first["BMI_组_KMeans"].map(
    {i: f"组{i+1}(BMI≈{centers[i]:.1f})" for i in range(4)}
)
group_km = df_first.groupby("BMI_组_KMeans_有序", observed=True).agg(
    孕妇数=("孕妇代码", "count"),
    BMI均值=("BMI", "mean"),
    首次达标孕周均值=("首次达标孕周", "mean"),
    首次达标孕周中位数=("首次达标孕周", "median"),
).reset_index().sort_values("BMI均值")
print(group_km.to_string())
group_km.to_csv(OUT / "BMI分组_KMeans.csv", index=False, encoding="utf-8-sig")

# ========== 4. 题目建议 5 组(baseline) ==========
print()
print("=" * 60)
print("【3. 题目建议 5 组(baseline)】")
print("=" * 60)

bmi_bins_baseline = [0, 28, 32, 36, 40, 100]
bmi_labels_baseline = ["[20,28)", "[28,32)", "[32,36)", "[36,40)", "40+"]
df_first["BMI_组_题目"] = pd.cut(df_first["BMI"], bins=bmi_bins_baseline, labels=bmi_labels_baseline, right=False)
group_base = df_first.groupby("BMI_组_题目", observed=True).agg(
    孕妇数=("孕妇代码", "count"),
    BMI均值=("BMI", "mean"),
    首次达标孕周均值=("首次达标孕周", "mean"),
    首次达标孕周中位数=("首次达标孕周", "median"),
).reset_index()
print(group_base.to_string())
group_base.to_csv(OUT / "BMI分组_题目建议.csv", index=False, encoding="utf-8-sig")

# ========== 5. 风险最小化(选最佳时点) ==========
print()
print("=" * 60)
print("【4. 风险最小化(选最佳时点)】")
print("=" * 60)

# 风险函数(总是正):
#   R(t) = α * P(未达标) + β * 延迟风险
#   P(未达标) = mean(首次达标孕周 > t)(即目标时点早于首次达标 → 浓度未达 4%)
#   延迟风险 = max(0, (t-12)/15) + max(0, (t-28)*5)(>= 28 周风险骤增)
def risk_func(t_target, achieved_weeks, alpha=0.5, beta=0.5):
    achieved = np.asarray(achieved_weeks)
    p_miss = np.mean(achieved > t_target)
    delay_penalty = max(0, (t_target - 12) / 15) + max(0, (t_target - 28) * 5)
    return alpha * p_miss + beta * delay_penalty

# 搜索 8-26 周,步长 0.5
weeks = np.arange(8, 26.5, 0.5)
print("\n决策树分组最佳时点搜索(8-26 周,步长 0.5):")
results = []
for grp in group_tree["BMI_组_决策树"]:
    achieved = df_first[df_first["BMI_组_决策树"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    best_t = None
    best_r = np.inf
    for t in weeks:
        r = risk_func(t, achieved)
        if r < best_r:
            best_r = r
            best_t = t
    results.append({
        "BMI_组": grp,
        "样本数": len(achieved),
        "最佳时点_周": round(best_t, 1),
        "最低风险": round(best_r, 4),
        "实际首次达标_均值": round(np.mean(achieved), 2),
    })

risk_df = pd.DataFrame(results)
print(risk_df.to_string())
risk_df.to_csv(OUT / "最佳时点_风险最小化.csv", index=False, encoding="utf-8-sig")

# ========== 6. 误差分析 ±10% Y 浓度扰动 ==========
print()
print("=" * 60)
print("【5. 误差分析:Y 浓度 ±10% 扰动对最佳时点的影响】")
print("=" * 60)

perturb_results = []
for grp in group_tree["BMI_组_决策树"]:
    achieved = df_first[df_first["BMI_组_决策树"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    best_t = None
    best_r = np.inf
    for t in weeks:
        r = risk_func(t, achieved)
        if r < best_r:
            best_r = r
            best_t = t
    perturb_results.append({"BMI_组": grp, "扰动": "0%", "最佳时点": round(best_t, 1)})

    for pct in [-0.10, 0.10]:
        # ±10% Y 浓度扰动 → 首次达标孕周等比例变化(浓度更难达 → 达标孕周推迟)
        perturbed = achieved * (1 + pct)
        best_t_p = None
        best_r_p = np.inf
        for t in weeks:
            r = risk_func(t, perturbed)
            if r < best_r_p:
                best_r_p = r
                best_t_p = t
        perturb_results.append({"BMI_组": grp, "扰动": f"{pct*100:+.0f}%", "最佳时点": round(best_t_p, 1)})

perturb_df = pd.DataFrame(perturb_results)
print(perturb_df.to_string())
perturb_df.to_csv(OUT / "误差分析_±10%.csv", index=False, encoding="utf-8-sig")

# ========== 7. 图 1:BMI 分布 + 分组 ==========
print()
print("画图...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
ax.hist(df_first["BMI"], bins=30, color="steelblue", alpha=0.7, edgecolor="black")
for t in thresh_list:
    ax.axvline(t, color="red", linestyle="--", linewidth=1.5, label=f"决策树阈值={t:.1f}")
ax.set_xlabel("孕妇 BMI")
ax.set_ylabel("孕妇数")
ax.set_title("(a) BMI 分布 + 决策树分组阈值")
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1]
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for i, grp in enumerate(group_tree["BMI_组_决策树"]):
    sub = df_first[df_first["BMI_组_决策树"] == grp]
    ax.scatter(sub["BMI"], sub["首次达标孕周"], alpha=0.5, s=20,
               color=colors[i % len(colors)], label=grp)
ax.set_xlabel("孕妇 BMI")
ax.set_ylabel("首次达标孕周(周)")
ax.set_title("(b) BMI vs 首次达标孕周(决策树分组)")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "1_BMI分布与分组.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 1: 1_BMI分布与分组.png")

# ========== 8. 图 2:各组最佳时点对比 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
x = np.arange(len(risk_df))
w = 0.35
ax.bar(x - w/2, risk_df["实际首次达标_均值"], w, color="steelblue", label="实际首次达标均值")
ax.bar(x + w/2, risk_df["最佳时点_周"], w, color="coral", label="最佳时点(风险最小化)")
ax.set_xticks(x)
ax.set_xticklabels(risk_df["BMI_组"], rotation=15)
ax.set_ylabel("孕周(周)")
ax.set_title("(a) 各组最佳时点 vs 实际达标均值")
ax.legend()
ax.grid(True, alpha=0.3, axis="y")

ax = axes[1]
pivot = perturb_df.pivot(index="BMI_组", columns="扰动", values="最佳时点")
pivot.plot(kind="bar", ax=ax, color=["steelblue", "coral", "lightcoral"])
ax.set_ylabel("最佳时点(周)")
ax.set_title("(b) 误差 ±10% 对最佳时点的影响")
ax.legend(title="扰动")
ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(FIG / "2_最佳时点对比.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 2: 2_最佳时点对比.png")

# ========== 9. 图 3:风险函数可视化 ==========
fig, ax = plt.subplots(figsize=(12, 6))
for i, row in risk_df.iterrows():
    grp = row["BMI_组"]
    achieved = df_first[df_first["BMI_组_决策树"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    risks = [risk_func(t, achieved) for t in weeks]
    ax.plot(weeks, risks, label=grp, linewidth=2)

ax.axvline(12, color="green", linestyle=":", alpha=0.5, label="12 周(早期)")
ax.axvline(28, color="red", linestyle=":", alpha=0.5, label="28 周(晚期)")
ax.set_xlabel("目标检测时点(周)")
ax.set_ylabel("风险")
ax.set_title("各 BMI 组风险函数曲线(最佳时点 = 曲线最低点)")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "3_风险函数曲线.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 3: 3_风险函数曲线.png")

# ========== 10. 图 4:达标孕周箱线图 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# (a) 决策树分组
ax = axes[0]
order = list(group_tree["BMI_组_决策树"])
data = [df_first[df_first["BMI_组_决策树"] == g]["首次达标孕周"].values for g in order]
data = [d for d in data if len(d) > 0]  # 过滤空组
labels_nonzero = [g for g, d in zip(order, data) if len(d) > 0]
if data:
    bp = ax.boxplot(data, tick_labels=labels_nonzero, patch_artist=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
ax.set_ylabel("首次达标孕周(周)")
ax.set_title("(a) 决策树分组 首次达标孕周分布")
ax.grid(True, alpha=0.3, axis="y")

# (b) 题目 5 组
ax = axes[1]
order2 = list(group_base["BMI_组_题目"].astype(str))
data2 = [df_first[df_first["BMI_组_题目"].astype(str) == g]["首次达标孕周"].dropna().values for g in order2]
data2 = [d for d in data2 if len(d) > 0]
labels2_nonzero = [g for g, d in zip(order2, data2) if len(d) > 0]
if data2:
    bp2 = ax.boxplot(data2, tick_labels=labels2_nonzero, patch_artist=True)
    for patch, color in zip(bp2["boxes"], colors):
        patch.set_facecolor(color)
ax.set_ylabel("首次达标孕周(周)")
ax.set_title("(b) 题目 5 组 首次达标孕周分布")
ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(FIG / "4_达标孕周箱线图.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 4: 4_达标孕周箱线图.png")

print()
print("=" * 60)
print("问题 2 完成")
print("=" * 60)
print(f"图片: {FIG} (4 张)")
print(f"结果: {OUT}")
print(f"\n关键结论:")
print(f"  决策树分组阈值: {thresh_list}")
print(f"  最佳时点(决策树分组,风险最小化):")
for _, row in risk_df.iterrows():
    print(f"    {row['BMI_组']}: 最佳 {row['最佳时点_周']} 周 (实际达标均值 {row['实际首次达标_均值']} 周)")
