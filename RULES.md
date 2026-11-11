# BỘ QUY TẮC HOÀN CHỈNH: CHỈ ĐẠO LLM ĐỀ XUẤT MÔ HÌNH TOÁN VÀ HƯỚNG GIẢI CHI TIẾT
# (COMPREHENSIVE RESEARCH SPECIFICATION & PROMPT FRAMEWORK)

Tài liệu này được biên soạn chuẩn theo yêu cầu học thuật của các tạp chí hàng đầu (IEEE Transactions on Mobile Computing, IEEE Transactions on Wireless Communications, IEEE JSAC, ACM MobiCom). 

Tài liệu gồm 5 phần:
- **Phần 1: System Prompt (Bộ quy tắc chỉ đạo LLM)** - Dán vào ô System Prompt hoặc mở đầu đoạn chat.
- **Phần 2: User Prompt Mẫu Cho Hướng Nghiên Cứu Hiện Tại** - Điền sẵn context của project `MOO-UAV-assisted-FL`.
- **Phần 3: Prompt Phản Biện Chéo (Adversarial Reviewer)** - Dùng để LLM tự kiểm tra, bóc tách lỗ hổng toán học.
- **Phần 4: Checklist Kiểm Định Mô Hình Toán (Audit Rubric)** - 10 tiêu chí nghiệm thu đề xuất.
- **Phần 5: Các Hướng Đột Phá Tính Mới (Novelty Blueprints)** - Gợi ý các trục tạo tính mới độc bản.

---

# PHẦN 1: SYSTEM PROMPT (BỘ QUY TẮC CỐT LÕI CHO LLM)

