# -*- coding: utf-8 -*-
"""Module 1 - Lam sach, khu de-peg USDT va dong bo muc thoi gian UTC."""
import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close"]


def _chuan_hoa_khung(df, ten):
    """Dua ve dang chuan: index UTC theo moc MO nen, cot OHLC(+volume) so thuc."""
    d = df.copy()
    if "time" in d.columns:
        d["time"] = pd.to_datetime(d["time"], utc=True)
        d = d.set_index("time")
    else:
        d.index = pd.to_datetime(d.index, utc=True)
    d.index.name = "time"

    thieu = [c for c in COLS if c not in d.columns]
    if thieu:
        raise ValueError("%s thieu cot %s" % (ten, thieu))

    giu = COLS + ([("volume")] if "volume" in d.columns else [])
    d = d[giu].astype(float)

    # Loai ban ghi hong: gia <= 0, co NaN, hoac vi pham quan he hinh hoc OHLC
    truoc = len(d)
    d = d[(d[COLS] > 0).all(axis=1)].dropna(subset=COLS)
    d = d[(d["high"] >= d[["open", "close"]].max(axis=1)) &
          (d["low"] <= d[["open", "close"]].min(axis=1)) &
          (d["high"] >= d["low"])]
    d = d[~d.index.duplicated(keep="last")].sort_index()
    return d, truoc - len(d)


def _dung_lai_tren_luoi(pax, moc_xau, do_dai):
    """Dung lai nen PAXG DUNG tren luoi nen cua XAU.

    Ly do: hai san dung quy uoc phien khac nhau. Nen D1 cua XAU/USD dan nhan tai
    22:00 UTC (moc mo phien ngoai hoi) con nen D1 cua Binance tai 00:00 UTC, nen
    ghep truc tiep theo dau thoi gian se khong co moc nao trung.

    Cach lam: voi moi nen XAU bat dau tai t, gom toan bo nen PAXG nam trong
    [t, t + do_dai) roi tinh lai OHLC. Gioi han cung do_dai la bat buoc - neu
    khong, du lieu PAXG cuoi tuan se bi hut vao nen dau tuan va lam sai muc tieu.
    """
    p = pax.sort_index()
    moc = pd.DataFrame({"bat_dau": moc_xau}).sort_values("bat_dau")
    g = pd.merge_asof(p.reset_index(), moc, left_on="time", right_on="bat_dau",
                      direction="backward")
    g = g[(g["time"] - g["bat_dau"]) < do_dai].dropna(subset=["bat_dau"])
    if g.empty:
        return pd.DataFrame(columns=pax.columns)

    agg = {"open": "first", "high": "max", "low": "min", "close": "last",
           "usdt_usd": "last", "peg_dev": "max"}
    if "volume" in g.columns:
        agg["volume"] = "sum"
    agg = {k: v for k, v in agg.items() if k in g.columns}
    out = g.groupby("bat_dau").agg(agg)
    out.index.name = "time"
    return out


