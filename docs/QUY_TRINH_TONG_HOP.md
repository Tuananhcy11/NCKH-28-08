# QUY TRÌNH TỔNG HỢP — Tái tạo chuỗi tham chiếu 24/7 và so sánh AI với tín hiệu kỹ thuật trên XAU/USD

**Ngày chạy:** 23/08/2026 · **Mã nguồn:** `src/` · **Kết quả:** `results/` · **Dữ liệu:** `data/`

---

## A. Sơ đồ quy trình

```
BƯỚC 1  Thu thập 3 luồng: XAU/USD · PAXG/USDT · GDELT
        (mỗi chuỗi MỘT nguồn duy nhất, không ghép sàn)
            │
BƯỚC 2  Chuẩn hóa PAXG về USD qua oracle USDT/USD độc lập
            │
BƯỚC 3  Đo tương quan nền trên phiên 24/5, phân tầng theo chế độ biến động  ──┐
            │                                                                 │ β, R²
BƯỚC 4  Dựng chuỗi tham chiếu cuối tuần bằng mô hình neo tương quan  ◄────────┘
            │
BƯỚC 5  Vòng lặp hiệu chỉnh tới khi ρ(24/7, PAXG) hội tụ về ρ nền ±0,05
            │
BƯỚC 6  Nén thành 3 đặc trưng gắn vào nến mở phiên thứ Hai  ── chuỗi 24/7 DỪNG tại đây
            │
BƯỚC 7  Gán nhãn Tăng/Giảm/Sideway bằng Triple Barrier theo ATR  (trên chuỗi 24/5)
            │
BƯỚC 8  XGBoost · LSTM · Random Forest · Baseline MACD+EMA
        walk-forward 7 fold có purging + embargo
            │
BƯỚC 9  Backtest lưới 4 lot × 6 cắt lỗ × 2 R:R + chế độ % rủi ro  (1 008 cấu hình)
            │
BƯỚC 10 Bảy chỉ tiêu · Wilcoxon · Diebold–Mariano · SHAP
```

**Hai nguyên tắc kiến trúc:**
1. **Một chuỗi — một nguồn.** Ghép hai sàn vào cùng một chuỗi giá tạo gãy cấu trúc giả tại điểm nối, đủ làm lệch beta và sinh nhãn sai.
2. **Kiến trúc dữ liệu hai lớp.** Chuỗi 24/7 là công cụ trích xuất thông tin, không phải mặt bằng sinh lệnh. Mọi giao dịch và chỉ tiêu hiệu suất tính trên chuỗi 24/5 gốc.

---

## B. Bảng tổng hợp mười bước

| Bước | Nội dung | Đầu ra chính | Trạng thái |
|---|---|---|---|
| 1 | Thu thập ba luồng, mỗi chuỗi một nguồn | 19 tệp thô | ✅ D1/H1 đủ 2015–2025 |
| 2 | Chuẩn hóa PAXG → USD | độ phủ oracle 100 % | ✅ |
| 3 | Tương quan nền | ρ = 0,905 / 0,663 / 0,463 | ✅ |
| 4 | Chuỗi tham chiếu 24/7 | `chuoi_247_{tf}.csv` | ✅ |
| 5 | Vòng lặp hội tụ ±0,05 | **ĐẠT cả 3 khung, 3 vòng** | ✅ |
| 6 | Ba đặc trưng cuối tuần | 279 kỳ nghỉ mỗi khung | ✅ |
| 7 | Triple Barrier + đối chiếu EMA200–ADX | 2 837 / 65 125 / 184 881 mẫu | ✅ κ ≈ 0 (kết quả âm tính) |
| 8 | Bốn mô hình, 7 fold | `du_bao_{tf}.csv` | ✅ |
| 9 | Lưới backtest | 1 008 cấu hình | ✅ |
| 10 | Chỉ tiêu + kiểm định + SHAP | 8 bảng kết quả | ✅ |

---

## C. Bảy kết luận của nghiên cứu

**1. Tương quan XAU–PAXG sụp đổ khi rút ngắn khung thời gian: 0,905 (D1) → 0,663 (H1) → 0,463 (M15).**
R² ở M15 chỉ 0,214 — gần 79 % biến động 15 phút của vàng không giải thích được bằng PAXG. Trên cả ba khung, tương quan tăng đơn điệu theo cường độ biến động (M15: 0,309 khi biến động thấp → 0,559 khi cao). → PAXG là biến đại diện hợp lệ cho vàng **ở khung ngày**, còn ở khung phút hai tài sản gần như độc lập. Beta bắt buộc phải phân tầng: β dao động 0,207–0,925, chênh 4,5 lần.

**2. Vòng lặp hiệu chỉnh hội tụ, và là điều kiện tự kiểm chứng bắt buộc.**
Cả ba khung hội tụ trong đúng 3 vòng, sai số −0,027 / +0,010 / −0,002 (ngưỡng ±0,05), và cùng hội tụ về κ = 1,5437. Nếu bỏ phần dư đặc thù `ε_t`, chuỗi tái tạo sẽ tương quan 1,00 với PAXG — một bản sao tuyến tính, không phải chuỗi vàng.

