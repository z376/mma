# -*- coding: utf-8 -*-
"""
问题 4:女胎异常判定
- 数据:女胎 605 条,标签"胎儿是否健康"全是"是"(100%) → 改用 |Z|>3 合成标签
- 特征:13/18/21 号 Z 值 + GC 含量 + 读段数 + 比例 + BMI + 年龄 + IVF
- 模型:Logistic(主,可解释)+ 随机森林(对比)+ SVM(对比)
- 评估:5 折分层 CV + AUC + F1 + 准确率 + 混淆矩阵
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

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report, RocCurveDisplay
)
from sklearn.preprocessing import StandardScaler

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

# ========== 1. 加载女胎数据 ==========
print("=" * 60)
print("问题 4:女胎异常判定")
print("=" * 60)

df = read_csv_safe(DATA)
df = df[df["胎别"] == "女"].copy()
print(f"女胎样本: {len(df)}")
print(f"原始标签'胎儿是否健康'分布: {df['胎儿是否健康'].value_counts().to_dict()}")
print(f"  → 全部为'是',无监督学习价值,改用 |Z|>3 合成标签")

# 合成异常标签:任一 |Z_13|, |Z_18|, |Z_21| > 3 视为异常
df["is_abnormal"] = (
    (df["13号染色体的Z值"].abs() > 3) |
    (df["18号染色体的Z值"].abs() > 3) |
    (df["21号染色体的Z值"].abs() > 3)
).astype(int)
print(f"\n合成标签 is_abnormal 分布:")
print(f"  正常(0): {(df['is_abnormal']==0).sum()} ({(df['is_abnormal']==0).mean()*100:.1f}%)")
print(f"  异常(1): {(df['is_abnormal']==1).sum()} ({(df['is_abnormal']==1).mean()*100:.1f}%)")

# ========== 2. 特征工程 ==========
print()
print("=" * 60)
print("【特征工程】")
print("=" * 60)

# 原始特征
raw_features = [
    "13号染色体的Z值", "18号染色体的Z值", "21号染色体的Z值", "X染色体的Z值",
    "13号染色体的GC含量", "18号染色体的GC含量", "21号染色体的GC含量",
    "原始读段数", "在参考基因组上比对的比例", "重复读段的比例", "唯一比对的读段数",
    "被过滤掉读段数的比例",
    "GC含量",  # 整体 GC 含量
    "孕妇BMI", "年龄", "身高", "体重", "IVF_数值",
]

# 衍生特征
df["Z_13_abs"] = df["13号染色体的Z值"].abs()
df["Z_18_abs"] = df["18号染色体的Z值"].abs()
df["Z_21_abs"] = df["21号染色体的Z值"].abs()
df["Z_X_abs"] = df["X染色体的Z值"].abs()
df["Z_max"] = df[["Z_13_abs", "Z_18_abs", "Z_21_abs"]].max(axis=1)
df["Z_sum"] = df["Z_13_abs"] + df["Z_18_abs"] + df["Z_21_abs"]
df["Z_mean"] = (df["Z_13_abs"] + df["Z_18_abs"] + df["Z_21_abs"]) / 3
df["Z_any_high"] = (df["Z_max"] > 3).astype(int)  # 跟 is_abnormal 一致,作为衍生

derived_features = ["Z_13_abs", "Z_18_abs", "Z_21_abs", "Z_X_abs", "Z_max", "Z_sum", "Z_mean", "Z_any_high"]

all_features = raw_features + derived_features

# 处理缺失(用中位数填充)
X = df[all_features].copy()
for c in X.columns:
    if X[c].isnull().any():
        median = X[c].median()
        X[c] = X[c].fillna(median)
y = df["is_abnormal"].values

# 标准化
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=all_features)

print(f"特征数: {len(all_features)} (原始 {len(raw_features)} + 衍生 {len(derived_features)})")
print(f"样本数: {len(X)}, 异常样本: {y.sum()} ({y.mean()*100:.1f}%)")
print(f"类别不平衡:1:{y.sum()/(len(y)-y.sum()):.1f}(异常:正常)")

# ========== 3. 模型训练与评估 ==========
print()
print("=" * 60)
print("【模型训练与 5 折分层 CV】")
print("=" * 60)

# 类别不平衡:用 class_weight='balanced'
models = {
    "Logistic(平衡)": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    "Logistic": LogisticRegression(max_iter=1000, random_state=42),
    "RandomForest(平衡)": RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1),
    "SVM(RBF)": SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=42),
    "NaiveBayes": GaussianNB(),
}

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}
for name, model in models.items():
    print(f"\n--- {name} ---")
    auc_scores = []
    acc_scores = []
    f1_scores = []
    prec_scores = []
    rec_scores = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X_scaled, y), 1):
        X_tr, X_te = X_scaled.iloc[train_idx], X_scaled.iloc[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]
        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_te)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_te)[:, 1]
        else:
            y_prob = y_pred  # fallback

        acc = accuracy_score(y_te, y_pred)
        prec = precision_score(y_te, y_pred, zero_division=0)
        rec = recall_score(y_te, y_pred, zero_division=0)
        f1 = f1_score(y_te, y_pred, zero_division=0)
        auc = roc_auc_score(y_te, y_prob) if len(np.unique(y_te)) > 1 else 0.5

        auc_scores.append(auc)
        acc_scores.append(acc)
        prec_scores.append(prec)
        rec_scores.append(rec)
        f1_scores.append(f1)
        print(f"  Fold {fold}: Acc={acc:.3f}, Prec={prec:.3f}, Rec={rec:.3f}, F1={f1:.3f}, AUC={auc:.3f}")

    print(f"  Mean: Acc={np.mean(acc_scores):.3f}±{np.std(acc_scores):.3f}, "
          f"F1={np.mean(f1_scores):.3f}±{np.std(f1_scores):.3f}, "
          f"AUC={np.mean(auc_scores):.3f}±{np.std(auc_scores):.3f}")
    results[name] = {
        "acc_mean": np.mean(acc_scores), "acc_std": np.std(acc_scores),
        "prec_mean": np.mean(prec_scores), "prec_std": np.std(prec_scores),
        "rec_mean": np.mean(rec_scores), "rec_std": np.std(rec_scores),
        "f1_mean": np.mean(f1_scores), "f1_std": np.std(f1_scores),
        "auc_mean": np.mean(auc_scores), "auc_std": np.std(auc_scores),
    }

# ========== 4. 选定主模型,fit 全量数据,输出特征重要性 ==========
print()
print("=" * 60)
print("【特征重要性(Logistic)】")
print("=" * 60)

main_model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
main_model.fit(X_scaled, y)
coef = pd.DataFrame({
    "特征": all_features,
    "系数(标准化)": main_model.coef_[0],
    "abs(系数)": np.abs(main_model.coef_[0]),
}).sort_values("abs(系数)", ascending=False)
print(coef.head(15).to_string())
coef.to_csv(OUT / "Logistic_特征重要性.csv", index=False, encoding="utf-8-sig")

# ========== 5. RF 特征重要性 ==========
rf_model = RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1)
rf_model.fit(X_scaled, y)
imp_rf = pd.DataFrame({
    "特征": all_features,
    "重要性": rf_model.feature_importances_,
}).sort_values("重要性", ascending=False)
print("\n随机森林特征重要性 TOP 10:")
print(imp_rf.head(10).to_string())
imp_rf.to_csv(OUT / "RandomForest_特征重要性.csv", index=False, encoding="utf-8-sig")

# ========== 6. 汇总结果 ==========
summary = pd.DataFrame(results).T
summary.index.name = "模型"
summary = summary.reset_index()
summary.to_csv(OUT / "模型对比.csv", index=False, encoding="utf-8-sig")
print()
print("=" * 60)
print("模型对比汇总")
print("=" * 60)
print(summary.to_string())

# ========== 7. 图 1:ROC 曲线对比 ==========
print()
print("画图...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
for name, model in models.items():
    model.fit(X_scaled, y)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_scaled)[:, 1]
    else:
        y_prob = model.decision_function(X_scaled) if hasattr(model, "decision_function") else model.predict(X_scaled)
    from sklearn.metrics import roc_curve, auc
    fpr, tpr, _ = roc_curve(y, y_prob)
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, label=f"{name} (AUC={roc_auc:.3f})", linewidth=2)

ax.plot([0, 1], [0, 1], "k--", linewidth=1)
ax.set_xlabel("假阳性率 FPR")
ax.set_ylabel("真阳性率 TPR")
ax.set_title("(a) ROC 曲线(全量数据)")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

# (b) 特征重要性(LR + RF 对比)
ax = axes[1]
top = coef.head(10)
colors_lr = ["steelblue" if c > 0 else "coral" for c in top["系数(标准化)"]]
ax.barh(top["特征"], top["系数(标准化)"], color=colors_lr)
ax.set_xlabel("Logistic 系数(标准化)")
ax.set_title("(b) Logistic 特征重要性 TOP 10(蓝正/红负)")
ax.grid(True, alpha=0.3, axis="x")
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(FIG / "1_ROC_特征重要性.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 1: 1_ROC_特征重要性.png")

# ========== 8. 图 2:特征重要性对比 ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
top10_lr = coef.head(10)
ax.barh(top10_lr["特征"], top10_lr["abs(系数)"], color="steelblue")
ax.set_xlabel("|系数|")
ax.set_title("(a) Logistic |系数| TOP 10")
ax.invert_yaxis()
ax.grid(True, alpha=0.3, axis="x")

ax = axes[1]
top10_rf = imp_rf.head(10)
ax.barh(top10_rf["特征"], top10_rf["重要性"], color="coral")
ax.set_xlabel("重要性")
ax.set_title("(b) RandomForest 重要性 TOP 10")
ax.invert_yaxis()
ax.grid(True, alpha=0.3, axis="x")

plt.tight_layout()
plt.savefig(FIG / "2_特征重要性对比.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 2: 2_特征重要性对比.png")

# ========== 9. 图 3:Z 值分布 + 异常阈值 ==========
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for i, z_col in enumerate(["13号染色体的Z值", "18号染色体的Z值", "21号染色体的Z值"]):
    ax = axes[i]
    z_normal = df[df["is_abnormal"] == 0][z_col]
    z_abnormal = df[df["is_abnormal"] == 1][z_col]
    ax.hist(z_normal, bins=30, alpha=0.6, label=f"正常(n={len(z_normal)})", color="steelblue")
    ax.hist(z_abnormal, bins=30, alpha=0.8, label=f"异常(n={len(z_abnormal)})", color="coral")
    ax.axvline(3, color="red", linestyle="--", label="阈值 +3")
    ax.axvline(-3, color="red", linestyle="--", label="阈值 -3")
    ax.set_xlabel(z_col.replace("号染色体的Z值", "号 Z 值"))
    ax.set_ylabel("频数")
    ax.set_title(f"{z_col} 分布")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG / "3_Z值分布.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 3: 3_Z值分布.png")

# ========== 10. 图 4:混淆矩阵(Logistic 全量) ==========
from sklearn.metrics import ConfusionMatrixDisplay
fig, ax = plt.subplots(figsize=(6, 5))
y_pred_all = main_model.predict(X_scaled)
cm = confusion_matrix(y, y_pred_all)
disp = ConfusionMatrixDisplay(cm, display_labels=["正常", "异常"])
disp.plot(ax=ax, cmap="Blues", values_format="d")
ax.set_title(f"Logistic 混淆矩阵(全量数据)\nAcc={accuracy_score(y, y_pred_all):.3f}")

plt.tight_layout()
plt.savefig(FIG / "4_混淆矩阵.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"  图 4: 4_混淆矩阵.png")

# ========== 11. 保存预测结果 ==========
pred_df = pd.DataFrame({
    "样本序号": df["序号"].values,
    "孕妇代码": df["孕妇代码"].values,
    "真实标签": y,
    "Logistic预测": main_model.predict(X_scaled),
    "Logistic概率": main_model.predict_proba(X_scaled)[:, 1],
    "RF预测": rf_model.predict(X_scaled),
    "RF概率": rf_model.predict_proba(X_scaled)[:, 1],
})
pred_df.to_csv(OUT / "问题4_预测结果.csv", index=False, encoding="utf-8-sig")

print()
print("=" * 60)
print("问题 4 完成")
print("=" * 60)
print(f"图片: {FIG} (4 张)")
print(f"结果: {OUT}")
print(f"\n关键结论:")
print(f"  异常样本: {y.sum()}/{len(y)} ({y.mean()*100:.1f}%)")
print(f"  Logistic |AUC| = {results['Logistic(平衡)']['auc_mean']:.3f} (5 折 CV)")
print(f"  RF(平衡) |AUC| = {results['RandomForest(平衡)']['auc_mean']:.3f} (5 折 CV)")
print(f"  关键特征(LR):")
for _, row in coef.head(5).iterrows():
    print(f"    {row['特征']}: coef={row['系数(标准化)']:.3f}")
