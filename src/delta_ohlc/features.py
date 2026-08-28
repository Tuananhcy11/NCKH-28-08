# -*- coding: utf-8 -*-
"""Module 2 - Trich xuat ma tran muc tieu Y (4 cot log-delta) va ma tran dac trung X.

NGUYEN TAC CHONG LOOKAHEAD
--------------------------
Dac trung tai nen t chi duoc dung thong tin co san TAI HOAC TRUOC moc MO nen t.
Cu the:
  * Moi dai luong tinh tu nen DA DONG (high/low/close cua nen t) deu bi tre 1 nen.
  * Cac dai luong biet ngay tai moc mo nen t duoc dung truc tiep: gia mo PAXG,
    khoang trong gia so voi nen truoc, gio/thu trong tuan.
  * Chuoi vi mo theo ngay bi tre 1 ngay roi moi ghep lui.
Ham kiem tra `kiem_tra_lookahead` xac nhan lai bang tuong quan cheo co do tre.
"""
import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close"]
TARGETS = ["Delta_open", "Delta_high", "Delta_low", "Delta_close"]


# --------------------------------------------------------------- chi bao co ban
def _khoa_thoi_gian(df):
    """Dua cot khoa 'time' ve cung do phan giai de merge_asof khong bao loi dtype."""
    d = df.reset_index()
    ten = d.columns[0]
    d = d.rename(columns={ten: "time"}) if ten != "time" else d
    d["time"] = pd.to_datetime(d["time"], utc=True).astype("datetime64[us, UTC]")
    return d


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _atr(h, l, c, n=14):
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _macd_hist(c, f=12, s=26, sig=9):
    line = c.ewm(span=f, adjust=False).mean() - c.ewm(span=s, adjust=False).mean()
    return line - line.ewm(span=sig, adjust=False).mean()


# ------------------------------------------------------------------- muc tieu Y
def build_targets(df):
    """Delta_{col,t} = ln(XAU_{col,t}) - ln(PAXG_USD_{col,t})."""
    Y = pd.DataFrame(index=df.index)
    for c in COLS:
        Y["Delta_" + c] = np.log(df["xau_" + c]) - np.log(df["paxg_" + c])
    return Y


