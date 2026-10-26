# Research Review: Hoàn thiện cơ sở lý thuyết và định hướng triển khai Direction A

**Research draft:** *Information-Aware Multiobjective Evolutionary Optimization with Multi-Fidelity Evaluation for UAV-Assisted Federated Learning* (JNCA research working draft)  
**Phạm vi:** Direction A — Set-aware Multiobjective Evolutionary Optimization  
**Ngày báo cáo:** 26/10/2026  
**Ngôn ngữ:** Tiếng Việt

> **Lưu ý về nguồn:** Các nhận định về phương trình, mô hình và thuật toán của JNCA được trình bày dựa trên research working draft mà người dùng cung cấp. Những đề xuất sửa đổi mô hình, định lý suy ra, thiết kế thực nghiệm và cách định vị novelty là **phân tích/khuyến nghị**, không phải nội dung đã được chứng minh trong draft. Các nghiên cứu liên quan được liệt kê kèm liên kết để đối chiếu trực tiếp bản gốc trước khi trích dẫn trong bài báo.

---

## 1. Đánh giá tổng quan

Direction A có cơ sở nghiên cứu hợp lý và có thể triển khai thành thuật toán thực nghiệm. Tuy nhiên, **chưa nên xem mô hình toán và phương pháp hiện tại là hoàn chỉnh**.

Ba câu hỏi nền tảng quan trọng nhất:

1. **Learning contribution:** Làm thế nào xác định một tập client có tính bổ trợ và hữu ích cho global learning, thay vì chỉ có gradient đa dạng?
2. **Optimization consistency:** Làm thế nào bảo đảm validation loss, energy và training time được đánh giá nhất quán cho cùng một schedule?
3. **Information availability:** Thuật toán biết thông tin gì khi tạo và đánh giá candidate schedules?

Đặc biệt, Direction A là **reference-evaluated scheduler**, được thiết kế và đánh giá trong môi trường simulator. Điều này chưa đồng nghĩa với một online controller có thể triển khai trực tiếp. Cần giữ ranh giới offline evaluation và implementable online decisions rõ ràng.

### 1.1. Bảng tổng hợp khoảng trống lý thuyết

| Mức độ | Vấn đề | Hướng xử lý |
|---|---|---|
| Nghiêm trọng | Định nghĩa/tính learning objective của candidate | Chốt trước khi code optimizer |
| Nghiêm trọng | Oracle evaluation so với thông tin đầu vào scheduler | Tránh information leakage |
| Nghiêm trọng | Định nghĩa set-aware operator | Bổ sung đầy đủ cách tạo, đánh giá và chọn swap |
| Quan trọng | UAV mobility, channel, backhaul, flight energy | Chốt mô hình vật lý và tham số |
| Quan trọng | Feasibility, constraint handling, resource decoding | Định nghĩa quy trình thống nhất |
| Quan trọng | Quan hệ giữa gradient proxy và learning performance | Bổ sung lập luận lý thuyết, đánh giá thực nghiệm |
| Quan trọng | Stochastic evaluation, Pareto comparison | Đồng nhất snapshot, seed, evaluation protocol |
| Hoàn thiện | Benchmark, baselines, ablations, novelty | Thiết kế đối chứng có khả năng cô lập đóng góp |

**Cảnh báo về novelty:** Gradient-aware client selection, set-based selection và phối hợp lựa chọn client với tài nguyên không dây đã được nghiên cứu trước đây. Chỉ bổ sung một heuristic swap vào NSGA-II chưa tự động tạo ra đóng góp thuật toán mới.

---

## 2. Hoàn thiện bài toán tối ưu Direction A

### 2.1. Phân biệt full-horizon objective và round-level objective

**Bài toán full horizon** trong Section 4.2 của draft:

$$
\min_{\pi^P,\pi^T}\mathbf J(\pi)
=\left(
\mathbb E[L_{\mathrm{val}}(w_K)],
\mathbb E\left[\sum_{k=0}^{K-1}E_k\right],
\mathbb E\left[\sum_{k=0}^{K-1}T_k\right]
\right).
$$

Nhưng **Direction A** ở Section 4.3 giải bài toán tại một snapshot/FL round:

$$
\min_{x\in\mathcal X(S_k)}\mathbf j_k(x)
=\left(
\mathbb E[L_{\mathrm{val}}(w_{k+1}(x))\mid S_k],
E_k(x),T_k(x)
\right),\quad x=(s,b^T,f^T).
\tag{29}
$$

Đây là một **single-round, single-fidelity, mixed-variable multiobjective optimization problem**. Nó không tự động tối ưu tốt objective full horizon vì một round có thể ảnh hưởng đến global model, battery và network state của các round sau.

