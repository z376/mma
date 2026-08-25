# -*- coding: utf-8 -*-
"""
问题 1:胎儿 Y 染色体浓度 与 孕周/BMI 等指标的关系模型 + 显著性检验
主方案:多元线性回归(OLS,自己算显著性,不依赖 statsmodels)
对比方案:随机森林回归
"""
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from scipy import stats
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import read_csv_safe, save_csv

# ========== 路径 ==========
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
print("问题 1:Y 染色体浓度 关系模型")
print("=" * 60)

df = read_csv_safe(DATA)
df = df[df["胎别"] == "男"].copy()
print(f"男胎样本: {len(df)}")

y = df["Y染色体浓度"].values * 100  # → 百分比

features = ["孕周_数值", "孕妇BMI", "年龄", "体重", "IVF_数值"]  # 去掉身高(与 BMI/体重共线)
X = df[features].copy()

mask = X.notnull().all(axis=1) & pd.notnull(y)
X = X[mask].reset_index(drop=True)
y = pd.Series(y).iloc[mask.values].reset_index(drop=True)
print(f"完整案例: {len(X)}")

# 标准化(给回归系数可比性,不影响 p 值)
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=features)

# ========== 2. 多元线性回归(OLS,自己算显著性) ==========
print()
print("=" * 60)
print("【1. 多元线性回归 OLS(自己算显著性)】")
print("=" * 60)

# 用 numpy.linalg.lstsq 拟合
n = len(y)
p = X_scaled.shape[1]  # 6 个特征
X_with_const = np.column_stack([np.ones(n), X_scaled.values])
beta, residuals, rank, sv = np.linalg.lstsq(X_with_const, y.values, rcond=None)
y_pred_ols = X_with_const @ beta
resid = y.values - y_pred_ols
rss = np.sum(resid ** 2)
r2 = 1 - rss / np.sum((y.values - y.mean()) ** 2)
rmse = np.sqrt(rss / n)
mae = np.mean(np.abs(resid))

# 显著性:Cov(beta) = sigma^2 * (X'X)^-1
sigma2 = rss / (n - p - 1)
XtX_inv = np.linalg.pinv(X_with_const.T @ X_with_const)  # 伪逆,处理奇异
se = np.sqrt(np.diag(sigma2 * XtX_inv))
t_vals = beta / se
p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), df=n - p - 1))

print(f"{'变量':<15} {'系数':>10} {'标准误':>10} {'t 值':>10} {'p 值':>10} {'显著性':>8}")
print("-" * 70)
var_names = ["const"] + features
for i, name in enumerate(var_names):
    sig = "***" if p_vals[i] < 0.001 else "**" if p_vals[i] < 0.01 else "*" if p_vals[i] < 0.05 else ""
    print(f"{name:<15} {beta[i]:>10.4f} {se[i]:>10.4f} {t_vals[i]:>10.3f} {p_vals[i]:>10.4f} {sig:>8}")

print(f"\nR² = {r2:.4f}, 调整 R² = {1 - (1-r2)*(n-1)/(n-p-1):.4f}")
print(f"RMSE = {rmse:.4f}%, MAE = {mae:.4f}%")

coef_df = pd.DataFrame({
    "变量": var_names,
    "系数": beta,
    "标准误": se,
    "t 值": t_vals,
    "p 值": p_vals,
})
coef_df.to_csv(OUT / "线性回归系数表.csv", index=False, encoding="utf-8-sig")

# 5 折 CV
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_r2 = cross_val_score(LinearRegression(), X_scaled, y, cv=kf, scoring="r2")
cv_rmse = -cross_val_score(LinearRegression(), X_scaled, y, cv=kf, scoring="neg_root_mean_squared_error")
print(f"5 折 CV R² = {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")
print(f"5 折 CV RMSE = {cv_rmse.mean():.4f} ± {cv_rmse.std():.4f}%")

# ========== 3. 随机森林回归(对比) ==========
print()
print("=" * 60)
print("【2. 随机森林回归(对比)】")
print("=" * 60)

rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X, y)
y_pred_rf = rf.predict(X)
r2_rf = r2_score(y, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y, y_pred_rf))
print(f"R² = {r2_rf:.4f}, RMSE = {rmse_rf:.4f}%")

cv_r2_rf = cross_val_score(rf, X, y, cv=kf, scoring="r2")
cv_rmse_rf = -cross_val_score(rf, X, y, cv=kf, scoring="neg_root_mean_squared_error")
print(f"5 折 CV R² = {cv_r2_rf.mean():.4f} ± {cv_r2_rf.std():.4f}")
print(f"5 折 CV RMSE = {cv_rmse_rf.mean():.4f} ± {cv_rmse_rf.std():.4f}%")

imp = pd.DataFrame({"特征": features, "重要性": rf.feature_importances_}).sort_values("重要性", ascending=False)
print("\n特征重要性(随机森林):")
print(imp.to_string())
imp.to_csv(OUT / "随机森林特征重要性.csv", index=False, encoding="utf-8-sig")

