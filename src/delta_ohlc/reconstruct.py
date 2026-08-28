# -*- coding: utf-8 -*-
"""Module 4 - Tai tao chuoi gia XAU va ap rang buoc nhat quan hinh hoc OHLC."""
import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close"]


def reconstruct_and_enforce_ohlc(pred_delta_df, df_paxg_usd, bao_cao=None):
    """Tai tao gia tu log-delta du bao roi kep lai cho dung quan he OHLC.

        \\hat{delta}_{col,t} = exp(\\hat{Delta}_{col,t})
        \\hat{XAU}_{col,t}   = PAXG_USD_{col,t} * \\hat{delta}_{col,t}

    Sau do ap rang buoc bat buoc:
        High = max(High, Open, Close)
        Low  = min(Low,  Open, Close)

    Tham so
    -------
    pred_delta_df : DataFrame cot hat_Delta_{open,high,low,close}
    df_paxg_usd   : DataFrame chua paxg_{open,high,low,close} (DA quy doi USD)
    bao_cao       : dict tuy chon nhan chi so chan doan ve muc do vi pham

    Tra ve DataFrame: hat_xau_{col}, delta_{col}, va co vi_pham_hinh_hoc.
    """
    rep = {} if bao_cao is None else bao_cao
    idx = pred_delta_df.index.intersection(df_paxg_usd.index)
    p = df_paxg_usd.loc[idx]
    d = pred_delta_df.loc[idx]

    out = pd.DataFrame(index=idx)
    for c in COLS:
        delta = np.exp(d["hat_Delta_" + c])
        out["delta_" + c] = delta
        out["hat_xau_" + c] = p["paxg_" + c] * delta

    # ---- do muc do vi pham TRUOC khi kep
    hi = out["hat_xau_high"]
    lo = out["hat_xau_low"]
    op = out["hat_xau_open"]
    cl = out["hat_xau_close"]
    can_tren = pd.concat([op, cl], axis=1).max(axis=1)
    can_duoi = pd.concat([op, cl], axis=1).min(axis=1)

    vi_pham = (hi < can_tren) | (lo > can_duoi) | (hi < lo)
    out["vi_pham_hinh_hoc"] = vi_pham
    rep["so_nen"] = int(len(out))
    rep["so_vi_pham"] = int(vi_pham.sum())
    rep["ty_le_vi_pham"] = float(vi_pham.mean()) if len(out) else np.nan
    if vi_pham.any():
        muc = pd.concat([(can_tren - hi).clip(lower=0),
                         (lo - can_duoi).clip(lower=0)], axis=1).max(axis=1)
        rep["vi_pham_tb_usd"] = float(muc[vi_pham].mean())
        rep["vi_pham_max_usd"] = float(muc.max())

    # ---- ap rang buoc
    out["hat_xau_high"] = pd.concat([hi, op, cl], axis=1).max(axis=1)
    out["hat_xau_low"] = pd.concat([lo, op, cl], axis=1).min(axis=1)

    # bao dam tuyet doi high >= low sau khi kep
    xau_hi = out["hat_xau_high"]
    xau_lo = out["hat_xau_low"]
    out["hat_xau_high"] = np.maximum(xau_hi, xau_lo)
    out["hat_xau_low"] = np.minimum(xau_hi, xau_lo)

    con_loi = ((out["hat_xau_high"] < out[["hat_xau_open", "hat_xau_close"]].max(axis=1) - 1e-9) |
               (out["hat_xau_low"] > out[["hat_xau_open", "hat_xau_close"]].min(axis=1) + 1e-9))
    rep["con_vi_pham_sau_kep"] = int(con_loi.sum())
    return out


def do_sai_so_gia(recon, df_aligned):
    """Sai so tuyet doi va tuong doi cua gia tai tao so voi gia XAU thuc."""
    idx = recon.index.intersection(df_aligned.index)
    r, a = recon.loc[idx], df_aligned.loc[idx]
    rows = []
    for c in COLS:
        e = r["hat_xau_" + c] - a["xau_" + c]
        rows.append(dict(thanh_phan=c,
                         mae_usd=round(float(e.abs().mean()), 4),
                         rmse_usd=round(float(np.sqrt((e ** 2).mean())), 4),
                         mape_pct=round(float((e / a["xau_" + c]).abs().mean() * 100), 5),
                         sai_so_max_usd=round(float(e.abs().max()), 3)))
    return pd.DataFrame(rows)
