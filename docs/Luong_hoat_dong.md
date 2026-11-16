# LUỒNG HOẠT ĐỘNG TỪ INPUT ĐẾN OUTPUT (CONVNEXT-TINY)
> **Tài liệu tham khảo:** Trích xuất từ quy trình huấn luyện và kiểm thử mô hình trong `ConvNeXtTiny/kltn-convnext-tiny.ipynb`.  
> **Mục đích:** Quy chuẩn các bước và kỹ thuật để thiết kế sơ đồ quy trình (Flowchart / Architecture Diagram).

---

### 1. Dữ liệu đầu vào (Input)
* **Tập dữ liệu ảnh rác thải**: 4 lớp con (`glass`, `metal`, `paper`, `plastic`).

---

### 2. Tiền xử lý dữ liệu
* **Ánh xạ phân cấp siêu lớp (Hierarchical Mapping)**: Thiết lập từ điển ánh xạ 4 lớp con (`glass`, `metal`, `paper`, `plastic`) về 3 siêu nhóm vật liệu (`cellulose`, `metal`, `polymer_glass`).
* **Phân chia dữ liệu phân tầng (Stratified Split)**: Tách tập dữ liệu thành 3 tập độc lập 80% Train – 10% Validation – 10% Test có bảo toàn tỷ lệ nhãn (cố định `SEED = 42`).
* **Mã hóa nhãn One-hot**: Chuyển đổi nhãn lớp con và siêu lớp thành vector nhị phân một vị trí nóng (One-hot vector) để nạp vào hàm mất mát đa tác vụ.
* **Tái định cỡ ảnh quang học (Area Resampling)**: Đọc và resize ảnh về kích thước chuẩn $320 \times 320$ bằng thuật toán `ResizeMethod.AREA` (kèm `antialias=True`) chống răng cưa và biến dạng vật thể.
* **Chuẩn hóa kênh màu (ConvNeXt Normalization)**: Chuẩn hóa phân phối giá trị điểm ảnh theo hàm chuẩn `preprocess_convnext` trước khi truyền vào mô hình.

---

### 3. Tăng cường dữ liệu (Data Augmentation - áp dụng tập Train)
* **Tăng cường hình học (Geometric Augmentation)**: Lật ngẫu nhiên (ngang/dọc), xoay ($\pm 25\%$), phóng to/thu nhỏ ($\pm 20\%$) và biến thiên độ tương phản.
* **Tăng cường trộn ảnh nâng cao (Mixup & CutMix)**: Áp dụng ngẫu nhiên 50/50 giữa `Mixup` và `CutMix` (hệ số $\alpha = 0.2$ theo phân phối Beta).

---

### 4. Kiến trúc mô hình (Hierarchical ConvNeXt-Tiny)
* **Mạng xương sống (Backbone)**: ConvNeXt-Tiny (Pre-trained ImageNet) trích xuất đặc trưng sâu.
* **Kết hợp Pooling đa đặc trưng**: Ghép nối song song Global Average Pooling (GAP) và Global Max Pooling (GMP).
* **Khối đặc trưng dùng chung (Shared Feature Layer)**: Dense (1024) $\rightarrow$ Layer Normalization $\rightarrow$ Kích hoạt phi tuyến GELU $\rightarrow$ Khử khớp quá mức (Dropout 0.3).
* **Nhánh phân loại chính (Sub-class Head - 4 lớp)**: Chuẩn hóa L2 $\rightarrow$ Tích vô hướng góc `CosineDense(scale=20.0)` $\rightarrow$ Softmax.
* **Nhánh phụ trợ siêu lớp (Super-class Head - 3 lớp)**: Dense (256) $\rightarrow$ GELU $\rightarrow$ Dropout (0.2) $\rightarrow$ Dense Softmax.

---

### 5. Chiến lược huấn luyện mô hình (Two-Stage Training)
* **Hàm mất mát đa tác vụ**: Categorical Crossentropy có Label Smoothing (0.05), chia trọng số 70% Sub-class và 30% Super-class.
* **Giai đoạn 1 (Warm-up Heads - 15 Epochs)**: Đóng băng backbone, huấn luyện các Head với optimizer AdamW ($lr = 3\times 10^{-4}$), ReduceLROnPlateau và EarlyStopping.
* **Giai đoạn 2 (Deep Fine-Tuning - 25 Epochs)**: Mở khóa 40 layers đỉnh của backbone, tối ưu bằng AdamW kết hợp bộ suy giảm CosineDecay ($lr_{start} = 10^{-4}$).

---

