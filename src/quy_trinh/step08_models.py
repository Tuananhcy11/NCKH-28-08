# -*- coding: utf-8 -*-
"""BUOC 8 - Huan luyen va so sanh BON phuong phap tren cung mat bang:
   XGBoost, LSTM, Random Forest, va baseline quy tac MACD + EMA 10/20/50.
   Khung kiem dinh: walk-forward 7 fold co thanh loc (purging) va cach ly (embargo).
"""
import os, json, warnings
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
from xgboost import XGBClassifier
from common import *
from step07_label import HORIZON

N_FOLD, EMBARGO = 7, 0.01
SEQ = 24                     # do dai chuoi dau vao cho LSTM
LOAI = [-1, 0, 1]            # Giam / Sideway / Tang

BO_COT = {"time","open","high","low","close","volume","nhan","nhan_ema_adx","gia_cham",
          "so_nen_giu","rao_tren","rao_duoi","he_so_ATR","ema10","ema20","ema50","ema200",
          "macd_signal","atr14"}

def cot_dac_trung(d):
    return [c for c in d.columns if c not in BO_COT and pd.api.types.is_numeric_dtype(d[c])]

# --------------------------------------------------- walk-forward co thanh loc
def folds(n, tf, k=N_FOLD):
    H = HORIZON[tf]; emb = int(EMBARGO * n)
    size = n // (k + 1)
    for i in range(k):
        te0 = size * (i + 1); te1 = min(n, te0 + size)
        tr1 = max(0, te0 - H - emb)            # purging + embargo
        if tr1 < 200 or te1 - te0 < 50: continue
        yield np.arange(0, tr1), np.arange(te0, te1)

# --------------------------------------------------------- baseline quy tac
def baseline_macd_ema(d):
    """MACD cat len + EMA10 > EMA20 > EMA50 -> Tang; nguoc lai -> Giam; con lai Sideway."""
    tang = (d["macd"] > d["macd_signal"]) & (d["ema10_20"] > 0) & (d["ema20_50"] > 0)
    giam = (d["macd"] < d["macd_signal"]) & (d["ema10_20"] < 0) & (d["ema20_50"] < 0)
    return np.where(tang, 1, np.where(giam, -1, 0))

# ------------------------------------------------------------------- LSTM
def lstm_fit_predict(Xtr, ytr, Xte, seed=SEED):
    import torch, torch.nn as nn
    torch.manual_seed(seed); np.random.seed(seed)

    def seqs(X, y=None):
        n, p = X.shape
        idx = np.arange(SEQ - 1, n)
        S = np.stack([X[i - SEQ + 1:i + 1] for i in idx])
        return (S, (y[idx] if y is not None else None), idx)

    Str, ytr2, _ = seqs(Xtr, ytr)
    Ste, _, idx_te = seqs(Xte)
    dev = "cpu"

    class Net(nn.Module):
        def __init__(s, p):
            super().__init__()
            s.l = nn.LSTM(p, 48, num_layers=1, batch_first=True, bidirectional=True)
            s.h = nn.Sequential(nn.Dropout(0.2), nn.Linear(96, 32), nn.ReLU(), nn.Linear(32, 3))
        def forward(s, x):
            o, _ = s.l(x); return s.h(o[:, -1, :])

    m = Net(Xtr.shape[1]).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3, weight_decay=1e-5)
    w = torch.tensor((len(ytr2) / (3 * np.bincount(ytr2, minlength=3).clip(1))), dtype=torch.float32)
    lf = nn.CrossEntropyLoss(weight=w)
    Xt = torch.tensor(Str, dtype=torch.float32); yt = torch.tensor(ytr2, dtype=torch.long)
    n = len(Xt); bs = 256
    m.train()
    for ep in range(12):
        perm = torch.randperm(n)
        for i in range(0, n, bs):
            b = perm[i:i + bs]
            opt.zero_grad(); loss = lf(m(Xt[b]), yt[b]); loss.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
    m.eval()
    with torch.no_grad():
        P = torch.softmax(m(torch.tensor(Ste, dtype=torch.float32)), 1).numpy()
    out = np.full((len(Xte), 3), np.nan); out[idx_te] = P
    return out

