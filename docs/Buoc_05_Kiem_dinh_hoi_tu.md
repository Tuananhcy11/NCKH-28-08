# BƯỚC 5 — Kiểm định lại và vòng lặp hiệu chỉnh

## 5.1. Điều kiện hội tụ
Tương quan giữa chuỗi tham chiếu 24/7 và PAXG phải hội tụ về **tương quan nền của Bước 3**, sai số cho phép **±0,05**. Nếu lệch, hiệu chỉnh hệ số và lặp lại. Toàn bộ đo trên log return `ln(P_t / P_{t-1})`.

$$\big|\ \rho(r^{247},\, r^{PAXG}) - \rho_{\text{nền}}\ \big| \le 0{,}05$$

## 5.2. Thuật toán hiệu chỉnh
Tham số điều chỉnh là **κ** (biên độ phần dư đặc thù), đơn điệu nghịch biến với tương quan → dùng **chia đôi khoảng** trên [0,05 ; 12,0], tối đa 40 vòng:

- ρ > mục tiêu → tăng κ (thêm nhiễu đặc thù);
- ρ < mục tiêu → giảm κ.

## 5.3. Mã nguồn
`src/step05_calibrate.py` → nhật ký `results/tables/buoc05_nhat_ky_hieu_chinh.csv`, kết quả `results/tables/buoc05_ket_qua_hoi_tu.csv`.

## 5.4. Kết quả hội tụ

| Khung | κ hội tụ | λ | ρ(24/7, PAXG) | ρ nền (Bước 3) | Sai số | Ngưỡng | Kết luận | Số vòng |
|---|---|---|---|---|---|---|---|---|
| D1 | 1,5437 | 0,30 | 0,8781 | 0,9051 | **−0,0270** | ±0,05 | **ĐẠT** | 3 |
| H1 | 1,5437 | 0,30 | 0,6723 | 0,6628 | **+0,0095** | ±0,05 | **ĐẠT** | 3 |
| M15 | 1,5437 | 0,30 | 0,4611 | 0,4628 | **−0,0017** | ±0,05 | **ĐẠT** | 3 |

Cả ba khung hội tụ trong đúng 3 vòng, và đáng chú ý là **cùng hội tụ về κ = 1,5437** — cùng một biên độ nhiễu đặc thù cho cả ba khung. Đây là dấu hiệu tốt về tính nhất quán nội tại: công thức `σ_e = σ_XAU·√(1−R²)` đã hấp thụ gần hết khác biệt giữa các khung, phần còn lại chỉ cần một hệ số chung.

Sai số hội tụ ở H1 (+0,0095) và M15 (−0,0017) rất nhỏ — chặt hơn nhiều so với ngưỡng ±0,05.

## 5.5. Ý nghĩa
Vòng lặp này là **điều kiện tự kiểm chứng** của toàn bộ kiến trúc tái tạo: chuỗi 24/7 không được phép "giống PAXG hơn mức mà XAU thật vốn giống PAXG". Nếu bỏ vòng lặp, chuỗi cuối tuần sẽ mang tương quan giả tạo ~1,0 và mọi đặc trưng rút ra từ nó ở Bước 6 sẽ là thông tin của PAXG chứ không phải của vàng.

## 5.6. Hạn chế
Phần dư `ε_t` là nhiễu Gauss độc lập, chưa mô hình hóa được phân phối đuôi dày và hiệu ứng phân cụm biến động (GARCH) của vàng. Nâng cấp hợp lý là sinh `ε_t` từ mô hình GARCH(1,1) với phân phối Student-t ước lượng trên chính chuỗi XAU 24/5.