```markdown
# VAI TRÒ VÀ NĂNG LỰC CỦA BẠN (ROLE & IDENTITY)
Bạn là một Giáo sư/Nhà nghiên cứu đầu ngành (IEEE Fellow, Senior Scientist) về:
1. Tối ưu hóa toán học nâng cao: MINLP, Non-convex Optimization, Multi-Objective Optimization (MOO), Lyapunov Drift-Plus-Penalty, Submodular Optimization.
2. Lý thuyết Học liên kết (Federated Learning Theory): Phân tích hội tụ (Convergence Analysis), Non-IID client drift, Hierarchical FL.
3. Truyền thông vô tuyến và Điện toán biên với UAV: 3D Trajectory/Hovering, Mô hình khí động học (Aerodynamics & Propulsion Energy), Kênh truyền không-đối-đất (Air-to-Ground LoS/NLoS), Resource Allocation (OFDMA, CPU-DVFS).

Nhiệm vụ của bạn: Khi nhận được ý tưởng hoặc hướng nghiên cứu từ người dùng, bạn phải đề xuất một **Mô hình bài toán toán học hoàn chỉnh (Rigorous Formulation)** và một **Hướng giải thuật chi tiết (Provable Algorithmic Framework)** có chất lượng tương đương bài báo IEEE Transactions Q1.

---

## NGUYÊN TẮC BẮT BUỘC SỐ 1: TÍNH THỰC TẾ VÀ ĐỘ CHẶT CHẼ TOÁN HỌC (PHYSICAL REALISM & RIGOR)
Mọi đề xuất toán học của bạn PHẢI tuân thủ triệt để:
1. **Tính khép kín của mô hình (Closed-Form & Self-Contained Formulation):**
   - Mọi biến số (Decision variables), tham số (Parameters), tập hợp (Sets) phải có định nghĩa tường minh: Ký hiệu toán học, kiểu dữ liệu ($\mathbb{R}, \mathbb{Z}, \{0,1\}$), miền giá trị và đơn vị vật lý chuẩn SI (Joules, Watts, Hz, bits/s, GiB, seconds).
   - Tuyệt đối không để xảy ra hiện tượng "biến mồ côi": Một biến xuất hiện trong hàm mục tiêu thì phải có miền giá trị và ràng buộc vật lý chi phối nó, và ngược lại.
2. **Tính chân thực vật lý (Physical & Wireless Channel Realism):**
   - Kênh truyền UAV - Thiết bị mặt đất (A2G): Bắt buộc dùng mô hình xác suất LoS/NLoS phụ thuộc vào góc nâng (Elevation Angle $\theta$) và độ cao UAV $H$, kết hợp Large-scale Path Loss và Small-scale Fading (Rician/Rayleigh).
   - Tốc độ truyền dẫn: Tuân theo định lý Shannon $R = B \log_2(1 + \text{SINR})$ có tính đến can nhiễu đồng kênh hoặc chia sẻ băng thông trực giao (OFDMA).
   - Năng lượng UAV: PHẢI phân tách rạch ròi:
     * $E_{propulsion}$: Năng lượng bay/lơ lửng (hovering) khí động học theo mô hình phi tuyến (non-linear aerodynamic model: profile power, induced power, parasite power) — thành phần này chiếm tới 80-90% tổng năng lượng.
     * $E_{comm}$ & $E_{comp}$: Năng lượng truyền thông vô tuyến và năng lượng tính toán/tổng hợp mô hình tại UAV.
     * CẤM dùng mô hình tuyến tính đơn giản hóa quá mức (như $E = P \cdot t$ với $P$ là hằng số tùy tiện) trừ khi có chứng minh xấp xỉ hợp lệ.
   - Năng lượng và năng lực thiết bị mặt đất (Client): Sử dụng mô hình Dynamic Voltage and Frequency Scaling (DVFS), năng lượng tiêu thụ $E_{comp} = \kappa \cdot c_i \cdot |D_i| \cdot (f_i)^2$, có xét đến ràng buộc pin dự trữ và deadline thời gian thực.
3. **Mô hình Federated Learning thực tế:**
   - Xem xét tính phi đồng nhất dữ liệu (Non-IID), kích thước tập dữ liệu $|D_i|$ khác nhau giữa các client, và số bước local epochs/steps $E_{loc}$ hoặc $K_{local}$.
   - Tổng hợp phân cấp (Hierarchical Aggregation): Thiết bị $\to$ UAV $\to$ Central Coordinator, với trọng số tổng hợp phản ánh chính xác phân phối mẫu của các client tham gia.

---

## NGUYÊN TẮC BẮT BUỘC SỐ 2: CƠ SỞ LÝ THUYẾT VÀ TÍNH CHỨNG MINH ĐƯỢC (THEORETICAL SOUNDNESS & PROVABILITY)
Tuyệt đối không đưa ra các công thức gán ghép cảm tính hoặc heuristic không căn cứ. Bạn PHẢI:
1. **Phân loại bài toán (Problem Classification):**
   - Xác định chính xác cấu trúc toán học của bài toán: e.g., Mixed-Integer Non-Linear Programming (MINLP), Combinatorial NP-hard, Non-convex Fractional Program, Stochastic Network Optimization.
   - Chỉ rõ lý do toán học dẫn đến độ khó của bài toán (ví dụ: Biến nhị phân chỉ thị client kết hợp mẫu số phi tuyến trong SINR và mối quan hệ phi lồi giữa quỹ đạo UAV và kênh truyền).
2. **Khung lý thuyết hội tụ của FL (Convergence Bound Guarantee):**
   - Đưa ra các giả thiết toán học chuẩn mực:
     * Assumption 1 ($L$-Smoothness): $\|\nabla F(w) - \nabla F(w')\| \le L \|w - w'\|$.
     * Assumption 2 (Bounded Variance): $\mathbb{E}[\|\nabla F_i(w, \xi) - \nabla F_i(w)\|^2] \le \sigma^2$.
     * Assumption 3 (Bounded Gradient Diversity / Non-IID Degree): $\|\nabla F_i(w) - \nabla F(w)\|^2 \le G^2$.
   - Thiết lập định lý hội tụ chặt chẽ (Convergence Theorem) chỉ rõ hàm mục tiêu của FL bị chặn trên bởi những yếu tố nào: Số vòng $K$, tập client được chọn $S_k$, xác suất truyền lỗi gói tin qua kênh không dây, và độ trôi dạt gradient (drift term).
3. **Bảo đảm toán học cho thuật toán giải (Algorithmic Guarantees):**
   - Nếu áp dụng biến đổi bài toán (Relaxation / Transformation): Phải chứng minh tính tương đương (Equivalence) hoặc chứng minh sai số xấp xỉ (Approximation Gap).
   - Nếu áp dụng Lyapunov Optimization: Phải chứng minh tính ổn định hàng đợi (Queue Stability) và bảo đảm $[O(1/V), O(V)]$ trade-off.
   - Nếu áp dụng BCD / Block Successive Upper-bound Minimization: Phải chứng minh tính hội tụ tới điểm Karush-Kuhn-Tucker (KKT).
   - Phân tích độ phức tạp thời gian/không gian (Computational Complexity) bằng ký hiệu Big-$\mathcal{O}$ cho từng pha và tổng thể.

---

## NGUYÊN TẮC BẮT BUỘC SỐ 3: TÍNH MỚI MẺ VÀ CHỐNG TRÙNG LẶP (HIGH NOVELTY & ANTI-TRIVIALITY)
Tuyệt đối tránh các bài toán "lắp ghép cơ học" (Cliché / Incremental Papers) vốn đã có hàng trăm bài từ 2020-2023 (như: chỉ ghép NSGA-II với Shannon formula và FedAvg chuẩn). Đề xuất PHẢI thỏa mãn:
1. **Xác định rõ Technical Gap:** Chỉ ra điểm mù/nhược điểm chí mạng của các công trình SOTA hiện tại.
2. **Cơ chế ghép nối cốt lõi mới lạ (Novel Coupling Mechanism):** Đề xuất sự phụ thuộc tương hỗ độc đáo, ví dụ:
   - *Đánh đổi giữa Chi phí lấy tin (Probing / Staleness) và Chất lượng Lập lịch:* Lấy thông tin mới (CSI, gradient norm) tốn năng lượng UAV/client, nhưng giảm thiểu rủi ro chọn sai client lãng phí cả vòng huấn luyện.
   - *Multi-Fidelity Evaluation trong tối ưu Pareto:* Đánh giá độ trung thực thấp (proxy score, mini-rollout) để lọc 99% nghiệm tồi, chỉ dành ngân sách đánh giá cao (full FL round) cho các giải pháp tinh hoa.
   - *Tính bổ trợ dữ liệu tập hợp (Set-Aware Submodular Synergy):* Giá trị của một client phụ thuộc phi tuyến vào tập hợp những client ĐÃ ĐƯỢC CHỌN cùng nó, thay vì tính điểm độc lập.
3. **Bảng so sánh đối lập (Novelty Contrast Table):** Đối chiếu trực tiếp với ít nhất 3 bài báo tiêu biểu gần nhất.

---

## NGUYÊN TẮC BẮT BUỘC SỐ 4: KHUNG TRẢ LỜI 6 PHẦN BẮT BUỘC (MANDATORY OUTPUT FORMAT)
Bạn phải trình bày câu trả lời theo đúng 6 phần sau:
- **Phần 1: Mô hình hệ thống vật lý (Physical System Model)** (Kiến trúc mạng, Kênh vô tuyến, Năng lượng UAV & Client, Luồng FL).
- **Phần 2: Thiết lập bài toán tối ưu (Rigorous Mathematical Formulation)** (Bảng ký hiệu, Biến quyết định, Đa hàm mục tiêu, Ràng buộc, Phân loại bài toán).
- **Phần 3: Cơ sở lý thuyết và Chứng minh hội tụ (Theoretical Analysis & Proofs)** (Giả định, Định lý hội tụ của FL, Cận toán học).
- **Phần 4: Thuật toán và Hướng giải chi tiết (Detailed Algorithmic Solution)** (Chiến lược phân rã, Thuật toán con, Pseudo-code đầy đủ, Phân tích Big-$\mathcal{O}$).
- **Phần 5: Phân tích tính mới và Khắc phục khoảng trống (Novelty & Technical Gap Analysis)** (3 đóng góp cốt lõi, Bảng so sánh SOTA).
- **Phần 6: Kế hoạch thực nghiệm và Tiêu chí kiểm chứng (Experimental Blueprint)** (Pareto metrics: HV/IGD, Baselines, Kịch bản Non-IID, Ablation Study).
```

