# Direction A v2 — Mô hình bài toán và thuật toán NSGA-II

**Ngày cập nhật:** 12/11/2026.  
**Ý tưởng đầu vào:** [raw-idea.txt](raw-idea.txt).  
**Mô hình nền:** [research draft JNCA](../../../../docs/developing%20directions/JNCA_Huy.pdf), mục 2–5.  
**Mục đích:** đặc tả mô hình toán và thuật toán để triển khai v2.

## 1. Phạm vi và các lựa chọn triển khai

Hệ thống gồm M client mặt đất, U UAV lơ lửng mang bộ tổng hợp và một coordinator/server mặt đất. Mỗi vòng chọn ít nhất một và tối đa N_max client. Một client được chọn truyền model update cho đúng một UAV, một UAV có thể phục vụ nhiều client. Mọi client đều được phép kết nối với mọi UAV. Tập client được chọn có thể thay đổi giữa các vòng.

V2 dùng NSGA-II để tìm các lịch có đánh đổi giữa chất lượng học, năng lượng và thời gian. Cá thể biểu diễn quyết định chọn client/gán UAV, bandwidth và CPU frequency bằng ba vector. Sau mỗi lần tìm kiếm, hệ thống chọn một lịch thực thi, cập nhật model, đồng hồ và chi phí tích lũy rồi chuyển sang vòng FL kế tiếp.

Các lựa chọn làm rõ những chi tiết còn để mở trong raw idea được chốt như sau.

| Thành phần | Lựa chọn cho v2 |
| --- | --- |
| Số vòng FL | K vòng, chỉ số k=0,…,K−1 |
| Số client mỗi vòng | 1<= số client được chọn <=min(N_max,M) |
| Thuật toán | NSGA-II với biến rời rạc và liên tục |
| UAV | Lơ lửng tại vị trí cố định trong suốt phiên |
| Kết nối | Mọi cặp client–UAV đều được phép association |
| Kênh cơ sở | Effective channel gain cố định trong vòng, upload của lịch khả thi thành công |
| Radio | Pool uplink độc lập giữa UAV, OFDMA trong mỗi pool |
| Local training | I bước SGD, batch size và learning rate đã khai báo |
| Trọng số FL | Theo tỷ trọng quần thể cố định, chuẩn hóa trên tập tham gia |
| Probing | Theo raw idea, giao thức chỉ gồm training và feedback từ các vòng đã thực thi |
| Chi phí vật lý | Local compute, radio, downlink, aggregation, backhaul và baseline điện tử |
| Môi trường tìm kiếm | Reference simulator offline, checkpoint nguồn bất biến trong mỗi lần search |
| Đánh giá cuối phiên | Accuracy của model cuối, tổng năng lượng và tổng thời gian của các lịch đã thực thi |
| Chọn lịch | Preference cố định trước khi chạy, áp dụng cho archive mỗi vòng |
| Trường hợp thiếu lịch khả thi | Tìm fallback đã kiểm tra, ghi nhận phiên dừng nếu vẫn thất bại |

K dùng cho số vòng FL, G dùng cho số thế hệ NSGA-II và D_k dùng cho thời lượng vật lý vòng k. Quy ước này tránh dùng T cho cả ba đại lượng.

## 2. Ký hiệu và đầu vào

| Ký hiệu | Miền hoặc đơn vị | Ý nghĩa |
| --- | --- | --- |
| M, U, K, G, N_pop | Số nguyên dương | Số client, UAV, vòng FL, thế hệ và population size |
| N_max | Số nguyên, 1<=N_max<=M | Số client tham gia tối đa |
| m thuộc calM, u thuộc calU | calM={1,…,M}, calU={1,…,U} | Chỉ số client và UAV |
| q_u=(x_u,y_u,H_u), r_m=(x_m,y_m,0) | m, H_u>0 | Tọa độ UAV và client |
| w_k thuộc R^d_w | Tham số model | Global model đầu vòng k |
| D_m, V_m | Tập mẫu | Local training và validation của client m |
| n_m, p_m | Số mẫu, không thứ nguyên | Kích thước training và trọng số quần thể |
| s_mu^k, s_m^k, y_u^k | {0,1} | Gán client–UAV, chọn client, UAV có nhóm hoạt động |
| b_mu^k, B_u, b_min | Hz | Bandwidth link, pool UAV và bandwidth tối thiểu |
| f_m^k, f_m^min, f_m^max | cycle/s | CPU frequency và giới hạn phần cứng |
| C_m | cycle | Công việc cho I bước local SGD |
| L_w, L_m^UL, L_u^BH | bit | Payload global model, client update, UAV aggregate |
| P_m^RF, N_0 | W, W/Hz | RF transmit power và noise power spectral density |
| h_mu^k | Không thứ nguyên | Channel power gain |
| zeta, Gamma | Không thứ nguyên | MAC efficiency và SNR gap |
| kappa_m | J·s²/cycle³ | Hệ số dynamic CPU energy |
| P_i^base, P_i^{tx,inc}, P_i^{rx,inc} | W | Baseline và công suất điện tăng thêm |
| tau_k, D_k, D_max | s | Đồng hồ vật lý, thời lượng vòng và deadline |
| I, B_loc, eta_k | Bước, mẫu, learning rate | Tham số SGD |
| lambda_L,lambda_E,lambda_D | Không thứ nguyên | Preference có tổng bằng 1 |
| a_m^k | {0,…,U} | 0 là inactive, u là gán tới UAV u |
| rho_m, nu_m | [0,1] | Gene bandwidth và CPU dùng khi decode |
| R_search | Số nguyên dương | Số seed replicate cho learning fitness |

Các đầu vào khác gồm goodput downlink/backhaul hoặc tham số để tính chúng, hệ số aggregation, bộ dữ liệu test độc lập và các RNG namespace. Channel gains và fixed goodputs dương trên mọi link. Năng lượng của client, UAV và coordinator đều được cộng vào objective theo các tác vụ tính toán, truyền thông và điện tử đã khai báo.

Giới hạn CPU thỏa 0<f_m^min<=f_m^max, b_min>0, B_u>=0, 0<zeta<=1, Gamma>=1, C_m>0 và payload dương trên mọi link hoạt động. Tham số được hiệu chỉnh từ phần cứng hoặc ghi rõ là synthetic trong thí nghiệm.

## 3. Quy trình FL và mục tiêu học

### 3.1. Phân phối mục tiêu