# ------------------------------------------------------------------- chay
def run(tf):
    d = load(os.path.join(PROC, "bo_du_lieu_%s.csv" % tf)).sort_values("time").reset_index(drop=True)
    cols = cot_dac_trung(d)
    d = d.dropna(subset=cols + ["nhan"]).reset_index(drop=True)
    X = d[cols].replace([np.inf, -np.inf], np.nan).ffill().fillna(0.0).values
    y = d["nhan"].values
    y3 = (y + 1).astype(int)                       # 0 Giam, 1 Sideway, 2 Tang
    log("BUOC 8 - %s: %d mau, %d dac trung, %d fold" % (tf, len(d), len(cols), N_FOLD))

    du_bao = []
    for fi, (tr, te) in enumerate(folds(len(d), tf), 1):
        sc = StandardScaler().fit(X[tr])
        Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        cw = {c: len(tr) / (3 * max(1, (y3[tr] == c).sum())) for c in range(3)}
        sw = np.array([cw[c] for c in y3[tr]])

        P = {}
        xgb = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                            objective="multi:softprob", num_class=3, tree_method="hist",
                            random_state=SEED, n_jobs=4, eval_metric="mlogloss")
        xgb.fit(Xtr, y3[tr], sample_weight=sw)
        P["XGBoost"] = xgb.predict_proba(Xte)

        rf = RandomForestClassifier(n_estimators=500, max_depth=10, min_samples_leaf=20,
                                    class_weight="balanced", random_state=SEED, n_jobs=4)
        rf.fit(Xtr, y3[tr])
        P["RandomForest"] = rf.predict_proba(Xte)

        try:
            P["LSTM"] = lstm_fit_predict(Xtr, y3[tr], Xte)
        except Exception as ex:
            log("   LSTM loi: %s" % ex); P["LSTM"] = np.full((len(te), 3), np.nan)

        bl = baseline_macd_ema(d.iloc[te])
        Pb = np.zeros((len(te), 3)); Pb[np.arange(len(te)), (bl + 1).astype(int)] = 1.0
        P["Baseline_MACD_EMA"] = Pb

        for mo, pr in P.items():
            dg = pd.DataFrame({"time": d["time"].values[te], "fold": fi, "mo_hinh": mo,
                               "p_giam": pr[:, 0], "p_sideway": pr[:, 1], "p_tang": pr[:, 2],
                               "nhan_that": y[te], "close": d["close"].values[te],
                               "atr14": d["atr14"].values[te]})
            hop_le = ~np.isnan(pr).any(axis=1)
            db = np.full(len(pr), np.nan)
            if hop_le.any():
                db[hop_le] = np.argmax(pr[hop_le], axis=1) - 1
            dg["du_bao"] = db
            du_bao.append(dg)
        log("   fold %d: train=%d test=%d" % (fi, len(tr), len(te)))

    D = pd.concat(du_bao, ignore_index=True)
    save(D, os.path.join(PROC, "du_bao_%s.csv" % tf))

    r = []
    for mo, g in D.groupby("mo_hinh"):
        gg = g.dropna(subset=["du_bao"])
        r.append(dict(khung=tf, mo_hinh=mo, n=len(gg),
                      do_chinh_xac=round(accuracy_score(gg["nhan_that"], gg["du_bao"]), 4),
                      f1_macro=round(f1_score(gg["nhan_that"], gg["du_bao"], average="macro"), 4),
                      f1_weighted=round(f1_score(gg["nhan_that"], gg["du_bao"], average="weighted"), 4)))
    return pd.DataFrame(r), cols

if __name__ == "__main__":
    out, cols = [], None
    for tf in TFS:
        r, cols = run(tf); out.append(r)
    t = pd.concat(out, ignore_index=True)
    save(t, os.path.join(TAB, "buoc08_so_sanh_mo_hinh.csv"))
    json.dump(cols, open(os.path.join(PROC, "danh_sach_dac_trung.json"), "w"), indent=1)
    print(t.to_string(index=False))
