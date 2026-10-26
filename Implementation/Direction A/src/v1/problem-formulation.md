# Direction A — Mô hình bài toán và đặc tả triển khai

**Phiên bản đề xuất:** A-REF v1.0.  
**Phạm vi:** một vòng FL, nhiều UAV, tối ưu ba mục tiêu, đánh giá tham chiếu đầy đủ trong mô phỏng offline.  
**Mục đích:** chốt mô hình, giả thiết, evaluator và giao thức so sánh trước khi triển khai optimizer.

Tài liệu xử lý các khoảng trống của [Research Review](Deep%20Report/Direction_A_Research_Review.md), [Research Report VI](Deep%20Report/Direction_A_Research_Report_VI.md) và [draft JNCA](../../docs/developing%20directions/JNCA_Huy.pdf). Giao thức vật lý, cách xử lý thông tin thiếu và các lựa chọn triển khai dưới đây là **đề xuất cho project**, không mặc định là nội dung đã được chứng minh trong draft.

## 1. Các lựa chọn được chốt

| Vấn đề của báo cáo | Quyết định trong bản cơ sở |
| --- | --- |
| Một vòng hay toàn horizon? | Tối ưu tại snapshot bất biến; nhiều vòng là heuristic lặp, chưa có bảo đảm tối ưu toàn horizon. |
| Learning objective chưa rõ | Loss validation thực sau local SGD và tổng hợp; proxy chỉ hướng dẫn proposal. |
| Oracle và online controller | A-REF là benchmark offline được phép gọi oracle; không tuyên bố deployable online. |
| Frozen channel và UAV mobility | Bản cơ sở dùng UAV hover, client cố định; mobility là biến thể riêng. |
| Chi phí downlink/backhaul/aggregation | Chốt các pha có barrier và cách tính thời gian, năng lượng từng nút. |
| Learning cache dư thừa | Cache update theo client/checkpoint/seed; loss theo tập client và giao thức validation. |
| Sketch thiếu/cũ | Chỉ dùng báo cáo hợp lệ, công bố độ phủ; không điền gradient 0 cho client chưa biết. |
| Bandwidth gần 0 | Cấp tối thiểu $b_{\min}>0$; giải mã trên simplex đóng. |
| CPU và pin phụ thuộc thời gian | Decode toàn lịch, tính thời gian rồi năng lượng; kiểm tra lại tất cả ràng buộc. |
| Noisy Pareto/validation overfit | Seed ghép cặp trong search, audit độc lập, test không dùng chọn lịch. |
| So sánh không công bằng | Cùng thông tin, evaluator, cache và allocator; đối sánh chi phí tính toán thực tế. |

**Sản phẩm Direction A:** evaluator kiểm tra được; benchmark loss–energy–time; NSGA-II với proposal xét quan hệ giữa client; thực nghiệm xác định khi nào proposal hữu ích. Các mệnh đề dưới đây chỉ áp dụng trong giả thiết đã nêu.

## 2. Giả thiết, snapshot và ký hiệu

### 2.1. Giả thiết cơ sở

1. Có $M$ client, $U$ UAV và coordinator mặt đất ký hiệu $0$. Tất cả client/UAV có vị trí cố định trong benchmark cơ sở, UAV ở độ cao dương.
2. FL đồng bộ, dùng cùng checkpoint nguồn, kiến trúc, learning rate, đúng $I$ bước local SGD và minibatch size $B_{\rm loc}$.
3. Client có DVFS liên tục; số chu kỳ công việc $C_m$ không phụ thuộc tần số. Tần số chỉ thay đổi thời gian/năng lượng, không thay đổi local update.
4. Mọi upload của lịch khả thi thành công. Không dropout, retransmission, outage, early stopping hoặc compression phụ thuộc tài nguyên.
5. Các UAV có phổ uplink độc lập. Mỗi client giữ bandwidth đã cấp trong cả pha; không tái sử dụng phần phổ khi client hoàn thành sớm.
6. Tất cả $U$ UAV hover suốt vòng, kể cả UAV không được gán client. Tắt/hạ cánh UAV chưa là quyết định.
7. Dữ liệu stationary; train, search-validation, audit-validation và final-test tách biệt theo mẫu.
8. Payload mô hình/cập nhật FP32 và metadata cố định. Đổi compression hoặc optimizer state phải đổi protocol ID.
9. Năng lượng gồm baseline theo thời gian và các phần tăng thêm định nghĩa ở Mục 5. Không có chi phí CPU phụ thuộc tần số/thời gian ngoài các hạng đã nêu.
10. Bộ tham số, normalization, ưu tiên chọn lịch và budget được chốt trên scenario phát triển trước khi chạy benchmark báo cáo.

Đây là deterministic effective-rate model, không phải bảo đảm độ tin cậy trên mạng thực. Giới hạn của mô hình là một phần của kết luận nghiên cứu.

### 2.2. Snapshot bất biến

$$
\mathcal S_k=(w_k,\tau_k,\mathbf q,\mathbf r,e^k,\mathcal B^k,
\mathcal H_k,\Theta_{\rm FL},\Theta_{\rm net},\Theta_{\rm cost}).
\tag{A1}
$$

- $w_k\in\mathbb R^d$: mô hình hiện tại; $\tau_k$: thời điểm vật lý bắt đầu vòng.
- $\mathbf q_u=(x_u,y_u,H_u)$, $H_u>0$: UAV; $\mathbf r_m=(x_m,y_m,0)$: client. Không dùng $p_m$ cho tọa độ.
- $e^k_{mu}\in\{0,1\}$: mask liên kết khả dụng được cung cấp.
- $\mathcal B_i^k,\mathcal B_i^{\rm res}$: pin còn lại và dự trữ, đơn vị J.
- $\mathcal H_k$: lịch sử báo cáo được phép; $\Theta$: cấu hình FL, mạng và chi phí.

Snapshot ID định danh checkpoint, split dữ liệu, protocol, trạng thái vật lý và lịch sử. Candidate evaluation không được sửa snapshot.

### 2.3. Tham số cần có

| Ký hiệu | Ý nghĩa | Đơn vị/miền |
| --- | --- | --- |
| $p_m$ | Trọng số quần thể mục tiêu | $p_m>0,\sum_mp_m=1$ |
| $C_m$ | Công việc local training và tạo báo cáo bắt buộc | cycles, $>0$ |
| $\kappa_m$ | Hệ số năng lượng CPU động | $\kappa_mC_mf_m^2$ tính bằng J |
| $f_m^{\min},f_m^{\max}$ | Miền DVFS | cycles/s, $0<f_m^{\min}\le f_m^{\max}$ |
| $B_u,b_{\min}$ | Uplink pool và cấp bandwidth tối thiểu | Hz, $0<b_{\min}\le B_u$ |
| $P_m^{\rm tx},N_0$ | Công suất phát và noise PSD | W, W/Hz |
| $\beta_0$ | Hệ số path gain, khoảng cách dùng mét | theo convention gain tại 1 m |
| $\eta_{\rm MAC},\Gamma$ | Hiệu suất giao thức, coding gap | $0<\eta_{\rm MAC}\le1,\Gamma\ge1$ |
| $L_w,L_m,L_u^{\rm bh}$ | Payload model, client update, UAV aggregate | bits, $>0$ |
| $r^{0u},r^{um},r^{u0}$ | Rate downlink/backhaul cố định | bit/s, dương trên link dùng |
| $a_u^{(0)},a_u^{(1)},a_0^{(0)},a_0^{(1)}$ | Hệ số thời gian aggregation | s, không âm |
| $P_i^{\rm base},P_u^{\rm hov}$ | Baseline điện tử, propulsion hover | W, không âm |
| $N_{\max},T_{\max}$ | Giới hạn số client, deadline | integer dương; s dương |

Công suất hoạt động bổ sung là phần **tăng thêm trên baseline**. Không cộng công suất toàn thiết bị với baseline lần nữa. Đổi dBm sang W trước khi tính. $C_m$ là cycles, không phải samples hay bits.

