# MOO-UAV-assisted-FL

**Tối ưu đa mục tiêu trong huấn luyện Federated Learning trên mạng có UAV hỗ trợ.**

Repository phục vụ việc phát triển ý tưởng, xây dựng mô hình và thực nghiệm cho một bài báo nghiên cứu. Project hướng tới lựa chọn tập thiết bị tham gia FL và phân bổ tài nguyên để cân bằng ba yếu tố: **chất lượng mô hình, năng lượng tiêu thụ và thời gian huấn luyện**.

Mô hình mạng và ý tưởng ban đầu được tham khảo từ bài báo **Federated Spatio-Temporal Policy Learning for Efficient Resource Management in UAV-Assisted IoT Edge Networks (FSTPO)**. Hướng phát triển hiện tại được trình bày trong draft **Information-Aware Multiobjective Evolutionary Optimization with Multi-Fidelity Evaluation for UAV-Assisted Federated Learning**.

## 1. Động lực nghiên cứu

Trong mạng FL có UAV hỗ trợ, thiết bị mặt đất sở hữu dữ liệu cục bộ khác nhau và có điều kiện truyền thông, khả năng tính toán, dung lượng pin không đồng nhất. Việc chọn thiết bị vì kênh tốt hoặc chi phí thấp có thể bỏ qua dữ liệu quan trọng cho mô hình chung. Ngược lại, chọn thêm thiết bị chứa dữ liệu hữu ích có thể làm tăng năng lượng và kéo dài vòng huấn luyện.

Project đặt ra câu hỏi:

> Làm thế nào lựa chọn một tập thiết bị có dữ liệu bổ trợ và phân bổ tài nguyên hiệu quả, khi chất lượng của lịch huấn luyện tốn kém để đánh giá và thông tin về thiết bị có thể không đầy đủ hoặc đã cũ?

Giá trị của một thiết bị được xem xét trong quan hệ với cả tập được chọn. Gradient khác biệt có thể phản ánh dữ liệu hiếm hữu ích, nhưng cũng có thể đến từ nhãn nhiễu; vì vậy, các chỉ số đại diện cần được đối chiếu với chất lượng học thực tế.

## 2. Mô hình hệ thống

Hệ thống gồm ba thành phần:

| Thành phần | Vai trò |
| --- | --- |
| Thiết bị IoT / client | Giữ dữ liệu tại chỗ, huấn luyện mô hình cục bộ và gửi cập nhật. |
| UAV | Cung cấp kết nối, tiếp nhận và tổng hợp cập nhật từ các client được gán. |
| Coordinator | Duy trì mô hình toàn cục, điều phối việc tham gia và tổng hợp cập nhật từ các UAV. |

Mỗi vòng FL gồm phân phối mô hình, huấn luyện cục bộ, truyền cập nhật, tổng hợp tại UAV và cập nhật mô hình toàn cục. Tổng hợp phân cấp sử dụng trọng số nhất quán với phép tổng hợp trên tập client tham gia.

Phạm vi ban đầu theo draft JNCA:

- FL đồng bộ, dữ liệu cố định; số bước SGD cục bộ và kích thước minibatch cố định.
- Chuyển động UAV cho trước theo thời gian vật lý; chưa tối ưu quỹ đạo.
- Quỹ băng thông trực giao giữa các UAV và công suất uplink cố định.
- Mô hình kênh ban đầu xem kênh không đổi trong một vòng.
- Bộ điều khiển sử dụng trạng thái mạng và các báo cáo được phép quan sát; không mặc định biết gradient hiện tại của mọi client.

Offloading ứng dụng độc lập trong bài FSTPO, tối ưu quỹ đạo, personalized FL và concept drift nằm ngoài phạm vi khởi đầu.

## 3. Bài toán tối ưu đa mục tiêu

### Đầu vào, quyết định và đầu ra

