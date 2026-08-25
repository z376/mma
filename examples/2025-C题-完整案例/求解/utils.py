"""mma 共享工具:绕过 Windows PowerShell GBK 环境问题。

主要修法:pandas read_csv 在 GBK 环境下会乱码,所以用 io.StringIO 强制 utf-8 读。
"""
import io
import pandas as pd
from pathlib import Path


def read_csv_safe(path, **kwargs):
    """强制 utf-8-sig 读 CSV,绕过 PowerShell GBK 环境问题。"""
    p = Path(path)
    with open(p, "r", encoding="utf-8-sig") as f:
        return pd.read_csv(f, **kwargs)


def save_csv(df, path, **kwargs):
    """写 CSV(utf-8-sig,Excel 兼容)。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, encoding="utf-8-sig", **kwargs)
