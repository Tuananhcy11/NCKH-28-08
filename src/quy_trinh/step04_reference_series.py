# -*- coding: utf-8 -*-
"""BUOC 4 - Xay dung chuoi tham chieu cuoi tuan bang mo hinh NEO TUONG QUAN.
   Bien dong cuoi tuan cua vang duoc uoc luong tu log return PAXG, hieu chinh
   bang he so beta uoc luong o Buoc 3, va dieu bien bang cuong do tin tuc
   FinBERT-GDELT.

       r_hat_t = beta(che do bien dong) * s * r_PAXG_t * (1 + lambda * I_t)

   trong do  s      : he so co gian hieu chinh (calibration shrink, Buoc 5)
             I_t    : cuong do tin tuc chuan hoa (z-score, cat o +/-3)
             lambda : bien do dieu bien tin tuc (Buoc 5)
"""
import os, json, glob
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from common import *

W_THEME = {"gold": 0.5, "macro": 0.3, "geopolitics": 0.2}   # trong so ba nhom tu khoa

# ------------------------------------------------------------- tin tuc GDELT
def news_frame():
    """Gop cac chuoi GDELT co san thanh cuong do tin tuc I_t va diem tam ly S_t (theo ngay)."""
    parts = {}
    for f in glob.glob(os.path.join(RAW, "gdelt_*_*.csv")):
        b = os.path.basename(f)[:-4].split("_")           # gdelt, <theme>, <tag>
        if len(b) < 3: continue
        theme, tag = b[1], b[2]
        d = load(f)
        if d.empty: continue
        col = [c for c in d.columns if c != "time"][0]
        d = d[["time", col]].rename(columns={col: "%s_%s" % (theme, tag)})
        d["ngay"] = d["time"].dt.floor("D")
        parts[(theme, tag)] = d.groupby("ngay")[["%s_%s" % (theme, tag)]].mean()
    if not parts:
        log("  ! chua co du lieu GDELT - dat I_t = 0, S_t = 0")
        return pd.DataFrame(columns=["ngay", "I", "S"])
    df = pd.concat(parts.values(), axis=1).sort_index()

    def z(s, win=180):
        m = s.rolling(win, min_periods=30).mean(); v = s.rolling(win, min_periods=30).std()
        return ((s - m) / v.replace(0, np.nan)).clip(-3, 3).fillna(0.0)

    I = pd.Series(0.0, index=df.index); S = pd.Series(0.0, index=df.index); wI = wS = 0.0
    for th, w in W_THEME.items():
        cv, ct = "%s_vol" % th, "%s_tone" % th
        if cv in df: I = I + w * z(df[cv]);  wI += w
        if ct in df: S = S + w * z(df[ct]);  wS += w
    if wI: I /= wI
    if wS: S /= wS
    out = pd.DataFrame({"ngay": df.index, "I": I.values, "S": S.values})
    # cuong do tin tuc la ve LON NHO cua dong tin, khong phai chieu -> dung tri tuyet doi
    out["I"] = out["I"].abs()
    return out.reset_index(drop=True)

# ------------------------------------------------- xac dinh khoang cuoi tuan
def weekend_mask(t):
    """Cac moc nam ngoai phien 24/5: tu 21:00 UTC thu Sau den 22:00 UTC Chu nhat."""
    dow, hh = t.dt.dayofweek, t.dt.hour
    return ((dow == 4) & (hh >= 21)) | (dow == 5) | ((dow == 6) & (hh < 22))

# ------------------------------------------------------------------ xay chuoi
def build(tf="H1", lam=0.30, shrink=1.0, kappa=1.0, betas=None, news=None, save_out=False, tag=""):
    if betas is None:
        betas = json.load(open(os.path.join(PROC, "buoc03_he_so_nen.json")))
    if news is None:
        news = news_frame()
    bt = betas[tf]

    p = load(os.path.join(PROC, "paxg_usd_%s.csv" % tf))[["time", "close", "logret"]]
    p = p.dropna(subset=["logret"]).reset_index(drop=True)
    x = load(os.path.join(RAW, "xau_%s.csv" % tf))[["time", "close"]].rename(columns={"close": "xau"})

    # che do bien dong lay tu chinh PAXG (co san 24/7)
    win = {"D1": 20, "H1": 120, "M15": 192}[tf]
    v = p["logret"].rolling(win, min_periods=win // 3).std()
    q1, q2 = v.quantile(1/3), v.quantile(2/3)
    p["che_do"] = np.where(v <= q1, "thap", np.where(v <= q2, "trung binh", "cao"))
    p.loc[v.isna(), "che_do"] = "tat ca"
    p["beta"] = p["che_do"].map(lambda r: bt.get(r, bt["tat ca"])["beta"])

    # cuong do tin tuc
    p["ngay"] = p["time"].dt.floor("D")
    if len(news):
        p = p.merge(news, on="ngay", how="left")
    else:
        p["I"] = 0.0; p["S"] = 0.0
    p[["I", "S"]] = p[["I", "S"]].fillna(0.0)

    p["cuoi_tuan"] = weekend_mask(p["time"])
    # phan du dac thu: chuoi tham chieu phai tai tao DUNG cau truc tuong quan nen,
    # khong duoc la ban sao 1:1 cua PAXG. Bien do phan du suy ra tu R^2 nen.
    r2 = float(bt["tat ca"]["r2"])
    sd_res = np.sqrt(max(1e-12, (1.0 - r2))) * float(bt["tat ca"]["sd_rx_bp"]) / 1e4
    rng = np.random.default_rng(SEED)
    eps = rng.standard_normal(len(p)) * sd_res * kappa
    p["r_hat"] = p["beta"] * shrink * p["logret"] * (1.0 + lam * p["I"]) + eps

    # chuoi 24/7: trong phien 24/5 dung log return that cua XAU, ngoai phien dung r_hat
    m = pd.merge_asof(p.sort_values("time"), x.sort_values("time"), on="time",
                      direction="nearest",
                      tolerance=pd.Timedelta({"D1": "12h", "H1": "30min", "M15": "8min"}[tf]))
    m["r_xau"] = np.log(m["xau"] / m["xau"].shift(1))
    m["r_247"] = np.where(m["cuoi_tuan"] | m["r_xau"].isna(), m["r_hat"], m["r_xau"])
    base = m["xau"].dropna()
    p0 = float(base.iloc[0]) if len(base) else 1800.0
    m["gia_247"] = p0 * np.exp(m["r_247"].fillna(0).cumsum())

    if save_out:
        out = m[["time", "gia_247", "r_247", "r_hat", "logret", "beta", "I", "S", "cuoi_tuan", "che_do"]]
        out = out.rename(columns={"logret": "r_paxg"})
        save(out, os.path.join(PROC, "chuoi_247_%s%s.csv" % (tf, tag)))
    return m

if __name__ == "__main__":
    news = news_frame()
    if len(news):
        save(news, os.path.join(PROC, "gdelt_cuong_do_tin_tuc.csv"))
    for tf in TFS:
        log("BUOC 4 - dung chuoi tham chieu %s (lambda=0.30, shrink=1.0 - so bo)" % tf)
        m = build(tf, save_out=True, news=news, tag="_sobo")
        log("   %d moc, %d moc cuoi tuan (%.1f%%)" % (len(m), int(m["cuoi_tuan"].sum()),
            100 * m["cuoi_tuan"].mean()))
