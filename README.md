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

Bản triển khai v1 hiện dùng UAV hover với vị trí cố định; chuyển động cho trước theo draft là bước mở rộng tiếp theo. Offloading ứng dụng độc lập trong bài FSTPO, tối ưu quỹ đạo, personalized FL và concept drift nằm ngoài phạm vi khởi đầu.

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

Kịch bản mở rộng dự kiến đặt client chứa lớp hiếm trên kênh yếu, kết hợp client dữ liệu phổ biến và client có nhãn nhiễu; các kịch bản này chưa được đánh giá đầy đủ trong v1. Fashion-MNIST với CNN nhỏ là cấu hình khởi đầu được đề xuất; CIFAR-10 và mạng lớn hơn dành cho bước mở rộng.

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
    |   |-- Deep Report/         # Phân tích và phản biện Direction A
    |   `-- src/v1/
    |       |-- problem-formulation.md
    |       |-- README.md
    |       |-- report.md
    |       |-- run.py
    |       |-- make_report.py
    |       |-- configs/
    |       |-- uavfl/           # Mô hình, FL engine, NSGA-II và MOEA/D
    |       |-- tests/
    |       `-- results/         # Benchmark, logs và biểu đồ
    |-- Direction B/             # Chưa triển khai
    `-- Direction C/             # Chưa triển khai
```

- [Bài báo FSTPO](docs/source%20idea/Federated_Spatio-Temporal_Policy_Learning_for_Efficient_Resource_Management_in_UAV-Assisted_IoT_Edge_Networks.pdf): mô hình mạng và ý tưởng tham khảo ban đầu.
- [Draft JNCA](docs/developing%20directions/JNCA_Huy.pdf): mô hình bài toán, hướng thuật toán và kế hoạch thực nghiệm đang phát triển.
- [Bài báo FedAvg](docs/1602.05629v4.pdf): nền tảng về huấn luyện FL bằng local SGD và tổng hợp mô hình.
- [Slide tổng hợp](docs/weekly%20presentation/slides.pdf) và [mã LaTeX](docs/weekly%20presentation/slides.tex): tài liệu trình bày và thảo luận định kỳ.

## 7. Trạng thái hiện tại

**Cập nhật ngày 26/10/2026:** project đã có bản triển khai và benchmark ban đầu của Direction A tại [src/v1](Implementation/Direction%20A/src/v1/README.md).

### Đã hoàn thành

| Hạng mục | Trạng thái |
| --- | --- |
| Mô hình bài toán Direction A | Đã đặc tả giả thiết, biến, ba mục tiêu, ràng buộc, giao thức đánh giá và chi phí từng nút. |
| Mô phỏng mạng | 6 client, 2 UAV hover; uplink, downlink, backhaul, tổng hợp, bandwidth/CPU, deadline và pin. |
| FL engine | Fashion-MNIST, CNN 105866 tham số, local SGD và tổng hợp phân cấp có trọng số; có cache update/loss. |
| Thuật toán | Đã triển khai NSGA-II và MOEA/D dùng chung evaluator, bộ sinh ứng viên và mô hình tài nguyên. |
| Search và audit | Tách dữ liệu/RNG; lựa chọn lịch trước khi mở audit/test; lưu kết quả thô và biểu đồ. |
| Historical guidance | Có code và kiểm thử; tắt trong so sánh chính để tập trung so sánh hai optimizer. |
| Kiểm thử | 14 kiểm thử đạt; đã rà ledger/timeline/mean loss của 130073 candidate records. |
| Direction B và C | Đang ở mức định hướng trong draft; các thư mục triển khai còn trống. |

### Phạm vi tối ưu và số vòng FL

**Mỗi lần gọi NSGA-II/MOEA/D hiện chỉ tối ưu cho một vòng FL**, tại checkpoint và trạng thái mạng hiện tại. Ba mục tiêu là validation loss sau vòng đó, năng lượng của vòng và thời gian hoàn thành vòng.

Runner hỗ trợ nhiều vòng liên tiếp: tối ưu vòng hiện tại → chọn một lịch → thực thi local SGD và tổng hợp → cập nhật model, pin, đồng hồ, history → chuyển sang vòng tiếp theo. Optimizer chưa nhìn trước các vòng sau để tối ưu trực tiếp loss cuối cùng và tổng chi phí toàn quá trình.

| Cấu hình đã chạy | Phạm vi |
| --- | --- |
| So sánh chính theo thời gian | 5 seed × 2 thuật toán = 10 lần chạy; **1 vòng FL/lần chạy**, trần search 15 giây. |
| So sánh bổ sung theo proposals | 5 seed × 2 thuật toán = 10 lần chạy; **1 vòng FL/lần chạy**, 10000 proposals, trần 30 giây. |
| Kiểm tra tích hợp nhiều vòng | Mỗi thuật toán chạy một episode **3 vòng FL**; tổng cộng 6 vòng, guidance probability=0.5. |
| Mặc định CLI | 1 vòng FL; thay đổi bằng tham số --rounds. |

