# BƯỚC 3 — Đo tương quan nền giữa XAU/USD và PAXG_USD

## 3.1. Mục tiêu
Đo tương quan **nền** trên log return của hai chuỗi, chỉ trong các phiên 24/5 mà cả hai cùng giao dịch, phân tầng theo khung thời gian và theo chế độ biến động.

## 3.2. Phương pháp
- Log return: `r_t = ln(P_t / P_{t-1})`.
- Ghép cặp D1: nến XAU dán nhãn tại 22:00 UTC hôm trước (mốc mở phiên ngoại hối), nên **cộng 2 giờ** để lấy đúng ngày giao dịch trước khi ghép với PAXG (mốc 00:00 UTC).
- Ghép cặp H1 / M15: `merge_asof` gần nhất, dung sai 30 phút / 8 phút.
- Loại toàn bộ mốc thứ Bảy – Chủ nhật để chỉ giữ phiên 24/5.
- Chế độ biến động: tam phân vị của độ lệch chuẩn trượt của `r_XAU` (cửa sổ 20 / 120 / 192 nến).
- Thống kê: Pearson, Spearman, và hồi quy `r_XAU = α + β·r_PAXG + ε` với sai số chuẩn **HAC (Newey–West)**, độ trễ 5 / 24 / 96.

## 3.3. Mã nguồn
`src/step03_baseline_corr.py` → `results/tables/buoc03_tuong_quan_nen.csv`; hệ số nền lưu ở `data/processed/buoc03_he_so_nen.json`.

## 3.4. Kết quả

| Khung | Chế độ biến động | n | Pearson | Spearman | β | SE(HAC) | t(β) | R² |
|---|---|---|---|---|---|---|---|---|
| **D1** | tất cả | 1 103 | **0,9051** | 0,9081 | 0,8970 | 0,0258 | 34,7 | 0,819 |
| D1 | thấp | 365 | 0,8664 | 0,8828 | 0,8237 | 0,0403 | 20,4 | 0,751 |
| D1 | trung bình | 364 | 0,8992 | 0,9092 | 0,9005 | 0,0432 | 20,9 | 0,809 |
| D1 | cao | 365 | 0,9229 | 0,9264 | 0,9249 | 0,0429 | 21,6 | 0,852 |
| **H1** | tất cả | 31 105 | **0,6628** | 0,5852 | 0,5787 | 0,0211 | 27,4 | 0,439 |
| H1 | thấp | 10 356 | 0,5257 | 0,4930 | 0,4225 | 0,0426 | 9,9 | 0,276 |
| H1 | trung bình | 10 355 | 0,6068 | 0,5605 | 0,5142 | 0,0327 | 15,7 | 0,368 |
| H1 | cao | 10 355 | 0,7430 | 0,6739 | 0,6794 | 0,0244 | 27,9 | 0,552 |
| **M15** | tất cả | 124 280 | **0,4628** | 0,3892 | 0,3498 | 0,0142 | 24,7 | 0,214 |
| M15 | thấp | 41 406 | 0,3088 | 0,2765 | 0,2068 | 0,0173 | 12,0 | 0,095 |
| M15 | trung bình | 41 405 | 0,3815 | 0,3463 | 0,2755 | 0,0160 | 17,2 | 0,146 |
| M15 | cao | 41 406 | 0,5594 | 0,5052 | 0,4516 | 0,0237 | 19,1 | 0,313 |

## 3.5. Bốn phát hiện

**1. Tương quan giảm mạnh khi rút ngắn khung thời gian: 0,91 (D1) → 0,66 (H1) → 0,46 (M15).**
Đây là kết quả **ngược hoàn toàn** với lần chạy trên dữ liệu ngắn hạn trước đó (0,82 / 0,86 / 0,97). Nguyên nhân: bộ số cũ chỉ có 4 544 quan sát M15 trong **hai tháng** của năm 2026, giai đoạn PAXG bám vàng rất sát. Bộ số hiện tại có 124 280 quan sát trải **5,3 năm**. Bài học phương pháp luận: một hệ số tương quan 0,97 ước lượng trên hai tháng không nói lên điều gì về quan hệ dài hạn — và nếu giữ nguyên con số đó trong báo cáo thì toàn bộ mô hình neo ở Bước 4 sẽ được hiệu chỉnh sai.

**2. Ở khung phút, PAXG và vàng giao ngay là hai tài sản khác nhau.** R² chỉ 0,214 ở M15: gần 79 % biến động 15 phút của vàng **không** giải thích được bằng PAXG. PAXG giao dịch trên sàn tiền mã hóa với thanh khoản mỏng, chênh lệch mua-bán rộng và dòng lệnh riêng. Chỉ khi tổng hợp lên khung ngày, các nhiễu đó triệt tiêu và quan hệ chênh lệch giá mới hiện rõ (R² = 0,819).

**3. Tương quan tăng đơn điệu theo chế độ biến động trên cả ba khung.** D1: 0,866 → 0,923; H1: 0,526 → 0,743; M15: 0,309 → 0,559. Khi thị trường căng, nghiệp vụ chênh lệch giá hoạt động mạnh và PAXG bám vàng chặt hơn hẳn. Đây là cơ sở kinh tế để **beta phải phân tầng theo chế độ biến động** ở Bước 4 thay vì dùng một hệ số cố định — mức chênh giữa hai đầu chế độ ở M15 là 2,2 lần.

**4. β < 1 và giảm theo khung thời gian** (0,897 → 0,579 → 0,350), trong khi độ lệch chuẩn của PAXG **lớn hơn** của XAU ở khung nhỏ (13,0 bp so với 9,8 bp ở M15). Nghĩa là PAXG dao động mạnh hơn vàng nhưng phần dao động thêm đó phần lớn là nhiễu riêng, không truyền sang vàng. Dùng β = 1 để tái tạo chuỗi cuối tuần sẽ **thổi phồng biến động ước lượng lên gần ba lần** ở khung M15.

## 3.6. Hạn chế
Tương quan nền chỉ đo được từ 2020-08 trở đi vì PAXG không tồn tại trước đó. Các hệ số β dùng ở Bước 4 do đó phản ánh chế độ thị trường 2020–2025 và được áp cho toàn bộ giai đoạn tái tạo — đây là giả định bắt buộc, không kiểm chứng được bằng dữ liệu hiện có.
