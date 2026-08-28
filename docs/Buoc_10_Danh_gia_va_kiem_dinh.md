# BƯỚC 10 — Bảy chỉ tiêu, kiểm định thống kê và giải thích mô hình

## 10.1. Bảy chỉ tiêu (trung vị trên 48 cấu hình lot cố định)

| Khung | Mô hình | Lợi nhuận ròng (USD) | Tỷ lệ thắng | Hệ số LN | Sharpe | Sortino | Sụt giảm tối đa | Kỳ vọng/lệnh |
|---|---|---|---|---|---|---|---|---|
| D1 | **Baseline** | **+7 100,9** | **0,409** | **1,126** | **0,406** | **2,104** | **−43,2 %** | **+21,93** |
| D1 | XGBoost | +5 057,4 | 0,391 | 1,080 | 0,342 | 1,519 | −64,8 % | +10,48 |
| D1 | RandomForest | −8 059,2 | 0,367 | 0,869 | −0,100 | −0,236 | −82,6 % | −23,20 |
| D1 | LSTM | −8 166,2 | 0,344 | 0,756 | −0,531 | −1,232 | −83,8 % | −57,51 |
| H1 | LSTM | −8 092,1 | **0,479** | **0,917** | **−0,345** | **−0,544** | −86,1 % | **−9,10** |
| H1 | RandomForest | **−8 024,3** | 0,417 | 0,831 | −0,516 | −0,833 | −81,9 % | −19,59 |
| H1 | Baseline | −8 059,1 | 0,410 | 0,806 | −0,585 | −1,140 | **−80,9 %** | −19,39 |
| H1 | XGBoost | −8 061,3 | 0,449 | 0,857 | −0,511 | −0,910 | −83,0 % | −14,97 |
| M15 | **Baseline** | **−4 888,6** | **0,474** | **0,923** | **−0,535** | **−0,986** | −79,4 % | **−7,66** |
| M15 | RandomForest | −8 006,0 | 0,406 | 0,851 | −0,854 | −2,768 | **−80,1 %** | −11,13 |
| M15 | XGBoost | −8 044,1 | 0,442 | 0,732 | −1,438 | −1,778 | −80,4 % | −17,11 |
| M15 | LSTM | −8 104,0 | 0,428 | 0,628 | −2,265 | −2,445 | −81,6 % | −25,41 |

**Đọc bảng này phải cẩn thận.** Trung vị toàn lưới bị chi phối bởi các cấu hình lot lớn vốn đã cháy tài khoản (xem Bước 9, mục 9.6a) — đó là lý do gần như mọi ô ở H1 và M15 đều âm ~8 000 USD, tức chạm ngưỡng dừng. Bảng phản ánh đúng **rủi ro của lưới tham số**, không phản ánh hiệu suất khả thi. Muốn xem hiệu suất thật, dùng bảng 0,1 lot ở Bước 9 mục 9.5, nơi baseline thắng cả ba khung.

## 10.2. Kiểm định Wilcoxon (bắt cặp theo cấu hình, n = 84 cặp)

| Khung | So sánh | Trung vị mô hình | Trung vị baseline | p-value | Kết luận |
|---|---|---|---|---|---|
| D1 | XGBoost vs Baseline (LN ròng) | +1 363,0 | +2 787,6 | **0,243** | **không khác biệt** |
| D1 | XGBoost vs Baseline (Sharpe) | +0,311 | +0,360 | **0,240** | **không khác biệt** |
| D1 | RandomForest vs Baseline (LN ròng) | −6 154,9 | +2 787,6 | 8,8e-15 | baseline thắng |
| D1 | LSTM vs Baseline (LN ròng) | −8 028,5 | +2 787,6 | 4,0e-15 | baseline thắng |
| H1 | XGBoost vs Baseline (LN ròng) | −3 696,1 | −5 335,8 | 8,6e-03 | XGBoost thắng |
| H1 | RandomForest vs Baseline (LN ròng) | +103,3 | −5 335,8 | **0,124** | **không khác biệt** |
| H1 | LSTM vs Baseline (LN ròng) | −8 009,4 | −5 335,8 | 5,5e-11 | baseline thắng |
| M15 | XGBoost vs Baseline (LN ròng) | −3 616,5 | +1 899,0 | 5,0e-14 | baseline thắng |
| M15 | RandomForest vs Baseline (LN ròng) | −1 563,1 | +1 899,0 | 4,9e-12 | baseline thắng |
| M15 | LSTM vs Baseline (LN ròng) | −4 995,4 | +1 899,0 | 3,7e-14 | baseline thắng |

Tổng kết 27 phép so sánh: baseline thắng ở phần lớn, **không khác biệt** ở 4 trường hợp, và chỉ thua XGBoost ở khung H1 — nơi cả hai đều lỗ, nên "thắng" ở đây chỉ nghĩa là lỗ ít hơn.

