# SO SÁNH HAI PHƯƠNG PHÁP XỬ LÝ DỮ LIỆU CUỐI TUẦN

**Ngày chạy:** 23/08/2026 · **Mã nguồn:** `src/run_so_sanh_hai_phuong_phap.py`
**Dữ liệu kiểm định:** 279–319 kỳ nghỉ cuối tuần thật, 2020-08 → 2025-12

---

## 0. Kết luận ngắn

**Phương pháp mới tốt hơn phương pháp cũ rõ rệt — nhưng cả hai đều thua các mốc đối chiếu tầm thường.**

| Xếp hạng | Cách xử lý | MAE giá mở cửa đầu tuần (H1) |
|---|---|---|
| 1 | Giả định giá không đổi (không dùng PAXG) | **2,84 USD** |
| 2 | Neo lợi suất với β = 0,15 | 2,93 USD |
| 3 | **Phương pháp mới** (hồi quy delta OHLC cuộn chiếu) | **3,91 USD** |
| 4 | Neo lợi suất với β = 0,90 | 7,80 USD |
| 5 | Giữ nguyên delta (β = 1) | 8,56 USD |
| 6 | **Phương pháp cũ đúng như đã triển khai** (Bước 4–5) | **32,54 USD** |

Phương pháp cũ sai số **gấp 11,5 lần** phương pháp mới và **gấp 11,5 lần** việc không làm gì cả.

---

## 1. Hai phương pháp khác nhau ở đâu

**Phương pháp cũ (Bước 4–5) — neo theo LỢI SUẤT:**

$$\hat r_t = \beta(\text{chế độ})\cdot s\cdot r^{PAXG}_t\cdot(1+\lambda I_t) + \varepsilon_t, \qquad \hat{XAU}_{mở} = XAU_{đóng}\cdot\exp\Big(\sum \hat r_t\Big)$$

Neo vào giá đóng cửa thứ Sáu của **chính vàng**, không dùng mức giá tuyệt đối của PAXG.

**Phương pháp mới (pipeline delta OHLC) — neo theo MỨC GIÁ:**

$$\hat{XAU}_{col} = PAXG^{USD}_{col}\cdot\exp(\hat\Delta_{col})$$

Dùng trực tiếp mức giá PAXG, nên thừa hưởng toàn bộ sai lệch tỷ lệ delta.

**Đồng nhất thức nối hai phương pháp:**

$$\Delta_t - \Delta_{t-1} = r_{XAU,t} - r_{PAXG,t}$$

Nghĩa là "giữ nguyên delta" chính là trường hợp **β = 1** của họ neo lợi suất. Hai phương pháp thực chất **cùng một họ, chỉ khác giá trị β**:

| β | Tương ứng với |
|---|---|
| 0,00 | Giả định giá không đổi |
| **0,15** | **Giá trị tối ưu đo được trên dữ liệu kỳ nghỉ** |
| 0,90 | Phương pháp cũ (β trong phiên, lấy từ Bước 3) |
| 1,00 | Giữ nguyên delta |

Phương pháp mới không cố định β mà **học nó bằng hồi quy cuộn chiếu** — đó chính là lý do nó tốt hơn hẳn phương pháp cũ.

---

## 2. Kết quả tái tạo mức giá

MAE ước lượng giá mở cửa phiên đầu tuần (USD):

| Cách xử lý | D1 | H1 | M15 |
|---|---|---|---|
| Giá không đổi (β=0) | **2,81** | **2,84** | **2,61** |
| β = 0,15 tối ưu | **2,72** | 2,93 | 2,70 |
| Pipeline delta OHLC (mới) | 8,45 | 3,91 | 3,22 |
| β = 0,90 (β phương pháp cũ) | 6,71 | 7,80 | 7,15 |
| β = 1 (giữ delta) | 7,42 | 8,56 | 7,85 |
| **Phương pháp cũ nguyên văn** | **30,99** | **32,54** | **30,62** |

So với mốc "giá không đổi": phương pháp cũ **+1 002 % đến +1 074 %**, phương pháp mới +38 % (H1) và +23 % (M15).

### Vì sao phương pháp cũ hỏng đến vậy: số hạng nhiễu ε

Bước 4 thêm phần dư đặc thù `ε_t ~ N(0, κ²σ_e²)` với `σ_e = σ_XAU·√(1−R²)` và `κ = 1,5437` (hiệu chỉnh ở Bước 5). Với **mỗi nến** trong kỳ nghỉ, một lượng nhiễu độc lập được cộng vào. Qua 50 nến H1 (hoặc 190 nến M15), nhiễu **tích lũy theo bước ngẫu nhiên**:

```
σ_e ≈ √(1−0,44) × 29 bp ≈ 22 bp mỗi nến
× κ = 1,5437                → 34 bp mỗi nến
× √50 nến cuối tuần         → 240 bp ≈ 2,4 % ≈ 53 USD
```

Khớp với sai số đo được 32–43 USD.

**Đây là lỗi thiết kế mục tiêu, không phải lỗi lập trình.** Bước 5 hiệu chỉnh κ để **tương quan** của chuỗi 24/7 với PAXG hội tụ về tương quan nền ±0,05. Mục tiêu đó **trực giao** với độ chính xác mức giá: người ta có thể làm khớp tương quan một cách hoàn hảo trong khi đường giá trôi đi hàng chục USD. Chuỗi thu được đúng về mặt thống kê bậc hai nhưng vô dụng về mặt mức giá.

