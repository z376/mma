# -*- coding: utf-8 -*-
"""
问题 3:多因素(身高/体重/年龄)+ 检测误差 + 达标比例的多目标优化
方法:加权求和(单目标化)+ 网格搜索
- 目标 1:风险最小化(沿用问题 2 风险函数)
- 目标 2:达标比例 ≥ 95%(作为约束)
- 决策变量:每组最佳检测时点
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

# ========== 1. 加载数据 ==========
print("=" * 60)
print("问题 3:多目标优化(风险最小 + 达标比例约束)")
print("=" * 60)

df = read_csv_safe(DATA)
df = df[df["胎别"] == "男"].copy()
print(f"男胎样本: {len(df)}")

# 每条记录首次达标孕周
df["达标孕周_当前"] = np.where(df["Y_达标"] == 1, df["孕周_数值"], np.nan)
df_first = df.dropna(subset=["达标孕周_当前"]).groupby("孕妇代码").agg(
    首次达标孕周=("达标孕周_当前", "min"),
    BMI=("孕妇BMI", "first"),
    年龄=("年龄", "first"),
    身高=("身高", "first"),
    体重=("体重", "first"),
    检测次数=("检测抽血次数", "max"),
).reset_index()
print(f"有首次达标孕周的孕妇: {len(df_first)}")

# 按 BMI + 年龄 + 体重(标准化后聚类,5 组)
from sklearn.cluster import KMeans

# 取 BMI + 年龄 + 体重 三个特征
features = ["BMI", "年龄", "体重"]
X = df_first[features].copy()
X = (X - X.mean()) / X.std()

# K-Means 5 组(模拟"综合考虑身高/体重/年龄")
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
df_first["组"] = kmeans.fit_predict(X)
centers = kmeans.cluster_centers_ * X.std().values + X.mean().values  # 反标准化
order = np.argsort(centers[:, 0])  # 按 BMI 排序
group_map = {old: new for new, old in enumerate(order)}
df_first["组_有序"] = df_first["组"].map(group_map)

print("\n多因素分组(K-Means 5 组,特征:BMI+年龄+体重):")
group_info = df_first.groupby("组_有序").agg(
    孕妇数=("孕妇代码", "count"),
    BMI均值=("BMI", "mean"),
    年龄均值=("年龄", "mean"),
    体重均值=("体重", "mean"),
    首次达标孕周均值=("首次达标孕周", "mean"),
).reset_index()
print(group_info.to_string())
group_info.to_csv(OUT / "多因素分组.csv", index=False, encoding="utf-8-sig")

# ========== 2. 多目标函数 ==========
print()
print("=" * 60)
print("【多目标定义】")
print("=" * 60)
print("目标 1:风险 R(t) = α·P(未达标) + β·延迟风险(沿用问题 2)")
print("目标 2:达标比例 ≥ 95%(硬约束)")
print("  P(未达标) = mean(首次达标孕周 > t)")
print("  达标比例 = mean(首次达标孕周 ≤ t)")

def risk_func(t_target, achieved_weeks, alpha=0.5, beta=0.5):
    achieved = np.asarray(achieved_weeks)
    p_miss = np.mean(achieved > t_target)
    delay_penalty = max(0, (t_target - 12) / 15) + max(0, (t_target - 28) * 5)
    return alpha * p_miss + beta * delay_penalty

def achieve_rate(t_target, achieved_weeks):
    """达标比例 = 在 t 时点已达 4% 的比例"""
    return float(np.mean(np.asarray(achieved_weeks) <= t_target))

# ========== 3. 加权求和单目标化(多目标→单目标) ==========
print()
print("=" * 60)
print("【1. 加权求和(多目标→单目标)】")
print("=" * 60)

# 综合目标:f(t) = w_risk * R(t) + w_violation * violation(t)
# violation(t) = max(0, 0.95 - achieve_rate(t)) * 10
def combined_obj(t, achieved_weeks, w_risk=0.7, w_viol=0.3, target_rate=0.95):
    r = risk_func(t, achieved_weeks)
    ar = achieve_rate(t, achieved_weeks)
    violation = max(0, target_rate - ar) * 10
    return w_risk * r + w_viol * violation

weeks = np.arange(8, 26.5, 0.5)
results = []
for grp in sorted(df_first["组_有序"].unique()):
    achieved = df_first[df_first["组_有序"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    best_t = None
    best_f = np.inf
    for t in weeks:
        f = combined_obj(t, achieved)
        if f < best_f:
            best_f = f
            best_t = t
    ar_best = achieve_rate(best_t, achieved)
    results.append({
        "组": f"组{grp+1}",
        "样本数": len(achieved),
        "BMI均值": round(np.mean(df_first[df_first["组_有序"]==grp]["BMI"]), 2),
        "年龄均值": round(np.mean(df_first[df_first["组_有序"]==grp]["年龄"]), 1),
        "体重均值": round(np.mean(df_first[df_first["组_有序"]==grp]["体重"]), 1),
        "最佳时点_周": round(best_t, 1),
        "综合目标值": round(best_f, 4),
        "达标比例": round(ar_best, 3),
        "实际首次达标均值": round(np.mean(achieved), 2),
    })

combined_df = pd.DataFrame(results)
print(combined_df.to_string())
combined_df.to_csv(OUT / "多目标_加权求和.csv", index=False, encoding="utf-8-sig")

# ========== 4. ε-constraint 法(单约束,多目标) ==========
print()
print("=" * 60)
print("【2. ε-constraint 法(达标比例 ≥ 95% 约束)】")
print("=" * 60)

results_eps = []
target_rate = 0.95
for grp in sorted(df_first["组_有序"].unique()):
    achieved = df_first[df_first["组_有序"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    # 找满足 达标比例 >= 95% 的最小 t,然后最小化风险
    feasible_t = None
    for t in weeks:
        if achieve_rate(t, achieved) >= target_rate:
            feasible_t = t
            break
    if feasible_t is None:
        # 没有满足约束的 t → 用最晚的 t
        feasible_t = weeks[-1]
    # 在 feasible_t 附近找最小风险
    nearby = weeks[(weeks >= feasible_t - 2) & (weeks <= feasible_t + 4)]
    best_t = feasible_t
    best_r = risk_func(feasible_t, achieved)
    for t in nearby:
        r = risk_func(t, achieved)
        if achieve_rate(t, achieved) >= target_rate and r < best_r:
            best_r = r
            best_t = t
    ar_best = achieve_rate(best_t, achieved)
    results_eps.append({
        "组": f"组{grp+1}",
        "样本数": len(achieved),
        "最佳时点_周": round(best_t, 1),
        "最小风险": round(best_r, 4),
        "达标比例": round(ar_best, 3),
        "约束满足": ar_best >= target_rate,
    })

eps_df = pd.DataFrame(results_eps)
print(eps_df.to_string())
eps_df.to_csv(OUT / "多目标_ε约束.csv", index=False, encoding="utf-8-sig")

# ========== 5. 误差分析 ±10% / ±20% 扰动 ==========
print()
print("=" * 60)
print("【3. 误差分析:Y 浓度 ±10% / ±20% 扰动】")
print("=" * 60)

perturb_results = []
for grp in sorted(df_first["组_有序"].unique()):
    achieved = df_first[df_first["组_有序"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    for pct in [0, -0.10, 0.10, -0.20, 0.20]:
        perturbed = achieved * (1 + pct)
        best_t = None
        best_f = np.inf
        for t in weeks:
            f = combined_obj(t, perturbed)
            if f < best_f:
                best_f = f
                best_t = t
        perturb_results.append({
            "组": f"组{grp+1}",
            "扰动": f"{pct*100:+.0f}%",
            "最佳时点": round(best_t, 1),
            "达标比例": round(achieve_rate(best_t, perturbed), 3),
        })

perturb_df = pd.DataFrame(perturb_results)
print(perturb_df.to_string())
perturb_df.to_csv(OUT / "误差分析_多目标.csv", index=False, encoding="utf-8-sig")

# ========== 6. 图 1:Pareto 前沿(风险 vs 达标比例) ==========
print()
print("画图...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (a) Pareto 前沿:每组的 风险-达标比例 散点
ax = axes[0, 0]
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
for i, grp in enumerate(sorted(df_first["组_有序"].unique())):
    achieved = df_first[df_first["组_有序"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    risks = [risk_func(t, achieved) for t in weeks]
    rates = [achieve_rate(t, achieved) for t in weeks]
    ax.plot(rates, risks, "-o", markersize=4, color=colors[i % len(colors)], label=f"组{grp+1}", alpha=0.7)
ax.axvline(0.95, color="red", linestyle="--", label="约束 95%")
ax.set_xlabel("达标比例")
ax.set_ylabel("风险")
ax.set_title("(a) 各组 Pareto 前沿(风险 vs 达标比例)")
ax.legend()
ax.grid(True, alpha=0.3)

# (b) 各组最佳时点对比
ax = axes[0, 1]
x = np.arange(len(combined_df))
w = 0.35
ax.bar(x - w/2, combined_df["实际首次达标均值"], w, color="steelblue", label="实际达标均值")
ax.bar(x + w/2, combined_df["最佳时点_周"], w, color="coral", label="最佳时点(加权求和)")
ax.set_xticks(x)
ax.set_xticklabels(combined_df["组"], rotation=15)
ax.set_ylabel("孕周(周)")
ax.set_title("(b) 各组最佳时点 vs 实际达标均值")
ax.legend()
ax.grid(True, alpha=0.3, axis="y")

# (c) 误差扰动热力图
ax = axes[1, 0]
pivot = perturb_df.pivot(index="组", columns="扰动", values="最佳时点")
import numpy as np
im = ax.imshow(pivot.values, aspect="auto", cmap="viridis")
ax.set_xticks(np.arange(len(pivot.columns)))
ax.set_xticklabels(pivot.columns)
ax.set_yticks(np.arange(len(pivot.index)))
ax.set_yticklabels(pivot.index)
ax.set_xlabel("Y 浓度扰动")
ax.set_ylabel("组")
ax.set_title("(c) 误差扰动对最佳时点的影响")
# 标数值
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        text = ax.text(j, i, f"{pivot.values[i, j]:.1f}", ha="center", va="center", color="w", fontsize=10)
plt.colorbar(im, ax=ax)

# (d) 误差扰动对达标比例的热力图
ax = axes[1, 1]
pivot2 = perturb_df.pivot(index="组", columns="扰动", values="达标比例")
im2 = ax.imshow(pivot2.values, aspect="auto", cmap="RdYlGn", vmin=0.8, vmax=1.0)
ax.set_xticks(np.arange(len(pivot2.columns)))
ax.set_xticklabels(pivot2.columns)
ax.set_yticks(np.arange(len(pivot2.index)))
ax.set_yticklabels(pivot2.index)
ax.set_xlabel("Y 浓度扰动")
ax.set_ylabel("组")
ax.set_title("(d) 误差扰动对达标比例的影响")
for i in range(len(pivot2.index)):
    for j in range(len(pivot2.columns)):
        text = ax.text(j, i, f"{pivot2.values[i, j]:.2f}", ha="center", va="center", color="black", fontsize=10)
plt.colorbar(im2, ax=ax)

plt.tight_layout()
plt.savefig(FIG / "1_多目标Pareto_最佳时点.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 1: 1_多目标Pareto_最佳时点.png")

# ========== 7. 图 2:多因素分组特征 ==========
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, feat in enumerate(["BMI", "年龄", "体重"]):
    ax = axes[i]
    for grp in sorted(df_first["组_有序"].unique()):
        sub = df_first[df_first["组_有序"] == grp][feat]
        ax.hist(sub, alpha=0.5, label=f"组{grp+1}", bins=15)
    ax.set_xlabel(feat)
    ax.set_ylabel("孕妇数")
    ax.set_title(f"{feat} 分布(按组)")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "2_多因素分组特征.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 2: 2_多因素分组特征.png")

# ========== 8. 图 3:风险函数曲线 ==========
fig, ax = plt.subplots(figsize=(12, 6))
for i, grp in enumerate(sorted(df_first["组_有序"].unique())):
    achieved = df_first[df_first["组_有序"] == grp]["首次达标孕周"].values
    if len(achieved) == 0:
        continue
    risks = [risk_func(t, achieved) for t in weeks]
    ax.plot(weeks, risks, label=f"组{grp+1}", linewidth=2)

ax.axvline(12, color="green", linestyle=":", alpha=0.5, label="12 周(早期)")
ax.axvline(28, color="red", linestyle=":", alpha=0.5, label="28 周(晚期)")
ax.set_xlabel("目标检测时点(周)")
ax.set_ylabel("风险")
ax.set_title("各组风险函数曲线(最佳时点 = 曲线最低点)")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "3_风险函数曲线.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 3: 3_风险函数曲线.png")

print()
print("=" * 60)
print("问题 3 完成")
print("=" * 60)
print(f"图片: {FIG} (3 张)")
print(f"结果: {OUT}")
print(f"\n关键结论(加权求和单目标化):")
for _, row in combined_df.iterrows():
    print(f"  {row['组']}: BMI={row['BMI均值']}, 年龄={row['年龄均值']}, 体重={row['体重均值']} → 最佳 {row['最佳时点_周']} 周,达标 {row['达标比例']*100:.0f}%")
