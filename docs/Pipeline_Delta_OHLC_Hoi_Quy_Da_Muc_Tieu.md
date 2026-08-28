# PIPELINE HỒI QUY ĐA MỤC TIÊU — HỆ SỐ DELTA OHLC GIỮA XAU/USD VÀ PAXG/USDT

**Ngày chạy:** 23/08/2026 · **Mã nguồn:** `src/delta_ohlc/` + `src/run_delta_pipeline.py`

---

## 1. Cơ sở toán học

Mô hình hóa quan hệ theo từng thành phần nến:

$$XAU_{col,t} = PAXG^{USD}_{col,t} \cdot \delta_{col,t}, \qquad col \in \{open, high, low, close\}$$

Chuyển đổi log-linear đưa về hệ hồi quy tuyến tính đa mục tiêu:

$$\Delta_{col,t} = \ln \delta_{col,t} = \ln XAU_{col,t} - \ln PAXG^{USD}_{col,t}$$

$$Y_t = X_t W + M + E_t, \qquad Y_t \in \mathbb{R}^{1\times 4},\ X_t \in \mathbb{R}^{1\times k},\ W \in \mathbb{R}^{k\times 4}$$

Tái tạo tỷ lệ nhân: $\hat\delta_{col,t} = \exp(\hat\Delta_{col,t})$.

---

## 2. Kiến trúc module

| Module | Hàm chính | Trách nhiệm |
|---|---|---|
| `preprocessing.py` | `clean_and_align_ohlc(df_xau, df_paxg_usdt, df_usdt_usd)` | Làm sạch, khử de-peg, đồng bộ UTC |
| `features.py` | `build_feature_matrix(df_aligned, macro_df, news_df)` | Ma trận Y (4 cột log-delta) và X |
| `model.py` | `rolling_multi_output_regression(X, Y, window_size, alpha)` | Hồi quy trượt đa mục tiêu |
| `reconstruct.py` | `reconstruct_and_enforce_ohlc(pred_delta_df, df_paxg_usd)` | Tái tạo giá + ràng buộc hình học |
| `evaluate.py` | `evaluate_residuals(actual_Y, pred_Y)` | MAE/RMSE/R² + ADF + KPSS |
| `datasources.py` | `nap_gia`, `nap_vi_mo`, `nap_tin_tuc` | Nạp dữ liệu từ kho của dự án |

Chạy: `python src/run_delta_pipeline.py D1 H1 M15 --window 500 --alpha 1.0`

---

## 3. Tiền xử lý và đồng bộ

**Khử de-peg USDT.** `P_PAXG_USD,col(t) = P_PAXG_USDT,col(t) × E_USDT/USD(t)`, tỷ giá lấy từ Bitfinex `tUSTUSD` — sàn fiat độc lập với Binance. Biến kiểm soát `peg_dev = |E − 1|`. Ghép **lùi** (`merge_asof backward`) nên chỉ dùng thông tin đã công bố tại hoặc trước mốc mở nến.

**Đồng bộ mốc thời gian — một vấn đề thực tế phải xử lý.** Nến D1 của XAU/USD dán nhãn tại **22:00 UTC** (mốc mở phiên ngoại hối) còn nến D1 của Binance tại **00:00 UTC**. Ghép trực tiếp theo dấu thời gian cho **0 mốc trùng**. Giải pháp: khi tỷ lệ trùng lưới dưới 50 %, module dựng lại nến PAXG **đúng trên lưới nến của XAU** — với mỗi nến XAU bắt đầu tại `t`, gom toàn bộ nến PAXG trong `[t, t + độ_dài)` rồi tính lại OHLC. Giới hạn cứng `độ_dài` là bắt buộc: nếu không, dữ liệu PAXG cuối tuần sẽ bị hút vào nến đầu tuần và làm sai mục tiêu.

**Kết quả đồng bộ:**

| Khung | Số mốc chung | Giai đoạn | Độ phủ oracle | peg_dev TB | peg_dev max |
|---|---|---|---|---|---|
| D1 | 1 379 | 2020-08-30 → 2025-12-30 | 100 % | 7,55 bp | 39 bp |
| H1 | 31 560 | 2020-08-28 → 2025-12-31 | 100 % | 7,77 bp | 58 bp |
| M15 | 126 166 | 2020-08-28 → 2025-12-31 | 100 % | 7,77 bp | 58 bp |

