# ĐỘ CHÍNH XÁC THỰC TẾ CỦA BỘ DỮ LIỆU TÁI TẠO

**Ngày chạy:** 23/08/2026 · **Mã nguồn:** `src/run_delta_weekend_test.py`, `src/run_delta_gap_test.py`

---

## 0. Câu hỏi và câu trả lời ngắn

**Hỏi:** bộ dữ liệu tạo bằng phương pháp hồi quy delta OHLC chính xác đến mức nào?

**Đáp:** phải phân biệt ba điều kiện đo hoàn toàn khác nhau:

| Điều kiện đo | MAE (close) | Ý nghĩa |
|---|---|---|
| Một bước, có nến XAU liền trước | 1,67–7,26 USD | Con số đẹp nhưng **không phải điều kiện sử dụng thật** |
| Thị trường đóng cửa, trí nhớ đóng băng | 5,7–5,8 USD sau 24+ nến | Điều kiện gần đúng với cuối tuần |
| **Ước lượng giá mở cửa thứ Hai thật** | **2,75–2,79 USD** | **Điều kiện sử dụng thật** |

Và kết luận quan trọng nhất: ở điều kiện thật, PAXG chỉ cải thiện **3,6–4,2 %** so với giả định "giá không đổi". Nếu dùng beta trong phiên như Bước 3–5 đang làm, sai số **tăng 136–172 %**.

---

## 1. Ba mức đo và vì sao chúng khác nhau

### 1.1. Dự báo một bước (đã báo cáo ở tài liệu pipeline)

| Khung | MAE open | MAE high | MAE low | MAE close | R² close | R² ngây thơ |
|---|---|---|---|---|---|---|
| D1 | 1,45 | 7,62 | 6,39 | 7,26 | 0,649 | 0,586 |
| H1 | 0,19 | 2,03 | 1,96 | 2,38 | 0,941 | 0,933 |
| M15 | 0,10 | 1,27 | 1,27 | 1,67 | 0,971 | 0,968 |

Vấn đề: ở điều kiện này, các đặc trưng `Delta_close_tre1..5` lấy từ **nến XAU liền trước đã quan sát được**. Nhưng mục đích của chuỗi tái tạo là lấp phiên cuối tuần — lúc đó suốt 48+ giờ **không có nến XAU nào**.

### 1.2. Mô phỏng điều kiện đóng cửa (`run_delta_weekend_test.py`)

Đóng băng toàn bộ nhóm đặc trưng "trí nhớ Delta" tại giá trị cuối cùng quan sát được, các đặc trưng PAXG / vĩ mô / tin tức vẫn cập nhật (vì luôn có 24/7). Chạy trên 400 khối × 50 nến (H1).

**MAE (USD) thành phần `close`, khung H1:**

| Chân trời | Một bước (trần trên) | Mô hình đóng băng | Giữ delta cố định |
|---|---|---|---|
| 1 nến | 2,33 | 2,57 | 2,50 |
| 2–4 | 2,44 | 3,42 | 3,52 |
| 5–12 | 2,40 | 4,12 | 4,51 |
| 13–24 | 2,49 | 4,78 | 5,22 |
| **>24** | **2,54** | **5,72** | **6,37** |

Sai số **tăng 2,2 lần** khi kéo dài từ 1 nến lên quá 24 nến, trong khi trần trên (có trí nhớ đầy đủ) đứng yên ở 2,5 USD. Toàn bộ phần tăng thêm đến từ việc mất trí nhớ, không phải từ độ khó của chuỗi.

Và mô hình 27 đặc trưng chỉ hơn cách làm tầm thường nhất ("giữ nguyên tỷ lệ delta cuối cùng") **10 %** (5,72 so với 6,37).

R² tương ứng ở khung H1 tụt từ 0,925 (1 nến) xuống **0,675** (>24 nến).

### 1.3. Kiểm định trên đúng kỳ nghỉ cuối tuần thật (`run_delta_gap_test.py`)

172–315 kỳ nghỉ thật, độ dài trung bình 46–75 giờ. Ước lượng giá **mở cửa phiên đầu tuần**:

| Khung | Kỳ nghỉ | Khoảng trống thật \|Δ\| | MAE "không đổi" | MAE "giữ delta" | MAE mô hình |
|---|---|---|---|---|---|
| D1 | 172 | 3,54 USD | **3,54** | 8,09 | 8,45 |
| H1 | 277 | 3,24 USD | **3,24** | 8,40 | 3,91 |
| M15 | 315 | 2,96 USD | **2,96** | 7,68 | 3,22 |

**Không cách nào dùng PAXG đánh bại được giả định "giá không đổi".** Cách dùng PAXG ngây thơ (giữ nguyên tỷ lệ delta) tệ hơn **2,4–2,6 lần**.

---

## 2. Nguyên nhân gốc: tỷ lệ tín hiệu trên nhiễu

Đo trực tiếp trên các kỳ nghỉ:

| Đại lượng | D1 | H1 | M15 |
|---|---|---|---|
| Biến động cuối tuần của **XAU**, \|r\| TB | 12,9 bp | 12,7 bp | 11,8 bp |
| Biến động cuối tuần của **PAXG**, \|r\| TB | 35,1 bp | 37,3 bp | 34,4 bp |
| **Tỷ lệ PAXG / XAU** | **2,7×** | **2,9×** | **2,9×** |
| Tương quan qua kỳ nghỉ | 0,489 | 0,339 | 0,336 |
| R² qua kỳ nghỉ | 0,239 | 0,115 | 0,113 |
| Beta qua kỳ nghỉ | **0,231** | **0,147** | **0,145** |
| *Đối chiếu:* tương quan **trong phiên** (Bước 3) | 0,905 | 0,663 | 0,463 |
| *Đối chiếu:* beta **trong phiên** (Bước 3) | 0,897 | 0,579 | 0,350 |