# ---------------------------------------------------------------- dac trung X
def build_feature_matrix(df_aligned, macro_df=None, news_df=None,
                         vol_rank_window=None, khung="H1"):
    """Tra ve (X, Y, ten_nhom) da can chinh, khong con NaN va khong co lookahead.

    df_aligned : dau ra cua clean_and_align_ohlc
    macro_df   : DataFrame theo NGAY, cot con {dxy, us10y, vix} (tuy chon)
    news_df    : DataFrame theo NGAY, cot con {SENT_DIR, SENT_INTENSITY} (tuy chon)
    khung      : "D1" | "H1" | "M15" - quyet dinh cua so xep hang thanh khoan
    """
    d = df_aligned
    Y = build_targets(d)
    X = pd.DataFrame(index=d.index)
    nhom = {}

    o, h, l, c = (d["paxg_" + k] for k in COLS)
    v = d.get("paxg_volume")

    if vol_rank_window is None:
        vol_rank_window = {"D1": 30, "H1": 30 * 24, "M15": 30 * 96}.get(khung, 720)

    # ---------------------------------------- (a) vi cau truc & thanh khoan PAXG
    spread = ((h - l) / c).shift(1)
    X["px_spread_chuan_hoa"] = spread
    X["px_spread_tb5"] = spread.rolling(5).mean()
    if v is not None and v.notna().any():
        X["px_khoi_luong_rank"] = (v.shift(1)
                                   .rolling(vol_rank_window, min_periods=30)
                                   .rank(pct=True))
    X["peg_dev"] = d["peg_dev"]                       # biet tai moc mo nen t
    X["peg_dev_tb5"] = d["peg_dev"].rolling(5).mean()
    nhom["vi_cau_truc"] = [k for k in X.columns]

    # -------------------------------------------------- (b) bien dong & dong luc
    atr = _atr(h, l, c, 14)
    X["px_atr14_chuan_hoa"] = (atr / c).shift(1)
    X["px_rsi14"] = (_rsi(c, 14) / 100.0).shift(1)
    X["px_macd_hist_atr"] = (_macd_hist(c) / atr.replace(0, np.nan)).shift(1)
    X["px_ty_le_than_nen"] = ((c - o).abs() / (h - l).replace(0, np.nan)).shift(1)
    X["px_logret1"] = np.log(c / c.shift(1)).shift(1)
    X["px_logret5"] = np.log(c / c.shift(5)).shift(1)
    X["px_bien_dong20"] = np.log(c / c.shift(1)).rolling(20).std().shift(1)
    # khoang trong gia: biet ngay tai moc mo nen t
    X["px_gap_mo"] = np.log(o / c.shift(1))
    nhom["bien_dong_dong_luc"] = [k for k in X.columns if k not in nhom["vi_cau_truc"]]

    # -------------------------------------------- (c) tri nho cua chinh muc tieu
    # Delta la chuoi rat dai dang; do tre cua chinh no la dac trung manh nhat.
    for lag in (1, 2, 3, 5):
        X["Delta_close_tre%d" % lag] = Y["Delta_close"].shift(lag)
    X["Delta_close_tb10"] = Y["Delta_close"].rolling(10).mean().shift(1)
    X["Delta_bien_do_tre1"] = (Y["Delta_high"] - Y["Delta_low"]).shift(1)
    da_co = set(sum(nhom.values(), []))
    nhom["tri_nho_delta"] = [k for k in X.columns if k not in da_co]

    # ------------------------------------------------------- (d) lich giao dich
    X["gio_sin"] = np.sin(2 * np.pi * d.index.hour / 24.0)
    X["gio_cos"] = np.cos(2 * np.pi * d.index.hour / 24.0)
    X["thu"] = d.index.dayofweek.astype(float)
    da_co = set(sum(nhom.values(), []))
    nhom["lich"] = [k for k in X.columns if k not in da_co]

    # --------------------------------------------------------- (e) vi mo ngoai sinh
    if macro_df is not None and len(macro_df):
        m = macro_df.copy()
        m.index = pd.to_datetime(m.index, utc=True)
        m = m.sort_index()
        g = pd.DataFrame(index=m.index)
        if "dxy" in m:
            g["mac_dxy_logret"] = np.log(m["dxy"] / m["dxy"].shift(1))
        if "us10y" in m:
            g["mac_us10y_bien_thien"] = m["us10y"].diff()
        if "vix" in m:
            g["mac_vix_z"] = ((m["vix"] - m["vix"].rolling(60, min_periods=20).mean())
                              / m["vix"].rolling(60, min_periods=20).std())
        # tre 1 ngay: phien vi mo t chi dong cua sau khi nen t da mo
        g = g.shift(1).dropna(how="all")
        X = pd.merge_asof(_khoa_thoi_gian(X), _khoa_thoi_gian(g),
                          on="time", direction="backward",
                          tolerance=pd.Timedelta("5D")).set_index("time")
        da_co = set(sum(nhom.values(), []))
        nhom["vi_mo"] = [k for k in X.columns if k not in da_co]

    # ------------------------------------------------------ (f) tam ly tin tuc
    if news_df is not None and len(news_df):
        n = news_df.copy()
        n.index = pd.to_datetime(n.index, utc=True)
        n = n.sort_index().shift(1)                  # tre 1 ngay
        n = n[[k for k in ("SENT_DIR", "SENT_INTENSITY") if k in n.columns]]
        n.columns = ["news_" + k for k in n.columns]
        X = pd.merge_asof(_khoa_thoi_gian(X), _khoa_thoi_gian(n),
                          on="time", direction="backward",
                          tolerance=pd.Timedelta("5D")).set_index("time")
        da_co = set(sum(nhom.values(), []))
        nhom["tin_tuc"] = [k for k in X.columns if k not in da_co]

    # ------------------------------------------------------------- can chinh
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.loc[:, X.notna().mean() > 0.5]
    # bo cot gan nhu hang so (vi du gio trong ngay o khung D1) - khong mang thong tin
    # va chi lam ma tran (X'X + aI) kem on dinh
    bien_thien = X.std(numeric_only=True)
    X = X.loc[:, bien_thien[bien_thien > 1e-12].index]
    hop_le = X.dropna().index.intersection(Y.dropna().index)
    X, Y = X.loc[hop_le], Y.loc[hop_le]
    nhom = {k: [c for c in vs if c in X.columns] for k, vs in nhom.items()}
    return X, Y, nhom


# ---------------------------------------------------------- kiem tra lookahead
def kiem_tra_lookahead(X, Y, muc_tieu="Delta_close", so_do_tre=3):
    """Voi moi dac trung, do |tuong quan| voi muc tieu tai cac do tre khac nhau.

    Quy uoc: do tre L do tuong quan giua X_t va y_{t+L}.
      * L > 0  : dac trung khop voi muc tieu TUONG LAI  -> dau hieu LOOKAHEAD.
      * L = 0  : dac trung khop voi muc tieu cung nen   -> binh thuong.
      * L < 0  : dac trung khop voi muc tieu QUA KHU    -> binh thuong, va la
                 hanh vi DUNG cua cac bien tre (vi du Delta_close_tre1 dat
                 tuong quan 1.0 tai L = -1 vi no chinh la muc tieu cua nen truoc).
    Chi danh dau nghi ngo khi dinh nam o do tre DUONG.
    """
    y = Y[muc_tieu]
    rows = []
    for c in X.columns:
        tq = {L: abs(X[c].corr(y.shift(-L))) for L in range(-so_do_tre, so_do_tre + 1)}
        dinh = max(tq, key=lambda k: (tq[k] if tq[k] == tq[k] else -1))
        rows.append(dict(dac_trung=c, do_tre_dinh=dinh,
                         tq_tai_dinh=round(float(tq[dinh]), 4),
                         tq_tai_0=round(float(tq[0]), 4),
                         tq_tai_duong1=round(float(tq.get(1, float("nan"))), 4),
                         nghi_ngo="CO" if dinh > 0 and tq[dinh] > tq[0] + 0.02 else ""))
    return pd.DataFrame(rows).sort_values("tq_tai_0", ascending=False)
