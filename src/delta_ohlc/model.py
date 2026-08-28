# -*- coding: utf-8 -*-
"""Module 3 - Hoi quy da muc tieu theo cua so truot (rolling window).

He phuong trinh tai moi buoc:      Y_t = X_t W + M + E_t
    Y_t : 1 x 4   (Delta_open, Delta_high, Delta_low, Delta_close)
    X_t : 1 x k
    W   : k x 4 ,  M : 1 x 4

Tuyet doi khong khop mo hinh tinh tren toan bo du lieu: moi du bao mot buoc
deu chi dung W nen lien truoc no.

HAI CO CHE TINH
---------------
engine="fast" (mac dinh)
    Giai truc tiep bai toan Ridge da muc tieu bang dai so tuyen tinh:
        W = (Xs' Xs + alpha I)^-1 Xs' Yc
    Tuong duong TOAN HOC voi MultiOutputRegressor(Ridge(alpha)) vi Ridge khop
    doc lap tung cot muc tieu tren cung ma tran thiet ke. Nhanh hon vai chuc lan
    do khong tao lai doi tuong sklearn o moi buoc lap.
engine="sklearn"
    Dung dung MultiOutputRegressor(Ridge/Lasso/ElasticNet/LinearRegression) cua
    scikit-learn. Dung de doi chieu, va bat buoc khi chon Lasso/ElasticNet.

Ham `kiem_chung_hai_co_che` xac nhan hai duong cho ket qua trung nhau.
"""
import numpy as np
import pandas as pd

TARGETS = ["Delta_open", "Delta_high", "Delta_low", "Delta_close"]


def _uoc_luong_ridge(Xtr, Ytr, Xte, alpha):
    """Ridge da muc tieu co chuan hoa StandardScaler khop tren tap huan luyen."""
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd = np.where(sd < 1e-12, 1.0, sd)              # cot hang so -> khong chia 0
    Xs = (Xtr - mu) / sd
    Xq = (Xte - mu) / sd

    ym = Ytr.mean(axis=0)                            # he so chan M xu ly bang tam hoa
    Yc = Ytr - ym

    k = Xs.shape[1]
    A = Xs.T @ Xs + alpha * np.eye(k)
    B = Xs.T @ Yc
    try:
        W = np.linalg.solve(A, B)
    except np.linalg.LinAlgError:
        W = np.linalg.pinv(A) @ B
    return Xq @ W + ym, W


def rolling_multi_output_regression(X, Y, window_size=500, alpha=1.0,
                                    engine="fast", model="ridge",
                                    step=1, luu_trong_so=False, log=print):
    """Du bao mot buoc bang hoi quy da muc tieu tren cua so truot.

    Tra ve
    ------
    pred   : DataFrame du bao \\hat{Delta} (index = moc du bao, 4 cot)
    actual : DataFrame gia tri thuc tuong ung
    W_log  : DataFrame quy dao trong so (neu luu_trong_so=True), nguoc lai None
    """
    cot_Y = [c for c in TARGETS if c in Y.columns]
    Xv = X.values.astype(float)
    Yv = Y[cot_Y].values.astype(float)
    n = len(Xv)
    if n <= window_size:
        raise ValueError("So quan sat (%d) phai lon hon cua so truot (%d)" % (n, window_size))

    chi_so = list(range(window_size, n, step))
    du_bao = np.empty((len(chi_so), len(cot_Y)))
    W_log = [] if luu_trong_so else None

    if engine == "sklearn" or model != "ridge":
        from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
        from sklearn.multioutput import MultiOutputRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        co_so = {"ridge": lambda: Ridge(alpha=alpha),
                 "lasso": lambda: Lasso(alpha=alpha, max_iter=5000),
                 "elasticnet": lambda: ElasticNet(alpha=alpha, l1_ratio=0.5, max_iter=5000),
                 "ols": lambda: LinearRegression()}[model]
        for j, i in enumerate(chi_so):
            sc = StandardScaler().fit(Xv[i - window_size:i])
            est = MultiOutputRegressor(co_so())
            est.fit(sc.transform(Xv[i - window_size:i]), Yv[i - window_size:i])
            du_bao[j] = est.predict(sc.transform(Xv[i:i + 1]))[0]
            if luu_trong_so:
                W_log.append(np.column_stack([e.coef_ for e in est.estimators_]))
            if j % 5000 == 0 and j:
                log("   ... %d/%d buoc" % (j, len(chi_so)))
    else:
        for j, i in enumerate(chi_so):
            yhat, W = _uoc_luong_ridge(Xv[i - window_size:i], Yv[i - window_size:i],
                                       Xv[i:i + 1], alpha)
            du_bao[j] = yhat[0]
            if luu_trong_so:
                W_log.append(W)
            if j % 20000 == 0 and j:
                log("   ... %d/%d buoc" % (j, len(chi_so)))

    idx = X.index[chi_so]
    pred = pd.DataFrame(du_bao, index=idx, columns=["hat_" + c for c in cot_Y])
    actual = Y.loc[idx, cot_Y]

    Wdf = None
    if luu_trong_so:
        A = np.array(W_log)                                   # (buoc, k, 4)
        Wdf = pd.DataFrame(A.reshape(len(idx), -1), index=idx,
                           columns=["W[%s->%s]" % (f, t)
                                    for f in X.columns for t in cot_Y])
    return pred, actual, Wdf


def kiem_chung_hai_co_che(X, Y, window_size=500, alpha=1.0, so_buoc=300):
    """So sanh duong 'fast' va duong 'sklearn' tren mot doan ngan."""
    Xs, Ys = X.iloc[:window_size + so_buoc], Y.iloc[:window_size + so_buoc]
    p1, _, _ = rolling_multi_output_regression(Xs, Ys, window_size, alpha, engine="fast")
    p2, _, _ = rolling_multi_output_regression(Xs, Ys, window_size, alpha, engine="sklearn")
    lech = (p1 - p2).abs()
    return dict(so_buoc=len(p1),
                lech_tuyet_doi_max=float(lech.values.max()),
                lech_tuyet_doi_tb=float(lech.values.mean()),
                trung_khop=bool(lech.values.max() < 1e-8))
