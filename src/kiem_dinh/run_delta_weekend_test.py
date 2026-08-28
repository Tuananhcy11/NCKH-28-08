# -*- coding: utf-8 -*-
"""Do do chinh xac THUC TE cua bo du lieu tai tao trong dieu kien phien dong cua.

VAN DE
------
Cac chi so R2 / MAE o run_delta_pipeline.py deu do tren du bao MOT BUOC, trong do
nen XAU lien truoc DA QUAN SAT DUOC (cac dac trung Delta_close_tre1..5 lay tu no).
Nhung muc dich cua chuoi tai tao la lap phien CUOI TUAN - luc do khong co bat ky
nen XAU nao trong suot 48+ gio, nen toan bo nhom dac trung "tri nho Delta" bi DONG
BANG tai gia tri cuoi cung quan sat duoc truoc khi thi truong dong cua.

CACH DO
-------
Mo phong dung dieu kien do tren chinh du lieu 24/5 (noi co dap an):
  1. Chon nhieu diem bat dau khoi s.
  2. Khop mo hinh tren cua so [s-W, s) nhu binh thuong.
  3. Du bao cac nen s, s+1, ..., s+H-1. Voi MOI nen trong khoi, cac dac trung
     thuoc nhom "tri nho Delta" bi thay bang gia tri tai s-1 (dong bang), dung
     nhu khi thi truong dong cua. Cac dac trung con lai (PAXG, vi mo, tin tuc,
     lich) van cap nhat vi chung luon co san 24/7.
  4. So sanh sai so theo tung buoc h = 1..H.

BA MOC DOI CHIEU
----------------
  mo_hinh   : du bao cua pipeline trong dieu kien dong bang
  giu_delta : gia dinh tam thuong nhat - giu nguyen Delta cuoi cung quan sat duoc
              (tuc \\hat{XAU} = PAXG * exp(Delta_{s-1}))
  mot_buoc  : du bao mot buoc co day du tri nho - tran tren khong the vuot
"""
import time
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import TAB, PROC, log, save
from delta_ohlc import clean_and_align_ohlc, build_feature_matrix
from delta_ohlc.model import _uoc_luong_ridge
from delta_ohlc import datasources as ds

COLS = ["open", "high", "low", "close"]
TARGETS = ["Delta_" + c for c in COLS]

# chan troi mo phong xap xi mot ky nghi cuoi tuan cua tung khung
CHAN_TROI = {"D1": 3, "H1": 50, "M15": 200}
SO_KHOI = {"D1": 200, "H1": 400, "M15": 400}


def _cot_tri_nho(X):
    return [c for c in X.columns if c.startswith("Delta_")]