# ========== 4. 图 1:Y 浓度 vs 孕周 / BMI ==========
print()
print("画图...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# (a) Y vs 孕周
ax = axes[0]
ax.scatter(X["孕周_数值"], y, alpha=0.3, s=20, color="steelblue", label="实际数据")
xx = np.linspace(X["孕周_数值"].min(), X["孕周_数值"].max(), 100)
X_pred = pd.DataFrame({f: [X[f].mean()] * 100 for f in features})
X_pred["孕周_数值"] = xx
X_pred_s = pd.DataFrame(scaler.transform(X_pred), columns=features)
X_pred_s.insert(0, "const", 1)
yy_ols = X_pred_s.values @ beta
yy_rf = rf.predict(X_pred)
ax.plot(xx, yy_ols, color="red", linewidth=2, label=f"线性回归 (R²={r2:.3f})")
ax.plot(xx, yy_rf, color="green", linewidth=2, linestyle="--", label=f"随机森林 (R²={r2_rf:.3f})")
ax.axhline(4, color="orange", linestyle=":", linewidth=1.5, label="达标线 4%")
ax.set_xlabel("检测孕周(周)")
ax.set_ylabel("Y 染色体浓度(%)")
ax.set_title("(a) Y 浓度 vs 孕周")
ax.legend()
ax.grid(True, alpha=0.3)

# (b) Y vs BMI
ax = axes[1]
ax.scatter(X["孕妇BMI"], y, alpha=0.3, s=20, color="coral")
xx = np.linspace(X["孕妇BMI"].min(), X["孕妇BMI"].max(), 100)
X_pred = pd.DataFrame({f: [X[f].mean()] * 100 for f in features})
X_pred["孕妇BMI"] = xx
X_pred_s = pd.DataFrame(scaler.transform(X_pred), columns=features)
X_pred_s.insert(0, "const", 1)
yy_ols = X_pred_s.values @ beta
yy_rf = rf.predict(X_pred)
ax.plot(xx, yy_ols, color="red", linewidth=2, label="线性回归")
ax.plot(xx, yy_rf, color="green", linewidth=2, linestyle="--", label="随机森林")
ax.axhline(4, color="orange", linestyle=":", linewidth=1.5, label="达标线 4%")
ax.set_xlabel("孕妇 BMI")
ax.set_ylabel("Y 染色体浓度(%)")
ax.set_title("(b) Y 浓度 vs BMI")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "1_Y浓度vs孕周_BMI.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 1: 1_Y浓度vs孕周_BMI.png")

# ========== 5. 图 2:预测值 vs 实际值 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, y_pred, name, r2v in [
    (axes[0], y_pred_ols, "线性回归", r2),
    (axes[1], y_pred_rf, "随机森林", r2_rf),
]:
    ax.scatter(y, y_pred, alpha=0.4, s=20)
    ax.plot([y.min(), y.max()], [y.min(), y.max()], "r--", linewidth=1.5, label="理想线 y=x")
    ax.set_xlabel("实际 Y 浓度(%)")
    ax.set_ylabel("预测 Y 浓度(%)")
    ax.set_title(f"{name}:预测 vs 实际 (R²={r2v:.3f})")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "2_预测vs实际.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 2: 2_预测vs实际.png")

# ========== 6. 图 3:残差图 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, y_pred, name in [
    (axes[0], y_pred_ols, "线性回归"),
    (axes[1], y_pred_rf, "随机森林"),
]:
    r = y - y_pred
    ax.scatter(y_pred, r, alpha=0.4, s=20)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.5)
    ax.set_xlabel("预测值(%)")
    ax.set_ylabel("残差(%)")
    ax.set_title(f"{name}:残差图")
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "3_残差图.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 3: 3_残差图.png")

# ========== 7. 图 4:系数 + 特征重要性 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# (a) OLS 系数
ax = axes[0]
coef_plot = coef_df[coef_df["变量"] != "const"].copy()
colors = ["steelblue" if p < 0.05 else "lightgray" for p in coef_plot["p 值"]]
ax.barh(coef_plot["变量"], coef_plot["系数"], color=colors)
ax.set_xlabel("回归系数(标准化)")
ax.set_title("(a) OLS 系数(深色=p<0.05 显著)")
ax.axvline(0, color="black", linewidth=0.5)
ax.grid(True, alpha=0.3, axis="x")

# (b) RF 特征重要性
ax = axes[1]
ax.barh(imp["特征"], imp["重要性"], color="coral")
ax.set_xlabel("特征重要性")
ax.set_title("(b) 随机森林特征重要性")
ax.grid(True, alpha=0.3, axis="x")

plt.tight_layout()
plt.savefig(FIG / "4_系数_特征重要性.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 4: 4_系数_特征重要性.png")

# ========== 8. 保存预测结果 ==========
result_df = pd.DataFrame({
    "实际Y浓度": y.values,
    "线性回归预测": y_pred_ols,
    "随机森林预测": y_pred_rf,
    "残差_线性": (y - y_pred_ols).values,
    "残差_随机森林": (y - y_pred_rf).values,
})
result_df.to_csv(OUT / "问题1_预测结果.csv", index=False, encoding="utf-8-sig")

summary = pd.DataFrame({
    "模型": ["线性回归", "随机森林"],
    "R²": [r2, r2_rf],
    "RMSE(%)": [rmse, rmse_rf],
    "MAE(%)": [mae, mean_absolute_error(y, y_pred_rf)],
    "5折CV_R²_mean": [cv_r2.mean(), cv_r2_rf.mean()],
    "5折CV_R²_std": [cv_r2.std(), cv_r2_rf.std()],
    "5折CV_RMSE_mean": [cv_rmse.mean(), cv_rmse_rf.mean()],
})
summary.to_csv(OUT / "问题1_模型对比.csv", index=False, encoding="utf-8-sig")

print()
print("=" * 60)
print("问题 1 完成")
print("=" * 60)
print(f"图片: {FIG} (4 张)")
print(f"结果: {OUT} (系数表 + 特征重要性 + 预测结果 + 模型对比)")
print(f"\n关键结论:")
print(f"  线性回归 R²={r2:.3f},随机森林 R²={r2_rf:.3f}")
print(f"  显著变量(p<0.05):")
for i, name in enumerate(features):
    if p_vals[i + 1] < 0.05:
        print(f"    {name}: coef={beta[i+1]:.4f}, p={p_vals[i+1]:.4f}")
