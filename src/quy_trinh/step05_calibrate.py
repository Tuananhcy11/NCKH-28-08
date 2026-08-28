# -*- coding: utf-8 -*-
"""BUOC 5 - Kiem dinh lai va hieu chinh vong lap.
   Tuong quan cua chuoi tham chieu 24/7 voi PAXG phai hoi tu ve tuong quan nen
   o Buoc 3, sai so cho phep +/- 0.05. Neu lech, hieu chinh he so (kappa, shrink)
   cho toi khi hoi tu. Toan bo do tren log return ln(P_t / P_{t-1}).
"""
import os, json
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from scipy import stats
from common import *
from step04_reference_series import build, news_frame

TOL, MAXIT = 0.05, 40

def corr_247(m):
    d = m[["r_247", "r_paxg" if "r_paxg" in m else "logret"]].dropna()
    d.columns = ["a", "b"]
    d = d[(d["a"] != 0) | (d["b"] != 0)]
    return float(stats.pearsonr(d["a"], d["b"])[0]), len(d)

def run():
    betas = json.load(open(os.path.join(PROC, "buoc03_he_so_nen.json")))
    news = news_frame()
    if len(news):
        save(news, os.path.join(PROC, "gdelt_cuong_do_tin_tuc.csv"))
    nhat_ky, tom_tat = [], []

    for tf in TFS:
        muc_tieu = betas[tf]["tat ca"]["pearson"]
        lam, shrink = 0.30, 1.0
        lo, hi = 0.05, 12.0          # bien do tim kiem cho kappa (nghich bien voi tuong quan)
        it, kappa, r = 0, 1.0, None
        log("BUOC 5 - hieu chinh %s, tuong quan nen muc tieu = %.4f" % (tf, muc_tieu))
        while it < MAXIT:
            it += 1
            kappa = 0.5 * (lo + hi)
            m = build(tf, lam=lam, shrink=shrink, kappa=kappa, betas=betas, news=news)
            m = m.rename(columns={"logret": "r_paxg"})
            r, n = corr_247(m)
            nhat_ky.append(dict(khung=tf, vong=it, kappa=round(kappa, 4), lam=lam,
                                shrink=shrink, tuong_quan=round(r, 4),
                                muc_tieu=muc_tieu, sai_so=round(r - muc_tieu, 4), n=n))
            log("   vong %2d: kappa=%.4f -> corr=%.4f (sai so %+.4f)" % (it, kappa, r, r - muc_tieu))
            if abs(r - muc_tieu) <= TOL:
                break
            if r > muc_tieu:      # tuong quan qua cao -> tang nhieu dac thu
                lo = kappa
            else:
                hi = kappa
            if hi - lo < 1e-4:
                break
        hoi_tu = abs(r - muc_tieu) <= TOL
        m = build(tf, lam=lam, shrink=shrink, kappa=kappa, betas=betas, news=news,
                  save_out=True, tag="")
        tom_tat.append(dict(khung=tf, kappa=round(kappa, 4), lambda_tin_tuc=lam, shrink=shrink,
                            tuong_quan_247=round(r, 4), tuong_quan_nen=muc_tieu,
                            sai_so=round(r - muc_tieu, 4), nguong=TOL,
                            hoi_tu="DAT" if hoi_tu else "CHUA DAT", so_vong=it))
        json.dump(dict(tf=tf, kappa=kappa, lam=lam, shrink=shrink),
                  open(os.path.join(PROC, "buoc05_hieu_chinh_%s.json" % tf), "w"), indent=1)

    save(pd.DataFrame(nhat_ky), os.path.join(TAB, "buoc05_nhat_ky_hieu_chinh.csv"))
    t = pd.DataFrame(tom_tat)
    save(t, os.path.join(TAB, "buoc05_ket_qua_hoi_tu.csv"))
    print(t.to_string(index=False))

if __name__ == "__main__":
    run()
