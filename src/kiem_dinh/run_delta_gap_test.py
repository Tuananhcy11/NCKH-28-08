# -*- coding: utf-8 -*-
"""Do gia tri thong tin THUC cua PAXG tren dung cac ky nghi cuoi tuan.

Cau hoi: khi thi truong vang dong cua tu chieu thu Sau den sang thu Hai, chuoi
PAXG (giao dich 24/7) co giup uoc luong gia mo cua thu Hai chinh xac hon so voi
viec chi gia dinh "gia khong doi" hay khong?

Ba cach uoc luong gia mo cua sau ky nghi:
  A. khong_doi   : \\hat{XAU}_mo = XAU_dong_cua_truoc_nghi          (khong dung PAXG)
  B. giu_delta   : \\hat{XAU}_mo = PAXG_mo * exp(Delta_dong_cua)     (dung PAXG, ty le co dinh)
  C. mo_hinh     : \\hat{XAU}_mo = PAXG_mo * exp(\\hat{Delta})       (pipeline hoi quy truot)

Neu B/C khong tot hon A thi chuoi tai tao khong mang lai thong tin nao.
"""
import time
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import TAB, log, save
from delta_ohlc import clean_and_align_ohlc, build_feature_matrix
from delta_ohlc.model import _uoc_luong_ridge
from delta_ohlc import datasources as ds

COLS = ["open", "high", "low", "close"]
TARGETS = ["Delta_" + c for c in COLS]
NGUONG_NGHI = {"D1": pd.Timedelta("2D"), "H1": pd.Timedelta("10h"),
               "M15": pd.Timedelta("3h")}


