# -*- coding: utf-8 -*-
"""So sanh truc tiep hai phuong phap tai tao phien cuoi tuan tren CUNG bo ky nghi.

PHUONG PHAP CU (Buoc 4-5): neo theo LOI SUAT
    r_hat_t = beta(che do) * s * r_PAXG_t * (1 + lambda*I_t) + eps_t
    \\hat{XAU}_mo = XAU_dong_thu_Sau * exp( sum r_hat qua ky nghi )
  -> Neo vao gia dong cua thu Sau cua CHINH vang. Khong dung muc gia tuyet doi
     cua PAXG, nen khong thua huong do lech muc gia giua hai thi truong.

PHUONG PHAP MOI (pipeline delta OHLC): neo theo MUC GIA
    \\hat{XAU}_mo = PAXG_mo * exp( \\hat{Delta}_mo )
  -> Dung truc tiep muc gia PAXG, nen thua huong toan bo sai lech ty le delta.

DONG NHAT THUC QUAN TRONG
    Delta_t - Delta_{t-1} = r_XAU,t - r_PAXG,t
  Vi vay "giu nguyen delta" chinh la truong hop dac biet beta = 1 cua phuong phap
  neo loi suat. Ca hai phuong phap thuc chat cung mot ho, chi khac gia tri beta:
        beta = 0    -> gia dinh gia khong doi
        beta = 0.15 -> gia tri toi uu do duoc tren du lieu ky nghi
        beta = 0.90 -> phuong phap cu (beta trong phien, Buoc 3)
        beta = 1.00 -> giu nguyen delta
"""
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import numpy as np
import pandas as pd
from common import RAW, PROC, TAB, log, save
from delta_ohlc import clean_and_align_ohlc
from delta_ohlc import datasources as ds

NGUONG = {"D1": pd.Timedelta("2D"), "H1": pd.Timedelta("10h"), "M15": pd.Timedelta("3h")}


def ky_nghi(df, khung):
    """Tra ve (vi_tri_sau_nghi, moc_truoc_nghi, moc_sau_nghi)."""
    t = pd.Series(df.index)
    gap = t.diff()
    pos = np.where(gap > NGUONG[khung])[0]
    return pos[pos > 0]


def loi_suat_paxg_247(t_dau, t_cuoi, chuoi247):
    """Tong log return cua PAXG trong khoang dong cua, lay tu chuoi 24/7."""
    m = chuoi247[(chuoi247.index > t_dau) & (chuoi247.index <= t_cuoi)]
    return m


def chay(khung="H1"):
    xau, paxg, peg = ds.nap_gia(khung)
    df = clean_and_align_ohlc(xau, paxg, peg)
    pos = ky_nghi(df, khung)

    # chuoi 24/7 do Buoc 4-5 sinh ra (co r_hat da hieu chinh, I, beta)
    f247 = os.path.join(PROC, "chuoi_247_%s.csv" % khung)
    c247 = None
    if os.path.exists(f247):
        c247 = pd.read_csv(f247)
        c247["time"] = pd.to_datetime(c247["time"], utc=True)
        c247 = c247.set_index("time").sort_index()

    rows = []
    for s in pos:
        t_truoc, t_sau = df.index[s - 1], df.index[s]
        xau_dong = df["xau_close"].iloc[s - 1]
        xau_mo_that = df["xau_open"].iloc[s]
        r_p_nghi = np.log(df["paxg_open"].iloc[s] / df["paxg_close"].iloc[s - 1])

        r = dict(thoi_diem=t_sau, xau_dong=xau_dong, xau_mo_that=xau_mo_that,
                 r_xau_nghi=np.log(xau_mo_that / xau_dong), r_paxg_nghi=r_p_nghi)

        # --- ho neo loi suat voi cac gia tri beta khac nhau
        for ten, b in (("beta0_khong_doi", 0.0), ("beta090_pp_cu_xap_xi", 0.90),
                       ("beta1_giu_delta", 1.0), ("beta015_toi_uu", 0.15)):
            r["uoc_" + ten] = xau_dong * np.exp(b * r_p_nghi)

        # --- phuong phap cu DUNG NGUYEN VAN: tong r_hat tu chuoi 24/7 cua Buoc 4-5
        if c247 is not None:
            m = c247[(c247.index > t_truoc) & (c247.index <= t_sau)]
            if len(m):
                r["uoc_pp_cu_nguyen_van"] = xau_dong * np.exp(float(m["r_hat"].sum()))
                r["so_moc_247"] = len(m)
                r["bien_dong_uoc_247"] = float(np.sqrt((m["r_hat"] ** 2).sum()))
        rows.append(r)

    d = pd.DataFrame(rows).dropna(subset=["uoc_beta0_khong_doi"])
    cach = [c[4:] for c in d.columns if c.startswith("uoc_")]
    out = []
    for c in cach:
        e = d["uoc_" + c] - d["xau_mo_that"]
        e = e.dropna()
        out.append(dict(khung=khung, cach=c, n=len(e),
                        mae_usd=round(float(e.abs().mean()), 3),
                        rmse_usd=round(float(np.sqrt((e ** 2).mean())), 3),
                        thien_lech_usd=round(float(e.mean()), 3)))
    b = pd.DataFrame(out).sort_values("mae_usd").reset_index(drop=True)
    goc = float(b[b["cach"] == "beta0_khong_doi"]["mae_usd"].iloc[0])
    b["so_voi_khong_doi_pct"] = (100 * (b["mae_usd"] / goc - 1)).round(1)

    # --- kiem tra gia tri cho BIEN DONG (khac voi huong)
    tq_bd = np.nan
    if "bien_dong_uoc_247" in d.columns:
        m = d.dropna(subset=["bien_dong_uoc_247"])
        if len(m) > 10:
            tq_bd = float(np.corrcoef(m["bien_dong_uoc_247"], m["r_xau_nghi"].abs())[0, 1])
    log("%s: %d ky nghi | tuong quan (bien dong uoc luong 24/7, |bien dong XAU that|) = %.4f"
        % (khung, len(d), tq_bd))
    save(d, os.path.join(TAB, "so_sanh_ky_nghi_chi_tiet_%s.csv" % khung))
    b["tuong_quan_bien_dong"] = round(tq_bd, 4) if tq_bd == tq_bd else np.nan
    print(b.to_string(index=False))
    print()
    return b


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or ["D1", "H1", "M15"]
    t = pd.concat([chay(k) for k in args], ignore_index=True)
    save(t, os.path.join(TAB, "so_sanh_hai_phuong_phap.csv"))