| Thành phần | Phạm vi Direction A |
|---|---|
| Quyết định | Client selection, UAV association, bandwidth, CPU frequency |
| Thời gian tối ưu | Một FL round |
| Objective học tập | Validation loss sau một round |
| Physical objectives | Energy, elapsed time |
| Phương pháp | Evolutionary multiobjective optimization |
| Evaluation | Full reference evaluator |
| UAV trajectory optimization | Không |
| Physical probing | Không cần cho bản cơ sở |
| Surrogate/multi-fidelity | Không dùng ở Direction A |

**Khuyến nghị:** Triển khai single-round trước; sau khi evaluator chính xác mới chạy complete FL episodes để đánh giá tác động dài hạn.

### 2.2. Input, output, feasible set

**Input tại round $k$:** global checkpoint $w_k$; topology snapshot; hardware limits; battery states; channel gains; FL protocol settings; available client information. Simulator có thể giữ local datasets và validation data để reference-evaluate, nhưng controller không mặc nhiên được đọc các trường ẩn này.

**Biến quyết định:**

$$x_k=(s_{m,u},b_{m,u},f_m).$$

**Output:** Tập feasible nondominated schedules, các objective values và một schedule được chọn để thực thi theo preference rule khai báo trước.

**Ràng buộc:**

Client–UAV assignment:

$$
 s_{m,u}\in\{0,1\},\qquad \sum_{u=1}^{U}s_{m,u}\le1.
$$

Số client được chọn:

$$
1\le\sum_m\sum_us_{m,u}\le N_{\max}.
$$

Bandwidth:

$$
\sum_m b_{m,u}\le B_u,\qquad 0\le b_{m,u}\le B_us_{m,u}.
$$

Một active link phải được phân bandwidth dương; không được dùng tốc độ upload với $b=0$.

CPU:

$$
f_m^{\min}s_m\le f_m\le f_m^{\max}s_m,\quad s_m=\sum_us_{m,u}.
$$

Liên kết khả dụng:

$$s_{m,u}\le e_{m,u}^k.$$

Deadline:

$$T_k(x)\le T_{\max}.$$

Battery reserve:

$$B_i^k-E_i^k(x)\ge B_i^{\mathrm{reserve}}.$$

**Lưu ý ký hiệu:** Draft đang dùng $p_m$ cho population weight và dùng gần như trùng ký hiệu cho tọa độ client. Có thể đổi tọa độ thành $\mathbf r_m(t)$ để tránh nhầm.

### 2.3. Learning objective: actual post-aggregation validation loss

Tại cùng checkpoint $w_k$, local training của client $m$ tạo increment:

$$\Delta_m^k=w_{m,I}^k-w_k.$$

Nếu schedule $x$ chọn tập $\mathcal S(x)$:

$$
w_{k+1}(x)=w_k+\sum_{m\in\mathcal S(x)}
\frac{p_m}{\sum_{j\in\mathcal S(x)}p_j}\Delta_m^k.
$$

Chọn objective thứ nhất:

$$\boxed{f_1(x)=L_{\mathrm{val}}(w_{k+1}(x))}.$$

Nếu đánh giá stochastic:

$$
f_1(x)=\mathbb E_{\xi}[L_{\mathrm{val}}(w_{k+1}(x;\xi))],
$$

trong đó $\xi$ mô tả randomness từ local SGD và các nguồn được khai báo.

**Không thay $f_1$ bằng gradient matching $D(S)$, gradient similarity hoặc diversity.** Chúng chỉ là proxy để hướng dẫn proposal generation.

#### Cache reference updates

Với fixed local SGD settings, fixed checkpoint và matched random seeds, local update $\Delta_m^k$ độc lập với bandwidth và CPU frequency nếu client hoàn thành thành công. Có thể tính/cached từng client update một lần tại snapshot, sau đó tổ hợp các subset.

Điều này là acceleration hợp lệ trong **offline simulator** (draft Section 5.3), nhưng không có nghĩa client ngoài đời huấn luyện miễn phí. Ghi nhận cache construction trong search evaluation cost. Quan trọng: nếu caching làm reference evaluation quá rẻ, lý do cần Direction B (multi-fidelity) về sau phải được kiểm chứng lại.

### 2.4. Communication, time, energy

Uplink rate:

$$
R_{m,u}=b_{m,u}\log_2\left(1+\frac{P_mh_{m,u}}{N_0b_{m,u}}\right).
$$

Client compute + upload time:

$$
t_{m,u}=\frac{C_m}{f_m}+\frac{L_m}{R_{m,u}}.
$$

CPU computation energy:

$$E_m^{\mathrm{comp}}=\kappa_m C_m f_m^2.$$

Uplink transmission energy:

$$E_{m,u}^{\mathrm{tx}}=P_m\frac{L_m}{R_{m,u}}.$$

Với mô hình system accounting được định nghĩa nhất quán:

$$\boxed{f_2(x)=E_k(x),\qquad f_3(x)=T_k(x)}.$$

| Thành phần | Năng lượng $E_k$ | Thời gian $T_k$ |
|---|---|---|
| Local computation | Có | Có |
| Client uplink | Có | Có |
| Global model downlink | Có nếu nằm trong system boundary | Có |
| UAV aggregation | Có | Có |
| UAV–Coordinator backhaul | Có | Có |
| UAV hovering/propulsion | Theo draft có | Tác động qua thời lượng hoạt động |
| Optimizer computation | Phân biệt offline và online | Chỉ tính vào round nếu optimizer chạy online |

**System boundary phải rõ ràng:** Không nên tính energy cho một thành phần nhưng bỏ qua hoàn toàn thời gian của nó nếu thành phần nằm trên critical path. Không được cộng trùng năng lượng qua client, UAV, coordinator.

### 2.5. UAV mobility, channel và flight energy

Với bản cơ sở đề xuất:

- Coordinator: trạm mặt đất cố định.
- Ground clients: vị trí cố định trong pilot benchmark; đây là **đề xuất**, không phải kết luận draft đã chốt. *Stationary datasets* không đồng nghĩa *stationary clients*.
- UAVs: prescribed trajectories, không là biến tối ưu.
- Channel gains: tính tại đầu round và block-frozen trong phiên bản mô phỏng thứ nhất.
- Backhaul: định nghĩa fixed-rate model hoặc distance-dependent model rõ ràng.
- Flight energy: sử dụng cùng physical clock với FL protocol.

Draft viết:

$$
E_k^{\mathrm{flight}}=\sum_u\int_{\tau_k}^{\tau_{k+1}}P_u^{\mathrm{flight}}(t)\,dt,
$$

nhưng chưa chốt $q_u(t)$ hay $P_u^{\mathrm{flight}}(t)$. Cần bổ sung bằng kịch bản bay/hovering có thể reproduce.

Nếu giả định hovering với công suất không đổi:

$$E_k^{\mathrm{flight}}=\sum_uP_u^{\mathrm{hover}}T_k.$$

Khi đó flight energy tỉ lệ với time objective. Đây không phải lỗi, nhưng cần kiểm tra xem CPU và communication energy có tạo ra trade-off energy–time độc lập đủ đáng kể không.

**Tài liệu tham khảo propulsion energy:** Zeng, Xu & Zhang, *Energy Minimization for Wireless Communication With Rotary-Wing UAV*, 2019: https://doi.org/10.1109/TWC.2019.2902559

---

## 3. Set-aware client selection: lý thuyết và thuật toán

### 3.1. Ý nghĩa và giới hạn của $D(S)$

Draft Section 2.2 định nghĩa:

$$
D(S)=\left\|\sum_{m\in S}\alpha_m(S)g_m-\bar g\right\|^2,
\tag{9}
$$

với:

$$
g_m=\nabla F_m(w),\qquad \bar g=\sum_mp_mg_m.
$$

$D(S)$ đo sự khác nhau giữa gradient aggregate của selected set và population gradient. Hạn chế chính:

1. Gradient matching không bảo đảm trực tiếp validation improvement.
2. Multi-step local SGD có client drift và hiệu ứng phi tuyến; $D(S)$ tại checkpoint không mô tả hoàn chỉnh cập nhật sau nhiều bước.
3. $\bar g$ và gradient hiện tại của mọi client là các đại lượng có thể không quan sát được miễn phí.

### 3.2. Một kết quả lý thuyết nên đưa vào motivation

**Kết quả suy ra từ descent lemma, không phải định lý đã có trong draft.**

Giả sử $F_{\mathrm{pop}}$ là $\beta$-smooth, xét một bước full-gradient:

$$w^+=w-\eta g_S,$$

trong đó:

$$g_S=\sum_{m\in S}\alpha_m(S)g_m,\qquad \bar g=\nabla F_{\mathrm{pop}}(w).$$

Theo smoothness:

$$
F_{\mathrm{pop}}(w^+)\le F_{\mathrm{pop}}(w)
-\eta\langle\bar g,g_S\rangle
+\frac{\beta\eta^2}{2}\|g_S\|^2.
$$

Tại $\eta=1/\beta$, sử dụng đồng nhất thức

$$2\langle\bar g,g_S\rangle-\|g_S\|^2=\|\bar g\|^2-\|g_S-\bar g\|^2,$$

thu được:

$$
\boxed{
F_{\mathrm{pop}}(w^+)\le F_{\mathrm{pop}}(w)
-\frac{1}{2\beta}\left(\|\bar g\|^2-D(S)\right).
}
$$