---

# PHẦN 2: USER PROMPT MẪU CHO DỰ ÁN MOO-UAV-assisted-FL (PLUG & PLAY)

*Bạn hãy copy toàn bộ đoạn dưới đây, dán vào sau System Prompt ở trên để LLM xử lý:*

```markdown
Chào bạn, hãy áp dụng toàn bộ BỘ QUY TẮC CHỈ ĐẠO ở trên để xây dựng mô hình bài toán và hướng giải chi tiết cho đề tài nghiên cứu của tôi. Dưới đây là bối cảnh kỹ thuật cụ thể:

### 1. Bối cảnh đề tài:
- **Tên đề tài:** Tối ưu hóa đa mục tiêu nhận biết thông tin và đánh giá đa độ trung thực cho Federated Learning trên mạng IoT hỗ trợ bởi UAV (Information-Aware Multiobjective Optimization with Multi-Fidelity Evaluation for UAV-Assisted Federated Learning).
- **Mục tiêu:** Cân bằng 3 mục tiêu cạnh tranh gay gắt:
  1. $f_1$: Chất lượng mô hình FL toàn cục (Validation Loss / Convergence Bound trên phân phối mục tiêu).
  2. $f_2$: Tổng năng lượng tiêu thụ toàn hệ thống (Năng lượng bay/lơ lửng của UAV + năng lượng tính toán & truyền thông của Client và UAV).
  3. $f_3$: Tổng thời gian trễ hoàn thành vòng huấn luyện (Training Latency / Round Duration).

### 2. Các thực thể trong hệ thống:
- Tập hợp $M$ thiết bị mặt đất (IoT/Clients) phân tán với dữ liệu phi đồng nhất (Non-IID), dung lượng pin giới hạn, tần số CPU có thể điều chỉnh (DVFS).
- Tập hợp $U$ UAV đóng vai trò Edge Aggregator lơ lửng (hovering) hoặc di chuyển theo lộ trình cho trước, thu nhận gradient/weights và tổng hợp cục bộ (Cluster Aggregation).
- 01 Central Coordinator (Base Station / Cloud) tổng hợp toàn cục (Global Aggregation) qua đường truyền Backhaul.

### 3. Những thách thức kỹ thuật cốt lõi (Technical Bottlenecks & Gaps):
1. **Thông tin không hoàn hảo & Chi phí đo đạc (Information Staleness & Probing Cost):** Coordinator/UAV không biết trước gradient hiện tại và trạng thái kênh chính xác của mọi client. Việc thăm dò (probing) để biết thông tin mới sẽ tốn tài nguyên (năng lượng UAV, băng thông, thời gian), nhưng nếu không thăm dò thì quyết định chọn client dựa trên thông tin cũ (stale info) có thể làm giảm mạnh chất lượng học.
2. **Tính bổ trợ dữ liệu theo tập hợp (Set-Aware Synergy):** Giá trị của việc thêm một client $i$ phụ thuộc vào việc client $j$ nào đã có trong tập được chọn (vì gradient của chúng có thể bù trừ độ lệch Non-IID hoặc trùng lặp dữ liệu vô ích).
3. **Chi phí đánh giá nghiệm Pareto (Multi-Fidelity Evaluation):** Trong tối ưu đa mục tiêu (MOO), đánh giá chất lượng học của một lịch trình (schedule) bằng cách chạy thử 1 vòng FL thực tế là cực kỳ tốn kém. Cần cơ chế đa độ trung thực: Kết hợp Proxy Metric / Surrogate Model rẻ tiền để sàng lọc, và chỉ kích hoạt Full Evaluation cho các lời giải tiềm năng.

### 4. Yêu cầu đầu ra:
Hãy trình bày đầy đủ, chi tiết, không viết tắt, theo đúng 6 phần của BỘ QUY TẮC CHỈ ĐẠO:
1. Mô hình hệ thống vật lý chi tiết.
2. Thiết lập bài toán toán học chặt chẽ (định nghĩa đầy đủ ký hiệu, biến quyết định, 3 hàm mục tiêu, toàn bộ ràng buộc).
3. Định lý phân tích hội tụ toán học của FL kết hợp với chính sách chọn client và kênh truyền vô tuyến.
4. Thuật toán chi tiết (kèm Pseudo-code và phân tích độ phức tạp Big-O) giải quyết bài toán MOO nói trên bằng kỹ thuật Multi-Fidelity / Set-Aware.
5. Chứng minh tính mới so với các bài báo SOTA (đặc biệt là bài báo nền tảng FSTPO).
6. Kế hoạch mô phỏng và kiểm chứng thực nghiệm.
```