## 3. Mô hình học và objective thực

### 3.1. Quần thể mục tiêu

$$
F_m(w)=\frac1{n_m}\sum_{\xi\in\mathcal D_m^{\rm tr}}\ell(w;\xi),
\qquad F_{\rm pop}(w)=\sum_mp_mF_m(w).
\tag{A2}
$$

Bản cơ sở dùng $p_m=n_m/\sum_jn_j$. Nếu ứng dụng cần cân bằng thiết bị/vùng, đổi trọng số từ khi sinh scenario và giữ nguyên giữa các phương pháp.

Với $v\in\{\mathrm{search},\mathrm{audit},\mathrm{test}\}$:

$$
L_v(w)=\sum_{m=1}^Mp_m
\frac1{|\mathcal V_m^v|}\sum_{\xi\in\mathcal V_m^v}\ell(w;\xi).
\tag{A3}
$$

Mỗi $\mathcal V_m^v$ phải không rỗng, hoặc dùng tập validation có trọng số tái hiện cùng quần thể. Không tự đổi $p_m$ khi bỏ client khó phục vụ. Tất cả validation/test thuộc evaluator, không nằm trong input của proposal operator.

### 3.2. Local SGD và aggregation

Seed client là hàm xác định của snapshot, seed replicate, client ID và mục đích:

$$
w^{k,r}_{m,0}=w_k,\qquad
w^{k,r}_{m,i+1}=w^{k,r}_{m,i}
-\eta_k\widehat\nabla F_m(w^{k,r}_{m,i};\omega_{m,r,i}),
\quad i=0,\ldots,I-1;
\quad \Delta_m^{k,r}=w^{k,r}_{m,I}-w_k.
\tag{A4}
$$

Mỗi bước lấy đúng B_loc mẫu có hoàn lại theo RNG riêng client; minibatch báo cáo dùng 32 mẫu có hoàn lại với RNG riêng. Nhờ vậy client ít dữ liệu vẫn có cùng số bước và kích thước batch. Cố định RNG minibatch, augmentation, dropout và reset optimizer. Bản cơ sở dùng SGD không momentum và model không có BatchNorm running statistics. Nếu đổi model phải quy định cả non-parameter state.

Với $S_u=\{m:s_{mu}=1\}$, $S=\bigcup_uS_u$, $P_A=\sum_{m\in A}p_m$:

$$
\Delta_u^{k,r}=\sum_{m\in S_u}\frac{p_m}{P_{S_u}}\Delta_m^{k,r},
\qquad
w_{k+1}^{r}(S)
=w_k+\sum_{u:S_u\ne\varnothing}\frac{P_{S_u}}{P_S}\Delta_u^{k,r}
=w_k+\sum_{m\in S}\frac{p_m}{P_S}\Delta_m^{k,r}.
\tag{A5}
$$

Trong reference evaluator, tổng hợp theo thứ tự client ID cố định bằng dạng flat ở (A5), để cache không phụ thuộc sai số làm tròn do thứ tự nhóm UAV. Kiểm tra hierarchical/flat trong tolerance số học; nếu mô phỏng giao thức làm tròn hoặc lượng tử hóa phụ thuộc nhóm, phải bỏ giả thiết separability theo tập. UAV rỗng không gửi aggregate; metadata chứa $P_{S_u}$. Chuẩn hóa trên tập được chọn nhìn chung gây bias khi lựa chọn có hệ thống; không gọi update này unbiased so với toàn quần thể.

### 3.3. Kỳ vọng và sample-average approximation

$$
J_L(S)=\mathbb E_\omega[L_{\rm search}(w_{k+1}^{\omega}(S))\mid\mathcal S_k].
\tag{A6}
$$
$$
\widehat J_L^{\rm search}(S)
=\frac1{R_{\rm search}}\sum_{r=1}^{R_{\rm search}}
 L_{\rm search}(w_{k+1}^{r}(S)).
\tag{A7}
$$

Optimizer thực sự giải bài toán hữu hạn với (A7), dùng cùng seed bundle cho mọi candidate tại snapshot. $R=1$ là một hiện thực, không phải kỳ vọng chính xác. Audit dùng seed độc lập và split audit riêng.

**Tách biệt theo tập:** trong giả thiết cơ sở, hai lịch khả thi có cùng $S$ tạo cùng model/loss với cùng seed vì (A4) không phụ thuộc tài nguyên và (A5) khử association. Đây là cơ sở cache theo tập. Tính chất không giữ nếu dropout, lượng công việc, compression hay aggregation thay đổi theo tài nguyên.

## 4. Quyết định, radio và timeline

### 4.1. Biến

$$
x=(s,b,f),\quad s_{mu}\in\{0,1\},\quad b_{mu}\ge0,\quad f_m\ge0.
\tag{A8}
$$

Đặt $s_m=\sum_us_{mu}$, $n_u=|S_u|$, $y_u=\mathbf1[n_u>0]$, $n_U=\sum_uy_u$. Chỉ tính learning objective khi $S\ne\varnothing$.

### 4.2. Uplink và local work

$$
h_{mu}=\frac{\beta_0}{\|\mathbf q_u-\mathbf r_m\|^2},\qquad
R_{mu}(b)=\eta_{\rm MAC}b\log_2\left(1+
\frac{P_m^{\rm tx}h_{mu}}{\Gamma N_0b}\right).
\tag{A9}
$$
$$
t_m^{\rm cmp}=\frac{C_m}{f_m},\quad
v_m=\frac{L_m}{R_{m,a_m}(b_{m,a_m})},\quad
d_{\rm svc}(x)=\max_{m\in S}\left(t_m^{\rm cmp}+v_m\right).
\tag{A10}
$$

Client bắt đầu compute đồng thời sau downlink, upload ngay khi compute xong trên phổ riêng. Do đó thời gian service là **max của tổng**, không phải tổng hai giá trị max.

Chỉ gọi các công thức chia cho client/link hoạt động. Mask inactive trước phép chia; không tính $0\times(1/0)$.

### 4.3. Giao thức sáu pha

| Pha | Quy tắc | Thời lượng |
| --- | --- | --- |
| Coordinator → UAV | Broadcast model một lần tới tất cả UAV hoạt động, rate theo link chậm nhất | $D_0=L_w/\min_{u:y_u=1}r^{0u}$ |
| UAV → client | Mỗi UAV broadcast tới nhóm; các UAV song song | $D_u=L_w/\min_{m\in S_u}r^{um}$, $D=\max_uD_u$ |
| Compute + uplink | Theo (A10), bandwidth không tái sử dụng | $d_{\rm svc}$ |
| UAV aggregation | Bắt đầu sau barrier toàn pha service; UAV song song | $A_u=y_u(a_u^{(0)}+a_u^{(1)}n_u)$, $A=\max_uA_u$ |
| UAV → coordinator | Backhaul trực giao đồng thời | $H_u=y_uL_u^{\rm bh}/r^{u0}$, $H=\max_uH_u$ |
| Global aggregation | Bắt đầu sau khi nhận đủ backhaul | $A_0=a_0^{(0)}+a_0^{(1)}n_U$ |

Đặt $D_u=A_u=H_u=0$ khi $y_u=0$. Downlink/backhaul có rate và công suất cấu hình riêng, không phụ thuộc băng thông uplink $b$.

$$
T(x)=D_0+D+d_{\rm svc}(x)+A+H+A_0.
\tag{A11}
$$

Các pha tuần tự có barrier; trong một pha UAV song song trên tài nguyên độc lập. Đây là giao thức bảo thủ nhưng xác định. Cho phép pipeline/aggregation sớm cần thay critical path và kiểm tra lại các bổ đề.

## 5. Năng lượng và pin

### 5.1. Quy ước

Baseline điện tử tính suốt vòng. Công suất transmit/receive/aggregate dưới đây là increment. UAV bật một receiver trong toàn bộ service, không cộng một receiver đầy đủ cho mỗi client. Coordinator bật receiver trong toàn bộ pha backhaul. Mọi UAV hover suốt vòng.