def chay(khung="H1", W=500, alpha=1.0):
    xau, paxg, peg = ds.nap_gia(khung)
    df = clean_and_align_ohlc(xau, paxg, peg)
    X, Y, _ = build_feature_matrix(df, macro_df=ds.nap_vi_mo(),
                                   news_df=ds.nap_tin_tuc(), khung=khung)
    # QUAN TRONG: X ngan hon df (do bo NaN khi dung dac trung). Moi truy cap theo
    # vi tri phai dung tren cung mot khung da can chinh, neu khong se lech hang.
    dfx = df.loc[X.index]
    tri_nho = [c for c in X.columns if c.startswith("Delta_")]
    idx_tri_nho = [X.columns.get_loc(c) for c in tri_nho]
    Xv, Yv = X.values.astype(float), Y[TARGETS].values.astype(float)

    # ---- nhan dien ky nghi: khoang trong thoi gian lon bat thuong
    t = X.index
    khoang = pd.Series(t).diff()
    vi_tri = np.where(khoang > NGUONG_NGHI[khung])[0]      # nen dau tien SAU ky nghi
    vi_tri = vi_tri[(vi_tri > W) & (vi_tri < len(Xv))]
    log("%s: phat hien %d ky nghi (nguong %s)" % (khung, len(vi_tri), NGUONG_NGHI[khung]))
    if not len(vi_tri):
        return None

    j_close = COLS.index("close")
    j_open = COLS.index("open")
    rows = []
    for s in vi_tri:
        Xtr, Ytr = Xv[s - W:s], Yv[s - W:s]
        Xte = Xv[s:s + 1].copy()
        Xte[:, idx_tri_nho] = Xv[s - 1, idx_tri_nho]        # dong bang tri nho
        yhat, _ = _uoc_luong_ridge(Xtr, Ytr, Xte, alpha)

        paxg_mo = dfx["paxg_open"].iloc[s]
        xau_mo_that = dfx["xau_open"].iloc[s]
        xau_dong_truoc = dfx["xau_close"].iloc[s - 1]
        delta_dong_truoc = Yv[s - 1, j_close]

        rows.append(dict(
            thoi_diem=t[s], do_dai_nghi_gio=khoang.iloc[s].total_seconds() / 3600,
            xau_dong_truoc=xau_dong_truoc, xau_mo_that=xau_mo_that,
            khoang_trong_that=xau_mo_that - xau_dong_truoc,
            uoc_khong_doi=xau_dong_truoc,
            uoc_giu_delta=paxg_mo * np.exp(delta_dong_truoc),
            uoc_mo_hinh=paxg_mo * np.exp(yhat[0, j_open]),
            paxg_khoang_trong=paxg_mo * np.exp(delta_dong_truoc) - xau_dong_truoc))

    d = pd.DataFrame(rows)
    for ten in ("khong_doi", "giu_delta", "mo_hinh"):
        d["sai_so_" + ten] = d["uoc_" + ten] - d["xau_mo_that"]

    tt = dict(khung=khung, so_ky_nghi=len(d),
              do_dai_nghi_tb_gio=round(float(d["do_dai_nghi_gio"].mean()), 1),
              khoang_trong_tb_abs_usd=round(float(d["khoang_trong_that"].abs().mean()), 3),
              khoang_trong_do_lech_chuan=round(float(d["khoang_trong_that"].std()), 3),
              khoang_trong_max_abs=round(float(d["khoang_trong_that"].abs().max()), 2))
    for ten in ("khong_doi", "giu_delta", "mo_hinh"):
        e = d["sai_so_" + ten]
        tt["mae_" + ten] = round(float(e.abs().mean()), 3)
        tt["rmse_" + ten] = round(float(np.sqrt((e ** 2).mean())), 3)
    tt["giam_mae_giu_delta_pct"] = round(
        100 * (1 - tt["mae_giu_delta"] / tt["mae_khong_doi"]), 1)
    tt["giam_mae_mo_hinh_pct"] = round(
        100 * (1 - tt["mae_mo_hinh"] / tt["mae_khong_doi"]), 1)

    # ty le giai thich duoc khoang trong: hoi quy khoang_trong_that ~ paxg_khoang_trong
    x, y = d["paxg_khoang_trong"], d["khoang_trong_that"]
    tt["tuong_quan_khoang_trong"] = round(float(x.corr(y)), 4)
    tt["r2_khoang_trong"] = round(float(x.corr(y) ** 2), 4)
    b = float(np.polyfit(x, y, 1)[0])
    tt["he_so_truyen_dan"] = round(b, 4)

    # ---- phep do truc tiep nhat: PAXG co giai thich duoc BIEN DONG CUOI TUAN cua vang khong
    from scipy import stats as _st
    r_x = np.log(dfx["xau_open"].values[vi_tri] / dfx["xau_close"].values[vi_tri - 1])
    r_p = np.log(dfx["paxg_open"].values[vi_tri] / dfx["paxg_close"].values[vi_tri - 1])
    ok = np.isfinite(r_x) & np.isfinite(r_p)
    r_x, r_p = r_x[ok], r_p[ok]
    pe, pp = _st.pearsonr(r_p, r_x)
    tt["bien_dong_nghi_XAU_abs_bp"] = round(float(np.abs(r_x).mean() * 1e4), 2)
    tt["bien_dong_nghi_XAU_sd_bp"] = round(float(r_x.std() * 1e4), 2)
    tt["bien_dong_nghi_PAXG_abs_bp"] = round(float(np.abs(r_p).mean() * 1e4), 2)
    tt["bien_dong_nghi_PAXG_sd_bp"] = round(float(r_p.std() * 1e4), 2)
    tt["tuong_quan_qua_ky_nghi"] = round(float(pe), 4)
    tt["p_tuong_quan_qua_ky_nghi"] = float("%.3g" % pp)
    tt["r2_qua_ky_nghi"] = round(float(pe ** 2), 4)
    tt["beta_qua_ky_nghi"] = round(float(np.polyfit(r_p, r_x, 1)[0]), 4)

    save(d, os.path.join(TAB, "delta_ky_nghi_chi_tiet_%s.csv" % khung))
    log("   khoang trong that trung binh %.2f USD | MAE: khong_doi %.2f, giu_delta %.2f, mo_hinh %.2f"
        % (tt["khoang_trong_tb_abs_usd"], tt["mae_khong_doi"],
           tt["mae_giu_delta"], tt["mae_mo_hinh"]))
    log("   tuong quan khoang trong PAXG vs XAU = %.4f (R2 %.4f), he so truyen dan %.3f"
        % (tt["tuong_quan_khoang_trong"], tt["r2_khoang_trong"], tt["he_so_truyen_dan"]))
    return tt


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or ["D1", "H1", "M15"]
    out = [r for r in (chay(k) for k in args) if r]
    t = pd.DataFrame(out)
    save(t, os.path.join(TAB, "delta_ky_nghi_tong_hop.csv"))
    print()
    print(t.to_string(index=False))