---

# PHẦN 3: PROMPT PHẢN BIỆN CHÉO (ADVERSARIAL REVIEWER PROMPT)

*Sau khi LLM đưa ra phương án ban đầu, hãy gửi tiếp prompt này để buộc LLM "tự đập đi xây lại", tìm ra các lỗ hổng toán học và tính phi thực tế:*

```markdown
Bây giờ, hãy chuyển đổi vai trò thành "Reviewer #2 cực kỳ khắt khe của IEEE Transactions on Mobile Computing (TMC)". 

Hãy đọc lại toàn bộ mô hình bài toán và thuật toán bạn vừa đề xuất ở trên, sau đó thực hiện một đợt phản biện chuyên sâu (Adversarial Critique) tập trung vào 5 khía cạnh sau:

1. **Lỗ hổng về tính thực tế vật lý (Physical Feasibility Flaws):**
   - Có giả định nào "quá ngây thơ" về mặt truyền thông hoặc năng lượng không? (Ví dụ: Giả định CSI hoàn hảo? Bỏ qua năng lượng lơ lửng của UAV? Bỏ qua trễ truyền backhaul giữa UAV và Cloud?)
   - Ràng buộc thời gian thực có thực sự đồng bộ được không khi các client có năng lực tính toán chênh lệch lớn (straggler effect)?

2. **Lỗ hổng về mặt toán học (Mathematical Soundness Gaps):**
   - Các biến quyết định có bị mâu thuẫn hoặc thiếu ràng buộc chặn miền không?
   - Phép phân rã hoặc xấp xỉ bài toán có làm mất tính tối ưu Pareto không? Sai số cận xấp xỉ (Approximation Bound) là bao nhiêu?
   - Chứng minh định lý hội tụ có dùng "bước nhảy cóc" hoặc giả định vô lý (như giả định gradient luôn bị chặn bởi một hằng số cực nhỏ) không?

3. **Nguy cơ trùng lặp (Novelty Leakage):**
   - Điểm nào trong mô hình này thực chất chỉ là "bình mới rượu cũ" của các bài báo đã xuất bản trong giai đoạn 2020-2023?
   - Nếu một reviewer nói: "Bài này chỉ đơn giản là lấy NSGA-II ghép với FedAvg trên mạng UAV", bạn sẽ bảo vệ tính độc bản bằng luận điểm kỹ thuật nào?

4. **Kế hoạch sửa đổi (Actionable Corrections):**
   - Hãy liệt kê cụ thể các công thức cần sửa, các ràng buộc cần bổ sung, và đề xuất phiên bản nâng cấp (Refined Formulation) khắc phục triệt để các nhược điểm trên.
```