---

## 4. Ma trận đặc trưng và chống lookahead

**Nguyên tắc:** đặc trưng tại nến `t` chỉ dùng thông tin có tại hoặc trước **mốc mở** nến `t`.
- Mọi đại lượng tính từ nến đã đóng (high/low/close của nến `t`) đều bị **trễ 1 nến**.
- Đại lượng biết ngay tại mốc mở được dùng trực tiếp: giá mở PAXG, khoảng trống giá `ln(open_t / close_{t−1})`, giờ/thứ, `peg_dev`.
- Chuỗi vĩ mô theo ngày bị **trễ 1 ngày** rồi mới ghép lùi.

**27 đặc trưng, sáu nhóm:**

| Nhóm | Đặc trưng |
|---|---|
| Vi cấu trúc & thanh khoản (5) | `px_spread_chuan_hoa` = (H−L)/C, `px_spread_tb5`, `px_khoi_luong_rank` (xếp hạng phần trăm trượt 30 ngày), `peg_dev`, `peg_dev_tb5` |
| Biến động & động lượng (8) | `px_atr14_chuan_hoa` = ATR₁₄/C, `px_rsi14`, `px_macd_hist_atr` = MACD_hist/ATR₁₄, `px_ty_le_than_nen` = \|C−O\|/(H−L), `px_logret1`, `px_logret5`, `px_bien_dong20`, `px_gap_mo` |
| Trí nhớ của mục tiêu (6) | `Delta_close_tre{1,2,3,5}`, `Delta_close_tb10`, `Delta_bien_do_tre1` |
| Lịch giao dịch (3) | `gio_sin`, `gio_cos`, `thu` |
| Vĩ mô ngoại sinh (3) | `mac_dxy_logret`, `mac_us10y_bien_thien`, `mac_vix_z` |
| Tâm lý tin tức (2) | `news_SENT_DIR`, `news_SENT_INTENSITY` (GDELT ba nhóm từ khóa, z-score trượt 180 ngày) |

**Kiểm tra lookahead tự động.** `kiem_tra_lookahead` đo `|corr(X_t, y_{t+L})|` với L ∈ [−3, +3]:
- **L > 0**: đặc trưng khớp với mục tiêu **tương lai** → dấu hiệu lookahead.
- **L = 0**: bình thường. **L < 0**: bình thường, và là hành vi **đúng** của biến trễ.

Kết quả: **0/27 ở H1 và M15**; ở D1 chỉ 1 đặc trưng (`px_macd_hist_atr`) có đỉnh ở L=+3 với |corr| = 0,060 so với 0,034 tại L=0 — mức nhiễu, không đáng kể.

> Lưu ý phương pháp: bản dò lookahead đầu tiên của tôi đảo ngược quy ước dấu và báo động giả 15/25 đặc trưng, vì biến trễ `Delta_close_tre1` đạt tương quan 1,0 tại L=−1 — đó chính xác là hành vi phải có. Một công cụ chẩn đoán sai còn tệ hơn không có.

---

## 5. Hồi quy trượt đa mục tiêu

Với mỗi bước `i` từ `W` đến `N`:
1. `X_train = X[i−W : i]`, `Y_train = Y[i−W : i]`; `X_test = X[i : i+1]`
2. Fit `StandardScaler` **chỉ trên `X_train`**, transform cả hai
3. Khớp Ridge đa mục tiêu, dự báo `Ŷ_i` (4 chiều)

Tuyệt đối không khớp mô hình tĩnh trên toàn bộ dữ liệu.

**Hai cơ chế tính.** `engine="fast"` giải trực tiếp `W = (Xₛ'Xₛ + αI)⁻¹Xₛ'Y_c` cho cả 4 mục tiêu cùng lúc; `engine="sklearn"` dùng đúng `MultiOutputRegressor(Ridge)`. Hai đường **tương đương toán học** vì Ridge khớp độc lập từng cột mục tiêu trên cùng ma trận thiết kế. Đã kiểm chứng bằng `kiem_chung_hai_co_che`:

```
so_buoc = 300, lech_tuyet_doi_max = 1.04e-17, trung_khop = True
```

Đường `fast` nhanh hơn khoảng 40 lần — cần thiết vì M15 có **122 442 bước** dự báo.

---

## 6. Tái tạo giá và ràng buộc hình học

`\hat{XAU}_{col} = PAXG^{USD}_{col} × exp(\hat\Delta_{col})`, sau đó kẹp bắt buộc:

```
High = max(High, Open, Close)
Low  = min(Low,  Open, Close)
```

**Tỷ lệ vi phạm trước khi kẹp rất cao và đó là điều phải báo cáo:**

| Khung | Số nến | Vi phạm trước kẹp | Còn vi phạm sau kẹp |
|---|---|---|---|
| D1 | 836 | 196 (23,4 %) | 0 |
| H1 | 30 720 | 14 044 (45,7 %) | 0 |
| M15 | 122 442 | 65 350 (53,4 %) | 0 |

Nguyên nhân bản chất: bốn thành phần được dự báo **độc lập**, không có ràng buộc nào trong hàm mục tiêu buộc `Ŷ_high ≥ max(Ŷ_open, Ŷ_close)`. Khi sai số dự báo cùng cỡ với biên độ nến — đúng trường hợp khung nhỏ — vi phạm xảy ra ở hơn nửa số nến. Bước kẹp không phải thủ tục hình thức mà là **thành phần bắt buộc** của pipeline.

**Hướng cải tiến:** thay vì dự báo 4 log-delta độc lập, tham số hóa lại thành `(Δ_open, Δ_close, log(range), vị_trí_thân_nến)` với `range > 0` — cấu trúc này thỏa mãn ràng buộc hình học **theo thiết kế**, không cần kẹp hậu kỳ.

---

## 7. Kết quả đánh giá

### 7.1. Bảng tổng hợp (`results/tables/delta_tong_hop.csv`)

| Khung | W | Quan sát | Bước dự báo | R²(open) | R²(high) | R²(low) | R²(close) | Thời gian |
|---|---|---|---|---|---|---|---|---|
| D1 | 500 | 1 336 | 836 | 0,9763 | 0,5735 | 0,5866 | 0,6488 | 0,02 phút |
| H1 | 500 | 31 220 | 30 720 | 0,9985 | 0,9403 | 0,9424 | 0,9408 | 0,64 phút |
| M15 | 500 | 122 942 | 122 442 | 0,9995 | 0,9741 | 0,9752 | 0,9713 | 5,64 phút |

### 7.2. Sai số trên thang giá USD

| Khung | MAE open | MAE high | MAE low | MAE close | MAPE close |
|---|---|---|---|---|---|
| D1 | 1,45 | 7,62 | 6,39 | 7,26 | 0,290 % |
| H1 | 0,19 | 2,03 | 1,96 | 2,38 | 0,112 % |
| M15 | 0,10 | 1,27 | 1,27 | 1,67 | 0,079 % |

### 7.3. Kiểm định ADF trên phần dư

**Toàn bộ 12 chuỗi phần dư (3 khung × 4 thành phần) đều bác bỏ H0 ở mức 1 %** — p-value từ 5,1e-29 xuống dưới ngưỡng máy. Phần dư **dừng**, nghĩa là quan hệ ước lượng ổn định, không trôi theo thời gian.

Kiểm định KPSS chạy song song làm đối chứng (H0 ngược lại: chuỗi dừng). **11/12 chuỗi không bác bỏ H0** (p = 0,10, giá trị trần của bảng tra) — hai kiểm định nhất trí: phần dư dừng. Ngoại lệ duy nhất là `Delta_close` khung D1 với p = 0,048, vừa đủ bác bỏ ở mức 5 %; đây cũng là khung có ít quan sát nhất (836 bước) nên kết luận yếu nhất.

Tự tương quan bậc 1 của phần dư nằm trong khoảng 0,009–0,077 — gần như không còn cấu trúc thời gian nào chưa khai thác.

### 7.4. Đồng tích hợp trên chính chuỗi Delta