### 6. Suy luận kiểm thử đa góc nhìn (5-View TTA Inference)
* **Tạo 5 biến thể góc nhìn (Test-Time Augmentation)**: Gốc, Lật ngang (Horizontal Flip), Xoay $90^\circ$, Xoay $270^\circ$, Cắt trung tâm 90% (Center Crop).
* **Tổng hợp xác suất đa góc nhìn (Softmax Ensemble)**: Tính trung bình xác suất của 5 góc nhìn để đưa ra dự đoán tổng thể.
* **Đo lường độ ổn định (Consensus Stability)**: Tính tỷ lệ đồng thuận giữa 5 góc nhìn dự đoán.
* **Tính toán chỉ số suy luận**: Xác định độ tự tin Top 1 (Conf) và khoảng cách biên (Margin = Top 1 - Top 2).

---

### 7. Hệ thống kiểm soát an toàn 2 chốt & Quy trình tái thẩm định thích ứng
* **Khóa bộ ngưỡng an toàn thống kê trên tập Validation (μ - kσ)**:
  * *Chốt 1 (Confidence Gate - theo từng lớp)*: Ngưỡng tự tin thích ứng riêng từng lớp τ_conf = μ_c - k1*σ_c.
  * *Chốt 2 (Margin Gate - chung)*: Ngưỡng biên phân biệt chung τ_margin = μ_m - k2*σ_m.
* **Phân luồng ban đầu qua Bộ lọc chuẩn kép**:
  * *Thỏa mãn đồng thời cả Chốt 1 VÀ Chốt 2*: Đạt chuẩn an toàn tuyệt đối $\rightarrow$ Chuyển thẳng sang **Tự động gắp**.
  * *Không đạt chuẩn kép*: Chuyển sang **Quy trình tái thẩm định thích ứng** (nhằm tối ưu tỷ lệ tự động hóa và giảm tải cho khay thủ công).
* **Quy trình tái thẩm định thích ứng cho mẫu có độ bất định**:
  * *Cơ chế thẩm định an toàn tổng hợp (Composite Safety Evaluation)*: Đánh giá bù trừ tương hỗ giữa độ tự tin và khoảng cách biên qua chỉ số an toàn kết hợp ($S_{composite} = 0.5 \cdot s_{conf} + 0.5 \cdot s_{margin} \ge 1.0$, kèm ngưỡng chặn dưới $Conf \ge 70\%$) $\rightarrow$ Xác nhận đạt chuẩn, đưa về **Tự động gắp**.
  * *Cơ chế xác thực đồng thuận đa góc nhìn (TTA Consensus Verification)*: Áp dụng ngưỡng dung sai an toàn ($S_{composite} \ge 0.90$) khi mô hình đạt độ nhất quán tuyệt đối 100% trên cả 5 góc nhìn suy luận TTA (kèm ngưỡng chặn dưới $Conf \ge 65\%$) $\rightarrow$ Xác nhận đạt chuẩn, đưa về **Tự động gắp**.
  * *Phân luồng thủ công (Manual Fallback)*: Mẫu không thỏa mãn bất kỳ tiêu chí an toàn nào $\rightarrow$ Xác định là mẫu có độ bất định cao, chuyển đến khay thủ công để xử lý.

---

### 8. Kết quả đầu ra & Phân luồng điều khiển (Output & Action Routing)
* **Nhãn phân loại & Độ tin cậy**: Nhãn rác dự đoán, điểm tin cậy và biên phân biệt.
* **Phân luồng hành động thực tế**:
  * **Tự động gắp (`Tu_Dong_Gap`)**: Mẫu đạt chuẩn an toàn, kích hoạt cơ cấu gắp tự động của hệ thống.
  * **Chuyển khay thủ công (`Chuyen_Khay_Thu_Cong`)**: Mẫu bị chặn do nghi ngờ lỗi hoặc độ tự tin thấp, chuyển sang phân loại bằng tay.
* **Báo cáo nghiệm thu & Trực quan hóa**: Đánh giá tỷ lệ bắt lỗi, tỷ lệ lọt lưới và trực quan hóa chi tiết các trường hợp phân loại.

---

### 9. Đánh giá đối sánh kiến trúc mô hình (Benchmark với ResNet-50)
* **Mục tiêu đối sánh**: So sánh hiệu năng giữa kiến trúc hiện đại ConvNeXt-Tiny (áp dụng triết lý Vision Transformer trên mạng tích chập) và kiến trúc kinh điển ResNet-50 trên cùng bài toán phân loại rác đa cấp.
* **Đồng nhất điều kiện thực nghiệm**:
  * Sử dụng cùng tập dữ liệu phân tầng 80/10/10 và độ phân giải quang học $320 \times 320$ (Area Resampling).
  * Đồng nhất kiến trúc đầu ra đa tác vụ phân cấp: Nhánh chính tích vô hướng góc `CosineDense(scale=20.0)` kết hợp nhánh phụ siêu lớp.
  * Áp dụng cùng quy trình suy luận 5-View TTA và hệ thống kiểm soát an toàn 2 chốt chặn.