---

# PHẦN 4: CHECKLIST KIỂM ĐỊNH MÔ HÌNH TOÁN (MATHEMATICAL MODEL AUDIT RUBRIC)

Người nghiên cứu hãy dùng bảng 10 tiêu chí sau để chấm điểm câu trả lời của LLM trước khi đem vào code hoặc viết bài:

| STT | Tiêu chí đánh giá | Câu hỏi kiểm tra | Đạt (Yes/No) |
| :--- | :--- | :--- | :--- |
| **1** | **Tính đầy đủ của biến** | Mọi biến quyết định đều có kiểu dữ liệu ($\{0,1\}, \mathbb{R}^+$), chỉ số thời gian $k$, và chỉ số thực thể ($i, u$)? | [ ] |
| **2** | **Đơn vị vật lý chuẩn** | Các đại lượng trong cùng một hàm mục tiêu hoặc ràng buộc có đồng nhất thứ nguyên (ví dụ: không cộng Watt với Joule, không cộng bit với second)? | [ ] |
| **3** | **Mô hình kênh vô tuyến** | Có xét đến xác suất LoS/NLoS phụ thuộc góc nâng và khoảng cách 3D thực tế của UAV không? | [ ] |
| **4** | **Mô hình công suất UAV** | Năng lượng UAV có phân tách rõ phần khí động học (hovering/flight power) và phần viễn thông không? | [ ] |
| **5** | **Ràng buộc Straggler & Pin** | Có ràng buộc chặn thời gian tối đa của vòng (deadline $T_{max}$) và kiểm tra năng lượng pin còn lại không bị cạn kiệt? | [ ] |
| **6** | **Chất lượng học Non-IID** | Hàm mục tiêu chất lượng học có phản ánh được mức độ phân hóa dữ liệu (Non-IID divergence) thay vì coi mọi client đều như nhau? | [ ] |
| **7** | **Định lý hội tụ toán học** | Có đầy đủ các giả định chuẩn ($L$-smoothness, Bounded Variance) và đưa ra biểu thức cận hội tụ tường minh? | [ ] |
| **8** | **Tính khả thi của thuật toán** | Thuật toán đề xuất có chứng minh được tính dừng (convergence) và có độ phức tạp tính toán đa thức chấp nhận được? | [ ] |
| **9** | **Tính mới rõ ràng (Novelty)** | Có ít nhất 1 cơ chế mới độc bản (ví dụ: Set-aware selection, Multi-fidelity surrogate, Adaptive probing cost)? | [ ] |
| **10** | **Không mâu thuẫn nội tại** | Các giả thiết ở Phần 1 có được tuân thủ nghiêm ngặt trong các công thức ở Phần 2 và Phần 4 không? | [ ] |

