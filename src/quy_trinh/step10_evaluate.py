# -*- coding: utf-8 -*-
"""BUOC 10 - Danh gia bang BAY chi tieu, kiem dinh y nghia thong ke bang
   Wilcoxon va Diebold-Mariano, giai thich mo hinh bang SHAP.
"""
import os, json, warnings
# Ban Python embeddable khong tu them thu muc script vao sys.path,
# nen phai nap tuong minh: thu muc hien tai + goc src/
import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)),
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from sklearn.metrics import accuracy_score, f1_score, log_loss, confusion_matrix
from common import *

BAY_CHI_TIEU = ["loi_nhuan_rong", "ty_le_thang", "he_so_loi_nhuan", "sharpe",
                "sortino", "sut_giam_toi_da", "ky_vong"]
MO_HINH = ["XGBoost", "LSTM", "RandomForest", "Baseline_MACD_EMA"]
CHUAN = "Baseline_MACD_EMA"

# ------------------------------------------------------- 1. Bay chi tieu
def bay_chi_tieu(g):
    t = (g[g["che_do"] == "lot co dinh"]
         .groupby(["khung", "mo_hinh"])[BAY_CHI_TIEU]
         .median().round(3).reset_index())
    save(t, os.path.join(TAB, "buoc10_bay_chi_tieu.csv"))
    b = (g[g["che_do"].str.startswith("%")]
         .groupby(["khung", "mo_hinh", "che_do"])[BAY_CHI_TIEU].median().round(3).reset_index())
    save(b, os.path.join(TAB, "buoc10_dinh_co_theo_rui_ro.csv"))
    return t

# ------------------------------------------------------------ 2. Wilcoxon
def wilcoxon(g):
    rows = []
    key = ["khung", "che_do", "lot", "cat_lo", "rr"]
    for tf in g["khung"].unique():
        d = g[g["khung"] == tf]
        base = d[d["mo_hinh"] == CHUAN].set_index(key, drop=False)
        for mo in MO_HINH:
            if mo == CHUAN: continue
            m = d[d["mo_hinh"] == mo].set_index(key, drop=False)
            chung = m.index.intersection(base.index)
            for ct in ["loi_nhuan_rong", "sharpe", "he_so_loi_nhuan"]:
                a = m.loc[chung, ct].astype(float).values
                b = base.loc[chung, ct].astype(float).values
                ok = np.isfinite(a) & np.isfinite(b)
                if ok.sum() < 8: continue
                st, p = stats.wilcoxon(a[ok], b[ok])
                rows.append(dict(khung=tf, so_sanh="%s vs %s" % (mo, CHUAN), chi_tieu=ct,
                                 n_cap=int(ok.sum()), trung_vi_mo_hinh=round(float(np.median(a[ok])), 3),
                                 trung_vi_chuan=round(float(np.median(b[ok])), 3),
                                 thong_ke_W=float(st), p_value=float("%.4g" % p),
                                 ket_luan="co y nghia (5%)" if p < 0.05 else "khong co y nghia"))
    r = pd.DataFrame(rows)
    save(r, os.path.join(TAB, "buoc10_kiem_dinh_wilcoxon.csv"))
    return r

# ------------------------------------------------- 3. Diebold - Mariano
def dm_test(l1, l2, h=1):
    d = l1 - l2
    n = len(d)
    if n < 20: return np.nan, np.nan
    dbar = d.mean()
    g0 = np.sum((d - dbar) ** 2) / n
    s = g0
    for k in range(1, h):
        gk = np.sum((d[k:] - dbar) * (d[:-k] - dbar)) / n
        s += 2 * (1 - k / h) * gk
    if s <= 0: return np.nan, np.nan
    dm = dbar / np.sqrt(s / n)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)      # hieu chinh Harvey
    p = 2 * (1 - stats.t.cdf(abs(dm), df=n - 1))
    return float(dm), float(p)

def mat_mat(g):
    """Ham mat mat: sai so binh phuong cua du bao huong so voi nhan thuc."""
    return (g["du_bao"].values - g["nhan_that"].values) ** 2

def diebold(tf, ham_mat_mat="binh_phuong"):
    p = load(os.path.join(PROC, "du_bao_%s.csv" % tf)).dropna(subset=["du_bao"])
    piv = {mo: g.set_index("time") for mo, g in p.groupby("mo_hinh")}
    rows = []
    for mo in MO_HINH:
        if mo == CHUAN or mo not in piv: continue
        a, b = piv[mo], piv[CHUAN]
        idx = a.index.intersection(b.index)
        if ham_mat_mat == "binh_phuong":
            l1 = (a.loc[idx, "du_bao"].values - a.loc[idx, "nhan_that"].values) ** 2
            l2 = (b.loc[idx, "du_bao"].values - b.loc[idx, "nhan_that"].values) ** 2
        else:                       # mat mat 0-1: sai lop thi phat 1
            l1 = (a.loc[idx, "du_bao"].values != a.loc[idx, "nhan_that"].values).astype(float)
            l2 = (b.loc[idx, "du_bao"].values != b.loc[idx, "nhan_that"].values).astype(float)
        h = {"D1": 5, "H1": 24, "M15": 32}[tf]
        dm, pv = dm_test(l1, l2, h)
        rows.append(dict(khung=tf, ham_mat_mat=ham_mat_mat,
                         so_sanh="%s vs %s" % (mo, CHUAN), n=len(idx),
                         mat_mat_mo_hinh=round(float(l1.mean()), 4),
                         mat_mat_chuan=round(float(l2.mean()), 4),
                         thong_ke_DM=round(dm, 3) if dm == dm else np.nan,
                         p_value=float("%.4g" % pv) if pv == pv else np.nan,
                         ket_luan=("mo hinh tot hon" if (pv == pv and pv < 0.05 and dm < 0) else
                                   ("chuan tot hon" if (pv == pv and pv < 0.05 and dm > 0)
                                    else "khong khac biet"))))
    return rows

