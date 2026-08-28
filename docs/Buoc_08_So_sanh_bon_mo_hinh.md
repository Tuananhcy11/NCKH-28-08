# BƯỚC 8 — Huấn luyện và so sánh bốn phương pháp trên cùng mặt bằng

## 8.1. Bốn phương pháp

| Mô hình | Cấu hình |
|---|---|
| **XGBoost** | 400 cây, depth 5, lr 0,05, subsample 0,8, colsample 0,8, `multi:softprob`, trọng số lớp cân bằng |
| **LSTM (Bi-LSTM)** | chuỗi 24 nến, 48 đơn vị ×2 chiều, dropout 0,2, đầu 32→3, Adam lr 1e-3, 12 epoch, CrossEntropy có trọng số lớp |
| **Random Forest** | 500 cây, depth 10, `min_samples_leaf` 20, `class_weight='balanced'` |
| **Baseline quy tắc** | MACD cắt tín hiệu **và** EMA10 > EMA20 > EMA50 → Tăng; đối xứng → Giảm; còn lại Sideway |

Cùng bộ đặc trưng, cùng chuẩn hóa (`StandardScaler` khớp **chỉ trên tập huấn luyện**), cùng phân chia fold.

## 8.2. Khung kiểm định chống rò rỉ
Walk-forward **7 fold**; mỗi fold huấn luyện trên toàn bộ dữ liệu trước đó, kiểm tra trên đoạn kế tiếp, có:
- **Purging**: cắt `H` nến cuối tập huấn luyện (đúng bằng chân trời nhãn) để nhãn huấn luyện không chồng lấn tập kiểm tra;
- **Embargo**: cách ly thêm 1 % số quan sát.

## 8.3. Mã nguồn
`src/step08_models.py` → `data/processed/du_bao_{tf}.csv`, `results/tables/buoc08_so_sanh_mo_hinh.csv`

## 8.4. Kết quả phân loại (gộp 7 fold ngoài mẫu)

| Khung | Mô hình | n | Độ chính xác | F1 macro | F1 weighted |
|---|---|---|---|---|---|
| D1 | **Baseline MACD+EMA** | 2 429 | **0,3853** | **0,3684** | 0,3781 |
| D1 | XGBoost | 2 429 | 0,3800 | 0,3765 | **0,3796** |
| D1 | LSTM | 2 268 | 0,3629 | 0,3647 | 0,3520 |
| D1 | RandomForest | 2 429 | 0,3623 | 0,3630 | 0,3594 |
| H1 | **XGBoost** | 27 237 | **0,3949** | 0,3781 | **0,3945** |
| H1 | RandomForest | 27 237 | 0,3921 | **0,3862** | 0,3935 |
| H1 | LSTM | 27 076 | 0,3716 | 0,3567 | 0,3741 |
| H1 | Baseline MACD+EMA | 27 237 | 0,2910 | 0,2914 | 0,2975 |
| M15 | **XGBoost** | 32 123 | **0,4276** | **0,4324** | **0,4256** |
| M15 | RandomForest | 32 123 | 0,4223 | 0,4271 | 0,4183 |
| M15 | LSTM | 31 962 | 0,4080 | 0,4083 | 0,4078 |
| M15 | Baseline MACD+EMA | 32 123 | 0,3018 | 0,3019 | 0,3055 |

Mốc ngẫu nhiên của bài toán ba lớp là 0,333.

## 8.5. Ba kết luận

**1. Khung ngày: học máy không thắng được quy tắc.** Bốn phương pháp nằm trong dải 0,362–0,385, tức chỉ nhỉnh hơn ngẫu nhiên 3–5 điểm phần trăm. Baseline dẫn đầu về độ chính xác, XGBoost dẫn đầu về F1 weighted — chênh lệch nhỏ tới mức kiểm định Diebold–Mariano ở Bước 10 kết luận **không có khác biệt** (p = 0,82). Với 2 429 mẫu kiểm tra trải 11 năm, không mô hình nào tìm được cấu trúc dự báo ổn định ở khung D1.

**2. Khung nội phiên: học máy thắng rõ rệt về phân loại.** H1: XGBoost 0,395 so với baseline 0,291 — chênh **+10,4 điểm phần trăm**. M15: 0,428 so với 0,302 — chênh **+12,6 điểm**. Khác với lần chạy trước (giai đoạn ngắn, dễ nghi ngờ), kết luận này nay dựa trên 27 237 và 32 123 quan sát ngoài mẫu trải nhiều năm, và được cả DM lẫn Wilcoxon xác nhận ở Bước 10.

**3. Mô hình cây thắng mạng nơ-ron trên mọi khung.** Thứ tự ổn định: XGBoost ≳ RandomForest > LSTM. Với dữ liệu tài chính dạng bảng và đặc trưng đã kỹ sư hóa sẵn, Bi-LSTM không có lợi thế — nhất quán với tài liệu về học máy trên dữ liệu bảng.

## 8.6. Cảnh báo quan trọng: dự báo tốt hơn không đồng nghĩa giao dịch tốt hơn
Ưu thế phân loại 10–13 điểm phần trăm ở H1/M15 **không chuyển thành lợi nhuận** — Bước 9 và 10 cho thấy baseline vẫn thắng về hiệu suất giao dịch trên chính hai khung này. Lý do: baseline chỉ phát tín hiệu khi MACD và ba đường EMA cùng đồng thuận, tức **giao dịch thưa và chọn lọc**, trong khi mô hình học máy phát tín hiệu ở mọi nến và trả phí chênh lệch mua-bán nhiều hơn hẳn. Đây là một trong những kết quả đáng giá nhất của nghiên cứu và cần được trình bày rõ, không được che đi bằng cách chỉ báo cáo độ chính xác.