Đặt trọng số p_m=n_m/sum_j n_j, hoặc dùng một phân phối ứng dụng cố định được khai báo trước. Hàm training và validation được định nghĩa theo cùng quần thể.

$$
F_m(w)=\frac1{n_m}\sum_{\xi\in D_m}\ell(w;\xi),\qquad
F(w)=\sum_{m=1}^M p_mF_m(w),\quad
p_m>0,\quad\sum_mp_m=1.
\tag{V2-01}
$$

$$
L_{\mathrm{val}}(w)=
\sum_m\frac{p_m}{|V_m|}\sum_{\xi\in V_m}\ell(w;\xi),\qquad
A_{\mathrm{val}}(w)=
\sum_m\frac{p_m}{|V_m|}
\sum_{(x,y)\in V_m}\mathbf1[\arg\max_c w(x)_c=y].
\tag{V2-02}
$$

Trong V2-02, w(x) là đầu ra model có tham số w. Mỗi V_m có ít nhất một mẫu. Nếu dùng một validation set tập trung, nó phải biểu diễn đúng các trọng số p_m hoặc có sample weights tương ứng.

Tách training, search-validation, audit-validation và test. Với từng split, định nghĩa rõ population weights. Scheduler dùng feedback validation được simulator cung cấp, và test được dùng đánh giá kết quả sau khi lựa chọn lịch đã khóa.

### 3.2. Local SGD

$$
w_{m,0}^k=w_k,\qquad
w_{m,i+1}^k=w_{m,i}^k-\eta_k
\widehat\nabla F_m(w_{m,i}^k;\xi_{m,i}^k),
\quad i=0,\ldots,I-1,
\qquad \Delta_m^k=w_{m,I}^k-w_k.
\tag{V2-03}
$$

C_m được profile cho đúng I bước, batch size và model. Với fixed local steps, có thể đặt C_m=I B_loc c_m^sample, trong đó c_m^sample có đơn vị cycle/sample. Nếu đổi sang local epochs thì workload cần tính lại theo n_m.

### 3.3. Tổng hợp phân cấp

Đặt S_k là tập client được chọn, S_{u,k} là tập được gán cho UAV u, P_{u,k}=sum_{m thuộc S_{u,k}}p_m và P_{S,k}=sum_{m thuộc S_k}p_m.

$$
\Delta_u^k=\sum_{m\in S_{u,k}}\frac{p_m}{P_{u,k}}\Delta_m^k,\qquad
w_{k+1}=w_k+\sum_{u:P_{u,k}>0}
\frac{P_{u,k}}{P_{S,k}}\Delta_u^k
=w_k+\sum_{m\in S_k}\frac{p_m}{P_{S,k}}\Delta_m^k.
\tag{V2-04}
$$

UAV rỗng được bỏ qua khi aggregate. Tích hai trọng số ở hai tầng bằng p_m/P_{S,k}, nên công thức tái tạo đúng selected-set FedAvg. Population weights giữ cố định trong toàn phiên.

## 4. Mô hình truyền thông UAV

### 4.1. Khoảng cách và gain

Khoảng cách ba chiều và mô hình free-space cơ sở kế thừa draft JNCA.

$$
d_{mu}=\sqrt{(x_u-x_m)^2+(y_u-y_m)^2+H_u^2},\qquad
h_{mu}^k=\beta_{\mathrm{ref}}(d_{mu}/d_{\mathrm{ref}})^{-2}.
\tag{V2-05}
$$

d_ref là khoảng cách tham chiếu tính bằng m, beta_ref là power gain tại khoảng cách đó. Có thể bổ sung large-scale attenuation đã đo vào h_mu^k. Trong bản cơ sở, fixed geometry và fixed effective gains cho phép giữ cùng gain qua các vòng. Nếu có trace môi trường, h_mu^k được cập nhật ở đầu vòng theo trace.

### 4.2. SNR và uplink goodput

Với s_mu^k=1 và b_mu^k>0, noise power trên link là N_0 b_mu^k.

$$
\mathrm{SNR}_{mu}^k=
\frac{P_m^{RF}h_{mu}^k}{N_0b_{mu}^k},\qquad
R_{mu}^{UL,k}=
\zeta b_{mu}^k\log_2\left(1+
\frac{P_m^{RF}h_{mu}^k}{\Gamma N_0b_{mu}^k}\right).
\tag{V2-06}
$$

zeta là hiệu suất payload của MAC, Gamma là implementation/coding gap. Chọn zeta=Gamma=1 thu dạng Shannon trong draft. Các pool UAV trực giao nên mẫu số gồm thermal noise theo mô hình cơ sở.

Payload cần gồm model/update sau cơ chế compression cố định và metadata. Nếu truyền d_w tham số với q bit/tham số, có thể dùng L_m^UL=q d_w+L_m^meta. L_w và L_u^BH được định nghĩa tương tự theo đúng message truyền. Pilot dùng q=32 với truyền tham số float32. Khi áp dụng quantization/compression làm thay đổi update, cùng toán tử đó phải xuất hiện trong cả reference aggregation và execution.

$$
t_m^{UL,k}=\frac{L_m^{UL}}{R_{m,a_m^k}^{UL,k}},\qquad
E_m^{tx,k}=P_m^{tx,inc}t_m^{UL,k},\qquad
P_m^{tx,inc}=\frac{P_m^{RF}}{\eta_m^{PA}}+P_m^{circuit,inc}.
\tag{V2-07}
$$

eta_m^PA thuộc (0,1] là hiệu suất PA. RF power dùng tính SNR, electrical power dùng tính Joule. Nếu dùng P_m^RF cho cả hai như một approximation thì khai báo eta_PA=1 và circuit increment=0.

### 4.3. Downlink coordinator–UAV

Các UAV hoạt động nhận cùng global model qua một broadcast. Đặt B_0^DL là bandwidth broadcast, P_0^RF là RF power và g_0u là gain trên link server–UAV.

$$
r_{0u}^{DL}=\zeta_0^{DL}B_0^{DL}
\log_2\left(1+\frac{P_0^{RF}g_{0u}}
{\Gamma_0^{DL}N_0B_0^{DL}}\right),\qquad
D_0^k=\frac{L_w}{\min_{u:y_u^k=1}r_{0u}^{DL}}.
\tag{V2-08}
$$