# ---------------------------------------------------------------- 4. SHAP
def shap_xgb(tf, topk=15):
    import shap
    from xgboost import XGBClassifier
    from sklearn.preprocessing import StandardScaler
    from step08_models import cot_dac_trung, folds
    d = load(os.path.join(PROC, "bo_du_lieu_%s.csv" % tf)).sort_values("time").reset_index(drop=True)
    cols = cot_dac_trung(d)
    d = d.dropna(subset=cols + ["nhan"]).reset_index(drop=True)
    X = d[cols].replace([np.inf, -np.inf], np.nan).ffill().fillna(0.0).values
    y3 = (d["nhan"].values + 1).astype(int)
    tr, te = list(folds(len(d), tf))[-1]
    sc = StandardScaler().fit(X[tr])
    m = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8,
                      colsample_bytree=0.8, objective="multi:softprob", num_class=3,
                      tree_method="hist", random_state=SEED, n_jobs=4, eval_metric="mlogloss")
    m.fit(sc.transform(X[tr]), y3[tr])
    ex = shap.TreeExplainer(m)
    sv = ex.shap_values(sc.transform(X[te]))
    sv = np.array(sv)
    a = np.abs(sv)
    truc = [i for i, k in enumerate(a.shape) if k == len(cols)][0]   # truc dac trung
    imp = a.mean(axis=tuple(i for i in range(a.ndim) if i != truc))
    r = pd.DataFrame({"dac_trung": cols, "shap_tb_tuyet_doi": imp}).sort_values(
        "shap_tb_tuyet_doi", ascending=False).head(topk).reset_index(drop=True)
    r["khung"] = tf
    return r

def shap_nen_dau_tuan(tf, ):
    """SHAP tinh RIENG tren cac nen mo phien dau tuan - noi ba dac trung cuoi tuan
       thuc su mang thong tin. Dung de bac bo/khang dinh gia thuyet 'bi pha loang'."""
    import shap
    from xgboost import XGBClassifier
    from sklearn.preprocessing import StandardScaler
    from step08_models import cot_dac_trung, folds
    d = load(os.path.join(PROC, "bo_du_lieu_%s.csv" % tf)).sort_values("time").reset_index(drop=True)
    cols = cot_dac_trung(d)
    d = d.dropna(subset=cols + ["nhan"]).reset_index(drop=True)
    if "co_bien_dong_cuoi_tuan" not in d:
        return None
    X = d[cols].replace([np.inf, -np.inf], np.nan).ffill().fillna(0.0).values
    y3 = (d["nhan"].values + 1).astype(int)
    tr, te = list(folds(len(d), tf))[-1]
    mask = d["co_bien_dong_cuoi_tuan"].values[te] == 1
    if mask.sum() < 10:
        log("   %s: chi co %d nen dau tuan trong fold cuoi - bo qua" % (tf, int(mask.sum())))
        return None
    sc = StandardScaler().fit(X[tr])
    m = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8,
                      colsample_bytree=0.8, objective="multi:softprob", num_class=3,
                      tree_method="hist", random_state=SEED, n_jobs=4, eval_metric="mlogloss")
    m.fit(sc.transform(X[tr]), y3[tr])
    sv = np.array(shap.TreeExplainer(m).shap_values(sc.transform(X[te][mask])))
    truc = [i for i, k in enumerate(sv.shape) if k == len(cols)][0]
    imp = np.abs(sv).mean(axis=tuple(i for i in range(sv.ndim) if i != truc))
    r = pd.DataFrame({"dac_trung": cols, "shap_nen_dau_tuan": imp, "khung": tf,
                      "so_nen": int(mask.sum()), "tong_dac_trung": len(cols)})
    r["hang"] = r["shap_nen_dau_tuan"].rank(ascending=False).astype(int)
    return r

def run():
    g = load(os.path.join(TAB, "buoc09_luoi_backtest.csv"), parse=())
    log("BUOC 10 - (1) bay chi tieu")
    t = bay_chi_tieu(g); print(t.to_string(index=False))
    log("BUOC 10 - (2) kiem dinh Wilcoxon")
    w = wilcoxon(g); print(w.to_string(index=False))
    log("BUOC 10 - (3) kiem dinh Diebold-Mariano")
    dm = pd.DataFrame(sum([diebold(tf, hm) for tf in TFS
                           for hm in ("binh_phuong", "0-1")], []))
    save(dm, os.path.join(TAB, "buoc10_kiem_dinh_diebold_mariano.csv")); print(dm.to_string(index=False))
    log("BUOC 10 - (4) giai thich bang SHAP")
    sh = pd.concat([shap_xgb(tf) for tf in TFS], ignore_index=True)
    save(sh, os.path.join(TAB, "buoc10_shap_xgboost.csv"))
    log("BUOC 10 - (5) SHAP rieng tren nen mo phien dau tuan")
    nd = [r for r in (shap_nen_dau_tuan(tf) for tf in TFS) if r is not None]
    if nd:
        save(pd.concat(nd, ignore_index=True), os.path.join(TAB, "buoc10_shap_nen_dau_tuan.csv"))
    print(sh.groupby("khung").head(8).to_string(index=False))

if __name__ == "__main__":
    run()