| Thành phần | Nội dung |
| --- | --- |
| Đầu vào | Mô hình hiện tại, dữ liệu phân tán, trọng số quần thể mục tiêu, trạng thái kênh, giới hạn băng thông/CPU, pin, deadline và lịch sử báo cáo. |
| Quyết định chính | Chọn client, gán client–UAV, phân bổ băng thông và tần số CPU của client. |
| Quyết định mở rộng | Chọn client để thu thập thông tin mới (probing) và cấp tài nguyên cho hoạt động này. |
| Đầu ra | Tập lịch khả thi thể hiện các đánh đổi Pareto; một lịch được chọn để thực thi theo ưu tiên đã xác định. |

### Hàm mục tiêu

Với cùng mô hình khởi tạo và ngân sách gồm $K$ vòng FL, draft xét bài toán:

$$
\min_{\pi}\;\mathbf{J}(\pi)=\left(
\mathbb{E}[L_{\mathrm{val}}(w_K)],\;
\mathbb{E}\left[\sum_{k=0}^{K-1}E_k\right],\;
\mathbb{E}\left[\sum_{k=0}^{K-1}T_k\right]
\right).
$$

Trong đó:

- $\pi$ là chính sách lựa chọn thiết bị và phân bổ tài nguyên.
- $L_{\mathrm{val}}(w_K)$ là validation loss của mô hình cuối trên quần thể mục tiêu.
- $E_k$ là năng lượng vận hành trong vòng $k$.
- $T_k$ là thời gian thực của vòng $k$.

Ba mục tiêu được giữ riêng để phân tích tập nghiệm Pareto. Trọng số quần thể dùng để đánh giá chất lượng học được xác định trước, không thay đổi theo việc loại bỏ các client khó phục vụ.

Bước triển khai đầu tiên tối ưu lịch một vòng tại cùng snapshot mô hình và trạng thái hệ thống. Chất lượng của lịch một vòng sau đó cần được kiểm tra trong quá trình FL nhiều vòng.

### Ràng buộc

Các lịch phải thỏa điều kiện gán client–UAV, tính khả dụng của liên kết, giới hạn băng thông, miền tần số CPU, số lượng client tham gia, deadline và pin dự trữ. Client không hoạt động nhận tài nguyên bằng 0; liên kết hoạt động phải có băng thông dương.

Chi phí được mô hình hóa theo phạm vi đã khai báo, gồm tính toán, truyền nhận, phân phối mô hình, tổng hợp, backhaul, bay/hover và các hoạt động probing hoặc tối ưu online. Thời gian vòng làm tiến đồng hồ vật lý, qua đó ảnh hưởng trạng thái mạng và năng lượng UAV.

## 4. Hướng phát triển từ FSTPO

Bài FSTPO cung cấp nền tảng về mạng UAV–IoT và điều khiển kết hợp lựa chọn thiết bị với phân bổ tài nguyên. Draft JNCA phát triển theo hướng tối ưu tiến hóa đa mục tiêu, sử dụng validation loss để đánh giá chất lượng học, đồng thời xem xét chi phí đánh giá và mức độ sẵn có của thông tin.

| Hướng | Ý tưởng | Nội dung cần đánh giá |
| --- | --- | --- |
| **A — Set-aware multiobjective scheduling** | Tìm kiếm tiến hóa trên tập client và tài nguyên, xét tính bổ trợ của dữ liệu giữa các client. | Chất lượng Pareto so với chọn ngẫu nhiên, greedy và các thuật toán tiến hóa đối chứng dưới cùng ngân sách. |
| **B — Multi-fidelity evaluation** | Kết hợp dự đoán rẻ, rollout rút gọn và đánh giá tham chiếu đầy đủ; nâng mức đánh giá cho các ứng viên có triển vọng. | Lợi ích khi tính đủ chi phí đánh giá, hiệu chuẩn, khám phá và kiểm chứng cuối. |
| **C — Adaptive probing** | Thu thông tin mới có tính chi phí, cập nhật dự đoán rồi tối ưu lại lịch huấn luyện. | Khi nào thông tin mới giúp cải thiện quyết định đủ để bù chi phí thu thập. |

Trong hướng B, tập nghiệm dự đoán và tập nghiệm đã đánh giá tham chiếu được quản lý riêng. Các kết luận về chất lượng Pareto cuối cùng phải dựa trên cùng giao thức tham chiếu.