Mọi UAV hoạt động nghe broadcast trong D_0^k. Pool downlink riêng có thể được thay bằng goodput r_0u^DL đã đo. Client chưa được chọn sẽ nhận checkpoint hiện tại khi tham gia một vòng sau.

### 4.4. Downlink UAV–client

Mỗi UAV multicast model cho nhóm client, trên bandwidth downlink riêng B_u^DL. Các UAV thực hiện pha này song song.

$$
r_{um}^{DL,k}=\zeta_u^{DL}B_u^{DL}
\log_2\left(1+\frac{P_u^{RF,DL}h_{mu}^{DL,k}}
{\Gamma_u^{DL}N_0B_u^{DL}}\right),\qquad
D_u^k=
\begin{cases}
L_w/\min_{m\in S_{u,k}}r_{um}^{DL,k},&y_u^k=1,\\
0,&y_u^k=0,
\end{cases}
\quad D^{DL,k}=\max_uD_u^k.
\tag{V2-09}
$$

Có thể dùng h_mu^{DL,k}=h_mu^k nếu giả thiết reciprocal channel phù hợp tần số và giao thức. Công suất điện phát/thu được tính cho thời gian multicast của nhóm.

### 4.5. Backhaul UAV–coordinator

Mỗi UAV hoạt động truyền một aggregate với bandwidth backhaul riêng B_u^BH. Các backhaul links chạy song song, tách phổ khỏi uplink/downlink.

$$
r_{u0}^{BH}=\zeta_u^{BH}B_u^{BH}
\log_2\left(1+\frac{P_u^{RF,BH}g_{u0}}
{\Gamma_u^{BH}N_0B_u^{BH}}\right),\qquad
H_u^k=y_u^k\frac{L_u^{BH}}{r_{u0}^{BH}},\qquad
H^k=\max_uH_u^k.
\tag{V2-10}
$$

Chỉ tính H_u khi UAV có nhóm hoạt động. Các fixed goodputs r_0u^DL, r_um^DL và r_u0^BH dương theo giả thiết đầu vào. Các phép chia payload/rate chỉ thực hiện trên active links. Nếu dùng backhaul tuần tự thì thay H^k bằng tổng H_u^k và cập nhật năng lượng receiver tương ứng.

## 5. Timeline và năng lượng của một vòng

### 5.1. Compute và service

$$
t_m^{cmp,k}=C_m/f_m^k,\qquad
E_m^{cmp,k}=\kappa_m C_m(f_m^k)^2,\qquad
d_{\mathrm{svc}}^k=
\max_{m\in S_k}\left(t_m^{cmp,k}+t_m^{UL,k}\right).
\tag{V2-11}
$$

Sau barrier downlink, mọi client được chọn bắt đầu compute. Mỗi client upload ngay khi compute xong trên bandwidth dành riêng. Bandwidth được giữ nguyên trong pha service.

### 5.2. Aggregation và thời lượng vòng

Đặt n_u^k=|S_{u,k}|, n_U^k=sum_u y_u^k. Với a_u^(0),a_u^(1) và a_0^(0),a_0^(1) là hệ số thời gian đã profile, tính bằng s và s/update.

$$
A_u^k=y_u^k(a_u^{(0)}+a_u^{(1)}n_u^k),\qquad
A^k=\max_uA_u^k,\qquad
A_0^k=a_0^{(0)}+a_0^{(1)}n_U^k.
\tag{V2-12}
$$

$$
D_k(x_k)=D_0^k+D^{DL,k}+d_{\mathrm{svc}}^k+A^k+H^k+A_0^k.
\tag{V2-13}
$$

Sáu pha đi theo thứ tự broadcast coordinator, multicast UAV, compute/uplink, UAV aggregation, backhaul và coordinator aggregation. UAV aggregate sau barrier service. Thời gian tổng bao gồm max của compute cộng upload của từng client.

### 5.3. Ledger từng nút

Mọi P^{tx,inc}, P^{rx,inc}, P^{agg,inc} là công suất điện tăng thêm so với baseline. Với m được chọn, a_m^k là UAV phục vụ.

$$
E_m^k=P_m^{base}D_k+
\begin{cases}
\kappa_m C_m(f_m^k)^2+
P_m^{rx,inc}D_{a_m^k}^k+
P_m^{tx,inc}t_m^{UL,k},&m\in S_k,\\
0,&m\notin S_k.
\end{cases}
\tag{V2-14}
$$

$$
\begin{aligned}
E_u^k={}&P_u^{base}D_k\\
&+y_u^k\big(
P_u^{rx,0,inc}D_0^k+
P_u^{tx,DL,inc}D_u^k+
P_u^{rx,UL,inc}d_{\mathrm{svc}}^k+
P_u^{agg,inc}A_u^k+
P_u^{tx,BH,inc}H_u^k\big).
\end{aligned}
\tag{V2-15}
$$

Mô hình receiver UAV được chốt là một bộ thu hoạt động trong toàn pha service khi nhóm có client. Công suất xử lý đồng thời nhiều stream cần được profile vào P_u^{rx,UL,inc}. Baseline điện tử chạy cho mọi UAV suốt vòng, kể cả UAV có nhóm rỗng.

$$
E_0^k=P_0^{base}D_k+
P_0^{tx,DL,inc}D_0^k+
P_0^{rx,BH,inc}H^k+
P_0^{agg,inc}A_0^k,\qquad
E_k=\sum_mE_m^k+\sum_uE_u^k+E_0^k.
\tag{V2-16}
$$

P_u^base là công suất nền của hệ thống điện tử UAV. Tổng E_k đo năng lượng tính toán, truyền thông và điện tử cần để hoàn thành các tác vụ FL trong vòng.

### 5.4. Trạng thái qua các vòng

$$
\tau_{k+1}=\tau_k+D_k,\qquad
X_{k+1}=(w_{k+1},\tau_{k+1},h^{k+1}).
\tag{V2-17}
$$

Trong fixed-geometry benchmark, có thể giữ h^{k+1}=h^k. Tổng năng lượng và thời gian phiên được cộng từ chi phí của các lịch đã thực thi.

Candidate evaluation chạy trên bản sao X_k. Chỉ lịch được chọn thực thi mới thay đổi model, đồng hồ và chi phí tích lũy của phiên thật.

## 6. Bài toán nhiều vòng và bài toán NSGA-II mỗi vòng

### 6.1. Mục tiêu cuối phiên

Với policy pi ánh xạ trạng thái vào lịch x_k=(s^k,b^k,f^k), bài toán ứng dụng là

