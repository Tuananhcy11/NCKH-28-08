# -*- coding: utf-8 -*-
"""Module 5 - Danh gia phan du: MAE / RMSE / R2 va kiem dinh tinh dung ADF."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.tsa.stattools import adfuller, kpss

COLS = ["open", "high", "low", "close"]


def evaluate_residuals(actual_Y, pred_Y, alpha=0.05, mo_hinh_ngay_tho=True):
    """Bang danh gia cho tung thanh phan OHLC.

    - MAE, RMSE, R2 tren log-delta.
    - R2 doi chieu voi mo hinh ngay tho (naive): du bao Delta_t bang Delta_{t-1}.
      Neu R2 cao nhung khong vuot duoc naive thi mo hinh chi dang sao chep tri nho.
    - Kiem dinh ADF tren phan du: bac bo gia thuyet H0 (co nghiem don vi) nghia la
      phan du DUNG -> hai chuoi log gia dong tich hop, quan he uoc luong on dinh.
    - Bo sung KPSS (H0 nguoc lai: chuoi dung) de doi chung ket luan.
    """
    rows = []
    for c in COLS:
        ten_y, ten_p = "Delta_" + c, "hat_Delta_" + c
        if ten_y not in actual_Y.columns or ten_p not in pred_Y.columns:
            continue
        y = actual_Y[ten_y].astype(float)
        yhat = pred_Y[ten_p].astype(float)
        idx = y.index.intersection(yhat.index)
        y, yhat = y.loc[idx], yhat.loc[idx]
        res = (y - yhat).dropna()

        r = dict(thanh_phan=c, n=int(len(idx)),
                 mae=float(mean_absolute_error(y, yhat)),
                 rmse=float(np.sqrt(mean_squared_error(y, yhat))),
                 r2=float(r2_score(y, yhat)))

        if mo_hinh_ngay_tho:
            naive = y.shift(1)
            ok = naive.notna()
            r["r2_ngay_tho"] = float(r2_score(y[ok], naive[ok]))
            r["vuot_ngay_tho"] = bool(r["r2"] > r["r2_ngay_tho"])
            r["rmse_ngay_tho"] = float(np.sqrt(mean_squared_error(y[ok], naive[ok])))
            r["ty_le_rmse_tren_ngay_tho"] = float(r["rmse"] / r["rmse_ngay_tho"])

        # ------------------------------------------------------------- ADF
        try:
            st, p, do_tre, nobs, cv, _ = adfuller(res.values, autolag="AIC")
            r.update(adf_thong_ke=float(st), adf_p=float(p), adf_do_tre=int(do_tre),
                     adf_cv5=float(cv["5%"]),
                     adf_ket_luan=("phan du DUNG (bac bo H0)" if p < alpha
                                   else "KHONG bac bo H0 - co the co nghiem don vi"))
        except Exception as ex:
            r["adf_ket_luan"] = "loi ADF: %s" % ex

        # ------------------------------------------------------------ KPSS
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kst, kp, _, kcv = kpss(res.values, regression="c", nlags="auto")
            r.update(kpss_thong_ke=float(kst), kpss_p=float(kp),
                     kpss_ket_luan=("phan du DUNG (khong bac bo H0)" if kp > alpha
                                    else "bac bo H0 - phan du KHONG dung"))
        except Exception as ex:
            r["kpss_ket_luan"] = "loi KPSS: %s" % ex

        # -------------------------------------------- dac trung khac cua phan du
        r.update(res_tb=float(res.mean()), res_do_lech_chuan=float(res.std()),
                 res_do_lech=float(res.skew()), res_do_nhon=float(res.kurtosis()),
                 res_tu_tuong_quan1=float(res.autocorr(1)) if len(res) > 2 else np.nan)
        rows.append(r)
    return pd.DataFrame(rows)


def kiem_dinh_dong_tich_hop(df_aligned):
    """ADF tren chinh chuoi Delta (khong phai phan du) - kiem tra dong tich hop
    giua ln(XAU) va ln(PAXG_USD). Neu Delta dung thi hai chuoi dong tich hop
    voi vector (1, -1), tuc ty le nhan delta co xu huong hoi ve trung binh."""
    rows = []
    for c in COLS:
        s = (np.log(df_aligned["xau_" + c]) - np.log(df_aligned["paxg_" + c])).dropna()
        st, p, do_tre, nobs, cv, _ = adfuller(s.values, autolag="AIC")
        rows.append(dict(thanh_phan=c, n=int(len(s)),
                         delta_tb=float(s.mean()), delta_do_lech_chuan=float(s.std()),
                         nua_doi_song_nen=(float(np.log(0.5) / np.log(abs(s.autocorr(1))))
                                           if 0 < abs(s.autocorr(1)) < 1 else np.nan),
                         adf_thong_ke=float(st), adf_p=float(p), adf_cv5=float(cv["5%"]),
                         ket_luan=("dong tich hop (Delta dung)" if p < 0.05
                                   else "khong du bang chung dong tich hop")))
    return pd.DataFrame(rows)
