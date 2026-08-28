# -*- coding: utf-8 -*-
"""BUOC 9 - Backtest theo luoi hai chieu:
   khoi luong vao lenh {0.1; 0.2; 0.3; 0.5} lot
   khoang cat lo      {5; 10; 15; 20; 25; 30} gia (USD)
   ty le R:R          {1:1.5; 1:2.0}
   Chay song song che do dinh co theo phan tram rui ro de kiem chung do vung.
   Moi giao dich deu tinh tren chuoi 24/5 goc.
"""
import os, itertools, json
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from common import *
from step07_label import HORIZON

LOTS    = [0.1, 0.2, 0.3, 0.5]
SLS     = [5, 10, 15, 20, 25, 30]
RRS     = [1.5, 2.0]
RUI_RO  = [0.005, 0.01, 0.02]          # che do dinh co theo % rui ro
VON_BD  = 10000.0
HOP_DONG = 100.0                        # 1 lot XAU/USD = 100 ounce -> 1 USD gia = 100 USD/lot
SPREAD  = 0.30                          # chenh lech mua-ban (USD tren mot ounce)
HOA_HONG = 7.0                          # hoa hong khu hoi tren mot lot

def mo_phong(bars, tin_hieu, sl, rr, lot=None, ty_le_rui_ro=None, H=24):
    """Mo phong tuan tu: moi thoi diem chi giu toi da mot vi the."""
    o, h, l, c = (bars[k].values for k in ("open", "high", "low", "close"))
    n = len(c); von = VON_BD; i = 0
    lich_su = []
    tp = sl * rr
    while i < n - 1:
        s = tin_hieu[i]
        if not np.isfinite(s) or s == 0:
            i += 1; continue
        vao = c[i] + (SPREAD / 2) * s                    # tra chenh lech khi vao
        klg = lot if lot is not None else max(0.01, (ty_le_rui_ro * von) / (sl * HOP_DONG))
        gia_sl = vao - s * sl
        gia_tp = vao + s * tp
        ket = min(i + H, n - 1); ra = c[ket]; ly_do = "het_han"
        for j in range(i + 1, ket + 1):
            if s > 0:
                if l[j] <= gia_sl: ra, ket, ly_do = gia_sl, j, "cat_lo"; break
                if h[j] >= gia_tp: ra, ket, ly_do = gia_tp, j, "chot_lai"; break
            else:
                if h[j] >= gia_sl: ra, ket, ly_do = gia_sl, j, "cat_lo"; break
                if l[j] <= gia_tp: ra, ket, ly_do = gia_tp, j, "chot_lai"; break
        pnl = s * (ra - vao) * klg * HOP_DONG - HOA_HONG * klg - (SPREAD / 2) * klg * HOP_DONG
        von += pnl
        lich_su.append((i, ket, s, klg, vao, ra, pnl, von, ly_do))
        i = ket + 1
        if von <= 0.2 * VON_BD:                          # dung khi chay von
            break
    return pd.DataFrame(lich_su, columns=["vao_i","ra_i","huong","lot","gia_vao","gia_ra",
                                          "loi_nhuan","von","ly_do"])

def chi_tieu(tr, so_nen, buoc_moi_nam):
    if tr.empty:
        return dict(so_lenh=0, loi_nhuan_rong=0.0, ty_le_thang=np.nan, he_so_loi_nhuan=np.nan,
                    sharpe=np.nan, sortino=np.nan, sut_giam_toi_da=np.nan, ky_vong=np.nan,
                    calmar=np.nan, loi_nhuan_pct=0.0)
    p = tr["loi_nhuan"].values
    von = np.concatenate([[VON_BD], tr["von"].values])
    dinh = np.maximum.accumulate(von)
    dd = (von - dinh) / dinh
    r = p / np.concatenate([[VON_BD], tr["von"].values[:-1]])
    n_nam = max(so_nen / buoc_moi_nam, 1e-9)
    tan_suat = len(tr) / n_nam
    sd = r.std(ddof=1) if len(r) > 1 else np.nan
    down = r[r < 0].std(ddof=1) if (r < 0).sum() > 1 else np.nan
    lai = p[p > 0].sum(); lo = -p[p < 0].sum()
    ln_pct = (von[-1] / VON_BD - 1)
    cagr = (von[-1] / VON_BD) ** (1 / n_nam) - 1
    return dict(so_lenh=len(tr), loi_nhuan_rong=round(float(p.sum()), 2),
                loi_nhuan_pct=round(float(ln_pct * 100), 2),
                ty_le_thang=round(float((p > 0).mean()), 4),
                he_so_loi_nhuan=round(float(lai / lo), 3) if lo > 0 else np.inf,
                sharpe=round(float(r.mean() / sd * np.sqrt(tan_suat)), 3) if sd and sd > 0 else np.nan,
                sortino=round(float(r.mean() / down * np.sqrt(tan_suat)), 3) if down and down > 0 else np.nan,
                sut_giam_toi_da=round(float(dd.min() * 100), 2),
                calmar=round(float(cagr / abs(dd.min())), 3) if dd.min() < 0 else np.nan,
                ky_vong=round(float(p.mean()), 2))

BUOC_NAM = {"D1": 252, "H1": 252 * 24, "M15": 252 * 96}

def run():
    ket_qua, tat_ca_lenh = [], []
    for tf in TFS:
        d = load(os.path.join(PROC, "bo_du_lieu_%s.csv" % tf))
        pred = load(os.path.join(PROC, "du_bao_%s.csv" % tf))
        H = HORIZON[tf]
        for mo, g in pred.groupby("mo_hinh"):
            g = g.sort_values("time")
            bars = d.merge(g[["time", "du_bao"]], on="time", how="inner").sort_values("time").reset_index(drop=True)
            sig = bars["du_bao"].values.astype(float)
            for lot, sl, rr in itertools.product(LOTS, SLS, RRS):
                tr = mo_phong(bars, sig, sl, rr, lot=lot, H=H)
                m = chi_tieu(tr, len(bars), BUOC_NAM[tf])
                ket_qua.append(dict(khung=tf, mo_hinh=mo, che_do="lot co dinh", lot=lot,
                                    cat_lo=sl, rr=rr, **m))
                if abs(lot - 0.1) < 1e-9 and sl == 15 and abs(rr - 2.0) < 1e-9:
                    tr2 = tr.copy(); tr2["khung"] = tf; tr2["mo_hinh"] = mo
                    tat_ca_lenh.append(tr2)
            for rrisk, sl, rr in itertools.product(RUI_RO, SLS, RRS):
                tr = mo_phong(bars, sig, sl, rr, ty_le_rui_ro=rrisk, H=H)
                m = chi_tieu(tr, len(bars), BUOC_NAM[tf])
                ket_qua.append(dict(khung=tf, mo_hinh=mo, che_do="%% rui ro %.1f%%" % (rrisk * 100),
                                    lot=np.nan, cat_lo=sl, rr=rr, **m))
            log("   xong %s / %s" % (tf, mo))
    r = pd.DataFrame(ket_qua)
    save(r, os.path.join(TAB, "buoc09_luoi_backtest.csv"))
    if tat_ca_lenh:
        save(pd.concat(tat_ca_lenh, ignore_index=True), os.path.join(PROC, "lenh_cau_hinh_chuan.csv"))
    top = (r[r["che_do"] == "lot co dinh"]
           .sort_values(["khung", "loi_nhuan_rong"], ascending=[True, False])
           .groupby("khung").head(3))
    print(top.to_string(index=False))
    return r

if __name__ == "__main__":
    run()