$$
\min_\pi\left(
1-\mathbb E[A_{\mathrm{val}}(w_K)],
\mathbb E[E_{\mathrm{episode}}],
\mathbb E[D_{\mathrm{episode}}]\right),\qquad
E_{\mathrm{episode}}=\sum_{k=0}^{K-1}E_k,\quad
D_{\mathrm{episode}}=\sum_{k=0}^{K-1}D_k.
\tag{V2-18}
$$

Model cuối là kết quả của K lần cập nhật V2-04. Năng lượng/thời gian là chi phí tích lũy của các tác vụ FL để tạo ra model đó.

V2 dùng validation cross-entropy làm learning fitness trong tìm kiếm, theo reference evaluation của raw idea. Accuracy của model cuối được dùng báo cáo chất lượng theo mục tiêu ứng dụng. Hai tiêu chí có thể cho thứ tự khác nhau, vì vậy lưu cả loss và accuracy trong kết quả cuối.

### 6.2. Bài toán tại snapshot k

$$
\begin{aligned}
\min_{s,b,f}\quad&
\mathbf j_k(x)=\big(\mu_k(S(x)),E_k(x),D_k(x)\big),\\
\mu_k(S)&=\mathbb E_{\xi}
L_{\mathrm{val}}\left(w_k+
\sum_{m\in S}\frac{p_m}{P_S}\Delta_m^k(\xi)\right),\\
\text{C1}\quad&s_{mu}\in\{0,1\},\quad s_m=\sum_us_{mu}\le1,\\
\text{C2}\quad&1\le\sum_ms_m\le N_{\max},\\
\text{C3}\quad&b_{\min}s_{mu}\le b_{mu}\le B_us_{mu},
\quad \sum_mb_{mu}\le B_u,\\
\text{C4}\quad&f_m^{min}s_m\le f_m\le f_m^{max}s_m,\\
\text{C5}\quad&D_k(x)\le D_{\max}.
\end{aligned}
\tag{V2-19}
$$

Mọi công thức FL, rate, timeline và ledger ở trên thuộc định nghĩa của bài toán. Optimizer giải một bài toán mixed-integer nonlinear, có learning fitness được đánh giá bằng training/aggregation.

NSGA-II được chạy lại ở từng vòng theo raw idea. Mục tiêu V2-19 đo learning progress một bước, sau đó toàn policy được kiểm tra qua V2-18. Tối ưu terminal objective trực tiếp cần mô phỏng các nhánh nhiều vòng tới w_K. Đặc tả v2 giữ vòng lặp một bước đã yêu cầu và ghi nhận giới hạn tối ưu dài hạn này.

Cộng năng lượng/thời gian quá khứ vào fitness mỗi vòng tạo cùng quan hệ dominance vì hai hạng đó là hằng theo mọi candidate tại snapshot. Việc cộng này chỉ hỗ trợ hiển thị trạng thái tích lũy.

### 6.3. Chi phí tìm kiếm và kết quả của phiên

Reference search có quyền mô phỏng phản thực tế nhiều lịch từ cùng checkpoint. Toàn bộ local training thử, tính gradient guidance, cache, validation và NSGA-II được đo bằng search wall time/CPU–GPU time. Search checkpoint giữ bất biến, còn operational ledger cộng các lịch đã thực thi.

Với deployment online, cần một controller dùng dữ liệu quan sát được và tính thêm thời gian quyết định t_opt cùng năng lượng tính toán, điện tử tương ứng. V2 được định vị là reference-evaluated benchmark offline.

Để so sánh các operating points cuối phiên, chạy toàn bộ K vòng cho từng preference lambda đã chọn trước, rồi lấy các vector episode cuối. Front trong một vòng là kết quả cục bộ của snapshot đó. Một point episode chỉ hình thành sau cả chuỗi lịch đã thực thi.

## 7. Ý tưởng set-dependent và công thức D(S)

### 7.1. Vì sao cần đánh giá cả tập client?

Với g_m^k=gradient F_m(w_k), đặt gradient quần thể g_pop^k=sum_m p_m g_m^k. Gradient trung bình của một tập được chọn phụ thuộc vào cả các thành viên lẫn tổng population mass của tập.

$$
P_S=\sum_{m\in S}p_m,\qquad
\alpha_m(S)=p_m/P_S,\qquad
g_S^k=\sum_{m\in S}\alpha_m(S)g_m^k,\qquad
\boxed{D(S)=\|g_S^k-g_{\mathrm{pop}}^k\|_2^2}.
\tag{V2-20}
$$

D(S) đo squared gradient matching error ở cùng checkpoint. Một client có ích cho matching khi gradient của nó đưa gradient trung bình hiện tại của tập gần gradient quần thể hơn. Tác động này thay đổi theo tập đang có.

D(S) luôn được tính tại snapshot k hiện tại và có đơn vị squared gradient norm. Thời gian vật lý viết D_k(x) với đối số lịch x, hoặc d_svc trong công thức. Khi triển khai dùng tên gradient_matching_error và round_duration để phân biệt.

### 7.2. Các hạng tương tác làm rõ tính set-dependent

Đặt c_m=g_m−g_pop. Vì sum_{m thuộc S}alpha_m=1, khai triển V2-20 cho

$$
D(S)=
\sum_{m\in S}\alpha_m^2\|c_m\|^2
+
2\sum_{\substack{i<j\\i,j\in S}}
\alpha_i\alpha_j\langle c_i,c_j\rangle.
\tag{V2-21}
$$

Các cross terms quyết định gradient bias của các client bù nhau hoặc tăng thêm nhau. Các trọng số alpha_m cũng thay đổi khi thêm/bớt thành viên. Đây là cơ sở của toán tử xét cả tập, thay vì chỉ xếp hạng từng client bằng một score cố định.

Ví dụ với ba client equal-weight và scalar gradients (2,−2,1), g_pop=1/3. Các cặp có matching error

$$
D(\{1,2\})=\frac19,\qquad
D(\{1,3\})=\frac{49}{36},\qquad
D(\{2,3\})=\frac{25}{36}.
\tag{V2-22}
$$

Hai gradient trái dấu có thể bổ trợ nhau khi aggregate. Mục tiêu thực nghiệm là kiểm tra việc dùng thông tin này để sinh proposal có cải thiện front loss–energy–time tại cùng compute budget hay không.