def clean_and_align_ohlc(df_xau, df_paxg_usdt, df_usdt_usd,
                         peg_tolerance="3D", bao_cao=None):
    """Lam sach, khu de-peg USDT va dong bo hai chuoi ve cung luoi thoi gian.

    Tham so
    -------
    df_xau        : OHLC cua XAU/USD (chuoi 24/5)
    df_paxg_usdt  : OHLC cua PAXG/USDT tren Binance (chuoi 24/7)
    df_usdt_usd   : ty gia USDT/USD tu san fiat DOC LAP voi Binance
    peg_tolerance : dung sai ghep ty gia neo theo kieu merge_asof lui
    bao_cao       : dict tuy chon de nhan cac chi so chan doan

    Tra ve
    ------
    DataFrame index UTC (moc MO nen) voi cac cot:
        xau_{open,high,low,close}
        paxg_{open,high,low,close}   - DA quy doi sang USD
        paxg_volume, usdt_usd, peg_dev

    Ghi chu ve khu de-peg
    ---------------------
        P_PAXG_USD,col(t) = P_PAXG_USDT,col(t) * E_USDT/USD(t)
        peg_dev(t)        = |E_USDT/USD(t) - 1.0|
    Ty gia neo duoc ghep LUI (backward) nen chi dung thong tin da cong bo
    tai hoac truoc moc mo nen - khong gay lookahead.
    """
    rep = {} if bao_cao is None else bao_cao

    xau, bo_xau = _chuan_hoa_khung(df_xau, "XAU/USD")
    pax, bo_pax = _chuan_hoa_khung(df_paxg_usdt, "PAXG/USDT")
    rep["ban_ghi_loai_xau"] = bo_xau
    rep["ban_ghi_loai_paxg"] = bo_pax

    # ---- ty gia neo USDT/USD
    peg = df_usdt_usd.copy()
    if "time" in peg.columns:
        peg["time"] = pd.to_datetime(peg["time"], utc=True)
        peg = peg.set_index("time")
    else:
        peg.index = pd.to_datetime(peg.index, utc=True)
    cot_peg = "close" if "close" in peg.columns else peg.columns[0]
    peg = (peg[[cot_peg]].rename(columns={cot_peg: "usdt_usd"})
           .astype(float).sort_index())
    peg = peg[peg["usdt_usd"] > 0]
    peg = peg[~peg.index.duplicated(keep="last")]

    pax = pd.merge_asof(pax.reset_index(), peg.reset_index(), on="time",
                        direction="backward",
                        tolerance=pd.Timedelta(peg_tolerance)).set_index("time")
    rep["phu_song_oracle"] = float(pax["usdt_usd"].notna().mean())
    pax = pax.dropna(subset=["usdt_usd"])

    # ---- khu de-peg: quy doi toan bo OHLC cua PAXG sang USD
    for c in COLS:
        pax[c] = pax[c] * pax["usdt_usd"]
    pax["peg_dev"] = (pax["usdt_usd"] - 1.0).abs()

    # ---- dua PAXG ve dung luoi nen cua XAU truoc khi ghep
    do_dai = pd.Series(xau.index).diff().dropna().mode()
    do_dai = do_dai.iloc[0] if len(do_dai) else pd.Timedelta("1h")
    rep["do_dai_nen"] = str(do_dai)
    trung_luoi = xau.index.intersection(pax.index)
    rep["ty_le_trung_luoi_truc_tiep"] = float(len(trung_luoi) / max(1, len(xau)))
    if rep["ty_le_trung_luoi_truc_tiep"] < 0.5:
        rep["cach_ghep"] = "dung lai nen PAXG tren luoi XAU"
        pax = _dung_lai_tren_luoi(pax, xau.index, do_dai)
    else:
        rep["cach_ghep"] = "ghep truc tiep theo dau thoi gian"

    # ---- ghep noi Inner Join tren cac phien chung 24/5
    x = xau[COLS].add_prefix("xau_")
    p = pax[COLS].add_prefix("paxg_")
    p["paxg_volume"] = pax["volume"] if "volume" in pax.columns else np.nan
    p["usdt_usd"] = pax["usdt_usd"]
    p["peg_dev"] = pax["peg_dev"]

    out = x.join(p, how="inner").sort_index()
    out = out[(out[["paxg_" + c for c in COLS]] > 0).all(axis=1)]
    rep["so_moc_xau"] = len(xau)
    rep["so_moc_paxg"] = len(pax)
    rep["so_moc_chung"] = len(out)
    rep["ty_le_ghep"] = float(len(out) / max(1, len(xau)))
    if len(out):
        rep["tu"] = str(out.index.min())
        rep["den"] = str(out.index.max())
        rep["peg_dev_tb_bp"] = float(out["peg_dev"].mean() * 1e4)
        rep["peg_dev_max_bp"] = float(out["peg_dev"].max() * 1e4)
    return out