**3. EMA200–ADX không phải bộ kiểm chứng hợp lệ cho nhãn Triple Barrier.**
Cohen κ trong khoảng −0,026 đến +0,033 trên cả ba khung. Quy tắc gán 60 % số nến vào Sideway (vì ADX < 25 phần lớn thời gian) trong khi TBM gán 28 %. Hai phương pháp đo hai đại lượng khác nhau: cường độ xu hướng *hiện tại* so với kết quả giá *tương lai*. Kết quả âm tính này ổn định qua mọi lần chạy.

**4. Học máy dự báo giỏi hơn nhưng kiếm được ít tiền hơn — nghịch lý trung tâm.**

| Lớp đo | Khung H1 / M15 | Ai thắng |
|---|---|---|
| Độ chính xác phân loại | XGBoost 0,395 / 0,428 so với baseline 0,291 / 0,302 | **Học máy, +10 đến +13 điểm %** |
| Diebold–Mariano, mất mát 0–1 | DM = −10,9 / −13,6, p < 1e-16 | **Học máy, rất có ý nghĩa** |
| Hiệu suất giao dịch ở 0,1 lot | Baseline +52,5 % / +60,5 %; XGBoost −7,4 % / −0,8 % | **Baseline** |

Nguyên nhân: baseline chỉ hành động khi MACD và ba đường EMA đồng thuận nên giao dịch thưa; mô hình học máy phát tín hiệu ở mọi nến và trả chi phí nhiều hơn (H1: 1 225 lệnh so với 1 066). **Baseline thắng không phải vì dự báo giỏi hơn mà vì im lặng đúng lúc.** Hệ quả: mô hình học máy dùng cho giao dịch phải được huấn luyện với hàm mục tiêu tính đến chi phí, hoặc phải kèm tầng lọc ngưỡng xác suất.

**5. Ở khung ngày, không phương pháp nào vượt được ngẫu nhiên một cách đáng kể.**
Bốn phương pháp nằm trong dải 0,362–0,385 (mốc ngẫu nhiên 0,333). Wilcoxon: XGBoost so với baseline p = 0,243; DM mất mát 0–1: p = 0,821. **Không khác biệt có ý nghĩa thống kê.** Đây là lần đầu trong nghiên cứu xuất hiện các cặp không có ý nghĩa — dấu hiệu cho thấy dữ liệu dài hạn đã loại bỏ khác biệt giả tạo của mẫu ngắn.

**6. Mô hình cây thắng mạng nơ-ron trên mọi khung.**
Thứ tự ổn định: XGBoost ≳ RandomForest > LSTM, cả về phân loại lẫn hiệu suất giao dịch. Với dữ liệu tài chính dạng bảng và đặc trưng đã kỹ sư hóa, Bi-LSTM không có lợi thế.

**7. Quản trị rủi ro quyết định nhiều hơn chọn mô hình — nhưng không cứu được chiến lược thua.**
- Từ **0,2 lot trở lên**, trung vị lợi nhuận rơi xuống −80 % trên cả ba khung: phần lớn cấu hình cháy tài khoản. Với vốn 10 000 USD, 0,1 lot là **mức trần**.
- Định cỡ theo % rủi ro kéo sụt giảm từ −80 % xuống −13 đến −16 %, nhưng hệ số lợi nhuận trung vị vẫn 0,93–1,03. Nó **kiểm soát thiệt hại, không tạo lợi thế**.
- Cắt lỗ 5 giá cho hệ số lợi nhuận dưới 1,0 trên mọi khung, mọi mô hình.
- **Trong 1 008 cấu hình, không cấu hình nào đạt hiệu suất đủ tốt để triển khai thực tế** khi tính đủ chi phí giao dịch.

---

## D. Ba hạn chế phải khai báo trong báo cáo