### 7.3. Lợi ích khi thêm, bỏ và hoán đổi client

Đặt r_S=g_S−g_pop và định nghĩa lợi ích matching của một thao tác là D(S)−D(S_new). Giá trị dương nghĩa là thao tác giảm sai lệch gradient của tập.

Với j chưa thuộc S, đặt t=p_j/(P_S+p_j).

$$
g_{S+j}=g_S+t(g_j-g_S),\qquad
D(S+j)-D(S)
=2t\langle r_S,g_j-g_S\rangle+t^2\|g_j-g_S\|^2.
\tag{V2-23}
$$

Với i thuộc S và |S|>=2, đặt t_i=p_i/(P_S−p_i).

$$
g_{S-i}=g_S+t_i(g_S-g_i),\qquad
D(S-i)-D(S)
=2t_i\langle r_S,g_S-g_i\rangle+t_i^2\|g_S-g_i\|^2.
\tag{V2-24}
$$

Với i thuộc S và j ngoài S, đặt

$$
\delta_{ij}(S)=
\frac{p_j(g_j-g_S)-p_i(g_i-g_S)}
{P_S-p_i+p_j},\qquad
D(S-i+j)-D(S)
=2\langle r_S,\delta_{ij}(S)\rangle+\|\delta_{ij}(S)\|^2.
\tag{V2-25}
$$

Các công thức được suy ra bằng chuẩn hóa lại weighted average rồi khai triển norm bình phương. Chúng cho phép tính marginal theo trạng thái tập hiện tại, gồm cả dữ liệu bổ trợ và hiệu ứng thay đổi trọng số.

Reassign cùng một client sang UAV khác giữ nguyên S và D(S) trong mô hình upload thành công, fixed local work. Toán tử này tìm cải thiện radio/energy/time. Add, drop, swap tìm tập client mới, đồng thời làm thay đổi tài nguyên.

### 7.4. Quan hệ với learning progress

Xét một bước gradient chính xác w^+=w−gamma g_S, F là L-smooth và 0<gamma<=1/L. Descent lemma và đồng nhất thức tích vô hướng cho

$$
F(w^+)\le F(w)-\frac{\gamma}{2}\|g_{\mathrm{pop}}\|^2
+\frac{\gamma}{2}D(S)
-\frac{\gamma}{2}(1-L\gamma)\|g_S\|^2
\le F(w)-\frac{\gamma}{2}\|g_{\mathrm{pop}}\|^2+\frac{\gamma}{2}D(S).
\tag{V2-26}
$$

Để chứng minh, thay w^+ vào smoothness bound và dùng
2<g_pop,g_S>=||g_pop||²+||g_S||²−||g_S−g_pop||².
D(S) xuất hiện trực tiếp như một hạng selection error trong cận giảm training loss.

Với I bước local SGD, update còn chịu local drift và stochastic noise. Khi ấy r_S chỉ là một thành phần của sai số update. Vì vậy v2 dùng D(S) để hướng dẫn đề xuất, còn survival và archive dùng actual post-training validation loss của V2-19. Thiết kế này cho phép kiểm tra proxy bằng chính kết quả FL.

### 7.5. Tính gradient và quyền truy cập thông tin

Trong simulator offline, mặc định tính g_m tại checkpoint nguồn trên training data, hoặc lấy minibatch estimate g_hat_m với seed guidance cố định. Thực hiện một lần trên mỗi client mỗi snapshot, ghi riêng chi phí gradient guidance. Cách này dùng quyền truy cập reference evaluator của Direction A.

Một phiên bản có thể dùng sketch z_m=R g_hat_m với projection seed chung và dimension d_s. Khi đó score triển khai là

$$
\widehat g_{\mathrm{pop}}=\sum_mp_m\widehat g_m,\qquad
\widehat D_R(S)=
\left\|\sum_{m\in S}\alpha_m R\widehat g_m-
\sum_mp_mR\widehat g_m\right\|^2.
\tag{V2-27}
$$

Mặc định đặt R là identity cho bài toán nhỏ để kiểm tra D chính xác. Nếu dùng minibatch/sketch thì ghi nhãn score là estimate, lưu guidance seed và projection config. Các hạng Gram có thể precompute để tăng tốc.

Nếu deploy chỉ có historical reports, phải ghi tuổi report/model version và dùng exploration cho client chưa quan sát. Matching trên tập report có sẵn là một biến thể cần kiểm nghiệm riêng. Quyền lấy gradient toàn bộ client trong simulator cần được thể hiện trong nhãn thí nghiệm offline.

### 7.6. Vai trò đóng góp

Cơ chế được đề xuất cho v2 là kết hợp marginal matching error của **tập hiện tại** với khả năng phục vụ UAV trong bước variation của NSGA-II. Mỗi candidate set-aware proposal đi qua decode/repair và reference evaluation giống proposal thông thường.

Các thành phần cần chứng minh bằng đối chứng gồm hiệu quả của add/drop/swap theo V2-23–V2-25, tỷ lệ proposal được nhận, giảm D có đi cùng giảm validation loss, và chất lượng episode cuối dưới cùng ngân sách thực.