`kiem_dinh_dong_tich_hop` chạy ADF trực tiếp trên `Delta_col` (không phải phần dư). Nếu Delta dừng thì `ln(XAU)` và `ln(PAXG_USD)` **đồng tích hợp với vector (1, −1)** — tỷ lệ nhân delta có xu hướng hồi về trung bình.

| Khung | Delta TB | Độ lệch chuẩn | Nửa đời sống | ADF p (close) | Kết luận |
|---|---|---|---|---|---|
| D1 | −0,00103 | 0,00684 | 3,2 nến ≈ 3 ngày | 9,2e-05 | đồng tích hợp |
| H1 | −0,00085 | 0,00683 | 19,7 nến ≈ 20 giờ | 7,2e-11 | đồng tích hợp |
| M15 | −0,00085 | 0,00683 | 42,1 nến ≈ 10,5 giờ | 2,5e-18 | đồng tích hợp |

**Hai phát hiện:**
1. **Delta trung bình ≈ −0,00085 trên cả ba khung** — PAXG giao dịch cao hơn XAU khoảng **8,5 bp** một cách có hệ thống. Đây là phần bù cấu trúc của token (phí lưu ký, phí phát hành/thu hồi), không phải nhiễu.
2. **Nửa đời sống hồi quy về trung bình: 10–20 giờ theo đồng hồ** (20 giờ ở H1, 10,5 giờ ở M15) và ~3 ngày ở D1. Độ lệch giữa hai thị trường bị triệt tiêu trong vòng chưa tới một ngày giao dịch — bằng chứng định lượng cho hoạt động chênh lệch giá.

---

## 8. Cảnh báo diễn giải: R² cao không phải là năng lực dự báo giá

**R²(open) = 0,9995 ở M15 phải được giải thích, không được khoe.** Có một đồng nhất thức gần đúng đứng sau:

```
Delta_open_t  = ln(XAU_open_t) − ln(PAXG_open_t)
XAU_open_t    ≈ XAU_close_{t−1}                    (khoảng trống giá ngoại hối rất nhỏ)
⟹ Delta_open_t ≈ Delta_close_{t−1} − ln(PAXG_open_t / PAXG_close_{t−1})
              =  Delta_close_tre1  − px_gap_mo
```

Cả hai vế phải đều là đặc trưng hợp lệ (biết tại mốc mở nến `t`), nên đây **không phải lookahead** — nhưng nó có nghĩa là mô hình chủ yếu đang tái hiện một đồng nhất thức kế toán, không phải khám phá quan hệ kinh tế mới.

**Đối chiếu với mô hình ngây thơ** (`\hat\Delta_t = \Delta_{t−1}`) được tính sẵn trong `evaluate_residuals`:

| Khung | Thành phần | R² mô hình | R² ngây thơ | Chênh lệch | RMSE / RMSE ngây thơ |
|---|---|---|---|---|---|
| D1 | close | 0,6488 | 0,5856 | +0,063 | — |
| D1 | high | 0,5735 | 0,3149 | **+0,259** | — |
| D1 | low | 0,5866 | 0,3044 | **+0,282** | — |
| H1 | open | 0,9985 | 0,9292 | +0,069 | **0,144** |
| H1 | high | 0,9403 | 0,9106 | +0,030 | 0,817 |
| H1 | low | 0,9424 | 0,9203 | +0,022 | 0,850 |
| H1 | close | 0,9408 | 0,9335 | **+0,007** | **0,944** |
| M15 | close | 0,9713 | 0,9683 | **+0,003** | — |

Mô hình vượt mô hình ngây thơ ở **toàn bộ 12 trường hợp**, nhưng biên độ vượt nói lên nhiều điều hơn con số R² tuyệt đối:

- **Ở thành phần `close` khung H1 và M15, giá trị gia tăng gần như bằng không** (+0,007 và +0,003). Tỷ lệ RMSE so với ngây thơ là 0,944 — 27 đặc trưng chỉ giảm được 5,6 % sai số so với việc chép lại giá trị của nến trước.
- **Giá trị gia tăng thật sự nằm ở `high` và `low` khung D1** (+0,26 và +0,28), tức đúng nơi R² tuyệt đối thấp nhất. Biên độ nến ngày là đại lượng mà mô hình thật sự học được điều gì đó.
- **`open` khung H1 giảm RMSE tới 85,6 %** so với ngây thơ — nhưng đó chính là hệ quả của đồng nhất thức kế toán nêu trên, không phải năng lực dự báo.