Trong pilot chính, mỗi client được chọn thực hiện **5 bước SGD cục bộ trong một vòng FL**. 5 seed là các lần chạy độc lập; số bước local SGD và số seed không phải số vòng FL.

### Kết quả ban đầu và giới hạn

Với cùng trần 15 giây tìm kiếm, audited hypervolume trung bình qua 5 seed:

| Thuật toán | Audited HV trung bình |
| --- | ---: |
| NSGA-II | 0.28779859 |
| MOEA/D | 0.28780684 |

Hai kết quả rất gần nhau; chưa đủ bằng chứng để kết luận thuật toán nào tốt hơn nói chung. Chi tiết từng seed, thống kê ghép cặp, thời gian thực và overrun nằm trong [report.md](Implementation/Direction%20A/src/v1/report.md).

**Số client được phép chọn là từ 1 đến 4 mỗi vòng. Tuy nhiên, các lịch cuối được chọn trong các thí nghiệm hiện tại đều chỉ có 1 client**, bao gồm cả ca kiểm tra 3 vòng. Đây là kết quả lựa chọn dưới hàm mục tiêu, scale và preference hiện tại, không phải code cố định số client bằng 1.

Checkpoint ban đầu là model ngẫu nhiên; local SGD ngắn nên lợi ích learning của việc thêm client còn nhỏ, trong khi thời gian và năng lượng hover/baseline có ảnh hưởng lớn. Các kết quả này kiểm tra pipeline và optimizer; chưa thể hiện rõ lợi ích học cộng tác nhiều client hoặc hội tụ FL dài hạn.

Các giới hạn khác của v1:

- UAV hover, kênh effective-rate xác định; chưa có dynamic channel, mất gói hoặc tối ưu quỹ đạo.
- Các hệ số phần cứng là scalar chung cho nhóm nút; chưa hỗ trợ đầy đủ phần cứng dị biệt từng client.
- Cycles/power/energy là tham số mô phỏng tổng hợp, chưa phải số đo trên thiết bị/UAV thật.
- Chưa đánh giá đóng góp set-aware trong một benchmark chính; ca nhiều vòng hiện chỉ là kiểm tra tích hợp.
- Chưa triển khai multi-fidelity evaluation và adaptive probing.

### Tài liệu triển khai và chạy lại

- [Đặc tả bài toán](Implementation/Direction%20A/src/v1/problem-formulation.md).
- [Hướng dẫn v1](Implementation/Direction%20A/src/v1/README.md).
- [Báo cáo so sánh](Implementation/Direction%20A/src/v1/report.md).
- [Kết quả cùng trần thời gian](Implementation/Direction%20A/src/v1/results/equal_time/summary.csv).
- [Kết quả 10000 proposals](Implementation/Direction%20A/src/v1/results/pilot/summary.csv).
- [Kiểm tra 3 vòng](Implementation/Direction%20A/src/v1/results/episode_smoke/summary.csv).

Từ thư mục gốc project, chạy trong PowerShell:

~~~powershell
Set-Location "Implementation/Direction A/src/v1"
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --config configs/equal_time.json --seeds 101 102 103 104 105 --output results/my_equal_time --download
~~~

Ví dụ chạy 20 vòng liên tiếp với một seed:

~~~powershell
python run.py --config configs/pilot.json --seeds 101 --rounds 20 --output results/fl20
~~~

Lệnh nhiều vòng vẫn lặp bộ tối ưu một vòng. Đây là cấu hình chạy tiếp, chưa phải thí nghiệm 20 vòng đã được báo cáo; khả năng hoàn thành còn phụ thuộc các ràng buộc pin/deadline.

### Ưu tiên tiếp theo

1. Chạy đủ nhiều vòng FL và theo dõi loss/accuracy theo thời gian, tổng năng lượng, thời gian đến chất lượng mục tiêu và mức pin còn lại.
2. Rà lại normalization, preference và ảnh hưởng hover để giải thích xu hướng chọn một client; đo tác động của việc chọn nhiều client lên chất lượng học.
3. Đánh giá tại các checkpoint đã học, với dữ liệu/thiết bị dị biệt và quy mô mạng lớn hơn.
4. So sánh generic với set-aware mutation trong cùng điều kiện thông tin, tài nguyên và ngân sách.
5. Sau khi Direction A ổn định, profiling chi phí evaluator để quyết định triển khai Direction B; tiếp tục Direction C khi đã chốt mô hình quan sát và chi phí probing.

Tối ưu tốt từng vòng chưa bảo đảm tối ưu toàn bộ quá trình FL. Tính mới và hiệu quả nghiên cứu cần tiếp tục được kiểm chứng qua các thí nghiệm trên.