Nếu $D(S)<\|\bar g\|^2$, có thể bảo đảm giảm **population training loss** cho mô hình một bước lý tưởng. Nếu ngược lại, bất đẳng thức không còn bảo đảm giảm loss.

**Giới hạn:** Không tự động suy ra kết quả cho validation loss, nhiều local SGD steps, stochastic gradients hoặc client drift. Đây là motivation cho gradient matching, không phải bảo đảm convergence cho toàn bộ Direction A.

### 3.3. Cần chốt $\hat V(S)$

Draft Section 2.2 nêu:

$$
\Delta V(m\mid S)=\hat V(S\cup\{m\})-\hat V(S),
\tag{10}
$$

nhưng chưa định nghĩa cụ thể $\hat V(S)$.

**Lựa chọn A — Gradient matching utility:**

$$\hat V_D(S)=-\hat D(S).$$

**Lựa chọn B — First-order learning utility:**

$$
\hat V_G(S)=\eta\langle\hat g_{\mathrm{ref}},\hat g_S\rangle
-\frac{\beta\eta^2}{2}\|\hat g_S\|^2.
$$

Ở đây $\hat g_{\mathrm{ref}}$ là ước lượng của population gradient (phải định nghĩa nguồn), và lựa chọn này vẫn yêu cầu xử lý sai số ước lượng/smoothness.

**Khuyến nghị:** Bắt đầu với $\hat D(S)$ cho guided operator và thử $\hat V_G(S)$ như ablation. Không nên đưa quá nhiều proxy mới cùng lúc.

### 3.4. Ước lượng $\hat D(S)$ từ sketches

Một projected gradient sketch:

$$z_m=Rg_m.$$

Gọi reference projected population gradient là $\hat z_{\mathrm{pop}}$:

$$
\hat g_S=\sum_{m\in S}\alpha_m(S)z_m,
$$

$$
\boxed{\hat D(S)=\|\hat g_S-\hat z_{\mathrm{pop}}\|^2}.
$$

Cần công bố rõ $\hat z_{\mathrm{pop}}$ đến từ đâu. Nếu simulator cấp toàn bộ *current sketches* cho scheduler, đó là **oracle-assisted/fully observed offline setting**; nếu dùng historical sketches, có vấn đề stale gradients.

| Setting | Thông tin | Mục đích |
|---|---|---|
| Oracle diagnostic | Tất cả current sketches | Kiểm tra upper bound của guided operator |
| History-based | Historical reports/sketches | Kiểm tra robustness dưới partial observation |

Nếu cần client tính và truyền sketch mới trước selection thì phần communication/computation đó có chi phí; không được coi là miễn phí. Physical probing thuộc Direction C, nên có thể để ngoài phiên bản đầu của A nhưng phải ghi ranh giới rõ.

### 3.5. Toán tử Set-aware Guided Mutation

Draft Section 6.1 mới đưa điều kiện swap:

$$
\hat D(S\setminus\{i\}\cup\{j\})<\hat D(S).
\tag{35}
$$

Điều đó chưa xác định đầy đủ cách chọn $i,j$, constraints, random exploration và điều kiện survival.

Đề xuất tính:

$$
\Delta_D(i,j\mid S)=
\hat D(S\setminus\{i\}\cup\{j\})-\hat D(S).
$$

Một guided mutation ưu tiên swap có $\Delta_D$ nhỏ (hoặc âm), nhưng vẫn giữ exploration:

$$
\operatorname{Mutation}(x)=
\begin{cases}
\text{Guided mutation},&\text{với xác suất }\rho,\\
\text{Generic mutation},&\text{với xác suất }1-\rho.
\end{cases}
$$

Sau mutation: decode → repair → evaluate true objective vector → constraint dominance/Pareto selection. **Không dùng $\hat D$ làm quyết định cuối cùng về survival.**

### 3.6. Pseudocode hoàn thiện

```text
Algorithm: Set-aware Multiobjective Evolutionary Scheduling

Input:
    Fixed FL snapshot S_k
    Population size N
    Reference evaluation budget B
    Available gradient sketches
    Network and hardware parameters

Output:
    Reference-evaluated feasible Pareto archive

1. Generate initial population:
     - Random feasible schedules
     - Channel-aware schedules
     - Gradient-representative schedules
     - Different client-set cardinalities
2. Decode and repair initial candidates
3. Reference-evaluate L_val, Energy, Time
4. Initialize Pareto population and archive
5. while evaluation budget remains:
     Select parents by Pareto rank and diversity
     Generate offspring using:
         - Generic add/drop/swap/reassign
         - Set-aware guided swap
         - Bandwidth mutation
         - CPU frequency mutation
     Decode and repair offspring
     Apply declared constraint handling
     Reference-evaluate candidate objectives
     Perform environmental selection
     Update feasible nondominated archive
6. Independently re-evaluate final candidates
   using the common declared protocol
7. Select one schedule using fixed preference rule
Return Pareto archive and selected schedule
```