**Multi-fidelity** phục vụ đánh giá các lịch ứng viên trong quá trình tìm kiếm. **Probing** thu thông tin mới từ thiết bị và phát sinh chi phí vận hành mạng. Các hướng A, B, C dự kiến được triển khai tuần tự; B phụ thuộc vào kết quả khảo sát chi phí đánh giá, còn C mở rộng scheduler sang thông tin không đầy đủ.

## 5. Lộ trình thực nghiệm

1. **Xây dựng mô phỏng nhỏ:** bắt đầu với 2 UAV và 6 client; kiểm tra mô hình kênh, phân bổ tài nguyên, thời gian, năng lượng và pin.
2. **Tích hợp FL:** local SGD, checkpoint có thể tái lập, tổng hợp phân cấp có trọng số và validation độc lập.
3. **Phát triển hướng A:** xây dựng baseline và bộ lập lịch xét tập client; kiểm tra với liệt kê tập con trong bài toán nhỏ có phân bổ cố định.
4. **Khảo sát và phát triển hướng B:** đo chi phí, sai lệch và tương quan thứ hạng giữa các mức đánh giá trước khi thiết kế cơ chế nâng mức.
5. **Mở rộng sang hướng C:** thêm báo cáo cũ, probing và lập lịch lại sau quan sát; tính đủ chi phí thu thông tin.

Kịch bản khởi đầu đặt client chứa lớp hiếm trên kênh yếu, kết hợp client dữ liệu phổ biến và client có nhãn nhiễu. Fashion-MNIST với CNN nhỏ là cấu hình khởi đầu được đề xuất; CIFAR-10 và mạng lớn hơn dành cho bước mở rộng.

Các chỉ số dự kiến gồm chất lượng Pareto đã kiểm chứng, test loss/accuracy, macro-F1, recall lớp hiếm, thời gian/năng lượng đến một chất lượng mục tiêu, vi phạm deadline, mức tiêu hao pin và chi phí optimizer/probing. So sánh cần thống nhất dữ liệu, giao thức FL, thông tin được phép sử dụng và ngân sách thực tế.

## 6. Tài liệu và cấu trúc repository

```text
MOO-UAV-assisted-FL/
|-- README.md
|-- docs/
|   |-- source idea/             # Bài báo FSTPO tham khảo ban đầu
|   |-- developing directions/   # Draft JNCA_Huy.pdf
|   |-- 1602.05629v4.pdf         # Bài báo FedAvg
|   `-- weekly presentation/     # Slide PDF và mã LaTeX
`-- Implementation/
    |-- Direction A/
    |-- Direction B/
    `-- Direction C/
```

- [Bài báo FSTPO](docs/source%20idea/Federated_Spatio-Temporal_Policy_Learning_for_Efficient_Resource_Management_in_UAV-Assisted_IoT_Edge_Networks.pdf): mô hình mạng và ý tưởng tham khảo ban đầu.
- [Draft JNCA](docs/developing%20directions/JNCA_Huy.pdf): mô hình bài toán, hướng thuật toán và kế hoạch thực nghiệm đang phát triển.
- [Bài báo FedAvg](docs/1602.05629v4.pdf): nền tảng về huấn luyện FL bằng local SGD và tổng hợp mô hình.
- [Slide tổng hợp](docs/weekly%20presentation/slides.pdf) và [mã LaTeX](docs/weekly%20presentation/slides.tex): tài liệu trình bày và thảo luận định kỳ.

## 7. Trạng thái hiện tại

Project đang ở giai đoạn **phát triển ý tưởng và đặc tả bài toán**. Repository hiện chứa tài liệu tham khảo, draft và slide; ba thư mục triển khai A/B/C còn trống. Chưa có chương trình thực nghiệm hoặc kết quả benchmark.

Bước tiếp theo là xây dựng mô phỏng mạng và FL engine dùng chung, sau đó triển khai hướng A trước khi bổ sung B và C. Tính mới và hiệu quả của các đóng góp dự kiến cần được kiểm chứng trước khi hoàn thiện bài báo.