# WEEKEND GAP — TỔNG HỢP ĐẦY ĐỦ

**Ngày chạy:** 28/08/2026 · **Dữ liệu:** 172–319 kỳ nghỉ cuối tuần thật, 2020-08 → 2025-12
**Mã nguồn:** `src/kiem_dinh/run_delta_gap_test.py`, `run_delta_weekend_test.py`, `run_so_sanh_hai_phuong_phap.py`

---

## 1. Weekend gap là gì và tại sao nó là trọng tâm

Thị trường vàng giao ngay đóng cửa từ khoảng 21:00 UTC thứ Sáu đến 22:00 UTC Chủ nhật. Trong 46–75 giờ đó không tồn tại một mức giá XAU/USD nào. Nhưng PAXG — token vàng trên sàn tiền mã hóa — vẫn giao dịch liên tục 24/7.

**Câu hỏi nghiên cứu:** PAXG có mang thông tin về biến động của vàng trong khoảng thị trường đóng cửa hay không, và nếu có thì khai thác được bao nhiêu?

Toàn bộ giá trị của kiến trúc tái tạo 24/7 (Bước 4–6) nằm ở câu trả lời này. Nếu PAXG không mang thông tin, ba đặc trưng cuối tuần chỉ là nhiễu.

### 1.1. Cách nhận diện kỳ nghỉ

Kỳ nghỉ được nhận diện bằng khoảng trống thời gian bất thường trên chuỗi 24/5 đã căn chỉnh, với ngưỡng riêng cho từng khung:

| Khung | Ngưỡng khoảng trống | Số kỳ nghỉ phát hiện | Độ dài trung bình |
|---|---|---|---|
| D1 | > 2 ngày | 172 | 74,8 giờ |
| H1 | > 10 giờ | 277 | 52,0 giờ |
| M15 | > 3 giờ | 315 | 46,0 giờ |

Số kỳ nghỉ khác nhau giữa các khung vì mỗi khung có số quan sát hợp lệ khác nhau sau khi bỏ NaN của đặc trưng, và vì cửa sổ khởi động W = 500 nến cắt bỏ phần đầu chuỗi.

---

## 2. Đo lường cơ bản: gap thật lớn bao nhiêu

| Đại lượng | D1 | H1 | M15 |
|---|---|---|---|
| Khoảng trống thật, trung bình \|Δ\| | 3,54 USD | 3,24 USD | 2,96 USD |
| Độ lệch chuẩn khoảng trống | 7,62 USD | 8,59 USD | 8,05 USD |
| Khoảng trống cực đại | 51,54 USD | 86,40 USD | 86,40 USD |
| Biến động cuối tuần XAU, \|r\| TB | 12,94 bp | 12,72 bp | 11,76 bp |
| Biến động cuối tuần XAU, độ lệch chuẩn | 24,61 bp | 28,83 bp | 27,12 bp |
| **Biến động cuối tuần PAXG, \|r\| TB** | **35,11 bp** | **37,34 bp** | **34,37 bp** |
| Biến động cuối tuần PAXG, độ lệch chuẩn | 52,00 bp | 66,60 bp | 62,83 bp |
| **Tỷ lệ PAXG / XAU** | **2,71×** | **2,94×** | **2,92×** |

**Phát hiện thứ nhất:** PAXG dao động gấp gần ba lần vàng trong cùng khoảng thời gian. Phần dao động thêm không phải là thông tin về vàng mà là nhiễu riêng của thị trường tiền mã hóa cuối tuần: thanh khoản mỏng, chênh lệch mua-bán rộng, dòng lệnh nhỏ lẻ chi phối.

Đây là điểm khởi đầu của mọi vấn đề về sau. Nếu dùng PAXG để ước lượng biến động vàng mà không thu nhỏ biên độ, ta bơm vào gấp ba lượng biến động cần có.

---

## 3. Tương quan qua kỳ nghỉ so với trong phiên

| Đại lượng | D1 | H1 | M15 |
|---|---|---|---|
| Tương quan **qua kỳ nghỉ** | 0,4888 | 0,3385 | 0,3362 |
| p-value | 1,0e-11 | 7,5e-09 | 9,2e-10 |
| R² qua kỳ nghỉ | 0,2389 | 0,1146 | 0,1130 |
| Beta **qua kỳ nghỉ** | **0,2313** | **0,1465** | **0,1451** |
| *Đối chiếu:* tương quan **trong phiên** (Bước 3) | 0,905 | 0,663 | 0,463 |
| *Đối chiếu:* beta **trong phiên** (Bước 3) | 0,897 | 0,579 | 0,350 |

**Phát hiện thứ hai — quan trọng nhất của toàn bộ nghiên cứu:**