def chay(khung="H1", W=500, alpha=1.0):
    t0 = time.time()
    xau, paxg, peg = ds.nap_gia(khung)
    df = clean_and_align_ohlc(xau, paxg, peg)
    X, Y, _ = build_feature_matrix(df, macro_df=ds.nap_vi_mo(),
                                   news_df=ds.nap_tin_tuc(), khung=khung)
    tri_nho = _cot_tri_nho(X)
    idx_tri_nho = [X.columns.get_loc(c) for c in tri_nho]
    H = CHAN_TROI[khung]

    Xv, Yv = X.values.astype(float), Y[TARGETS].values.astype(float)
    n = len(Xv)
    log("Mo phong phien dong cua tren %s: %d quan sat, chan troi %d nen, "
        "dong bang %d dac trung tri nho" % (khung, n, H, len(tri_nho)))

    # chon cac diem bat dau khoi rai deu
    kha_dung = np.arange(W, n - H)
    if len(kha_dung) == 0:
        log("   khong du du lieu"); return None
    buoc_nhay = max(1, len(kha_dung) // SO_KHOI[khung])
    diem = kha_dung[::buoc_nhay]
    log("   %d khoi mo phong, moi khoi %d nen" % (len(diem), H))

    rows = []
    for s in diem:
        Xtr, Ytr = Xv[s - W:s], Yv[s - W:s]
        # gia tri tri nho tai nen quan sat cuoi cung truoc khi "dong cua"
        dong_bang = Xv[s - 1, idx_tri_nho].copy()
        delta_cuoi = Yv[s - 1]                       # moc doi chieu "giu_delta"

        Xte = Xv[s:s + H].copy()
        Xte[:, idx_tri_nho] = dong_bang              # <-- dieu kien dong cua
        yhat, _ = _uoc_luong_ridge(Xtr, Ytr, Xte, alpha)

        # tran tren: du bao mot buoc voi tri nho day du (khong dong bang)
        yhat_1b, _ = _uoc_luong_ridge(Xtr, Ytr, Xv[s:s + H], alpha)

        that = Yv[s:s + H]
        gia_paxg = df.loc[X.index[s:s + H], ["paxg_" + c for c in COLS]].values
        gia_xau = df.loc[X.index[s:s + H], ["xau_" + c for c in COLS]].values

        for h in range(H):
            for j, c in enumerate(COLS):
                rows.append(dict(
                    khoi=int(s), buoc=h + 1, thanh_phan=c,
                    that=that[h, j],
                    mo_hinh=yhat[h, j],
                    giu_delta=delta_cuoi[j],
                    mot_buoc=yhat_1b[h, j],
                    gia_that=gia_xau[h, j],
                    gia_mo_hinh=gia_paxg[h, j] * np.exp(yhat[h, j]),
                    gia_giu_delta=gia_paxg[h, j] * np.exp(delta_cuoi[j]),
                    gia_mot_buoc=gia_paxg[h, j] * np.exp(yhat_1b[h, j])))

    d = pd.DataFrame(rows)
    d["sai_so_mo_hinh"] = d["gia_mo_hinh"] - d["gia_that"]
    d["sai_so_giu_delta"] = d["gia_giu_delta"] - d["gia_that"]
    d["sai_so_mot_buoc"] = d["gia_mot_buoc"] - d["gia_that"]

    # ---- tong hop theo buoc
    def gom(g):
        return pd.Series({
            "n": len(g),
            "mae_mo_hinh_usd": g["sai_so_mo_hinh"].abs().mean(),
            "mae_giu_delta_usd": g["sai_so_giu_delta"].abs().mean(),
            "mae_mot_buoc_usd": g["sai_so_mot_buoc"].abs().mean(),
            "mape_mo_hinh_pct": (g["sai_so_mo_hinh"] / g["gia_that"]).abs().mean() * 100,
            "rmse_mo_hinh_usd": np.sqrt((g["sai_so_mo_hinh"] ** 2).mean()),
            "gia_tri_tb_usd": g["gia_that"].mean()})

    theo_buoc = d.groupby(["thanh_phan", "buoc"]).apply(gom, include_groups=False).reset_index()
    theo_buoc.insert(0, "khung", khung)
    save(theo_buoc, os.path.join(TAB, "delta_cuoi_tuan_theo_buoc_%s.csv" % khung))

    # ---- tong hop theo nhom chan troi
    nhom = pd.cut(d["buoc"], bins=[0, 1, 4, 12, 24, 10 ** 6],
                  labels=["1 nen", "2-4", "5-12", "13-24", ">24"])
    d["nhom_chan_troi"] = nhom
    theo_nhom = (d.groupby(["thanh_phan", "nhom_chan_troi"], observed=True)
                 .apply(gom, include_groups=False).reset_index())
    theo_nhom.insert(0, "khung", khung)
    save(theo_nhom, os.path.join(TAB, "delta_cuoi_tuan_theo_nhom_%s.csv" % khung))

    # ---- R2 tren log-delta theo nhom chan troi
    r2 = []
    for (c, nh), g in d.groupby(["thanh_phan", "nhom_chan_troi"], observed=True):
        ss = ((g["that"] - g["that"].mean()) ** 2).sum()
        r2.append(dict(khung=khung, thanh_phan=c, nhom_chan_troi=str(nh), n=len(g),
                       r2_mo_hinh=1 - ((g["that"] - g["mo_hinh"]) ** 2).sum() / ss,
                       r2_giu_delta=1 - ((g["that"] - g["giu_delta"]) ** 2).sum() / ss))
    r2 = pd.DataFrame(r2)
    save(r2, os.path.join(TAB, "delta_cuoi_tuan_r2_%s.csv" % khung))

    log("   xong sau %.1f phut" % ((time.time() - t0) / 60))
    print()
    print("=== %s: MAE (USD) theo chan troi, thanh phan close ===" % khung)
    print(theo_nhom[theo_nhom.thanh_phan == "close"][
        ["nhom_chan_troi", "n", "mae_mot_buoc_usd", "mae_mo_hinh_usd",
         "mae_giu_delta_usd", "mape_mo_hinh_pct"]].round(3).to_string(index=False))
    return theo_nhom


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or ["D1", "H1", "M15"]
    out = [chay(k) for k in args]
    out = [o for o in out if o is not None]
    if out:
        save(pd.concat(out, ignore_index=True),
             os.path.join(TAB, "delta_cuoi_tuan_tong_hop.csv"))