Client không được chọn vẫn có baseline nếu scenario quy định, nhưng không có local training/upload cost. Đặt baseline bằng 0 là chế độ năng lượng tăng thêm, phải ghi nhãn rõ.

### 5.2. Năng lượng từng nút

Với client hoạt động:
$$
E_m=P_m^{\rm base}T+
\kappa_mC_mf_m^2+P_m^{\rm rx,DL}D_{a_m}+P_m^{\rm tx}v_m.
\tag{A12}
$$
Với client inactive: $E_m=P_m^{\rm base}T$.

$$
\begin{aligned}
E_u={}&(P_u^{\rm hov}+P_u^{\rm base})T\\
&+y_u\left(P_u^{\rm rx,0}D_0+P_u^{\rm tx,DL}D_u
+P_u^{\rm rx,UL}d_{\rm svc}
+P_u^{\rm agg}A_u+P_u^{\rm tx,BH}H_u\right).
\end{aligned}
\tag{A13}
$$
$$
E_0=P_0^{\rm base}T+P_0^{\rm tx,DL}D_0+
P_0^{\rm rx,BH}H+P_0^{\rm agg}A_0,\qquad
E(x)=\sum_mE_m+\sum_uE_u+E_0.
\tag{A14}
$$

Không cộng baseline lần hai cho thời gian compute/receive. Không bỏ hover của UAV rỗng. Báo riêng propulsion và radio/compute để nhận diện trường hợp energy gần trùng time.

Coordinator dùng điện lưới vẫn góp vào objective nhưng không chịu giới hạn pin. Với tập nút chạy pin $\mathcal I_{\rm bat}$:
$$
\mathcal B_i^{k+1}=\mathcal B_i^k-E_i(x)\ge\mathcal B_i^{\rm res}.
\tag{A15}
$$

### 5.3. Tách hai loại chi phí

$E(x),T(x)$ là chi phí **thực thi một lịch**. Việc thử candidate, training phản thực tế, validation, tạo cache và audit thuộc chi phí tìm kiếm offline, ghi riêng wall time, CPU/GPU-seconds, năng lượng nếu đo được.

A-REF đóng băng đồng hồ mô phỏng khi search. Muốn đánh giá một controller online phải thêm chi phí quyết định và cập nhật kênh/pin trong khoảng chờ; không được đơn giản gọi A-REF online mà vẫn dùng oracle miễn phí.

## 6. Bài toán hoàn chỉnh P-A

$$
\boxed{
\begin{aligned}
\min_{s,b,f}\quad&
\left(\widehat J_L^{\rm search}(S(s)),E(s,b,f),T(s,b,f)\right)\\
\mathrm{C1}:\;&s_{mu}\in\{0,1\},\quad \sum_us_{mu}\le1;\\
\mathrm{C2}:\;&s_{mu}\le e_{mu}^k;\\
\mathrm{C3}:\;&1\le\sum_ms_m\le\min(N_{\max},M);\\
\mathrm{C4}:\;&b_{\min}s_{mu}\le b_{mu}\le B_us_{mu};\\
\mathrm{C5}:\;&\sum_mb_{mu}\le B_u\quad(\forall u);\\
\mathrm{C6}:\;&f_m^{\min}s_m\le f_m\le f_m^{\max}s_m;\\
\mathrm{C7}:\;&T(s,b,f)\le T_{\max};\\
\mathrm{C8}:\;&E_i(s,b,f)\le\mathcal B_i^k-\mathcal B_i^{\rm res}
\quad(\forall i\in\mathcal I_{\rm bat}).
\end{aligned}}
\tag{A16}
$$

Các phương trình (A4)–(A14) là một phần của định nghĩa. Optimizer không được tự chọn loss, thời gian hoặc năng lượng độc lập với lịch. C4–C5 suy ra $n_ub_{\min}\le B_u$.

$x$ trội $x'$ nếu cả hai khả thi, ba objective không lớn hơn và ít nhất một nhỏ hơn. Không đưa proxy gradient hay số client thành mục tiêu thứ tư.

Miền là hợp hữu hạn của các miền liên tục bị chặn; $b_{\min},f_{\min}>0$ loại điểm kỳ dị. Với loss hữu hạn, tham số hợp lệ và miền khả thi khác rỗng, tính đóng/liên tục theo mỗi assignment cho phép đạt nghiệm Pareto. Tuy nhiên không mặc định instance luôn khả thi.

Benchmark phải có một lịch witness đã kiểm tra. Trong episode, dùng witness còn khả thi làm fallback. Nếu không tìm được lịch, trả **NO_FEASIBLE_SCHEDULE_FOUND**, báo số vòng và chi phí đã thực hiện. Không đồng nhất thất bại của EA với chứng minh vô nghiệm. Chỉ dùng **PROVEN_INFEASIBLE** khi có chứng cứ giải đầy đủ trong miền được tuyên bố.

## 7. Rút gọn tài nguyên có chứng minh

### 7.1. Dùng hết băng thông trên UAV hoạt động

Đặt $a=P_m^{\rm tx}h_{mu}/(\Gamma N_0)>0$. Theo (A9):
$$
R'(b)=\frac{\eta_{\rm MAC}}{\ln2}
\left[\ln(1+a/b)-\frac{a}{a+b}\right]>0.
\tag{A17}
$$

Giữ $S,s,f$, phân phần phổ còn dư cho ít nhất một link hoạt động làm $v_m$ giảm, $d_{\rm svc},T$ không tăng. Năng lượng phát client giảm nghiêm ngặt; baseline, hover và năng lượng receiver không tăng. Các pha khác không đổi. Vì vậy mọi lịch để dư phổ ở UAV hoạt động bị một lịch dùng hết phổ trội trong mô hình này.

Có thể thay C5 bằng:
$$
\sum_mb_{mu}=B_uy_u.
\tag{A18}
$$

Mệnh đề cần $P_m^{\rm tx},L_m>0$, không có chi phí sử dụng phổ hoặc can nhiễu mới. Không khái quát sang mọi radio model.

### 7.2. CPU giải tích với một biến thời hạn

Giữ assignment và bandwidth. Đặt:
$$
T_0=D_0+D+A+H+A_0,\quad
d_{\min}=\max_{m\in S}(C_m/f_m^{\max}+v_m),\quad
d_{\max}=\max_{m\in S}(C_m/f_m^{\min}+v_m).
\tag{A19}
$$

Chọn:
$$
d\in[d_{\min},d_{\rm cap}],\qquad
d_{\rm cap}=\min(d_{\max},T_{\max}-T_0).
\tag{A20}
$$
$$
f_m^\star(d)=
\max\left(f_m^{\min},\frac{C_m}{d-v_m}\right),\quad m\in S;
\qquad f_m^\star=0\ (m\notin S).
\tag{A21}
$$

Nếu $d_{\rm cap}<d_{\min}$, assignment/bandwidth không đáp ứng deadline với bất cứ CPU khả thi nào. Không clip công thức vượt $f_{\max}$ rồi coi lịch hợp lệ.

**Chứng minh:** deadline service của từng client tương đương $f_m\ge C_m/(d-v_m)$. Vì $\kappa_mC_mf_m^2$ tăng theo $f_m>0$, (A21) là tần số tối thiểu thỏa bound. Trong (A20), $d>v_m$ và $f_m^\star\le f_m^{\max}$. Khi $d<d_{\max}$, có ít nhất một client dùng nhánh $C_m/(d-v_m)$, nên thời gian service thực bằng $d$; tại $d=d_{\max}$, client chậm nhất ở $f_{\min}$ cũng đạt $d$.

Với một lịch khả thi bất kỳ, lấy $d=d_{\rm svc}$. Thay $f$ bằng $f^\star(d)$ giữ service thực bằng $d$, giảm hoặc giữ từng năng lượng client; các pha và năng lượng UAV/coordinator giữ nguyên. Do đó không mất vector mục tiêu Pareto khi rút gọn CPU theo (A21). Pin cũng không xấu hơn.