So với lần chạy trước, điểm khác biệt lớn nhất là **đã xuất hiện những cặp không có ý nghĩa thống kê** (p = 0,12 đến 0,24). Lần trước toàn bộ 27 cặp đều có p < 0,05, một dấu hiệu đáng ngờ mà dữ liệu dài hạn nay đã lý giải: mẫu ngắn tạo ra khác biệt giả tạo nhất quán trên toàn lưới.

Lưu ý phương pháp luận giữ nguyên: 84 cặp là 84 **cấu hình lưới** dùng chung một chuỗi dự báo, không phải 84 quan sát độc lập. p-value nhỏ nghĩa là "bền vững trên toàn lưới tham số", không phải "xác suất sai lầm 1e-15".

## 10.3. Kiểm định Diebold–Mariano

Chạy với **hai hàm mất mát**, và hai hàm cho hai kết luận trái ngược — bản thân đó là một phát hiện.

**(a) Mất mát bình phương `(ŷ − y)²` trên nhãn mã hóa thứ tự {−1, 0, +1}:**

| Khung | So sánh | DM | p | Kết luận |
|---|---|---|---|---|
| D1 | XGBoost vs Baseline | +5,52 | 3,8e-08 | baseline tốt hơn |
| H1 | XGBoost vs Baseline | +12,88 | < 1e-16 | baseline tốt hơn |
| M15 | XGBoost vs Baseline | +12,64 | < 1e-16 | baseline tốt hơn |

**(b) Mất mát 0–1 (phân loại sai = 1):**

| Khung | So sánh | Mất mát mô hình | Mất mát baseline | DM | p | Kết luận |
|---|---|---|---|---|---|---|
| D1 | XGBoost vs Baseline | 0,620 | 0,615 | +0,23 | 0,821 | không khác biệt |
| D1 | RandomForest vs Baseline | 0,638 | 0,615 | +1,02 | 0,308 | không khác biệt |
| D1 | LSTM vs Baseline | 0,637 | 0,612 | +1,05 | 0,295 | không khác biệt |
| H1 | XGBoost vs Baseline | 0,605 | 0,709 | **−10,93** | < 1e-16 | **mô hình tốt hơn** |
| H1 | RandomForest vs Baseline | 0,608 | 0,709 | −10,72 | < 1e-16 | mô hình tốt hơn |
| H1 | LSTM vs Baseline | 0,628 | 0,709 | −8,02 | 1,1e-15 | mô hình tốt hơn |
| M15 | XGBoost vs Baseline | 0,572 | 0,698 | −13,61 | < 1e-16 | mô hình tốt hơn |
| M15 | RandomForest vs Baseline | 0,578 | 0,698 | **−14,69** | < 1e-16 | mô hình tốt hơn |
| M15 | LSTM vs Baseline | 0,592 | 0,698 | −11,16 | < 1e-16 | mô hình tốt hơn |

**Vì sao trái ngược.** Mất mát bình phương trên nhãn mã hóa thứ tự phạt một dự báo sai chiều (|+1 − (−1)|² = 4) gấp bốn lần một dự báo trung tính sai (|0 − (±1)|² = 1). Baseline phát tín hiệu Sideway ở phần lớn thời gian nên "an toàn" theo thước đo này — nhưng an toàn bằng cách **không dự báo gì cả**. Mất mát 0–1 loại bỏ ưu thế giả đó và cho kết quả khớp với độ chính xác ở Bước 8.

**Khuyến nghị:** trong báo cáo chính thức dùng **DM với mất mát 0–1** làm kiểm định chuẩn cho bài toán phân loại ba trạng thái; nếu vẫn trình bày bản mất mát bình phương thì phải kèm diễn giải trên.

## 10.4. Nghịch lý trung tâm của nghiên cứu

Ba lớp kiểm định cho ba câu trả lời khác nhau, và mâu thuẫn đó chính là kết quả:

| Lớp đo | Khung H1 / M15 | Kết luận |
|---|---|---|
| Độ chính xác phân loại (Bước 8) | XGBoost 0,395 / 0,428 so với baseline 0,291 / 0,302 | **Học máy thắng đậm** |
| Diebold–Mariano, mất mát 0–1 | DM = −10,9 / −13,6, p < 1e-16 | **Học máy thắng, rất có ý nghĩa** |
| Hiệu suất giao dịch ở 0,1 lot (Bước 9) | Baseline +52,5 % / +60,5 %; XGBoost −7,4 % / −0,8 % | **Baseline thắng** |

Học máy dự báo hướng giá **giỏi hơn hẳn** nhưng **kiếm được ít tiền hơn**. Nguyên nhân là chi phí giao dịch cộng với tần suất vào lệnh: baseline chỉ hành động khi MACD và ba đường EMA đồng thuận, còn mô hình học máy phát tín hiệu ở mọi nến. Ưu thế 10–13 điểm phần trăm về độ chính xác không đủ bù chênh lệch mua-bán 0,30 USD và hoa hồng 7 USD/lot trên số lệnh lớn hơn.

