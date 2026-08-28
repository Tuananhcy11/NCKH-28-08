# -*- coding: utf-8 -*-
"""Bo chi bao ky thuat dung chung (thuan pandas/numpy, khong phu thuoc TA-Lib)."""
import numpy as np, pandas as pd

def ema(s, n):  return s.ewm(span=n, adjust=False).mean()
def sma(s, n):  return s.rolling(n).mean()

def rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))

def true_range(h, l, c):
    pc = c.shift(1)
    return pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)

def atr(h, l, c, n=14):
    return true_range(h, l, c).ewm(alpha=1/n, adjust=False).mean()

def adx(h, l, c, n=14):
    up, dn = h.diff(), -l.diff()
    plus  = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = true_range(h, l, c).ewm(alpha=1/n, adjust=False).mean()
    pdi = 100 * pd.Series(plus,  index=h.index).ewm(alpha=1/n, adjust=False).mean() / tr
    mdi = 100 * pd.Series(minus, index=h.index).ewm(alpha=1/n, adjust=False).mean() / tr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean(), pdi, mdi

def macd(c, f=12, s=26, sig=9):
    line = ema(c, f) - ema(c, s)
    signal = ema(line, sig)
    return line, signal, line - signal

def bollinger(c, n=20, k=2):
    m, sd = sma(c, n), c.rolling(n).std()
    return m + k * sd, m, m - k * sd, (2 * k * sd) / m

def stoch(h, l, c, n=14, d=3):
    ll, hh = l.rolling(n).min(), h.rolling(n).max()
    k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
    return k, k.rolling(d).mean()
