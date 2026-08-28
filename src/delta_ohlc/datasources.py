# -*- coding: utf-8 -*-
"""Nap du lieu dau vao cho pipeline delta OHLC tu kho du lieu cua du an."""
import os, sys, time, json
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
from common import RAW, PROC, UA, START, END, log     # noqa: E402

MACRO = {"dxy": "DX-Y.NYB", "us10y": "^TNX", "vix": "^VIX"}


def nap_gia(khung="H1"):
    """Tra ve (df_xau, df_paxg_usdt, df_usdt_usd) o dang tho cho module 1."""
    xau = pd.read_csv(os.path.join(RAW, "xau_%s.csv" % khung))
    paxg = pd.read_csv(os.path.join(RAW, "paxg_%s.csv" % khung))
    ten_peg = "usdtusd_%s.csv" % ("H1" if khung in ("H1", "M15") else "D1")
    peg = pd.read_csv(os.path.join(RAW, ten_peg))
    return xau, paxg, peg


def nap_vi_mo(tai_lai=False):
    """DXY, lai suat trai phieu My 10 nam, VIX theo ngay (nguon Yahoo Finance)."""
    f = os.path.join(RAW, "vimo_D1.csv")
    if os.path.exists(f) and not tai_lai:
        d = pd.read_csv(f)
        d["time"] = pd.to_datetime(d["time"], utc=True)
        return d.set_index("time")

    import requests
    S = requests.Session(); S.headers.update({"User-Agent": UA})
    p1 = int(pd.Timestamp(START, tz="UTC").timestamp())
    p2 = int(pd.Timestamp(END, tz="UTC").timestamp()) + 86400
    khung = {}
    for ten, ma in MACRO.items():
        for k in range(5):
            r = S.get("https://query1.finance.yahoo.com/v8/finance/chart/" + ma,
                      params={"interval": "1d", "period1": p1, "period2": p2}, timeout=40)
            if r.status_code == 200:
                break
            time.sleep(3 * (k + 1))
        res = r.json()["chart"]["result"][0]
        s = pd.Series(res["indicators"]["quote"][0]["close"],
                      index=pd.to_datetime(res["timestamp"], unit="s", utc=True)).dropna()
        # Yahoo tra moc dong phien theo gio dia phuong cua tung san (13:30, 14:30...),
        # nen PHAI ha ve moc ngay TRUOC khi ghep - neu khong, ba chuoi se nam tren ba
        # luoi thoi gian khac nhau va bang ghep se gan nhu toan NaN.
        s.index = s.index.floor("D")
        s = s[~s.index.duplicated(keep="last")]
        khung[ten] = s
        log("   vi mo %s (%s): %d diem" % (ten, ma, len(khung[ten])))
    d = pd.concat(khung, axis=1).sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.index.name = "time"
    d.to_csv(f, encoding="utf-8")
    return d


def nap_tin_tuc():
    """SENT_DIR (huong tam ly) va SENT_INTENSITY (cuong do tin) tu GDELT.

    Ba nhom tu khoa gop theo trong so vang 0.5 / vi mo 0.3 / dia chinh tri 0.2,
    moi chuoi chuan hoa z-score truot 180 ngay va cat o +/-3.
    """
    import glob
    W = {"gold": 0.5, "macro": 0.3, "geopolitics": 0.2}
    phan = {}
    for f in glob.glob(os.path.join(RAW, "gdelt_*_*.csv")):
        b = os.path.basename(f)[:-4].split("_")
        if len(b) < 3:
            continue
        d = pd.read_csv(f)
        if d.empty:
            continue
        d["time"] = pd.to_datetime(d["time"], utc=True)
        col = [c for c in d.columns if c != "time"][0]
        phan[(b[1], b[2])] = (d.set_index(d["time"].dt.floor("D"))[[col]]
                              .groupby(level=0).mean())
    if not phan:
        return None
    df = pd.concat(phan.values(), axis=1).sort_index()

    def z(s, win=180):
        m = s.rolling(win, min_periods=30).mean()
        v = s.rolling(win, min_periods=30).std()
        return ((s - m) / v.replace(0, np.nan)).clip(-3, 3).fillna(0.0)

    I = pd.Series(0.0, index=df.index); D = pd.Series(0.0, index=df.index)
    wi = wd = 0.0
    for th, w in W.items():
        cv, ct = "%s_vol" % th, "%s_tone" % th
        if cv in df:
            I = I + w * z(df[cv]); wi += w
        if ct in df:
            D = D + w * z(df[ct]); wd += w
    if wi:
        I /= wi
    if wd:
        D /= wd
    out = pd.DataFrame({"SENT_INTENSITY": I.abs(), "SENT_DIR": D})
    out.index.name = "time"
    return out