**Hệ quả cho thiết kế nghiên cứu:** một mô hình học máy muốn dùng được trong giao dịch phải được huấn luyện với **hàm mục tiêu tính đến chi phí**, hoặc phải kèm một tầng lọc ngưỡng xác suất để giảm tần suất vào lệnh. Tối ưu độ chính xác phân loại là tối ưu sai đại lượng.

## 10.5. Giải thích mô hình bằng SHAP

TreeExplainer trên XGBoost, fold cuối cùng của mỗi khung (`results/tables/buoc10_shap_xgboost.csv`).

| Hạng | D1 | H1 | M15 |
|---|---|---|---|
| 1 | `vol60` (0,244) | `vol20` (0,101) | `gio` (0,326) |
| 2 | `ema50_200` (0,236) | `vol60` (0,098) | `spread` (0,137) |
| 3 | `kc_ema200` (0,159) | `ema50_200` (0,088) | `atr_pct` (0,133) |
| 4 | `atr_pct` (0,144) | `atr_pct` (0,073) | `vol20` (0,127) |
| 5 | `vol20` (0,131) | `gio` (0,070) | `ema50_200` (0,098) |
| 6 | `adx14` (0,128) | `bb_width` (0,068) | `vol60` (0,078) |
| 7 | `ret20` (0,106) | `kc_ema200` (0,065) | `ema20_50` (0,071) |
| 8 | `bb_width` (0,102) | `adx14` (0,063) | `kc_ema200` (0,064) |

**Ba nhận xét:**

1. **Biến động chiếm ưu thế ở mọi khung.** `vol60`, `vol20`, `atr_pct`, `bb_width` chiếm 4/8 vị trí đầu ở cả ba khung. Mô hình chủ yếu học *khi nào thị trường sẽ chạm rào cản ATR*, tức học chế độ biến động — điều này hợp lý vì bản thân nhãn Triple Barrier được định nghĩa theo ATR.

2. **Cấu trúc xu hướng dài hạn chỉ quan trọng ở khung ngày.** `ema50_200` hạng 2 và `kc_ema200` hạng 3 ở D1, nhưng tụt xuống hạng 5 và 8 ở M15.

3. **Ở M15, `gio` (giờ trong ngày) là đặc trưng mạnh nhất tuyệt đối** với SHAP 0,326 — gấp 2,4 lần đặc trưng đứng thứ hai. Mô hình học cấu trúc phiên Á / Âu / Mỹ chứ không học tín hiệu giá. `spread` vào hạng 2 cũng cùng bản chất: chênh lệch mua-bán rộng ra vào giờ thanh khoản mỏng. Nói cách khác, **ở khung M15 mô hình chủ yếu học đồng hồ, không học thị trường**.

## 10.6. Đóng góp của kiến trúc tái tạo 24/7 — kết quả âm tính

SHAP tính **riêng trên các nến mở phiên đầu tuần**, nơi ba đặc trưng cuối tuần thực sự mang thông tin (`results/tables/buoc10_shap_nen_dau_tuan.csv`):

| Đặc trưng | D1 (71 nến) | H1 (43 nến) | M15 (14 nến) |
|---|---|---|---|
| `bien_dong_cuoi_tuan` | 0,0321 — hạng 31/40 | 0,0218 — hạng 22/40 | 0,0427 — hạng **15/41** |
| `lech_tich_luy` | 0,0372 — hạng 28/40 | 0,0086 — hạng 36/40 | 0,0000 — hạng 40/41 |
| `diem_tam_ly_cuoi_tuan` | 0,0222 — hạng 35/40 | 0,0051 — hạng 37/40 | 0,0005 — hạng 38/41 |

Giả thuyết "SHAP trung bình toàn tập bị pha loãng" đã được kiểm chứng trực tiếp và **bị bác bỏ**: ngay trên đúng những cây nến mang thông tin, ba đặc trưng vẫn xếp hạng 15–40 trên 40.

Điểm sáng duy nhất: `bien_dong_cuoi_tuan` đạt hạng 15/41 ở M15 — nhưng chỉ trên 14 nến, quá ít để kết luận.

**Kết luận trung thực: trong phạm vi dữ liệu hiện có, kiến trúc tái tạo chuỗi 24/7 ở Bước 4–6 không tạo ra giá trị dự báo đo được.**

Điều này **không** làm mất giá trị của Bước 3–5. Vòng lặp hội tụ tương quan vẫn là một đóng góp phương pháp luận đứng vững, và bản thân Bước 3 đã cho một phát hiện có giá trị độc lập: tương quan XAU–PAXG sụp từ 0,91 xuống 0,46 khi đi từ khung ngày xuống khung 15 phút. Kết quả âm tính này chính là câu trả lời định lượng cho câu hỏi nghiên cứu — và nó có giá trị hơn việc gán cho ba đặc trưng một vai trò mà số liệu không ủng hộ.