Kết luận thẳng: **phần lớn R² đến từ tính dai dẳng của chính chuỗi Delta, không từ sức mạnh của bộ đặc trưng.** Bất kỳ báo cáo nào trích R² = 0,97 mà không kèm cột "R² ngây thơ" đều đang trình bày sai kết quả.

---

## 9. Phân tích độ nhạy (`results/tables/delta_do_nhay_H1.csv`)

15 cấu hình trên khung H1 (bước nhảy 10 để lấy mẫu thưa):

| Cửa sổ W | α=0,1 | α=1 | α=10 | α=100 | OLS (α=0) |
|---|---|---|---|---|---|
| 250 | 0,9518 | 0,9525 | 0,9542 | 0,9474 | 0,9517 |
| 500 | 0,9595 | 0,9596 | 0,9595 | 0,9540 | 0,9595 |
| 1000 | 0,9622 | 0,9622 | 0,9621 | 0,9582 | 0,9622 |

*(R² trung bình bốn thành phần)*

**Ba kết luận:**
1. **Kết quả gần như bất biến với α trong khoảng 0,1–10** — chênh lệch dưới 0,003. Chỉ khi α = 100 mới suy giảm rõ (−0,005). Ma trận đặc trưng không bị đa cộng tuyến nghiêm trọng.
2. **Ridge ≈ OLS** ở mọi cửa sổ (chênh ≤ 0,0002). Với 500 quan sát và 27 đặc trưng, phạt L2 gần như không cần thiết.
3. **Cửa sổ dài hơn tốt hơn một cách đơn điệu** (0,9525 → 0,9596 → 0,9622). Quan hệ delta đủ ổn định để mô hình hưởng lợi từ mẫu lớn hơn — nhất quán với kết quả ADF cho thấy phần dư dừng.

---

## 10. Tệp đầu ra

| Tệp | Nội dung |
|---|---|
| `data/processed/delta_{tf}_du_bao.csv` | `\hat\Delta` bốn thành phần theo từng bước |
| `data/processed/delta_{tf}_tai_tao.csv` | `\hat\delta`, giá XAU tái tạo, cờ vi phạm hình học |
| `results/tables/delta_tong_hop.csv` | Bảng tổng hợp ba khung |
| `results/tables/delta_danh_gia_{tf}.csv` | MAE/RMSE/R², ADF, KPSS, mô men phần dư |
| `results/tables/delta_sai_so_gia_{tf}.csv` | Sai số trên thang giá USD |
| `results/tables/delta_dong_tich_hop_{tf}.csv` | ADF trên Delta, nửa đời sống |
| `results/tables/delta_lookahead_{tf}.csv` | Chẩn đoán lookahead từng đặc trưng |
| `results/tables/delta_do_nhay_H1.csv` | Độ nhạy theo W, α, dạng mô hình |

---

## 11. Hạn chế

1. **Bài toán là nowcasting, không phải forecasting.** Công thức tái tạo `\hat{XAU}_{col,t} = PAXG_{col,t} · exp(\hat\Delta_{col,t})` dùng nến PAXG **đã đóng** của chính thời điểm `t`. Pipeline trả lời câu hỏi "biết nến PAXG, suy ra nến XAU" — hữu ích để lấp phiên cuối tuần. Nó **không** dự báo giá vàng tương lai.
2. **Chỉ phủ từ 2020-08** vì PAXG không tồn tại trước 09/2019 và Binance niêm yết 08/2020.
3. **Ràng buộc hình học được áp hậu kỳ**, không nằm trong hàm mục tiêu — xem hướng cải tiến ở mục 6.
4. **Mô hình tuyến tính** theo đúng đặc tả. Với quan hệ phi tuyến (ví dụ delta giãn ra khi thanh khoản cạn), cần mô hình phi tuyến hoặc hồi quy phân vị.