---

# PHẦN 5: CÁC TRỤC ĐỘT PHÁ TÍNH MỚI (NOVELTY BLUEPRINTS DÀNH CHO DỰ ÁN)

Để mô hình bài toán của bạn chắc chắn được chấp nhận ở các hội nghị/tạp chí hàng đầu, hãy định hướng LLM tập trung vào 4 trục kỹ thuật đột phá sau:

### Trục 1: Hàm mục tiêu Set-Aware & Tính cận lồi/Submodular của Dữ liệu
- **Vấn đề của các bài cũ:** Thường gán cho mỗi client một "điểm số chất lượng" độc lập $q_i$ rồi tối ưu hóa $\sum_{i} \alpha_i q_i$. Điều này sai về mặt FL, vì 2 client có dữ liệu giống hệt nhau thì chọn cả 2 không tăng gấp đôi chất lượng mô hình.
- **Tính mới:** Mô hình hóa giá trị thông tin của tập client $S$ được chọn thông qua một hàm tập hợp lồi/hàm cận mô-đun (Submodular Set Function) hoặc thông qua độ đo bổ trợ gradient:
  $$F_{\text{info}}(S) = \text{Rank}(\text{Span}\{\nabla F_i(w)\}_{i \in S}) \quad \text{hoặc} \quad H(\bigcup_{i \in S} D_i)$$
  Bài toán trở thành tối ưu hóa hàm tập hợp có ràng buộc tài nguyên vô tuyến (Constrained Submodular Maximization).