**Giới hạn:** chứng minh dựa trên barrier và sổ năng lượng đã chốt. Nếu có công suất active CPU bổ sung phụ thuộc $C_m/f_m$, discrete DVFS, sleep mode, pipeline hoặc compute phụ thuộc seed, phải giải lại bài toán con. Không áp dụng công thức rồi giữ nguyên tuyên bố exact.

### 7.3. Biểu diễn triển khai

Dùng chromosome $(a,z,\xi)$:

- $a_m\in\{0,1,\ldots,U\}$: 0 inactive, $u$ gán vào UAV $u$.
- Trong nhóm $S_u$, $z_{mu}\ge0,\ \sum_{m\in S_u}z_{mu}=1$.
- $\xi\in[0,1]$, $d=d_{\min}+\xi(d_{\rm cap}-d_{\min})$.

$$
b_{mu}=b_{\min}+(B_u-n_ub_{\min})z_{mu}\quad(m\in S_u).
\tag{A22}
$$

Inactive nhận $b=0$. Nếu $n_ub_{\min}=B_u$, mọi client nhận $b_{\min}$; $z$ không ảnh hưởng. Dùng projection lên simplex hoặc trọng số không âm được chuẩn hóa, cho phép giá trị 0. Softmax với logit bị chặn chỉ mô tả một phần miền; không gọi đó là biểu diễn exact của toàn P-A.

Mutation $z,\xi$ và assignment tạo cấu hình mới; **decode lại toàn bộ** $D_0,D,A,H,A_0,d,f,E,T$. Không giữ d/CPU cũ sau swap thay đổi các pha khác.

Bản đối chứng A-FULL giữ gene CPU riêng:
$f_m=f_m^{\min}+\xi_m(f_m^{\max}-f_m^{\min})$.
So A-FULL/A-REDUCED với cùng operator chọn client và evaluator để đo riêng lợi ích giảm chiều.

## 8. Information contract

### 8.1. Ba đối tượng dữ liệu

| Đối tượng | Có thể chứa | Không cấp cho proposal |
| --- | --- | --- |
| ControllerView | Snapshot vật lý, hardware, pin, $p_m$, model ID, lịch sử/sketch hợp lệ | Dữ liệu train, validation, test; update hiện tại của client chưa chạy |
| ReferenceEvaluator | Dữ liệu train/search-validation, checkpoint đầy đủ, RNG, cache phản thực tế | Không tự đẩy gradient/update nội bộ sang ControllerView |
| AuditEvaluator | Audit-validation và seed audit độc lập | Kết quả audit không quay lại search, tuning hoặc lịch sử |

Trong A-REF, đề xuất ở iteration $t$ có thể phụ thuộc ControllerView, RNG và **các fitness đã trả qua API đến $t-1$**. Toàn bộ tìm kiếm vì vậy là oracle-assisted, kể cả khi proxy chỉ dùng history. Không tuyên bố rằng lịch cuối chỉ dựa trên thông tin có sẵn của một controller online.

Oracle trả loss replicates/mean và chi phí; không trả tensor update hoặc gradient nếu không chạy chế độ oracle diagnostic được ghi nhãn riêng.

### 8.2. Báo cáo lịch sử có nguồn gốc và chi phí

Mỗi client được chọn trong một vòng **được thực thi** tạo sketch tại model đầu vòng, trước local training:
$$
r_m^{\rm rep}=Q\,\widehat\nabla F_m(w_k;\zeta_m),
\quad Q\in\mathbb R^{d_s\times d}.
\tag{A23}
$$

$Q_{ij}$ là Rademacher $\pm1/\sqrt{d_s}$, seed phép chiếu dùng chung; $\zeta_m$ là seed minibatch báo cáo riêng, độc lập seed tìm kiếm. Payload report gồm sketch, model ID, thời điểm tạo, sample count và thông tin seed/protocol cần thiết. Một phép chiếu phải có cùng tọa độ/thứ tự tham số giữa client.

**Chốt overhead:** đặt
$$
C_m=C_m^{\rm SGD}+C_m^{\rm report},\quad
L_m=L_{\rm update}+L_m^{\rm report},\quad
L_u^{\rm bh}=L_{\rm aggregate}+\sum_{m\in S_u}L_m^{\rm report}.
\tag{A24}
$$

UAV forward report từng client cùng aggregate để coordinator có lịch sử client, thay vì chỉ biết aggregate. Metadata aggregation nằm trong payload tương ứng. Chi phí encode/forward của report nằm trong $C_m$ và hệ số aggregation đã profile. Mọi phương pháp trong cùng thí nghiệm dùng cùng overhead, kể cả baseline không tận dụng sketch.

Timestamp của report là thời điểm tạo xong phần công việc báo cáo, tính từ đầu pha service bằng C_report/f_m; model ID vẫn là w_k trước local SGD. Report được thêm vào history **sau khi lịch thực thi kết thúc**. Tạo report/update cho candidate phản thực tế không cập nhật history, pin, model hoặc đồng hồ. Không lấy cache oracle làm report miễn phí.

Snapshot benchmark có thể có history từ một trace quá khứ chung; lưu provenance và chi phí tạo trace. Episode bắt đầu rỗng thì guidance tự fallback cho đến khi có đủ history; không giả định một vòng all-client khả thi miễn phí.

## 9. Proxy set-aware xác định được với dữ liệu thiếu/cũ

Đây là proposal heuristic, không là objective thay thế và không cần học surrogate. Bản cơ sở **không** gán Gaussian posterior/covariance chưa được hiệu chuẩn.

### 9.1. Tập báo cáo hợp lệ

Đặt:
$$
\mathcal O_k=\left\{m:
\begin{array}{l}
\text{có report đúng protocol và phép chiếu }Q;\\
\tau_k-t_m^{\rm rep}\le a_{\max};\\
\|w_k-w_m^{\rm rep}\|/
 \max(1,\|w_m^{\rm rep}\|)\le\delta_{\max}
\end{array}\right\}.
\tag{A25}
$$

Model tạo report được xác định từ checkpoint history do coordinator có; không lấy gradient mới để kiểm tra. $a_{\max},\delta_{\max}$ là tham số chốt trước. Dữ liệu stationary không làm gradient cũ trở thành gradient hiện tại.

Với $S_O=S\cap\mathcal O_k$, nếu $S_O\ne\varnothing$:
$$
\bar r_O=\frac{\sum_{m\in\mathcal O_k}p_mr_m^{\rm rep}}{P_{\mathcal O_k}},
\quad
r_{S_O}=\frac{\sum_{m\in S_O}p_mr_m^{\rm rep}}{P_{S_O}},
\quad
\widehat D_O(S)=\|r_{S_O}-\bar r_O\|^2.
\tag{A26}
$$

Đây là mismatch của **phần quần thể có thông tin**, không phải ước lượng không chệch của gradient toàn bộ quần thể. Khi $\mathcal O_k=\mathcal M$ và report mới/chính xác, nó trở thành projected population mismatch quen thuộc. Trọng số $p_m$ của objective (A3) không thay đổi; chỉ proxy được chuẩn hóa trên phần có báo cáo.

Luôn log $P_{\mathcal O_k}$, $|\mathcal O_k|/M$, tỷ lệ proposal fallback, tuổi report và model drift. Không so kết quả history-guided với oracle-guided mà che mức độ quan sát.

### 9.2. Guided swap

