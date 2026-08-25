# -*- coding: utf-8 -*-
"""
预处理数据:读 附件.xlsx(2 sheet),清洗 + 特征工程 + 保存 预处理数据.csv
供问题 1-4 共享。
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

# 路径
BASE = Path(__file__).resolve().parent
WS = BASE.parent
XLSX = WS / "数据" / "附件.xlsx"
OUT = BASE / "预处理数据.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

# ========== 1. 读取数据 ==========
print("=" * 60)
print("预处理数据 — 2025 国赛 C 题")
print("=" * 60)

xl = pd.ExcelFile(XLSX)
print(f"sheets: {xl.sheet_names}")

# 男胎:第一行是中文表头(从 xlsx 看,序号是 col 0,实际 xlsx header=0)
df_m_raw = pd.read_excel(XLSX, sheet_name="男胎检测数据")
df_f_raw = pd.read_excel(XLSX, sheet_name="女胎检测数据")
print(f"男胎 raw: {df_m_raw.shape}")
print(f"女胎 raw: {df_f_raw.shape}")

# ========== 2. 数据类型转换 ==========
def convert_types(df):
    df = df.copy()
    # 数值列
    num_cols = ["年龄", "身高", "体重", "原始读段数", "在参考基因组上比对的比例",
                "重复读段的比例", "唯一比对的读段数", "GC含量",
                "13号染色体的Z值", "18号染色体的Z值", "21号染色体的Z值",
                "X染色体的Z值", "Y染色体的Z值", "Y染色体浓度", "X染色体浓度",
                "13号染色体的GC含量", "18号染色体的GC含量", "21号染色体的GC含量",
                "被过滤掉读段数的比例", "怀孕次数", "生产次数"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 末次月经 / 检测日期 → datetime
    if "末次月经" in df.columns:
        df["末次月经"] = pd.to_datetime(df["末次月经"], errors="coerce")
    if "检测日期" in df.columns:
        df["检测日期"] = pd.to_datetime(df["检测日期"], errors="coerce")

    # 标签:胎儿是否健康 → 1=是(健康),0=否(异常)
    if "胎儿是否健康" in df.columns:
        df["is_healthy"] = df["胎儿是否健康"].map({"是": 1, "否": 0})

    return df

df_m = convert_types(df_m_raw)
df_f = convert_types(df_f_raw)

print(f"男胎 cleaned: {df_m.shape},缺失率: {df_m.isnull().mean().mean():.3f}")
print(f"女胎 cleaned: {df_f.shape},缺失率: {df_f.isnull().mean().mean():.3f}")

# ========== 3. 孕周数值化("11w+6" → 11+6/7 = 11.857) ==========
def parse_gestational_week(s):
    """'11w+6' → 11.857, '12w' → 12.0"""
    if pd.isna(s):
        return np.nan
    s = str(s).strip()
    if "w" not in s:
        return np.nan
    try:
        parts = s.split("w")
        weeks = int(parts[0])
        if "+" in parts[1]:
            days = int(parts[1].split("+")[1])
        else:
            days = 0
        return weeks + days / 7.0
    except Exception:
        return np.nan

df_m["孕周_数值"] = df_m["检测孕周"].apply(parse_gestational_week)
df_f["孕周_数值"] = df_f["检测孕周"].apply(parse_gestational_week)
print(f"男胎 孕周_数值: mean={df_m['孕周_数值'].mean():.2f}, range=[{df_m['孕周_数值'].min():.1f}, {df_m['孕周_数值'].max():.1f}]")

# ========== 4. 特征工程 ==========
# Y 浓度达标(>= 4%)
df_m["Y_达标"] = (df_m["Y染色体浓度"] >= 0.04).astype(int)

# 女胎 Z 值异常标记
for col in ["13号染色体的Z值", "18号染色体的Z值", "21号染色体的Z值", "X染色体的Z值"]:
    if col in df_f.columns:
        df_f[f"{col}_abs"] = df_f[col].abs()
        df_f[f"{col}_is_high"] = (df_f[col].abs() > 3).astype(int)

df_f["is_high_risk"] = (
    df_f.get("13号染色体的Z值_is_high", 0)
    | df_f.get("18号染色体的Z值_is_high", 0)
    | df_f.get("21号染色体的Z值_is_high", 0)
).astype(int)

# BMI 分组(题目建议 5 组)
bmi_bins = [0, 28, 32, 36, 40, 100]
bmi_labels = ["[20,28)", "[28,32)", "[32,36)", "[36,40)", "40+"]
df_m["BMI_组"] = pd.cut(df_m["孕妇BMI"], bins=bmi_bins, labels=bmi_labels, right=False)
df_f["BMI_组"] = pd.cut(df_f["孕妇BMI"], bins=bmi_bins, labels=bmi_labels, right=False)

# IVF 妊娠 → 0/1
df_m["IVF_数值"] = (df_m["IVF妊娠"] == "IVF妊娠").astype(int)
df_f["IVF_数值"] = (df_f["IVF妊娠"] == "IVF妊娠").astype(int)

# ========== 5. 数据概况打印 ==========
print()
print("=" * 60)
print("男胎数据概况")
print("=" * 60)
print(f"Y 染色体浓度: mean={df_m['Y染色体浓度'].mean()*100:.2f}%, 达标率={df_m['Y_达标'].mean()*100:.1f}%")
print(f"BMI 分布: {df_m['BMI_组'].value_counts().sort_index().to_dict()}")
print(f"孕周: {df_m['孕周_数值'].describe()[['min','25%','50%','75%','max']].to_dict()}")
print(f"孕妇代码唯一: {df_m['孕妇代码'].nunique()}")
print(f"Y 浓度 - 孕周相关系数: {df_m['Y染色体浓度'].corr(df_m['孕周_数值']):.3f}")
print(f"Y 浓度 - BMI 相关系数: {df_m['Y染色体浓度'].corr(df_m['孕妇BMI']):.3f}")

print()
print("=" * 60)
print("女胎数据概况")
print("=" * 60)
print(f"健康比例: 是={df_f['is_healthy'].sum()}, 否={(df_f['is_healthy']==0).sum()}, 缺失={df_f['is_healthy'].isnull().sum()}")
print(f"|Z_13|>3: {(df_f['13号染色体的Z值'].abs() > 3).sum()}")
print(f"|Z_18|>3: {(df_f['18号染色体的Z值'].abs() > 3).sum()}")
print(f"|Z_21|>3: {(df_f['21号染色体的Z值'].abs() > 3).sum()}")
print(f"is_high_risk(任一|Z|>3): {df_f['is_high_risk'].sum()}")
print(f"孕妇代码唯一: {df_f['孕妇代码'].nunique()}")

# ========== 6. 保存合并的预处理数据 ==========
df_m["胎别"] = "男"
df_f["胎别"] = "女"
# 保留所有列(不去 common_cols,男胎的 Y 染色体浓度列对女胎是 NaN,反之亦然)
df_all = pd.concat([df_m, df_f], ignore_index=True)
df_all.to_csv(OUT, index=False, encoding="utf-8-sig")
print()
print(f"✅ 预处理完成,共 {len(df_all)} 条记录,共 {df_all.shape[1]} 列")
print(f"输出: {OUT}")
print(f"  男胎: {len(df_m)} 条 (含 Y 染色体浓度列)")
print(f"  女胎: {len(df_f)} 条 (Y 染色体浓度为 NaN)")