Khuyến nghị dùng **NSGA-II** làm framework đầu tiên; không đồng thời thay đổi cả Pareto selection vì sẽ khó cô lập vai trò của set-aware operator.

### 3.7. Mixed-variable encoding và decoding

Client association:

$$a_m\in\{0,1,\ldots,U\}.$$

$0$ = client inactive; $a_m=u$ = gán vào UAV $u$.

Bandwidth softmax:

$$
b_{m,u}=B_u\frac{\exp(\rho_m)}{\sum_{j:a_j=u}\exp(\rho_j)}.
$$

CPU:

$$
f_m=f_m^{\min}+\xi_m(f_m^{\max}-f_m^{\min}).
$$

Trong base Shannon-rate model với fixed transmit power và spectrum orthogonal, sử dụng toàn bộ bandwidth pool cho active links thường không làm xấu upload time hoặc energy nếu không thêm chi phí sử dụng spectrum. Vì vậy chưa cần biến **unused bandwidth utilization** $\gamma_u$ trong phiên bản đầu; bổ sung khi có lý do vật lý rõ ràng.

### 3.8. CPU allocation: evolve hay giải tích?

Với bound service time $d$:

$$\frac{C_m}{f_m}+\frac{L_m}{R_m}\le d,$$

CPU tối thiểu để thỏa bound:

$$
f_m^\star=\max\left\{f_m^{\min},\frac{C_m}{d-L_m/R_m}\right\}
$$

với điều kiện $d>L_m/R_m$ và $f_m^\star\le f_m^{\max}$.

Thử hai variants:

| Variant | Cơ chế CPU | Mục đích |
|---|---|---|
| A1 | Evolved CPU frequencies | Generic mixed evolutionary baseline |
| A2 | Analytical CPU từ service-time bound | Kiểm tra lợi ích giảm chiều tìm kiếm |

Cần quét nhiều giá trị $d$ để phản ánh đầy đủ energy–time trade-off thay vì khóa một deadline duy nhất.

---

## 4. Literature review: nghiên cứu liên quan

### 4.1. Nhóm A — Set-aware, gradient-aware, multiobjective client selection

**1. G-M3CS / G-M3CS+ (2026), Applied Soft Computing**  
*G-M3CS: A gradient-based multi-metric multi-objective client selection algorithm for hierarchical federated learning*  
https://doi.org/10.1016/j.asoc.2026.115642

- Sử dụng NSGA-II trong hierarchical FL với nhiều gradient metrics: direction consistency, diversity, magnitude và historical consistency ở bản mở rộng.
- Liên quan trực tiếp đến multiobjective evolutionary client selection và gradient complementarity.
- **Khả năng chồng lấn novelty cao** với một NSGA-II chỉ được thêm gradient-aware heuristic.
- Điểm Direction A cần kiểm chứng khác biệt: jointly optimized UAV association, bandwidth, CPU, actual post-round validation loss và explicit energy/time objectives.

**2. DivFL (ICLR 2022)**  
*Diverse Client Selection for Federated Learning via Submodular Maximization*  
https://openreview.net/forum?id=nwKXyFvaUm

- Client selection dựa trên facility-location submodular maximization trong gradient space.
- Tài liệu nền cho gradient representativeness và set-dependent utility.
- Không trực tiếp nhắm tới 3-objective loss–energy–time UAV resource allocation.

**3. FedCG (IEEE TMC 2024)**  
*Federated Learning With Client Selection and Gradient Compression in Heterogeneous Edge Systems*  
https://doi.org/10.1109/TMC.2023.3309497

- Representative client selection với gradient compression theo heterogeneity của edge devices.
- Có phân tích convergence, hữu ích khi xây dựng lập luận về selected-client representation và resource constraints.

**4. FedCor (CVPR 2022)**  
*FedCor: Correlation-Based Active Client Selection Strategy for Heterogeneous Federated Learning*  
https://openaccess.thecvf.com/content/CVPR2022/html/Tang_FedCor_Correlation-Based_Active_Client_Selection_Strategy_for_Heterogeneous_Federated_Learning_CVPR_2022_paper.html

- Gaussian Process mô hình hóa correlations giữa client losses và expected loss reduction.
- Phù hợp nếu mở rộng $\hat V(S)$ thành learning utility thay vì gradient matching đơn thuần.

**5. HiCS-FL (NeurIPS 2024)**  
*Heterogeneity-Guided Client Sampling: Towards Fast and Efficient Non-IID Federated Learning*  
https://papers.nips.cc/paper_files/paper/2024/hash/7886b9bafe76c52fd568db10ff9772df-Abstract-Conference.html