Quan hệ giữa PAXG và vàng **sụp đổ khi thị trường giao ngay đóng cửa**. Tương quan giảm từ 0,905 xuống 0,489 ở khung ngày. Beta giảm từ 0,897 xuống 0,231 — **chênh 3,9 lần**; ở H1 chênh **4,0 lần**; ở M15 chênh **2,4 lần**.

Lý giải kinh tế: cơ chế giữ PAXG bám theo vàng là nghiệp vụ chênh lệch giá của nhà tạo lập — họ mua PAXG bán vàng giao ngay hoặc ngược lại. Khi thị trường giao ngay đóng cửa, một chân của giao dịch chênh lệch không thực hiện được, nên cơ chế neo bị ngắt. PAXG cuối tuần trôi theo dòng lệnh riêng của nó.

Tương quan vẫn có ý nghĩa thống kê (p < 1e-8), tức PAXG **có** mang một ít thông tin. Nhưng R² chỉ 0,11–0,24 nghĩa là **76–89 % biến động cuối tuần của vàng không giải thích được bằng PAXG**.

---

## 4. Suy giảm độ chính xác theo chân trời dự báo

Mô phỏng đúng điều kiện thị trường đóng cửa: đóng băng toàn bộ nhóm đặc trưng "trí nhớ Delta" tại giá trị cuối cùng quan sát được, các đặc trưng PAXG / vĩ mô / tin tức vẫn cập nhật. 400 khối × 50 nến (H1).

**MAE thành phần `close`, đơn vị USD:**

| Chân trời | D1 (một bước / mô hình / giữ delta) | H1 | M15 |
|---|---|---|---|
| 1 nến | 7,24 / 8,24 / 7,45 | 2,33 / 2,57 / 2,50 | 1,56 / 1,92 / 1,66 |
| 2–4 nến | 7,48 / 9,10 / 9,65 | 2,44 / 3,42 / 3,52 | 1,77 / 2,47 / 2,31 |
| 5–12 nến | — | 2,40 / 4,12 / 4,51 | 1,77 / 3,00 / 2,94 |
| 13–24 nến | — | 2,49 / 4,78 / 5,22 | 2,01 / 3,68 / 3,66 |
| **> 24 nến** | — | **2,54 / 5,72 / 6,37** | **2,62 / 5,82 / 5,67** |

*(D1 chỉ có chân trời tối đa 3 nến vì một kỳ nghỉ chỉ tương đương 1 nến ngày.)*

**Phát hiện thứ ba:** sai số tăng **2,2 lần** khi kéo dài từ 1 nến lên quá 24 nến (2,57 → 5,72 USD ở H1), trong khi mốc "một bước có trí nhớ đầy đủ" **đứng yên ở 2,5 USD**. Toàn bộ phần tăng thêm đến từ việc mất trí nhớ, không phải từ độ khó nội tại của chuỗi.

R² tương ứng ở H1 tụt từ 0,925 (1 nến) xuống **0,675** (> 24 nến).

Mô hình 27 đặc trưng chỉ hơn cách làm tầm thường nhất ("giữ nguyên tỷ lệ delta cuối cùng") **10 %** ở chân trời dài (5,72 so với 6,37).

---

## 5. So sánh sáu cách xử lý trên cùng bộ kỳ nghỉ

Bài toán: ước lượng **giá mở cửa phiên đầu tuần**. MAE, đơn vị USD.

| Xếp hạng | Cách xử lý | D1 | H1 | M15 | So với "không đổi" |
|---|---|---|---|---|---|
| 1 | Giả định giá không đổi (β = 0) | 2,813 | **2,835** | **2,609** | mốc |
| 2 | Neo lợi suất β = 0,15 | **2,723** | 2,934 | 2,701 | −3,2 % đến +3,5 % |
| 3 | Pipeline delta OHLC (hồi quy cuộn chiếu) | 8,453 | 3,914 | 3,216 | +23 % đến +139 % |
| 4 | Neo lợi suất β = 0,90 (beta quy trình cũ) | 6,711 | 7,795 | 7,148 | +139 % đến +175 % |
| 5 | Giữ nguyên delta (β = 1) | 7,419 | 8,559 | 7,849 | +164 % đến +202 % |
| 6 | **Quy trình cũ đúng như đã triển khai** | **30,993** | **32,538** | **30,619** | **+1 002 % đến +1 074 %** |

### 5.1. Đồng nhất thức nối các phương pháp

$$\Delta_t - \Delta_{t-1} = r_{XAU,t} - r_{PAXG,t}$$

Nghĩa là "giữ nguyên delta" chính là trường hợp **β = 1** của họ neo lợi suất. Sáu cách xử lý trên thực chất là **một họ duy nhất, chỉ khác giá trị β**:

| β | Tương ứng | Kết quả |
|---|---|---|
| 0,00 | Không dùng PAXG | Tốt nhất trong thực tế |
| **0,15** | **Giá trị tối ưu đo được** | **Tốt nhất về lý thuyết** |
| 0,90 | Beta trong phiên (quy trình cũ) | Sai số gấp 2,5–2,8 lần |
| 1,00 | Giữ nguyên delta | Sai số gấp 2,6–3,0 lần |

### 5.2. Vì sao quy trình cũ hỏng gấp 11 lần

Bước 4 cộng phần dư đặc thù `ε_t ~ N(0, κ²σ_e²)` vào **mỗi nến** trong kỳ nghỉ, với `κ = 1,5437` hiệu chỉnh ở Bước 5. Qua 50 nến H1, nhiễu tích lũy theo bước ngẫu nhiên:

```
σ_e = √(1 − R²) × σ_XAU ≈ √(1 − 0,44) × 29 bp ≈ 22 bp mỗi nến
× κ = 1,5437                                   → 34 bp mỗi nến
× √50 nến cuối tuần                            → 240 bp ≈ 2,4 % ≈ 53 USD
```

Khớp với sai số đo được 30,6–32,5 USD.

**Đây là lỗi thiết kế hàm mục tiêu, không phải lỗi lập trình.** Bước 5 hiệu chỉnh κ để *tương quan* của chuỗi 24/7 với PAXG hội tụ về tương quan nền ±0,05. Mục tiêu đó **trực giao** với độ chính xác mức giá: có thể làm khớp tương quan hoàn hảo trong khi đường giá trôi đi hàng chục USD.

---

## 6. Beta đúng thì cải thiện được bao nhiêu

Beta cuối tuần ước lượng **cuộn chiếu** — chỉ dùng các kỳ nghỉ đã qua, tối thiểu 30 kỳ trước khi áp dụng, không nhìn trước.

| Cách chọn beta | D1 | H1 | M15 |
|---|---|---|---|
| Giả định giá không đổi (β = 0) | 2,875 | 2,899 | 2,639 |
| Beta trong phiên = 0,90 | 6,791 | 7,790 | 7,166 |
| **Beta cuối tuần cuộn chiếu** | **2,754** | **2,793** | **2,544** |
| Beta hội tụ cuối kỳ | 0,1757 | 0,0874 | 0,0872 |
| **Cải thiện so với "không đổi"** | **−4,2 %** | **−3,7 %** | **−3,6 %** |
| Thiệt hại nếu dùng beta trong phiên | +136,2 % | +168,7 % | +171,5 % |

**Phát hiện thứ tư:** dùng beta đúng biến một phương pháp *tệ hơn 170 %* thành một phương pháp *tốt hơn 3,6–4,2 %*. Nhưng mức cải thiện 4 % là toàn bộ những gì khai thác được.

**Trần lý thuyết:** với R² qua kỳ nghỉ = 0,2389 (D1), mức giảm RMSE tối đa mà bất kỳ mô hình tuyến tính nào đạt được là

$$1 - \sqrt{1 - R^2} = 1 - \sqrt{0{,}7611} = 12{,}8\ \%$$

Ở H1 và M15, trần này chỉ còn 5,9 % và 5,8 %. Không mô hình nào — dù phức tạp đến đâu — vượt được ngưỡng này với dữ liệu PAXG.

---

## 7. Chất lượng đặc trưng biến động

Quy trình cũ không nhằm tạo mức giá mà tạo **ba đặc trưng** (Bước 6). Đo ở đúng mục đích đó: tương quan giữa biến động cuối tuần ước lượng và biến động thật của vàng.

| Đặc trưng | D1 (Pearson / Spearman) | H1 | M15 |
|---|---|---|---|
| Chuỗi 24/7 quy trình cũ (β, tin tức, ε) | 0,2412 / 0,1462 | 0,0924 / 0,0976 | 0,1476 / 0,1919 |
| **`\|r_PAXG\|` thô** | **0,3455 / 0,2196** | **0,1687 / 0,1462** | **0,1831 / 0,1799** |
| `\|β × r_PAXG\|` với β = 0,15 | 0,3455 / 0,2196 | 0,1687 / 0,1462 | 0,1831 / 0,1799 |

**Phát hiện thứ năm:** toàn bộ bộ máy phân tầng beta, điều biến tin tức và vòng lặp hiệu chỉnh κ làm đặc trưng biến động **xấu đi** so với việc chỉ lấy trị tuyệt đối lợi suất PAXG. Ở H1 tương quan giảm gần một nửa (0,092 so với 0,169).

