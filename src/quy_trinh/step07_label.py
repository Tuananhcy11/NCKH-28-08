# -*- coding: utf-8 -*-
"""BUOC 7 - Gan nhan ba trang thai Tang / Giam / Sideway tren chuoi 24/5
   bang Triple Barrier Method co rao can theo ATR, doi chieu cheo voi
   bo quy tac EMA200 - ADX. Dong thoi dung bo dac trung dau vao cho Buoc 8.
"""
import os
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from common import *
import indicators as ta

HORIZON = {"D1": 10, "H1": 24, "M15": 32}     # so nen toi da giu lenh (rao can doc)
M_ATR   = 1.5                                  # he so rao can ngang theo ATR
ADX_NG  = 25.0
MUC_SIDEWAY = 0.25                             # ty le Sideway muc tieu khi hieu chinh rao can
LUOI_M = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0]

# ------------------------------------------------------------------ dac trung
def features(df, tf):
    d = df.copy()
    c, h, l = d["close"], d["high"], d["low"]
    d["ret1"] = np.log(c / c.shift(1))
    for n in (2, 3, 5, 10, 20):
        d["ret%d" % n] = np.log(c / c.shift(n))
    for n in (10, 20, 50, 200):
        d["ema%d" % n] = ta.ema(c, n)
        d["kc_ema%d" % n] = (c - d["ema%d" % n]) / c
    d["ema10_20"] = (d["ema10"] - d["ema20"]) / c
    d["ema20_50"] = (d["ema20"] - d["ema50"]) / c
    d["ema50_200"] = (d["ema50"] - d["ema200"]) / c
    d["macd"], d["macd_signal"], d["macd_hist"] = ta.macd(c)
    d["macd"] /= c; d["macd_signal"] /= c; d["macd_hist"] /= c
    d["rsi14"] = ta.rsi(c, 14)
    d["rsi7"]  = ta.rsi(c, 7)
    d["atr14"] = ta.atr(h, l, c, 14)
    d["atr_pct"] = d["atr14"] / c
    d["adx14"], d["pdi"], d["mdi"] = ta.adx(h, l, c, 14)
    bu, bm, bl, bw = ta.bollinger(c)
    d["bb_width"] = bw
    d["bb_pos"] = (c - bl) / (bu - bl).replace(0, np.nan)
    d["stoch_k"], d["stoch_d"] = ta.stoch(h, l, c)
    for n in (5, 20, 60):
        d["vol%d" % n] = d["ret1"].rolling(n).std()
    d["vol_ratio"] = d["vol5"] / d["vol20"]
    d["bien_do"] = (h - l) / c
    d["than_nen"] = (c - d["open"]) / c
    if "volume" in d:
        d["kl_z"] = (d["volume"] - d["volume"].rolling(50).mean()) / d["volume"].rolling(50).std()
    d["gio"] = d["time"].dt.hour
    d["thu"] = d["time"].dt.dayofweek

    # ba dac trung nen tu chuoi 24/7 (Buoc 6)
    f = os.path.join(PROC, "dac_trung_cuoi_tuan_%s.csv" % tf)
    if os.path.exists(f):
        wk = load(f)
        d = d.merge(wk[["time", "bien_dong_cuoi_tuan", "lech_tich_luy",
                        "diem_tam_ly_cuoi_tuan"]], on="time", how="left")
        for cc in ("bien_dong_cuoi_tuan", "lech_tich_luy", "diem_tam_ly_cuoi_tuan"):
            d[cc] = d[cc].fillna(0.0)
            d["co_" + cc] = (d[cc] != 0).astype(int)
    return d

