# -*- coding: utf-8 -*-
"""BUOC 3 - Do tuong quan nen giua log return cua XAU/USD va PAXG_USD
   tren cac phien 24/5 ma ca hai cung giao dich; phan tang theo khung thoi gian
   va theo che do bien dong (thap / trung binh / cao).
"""
import os, json
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from common import *

VOL_WIN = {"D1": 20, "H1": 120, "M15": 192}      # ~1 thang giao dich moi khung

def align(tf):
    """Ghep cap nen XAU - PAXG tren dung phien 24/5 chung."""
    x = load(os.path.join(RAW, "xau_%s.csv" % tf))[["time", "close"]].rename(columns={"close": "xau"})
    p = load(os.path.join(PROC, "paxg_usd_%s.csv" % tf))[["time", "close"]].rename(columns={"close": "paxg"})
    x["rx"] = logret(x["xau"]); p["rp"] = logret(p["paxg"])
    if tf == "D1":
        # Nen D1 cua XAU duoc dan nhan tai 22:00 UTC hom truoc (moc mo phien ngoai hoi),
        # nen phai cong 2 gio de lay dung NGAY GIAO DICH truoc khi ghep voi PAXG (moc 00:00).
        x["k"] = (x["time"] + pd.Timedelta(hours=2)).dt.date
        p["k"] = p["time"].dt.date
        m = pd.merge(x[["k", "time", "rx"]], p[["k", "rp"]], on="k").drop(columns="k")
    else:
        tol = pd.Timedelta("30min" if tf == "H1" else "8min")
        m = pd.merge_asof(x[["time", "rx"]].sort_values("time"),
                          p[["time", "rp"]].sort_values("time"),
                          on="time", direction="nearest", tolerance=tol)
    m = m.dropna(subset=["rx", "rp"])
    m = m[(m["rx"] != 0) | (m["rp"] != 0)]
    # loai bo cuoi tuan: chi giu phien 24/5
    m = m[m["time"].dt.dayofweek < 5].reset_index(drop=True)
    return m

def regime(m, tf):
    v = m["rx"].rolling(VOL_WIN[tf], min_periods=max(10, VOL_WIN[tf] // 3)).std()
    q1, q2 = v.quantile(1/3), v.quantile(2/3)
    r = pd.Series(np.where(v <= q1, "thap", np.where(v <= q2, "trung binh", "cao")), index=m.index)
    r[v.isna()] = "khong xac dinh"
    return r

def stat_block(d, nlag):
    if len(d) < 30:
        return None
    pe, ppe = stats.pearsonr(d["rp"], d["rx"])
    sp, psp = stats.spearmanr(d["rp"], d["rx"])
    X = sm.add_constant(d["rp"].values)
    ols = sm.OLS(d["rx"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": nlag})
    return dict(n=len(d),
                pearson=round(float(pe), 4), p_pearson=float("%.3g" % ppe),
                spearman=round(float(sp), 4), p_spearman=float("%.3g" % psp),
                beta=round(float(ols.params[1]), 4),
                se_beta_HAC=round(float(ols.bse[1]), 4),
                t_beta=round(float(ols.tvalues[1]), 2),
                alpha_bp=round(float(ols.params[0] * 1e4), 3),
                r2=round(float(ols.rsquared), 4),
                sd_rx_bp=round(float(d["rx"].std() * 1e4), 1),
                sd_rp_bp=round(float(d["rp"].std() * 1e4), 1))

def run():
    rows, betas = [], {}
    for tf in TFS:
        m = align(tf); m["che_do"] = regime(m, tf)
        nlag = {"D1": 5, "H1": 24, "M15": 96}[tf]
        b = stat_block(m, nlag)
        if b:
            rows.append(dict(khung=tf, che_do_bien_dong="tat ca",
                             tu=str(m['time'].min())[:10], den=str(m['time'].max())[:10], **b))
            betas[tf] = {"tat ca": b}
        for rg in ["thap", "trung binh", "cao"]:
            d = m[m["che_do"] == rg]
            bb = stat_block(d, nlag)
            if bb:
                rows.append(dict(khung=tf, che_do_bien_dong=rg,
                                 tu=str(d['time'].min())[:10], den=str(d['time'].max())[:10], **bb))
                betas[tf][rg] = bb
        save(m, os.path.join(PROC, "cap_xau_paxg_%s.csv" % tf))
    r = pd.DataFrame(rows)
    save(r, os.path.join(TAB, "buoc03_tuong_quan_nen.csv"))
    json.dump(betas, open(os.path.join(PROC, "buoc03_he_so_nen.json"), "w"), indent=1)
    print(r.to_string(index=False))

if __name__ == "__main__":
    run()