Lưu ý: nhân β là phép biến đổi tuyến tính dương nên **không đổi tương quan** — hai dòng cuối trùng nhau. Điều này xác nhận thủ phạm là số hạng ε chứ không phải hệ số β.

**Đây là lời giải thích cuối cùng cho kết quả âm tính ở Bước 10:** ba đặc trưng cuối tuần xếp hạng 23–37 trên 40 theo SHAP không phải vì ý tưởng sai, mà vì chúng được dựng từ một chuỗi đã bị làm nhiễu có chủ đích.

---

## 8. Kết luận

### 8.1. Năm phát hiện

1. **PAXG dao động gấp 2,7–2,9 lần vàng** trong kỳ nghỉ; phần dư là nhiễu thị trường tiền mã hóa.
2. **Quan hệ neo sụp đổ khi thị trường giao ngay đóng cửa:** tương quan 0,905 → 0,489; beta 0,897 → 0,231.
3. **Sai số tăng 2,2 lần theo chân trời** khi mất trí nhớ, trong khi mốc một bước đứng yên.
4. **Beta trong phiên làm sai số tăng 136–172 %**; beta cuối tuần đúng chỉ cải thiện 3,6–4,2 %.
5. **Số hạng nhiễu ε phá hủy cả mức giá lẫn đặc trưng biến động**, khiến quy trình cũ tệ hơn 11 lần so với không làm gì.

### 8.2. Trả lời câu hỏi nghiên cứu

> PAXG có thay thế được vàng giao ngay ngoài giờ giao dịch không?

**Không, ở mức có ý nghĩa thực hành.** PAXG mang một lượng thông tin nhỏ nhưng thật (R² = 0,11–0,24, p < 1e-8). Khai thác tối ưu chỉ giảm được 3,6–4,2 % sai số, với trần lý thuyết 5,8–12,8 %. Trong khi đó, sai số còn lại (≈ 2,75 USD) **xấp xỉ đúng bằng chính đại lượng cần dự báo** (khoảng trống cuối tuần trung bình 2,9 USD).

Đây là kết quả âm tính có giá trị học thuật độc lập, và cần được trình bày như một đóng góp chứ không phải một thất bại.

### 8.3. Khuyến nghị sử dụng

| # | Khuyến nghị |
|---|---|
| 1 | Dùng chuỗi tái tạo cho **BIẾN ĐỘNG**, tuyệt đối không cho **HƯỚNG** (tương quan 0,34–0,49 quá thấp) |
| 2 | Nếu cần đặc trưng biến động cuối tuần, dùng thẳng `\|r_PAXG\|` — đơn giản hơn và tốt hơn 1,4–1,8 lần |
| 3 | Nếu tái tạo mức giá, dùng beta cuối tuần cuộn chiếu (0,087–0,176), tuyệt đối không dùng beta Bước 3 |
| 4 | Bỏ số hạng ε; chỉ giữ khi mô phỏng Monte Carlo và khi đó phải dùng phân vị nhiều đường mẫu |
| 5 | Luôn khai báo sai số **±2,8 USD** khi trình bày chuỗi 24/7 |
| 6 | Không trích R² 0,94–0,97 của dự báo một bước như thể mô tả chất lượng dữ liệu cuối tuần |

---

## 9. Tệp kết quả

| Tệp | Nội dung |
|---|---|
| `delta_ky_nghi_tong_hop.csv` | Tổng hợp ba khung: gap thật, ba ước lượng, tương quan và beta qua kỳ nghỉ |
| `delta_ky_nghi_chi_tiet_{tf}.csv` | Từng kỳ nghỉ: giá thật và các ước lượng |
| `delta_ky_nghi_beta_dung.csv` | So sánh beta trong phiên với beta cuối tuần cuộn chiếu |
| `delta_cuoi_tuan_theo_buoc_{tf}.csv` | MAE theo từng bước chân trời |
| `delta_cuoi_tuan_theo_nhom_{tf}.csv` | MAE theo nhóm chân trời |
| `delta_cuoi_tuan_r2_{tf}.csv` | R² suy giảm theo chân trời |
| `so_sanh_hai_phuong_phap.csv` | Xếp hạng sáu cách xử lý |
| `so_sanh_ky_nghi_chi_tiet_{tf}.csv` | Từng kỳ nghỉ với sáu ước lượng |
| `so_sanh_dac_trung_bien_dong.csv` | Chất lượng đặc trưng biến động |

Tất cả nằm trong `results/tables/`.

## 10. Cách chạy lại

```bash
python src/kiem_dinh/run_delta_gap_test.py D1 H1 M15
python src/kiem_dinh/run_delta_weekend_test.py D1 H1 M15
python src/kiem_dinh/run_so_sanh_hai_phuong_phap.py D1 H1 M15
```