# ------------------------------------------------------- Triple Barrier Method
def triple_barrier(d, tf, m=M_ATR):
    H = HORIZON[tf]
    c = d["close"].values; hi = d["high"].values; lo = d["low"].values
    a = d["atr14"].values
    n = len(d)
    nhan = np.full(n, np.nan); cham = np.full(n, np.nan); tg = np.full(n, np.nan)
    for i in range(n - 1):
        if not np.isfinite(a[i]) or a[i] <= 0: continue
        up, dn = c[i] + m * a[i], c[i] - m * a[i]
        j_end = min(i + H, n - 1)
        lab, k = 0, j_end
        for j in range(i + 1, j_end + 1):
            tu = hi[j] >= up; td = lo[j] <= dn
            if tu and td:                      # cham ca hai trong cung nen
                lab, k = 0, j; break
            if tu: lab, k = 1, j; break
            if td: lab, k = -1, j; break
        nhan[i] = lab; cham[i] = c[k]; tg[i] = k - i
    d = d.copy()
    d["nhan"] = nhan                  # 1 Tang, -1 Giam, 0 Sideway
    d["gia_cham"] = cham
    d["so_nen_giu"] = tg
    d["rao_tren"] = d["close"] + m * d["atr14"]
    d["rao_duoi"] = d["close"] - m * d["atr14"]
    return d

# ----------------------------------------------------- doi chieu EMA200 - ADX
def quy_tac_ema_adx(d):
    manh = d["adx14"] >= ADX_NG
    tren = d["close"] > d["ema200"]
    huong = d["pdi"] > d["mdi"]
    return np.where(manh & tren & huong, 1, np.where(manh & (~tren) & (~huong), -1, 0))

def run():
    tong = []
    hc = []
    for tf in TFS:
        x = load(os.path.join(RAW, "xau_%s.csv" % tf)).sort_values("time").reset_index(drop=True)
        d0 = features(x, tf)
        # hieu chinh do rong rao can ATR de bai toan ba lop khong bi suy bien
        best, bm = None, M_ATR
        for m in LUOI_M:
            t = triple_barrier(d0, tf, m=m)
            sw = float((t["nhan"] == 0).mean())
            hc.append(dict(khung=tf, he_so_ATR=m, ty_le_Sideway=round(sw, 4)))
            log("   %s m=%.2f -> Sideway %.3f" % (tf, m, sw))
            if best is None or abs(sw - MUC_SIDEWAY) < best:
                best, bm = abs(sw - MUC_SIDEWAY), m
        log("   %s chon he so ATR = %.2f" % (tf, bm))
        d = triple_barrier(d0, tf, m=bm)
        d["he_so_ATR"] = bm
        d["nhan_ema_adx"] = quy_tac_ema_adx(d)
        d = d[d["nhan"].notna()].reset_index(drop=True)
        d["nhan"] = d["nhan"].astype(int)
        save(d, os.path.join(PROC, "bo_du_lieu_%s.csv" % tf))

        pp = d["nhan"].value_counts(normalize=True).reindex([1, 0, -1]).fillna(0)
        k = cohen_kappa_score(d["nhan"], d["nhan_ema_adx"])
        khop = float((d["nhan"] == d["nhan_ema_adx"]).mean())
        cm = confusion_matrix(d["nhan"], d["nhan_ema_adx"], labels=[1, 0, -1])
        pd.DataFrame(cm, index=["TBM_Tang", "TBM_Sideway", "TBM_Giam"],
                     columns=["QT_Tang", "QT_Sideway", "QT_Giam"]).to_csv(
            os.path.join(TAB, "buoc07_doi_chieu_%s.csv" % tf), encoding="utf-8")
        tong.append(dict(khung=tf, so_mau=len(d),
                         tu=str(d["time"].min())[:10], den=str(d["time"].max())[:10],
                         ty_le_Tang=round(float(pp[1]), 4),
                         ty_le_Sideway=round(float(pp[0]), 4),
                         ty_le_Giam=round(float(pp[-1]), 4),
                         so_nen_giu_tb=round(float(d["so_nen_giu"].mean()), 2),
                         khop_EMA200_ADX=round(khop, 4), cohen_kappa=round(float(k), 4),
                         he_so_ATR=bm, so_dac_trung=int(d.shape[1])))
    save(pd.DataFrame(hc), os.path.join(TAB, "buoc07_hieu_chinh_rao_can.csv"))
    t = pd.DataFrame(tong)
    save(t, os.path.join(TAB, "buoc07_gan_nhan.csv"))
    print(t.to_string(index=False))

if __name__ == "__main__":
    run()