Diversity/representative client selection đã có trong DivFL. Định vị đóng góp cần dựa vào thiết kế toán tử theo marginal D(S), sự ghép với resource feasibility và bằng chứng so sánh đầy đủ. [DivFL](https://github.com/melodi-lab/divfl).

## 8. Biểu diễn cá thể và giải mã

### 8.1. Ba vector quyết định

Cá thể lưu ba vector độ dài M, gồm assignment a và hai vector resource keys rho,nu. Đây là dạng mã hóa của ba thành phần (s,b,f) trong raw idea.

$$
a_m\in\{0,1,\ldots,U\},\quad
\rho_m,\nu_m\in[0,1],\qquad
s_{mu}=\mathbf1[a_m=u],\quad s_m=\mathbf1[a_m>0].
\tag{V2-28}
$$

rho và nu của inactive client được giữ như latent keys để tái dùng khi add. Physical bandwidth và CPU của inactive client bằng 0.

Với n_u=|S_u|, decode bandwidth và CPU bằng

$$
z_m=\frac{\rho_m+\epsilon_\rho}
{\sum_{j\in S_u}(\rho_j+\epsilon_\rho)},\qquad
b_{mu}=b_{\min}+(B_u-n_ub_{\min})z_m\quad(m\in S_u),
\quad
f_m=f_m^{min}+\nu_m(f_m^{max}-f_m^{min})\quad(m\in S).
\tag{V2-29}
$$

epsilon_rho>0 là hằng số decode, ví dụ 10^−8. Decoder này cần n_u b_min<=B_u và dùng hết pool UAV hoạt động. Đối với S_u rỗng, mọi b_mu=0.

Dùng hết bandwidth có cơ sở trong radio model hiện tại. R(b) tăng theo b, nên tăng bandwidth giảm thời gian upload, giảm năng lượng phát và giữ các chi phí còn lại không tăng. Với P_tx,inc>0, L_UL>0 và bandwidth dư ở một nhóm hoạt động, có thể cải thiện energy bằng cấp phần dư cho một client trong nhóm. Hệ quả này dựa trên pool trực giao và sổ năng lượng đã chốt.

### 8.2. Structural repair

Đặt c_u=floor(B_u/b_min) là số client tối đa có thể cấp bandwidth tối thiểu trong nhóm UAV u. Repair theo thứ tự sau.

1. Kiểm tra assignment a_m thuộc {0,…,U}, sửa gene ngoài miền về một giá trị trong miền bằng RNG đã khai báo.
2. Nếu |S|>N_max, lần lượt drop client, dùng marginal D(S) hoặc tie-break ngẫu nhiên theo chế độ thuật toán.
3. Nếu |S|=0, chọn một client và một UAV còn capacity c_u>=1 rồi add. Nếu mọi c_u=0, đánh dấu infeasible.
4. Sửa nhóm vượt capacity c_u bằng reassign client tới UAV còn capacity, hoặc drop khi tập vẫn có ít nhất một client.
5. Clip resource keys vào [0,1], decode V2-29, tính lại toàn bộ timeline và node ledgers.
6. Tính residual deadline và các ràng buộc C1–C5, lưu chúng vào evaluation record.

Giới hạn số lần repair bằng R_repair cấu hình. Nếu association repair vẫn thất bại, đánh dấu infeasible. Feasibility deadline được đánh giá bằng công thức sau decode. Một structural repair thành công có nghĩa là các bound/cardinality/bandwidth hợp lệ.

Có thể bổ sung một local resource repair hữu hạn, thử tăng CPU của straggler hoặc chuyển bandwidth trước khi đánh giá cuối. Mỗi lần thử phải tính lại cả energy và time vì CPU nhanh hơn tăng dynamic energy. Ghi nhận số lần thử và chi phí repair.

### 8.3. Constraint violation và dominance

Với residual g_j(x)<=0, scale sigma_j>0 có cùng đơn vị residual, đặt

$$
CV(x)=\sum_j\frac{\max(0,g_j(x))}{\sigma_j}.
\tag{V2-30}
$$

Residual gồm assignment bounds, cardinality, resource bounds, bandwidth sum và deadline. Dùng scale deadline D_max, scale bandwidth B_u trên pool dương, scale CPU f_m^max và scale số lượng bằng 1. Nếu B_u=0, kiểm tra allocation bằng 0 trực tiếp. Feasible được xác định bằng tolerance theo đơn vị từng constraint.

Feasible ưu tiên hơn infeasible. Hai infeasible so theo CV, tie-break ngẫu nhiên. Hai feasible so theo Pareto rank, sau đó crowding distance trong binary tournament. Learning oracle được gọi cho candidate physical-feasible.

## 9. NSGA-II với variation dựa trên D(S)

### 9.1. Khởi tạo population

Tạo N_pop cá thể với cardinality phân bố trên 1,…,N_max. Trộn random feasible association, channel-efficient association và các tập giảm matching error bằng add/swap. Decode/repair mọi cá thể và tính fitness.

Trạng thái X_k, model và seed bundle giống nhau cho mọi cá thể ở vòng k. Guidance gradient của mục 7 chỉ tính một lần cho snapshot. Có thể tái dùng genotype tốt từ vòng trước làm một phần warm start nếu cấu hình cho phép, nhưng phải đánh giá lại tại w_k.

### 9.2. Parent selection và crossover

Binary tournament chọn bố mẹ theo constraint handling, rank và crowding.

Assignment crossover bắt đầu từ intersection của hai selected sets, rồi lấy ngẫu nhiên từ symmetric difference và thêm client ngoài union khi cần. Chọn child cardinality trong khoảng giữa cardinality hai bố mẹ, hoặc một cardinality ngẫu nhiên trong [1,N_max] theo xác suất exploration đã khai báo. UAV của client được kế thừa từ một bố mẹ có chọn client đó. Với client mới, chọn một UAV trong {1,…,U}, sau đó repair theo bandwidth capacity.

Đối với rho,nu, dùng simulated binary crossover có bound [0,1], distribution index eta_c và xác suất p_c. Hai con sau crossover đi qua repair. Association luôn được giải mã lại sau mỗi thay đổi.

### 9.3. Generic mutation

Generic mutation chọn một thao tác khả dụng theo xác suất cấu hình.

| Thao tác | Điều kiện | Thay đổi |
| --- | --- | --- |
| Add | $\lvert S\rvert<N_{\max}$ và còn client ngoài S | Thêm client và chọn UAV |
| Drop | $\lvert S\rvert>1$ | Bỏ một client |
| Swap | Có client trong/ngoài S | Đổi một client tham gia |
| Reassign | Có client được chọn và U>1 | Chuyển association sang UAV khác |
| Resource mutation | Có gene liên tục | Polynomial mutation trên rho hoặc nu |

Nếu thao tác không khả dụng, chọn lại từ danh sách khả dụng. Ở M=N_max và S=calM, swap/add có thể không dùng được. Khi chỉ có một client và một UAV, resource mutation vẫn cho phép sinh biến thể.

### 9.4. Set-dependent mutation

Với xác suất p_set, dùng D(S) để đề xuất thay đổi selected set. Các bước thực hiện như sau.

1. Tạo tối đa L_move thao tác add/drop/swap đáp ứng cardinality. Thử cả thao tác khác số lượng và thao tác giữ số lượng khi khả dụng.
2. Tính delta_D bằng V2-23–V2-25 từ g_S,P_S hiện tại. Khi dùng estimate/sketch, thay bằng cùng dạng công thức trong không gian estimate.
3. Với mỗi tập đề xuất, chọn association còn capacity hoặc thử UAV có goodput cao, rồi decode/repair.
4. Lọc các proposal structural-infeasible. Tính D trên **tập cuối sau repair**, vì repair có thể thêm/bỏ client khác.
5. Chọn proposal có D thấp nhất trong shortlist. Nếu nhiều proposal có cùng D trong tolerance, ưu tiên CV nhỏ, sau đó time nhỏ, rồi tie-break RNG.
6. Với xác suất exploration p_explore, chọn một proposal ngẫu nhiên trong shortlist. Nếu shortlist rỗng, dùng generic mutation.

Guided proposal chỉ là một ứng viên cho NSGA-II. Actual learning fitness và hai chi phí vận hành quyết định survival. Một proposal giảm D vẫn có thể bị loại do loss hoặc chi phí tài nguyên.

Có thể giữ cả best-guided proposal và một proposal resource/generic nếu còn offspring budget. Đảm bảo số offspring mỗi generation vẫn bằng N_pop. Cùng evaluation budget được áp dụng khi so generic và set-dependent variants.

### 9.5. Reference evaluation và cache

Dùng R_search independent seed bundles được khóa trước search tại snapshot.

$$
\widehat\mu_k(S)=\frac1{R_{\mathrm{search}}}
\sum_{r=1}^{R_{\mathrm{search}}}
L_{\mathrm{val,search}}(w_{k+1}(S;\xi_r)).
\tag{V2-31}
$$

Cache local updates theo snapshot/checkpoint hash, client, local-work config và seed. Cache set-loss theo sorted selected set, snapshot, seed bundle và validation protocol. Tập S giống nhau có learning output giống nhau khi fixed work, fixed seeds và successful upload, nên các biến thể b,f và gán UAV có thể chia sẻ loss.

Cache guidance gradient riêng, ghi chi phí tạo cache vào search budget. Khi k tăng, mọi learning-cache key phải phản ánh checkpoint mới. Candidate evaluation không cập nhật X_k.

Audit dùng seed bundle và validation protocol độc lập đã định nghĩa. Nếu audit dùng corpus khác, giá trị loss là objective trên corpus đó. Chọn lịch thực thi theo preference được khóa, rồi dùng một execution seed độc lập để thực hiện đúng một chuỗi local updates cho lịch đã chọn.

### 9.6. Environmental selection và archive

Gộp population cha và con thành R_g=P_g hợp Q_g, cỡ 2N_pop. Thực hiện constrained nondominated sorting. Lấy đủ các front theo rank, rồi cắt front cuối theo crowding distance để còn N_pop cá thể.

Trong front khả thi, crowding distance cộng theo ba objective sau chia range của objective trong front. Objective có range bằng 0 đóng góp 0. Boundary points trên objective có range dương được ưu tiên crowding lớn.

Archive lưu các candidate khả thi không bị trội trong cùng snapshot và common search protocol. Loại duplicate physical schedules bằng canonical key. Các resource variants cùng selected set vẫn có thể có energy/time khác nhau và cần được giữ nếu không trội nhau.

### 9.7. Chọn một lịch thực thi

Chốt trước lambda_j>=0, sum_j lambda_j=1 và positive scales c_L,c_E,c_D từ pilot/tuning riêng.

$$
x_k^\star=\arg\min_{x\in\mathcal A_k}
\left[
\lambda_L\frac{\widehat\mu_k(S(x))}{c_L}
+\lambda_E\frac{E_k(x)}{c_E}
+\lambda_D\frac{D_k(x)}{c_D}
\right].
\tag{V2-32}
$$

Tie-break lần lượt theo validation loss, energy, time và canonical key. Preference/scales giữ cố định giữa thuật toán so sánh và các vòng trong một run. Với ứng dụng có energy/time caps, có thể chọn min-loss trong archive thỏa các cap đã định trước.

Nếu archive rỗng, thử lịch witness/fallback đã kiểm tra trên trạng thái hiện tại. Nếu chưa tìm được lịch khả thi, trả trạng thái SEARCH_FAILED và báo vòng dừng. Chứng cứ bất khả thi cần một phép kiểm tra đầy đủ riêng. Kết quả episode dừng sớm ghi rõ số vòng đã hoàn tất.

### 9.8. Mã giả hoàn chỉnh

~~~text
INPUT:
    Initial state X0, K FL rounds, G generations, population N_pop
    N_max, physical parameters, local SGD protocol
    NSGA-II operators, p_set, p_explore, shortlist size L_move
    Fixed deployment preference/scales, search/audit/execution seed namespaces

FOR k = 0,...,K-1:
    Freeze snapshot Xk and source checkpoint wk
    Create guidance gradients or gradient estimates at wk
    Compute g_pop; prepare matching-error sufficient statistics
    Initialize population P0 across cardinalities 1,...,N_max
    Decode, repair, physically evaluate each candidate
    Reference-evaluate physically feasible candidates with shared seed bundle
    Initialize the feasible nondominated archive Ak

    FOR generation g = 0,...,G-1:
        Qg = empty; attempts = 0
        WHILE size(Qg) < N_pop AND attempts < R_offspring:
            Increment attempts
            Select parents by constrained binary tournament
            Create children by assignment crossover and bounded SBX

            FOR each child while offspring budget remains:
                WITH probability p_set:
                    Compute current P_S, g_S, residual r_S
                    Propose add/drop/swap shortlist with marginal D(S) formulas
                    Assign UAVs, decode/repair and recompute D on repaired sets
                    Choose best-D proposal or explore a random proposal
                OTHERWISE:
                    Apply generic add/drop/swap/reassign mutation

                Apply bounded polynomial mutation to bandwidth/CPU keys
                Decode and repair child with finite repair budget
                Compute constraints, energy and round duration
                If physically feasible:
                    Get actual post-training validation loss from reference cache
                Store child and its evaluation record in Qg

        If needed, fill Qg to N_pop using parent copies and log this event
        Merge Pg and Qg
        Perform feasibility-first nondominated sorting
        Select N_pop survivors by rank and crowding
        Update Ak from all feasible evaluated candidates

    Select x_star from Ak using fixed deployment preference
    If Ak is empty, try the declared feasible fallback
    If no schedule is found, record early termination and stop

    Lock the selected schedule
    Independently audit the reported front if required by the experiment
    Execute x_star from wk with the independent execution seed
    Aggregate by weighted client-to-UAV-to-coordinator rule
    Commit wk+1, physical clock and cumulative costs
    Store round trace and selected-set diagnostics

Evaluate the final model on held-out test data
Return final accuracy/loss, total energy/time, completion status and full trace
~~~

## 10. Độ phức tạp và phép kiểm tra đóng góp

### 10.1. Chi phí tính toán

Đặt Q=N_pop(G+1) là upper count số candidate evaluations trước duplicate handling, Q_S là số selected sets khác nhau, C_train là cost một client update và C_val là cost validation.

| Thành phần | Chi phí tại một snapshot |
| --- | --- |
| Guidance gradient | Sum_m C_grad,m |
| Lazy local-update cache | Tối đa R_search M C_train khi cùng work cost |
| Aggregate và validation theo tập | O(R_search Q_S(N_max d_w+C_val)) |
| Decode và physical cost | O(M+U) mỗi candidate với assignment vector |
| Guided shortlist | O(L_move N_max d_s) để tính lại matching score trực tiếp |
| NSGA-II sorting | O(G N_pop² J), J=3 |
| Update cache memory | O(R_search M d_w) nếu giữ toàn bộ updates |

Duy trì P_S và v_S=sum_{m thuộc S}p_m g_m giảm việc tính score một move xuống O(d_s) trước resource repair. Dùng Gram matrix có thể tăng tốc thêm nhưng cần O(M²) memory và chi phí tạo matrix. Thời gian repair và archive maintenance được đo riêng trong search budget.

### 10.2. Các tính chất có thể kiểm tra

1. Decoder V2-29 bảo đảm inactive resources bằng 0, active bandwidth dương và sum b_mu=B_u trên nhóm hợp lệ.
2. Aggregation V2-04 tương đương selected-set weighted average phẳng.
3. Công thức marginal V2-23–V2-25 bằng hiệu của hai giá trị D được tính trực tiếp.
4. Trong cơ sở fixed work/upload thành công, learning loss chỉ phụ thuộc S khi checkpoint và RNG cố định.
5. D(S) có cross terms theo V2-21 và có thể giảm khi thêm client bổ trợ. D(S) cũng có thể tăng khi thêm client, nên generic exploration vẫn cần thiết.
6. NSGA-II elitism giữ các ứng viên theo rank/crowding trên những gì đã đánh giá. Chất lượng terminal được kiểm chứng qua các episode hoàn chỉnh.

### 10.3. Thiết kế đối chứng cho đóng góp set-dependent

So ít nhất ba cấu hình trên cùng simulator, initialization, local work, NSGA-II parameters và deployment preference.

| Cấu hình | Variation trên selected set |
| --- | --- |
| Generic NSGA-II | Random add/drop/swap/reassign |
| Individual-score guidance | Xếp hạng client bằng score cá thể cố định tại snapshot |
| Set-dependent NSGA-II | Marginal D(S) theo tập hiện tại và các bước mục 9.4 |

Có thể thêm variant chỉ dùng swap, variant add/drop/swap, guidance exact-gradient so với minibatch/sketch, và p_set=0 để xác minh ablation.

Đo final test accuracy/loss, total energy/time, số vòng hoàn tất, per-round cardinality, rare-class recall nếu có kịch bản phù hợp, search cost gồm gradient guidance, marginal D giảm bao nhiêu, correlation giữa D và actual loss, và tỷ lệ guided offspring sống sót.

Để cô lập lợi ích dùng tương tác của tập, các guided baselines nhận cùng nguồn gradient information và trả cùng phí tạo gradient. Báo learning-oracle calls và số tập khác nhau, vì cache có thể làm số proposal lớn nhưng số reference computations nhỏ.

## 11. Thông số đề xuất và đầu ra để triển khai

Một pilot có thể dùng N_pop=40, G=30, p_c=0.9, eta_c=15, eta_m=20, continuous mutation probability 1/(2M) trên từng gene, p_set=0.5, p_explore=0.2 và L_move=16. Đây là lựa chọn khởi đầu cần tuning bằng data/scenarios riêng.

Các xác suất add/drop/swap/reassign được chuẩn hóa lại trên thao tác khả dụng. Seed dùng tái lập cả parent selection, crossover, mutation, repair, shortlist, guidance, search SGD, audit và execution. Đặt số lần sinh lại offspring tối đa R_offspring và số lần thử khởi tạo R_init. Khi chạm trần sinh offspring, điền phần còn thiếu bằng bản sao các parent hiện có để hoàn tất generation và log số bản sao. Các lần retry đều tính vào search cost.

Một evaluation record cần chứa snapshot_id, candidate/genotype hash, selected set, association, decoded bandwidth/CPU, D_matching hoặc estimate, ba objective, constraint residuals, cache hits/misses và actual evaluation cost.

Một round record cần chứa selected schedule, execution seed, model hash trước/sau, node energy ledgers, cumulative energy/time, archive và NSGA-II configuration. Một episode summary cần chứa requested/completed rounds, final test metrics, cumulative operational cost và cumulative search cost.

## 12. Nguồn và phạm vi kế thừa

- Raw idea của v2 xác định cấu trúc mạng, tối đa N_max client, ba vector quyết định và vòng lặp NSGA-II. [raw-idea.txt](raw-idea.txt).
- Draft JNCA cung cấp FL phân cấp, Shannon uplink, DVFS, elapsed-time/energy accounting, population validation và round-level reference evaluation. [JNCA_Huy.pdf](../../../../docs/developing%20directions/JNCA_Huy.pdf).
- Đặc tả v1 cung cấp chi tiết barrier protocol và cách kiểm tra ledger để kế thừa triển khai. [problem-formulation v1](../v1/problem-formulation.md).
- Cơ chế NSGA-II gồm rank, crowding và elitist survival được mô tả trong tài liệu thuật toán. [NSGA-II](https://pymoo.org/algorithms/moo/nsga2.html).
- FedAvg là cơ sở local training và model averaging. [McMahan và cộng sự, 2017](https://proceedings.mlr.press/v54/mcmahan17a.html).

- Representative client-set selection có tiền lệ trong FL. Thiết kế v2 cần được đánh giá cùng nguồn thông tin và ngân sách. [DivFL](https://github.com/melodi-lab/divfl).

Các lựa chọn thêm của đặc tả gồm goodput downlink/backhaul, sáu pha barrier cụ thể, ba resource-key vectors, variation theo marginal D(S), quy trình repair và deployment preference. Chúng là các quyết định thiết kế cho triển khai v2 và cần được log trong cấu hình thí nghiệm.