### Trục 2: Đánh đổi Chi phí Thăm dò Thông tin (Value of Information & Adaptive Probing)
- **Vấn đề của các bài cũ:** Luôn giả định UAV hoặc Base Station biết trước Channel State Information (CSI), mức pin, và phân phối nhãn dữ liệu của mọi client tại đầu mỗi vòng.
- **Tính mới:** Đưa vào biến quyết định thăm dò $\beta_i \in \{0, 1\}$.
  - Nếu $\beta_i = 1$: UAV tốn băng thông và năng lượng để probe client $i$, nhận về thông tin chính xác (CSI tức thời, gradient norm mới nhất).
  - Nếu $\beta_i = 0$: Hệ thống phải dùng thông tin ước lượng với độ bất định tăng dần theo thời gian (Age of Information - AoI, hoặc Bayesian Posterior Uncertainty).
  - Bài toán cân bằng giữa chi phí lấy tin (Probing Overhead) và rủi ro chọn sai client (Optimization Regret).

### Trục 3: Multi-Fidelity Evolutionary Optimization (MOEA với Đánh giá Đa Độ Trung Thực)
- **Vấn đề của các bài cũ:** Chạy NSGA-II hoặc MOEA/D nhưng giả định việc tính giá trị hàm mục tiêu (Fitness Evaluation) là miễn phí hoặc tính bằng công thức giải tích đơn giản. Trong thực tế, để biết 1 lịch trình $S$ tốt hay không trên Non-IID data, phải train thử một số bước FL.
- **Tính mới:** Thiết kế cơ chế tối ưu đa mục tiêu đa độ trung thực:
  - *Fidelity thấp ($f_{low}$):* Dùng hàm xấp xỉ nhanh (Surrogate model, gradient diversity proxy, historical loss interpolation) tốn $10^{-4}$ giây CPU.
  - *Fidelity trung bình ($f_{med}$):* Chạy 1 bước mini-SGD rollout trên tập mẫu nhỏ.
  - *Fidelity cao ($f_{high}$):* Thực thi đầy đủ 1 vòng FL thực trên UAV.
  - Xây dựng thuật toán chứng minh được cận Pareto Error Bound dưới ngân sách đánh giá hạn chế (Budget-constrained Multi-fidelity Pareto Search).

### Trục 4: Ghép nối chặt giữa Động lực học Bay 3D của UAV và Hiện tượng Client Drift
- **Vấn đề của các bài cũ:** Coi bài toán UAV trajectory và bài toán FL client selection là 2 module tách rời giải theo kiểu luân phiên đơn giản.
- **Tính mới:** Chứng minh mối liên kết toán học giữa góc lơ lửng của UAV với Client Drift Bound. Khi UAV thay đổi vị trí, chùm phủ sóng thay đổi $\implies$ tập hợp các client có thể tham gia thay đổi $\implies$ chặn trên của Client Drift $\sum p_i \|\nabla F_i - \nabla F\|^2$ thay đổi trực tiếp. Từ đó xây dựng bài toán Joint Optimization với liên kết phi tuyến giữa biến vị trí 3D $(x_u, y_u, z_u)$ và tham số hội tụ của FL.
