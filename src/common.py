# -*- coding: utf-8 -*-
"""Cau hinh va tien ich dung chung cho toan bo quy trinh 10 buoc."""
import os, sys, json, time, io
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
TAB = os.path.join(RES, "tables")
FIG = os.path.join(RES, "figures")
DOCS = os.path.join(ROOT, "docs")
for _d in (RAW, PROC, RES, TAB, FIG, DOCS):
    os.makedirs(_d, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
START = "2015-01-01"
END   = "2025-12-31"          # giai doan nghien cuu chinh
NOW   = pd.Timestamp.utcnow().strftime("%Y-%m-%d")   # moc thu thap toi da
TFS   = ["D1", "H1", "M15"]
SEED  = 42

def log(*a):
    print("[%s]" % time.strftime("%H:%M:%S"), *a, flush=True)

def save(df, path, **kw):
    df.to_csv(path, index=False, encoding="utf-8", **kw)
    log("  -> %s  (%d dong, %d cot)" % (os.path.relpath(path, ROOT), len(df), df.shape[1]))

def load(path, parse=("time",)):
    df = pd.read_csv(path)
    for c in parse:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], utc=True)
    return df

def logret(s):
    s = pd.Series(s).astype(float)
    return np.log(s / s.shift(1))

def resample_ohlc(df, rule):
    d = df.set_index("time")
    o = d["open"].resample(rule).first()
    h = d["high"].resample(rule).max()
    l = d["low"].resample(rule).min()
    c = d["close"].resample(rule).last()
    v = d["volume"].resample(rule).sum() if "volume" in d else None
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c})
    if v is not None:
        out["volume"] = v
    return out.dropna(subset=["close"]).reset_index()