* **Tiêu chí & Chỉ số đối sánh**:
  * *Hiệu năng phân loại*: So sánh độ chính xác tổng thể (Top-1 Accuracy) và chỉ số Macro F1-Score trên 4 lớp rác.
  * *Chỉ số an toàn vận hành*: Tỷ lệ tự động gắp an toàn (`Tu_Dong_Gap`), Tỷ lệ tóm gọn lỗi sai (`Caught Error Rate`) và Số lỗi lọt lưới (`Leaked Errors`).
  * *Chi phí tính toán*: So sánh số lượng tham số (Parameters), tài nguyên bộ nhớ và thời gian suy luận (Latency) trên từng mẫu ảnh.

---

### 10. Đánh giá đối sánh phương pháp gán nhãn tự động (Stage 1 & Stage 2)
* **Mục tiêu nghiên cứu**: Kiểm định giả thuyết khoa học: *"Liệu mô hình học từ dữ liệu gán nhãn tự động có bảo vệ an toàn (Model V2) có đạt hiệu năng tiệm cận với mô hình học từ 100% dữ liệu gán thủ công (Model V1) để giảm chi phí nhân lực hay không?"*
* **Giai đoạn 1 (Stage 1 - Huấn luyện mầm & Gán nhãn tự động an toàn)**:
  * *Huấn luyện mô hình hạt nhân (Seed Model)*: Sử dụng tập dữ liệu mầm đã dán nhãn thủ công (`MyTrashNet_Duplicates` ~1.512 ảnh) chia tỷ lệ 85% Train – 15% Validation để huấn luyện ConvNeXt-Tiny ban đầu.
  * *Hiệu chuẩn bộ lọc an toàn 2 chốt*: Xác định ngưỡng tự tin riêng từng lớp ($\tau_{conf}$) và biên phân biệt ($\tau_{margin}$) trên tập Validation của Duplicates.
  * *Vận hành gán nhãn tự động quy mô lớn*: Đưa tập ảnh lớn chưa gán nhãn (`MyTrashNet_Unique` ~7.264 ảnh) qua bộ lọc 5-View TTA:
    - *Gán nhãn tự động thành công*: Các mẫu vượt qua 2 chốt an toàn được tự động gán nhãn để nạp vào tập huấn luyện tiếp theo.
    - *Chuyển khay thủ công*: Các mẫu nghi ngờ hoặc biên độ hẹp chuyển cho người phân loại can thiệp.
* **Giai đoạn 2 (Stage 2 - Huấn luyện đối sánh & Kiểm định trực diện V1 vs V2)**:
  * *Nguyên tắc bảo vệ tập Test (Zero Data Leakage)*: Khóa chặt tập Test chuẩn 10% độc lập (`test_set_chuan_10_percent.csv` từ Model V1) với nhãn gốc Ground Truth chuẩn tên file; tuyệt đối không đưa tập này vào quá trình huấn luyện V2.
  * *Huấn luyện Model V2*: Huấn luyện mô hình ConvNeXt-Tiny trên tập dữ liệu đối sánh (kết hợp tập Duplicates và toàn bộ ảnh Unique đã được gán nhãn tự động từ Stage 1).
  * *Đối chứng trực diện (Model V1 vs Model V2)*: Kiểm tra song song cả hai mô hình trên cùng tập Test chuẩn 10% để đối soát: độ chính xác tổng thể, F1-Score từng lớp, tỷ lệ tự động gắp và tỷ lệ lỗi lọt lưới.

---

### 11. Chọn ra mô hình tối ưu nhất (Optimal Model Selection)
* **Bộ tiêu chí đánh giá đa chiều**:
  * *Độ chính xác phân loại*: Điểm số Accuracy và F1-Score vượt trội trên tập Test chuẩn độc lập.
  * *Mức độ an toàn tuyệt đối*: Ưu tiên số lỗi lọt lưới thấp nhất (hướng tới 0 lỗi lọt lưới) và khả năng tóm gọn tối đa các ca phân loại sai vào khay thủ công.
  * *Tỷ lệ tự động hóa tối đa*: Tỷ lệ mẫu được phân luồng tự động gắp (`Tu_Dong_Gap`) đạt mức cao nhất để giảm thiểu sự can thiệp của con người.
  * *Khả năng mở rộng & tiết kiệm chi phí*: Đánh giá hiệu quả kinh tế giữa việc dùng 100% nhãn thủ công và phương pháp gán nhãn tự động an toàn.
* **Tổng hợp và phân tích cân bằng Pareto**: Phân tích điểm cân bằng tối ưu giữa độ chính xác, tỷ lệ tự động gắp an toàn và chi phí tạo lập dữ liệu.
* **Quyết định mô hình tối ưu triển khai**: Lựa chọn phiên bản mô hình xuất sắc nhất để đóng gói trọng số (Weights Checkpoint), sẵn sàng tích hợp vào hệ thống robot phân loại rác thải tự động trong thực tế.