- Ước lượng heterogeneity từ output-layer updates và clustered sampling.
- Phù hợp làm statistical selection baseline và tham khảo convergence dưới non-IID.

### 4.2. Nhóm B — Joint client selection và wireless resource allocation

| Công trình | Trọng tâm | Mức liên quan |
|---|---|---|
| [Multi-UAV-assisted FL (2024)](https://doi.org/10.1109/TNSM.2023.3298220) | Multi-UAV aggregation, client selection/resource management bằng Lyapunov/DRL | Rất cao về kiến trúc |
| [CBCSBA (2025)](https://doi.org/10.1109/TMC.2025.3539284) | Class-balanced client groups và bandwidth allocation | Rất cao về joint optimization |
| [FedGCS (IJCAI 2024)](https://doi.org/10.24963/ijcai.2024/526) | Generative client selection, learning/time/energy | Cao |
| [EECS-Apt (2024)](https://doi.org/10.1109/VTC2024-Spring62846.2024.10683401) | Client selection + adaptive bandwidth, energy/deadline | Cao |
| [MetaCS-FL (2026)](https://doi.org/10.1016/j.future.2026.108707) | Metaheuristic selection với accuracy/time/energy/fairness | Cao |

Ưu tiên đọc chi tiết **Multi-UAV-assisted FL** và **CBCSBA** để đối chiếu system model, chi phí truyền thông, ràng buộc và baseline allocation.

Bài **FSTPO** người dùng cung cấp cũng là một comparator quan trọng về kiến trúc UAV-assisted FL và 3 nhóm quyết định scheduling/bandwidth/CPU, nhưng dùng DRL và weighted scalar utility, không phải Pareto MOEA.

### 4.3. Nhóm C — Multiobjective evolutionary foundations

| Thuật toán | Tài liệu | Vai trò |
|---|---|---|
| NSGA-II | [Deb et al. (2002)](https://doi.org/10.1109/4235.996017) | Main framework và generic MOEA baseline |
| MOEA/D | [Zhang & Li (2007)](https://doi.org/10.1109/TEVC.2007.892759) | Decomposition-based baseline |
| Random feasible search | Không cần paper riêng | Baseline đo giá trị thực của evolutionary search |

### 4.4. Ma trận so sánh đóng góp

| Công trình | Set-aware selection | Resource allocation | Pareto/MOO | UAV model |
|---|---|---|---|---|
| DivFL | Có | Không phải trọng tâm | Không phải Pareto MOEA | Không |
| FedCG | Representative selection | Có, qua compression | Joint optimization | Không |
| G-M3CS | Có, qua gradient metrics | Không tập trung wireless bandwidth/CPU | NSGA-II | Không phải UAV physical optimization |
| Multi-UAV-assisted FL | Complementarity không là đóng góp chính | Có | Không dùng Pareto MOEA làm phương pháp chính | Có |
| CBCSBA | Class-balanced grouping | Có | Joint cost optimization | Không đặc thù multi-UAV |
| FSTPO | Gradient divergence | Có | Weighted utility | Có |
| **Direction A đề xuất** | **Gradient-guided set mutation** | **Bandwidth + CPU + UAV association** | **Loss–Energy–Time Pareto** | **Prescribed mobility** |

Ma trận trên là nhận xét về **trọng tâm đóng góp được công bố**, không phải kiểm toán rằng mỗi công trình hoàn toàn không đề cập thành phần được ghi “Không”. Trước khi xuất bản cần đọc full text các bài gần nhất, kiểm tra thuật toán/baselines và xác minh thông tin thư mục.

---

## 5. Thiết kế thực nghiệm Direction A

### 5.1. Ba phase triển khai

**Phase 1 — Kiểm chứng physical/FL evaluator**

- 2 UAV, 6 clients, một checkpoint.
- Dữ liệu non-IID nhỏ, fixed local work, fixed communication model.
- Liệt kê 63 nonempty client subsets; với mỗi subset, dùng một **restricted** resource-allocation grid đã chọn.
- Kiểm tra hierarchical aggregation có tương đương flat aggregation; kiểm tra unit và feasibility.
- Reference subset enumeration chỉ là exact trong không gian rời rạc bị giới hạn, **không phải** exact solution cho bài toán continuous hoàn chỉnh.

**Phase 2 — Kiểm chứng set-aware operator**

- Khoảng 20 clients, 2 UAV, Fashion-MNIST, nhiều checkpoint.
- IID, non-IID, rare-class client, noisy-label client.
- So sánh generic NSGA-II và Set-aware NSGA-II dưới cùng evaluation budget.
- Đo Pareto quality, số candidate evaluations, selection frequency và validation impact.

**Phase 3 — End-to-end FL và physical mobility**

- 20–100 clients, 2–5 UAV, nhiều FL rounds.
- Prescribed UAV traces, channel conditions, multiple partitions/seeds.
- Cố định preference rule để chọn một schedule từ archive mỗi round.
- Đo final accuracy, macro-F1, rare-class recall, energy/time-to-target, battery depletion, deadline violation.

### 5.2. Các baselines đề xuất

| Baseline | Client selection | Resource allocation |
|---|---|---|
| Random | Random feasible | Common allocator |
| Channel-greedy | Good-channel clients | Common allocator |
| Gradient similarity | Similarity-based | Common allocator |
| Gradient diversity | Diversity-based | Common allocator |
| Generic NSGA-II | Random/generic mutation | Evolutionary |
| **Set-aware NSGA-II** | **Guided + generic mutation** | **Same evolutionary setup** |
| MOEA/D | Decomposition-based | Same encoding and feasibility |

Khi so sánh riêng client selection, dùng **cùng allocator**. Khi so generic NSGA-II với set-aware NSGA-II, giữ giống N, budget, survival, constraints, seed và evaluator — chỉ thay guided operator.

### 5.3. Ablation studies

| Ablation | Câu hỏi |
|---|---|
| Có/không set-aware swap | Guided operator có cải thiện Pareto quality? |
| $\hat D(S)$ so với $\hat V_G(S)$ | Proxy nào dự báo learning tốt hơn? |
| Oracle sketches so với historical sketches | Thiếu thông tin ảnh hưởng thế nào? |
| Fixed vs evolved CPU | Joint allocation có ích không? |
| Evolved vs analytical CPU | Giảm chiều giúp tiết kiệm evaluation không? |
| Stationary vs prescribed UAV mobility | Mobility có thay đổi thứ hạng algorithms không? |
| One-round vs complete episode | Snapshot Pareto tốt có tạo learning trajectory tốt? |

Hai ablations quan trọng nhất: **set-aware vs generic mutation** và **oracle vs history-based information**.

### 5.4. Đánh giá Pareto archive và stochastic performance

Metrics:

$$HV(\mathcal A),\qquad IGD(\mathcal A,\mathcal P_{\mathrm{ref}}).$$

- HV càng lớn thường càng tốt khi reference point và normalization cố định.
- IGD càng nhỏ càng tốt, nhưng phải có reference set đủ đáng tin; pooled empirical reference cần ghi rõ là approximate.
- Không so raw validation losses từ các global checkpoints khác nhau như một fitness landscape duy nhất.
- Dùng matched random seeds để giảm phương sai khi so candidates tại cùng snapshot.
- Final archive được đánh giá lại với common independent audit seeds nếu báo cáo verified Pareto front.
- Báo search-time/search-energy và operational costs theo system boundary rõ ràng.

---

## 6. Implementation readiness checklist

- [ ] **FL evaluator:** Common checkpoint, fixed local SGD, weighted hierarchical aggregation, tách train/validation/test.
- [ ] **Information contract:** Rõ oracle sketches, historical reports và quyền truy cập controller.
- [ ] **Set-aware operator:** Có proxy, proposal/sampling, exploration, acceptance và survival rules.
- [ ] **Physical model:** Chốt client mobility, UAV traces, channel, backhaul, downlink và flight power.
- [ ] **Resource feasibility:** Repair/constraint handling, active bandwidth, CPU, deadlines, battery.
- [ ] **Candidate evaluation:** Đồng nhất objectives, units, snapshot IDs, seeds và caching.
- [ ] **Multiobjective benchmarking:** Equal budgets, common protocol, verified archive.
- [ ] **End-to-end evaluation:** Snapshot fronts cùng complete episodes.
- [ ] **Novelty validation:** Đối chiếu trực tiếp G-M3CS, DivFL và joint resource allocation literature.

---

## 7. Định vị đóng góp khoa học và kế hoạch hành động

### 7.1. Hai hướng research positioning

**Hướng định vị 1 — Set-aware operator.**

Tập trung vào việc chứng minh marginal/set-dependent client contribution làm Pareto front tốt hơn independent scoring dưới cùng network constraints và evaluation budget. Khó nhất là phân biệt rõ với DivFL/G-M3CS và các gradient-aware strategies đã có.

**Hướng định vị 2 — Joint Learning–Communication–Computation Optimization.**

Xem set-aware mutation là một phần của hệ thống joint optimization:

$$
\boxed{
\text{Set-dependent learning contribution}
+\text{Client--UAV association}
+\text{Resource allocation}
+\text{Pareto optimization}
}
$$

Cách thứ hai có phạm vi mô hình và đánh giá rõ hơn nhưng **chưa đủ để khẳng định novelty**. Cần chứng minh bằng comparison/ablation.

### 7.2. Thứ tự thực hiện

1. **Hoàn thiện mathematical problem P-A:** Chốt decision variables, objective functions, constraints, information contract.
2. **Xây reference evaluator:** Kiểm chứng weighted aggregation, costs, deadlines, seeds và caches.
3. **Triển khai generic NSGA-II:** Có mixed encoding và feasibility trước khi thêm heuristic.
4. **Thêm Set-aware Guided Mutation:** $\hat D(S)$ + random exploration, equal-budget comparison.
5. **Chạy benchmark và failure diagnostics:** Hiểu khi nào guided search hữu ích và khi nào thất bại.

### 7.3. Kết luận

Direction A **có thể triển khai ngay như một reference-evaluated optimization benchmark**, nhưng cần hoàn thiện ranh giới theoretical proxy / actual learning objective, mô hình vật lý, information availability và phạm vi novelty.

Ba việc ưu tiên nhất:

1. Làm rõ $D(S)$, $\hat V(S)$ và quan hệ với validation loss, gồm giới hạn của gradient proxy.
2. Hoàn thiện nhất quán resource/energy/time evaluator, đặc biệt mobility, backhaul và offline oracle evaluation.
3. Đọc và đối chiếu chi tiết G-M3CS, DivFL, FedCG và những nghiên cứu joint client selection–resource allocation trước khi đưa ra novelty claim.

**Khuyến nghị kỹ thuật ban đầu:**

$$
\boxed{\text{Reference-evaluated Set-aware NSGA-II}}
$$

với ba mục tiêu **actual post-round validation loss — physical energy — elapsed time**, sử dụng gradient-guided proposal generation và verified reference evaluation.

Phương án này tạo baseline có kiểm chứng cho Direction B (multi-fidelity) và Direction C (adaptive probing).

---

## 8. Danh mục tài liệu và liên kết

1. Deb, K. et al. (2002). **A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II.** IEEE TEC. https://doi.org/10.1109/4235.996017
2. Zhang, Q. & Li, H. (2007). **MOEA/D: A Multiobjective Evolutionary Algorithm Based on Decomposition.** IEEE TEC. https://doi.org/10.1109/TEVC.2007.892759
3. Zeng, Y., Xu, J., & Zhang, R. (2019). **Energy Minimization for Wireless Communication With Rotary-Wing UAV.** IEEE TWC. https://doi.org/10.1109/TWC.2019.2902559
4. **G-M3CS: A gradient-based multi-metric multi-objective client selection algorithm for hierarchical federated learning** (2026). Applied Soft Computing. https://doi.org/10.1016/j.asoc.2026.115642
5. **Diverse Client Selection for Federated Learning via Submodular Maximization (DivFL)** (ICLR 2022). https://openreview.net/forum?id=nwKXyFvaUm
6. **Federated Learning With Client Selection and Gradient Compression in Heterogeneous Edge Systems (FedCG).** IEEE TMC. https://doi.org/10.1109/TMC.2023.3309497
7. Tang et al. (2022). **FedCor: Correlation-Based Active Client Selection Strategy for Heterogeneous Federated Learning.** CVPR. https://openaccess.thecvf.com/content/CVPR2022/html/Tang_FedCor_Correlation-Based_Active_Client_Selection_Strategy_for_Heterogeneous_Federated_Learning_CVPR_2022_paper.html
8. **Heterogeneity-Guided Client Sampling: Towards Fast and Efficient Non-IID Federated Learning (HiCS-FL)** (NeurIPS 2024). https://papers.nips.cc/paper_files/paper/2024/hash/7886b9bafe76c52fd568db10ff9772df-Abstract-Conference.html
9. **Multi-UAV-assisted FL**. https://doi.org/10.1109/TNSM.2023.3298220
10. **CBCSBA**. https://doi.org/10.1109/TMC.2025.3539284
11. **FedGCS**. https://doi.org/10.24963/ijcai.2024/526
12. **EECS-Apt**. https://doi.org/10.1109/VTC2024-Spring62846.2024.10683401
13. **MetaCS-FL**. https://doi.org/10.1016/j.future.2026.108707
14. Yang, X. et al. **Federated Spatio-Temporal Policy Learning for Efficient Resource Management in UAV-Assisted IoT Edge Networks (FSTPO).** User-provided PDF; DOI: https://doi.org/10.1109/JIOT.2026.3727888
15. **Information-Aware Multiobjective Evolutionary Optimization with Multi-Fidelity Evaluation for UAV-Assisted Federated Learning**. User-provided JNCA research working draft (13 pages).

> **Ghi chú:** Đây là bản tổng hợp nội dung phân tích đã trình bày trong cuộc hội thoại. Khi dùng cho manuscript, cần kiểm tra chính xác title, authorship, publication status, DOI và nội dung đầy đủ của từng related work; các hướng đề xuất chưa được chứng minh bằng benchmark thực nghiệm.