Ba con số nói lên tất cả:

1. **PAXG dao động gấp gần 3 lần vàng trong kỳ nghỉ.** Phần dao động thêm là nhiễu riêng của thị trường tiền mã hóa cuối tuần (thanh khoản mỏng, dòng lệnh nhỏ lẻ), không phải thông tin về vàng.
2. **Tương quan sụt từ 0,905 xuống 0,489** khi đi từ trong phiên sang qua kỳ nghỉ. Quan hệ chênh lệch giá cần thị trường giao ngay mở cửa mới hoạt động; cuối tuần nó bị ngắt.
3. **Beta thật của cuối tuần là 0,15–0,23, không phải 0,86–0,93.** Đây là sai lệch nghiêm trọng nhất.

---

## 3. Hệ quả trực tiếp cho Bước 3–6 của nghiên cứu chính

Bước 4 ước lượng biến động cuối tuần bằng `r̂ = β(chế độ) · r_PAXG · (1 + λI) + ε` với **β lấy từ Bước 3, tức β trong phiên**. Kiểm chứng trên đúng dữ liệu kỳ nghỉ:

| Cách ước lượng giá mở cửa đầu tuần | MAE (D1) | MAE (H1) | MAE (M15) |
|---|---|---|---|
| Giả định giá không đổi | 2,875 | 2,899 | 2,639 |
| **Dùng β trong phiên = 0,90** (cách Bước 4 đang làm) | **6,791** | **7,790** | **7,166** |
| Dùng β cuối tuần ước lượng cuộn chiếu | **2,754** | **2,793** | **2,544** |

- Dùng β trong phiên làm sai số **tăng 136 % (D1), 169 % (H1), 172 % (M15)**.
- Dùng β cuối tuần đúng chỉ cải thiện **4,2 % / 3,7 % / 3,6 %** so với không làm gì.

β cuối tuần ước lượng cuộn chiếu (chỉ dùng các kỳ nghỉ đã qua, không nhìn trước) hội tụ về **0,176 (D1)** và **0,087 (H1/M15)**.

**Đây chính là lời giải thích định lượng cho kết quả âm tính ở Bước 10:** ba đặc trưng cuối tuần xếp hạng 23–37/40 theo SHAP không phải vì ý tưởng sai, mà vì chúng được dựng bằng một hệ số beta lớn gấp 4–6 lần giá trị đúng. Chuỗi tái tạo cuối tuần chủ yếu chứa nhiễu của PAXG chứ không phải tín hiệu của vàng.

---

## 4. Kết luận về độ chính xác

**Trong điều kiện sử dụng thật** (ước lượng phiên cuối tuần):

- Sai số tuyệt đối trung bình **≈ 2,75 USD** trên mức giá ~2 200 USD, tức **≈ 0,125 %**.
- Nhưng bản thân khoảng trống cuối tuần chỉ **2,9 USD**. Nói cách khác, sai số của phương pháp **xấp xỉ đúng bằng đại lượng cần dự báo**.
- Giá trị gia tăng của toàn bộ kiến trúc PAXG so với việc chỉ giữ nguyên giá đóng cửa thứ Sáu: **3,6–4,2 %**.
- Giới hạn lý thuyết: với R² qua kỳ nghỉ = 0,239 (D1), mức cải thiện RMSE tối đa đạt được là `1 − √(1−0,239) = 12,8 %`. Không mô hình nào vượt được ngưỡng này với dữ liệu PAXG.

**Ba khuyến nghị:**

1. **Bắt buộc thay β trong phiên bằng β cuối tuần** (0,15–0,23) trong Bước 4. Đây là sửa lỗi, không phải tinh chỉnh.
2. **Dùng chuỗi tái tạo cho biến động, không cho hướng.** Tương quan 0,34–0,49 quá thấp để suy ra chiều đi của giá, nhưng cường độ biến động của PAXG cuối tuần vẫn là chỉ báo hợp lệ cho mức độ căng thẳng thị trường.
3. **Khai báo rõ sai số ±2,8 USD** khi trình bày chuỗi 24/7, và không trích các con số R² 0,94–0,97 của dự báo một bước như thể chúng mô tả chất lượng dữ liệu cuối tuần.

---

## 5. Tệp kết quả

| Tệp | Nội dung |
|---|---|
| `results/tables/delta_cuoi_tuan_theo_buoc_{tf}.csv` | MAE theo từng bước chân trời |
| `results/tables/delta_cuoi_tuan_theo_nhom_{tf}.csv` | MAE theo nhóm chân trời |
| `results/tables/delta_cuoi_tuan_r2_{tf}.csv` | R² suy giảm theo chân trời |
| `results/tables/delta_ky_nghi_chi_tiet_{tf}.csv` | Từng kỳ nghỉ: khoảng trống thật và ba ước lượng |
| `results/tables/delta_ky_nghi_tong_hop.csv` | Tổng hợp ba khung, tương quan và beta qua kỳ nghỉ |
| `results/tables/delta_ky_nghi_beta_dung.csv` | So sánh β trong phiên với β cuối tuần cuộn chiếu |