---

## 3. So sánh chất lượng đặc trưng biến động

Phương pháp cũ không nhằm tạo mức giá mà nhằm tạo **ba đặc trưng** (Bước 6). Vì vậy phải đo thêm ở đúng mục đích đó: tương quan giữa biến động cuối tuần ước lượng và **biến động thật** của vàng qua kỳ nghỉ.

| Đặc trưng | D1 | H1 | M15 |
|---|---|---|---|
| Biến động ước lượng từ chuỗi 24/7 (phương pháp cũ) | 0,241 | 0,092 | 0,148 |
| **\|r_PAXG\| thô — không β, không ε, không tin tức** | **0,346** | **0,169** | **0,183** |

*(Spearman cho cùng thứ hạng: 0,146 / 0,098 / 0,192 so với 0,220 / 0,146 / 0,180)*

**Toàn bộ bộ máy của Bước 4–5 — phân tầng beta, điều biến tin tức, vòng lặp hiệu chỉnh κ — làm đặc trưng biến động XẤU ĐI** so với việc chỉ lấy trị tuyệt đối lợi suất PAXG qua kỳ nghỉ. Ở khung H1, tương quan giảm gần một nửa (0,092 so với 0,169).

Đây là lời giải thích cuối cùng cho kết quả âm tính ở Bước 10: ba đặc trưng cuối tuần xếp hạng 23–37/40 theo SHAP vì chúng được dựng từ một chuỗi đã bị làm nhiễu có chủ đích.

---

## 4. Bảng tổng kết

| Tiêu chí | Phương pháp cũ (Bước 4–5) | Phương pháp mới (delta OHLC) |
|---|---|---|
| Neo vào | Giá đóng cửa vàng, cộng dồn lợi suất | Mức giá PAXG cùng nến |
| β | Cố định theo chế độ, lấy từ trong phiên (0,86–0,93) | **Học cuộn chiếu từ dữ liệu** |
| Nhiễu bổ sung | **Có — ε tích lũy theo bước ngẫu nhiên** | Không |
| Mục tiêu hiệu chỉnh | Khớp tương quan nền ±0,05 | Cực tiểu sai số dự báo |
| Ràng buộc hình học OHLC | Không có | **Có, áp bắt buộc** |
| Tách riêng bốn thành phần OHLC | Không, chỉ một chuỗi giá | **Có, bốn mục tiêu** |
| Kiểm tra lookahead | Không có | **Có, tự động** |
| MAE giá mở đầu tuần (H1) | 32,54 USD | **3,91 USD** |
| Tương quan đặc trưng biến động (D1) | 0,241 | *(không tạo đặc trưng này)* |
| **Kết luận** | **Không dùng được** | **Dùng được nhưng chưa thắng mốc tầm thường** |

---

## 5. Khuyến nghị: phương án lai

Không phương pháp nào trong hai nên giữ nguyên. Kết hợp phần tốt của cả hai:

1. **Giữ cách neo theo lợi suất của phương pháp cũ** — neo vào giá vàng thứ Sáu, không neo vào mức giá PAXG. Điều này tránh thừa hưởng chênh lệch mức giá giữa hai thị trường (sai số ~38 bp mỗi kỳ nghỉ).
2. **Thay β trong phiên bằng β cuối tuần ước lượng cuộn chiếu** (0,15 ở D1, 0,087 ở H1/M15). Đây là sửa lỗi, không phải tinh chỉnh.
3. **Bỏ hẳn số hạng nhiễu ε khi mục đích là dựng đặc trưng.** Giữ ε chỉ khi cần mô phỏng Monte Carlo phân phối, và khi đó không được dùng một đường mẫu duy nhất làm dữ liệu đầu vào cho mô hình.
4. **Bỏ vòng lặp hiệu chỉnh khớp tương quan ở Bước 5** — hoặc đổi hàm mục tiêu sang cực tiểu sai số dự báo giá mở cửa đầu tuần, đo trên chính các kỳ nghỉ đã có đáp án.
5. **Giữ toàn bộ hạ tầng đánh giá của phương pháp mới:** ràng buộc hình học OHLC, kiểm tra lookahead tự động, đối chiếu với mô hình ngây thơ, kiểm định ADF/KPSS trên phần dư.
6. **Dùng `|r_PAXG|` thô làm đặc trưng biến động cuối tuần** thay cho `bien_dong_cuoi_tuan` hiện tại — đơn giản hơn và tương quan cao hơn 1,4–1,8 lần.

Kỳ vọng thực tế sau khi sửa: MAE khoảng **2,7 USD** so với 2,84 USD của mốc "không làm gì" — cải thiện 3–4 %, với trần lý thuyết là 12,8 %.

---

## 6. Tệp kết quả

| Tệp | Nội dung |
|---|---|
| `results/tables/so_sanh_hai_phuong_phap.csv` | Bảng xếp hạng sáu cách xử lý, ba khung |
| `results/tables/so_sanh_ky_nghi_chi_tiet_{tf}.csv` | Từng kỳ nghỉ: giá thật và sáu ước lượng |
| `results/tables/so_sanh_dac_trung_bien_dong.csv` | Chất lượng đặc trưng biến động |
| `results/tables/delta_ky_nghi_beta_dung.csv` | β trong phiên so với β cuối tuần |