1. Với xác suất $\rho\in(0,1)$, thử guidance; còn lại dùng generic mutation.
2. Guidance chỉ thử $i\in S\cap\mathcal O_k$, $j\in\mathcal O_k\setminus S$. Nếu không có cặp, fallback generic; không tự tạo sketch cho client chưa biết.
3. Lấy tối đa $c_{\rm swap}$ bộ $(i,j,u)$ khác nhau có xác suất dương đều trên tập hợp hợp lệ cấu trúc. UAV $u$ có $e_{ju}=1$, đủ chỗ $n_ub_{\min}\le B_u$ sau swap; giữ các client khác.
4. Tính (A26) cho $S'=S\setminus\{i\}\cup\{j\}$. Nếu có cải thiện, chọn mismatch nhỏ nhất; tie theo bộ ID cố định. Nếu không, lấy một đề xuất ngẫu nhiên.
5. Đưa client mới vào UAV $u$, cho trọng số bandwidth khởi tạo $1/|S'_u|$, chuẩn hóa các trọng số còn lại; giải mã toàn bộ và kiểm tra thật.
6. Quyết định sống sót dựa trên feasibility và ba objective tham chiếu. Proxy giảm không đồng nghĩa child sống sót.

Khi đổi $i\to j$:
$$
P_{S'_O}=P_{S_O}-p_i+p_j,\qquad
G_{S'_O}=G_{S_O}-p_ir_i^{\rm rep}+p_jr_j^{\rm rep}.
\tag{A27}
$$
Không giữ nguyên mẫu số khi $p_i\ne p_j$. Với $G_{S_O}$ đã cache, mỗi candidate swap tốn $O(d_s)$.

Generic mutation phải có add, drop, swap, reassign, bandwidth và thời hạn; tất cả client đủ điều kiện vật lý có xác suất được đề xuất dương. Điều này duy trì khám phá trong **proposal**, không bảo đảm mỗi client sẽ được chọn thực thi hoặc fairness lâu dài. Fairness cứng nếu cần phải thêm vào một phiên bản bài toán khác.

### 9.3. Lý do lý thuyết và giới hạn

Với gradient đầy đủ hiện tại, $g_m=\nabla F_m(w)$,
$\bar g=\sum_mp_mg_m$, $g_S=\sum_{m\in S}p_mg_m/P_S$,
$D(S)=\|g_S-\bar g\|^2$.

Nếu $F_{\rm pop}$ có gradient $\beta$-Lipschitz, một bước full-gradient với $\eta=1/\beta$ cho:
$$
F_{\rm pop}(w-\eta g_S)
\le F_{\rm pop}(w)-\frac1{2\beta}
 \left(\|\bar g\|^2-D(S)\right).
\tag{A28}
$$

Suy ra từ descent lemma và
$2\langle\bar g,g_S\rangle-\|g_S\|^2
=\|\bar g\|^2-\|g_S-\bar g\|^2$.
Đây là bound **training loss một bước**, không chứng minh validation nhiều bước.

Một phát biểu sát local SGD hơn dùng update thực:
$$
D_\Delta(S)=\|\Delta_S-\Delta_{\rm all}\|^2,\quad
\Delta_S=\sum_{m\in S}\frac{p_m}{P_S}\Delta_m,\quad
\Delta_{\rm all}=\sum_mp_m\Delta_m.
\tag{A29}
$$
Nếu $L_v$ là $G_v$-Lipschitz trên đoạn nối hai model:
$$
|L_v(w+\Delta_S)-L_v(w+\Delta_{\rm all})|
\le G_v\sqrt{D_\Delta(S)}.
\tag{A30}
$$

Bound chỉ nói gần update all-client, không nói all-client là nghiệm tốt nhất hay mismatch nhỏ hơn luôn có loss nhỏ hơn. $D_\Delta$ hiện tại thuộc diagnostic oracle, không có sẵn cho proposal lịch sử.

Nếu $\nabla F_m$ là $L_m^g$-Lipschitz thì:
$$
\|\nabla F_m(w_k)-\nabla F_m(w_m^{\rm rep})\|
\le L_m^g\|w_k-w_m^{\rm rep}\|.
\tag{A31}
$$
Đây là motivation cho model-drift gate; $\delta_{\max}$ không tự trở thành bound thống kê khi chưa biết $L_m^g$, minibatch noise và sai số projection. Không tuyên bố JL bảo đảm cho toàn bộ tập ứng viên thích nghi chỉ bằng cách thay số candidate vào một bound hữu hạn.

## 10. Evaluator, cache và constraint handling

### 10.1. Trình tự đánh giá bắt buộc

1. Validate shape, số hữu hạn, protocol ID và tham số scenario.
2. Decode association; sửa **cấu trúc** nếu thuật toán quy định: mask, cardinality, capacity.
3. Decode bandwidth theo (A22); tính mọi pha trừ CPU; tính $d_{\min},d_{\rm cap}$.
4. Nếu khoảng d rỗng: đánh dấu deadline-infeasible. Có thể dùng $f_{\max}$ để tính lower-bound violation và diagnostic physical costs, nhưng không gọi reference loss.
5. Nếu khoảng hợp lệ: decode d, CPU; tính service thực, toàn bộ $T$, từng $E_i$, rồi vector residual.
6. Chỉ lịch khả thi mới được gọi learning evaluator/cached loss.
7. Lưu record; evaluator không cập nhật state nguồn.

Repair không được tùy tiện bỏ client để “sửa pin” mà không tính lại tất cả pha. Bản cơ sở chỉ repair cấu trúc, xử lý deadline/pin bằng feasibility dominance. Mutation và repair của baseline/set-aware phải giống nhau ngoài bước guided proposal.

### 10.2. Residual và tolerance

Với mọi bất đẳng thức $g_j(x)\le0$, định nghĩa:
$$
CV(x)=\sum_j\max\left(0,\frac{g_j(x)-\epsilon_j}{\sigma_j}\right).
\tag{A32}
$$

$\sigma_j>0$ cố định theo đơn vị: $T_{\max}$ cho thời gian, $B_u$ cho băng thông, một thang năng lượng scenario cho pin; không chia cho available battery bằng 0. $\epsilon_j$ là tolerance số học theo cùng đơn vị, không phải mức cho phép vi phạm ứng dụng.

- Feasible trội infeasible.
- Hai feasible: nondominated sorting trên loss–energy–time.
- Hai infeasible: CV nhỏ hơn được ưu tiên; tie dùng diversity/ID đã định.
- NaN/Inf/assignment sai kiểu bị reject, không đặt loss giả bằng 0.
- Infeasible có loss null; không đưa vào Pareto archive hoặc crowding feasible.
- Lưu cả residual chưa trừ tolerance để người đọc thấy sai lệch thật.

### 10.3. Hai lớp cache

**Update cache:** key gồm checkpoint hash, client ID, train split/hash, local optimizer config, seed, model/software version. Value là local update dùng nội bộ evaluator; lazy compute theo nhu cầu.

**Loss cache:** key gồm checkpoint, tập client canonical đã sort, $p_m$, aggregation protocol, seed bundle, validation split/hash và model/software version. Resource/association không nằm trong key chỉ khi tính tách biệt đã được xác minh.

Một resource variant cùng $S$ vẫn phải tính lại vật lý và constraints. Search và audit có namespace riêng. Không làm tròn tài nguyên rồi cache vật lý thiếu kiểm soát gần biên deadline/pin.

Các phương pháp có cache lạnh riêng nhưng cùng policy; không cho phương pháp chạy sau hưởng cache đã được phương pháp trước trả phí. Nếu precompute dùng chung, mọi phương pháp phải được phân bổ cùng chi phí khởi tạo và báo rõ.

## 11. Thuật toán và budget

### 11.1. Khung thuật toán

NSGA-II là framework ban đầu; novelty cần nằm ở cơ chế đề xuất được kiểm chứng, không ở việc dùng framework.

1. Tạo population từ witness, lịch ngẫu nhiên nhiều cardinality và một số lịch channel-greedy; giữ cùng initialization khi so operator.
2. Decode, đánh giá vật lý, gọi reference loss cho tập khả thi chưa cache.
3. Tournament theo constraint dominance, Pareto rank và crowding.
4. Crossover association theo từng client; crossover simplex/d bằng quy tắc đã chốt.
5. Dùng guided/generic mutation theo Mục 9; mutation tài nguyên.
6. Decode/repair/evaluate; environmental selection từ parent và offspring.
7. Cập nhật archive các lịch khả thi, đã có reference fitness. Cùng tập client có thể giữ nhiều cấu hình tài nguyên không trội.
8. Khi hết budget, khóa kết quả search; chọn lịch thực thi theo rule Mục 12. Audit phục vụ báo cáo riêng.

Nếu một objective có range 0 trong front, bỏ contribution crowding của objective đó; không chia cho 0. Tối thiểu lưu một đại diện cho duplicate toàn bộ objective/decision.

### 11.2. Budget hữu hạn, kể cả khi cache hit

Thí nghiệm chính dùng tổng wall time tìm kiếm trên cùng máy, worker count và số luồng; tính cả đề xuất, decode, cache miss, aggregation, validation và selection. Log thêm CPU/GPU-seconds, số tập duy nhất, local-update cache miss, số candidate vật lý và thời gian chờ.

Đặt thêm giới hạn proposal $N_{\rm prop}^{\max}$ để chắc chắn kết thúc. Budget số tập duy nhất là chỉ số phụ, không đủ kiểm soát các resource variants dùng cache. Khi hết budget tập mới vẫn có thể tinh chỉnh tài nguyên cho tập đã cache trong thời gian còn lại.

Đánh giá một seed bundle là đơn vị nguyên tử. Chỉ bắt đầu khi còn budget; nếu call cuối vượt thời gian dự toán, log toàn bộ overrun và dùng chi phí thực trên đường HV–cost. Không trộn candidate mới chỉ chạy một phần seed với các candidate đầy đủ. Audit có ngân sách đặt trước riêng và không cấp thêm search budget khi thuật toán ít nghiệm.

Phải báo CPU/GPU và chính sách lazy cache; một unique-set evaluation không nhất thiết có cùng chi phí với một tập khác.

## 12. Audit, lựa chọn lịch và chạy nhiều vòng

### 12.1. Hai đầu ra khác nhau

- **Search archive:** dựa trên search-validation và $\Omega_{\rm search}$, được phép dùng để chọn lịch.
- **Audited archive:** nghiệm từ search được đánh giá lại trên audit-validation và $\Omega_{\rm audit}$, dùng để báo cáo chất lượng.

Audit không chạy thêm tối ưu; không đưa loss audit trở lại mutation, history, tuning hay lựa chọn lịch trong episode. Mỗi thuật toán audit mọi phần tử của search archive cuối; loss audit chỉ tính một lần cho mỗi tập S. Nếu cần giới hạn archive, chốt cap và quy tắc thinning chỉ dùng search objectives trước khi mở audit.

Sau audit, tính lại nondominance trên chính các nghiệm đã audit. Đây là **empirical nondominated archive dưới giao thức audit**, không phải chứng minh Pareto front thật. Candidate bị trội trong search có thể trở nên tốt khi audit; vì vậy nên lưu thêm log tất cả nghiệm để đánh giá độ nhạy của candidate pool nếu ngân sách cho phép, theo quy tắc đặt trước.

Không đặt điều kiện “nếu audit kém thì quay lại search”. Nếu dùng audit để thay thiết kế, scenario đó trở thành development scenario và cần một bộ đánh giá mới cho báo cáo cuối.

### 12.2. Chọn một lịch để thực thi

Đặt scale $c_L,c_E,c_T>0$ và trọng số $\lambda_j>0,\sum_j\lambda_j=1$ trước thí nghiệm. Dùng search archive:
$$
x_k^\star=\arg\min_{x\in\mathcal A_k^{\rm search}}
\left[
\lambda_L\frac{\widehat J_L^{\rm search}(S(x))}{c_L}
+\lambda_E\frac{E(x)}{c_E}
+\lambda_T\frac{T(x)}{c_T}
\right].
\tag{A33}
$$

Tie theo time, energy rồi candidate hash. Đây là **quy tắc triển khai từ tập Pareto**, không thay P-A thành một bài toán đơn mục tiêu trong search. Có thể báo nhiều preference, nhưng chạy episode riêng cho từng preference. Không chọn $\lambda$ sau khi xem final test.

Scale cố định theo scenario family hoặc pilot độc lập, không cập nhật bằng min/max của archive mỗi round. Nếu snapshot chất lượng học khác nhau, không gộp raw losses thành một front duy nhất.

### 12.3. Thực thi trong simulator

1. Chọn lịch bằng (A33) trước khi mở audit.
2. Dùng một seed execution độc lập với search/audit để tạo update thực của vòng. Không “thực thi” model trung bình của nhiều seed SAA.
3. Cập nhật $w_{k+1}$, $\tau_{k+1}=\tau_k+T(x_k^\star)$ và pin theo (A15).
4. Chỉ thêm report của client thực sự tham gia vào history.
5. Tạo snapshot mới, mất hiệu lực cache learning của checkpoint cũ.
6. Dừng khi đạt K vòng hoặc không còn tìm thấy lịch khả thi; báo đầy đủ failure/censored time-to-target.

Nếu khởi tạo history bằng warm-up, mọi phương pháp có cùng warm-up, và episode totals chứa thời gian/năng lượng đó. Snapshot-only có thể condition trên history đã cho nhưng phải báo riêng chi phí dựng history.

Vì A-REF dùng counterfactual oracle, episode này vẫn là **offline oracle-assisted reference rollout**. Kết quả nhiều vòng kiểm tra tính myopic và trade-off, không chứng minh khả năng chạy real time hoặc giải tối ưu full-horizon.

### 12.4. Đo chất lượng Pareto

Dùng objective audit cùng normalization và một reference point cố định để tính hypervolume. Chọn scale/reference point từ development scenarios; kiểm tra điểm được báo nằm trong box đã định. Điểm nằm ngoài box được báo số lượng và không lén thay reference point theo từng phương pháp.

IGD chỉ dùng khi có reference front đáng tin; pooled audited front ở quy mô lớn phải ghi là empirical approximation. So sánh thống kê ghép cặp theo scenario–seed; các candidate trong cùng snapshot không phải các quan sát độc lập.

Báo ít nhất: audited HV theo actual search cost; final test loss/accuracy; macro-F1/rare-class recall; năng lượng/thời gian; vi phạm deadline và pin; tần suất tham gia; độ phủ history; cache hits/misses. Tách search cost, audit cost và execution cost.

## 13. Mở rộng mobility: phiên bản riêng, không thay ngầm mô hình cơ sở

### 13.1. Prescribed motion

Cho $\mathbf q_u(t)$ và trace công suất propulsion $P_u^{\rm fly}(t)\ge0$, không phải biến quyết định. Client có thể giữ cố định. Trace phải đủ dài cho episode và có quy tắc hết trace.

$$
h_{mu}(t)=\beta_0/\|\mathbf q_u(t)-\mathbf r_m\|^2,\qquad
E_u^{\rm fly}=\int_{\tau_k}^{\tau_k+T}P_u^{\rm fly}(t)\,dt.
\tag{A34}
$$

Thay $P_u^{\rm hov}T$ bằng tích phân, không cộng cả hai. Tất cả thuật toán dùng cùng trace theo physical time, không đánh chỉ số trace bằng số round.

### 13.2. Dynamic upload

Client bắt đầu upload tại
$t_s=\tau_k+D_0+D+C_m/f_m$. Thời điểm kết thúc là nghiệm nhỏ nhất:
$$
t_e=\inf\left\{t\ge t_s:
\int_{t_s}^t R_{m,a_m}(b_{m,a_m};z)\,dz\ge L_m\right\}.
\tag{A35}
$$

Nếu không đủ payload trước deadline/trace end, lịch infeasible; không dùng rate cuối vòng nhân thời gian. Năng lượng phát $P_m^{\rm tx}(t_e-t_s)$; service lấy max thời điểm hoàn thành trừ thời điểm bắt đầu pha.

Downlink động phải dùng một giao thức broadcast đã định; ví dụ rate tức thời bằng min rate của các receiver, rồi tích phân lượng bit chung. Backhaul nếu giữ fixed-rate phải ghi là hạ tầng ổn định riêng. Eligibility cần có nghĩa suốt truyền hoặc outage phải khiến lịch thất bại theo quy tắc cụ thể.

**CPU reduction (A21) không được mặc định còn exact:** khi CPU đổi thời điểm bắt đầu upload, rate tích phân đổi. Phiên bản dynamic dùng A-FULL hoặc giải riêng bài toán con. Tính tách biệt loss vẫn giữ cho những lịch có cùng S hoàn thành thành công và cùng local work; thất bại làm thay đổi tập tổng hợp thì phải đổi cache rule.

### 13.3. Kiểm tra frozen-channel approximation

Với tốc độ UAV không quá $v_{\max}$, client đứng yên, khoảng cách đầu vòng $d_0$, và $\zeta=v_{\max}T/d_0<1$:
$$
(1+\zeta)^{-2}\le h(t)/h(\tau_k)\le(1-\zeta)^{-2}.
\tag{A36}
$$

So sánh cùng lịch trên static/frozen/dynamic evaluators, báo lỗi time/energy, feasibility flips và đảo thứ hạng. Ngưỡng chấp nhận phải đặt trước theo ứng dụng; không coi một ngưỡng phần trăm trong báo cáo là định lý. Dynamic-channel audit là **kiểm tra sai mô hình vật lý**, không gọi nó là Direction B chỉ vì tốn tính toán hơn.

## 14. Scenario và cấu hình khởi đầu

### 14.1. Manifest bắt buộc

| Nhóm | Các trường cần chốt |
| --- | --- |
| Model | Architecture, parameter order/count, precision, checkpoint hash, non-parameter state policy |
| Data | Dataset/version, bốn split/hash, partitions, $p_m$, IID/Dirichlet config, rare/noisy groups |
| FL | Local steps, minibatch, learning rate, optimizer reset, augmentation/RNG policy |
| Geometry | Tọa độ client/UAV, altitude, mask, channel mode, trace nếu có |
| Radio | $B_u,b_{\min},P_m^{tx},N_0,\beta_0,\eta_{\rm MAC},\Gamma$, rates DL/BH, payload bits |
| Cost | $C^{SGD},C^{report},\kappa,f_{\min/\max}$, baseline/incremental powers, aggregation coefficients |
| Constraints | Deadline, Nmax, pin/reserve từng nút, tolerance và scale residual |
| History | Provenance, timestamps, model IDs, Q seed/dimension, age/model-drift thresholds |
| Search | Population, crossover/mutation, rho, swap budget, proposal cap, wall budget, cache mode |
| Evaluation | Search/audit/execution seed bundles, preference scales/weights, HV point, archive cap |
| Reproducibility | Scenario ID, partition/MOEA seeds, code commit, library versions, hardware, workers |

Scenario thiếu trường bắt buộc hoặc có unit mâu thuẫn phải bị reject; không để evaluator tự điền các giá trị “hợp lý” không được log.

### 14.2. Pilot cụ thể để bắt đầu code

Các số dưới đây là **synthetic defaults để kiểm tra phần mềm**, chưa là thông số đo từ thiết bị hoặc thiết lập đủ cho claim thực nghiệm.

| Nhóm | Giá trị đề xuất |
| --- | --- |
| Quy mô | $M=6,U=2,N_{\max}=4$; CPU/radio đồng nhất trước khi thêm heterogeneity |
| UAV (m) | $(0,0,100)$, $(200,0,100)$ |
| Client (m, mặt đất) | $(-80,-40)$, $(0,40)$, $(70,-20)$, $(130,50)$, $(220,-40)$, $(300,30)$ |
| Mask | $e_{mu}=1$ nếu khoảng cách 3D không quá 350 m; rates DL/BH dương |
| Uplink | $B_u=2\cdot10^6$ Hz, $b_{\min}=5\cdot10^4$ Hz, $P_m^{tx}=0.1$ W |
| Channel | $\beta_0=10^{-4},N_0=4\cdot10^{-20}$ W/Hz, $\eta_{\rm MAC}=0.8,\Gamma=1$ |
| CPU | $f_{\min}=0.5\cdot10^9,\ f_{\max}=2\cdot10^9$ cycles/s; $\kappa=10^{-28}$ |
| Công việc | $C^{SGD}=10^8,\ C^{report}=10^6$ cycles/client/vòng; sau pilot phải profile theo model/I/batch |
| Rates | $r^{0u}=r^{u0}=20\cdot10^6$, $r^{um}=5\cdot10^6$ bit/s |
| Aggregation | $a_u^{(0)}=0.002,a_u^{(1)}=0.001;\ a_0^{(0)}=0.002,a_0^{(1)}=0.001$ s |
| Baseline | Client 0.05 W; UAV điện tử 5 W; coordinator 20 W; hover 80 W/UAV |
| Increment radio/compute | Client rx 0.05 W; UAV rx 0.2 W, tx DL/BH 1 W, agg 2 W; coordinator tx 2 W, rx 0.5 W, agg 5 W |
| Pin/reserve | Client 1000/100 J; UAV 20000/2000 J; coordinator điện lưới |
| Deadline | $T_{\max}=5$ s |
| FL | Fashion-MNIST, SGD lr 0.01, I=5, batch=32, không augmentation/dropout |
| Search | N=64; rho=0.5; tối đa 16 guided tuples/proposal; tối đa 10000 proposals |
| Budget | 60 s/snapshot pilot; 1 worker; log overrun; snapshot tiny có thể dừng khi hết không gian restricted |
| Seeds | $R_{\rm search}=3,\ R_{\rm audit}=10$, execution seed độc lập; R=1 chỉ cho debug |
| History | $d_s=64,a_{\max}=30$ s, $\delta_{\max}=0.1$; ban đầu rỗng nếu chưa có warm-up |
| Preference | $c_L=\ln10,c_E=1000$ J, $c_T=5$ s; $\lambda=(1/3,1/3,1/3)$ |

CNN pilot: Conv(1→16, 3×3, padding 1)–ReLU–MaxPool2; Conv(16→32, 3×3, padding 1)–ReLU–MaxPool2; Flatten(1568)–Linear64–ReLU–Linear10. Có bias ở các Conv/Linear, tổng $d=105866$ tham số. Cross-entropy từ logits. $L_w=L_{\rm update}=32d$ bits; $L_m^{report}=32d_s+256$ bits; $L_{\rm aggregate}=32d+256$ bits. Payload toàn bộ theo (A24).

Split pilot: từ 60000 mẫu training chuẩn lấy stratified 48000 train, 6000 search-validation, 6000 audit-validation; 10000 test chuẩn để test cuối. Pilot đầu chia IID, sau đó dùng partition non-IID được lưu rõ; mọi validation client phải không rỗng. Với partitions làm tròn lệch kích thước, tính $p_m$ từ train và dùng đúng (A3). Không lấy audit/test để tạo proxy.

Các seed phải được lưu trong manifest, ví dụ dataset split=101, Q=202, MOEA=303; namespace search/audit/execution khác nhau. Seed số giống nhau ở namespace khác phải được hash khác nhau.

Khởi tạo witness bằng thử tuần tự singleton client–UAV với toàn bandwidth và d trong khoảng hợp lệ, kiểm tra pin/deadline. Nếu chỉ thử hữu hạn giá trị d mà chưa tìm được singleton khả thi, chưa được kết luận infeasible: có thể bỏ sót khoảng d thỏa pin. Dùng bộ tìm khả thi có kiểm chứng hoặc generator tạo lại instance và ghi lý do. Trong mô hình cơ sở, bỏ client khỏi một lịch khả thi rồi giữ tài nguyên của client còn lại không làm chi phí tăng; vì vậy có thể dùng kiểm tra singleton đầy đủ như một chứng cứ tồn tại lịch khả thi, nhưng phép quét d thưa không phải kiểm tra đầy đủ.

Sau pilot, thay các hệ số cycles/power bằng đo/profiling, mở rộng IID/non-IID, client hiếm ở link yếu và label noise. Khi đổi I/batch/model mà giữ C không đổi, phải ghi là cost model tổng hợp; không dùng để kết luận hiệu quả năng lượng phần cứng thật.

## 15. Giao diện triển khai và nghiệm thu

### 15.1. API tối thiểu

- **get_controller_view(snapshot_id)** → public physical state + permitted history.
- **decode(snapshot_id, chromosome)** → schedule, structural errors, decoded quantities.
- **evaluate_physics(snapshot_id, schedule)** → phase times, per-node ledger, E, T, raw residuals, CV.
- **reference_loss(snapshot_id, selected_set, search_protocol_id)** → per-seed losses, mean, cost, cache status.
- **audit_loss(snapshot_id, selected_set, audit_protocol_id)** → audit result; gọi sau khóa search.
- **execute_one(snapshot_id, schedule, execution_seed)** → snapshot mới; đây là nơi duy nhất cập nhật w, clock, batteries và history.

Không đưa toàn bộ SimulatorTruth vào constructor của proposal operator. Audit và test không đi qua API reference search. Unit/data-access checks cần kiểm tra điều này, không chỉ dựa vào convention.

### 15.2. Record mỗi candidate

Lưu snapshot/checkpoint IDs; parent/operator; selected-set hash; association; bandwidth/d/CPU; phase times; per-node energy và từng thành phần; raw constraints/CV; search seed bundle/split; per-seed loss/mean; cache hit/miss; wall/GPU/CPU cost; history coverage; proxy score nếu có; status feasible/reference-evaluated/audited. Khi infeasible, loss là null.

Model update/report không nằm trong record công khai của optimizer. Log test kết thúc episode ở luồng riêng, không làm nguồn feedback cho search.

### 15.3. Các kiểm tra phải đạt trước benchmark thuật toán

1. **Aggregation:** hierarchical và flat aggregation cùng $p_m/P_S$ khớp trong tolerance; UAV rỗng không chia 0.
2. **Set separability:** đổi assignment/bandwidth/CPU với cùng S và seed, model/loss không đổi khi mọi lịch khả thi.
3. **Inactive masking:** không tính rate tại b=0; inactive không có training/upload energy, baseline vẫn đúng cấu hình.
4. **Timeline:** ca compute=1/3 s, upload=4/1 s cho hai client tạo service=max(5,4)=5 s, không phải max(1,3)+max(4,1)=7 s.
5. **Đơn vị CPU/radio:** $C=10^8,\kappa=10^{-28},f=10^9,L=2\cdot10^6,R=10^7,P=0.1$ cho compute 0.1 s/0.01 J, uplink 0.2 s/0.02 J. Đây là chi phí local tăng thêm, chưa gồm các pha/baseline.
6. **Resource reduction:** tăng bandwidth dư không làm E/T xấu đi; (A21) có service thực bằng d, CPU đúng miền và không xấu hơn lịch gốc cùng d.
7. **Pin:** tổng ledger bằng objective, pin trừ đúng nút; UAV rỗng vẫn hover; coordinator không bị trừ vào pin UAV.
8. **Cache/provenance:** đổi checkpoint, p, split, seed hoặc protocol phải miss tương ứng; evaluate không sửa snapshot/history.
9. **Information:** client không có report không xuất hiện trong proxy với giá trị 0; fallback/generic có thể đề xuất client đó; audit không ảnh hưởng search.
10. **SAA/audit:** candidate dùng cùng số seed hoàn chỉnh; audit độc lập; execution dùng một seed riêng.
11. **Tiny exact restricted:** với 6 client có 63 tập không rỗng trước giới hạn Nmax; với 2 UAV có 728 assignment không rỗng trước mask/cardinality. Liệt kê với cùng allocator cố định hoặc finite grid để đối chiếu archive.
12. **Dominance:** kiểm tra trên các vector mục tiêu nhân tạo biết trước, duplicate và objective range=0.

Các con số 63/728 là kích thước **trước** lọc; nghiệm enumeration chỉ exact trong miền restricted đã định, không là lời giải exact cho tài nguyên liên tục.

### 15.4. Thiết kế đối chứng

- Cặp chính: generic NSGA-II và set-aware NSGA-II, cùng initialization, representation, resource mutation, repair, survival, cache và budgets; chỉ đổi guidance.
- A-FULL và A-REDUCED để cô lập CPU reduction.
- Random feasible search và MOEA/D với cùng evaluator/miền.
- Client selectors channel-only, individual-gradient score và một set-based selector với cùng resource allocator để cô lập giá trị chọn tập.
- History-guided so với fresh-oracle diagnostic; fresh oracle được gắn nhãn đầy đủ thông tin, không là đối thủ online công bằng.
- Proxy correlation theo từng snapshot; không giả định mismatch nhỏ bảo đảm loss thấp.
- Đánh giá energy–time correlation và phần hover để phát hiện mục tiêu gần dư thừa.
- Dùng scenario/seed ghép cặp, báo độ phân tán và confidence interval; số lần chạy chính được xác định từ pilot variance/budget, không coi một ngưỡng effect size trong báo cáo là bảo đảm thống kê.

## 16. Phạm vi kết luận và các điểm cố ý chưa mở rộng

Đặc tả này chốt một bài toán có thể triển khai: **một vòng, fixed local work, reference SAA loss, ba mục tiêu, đầy đủ timeline/ledger, feasibility, historical proposal và audit**.

Các kết quả giải tích về cache, bandwidth và CPU giúp tránh lãng phí tính toán; bản thân chúng chưa chứng minh thuật toán tiến hóa hội tụ tới Pareto front toàn cục. Random mutation duy trì cơ hội đề xuất, không tạo bảo đảm fairness hay hội tụ hữu hạn.

Partial-history proxy (A26) là lựa chọn bảo thủ để xử lý dữ liệu thiếu mà không cần posterior giả định. Báo cáo đề xuất expected mismatch có covariance; hướng đó chỉ nên thêm khi đã chỉ rõ mô hình joint uncertainty, dữ liệu hiệu chuẩn và cross-covariance. Không trình bày điểm phạt tuổi thông tin tùy ý như một kỳ vọng Bayesian.

Không thêm multi-fidelity, adaptive probing, trajectory optimization hoặc packet-loss modeling trong code bản cơ sở. Khi mở rộng, tăng protocol/model version và xem lại mọi mệnh đề có điều kiện. A-REF cung cấp mốc tham chiếu cho các bước đó, chưa là kết quả chứng minh tính mới của bài báo.

## 17. Nguồn và cách sử dụng

1. [Direction_A_Research_Review.md](Deep%20Report/Direction_A_Research_Review.md): các khoảng trống learning objective, information, accounting, guided swap và baseline.
2. [Direction_A_Research_Report_VI.md](Deep%20Report/Direction_A_Research_Report_VI.md): phân biệt A-REF/deploy, separability, bandwidth/CPU reduction, missing/stale sketch và audit.
3. [JNCA_Huy.pdf](../../docs/developing%20directions/JNCA_Huy.pdf): mô hình và định hướng A/B/C gốc, đặc biệt Mục 2–6 và 9–10.
4. [FSTPO](../../docs/source%20idea/Federated_Spatio-Temporal_Policy_Learning_for_Efficient_Resource_Management_in_UAV-Assisted_IoT_Edge_Networks.pdf): kiến trúc tham khảo và liên hệ lựa chọn thiết bị–tài nguyên.
5. [McMahan và cộng sự, AISTATS 2017](https://proceedings.mlr.press/v54/mcmahan17a.html), [bản v4 nội bộ](../../docs/1602.05629v4.pdf): nền tảng local SGD và model averaging. Công thức selected-set normalization trong tài liệu này theo bản v4 và draft.
6. Các nguồn related work khác được giữ trong hai báo cáo; tài liệu này không xác nhận thay metadata hoặc tuyên bố novelty từ các bảng tổng hợp đó.

**Trình tự triển khai:** scenario/schema → physical evaluator → FL/reference/cache → exact restricted benchmark → generic NSGA-II → set-aware operator → independent audit → episode và mobility.