| # | Hạn chế | Ảnh hưởng | Cách khắc phục |
|---|---|---|---|
| 1 | **XAU M15 chỉ từ 2018-03.** Nhà cung cấp giới hạn cứng 200 000 nến mỗi tệp; 200 000 nến M15 ≈ 8 năm. **H1 và D1 đã đủ trọn 2015–2025.** | Kết luận ở khung M15 dựa trên 7,8 năm thay vì 11 năm. H1 và D1 không bị ảnh hưởng. | `src/step01d_xau_intraday.py` với API key Twelve Data hoặc Polygon (cả hai máy chủ đã kiểm tra là truy cập được, chỉ thiếu khóa); hoặc xuất lịch sử M1 XAUUSD từ MetaTrader 5. |
| 2 | **PAXG không thể có trước 09/2019** — token PAX Gold phát hành tháng 9/2019. Binance (2020-08-28) là sàn có lịch sử sớm nhất truy cập được. | Tương quan nền và toàn bộ chuỗi tái tạo cuối tuần chỉ đo được từ 2020-08. Các hệ số β phản ánh chế độ 2020–2025 nhưng được áp cho toàn giai đoạn. | **Không khắc phục được** — đây là giới hạn của bản thân tài sản. Đã bổ sung XAUT/USD (Tether Gold) từ 01/2020 làm chuỗi vàng token thứ hai để kiểm chứng chéo. |
| 3 | **FinBERT chưa được dùng đúng nghĩa.** GDELT DOC API không trả toàn văn ở quy mô 9 năm; vai trò "cường độ tin tức FinBERT–GDELT" do cường độ đưa tin và tone GDELT đã chuẩn hóa đảm nhiệm. | Thành phần điều biến tin tức yếu hơn thiết kế. Dù vậy `diem_tam_ly_cuoi_tuan` xếp hạng 35–38/40 theo SHAP, nên nâng cấp FinBERT nhiều khả năng không đổi kết luận. | Tải danh sách bài (`mode=artlist`) rồi chấm điểm từng tiêu đề bằng FinBERT. |

**Đã khắc phục so với các lần chạy trước:**
- XAU/USD H1 mở rộng từ 730 ngày lên **trọn 2015–2025** (65 126 nến) nhờ chuyển sang nguồn Dukascopy; M15 từ 60 ngày lên **7,8 năm** (184 882 nến).
- Nến D1 gộp theo **phiên ngoại hối 22:00→22:00 UTC**, loại bỏ 565 nến giả dài 2 giờ do phiên mở tối Chủ nhật; số nến/năm về đúng 258.
- Bỏ toàn bộ việc ghép nguồn: USDT/USD nay chỉ dùng Bitfinex. Hệ quả đo được: lệch neo cực đại giảm từ 280 bp xuống **39–58 bp** — phần lớn "đuôi lệch" trước đây là hiện vật của việc nối hai sàn.
- Độ phủ oracle 100 %, không mốc nào phải giả định neo = 1,0.

**Hai lưu ý diễn giải:**
- p-value Wilcoxon đến từ 84 **cấu hình lưới** dùng chung một chuỗi dự báo, không phải 84 quan sát độc lập. Đọc là "bền vững trên toàn lưới tham số".
- Bảng bảy chỉ tiêu ở Bước 10 mục 10.1 là trung vị toàn lưới, bị chi phối bởi các cấu hình lot lớn đã cháy tài khoản. Muốn xem hiệu suất khả thi, đọc bảng 0,1 lot ở Bước 9 mục 9.5.

---

## E. Bản đồ tệp

**Mã nguồn (`src/`)**

| Tệp | Bước |
|---|---|
| `common.py`, `indicators.py` | tiện ích dùng chung |
| `step01e_forexsb.py` | 1 — XAU/USD M15/H1/D1 (**nguồn chính**, Dukascopy) |
| `step01_collect.py` | 1 — PAXG/USDT; GLD kiểm chứng chéo |
| `step01c_bitfinex.py` | 1 — USDT/USD và XAUT/USD |
| `step01b_gdelt.py` | 1 — sáu chuỗi tin GDELT |
| `step01d_xau_intraday.py` | 1 — dự phòng XAU nội phiên (cần API key) |
| `step02_normalize_paxg.py` … `step10_evaluate.py` | 2 → 10 |
| `run_all.py` | chạy Bước 2 → 10 |

**Bảng kết quả (`results/tables/`)**
`buoc02_chuan_hoa_paxg` · `buoc03_tuong_quan_nen` · `buoc05_nhat_ky_hieu_chinh` · `buoc05_ket_qua_hoi_tu` · `buoc06_dac_trung_cuoi_tuan` · `buoc07_hieu_chinh_rao_can` · `buoc07_gan_nhan` · `buoc07_doi_chieu_{tf}` · `buoc08_so_sanh_mo_hinh` · `buoc09_luoi_backtest` · `buoc10_bay_chi_tieu` · `buoc10_dinh_co_theo_rui_ro` · `buoc10_kiem_dinh_wilcoxon` · `buoc10_kiem_dinh_diebold_mariano` · `buoc10_shap_xgboost` · `buoc10_shap_nen_dau_tuan`

---

## F. Cách chạy lại

```bash
python src/step01e_forexsb.py       # XAU/USD M15 + H1 + D1 (nguồn chính)
python src/step01_collect.py paxg   # PAXG/USDT
python src/step01c_bitfinex.py      # USDT/USD, XAUT/USD
python src/step01b_gdelt.py         # GDELT (~45 phút vì bị giới hạn tốc độ)
python src/run_all.py 02            # Bước 2 → 10 (~11 phút)
```

Môi trường: Python 3.11 · numpy · pandas · scipy · scikit-learn · xgboost · statsmodels · shap · torch (CPU) · requests. Hạt giống ngẫu nhiên cố định `SEED = 42` ở `src/common.py`; toàn bộ kết quả tái lập được.
