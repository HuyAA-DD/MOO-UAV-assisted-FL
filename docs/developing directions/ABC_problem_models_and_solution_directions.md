# Đề xuất mô hình và hướng giải A, B, C cho UAV-assisted Federated Learning

**Ngày:** 28/10/2026. **Rà soát lần 2:** 28/10/2026; xem mục 12 về các hiệu chỉnh.  
**Nguồn nền:** [research draft JNCA](JNCA_Huy.pdf), đặc biệt các mục 2–8; [RULES.md](../../RULES.md); [Research Review](../../Implementation/Direction%20A/Deep%20Report/Direction_A_Research_Review.md) và [Research Report VI](../../Implementation/Direction%20A/Deep%20Report/Direction_A_Research_Report_VI.md); [đặc tả v1](../../Implementation/Direction%20A/src/v1/problem-formulation.md) và [kết quả v1](../../Implementation/Direction%20A/src/v1/report.md).  
**Trạng thái:** đề xuất nghiên cứu và các phép chứng minh có điều kiện; chưa phải kết quả thực nghiệm mới hoặc chứng nhận tính mới tuyệt đối. Các công thức dưới đây do báo cáo phát triển, không phải toàn bộ đều có sẵn trong draft.

## 0. Định hướng và cách sử dụng

Nên xây dựng **một mô hình vật lý và FL chung, ba lớp bài toán kế thừa nhau**, thay vì ba simulator không tương thích:

| Hướng | Quyết định chính | Câu hỏi khoa học | Kết quả cần có |
|---|---|---|---|
| A | Chọn tập client, gán UAV, cấp bandwidth và CPU | Tập client nào có lợi cho học khi tính đúng chi phí phục vụ? | Front loss–energy–time và cấu trúc phân rã có chứng minh |
| B | Chọn ứng viên, fidelity và số lần đánh giá | Dùng ngân sách tính toán hữu hạn để nhận diện front đáng tin cậy như thế nào? | Front được kiểm tra, cận sai số trên miền ứng viên hữu hạn và lợi ích đo được |
| C | Probe ai, đo bao nhiêu, rồi lập lịch lại | Thông tin mới đáng trả bao nhiêu pin/thời gian, và khi nào nên dừng đo? | Chính sách không nhìn trước, hạch toán đủ chi phí và lợi ích recourse |

A là bài toán vận hành được đánh giá trong simulator. B là bài toán **phân bổ tính toán để giải A**, không phải đổi mục tiêu vật lý. C là bài toán điều khiển thông tin không đầy đủ; có thể dùng bộ giải A/B bên trong nhưng không được gọi oracle online miễn phí.

**Khuyến nghị trọng tâm:** A làm nền và baseline mạnh; B tập trung vào cấu trúc cache dùng chung và chứng nhận quyết định; C tập trung vào việc probe làm thay đổi cả thông tin lẫn miền lịch còn khả thi. Đây là các cơ chế cụ thể đáng nghiên cứu hơn việc chỉ thay NSGA-II bằng MOEA/D.

### 0.1. Phần nào kế thừa, phần nào đề xuất thêm?

- Kế thừa draft: ba mục tiêu, FL phân cấp, loss trên quần thể cố định, selected-set normalization, resource constraints, phân biệt offline/online, multi-fidelity và probing.
- Kế thừa v1: benchmark một vòng, cache theo tập, decoder CPU, ledger theo nút, audit tách biệt.
- Đề xuất thêm trong báo cáo: bộ cấp tài nguyên lồi theo tập/gán UAV; chứng minh cấu trúc Pareto; cận FL tách sai lệch chọn tập, local drift và nhiễu; chứng nhận đa fidelity trên miền hữu hạn; chi phí đánh giá phụ thuộc cache; VOI có mất khả năng phục vụ và bảo đảm chọn probe trên tập chính sách hữu hạn.
- Chưa triển khai: các thành phần mới trên, kênh fading/outage đầy đủ, chứng nhận thống kê, optimizer B và controller C. Không gán kết quả hiện có của v1 cho các đề xuất này.

### 0.2. Áp dụng RULES.md có chọn lọc

Giữ yêu cầu về miền biến, đơn vị, deadline, pin, non-IID, chứng minh và đối chứng. Điều chỉnh những điểm không thể áp dụng máy móc:

1. Hover có công suất không đổi là trường hợp vật lý hợp lệ của mô hình rotor tại vận tốc bằng 0; không phải lúc nào dạng P nhân t cũng sai.
2. Không khẳng định “80–90% năng lượng là propulsion” nếu chưa đo ở cấu hình cụ thể.
3. Gradient matching không tự động submodular; diversity không đồng nghĩa ích lợi học tập.
4. Không gán bảo đảm KKT cho toàn MINLP hoặc bảo đảm tối ưu toàn cục cho MOEA.
5. Không yêu cầu có cả Lyapunov, SCA và POMDP trong cùng một bài. Chỉ dùng công cụ giải đúng cấu trúc.
6. Không thể chứng minh “chưa ai làm” bằng một định lý. Có thể chứng minh tính chất toán học và đối chiếu novelty với tài liệu đã đọc; vẫn phải rà soát tiếp trước khi nộp bài.

---

## 1. Mô hình hệ thống vật lý chung

### 1.1. Bối cảnh thực tế và phạm vi

Xét camera/cảm biến mặt đất có dữ liệu riêng, mạng mặt đất không đủ phủ sóng. UAV mang bộ tổng hợp biên, coordinator đặt tại trạm mặt đất. Ví dụ phù hợp là giám sát nông nghiệp/công trường: dữ liệu khác nhau theo khu vực, một số sự kiện hiếm ở vùng liên kết yếu. Không mặc định mọi client có CPU, pin và số mẫu như nhau.

Bản cơ sở dùng **UAV hover trong phiên huấn luyện**, các vị trí đã được hoạch định. Điều này hợp lý khi chuyến bay gồm di chuyển tới điểm phục vụ, hover, rồi quay về. Năng lượng cất cánh/di chuyển/return phải được dự trù trong pin, dù không là biến tối ưu. Chưa tối ưu quỹ đạo để giữ cơ chế nghiên cứu tập trung.

Hai cấp vật lý cần triển khai riêng:

- **P0:** effective rate xác định, upload thành công. Dùng cho định lý phân rã và benchmark dễ kiểm tra.
- **P1:** LoS/NLoS, fading, ước lượng CSI, timeout và upload thất bại. Dùng stress test và Direction C; không chuyển nguyên xi định lý P0 sang P1.

### 1.2. Bảng ký hiệu chính

| Ký hiệu | Miền/đơn vị | Ý nghĩa |
|---|---|---|
| $m \in \mathcal{M}=\{1,\dots,M\}, u \in \mathcal{U}=\{1,\dots,U\}$ | chỉ số | Client và UAV; coordinator ký hiệu $0$ |
| $k=0,\dots,K-1$ | số vòng | Chỉ số vòng FL |
| $w_k \in \mathbb{R}^D$ | tham số mô hình | Checkpoint toàn cục |
| $\tau_k, T_k$ | s | Thời điểm bắt đầu và thời lượng vòng |
| $r_m, q_u \in \mathbb{R}^3$ | m | Vị trí client/UAV, độ cao UAV dương |
| $p_m>0, \sum_m p_m=1$ | không thứ nguyên | Trọng số quần thể cố định trước thí nghiệm |
| $s_{mu}, z_{mu}$ | $\{0,1\}$ | Gán training/probing tới UAV |
| $b_{mu}^r$ | Hz | Bandwidth pha $r \in \{\text{P},\text{T}\}$ |
| $f_m^r$ | cycle/s | Tần số CPU pha $r$ |
| $C_m^r, L_m^r$ | cycle, bit | Workload và payload pha $r$ |
| $P_m^{\rm tx}, P_i^{\rm idle}$ | W | Công suất phát và baseline |
| $\kappa_m$ | $\text{J}\cdot\text{s}^2/\text{cycle}^3$ | Hệ số DVFS trong $\kappa C f^2$ |
| $B_u^{\rm bw}, b_{\min}$ | Hz | Pool bandwidth UAV và allocation tối thiểu |
| $Q_i^k, Q_i^{\rm res}$ | J | Pin và pin dự trữ của nút $i$ |
| $h_{mu}, N_0$ | không thứ nguyên, W/Hz | Power gain và noise PSD |
| $I, \eta_k, B_{\rm loc}$ | bước, learning rate, mẫu | Giao thức local SGD cố định |
| $S, \mathcal{A}$ | tập client | Tập được chọn, tập upload thành công |
| $d, \bar{T}$ | s | Biến epigraph service time và cap thời lượng phục vụ |
| $\mathcal{H}_k$ | sigma-field/thông tin | Toàn bộ dữ liệu controller được phép biết |
| $\theta_k$ | trạng thái ẩn | Thống kê học, kênh chưa quan sát |
| $\beta_k$ | phân phối | Belief có điều kiện theo $\mathcal{H}_k$ |
| $B_{\rm search}, B_{\rm audit}$ | s hoặc GPU-s | Ngân sách đánh giá; không phải Joule vận hành |
| $\lambda$ thuộc simplex 3 chiều | không thứ nguyên | Preference dùng để chọn một lịch thực thi |

Mọi chỉ số $k$ bị bỏ trong bài toán snapshot đều được hiểu là cố định tại cùng một vòng. Tránh dùng cùng $B$ cho cả pin, bandwidth và ngân sách đánh giá. Với active client $m$, $a_m$ là UAV duy nhất có $s_{m,a_m}=1$ và $b_m=b_{m,a_m}$; với inactive client không đánh giá rate/service formula. Đặt $1 \le N_{\min} \le N_{\max} \le M$, $0 < f_m^{\min} \le f_m^{\max}$, $C_m, L_m > 0$, $\kappa_m > 0$; $d \ge 0$. Battery constraints áp dụng cho client/UAV dùng pin, không áp lên coordinator dùng điện lưới.

### 1.3. Kênh air-to-ground

Với khoảng cách 3D $d_{mu}=\|q_u-r_m\|$ và góc nâng $\theta_{mu}$ tính bằng độ:

\[
p_{\rm LoS}(\theta)=\{1+a_{\rm env}\exp[-b_{\rm env}(\theta-a_{\rm env})]\}^{-1}. \tag{S1}
\]

Đây là dạng mô hình xác suất LoS theo góc nâng từ Al-Hourani và cộng sự [R3]; tham số phải khớp môi trường. Không lấy trung bình path loss dB rồi coi đó là một realization của fading.

Lấy trạng thái $Z_{mu} \in \{\text{LoS}, \text{NLoS}\}$, xác suất theo S1. Một mô hình scenario có đơn vị rõ là:

\[
h_{mu}=\beta_{\rm ref}(d_{mu}/d_{\rm ref})^{-\alpha_{Z_{mu}}}
10^{-\chi_{Z_{mu}}/10}X_{mu},\qquad \mathbb E[X_{mu}\mid Z_{mu}]=1. \tag{S2}
\]

Ở đây $\beta_{\rm ref}$ là gain tại khoảng cách tham chiếu $d_{\rm ref}$; $\alpha$ là path-loss exponent; $\chi$ là excess attenuation dB. $X$ dùng Rician power gain khi LoS và exponential power gain khi Rayleigh/NLoS. Đây là **lựa chọn mô hình scenario**, không phải tuyên bố S2 được đo đúng ở mọi môi trường. Cần profile hoặc sweep độ nhạy.

Các UAV dùng pool phổ trực giao; bên trong mỗi UAV dùng OFDMA. Với fixed transmit power:

\[
R_{mu}(b,h)=\zeta b\log_2(1+P_m^{tx}h/(N_0b)),\quad 0<\zeta\le1. \tag{S3}
\]

$\zeta$ là hiệu suất giao thức đã hiệu chỉnh, không dùng Shannon capacity như goodput đo được. Rate chỉ được tính khi link active và $b>0$. DL/backhaul dùng goodput riêng đã đo hoặc cùng công thức với tham số riêng.

P0 sử dụng $h$ hiệu dụng cố định. P1 có thể chọn lower quantile gain $h_{\rm low}$ sao cho xác suất gain thấp hơn $h_{\rm low}$ không quá $\epsilon_{mu}$. Nếu phân bổ tổng $\epsilon_{mu}$ không quá $\epsilon_{\rm round}$ thì union bound cho bảo đảm thành công đồng thời dưới mô hình phân phối đã khai báo. **Ước lượng quantile từ ít mẫu không tự động có bảo đảm này.** Cần khoảng tin cậy quantile hoặc validation độc lập.

Với chuyển động cho trước, $q_u=q_u(\tau)$; cập nhật theo thời gian vật lý. Nếu kênh biến đổi trong upload, thời điểm hoàn tất giải từ tích phân goodput đạt payload, không còn mặc định $L/R$ ở đầu vòng.

### 1.4. Giao thức thời gian

P0 chốt barrier protocol:

1. Coordinator truyền checkpoint cho các UAV cần dùng.
2. UAV multicast checkpoint cho client được chọn.
3. Mỗi client compute rồi upload; các client chạy song song.
4. Các UAV tổng hợp; barrier sau khi tất cả nhóm cần thiết hoàn tất.
5. UAV backhaul song song trên các đường độc lập.
6. Coordinator tổng hợp.

Đặt $t_{\rm CDL}, t_{\rm UDL}, t_{\rm Uagg}, t_{\rm BH}, t_{\rm Cagg}$ là thời lượng từng pha. Multicast trong mỗi nhóm lấy rate của client chậm nhất; các UAV multicast song song. Tổng hợp tại UAV tính từ số model/byte được nhận và tốc độ đã profile. Backhaul song song lấy $\max_u L_u^{\rm agg}/R_u^{\rm BH}$; không dùng tổng nếu giao thức là song song.

\[
T_0(s)=t_{\rm CDL}+t_{\rm UDL}+t_{\rm Uagg}+t_{\rm BH}+t_{\rm Cagg},
\quad
T^T=T_0(s)+\max_{m\in S}\{C_m/f_m+v_m(b_m)\},
\quad v_m=L_m/R_{m,a_m}. \tag{S4}
\]

Phải lấy max của **compute cộng upload cho từng client**. Max compute cộng max upload là protocol khác.

Nếu optimizer chạy online, $T_k=t_{\rm opt}+T^T$; UAV hover cả lúc optimizer chạy. Nếu tìm kiếm là offline benchmark, $t_{\rm opt}$ chỉ vào ledger tính toán, không cộng giả tạo vào tất cả lịch vật lý.

P1 đặt hard timeout cho từng pha. Client có đủ bit trước timeout là thành công; khi thất bại vẫn tính phần compute, phát và chờ đã thực hiện. Không vừa tính L/R vô hạn trong deep fade vừa tuyên bố mọi vòng có deadline cứng.

### 1.5. Năng lượng và pin

Dùng power baseline cộng chi phí tăng thêm, tránh đếm static power hai lần:

\[
E_m^T=P_m^{idle}T_k+s_m\kappa_m C_m f_m^2+
s_m P_m^{tx,inc}v_m+E_m^{rx,DL}+E_m^{ctrl}. \tag{S5}
\]

S5 là ledger **toàn vòng P0** của client, với $E_m=E_m^T$ trong phiên không probe; baseline đã gồm thời gian chờ optimizer nếu chạy online. $P_m^{\rm tx}$ trong S3 là công suất RF phát ra, còn $P_m^{\rm tx,inc}$ là công suất điện tăng thêm so với baseline, chẳng hạn $P_m^{\rm tx}/\eta_m^{\rm PA}+P_m^{\rm circuit,inc}$ với hiệu suất PA $\eta_m^{\rm PA} \in (0,1]$. Không đồng nhất hai đại lượng nếu chưa hiệu chỉnh phần cứng.

Nếu dùng mô hình sleep thực, thay baseline bằng tích phân state-dependent power. Công thức giải tích CPU về sau chỉ áp dụng cho S5 hoặc mô hình được chứng minh tương đương. Khi chuyển sang C, phải tách ledger toàn vòng thành các khoảng không giao nhau như mục 5.2, không cộng lại S5 cùng một ledger optimizer khác.

Mô hình propulsion rotor ở bay ngang đều [R4]:

\[
P_{\rm prop}(v)=
P_0(1+3v^2/U_{\rm tip}^2)
+P_{\rm ind}\left(\sqrt{1+v^4/(4v_0^4)}-v^2/(2v_0^2)\right)^{1/2}
+\tfrac12 d_0\rho_{\rm air}\varsigma A_{\rm rotor}v^3. \tag{S6}
\]

$P_0$ và $P_{\rm ind}$ tính bằng W; $U_{\rm tip}$ và $v_0$ bằng m/s; $d_0$ và solidity $\varsigma$ không thứ nguyên; $\rho_{\rm air}$ bằng $\text{kg/m}^3$; $A_{\rm rotor}$ bằng $\text{m}^2$. Mô hình giả thiết loại rotor, điều kiện bay và tham số tương ứng; không dùng cho fixed-wing hoặc tăng tốc/leo cao tùy ý.

Tại hover, $P_{\rm hover}=P_0+P_{\rm ind}$, do đó:

\[
E_u=P_u^{hover}T_k+P_u^{elec,idle}T_k+
E_u^{rx,UL}+E_u^{tx,DL}+E_u^{agg}+E_u^{tx,BH}. \tag{S7}
\]

Mọi UAV đang được giữ trên không đều trả hover, kể cả không nhận client. Trong base model $E_u^{\rm rx,UL}=\sum_m s_{mu} P_{mu}^{\rm rx,inc} v_m$; đây là mô hình incremental processing theo stream cần profile. Nếu phần cứng chỉ bật một receiver chung, thay bằng thời gian receiver thực sự bật.

\[
E_k=\sum_m E_m+\sum_u E_u+E_0,\qquad
Q_i^{k+1}=Q_i^k-E_i^k\ge Q_i^{res}. \tag{S8}
\]

E_0 gồm baseline, tx, rx, tổng hợp và online optimization tại coordinator; các hạng tăng thêm không chứa lại baseline đã tính. Nếu coordinator dùng lưới điện, E_0 vẫn vào tổng hệ thống nhưng không trừ pin UAV. S8 trừ pin chỉ với các nút có pin.

Q_u^res ít nhất phải đủ năng lượng return/landing cộng biên an toàn đã chọn. Với quỹ đạo thay đổi, return reserve có thể phụ thuộc vị trí; không cố định tùy tiện.

### 1.6. Toàn bộ ràng buộc snapshot P0

\[
s_{mu}\in\{0,1\},\quad s_m=\sum_us_{mu}\le1,\quad
s_{mu}\le e_{mu},\quad N_{\min}\le\sum_ms_m\le N_{\max}. \tag{S9}
\]

\[
b_{\min}s_{mu}\le b_{mu}\le B_u^{bw}s_{mu},\quad
\sum_m b_{mu}\le B_u^{bw},\quad
f_m^{min}s_m\le f_m\le f_m^{max}s_m. \tag{S10}
\]

\[
C_m/f_m+v_m(b_m)\le d\;(m\in S),\quad
T_0(s)+d+t_{\rm opt}\le T_{\max},\quad
E_i\le Q_i^k-Q_i^{res}. \tag{S11}
\]

$e_{mu}$ là mask dựa trên khả năng kết nối/được phép phục vụ, không phải biến tự do. $f_{\min}>0$; $b_{\min}>0$. Inactive client không đánh giá biểu thức 0/0.

$N_{\min}=1$ nếu ứng dụng cho phép. Chỉ đặt $N_{\min} \ge 2$ khi có yêu cầu nghiệp vụ/aggregation cụ thể, không để ép kết quả “trông giống FL”. Selected-set FL với một client là update một client; vẫn hợp lệ nhưng không chứng minh lợi ích hợp tác trong vòng đó.

Nếu thêm yêu cầu phủ khu vực: $\sum_{m \in \mathcal{G}_g} s_m \ge r_g$, phải chỉ rõ $\mathcal{G}_g$ là nhóm địa lý công khai và lý do SLA. Không dùng nhãn riêng chưa quan sát để đặt ràng buộc online miễn phí. Chứng minh khả thi trước khi bật tất cả quota.

Không có lịch khả thi: dừng phiên hoặc thực thi recovery đã khai báo (return/landing/wait nếu còn pin), tính đủ chi phí; không bỏ mẫu thí nghiệm này.

---

### 1.7. Một giao thức P1 cụ thể để mô phỏng lỗi truyền

Để tránh để “outage extension” ở mức khẩu hiệu, có thể chốt phiên bản đầu như sau. Từ thông tin trước execution, đặt gain thiết kế $h_{mu}^{\rm des}>0$ và rate mã hóa $r_{mu}^{\rm code}=R(b_{mu},h_{mu}^{\rm des})$. Client dành đúng $v_{mu}=L_m/r_{mu}^{\rm code}$ giây phát sau compute, không tự tăng rate khi realization tốt hơn, không retransmission trong pha.

\[
A=\{m\in S:R(b_m,h_m^{actual})\ge r_m^{code}\},
\qquad
T_{\rm service}=\max_{m\in S}(C_m/f_m+v_m). \tag{S12}
\]

Đây là block-fading coded-link approximation: gain actual cố định trong một lần upload, packet/model thành công hoặc thất bại theo khả năng giải mã. Nếu coherence time ngắn hơn payload duration, phải chia packet/block và mô phỏng accumulated successful bits; không dùng nguyên S12.

Mọi client trong $S$ trả compute và tx energy, kể cả $m \notin \mathcal{A}$. UAV aggregation/backhaul dùng $\mathcal{A}$ và mask nhóm thành công; empty success giữ checkpoint. Để bảo đảm deadline/pin trước khi biết $\mathcal{A}$, dùng upper bound các pha với toàn $S$:

\[
\max_{A\subseteq S}T(s,b,f,A)\le T_{\max},\qquad
\max_{A\subseteq S}E_i(s,b,f,A)\le Q_i-Q_i^{res}. \tag{S13}
\]

Trong giao thức mà aggregation/backhaul costs tăng theo số update nhận, full-success S là bound bảo thủ. Nếu protocol không đơn điệu theo A, phải tính worst case đúng hoặc dùng bound khác; không mặc nhiên chọn S.

P1 learning objective là $\mathbb{E}_{\rm channel,SGD}[L_{\rm val}(w^+(\mathcal{A}))]$. Khi $\mathcal{A}$ rỗng vẫn ghi loss của $w$ hiện tại, không bỏ lần đánh giá. Gain thiết kế/quantile và reliability allocation là tham số protocol cố định trong bản đầu, không phải decision variables chưa có constraint. Có thể mở rộng tối ưu chúng nhưng phải thêm miền giá trị, observation model và chance-constraint certificate tương ứng.

---

## 2. Mô hình học và bài toán nhiều vòng

### 2.1. Quần thể mục tiêu, đầu vào và đầu ra

\[
F_m(w)=\frac1{n_m}\sum_{\xi\in D_m}\ell(w;\xi),\quad
F(w)=\sum_m p_mF_m(w),\quad
L_{\rm val}(w)=\sum_m\frac{p_m}{|V_m|}\sum_{\xi\in V_m}\ell_{\rm val}(w;\xi). \tag{L1}
\]

p_m được chọn theo ứng dụng: tỷ lệ mẫu, đều theo thiết bị, hoặc tỷ trọng vùng. Không đổi p_m khi loại client yếu. Train/search-validation/audit-validation/test tách nhau. Mục tiêu population ở đây là quần thể được xác định trong L1, không phải tự động bảo đảm generalization tới phân phối thực chưa biết.

Input: checkpoint, local datasets do evaluator giữ, physical state, giao thức SGD, target weights, thông tin cho phép và ngân sách. Output: archive lịch khả thi, objective kèm độ bất định và một quyết định thực thi theo preference cố định.

\[
w_{m,0}=w_k,\quad
w_{m,i+1}=w_{m,i}-\eta_k\widehat\nabla F_m(w_{m,i}),
\quad \Delta_m=w_{m,I}-w_k. \tag{L2}
\]

Với A là tập upload thành công:

\[
w_{k+1}=w_k+\sum_{m\in A}\alpha_m(A)\Delta_m,\quad
\alpha_m(A)=p_m/\sum_{j\in A}p_j. \tag{L3}
\]

Nếu $\mathcal{A}$ rỗng, giữ $w_k$. UAV tổng hợp bằng $p_m/P_u$; coordinator tổng hợp bằng $P_u/\sum_v P_v$. Nhân hai trọng số cho ra $\alpha_m(\mathcal{A})$, chứng minh aggregation phân cấp đúng bằng aggregation phẳng. Equal-weight averaging giữa UAV không đúng nếu population mass khác nhau.

### 2.2. Bài toán gốc: tối ưu chính sách nhiều vòng

Trạng thái đầy đủ $X_k=(w_k,Q^k,\tau_k,\text{geometry},\theta_k)$; $\mathcal{H}_k$ là lịch sử quan sát. Chính sách phải đo được theo $\mathcal{H}_k$:

\[
\min_{\pi}\mathbf J_K(\pi)=
\left(
\mathbb E L_{\rm val}(w_K),
\mathbb E\sum_{k=0}^{K-1}E_k,
\mathbb E\sum_{k=0}^{K-1}T_k
\right), \tag{L4}
\]

với L2–L3, S8–S11 ở mọi vòng và $\tau_{k+1}=\tau_k+T_k$. Fixed $K$ đếm các lượt điều khiển đã định nghĩa; dropout không được bỏ khỏi thống kê để làm đẹp kết quả. Có thể dùng trạng thái kết thúc nhiệm vụ hấp thụ, giữ model và không phát sinh thêm training cost sau landing; phải báo cáo số vòng hoàn tất và tỷ lệ dừng sớm.

Với deadline nhiệm vụ thực tế, biến thể rõ hơn là:

\[
\min_\pi\left(
\mathbb E L_{\rm val}(w(\mathcal T)),
\mathbb E E_{\rm mission},
\mathbb E T_{\rm stop}
\right),\quad
T_{\rm stop}\le\mathcal T,\;\; Q_i\ge Q_i^{res}. \tag{L5}
\]

Trong L5, T_stop là thời điểm hoàn tất toàn nhiệm vụ, gồm return/landing nếu có, và E_mission gồm cả các pha đó. Kết thúc local training có thể sớm hơn T_stop. Model được giữ đến thời điểm đánh giá chung Tcal; return reserve chỉ là ràng buộc khả thi, không tự thay thế năng lượng return thực trong ledger. Nếu mọi thuật toán bị buộc chạy hết cùng Tcal thì objective thời gian là hằng số và phải bỏ, không gọi đó là tối ưu ba mục tiêu.

**Điểm cần giữ rõ:** lặp lời giải một vòng K lần không tương đương giải L4. Nó là chính sách myopic. Muốn phát biểu bài báo về huấn luyện FL thực sự, phải có đường cong nhiều vòng và resource-to-target, không chỉ snapshot HV.

### 2.3. Cận FL chung, dùng được cho cả A/B/C

Các giả thiết chỉ phục vụ định lý sau:

- $F$ và từng $F_m$ khả vi $L$-smooth trên miền chứa toàn bộ iterates và các đoạn nối cần dùng; $F \ge F_{\inf}$.
- Minibatch gradient unbiased, conditional variance $\le \sigma^2$.
- Second moment có điều kiện của mỗi stochastic gradient, theo lịch sử trước bước SGD và các thông tin đã dùng chọn lịch, $\le G^2$. Đây là cận uniform qua client/iterate khả dĩ; một cận trung bình vô điều kiện trên toàn client không đủ khi scheduler ưu tiên client có gradient lớn.
- Chọn lịch dựa vào thông tin trước execution. Đặt G_k là sigma-field gồm checkpoint, lịch sử, lựa chọn lịch và randomness đã dùng để chọn lịch. Có điều kiện theo G_k, successful set A độc lập với **toàn bộ seed stream của local SGD đang thực thi**; các client dùng RNG độc lập. Nếu probe gradient đã dùng một minibatch để chọn client, execution dùng minibatch/seed mới. Independence chỉ với từng noise riêng lẻ không đủ cho các phép conditioning sau.
- $\Gamma_k=\eta_k I \le 1/L$. Kiến trúc ReLU không mặc nhiên thỏa global smoothness; có thể kiểm chứng mô hình trơn nhỏ cho lý thuyết và báo cáo CNN thực là thực nghiệm ngoài giả thiết.

Gọi $g_k=\nabla F(w_k)$, và $v_k=(w_k-w_{k+1})/\Gamma_k$. Đặt $e_k=v_k-g_k$. Smoothness cho:

\[
F(w_{k+1})\le F(w_k)
-\frac{\gamma_k}{2}\|g_k\|^2
+\frac{\gamma_k}{2}\|e_k\|^2
-\frac{\gamma_k}{2}(1-L\gamma_k)\|v_k\|^2. \tag{L6}
\]

**Chứng minh:** dùng descent lemma $F(w-\gamma v) \le F(w) - \gamma \langle g,v \rangle + \frac{L\gamma^2}{2}\|v\|^2$ và đồng nhất thức $2\langle g,v \rangle = \|g\|^2 + \|v\|^2 - \|v-g\|^2$. Đây là bất đẳng thức theo từng realization; chưa cần giả định unbiased selection.

Với successful set không rỗng:

\[
e_k=
\underbrace{\sum_{m\in A}\alpha_m\nabla F_m(w_k)-g_k}_{b_k}
+\underbrace{\sum_{m\in A}\frac{\alpha_m}{I}
\sum_{i=0}^{I-1}[\nabla F_m(w_{m,i})-\nabla F_m(w_k)]}_{d_k}
+\underbrace{\sum_{m\in A}\frac{\alpha_m}{I}\sum_i\zeta_{m,i}}_{n_k}. \tag{L7}
\]

$\zeta$ là stochastic gradient trừ conditional mean. Đặt $D_k=\|b_k\|^2; J_k=\|d_k\|^2; V_k=\|n_k\|^2$. Bất đẳng thức tổng ba vector:

\[
\mathbb E\|e_k\|^2\le3(\mathbb ED_k+\mathbb EJ_k+\mathbb EV_k). \tag{L8}
\]

Dùng Jensen, smoothness và $\|\sum_{j<i}\hat{g}_j\|^2 \le i \sum_{j<i}\|\hat{g}_j\|^2$:

\[
\mathbb E[J_k\mid\mathcal G_k,A]\le
L^2\eta_k^2G^2\frac{(I-1)(2I-1)}6,\qquad
\mathbb E[V_k\mid\mathcal G_k,A]\le\frac{\sigma^2}{I}\sum_{m\in A}\alpha_m^2. \tag{L9}
\]

L9 áp dụng cho A không rỗng. Cận thứ hai dùng orthogonality của martingale noise giữa bước và độc lập giữa client, sau khi conditioning theo G_k,A. Cận thứ nhất dùng Jensen theo client và bước, rồi trung bình i² qua i=0,…,I−1. Lấy kỳ vọng ngoài cho ra các cận vô điều kiện cần trong L10. Nếu selection/failure phụ thuộc cùng execution seed stream, không áp dụng L9 trực tiếp; giữ bất đẳng thức theo realization L6–L8 hoặc xây cận khác. Audit/execution dùng seed độc lập tránh chọn lịch dựa vào chính realization rồi gọi đó là unbiased.

Cho $0<\gamma \le 1/L$ không đổi, initial checkpoint $w_0$ cố định và $\mathcal{A}$ luôn không rỗng, cộng L6 và dùng L8:

\[
\frac1K\sum_{k=0}^{K-1}\mathbb E\|\nabla F(w_k)\|^2
\le
\frac{2(F(w_0)-F_{\inf})}{\gamma K}
+\frac3K\sum_k(\mathbb ED_k+\mathbb EJ_k+\mathbb EV_k). \tag{L10}
\]

**Kết luận chính xác:** stationarity bị giới hạn bởi selection bias, local drift và stochastic noise. Không chứng minh global optimality, không bảo đảm test accuracy và không bảo đảm lỗi về 0 nếu D_k không giảm.

Nếu có xác suất mọi client đều thất bại, L6 vẫn đúng với =0, e_k=-g_k$. Trong L8–L10 phải thay cận sai số bằng $\mathbb{E}[\mathbf{1}_{\mathcal{A} \neq \emptyset} 3(D_k+J_k+V_k) + \mathbf{1}_{\mathcal{A} = \emptyset} \|g_k\|^2]$. Không được bỏ hạng all-failure để tuyên bố cùng tốc độ hội tụ.

L10 phân tích training $, trong khi mục tiêu tối ưu là validation {\rm val}. Liên hệ generalization cần giả thiết thống kê riêng; báo cáo không đánh tráo hai đại lượng này.

### 2.4. Biên sai số thông tin cũ

Nếu report của client m được đo tại w_m^last có sai số norm tối đa epsilon_m thì:

\[
\|\widehat g_m^{last}-\nabla F_m(w_k)\|
\le \epsilon_m+L_m\|w_k-w_m^{last}\|. \tag{L11}
\]

Đây là hệ quả trực tiếp của tam giác và smoothness. Tuổi thông tin theo giây không đủ trong dữ liệu stationary: model drift mới là hạng toán học trực tiếp. Nếu dữ liệu thay đổi theo thời gian và có cận drift gradient $\nu_m$ thì cộng $\nu_m(\tau_k-t_m^{\rm last})$, với giả thiết được nêu riêng.

Với residual $r(S)=\sum_{m \in S}\alpha_m g_m - \sum_m p_m g_m$ và estimate $\hat{r}$:

\[
\|r(S)-\widehat r(S)\|\le
\sum_{m\in S}\alpha_m\epsilon_m^k+\sum_m p_m\epsilon_m^k
=:e(S). \tag{L12}
\]

Do đó $\max(0,\|\hat{r}\|-e)^2 \le D(S) \le (\|\hat{r}\|+e)^2$. Client chưa có report phải có cận/prior thực, không điền gradient $0$ với uncertainty $0$. Nếu chỉ biết một subpopulation, phải gọi score là matching subpopulation, không phải certified population matching.

Sketch projection chỉ bảo toàn norm trên không gian/tập vector được bảo đảm. Một phép chiếu ít chiều có nullspace nên không thể kiểm soát mọi vector thích nghi. Muốn certificate uniform: subspace embedding cho span gradient cố định, hoặc holdout projection độc lập sau khi khóa candidate; còn sketch dùng trong search chỉ là heuristic.

---

### 2.5. Validation là dịch vụ có điều kiện quan sát, không phải dữ liệu miễn phí

A/B offline được phép gọi evaluator L1 trên các local held-out sets trong simulator. Với C online, có hai cấu hình hợp lệ cần chọn trước:

1. Coordinator có một tập đánh giá đại diện được thu thập độc lập và được phép sử dụng. Phải kiểm tra distribution mismatch với target population; không mặc định đại diện hoàn hảo.
2. Distributed validation: gửi model tới các validation participants, tính loss cục bộ, truyền aggregate statistic. Thời gian download/forward pass/upload và pin được tính như một pha riêng; có thể trả feedback trễ.

Candidate prediction trong C không được gửi hàng nghìn model tới toàn bộ client rồi gọi đó là “surrogate inference” miễn phí. Chỉ mô phỏng/predict offline; feedback thực tế chỉ từ các operation đã chi trả. Test set không dùng cập nhật scheduler.

Nếu có validation feedback phase trong deployment, thêm T_val,E_val và model-version của feedback vào state/ledger. Resource solver A5 vẫn áp dụng chỉ khi các chi phí phụ thêm có đúng cấu trúc cố định/lồi được nêu; nếu không thì phải phân tích lại.

---

## 3. Direction A: tối ưu theo tập client với bộ cấp tài nguyên có chứng minh

### 3.1. Mô hình A0: reference-evaluated one-round scheduling

Tại snapshot X_k cố định, P0 và local work cố định, d là biến phụ epigraph của S11, không là số bước SGD hay deadline tự thay đổi giao thức:

\[
\boxed{\min_{s,b,f,d}\;(\mu_k(S),E_k(s,b,f),T_k(s,b,f))}
\quad\text{s.t. S9–S11},\qquad
\mu_k(S)=\mathbb E_\xi L_{\rm val}(w_{k+1}(S;\xi)). \tag{A1}
\]

Đây là mixed-integer, nonlinear, stochastic black-box multiobjective problem. Phần chọn tập có tối đa sum_{j=Nmin}^{Nmax} binomial(M,j) tập; mỗi tập có tối đa U^j phép gán. Liệt kê tăng theo hàm mũ. Điều này **không tự nó là chứng minh NP-hard** cho mọi instance CNN; nếu muốn ghi NP-hard trong bài phải cho phép quy dẫn một lớp con cụ thể.

Đầu vào optimizer không được truy cập gradient hiện tại ngoài quyền oracle offline đã khai báo. Reference evaluator được gọi là dịch vụ đánh giá; không đồng nghĩa controller có các phép đo đó miễn phí ngoài đời.

### 3.2. Mệnh đề A1: learning objective chỉ phụ thuộc tập

Trong P0, local SGD không phụ thuộc bandwidth/CPU, tất cả update được nhận và aggregation đúng L3. Vì vậy, với cùng checkpoint, local settings và seed bundle:

\[
S(x)=S(y)\implies w_{k+1}(x;\xi)=w_{k+1}(y;\xi)
\implies \mu_k(x)=\mu_k(y). \tag{A2}
\]

**Chứng minh:** L2 giống nhau theo từng client; hệ số L3 chỉ phụ thuộc p và tập S. Gán UAV bị triệt tiêu do nhân trọng số phân cấp. Nguồn khác biệt còn lại chỉ là physical costs.

**Hệ quả triển khai:** mỗi tập client là một đơn vị đánh giá learning, còn các phương án tài nguyên là các biến thể energy–time của tập đó. Cache update keyed bởi checkpoint/client/seed/config; cache loss keyed thêm tập S, validation protocol. CPU/bandwidth không thuộc learning-cache key trong P0.

**Giới hạn:** mất A2 khi CPU quyết định số bước hoàn tất, compression thay đổi theo tài nguyên, timeout làm đổi successful set, hoặc local optimizer phụ thuộc thời gian. Trong P1, có thể chia sẻ conditional loss theo successful subset A nhưng expected loss của lịch vẫn phụ thuộc phân phối A(s,b,f).

### 3.3. Mệnh đề A2: bài toán tài nguyên lồi khi cố định tập và gán

Với $s$ cố định, các $h_{mu}>0$ cố định, đặt $a=P^{\rm tx}h/N_0$:

\[
R(b)=\frac{\zeta}{\ln2}b\ln(1+a/b),\quad
R'(b)=\frac{\zeta}{\ln2}\{\ln(1+a/b)-a/(a+b)\}>0,
\quad
R''(b)=-\frac{\zeta a^2}{\ln2\,b(a+b)^2}<0. \tag{A3}
\]

Do $R$ dương, lõm và $1/x$ lồi giảm, $v(b)=L/R(b)$ lồi trên $b>0$. $C/f$ lồi khi $f>0$; $\kappa C f^2$ lồi. Trong S5–S7, fixed-assignment energy có dạng:

\[
E(b,f,d)=E_{\rm fixed}(s)+P_{\rm base}(T_0(s)+d)
+\sum_{m\in S}\kappa_m C_m f_m^2+\sum_{m\in S}a_m^{radio}v_m(b_m), \tag{A4}
\]

với các hệ số công suất không âm. E_fixed gồm DL, aggregation, BH cố định theo gán; P_base gồm hover và baseline đã phân bổ đúng vào ledger. Ở đây DL/backhaul dùng pool riêng và tốc độ, công suất, CPU aggregation cố định; nếu dùng chung resource đang tối ưu thì T_0/E_fixed không còn hằng theo s.

Cần tính lồi **cho từng ledger E_i**, không chỉ tổng E: mỗi ledger trong A5 phải có dạng constant không âm cộng hệ số không âm nhân d, f_m² và v_m(b_m), như S5–S7. Một tổng lồi không suy ra từng battery constraint lồi. A4–A5 dùng T_0+d để lập epigraph; actual physical time vẫn theo S4.

Cho deadline cap phục vụ $0<\bar{T} \le T_{\max}-t_{\rm opt}$ đã cố định tại snapshot ($t_{\rm opt}=0$ trong offline physical benchmark), giải:

\[
\begin{aligned}
\mathcal R(s,\bar T):\quad \min_{b,f,d}\;&E(b,f,d)\\
\text{s.t. }\;&C_m/f_m+v_m(b_m)\le d,\quad T_0(s)+d\le\bar T,\\
&b_{\min}\le b_m,\quad \sum_{m:a_m=u}b_m\le B_u^{bw},\\
&f_m^{min}\le f_m\le f_m^{max},\quad E_i(b,f,d)\le Q_i-Q_i^{res}.
\end{aligned} \tag{A5}
\]

Mọi constraint là convex sublevel hoặc affine, nên A5 là convex optimization; quy tắc hợp hàm lồi và KKT/Slater dùng theo lý thuyết chuẩn [R16]. Nếu khả thi, miền compact và objective liên tục thì có nghiệm. Slater là điều kiện đủ cho strong duality và KKT cần–đủ; ở boundary không được mặc nhiên dùng Slater. Một nghiệm thỏa KKT vẫn đủ tối ưu với bài toán convex.

$d$ là biến epigraph của service time. $P_{\rm base}>0$ bảo đảm nghiệm tối ưu không giữ $d$ lớn hơn cần thiết; mọi ledger dùng $T_0+d$ nhất quán. Online $t_{\rm opt}$ cố định cho một call có thể cộng hằng; nếu bản thân $t_{\rm opt}$ là biến phụ thuộc tìm kiếm thích nghi, cần mô hình thêm, không nhét vào A5 như hằng giả.

**Ý nghĩa:** thay vì MOEA tiến hóa mọi CPU và bandwidth, MOEA chỉ đề xuất S/gán và deadline cap; bộ giải lồi trả về resource allocation tối ưu cho cap đó. NSGA-II/MOEA/D vẫn là baseline tìm kiếm tổ hợp, không phải nơi chứng minh KKT cho toàn bài toán.

A5 có thể giải qua convex solver với derivative phù hợp. Không được mặc định mọi solver DCP nhận nguyên biểu thức 1/[b log(1+a/b)]; có thể dùng epigraph rate r<=R(b), v>=L/r và constraint C/f+v<=d, rồi kiểm tra discipline/solver hỗ trợ.

### 3.4. Mệnh đề A3: decoder CPU và phân rã Pareto

Với $b,d$ cố định và chỉ dynamic CPU tăng theo $f$:

\[
f_m^\star(b,d)=\max\{f_m^{min},C_m/[d-v_m(b)]\}, \tag{A6}
\]

nếu $d>v_m$ và $f_m^\star \le f_m^{\max}$; ngược lại infeasible.

**Chứng minh:** constraint tương đương $f_m \ge C_m/(d-v_m)$; energy $\kappa C f^2$ tăng nghiêm ngặt theo $f>0$. Chọn lower bound khả thi. Baseline toàn vòng cố định theo $d$ nên không đổi lập luận. Với CPU leakage chỉ khi active, energy có thêm $P_{\rm leak} C/f$ và nghiệm không còn A6: điểm cực tiểu không ràng buộc là $[P_{\rm leak}/(2\kappa)]^{1/3}$, rồi xét lower/upper bounds.

Gọi $\mathcal{P}_{\rm res}(S)$ là các cặp energy–time không bị trội trong hợp tất cả gán và resource feasible của $S$. Khi đó:

\[
\mathcal P_{\rm full}
=
\operatorname{ND}\!\left[
\bigcup_{S\ {\rm feasible}}\{(\mu_k(S),E,T):(E,T)\in\mathcal P_{\rm res}(S)\}
\right]. \tag{A7}
\]

**Chứng minh:** lịch bị trội về $E,T$ trong cùng $S$ có loss giống nhau theo A2, nên không thể là điểm Pareto đầy đủ. Ngược lại, sau khi bỏ các lịch này, không mất vector không trội; ND ngoài cùng loại domination giữa các tập. A7 là đẳng thức theo objective vectors, không khẳng định nghiệm quyết định là duy nhất.

Khi A5 có nhiều nghiệm đồng năng lượng, chọn nghiệm có actual time nhỏ nhất (lexicographic tie-break: tối thiểu $E$ trước, rồi $T$ với ràng buộc lồi $E \le E^\star$; vì $E^\star$ là minimum nên các nghiệm khả thi của bước này có $E=E^\star$). Cách này tránh giữ nghiệm weakly efficient nhưng bị trội về thời gian. Mỗi resource Pareto vector $(E^\star,T^\star)$ của một gán được khôi phục khi đặt $\bar{T}=T^\star$ và giải chính xác với tie-break: một nghiệm có $E$ nhỏ hơn, hoặc $E$ bằng mà $T$ nhỏ hơn, sẽ mâu thuẫn tính Pareto. Sau đó lấy hợp các gán và lọc ND như A7.

Sweep bar_T trên lưới hữu hạn chỉ cho xấp xỉ. Không ghi “front chính xác” nếu chưa có bound discretization và solver tolerance. Với miền tài nguyên có biên khả thi và Lipschitz constants hữu hạn, có thể suy cận từ sai số lưới; gần biên coverage/feasibility phải chứng minh riêng. Trong code, hai vòng solve có tolerance phải báo sai số E và feasibility, không gọi tie-break xấp xỉ là đẳng thức exact.

### 3.5. Toán tử set-aware: dùng proxy đúng vai trò

Với report cho phép, residual score là $\hat{D}(S)=\|\sum \alpha_m \hat{g}_m - \hat{g}_{\rm pop}\|^2$. Có thể dùng $U_D(S)=(\|\hat{r}(S)\|+e(S))^2$ nếu thực sự có cận L12.

Với hoán đổi i ra, j vào:

\[
P_S=\sum_{m\in S}p_m,\quad v_S=\sum_{m\in S}p_m\widehat g_m,\quad
\widehat g_{S-i+j}=
\frac{v_S-p_i\widehat g_i+p_j\widehat g_j}{P_S-p_i+p_j}. \tag{A8}
\]

Công thức có chuẩn hóa lại, không lấy đơn giản g_S−g_i+g_j khi p khác nhau. Duy trì v_S,P_S giúp mỗi swap mất O(d_s) với sketch dimension d_s.

Hướng dẫn proposal bằng cận robust chỉ khi known errors; nếu report thiếu, dùng empirical proxy và luôn có generic mutation/exploration. Survival offline dùng actual validation loss, không dùng D_hat làm nhãn “ground truth”.

**Phản ví dụ tính đơn điệu:** equal weights, gradient ba client (1,−1,0), population gradient 0. D({3})=0 nhưng D({1,3})=1/4. Thêm client có thể làm proxy xấu đi.

**Phản ví dụ submodularity:** với utility $V=-D$, chọn $A=\{3\}, B=\{1,3\}, j=2$. Khi đó $A \subseteq B$ nhưng hai marginal lần lượt là $-1/4$ và $+1/4$, vi phạm diminishing returns: $\text{marginal}(A) \ge \text{marginal}(B)$. Phản ví dụ chỉ dùng tập không rỗng nên không phụ thuộc cách định nghĩa $V(\emptyset)$. Không được gán bảo đảm greedy $1-1/e$ cho utility này.

### 3.6. A-H: mở rộng horizon ngắn có kiểm soát

Để kiểm tra ảnh hưởng của myopic scheduling và hiện tượng v1 chọn một client, nghiên cứu thêm H=2 hoặc 3. Horizon dài hơn không bảo đảm sẽ chọn nhiều client hay cải thiện kết quả:

\[
\min_{\pi_{k:k+H-1}}
\left(
\mathbb E L_{\rm val}(w_{k+H}),
\mathbb E\sum_{t=k}^{k+H-1}E_t,
\mathbb E\sum_{t=k}^{k+H-1}T_t
\right), \tag{A9}
\]

ràng buộc model, pin, clock ở từng bước và H<=K−k. Chỉ thực thi quyết định đầu rồi tối ưu lại. Chính sách future trong scenario tree phải nonanticipative: nhánh có cùng observation history phải dùng cùng hành động. Tối ưu độc lập mỗi nhánh với biết trước hidden truth là optimistic oracle, không phải chính sách online hợp lệ.

Phiên bản dễ triển khai: candidate gồm lịch đầu và một **continuation policy cố định** cho H−1 vòng. Khi đó quyết định chỉ tối ưu trong lớp này, không tuyên bố tối ưu toàn bộ policy tree. Dùng chung continuation giữa các thuật toán.

A2 chỉ còn đúng tại mỗi checkpoint/transition; không cache toàn bộ trajectory chỉ bằng tập đầu, vì model và pin tương lai đã khác. Đây là setting có cơ sở thực hơn để Direction B tiết kiệm rollout cost.

Horizon ngắn không tự bảo đảm recursive feasibility. Muốn bảo đảm an toàn cần terminal reserve/terminal safe set chứa trạng thái có recovery khả thi; nếu không, chỉ báo cáo actual violations và stop rate.

### 3.7. Mã giả đề xuất

~~~text
A-STRUCT(snapshot, search_budget, deadline_grid, optimizer):
    Lock checkpoint, validation protocol, local work, seeds, target weights
    Create client-update cache and selected-set loss cache
    Seed population with multiple cardinalities and feasible associations
    while remaining search budget permits:
        Propose (selected set S, association a, deadline cap)
        Use generic variation, sometimes set-aware swap from authorized reports
        Check structural constraints and cheap lower bounds
        Solve convex resource problem R(S, a, deadline cap)
        If infeasible: record residuals; skip learning evaluation
        Else:
            Obtain loss(S) from lazy reference cache
            Store one learning record shared by resource variants
            Update population using NSGA-II or MOEA/D
            Update empirical nondominated archive
    Lock a deployment schedule using declared energy/time caps or preference
    Independently audit reported points; do not tune deployment on test data
    Execute only locked schedule; update model, physical clock, batteries, history
~~~

### 3.8. Bảo đảm thuật toán và độ phức tạp

Gọi N là population size; G số generation; Q số proposal; C_cvx độ phức tạp mỗi lần giải A5 tới tolerance; C_train chi phí local update/client/replicate; C_val chi phí validation một model; R số replicate; Q_S số tập duy nhất.

- Resource: O(Q C_cvx), lưu warm start theo gán.
- Local training cache một snapshot: tối đa O(R M C_train).
- Learning evaluation: O(R Q_S (|S|D+C_val)).
- NSGA-II sorting thông thường O(G N² J), J=3; MOEA/D update neighborhood cỡ T_neigh là O(Q T_neigh J), chưa tính evaluator.
- Guided swaps liệt kê cặp là O(|S|(M−|S|)d_s) mỗi proposal; shortlist r cặp giảm còn O(r d_s).
- Cache đầy đủ update có thể cần O(R M D) memory; dùng lazy/LRU nhưng log recomputation cost. Không lưu toàn model mọi candidate nếu không cần.

C_cvx được đo và phụ thuộc solver/tolerance; không thay bằng “O(1)” hoặc tuyên bố một số mũ universal cho mọi conic formulation.

**Bảo đảm hữu hạn trung thực:** A5 có global optimum dưới giả thiết convex; archive chỉ đúng trên ứng viên đã đánh giá, có sampling error. MOEA không được bảo đảm tìm full Pareto trong budget hữu hạn.

Một bảo đảm asymptotic có thể chứng minh trên **miền rời rạc hữu hạn**: nếu xác suất đề xuất mỗi feasible encoding, **có điều kiện theo toàn bộ lịch sử tìm kiếm trước bước đó**, luôn ít nhất $p_{\min}>0$, evaluation xác định và archive không cắt bỏ điểm Pareto, xác suất còn bỏ sót ít nhất một trong $N_X$ điểm sau $n$ bước không quá $N_X(1-p_{\min})^n$. Chứng minh bằng bound xác suất chưa ghé từng điểm và union bound. Điều kiện này không tự đúng cho SBX/continuous mutation hay noisy archive hiện tại, và không tạo bảo đảm runtime hữu ích.

### 3.9. Đóng góp và tiêu chí bác bỏ A

Đóng góp khả dĩ: khai thác equivalence classes theo tập; allocator lồi và reduction bảo toàn Pareto; set-aware proposals có uncertainty/staleness xử lý đúng; benchmark snapshot và episode nhất quán.

Đây là đóng góp cấu trúc/ứng dụng, **chưa đủ khẳng định bài thuật toán mới**. Nếu baseline dùng cùng cache/allocator và random/generic search có hiệu quả ngang nhau, phải báo cáo kết quả âm. Đừng chuyển sự cải thiện do allocator sang tên “set-aware intelligence”.

Thí nghiệm quyết định:

1. M=6: enumerate tập và gán trên lưới deadline; so khớp A7.
2. Đối chiếu resource solver và decoder bằng KKT residual/duality gap khi có.
3. Cùng ngân sách thực: generic NSGA-II, generic MOEA/D, random feasible, guided variants.
4. Checkpoint đầu/giữa/cuối; IID/non-IID; client rare/noisy đặt trên link tốt/xấu.
5. Episode nhiều vòng, không chỉ 5 local steps một lần. Đo test curve, macro-F1, rare recall và năng lượng/thời gian tới mức chất lượng chung.
6. A0 so A-H bằng cùng compute budget; H dài hơn chỉ có ý nghĩa nếu lợi ích vượt rollout overhead.

---

## 4. Direction B: đa fidelity có xét cache và kiểm tra sai số Pareto

### 4.1. Bài toán nào đang được tối ưu?

A1 vẫn là bài toán vận hành. Direction B thêm **meta-policy** rho quyết định query q_t=(x_t,ell_t,n_t): đánh giá candidate nào, fidelity nào và thêm bao nhiêu replicate.

\[
\min_{\rho}\ \mathbb E\,\mathcal E(\widehat{\mathcal A}_{\rho},\mathcal P)
\quad\text{s.t.}\quad
\sum_t c(q_t\mid\mathcal C_t)+c_{\rm fit}+c_{\rm manage}+B_{\rm audit}
\le B_{\rm total}. \tag{B1}
\]

C_t là trạng thái cache; c đo bằng wall-clock tuần tự hoặc GPU-seconds cộng trên các worker, đơn vị chốt trước. Với concurrent queries, tổng task wall-times không bằng elapsed wall-clock: phải dùng thời gian theo đồng hồ chung gồm overhead, hoặc chọn worker-seconds làm resource budget. Ecal có thể là loss hypervolume hoặc epsilon-coverage error. P là Pareto set của miền tham chiếu đã định nghĩa, không mặc nhiên biết trước để tính acquisition.

B_audit là phần trần ngân sách giữ trước; số đã chi thực tế phải được log riêng. Nếu query không thể ngắt và runtime chưa biết trước, chỉ có thể cam kết hard budget khi dùng upper bound thời gian hoặc cancellation protocol. Ngược lại phải báo actual overrun; không coi measured runtime sau khi chạy là chứng minh đã tuân hard cap.

B1 là budgeted sequential information acquisition problem. Một lịch vật lý rẻ không đồng nghĩa nó rẻ để mô phỏng; một query rẻ cũng không đồng nghĩa lịch thực thi tiết kiệm pin.

**Phân biệt hai setting:**

- B0: giải A0 nhiều ứng viên, dùng A2 để chia sẻ learning estimates theo tập. Phải đo xem cache có làm high fidelity đủ rẻ để bỏ multi-fidelity hay không.
- B-H: giải A-H hoặc continuation rollout H>=2. Cache chung ở root và prefix, nhưng model branching làm chi phí thật tăng. Đây là trường hợp nên thử nếu B0 không còn bottleneck.

### 4.2. Fidelity hierarchy không thay đổi bài toán đích

| Mức | Đánh giá learning | Chi phí | Có dùng để loại nghiệm chắc chắn? |
|---|---|---|---|
| L1 | Predictor từ tập sketch/history và state descriptors | Inference + cập nhật model | Chỉ nếu có cận uniform hợp lệ; mặc định không |
| L2a | Cùng full local update, ít validation samples/replicates | Giảm validation/Monte Carlo | Có thể nếu sampling unbiased, loss bounded và CI đúng |
| L2b | Ít local steps $I_\ell < I$ hoặc rollout ngắn hơn | Giảm training/rollout | Cần bias bound hoặc coupled discrepancy certificate |
| L3 | Full target work/horizon, reference validation | Cao nhất nhưng đã cache đúng | Vẫn là estimate stochastic, không phải exact population truth |

Energy/time ở mọi fidelity phải mô tả **target full-work schedule**. Không gán energy của I_ell bước cho lịch dự định chạy I bước. Với B-H, energy/time tương lai có thể stochastic vì model/decision thay đổi; khi đó cả ba objective cần intervals, không còn giả thiết “chỉ loss bất định”.

Predictor nên dùng permutation-invariant set features: weighted sketch sums/moments, selected mass, cardinality, uncertainty và checkpoint descriptors. Cross-round prediction dùng delta-loss hoặc conditioning rõ; không trộn raw loss từ checkpoint mới khởi tạo với checkpoint đã hội tụ.

### 4.3. Cấu trúc cache tạo ra chi phí query không cộng độc lập

Tại một snapshot và replicate r:

\[
c_{\rm HF}(S,r\mid\mathcal C)=c_{\rm lookup}
+\mathbf1[(S,r)\notin\mathcal C_{\rm loss}]
\left\{
\mathbf1[(S,r)\notin\mathcal C_{\rm model}]
\left[\sum_{m\in S:(m,r)\notin\mathcal C_{\rm update}}c_{m,r}^{train}
+c^{aggregate}(S,r)\right]
+c^{validation}(S,r)
\right\}. \tag{B2}
\]

C_update, C_model và C_loss là ba cache khác nhau; key còn gồm snapshot, fidelity/work config, validation protocol và RNG namespace. B2 mô tả query full-validation theo một seed r: hit loss chỉ trả lookup; hit aggregated model không phải retrain/reaggregate dù local-update cache đã bị evict. Khi validation chỉ lấy thêm mẫu, lưu sufficient statistics theo protocol thay vì coi một scalar loss cache là mọi mẫu mới; log công việc thực tế.

**Ví dụ:** hai tập S1={1,2}, S2={2,3}. Evaluate S1 rồi S2 chỉ cần ba local updates cho cùng replicate, không phải bốn. Hai resource schedules khác nhau nhưng cùng S1 chỉ cần một loss estimate. Khi tăng replicate index, các local updates mới vẫn phải tính; không xem cùng seed cache là một quan sát độc lập mới.

Hướng mới đề xuất: query ở cấp tập/prefix, credit tất cả resource variants được cập nhật confidence và tính **marginal cost sau cache**. Một acquisition per-candidate với cost cố định có thể ưu tiên sai. Cơ chế cache-aware/shared-query này cần đối chiếu sâu thêm với expensive optimization có reusable simulations; chưa tuyên bố là đầu tiên.

### 4.4. Điều kiện để có chứng nhận thống kê thật

Chứng nhận sau áp dụng cho **một snapshot và tập hữu hạn X_0 đã cố định trước giai đoạn certification**, gồm N_x lịch khả thi và Q tập client khác nhau. Có thể tạo X_0 bằng discovery search rồi khóa, sau đó dùng fresh seeds để certification. Khi ấy các mệnh đề đúng có điều kiện theo X_0; không bảo đảm xác suất tìm được các tập nằm ngoài X_0. Khóa cả validation target V_cert: nếu V_cert khác search-validation thì mu_cert(S) là một hàm khác mu_search(S). Toàn bộ intervals và coverage trong giai đoạn này phải dùng mu_cert, không giao CI từ hai corpus khác nhau. Independent audit seeds trên cùng corpus giữ nguyên target; đổi sang test/audit corpus khác thì phải đánh giá/chứng nhận lại target mới, không chuyển certificate sang nguyên xi.

- Chỉ đánh giá expected loss trên validation set cố định, randomness từ local SGD/declared scenarios. Không suy ra generalization tới quần thể thực chỉ từ CI này.
- Với mỗi (S,ell), có một chuỗi replicate iid định trước, cùng mean theo protocol cố định. Adaptive allocation chọn **stream và độ dài prefix**, không chọn tùy ý các seed thuận lợi sau khi thấy outcome/cache của tập hoặc fidelity khác.
- Có known bound $0 \le Y_\ell(S) \le L_{\max}$.
- Bias bound $|\mathbb{E}[Y_\ell(S)] - \mu(S)| \le b_\ell(S)$ phải là bound hợp lệ; $b_3=0$. Nếu $b_\ell$ chỉ được ước lượng với confidence $1-\delta_{\rm bias}$, coverage tổng phải trừ thêm $\delta_{\rm bias}$. Maximum discrepancy quan sát trên ít cặp không phải deterministic bias bound.
- Dùng cùng target distribution và full-work semantics.
- Correlation giữa các tập do common random numbers/cache được phép cho union bound; nhưng không được nhân số mẫu vì cùng một local update được dùng nhiều lần.

**Cross-entropy không bị chặn mặc định.** Để dùng Hoeffding có thể định nghĩa validation logits hữu hạn, ví dụ z'_c=A tanh(z_c/A), rồi CE<=2A+ln C_classes. Đây là thay đổi evaluator cần khai báo và áp dụng cho mọi baseline. Một lựa chọn khác là bounded Brier score. Nếu giữ raw CE như v1, chỉ được dùng chứng nhận dưới giả thiết tail/variance thích hợp đã kiểm chứng, hoặc báo cáo empirical confidence; không gán công thức bounded-loss như một định lý cho code hiện tại.

**Hai loại randomness không được nhập làm một.** Với L2a, chọn rõ một trong hai target:

1. Expected SGD outcome mu(S): mỗi replicate tạo một model từ một independent SGD seed bundle mới, rồi đánh giá full validation hoặc lấy mẫu validation unbiased. Có thể lấy client m với xác suất p_m rồi lấy đều một mẫu trong V_m; lấy đều từ hợp các V_m chỉ đúng khi tỷ trọng mẫu khớp p_m. Tăng số mẫu validation trên **cùng model đã cache** chỉ giảm nhiễu validation có điều kiện theo model đó; nó không làm tăng số independent SGD replicates.
2. Fixed-seed SAA target $\mu_R(S)=R^{-1} \sum_{r=1}^R L_{\rm val}(w^+(S;\xi_r))$: có thể lấy mẫu validation trên các model trong seed bank và chứng nhận **$\mu_R$ có điều kiện theo bank**. Muốn suy ra $\mu(S)$ phải thêm cận Monte Carlo từ $R$ independent training seed bundles; sampling validation vô hạn vẫn không loại được sai số hữu hạn $R$.

Chứng nhận B3 dưới đây dùng target thứ nhất, hoặc target thứ hai nếu đổi ký hiệu/claim rõ ràng. Ví dụ cực đoan: một model loss là Bernoulli(1/2), không có validation noise. Đọc lại cached loss n lần vẫn chỉ là một Bernoulli draw; CI co về 0 hoặc 1 không phải CI hợp lệ cho mean 1/2.

### 4.5. Định lý B1: confidence intervals đồng thời và an toàn với dừng thích nghi

Cho confidence failure probability delta thuộc (0,1), tolerance epsilon>0, và F_levels mức fidelity có sampling model và bias bound. Với n>=1 mẫu tại (S,ell), đặt:

\[
r_{\ell,n}=L_{\max}
\sqrt{\frac{\ln\{\pi^2 QF_{\rm levels}n^2/(3\delta)\}}{2n}},
\quad
I_{\ell,n}(S)=
[\bar Y_{\ell,n}-r_{\ell,n}-b_\ell,\,
 \bar Y_{\ell,n}+r_{\ell,n}+b_\ell]\cap[0,L_{\max}]. \tag{B3}
\]

Xác suất tất cả intervals chứa mu(S), đồng thời cho mọi S,ell,n, ít nhất 1−delta.

**Chứng minh:** Hoeffding cho xác suất vi phạm mỗi sample mean <=2 exp(−2nr²/L_max²)=6delta/(pi² QF_levels n²). Cộng theo Q tập, F_levels mức và n>=1; dùng tổng 1/n²=pi²/6. Sau đó n có thể được chọn thích nghi, vì event đã đúng đồng thời mọi n. Cộng bias bound bằng bất đẳng thức tam giác.

Lấy giao các interval hợp lệ theo fidelity và mọi prefix đã quan sát để tạo [l(S),u(S)] (chưa có mẫu thì dùng [0,L_max]). Giao rỗng là dấu hiệu model/bias/coverage lỗi hoặc event thất bại: log, không tùy tiện thay bằng interval rất hẹp. L1 empirical ensemble không có valid b_1 thì không được đưa vào giao để loại nghiệm; chỉ dùng chọn query.

B3 là bảo đảm cho fixed pool và fresh replicate streams; cấu hình mỗi fidelity và validation target được khóa trong giai đoạn certification. Refit predictor làm thay đổi sampling mean nên không được gộp các lần prediction đó thành cùng iid stream. Để tham khảo confidence sequences sắc hơn bound union trên n², xem [R15]. Với miền continuously/adaptively generated không khóa, cần allocation failure probability theo thời điểm candidate xuất hiện và conditional-valid observations, hoặc confidence process riêng. Không dùng Q hữu hạn biết sau cùng để lách selection bias.

### 4.6. Bias bound cho reduced steps và phép hiệu chỉnh bằng paired difference

Giả sử stochastic gradient được chặn norm bởi G_upd trên mọi bước, cùng seed/prefix local path, cùng eta và aggregation weights; validation loss G_val-Lipschitz trên miền model. Khi L2 dùng I_ell bước, L3 dùng I bước:

\[
|L_{\rm val}(w^+_I(S))-L_{\rm val}(w^+_{I_\ell}(S))|
\le G_{\rm val}\eta (I-I_\ell)G_{\rm upd}
=:b_\ell. \tag{B4}
\]

**Chứng minh:** mỗi client thiếu $I-I_\ell$ increments, mỗi increment norm $\le \eta G_{\rm upd}$. Trung bình có trọng số không làm tăng cận; áp dụng Lipschitz. Kết quả đòi cùng prefix và optimizer; không áp dụng nguyên xi cho momentum khác config hoặc “one step scaled by I”.

B4 có thể quá lỏng. Gradient clipping cho known update bound thay đổi optimizer; khi đó lý thuyết unbiased SGD của L9 cần bổ sung clipping bias, không vừa clipping vừa giữ giả thiết unbiased như cũ.

Lựa chọn thực dụng: paired discrepancy D=Y_3−Y_ell trên cùng seeds:

\[
\mu_3(S)=\mathbb E Y_\ell(S)+\mathbb E D(S),\quad
\widehat\mu_3=\overline Y_\ell+\overline D. \tag{B5}
\]

Nếu Y trong [0,L_max], D trong [−L_max,L_max]. Dùng Hoeffding với range L_max cho mean thấp và range 2L_max cho discrepancy, chia delta giữa hai stream và các tập/prefix, cộng hai bán kính. Không cần hai estimator mean-low và mean-difference độc lập với nhau cho union bound; cần từng stream có sampling law hợp lệ.

Các cặp discrepancy phải dùng seed stream mới hoặc lấy prefix theo thứ tự cố định. Chỉ chạy L3 trên những realization L2 có loss thấp rồi lấy trung bình Y3−Y2 sẽ gây selection bias. Adaptive promotion **tập S/fidelity** được phép; cherry-pick replicate theo outcome đã xem thì không. Nếu dùng B4 để giảm range của D, hai fidelity còn phải dùng cùng validation operator/sample để sai khác không chứa thêm validation noise; nếu không, dùng range 2L_max hoặc cộng cận noise đúng.

Variance reduction nhờ common seeds là giả thuyết phải đo, không có bảo đảm D luôn ít nhiễu. Khi fit regression discrepancy/GP, phải phân biệt model prediction uncertainty với confidence interval có chứng minh như B3/B5.

### 4.7. Định lý B2: loại nghiệm an toàn và epsilon-coverage

Giả sử E,T được biết chính xác như P0. Candidate y **chắc chắn trội** x nếu:

\[
u(S_y)\le l(S_x),\quad E_y\le E_x,\quad T_y\le T_x, \tag{B6}
\]

và ít nhất một bất đẳng thức objective là nghiêm ngặt đã được chứng nhận ($u_y<l_x$ hoặc $E_y<E_x$ hoặc $T_y<T_x$). Trên event B1, một true Pareto point trong X_0 không bị loại bởi B6.

**Chứng minh:** $\mu_y \le u_y \le l_x \le \mu_x$; hai objective còn lại exact. Strict condition cho dominance thật. Giữ witness để mọi deletion có thể kiểm toán. Nếu witness sau bị loại, chuỗi dominance kết thúc ở một điểm còn lại vì $X_0$ hữu hạn và strict dominance không có chu trình.

Để có bound coverage đơn giản, giả sử đã có $|\hat{\mu}(x)-\mu(x)| \le \epsilon$ cho mọi $x \in X_0$. Giữ tất cả estimated nondominated points $\hat{A}$. Với mỗi $x \in X_0$, tồn tại $y \in \hat{A}$ sao cho:

\[
\mu(y)\le\mu(x)+2\epsilon,\quad E_y\le E_x,\quad T_y\le T_x. \tag{B7}
\]

**Chứng minh:** nếu $x$ không được giữ thì trên tập hữu hạn có $y$ không trội theo estimates với $\hat{\mu}(y) \le \hat{\mu}(x), E_y \le E_x, T_y \le T_x$. Chèn hai sai số $\epsilon$ cho loss.

B7 là additive coverage theo một chiều loss, không khẳng định chính xác Pareto membership hoặc mọi điểm được giữ đều true-Pareto. Nếu cả ba objective có sai số epsilon_j, bound tương ứng là 2epsilon_j mỗi chiều.

Đặt scale loss cố định $s_L>0$ và $\epsilon_{\rm norm}=\epsilon/s_L$. Trong cùng normalized reference box với lower/upper bounds cố định và diện tích mặt energy–time $A_{\rm ET}$, **true-objective HV** của archive trong B7 có deficit so với $X_0$ không quá $2\epsilon_{\rm norm} A_{\rm ET}$. Ở mỗi tọa độ $E,T$, độ cao phủ theo normalized loss mất tối đa $2\epsilon_{\rm norm}$; tích phân cho cận trên. Nếu tất cả objective đang ở raw units, cận là $2\epsilon$ nhân diện tích $E\text{–}T$ ở raw units. Không bỏ $\text{scale}_L$ khi trộn hai quy ước. Đây là set-relative bound, không phải gap tới toàn miền liên tục hoặc cận cho HV tính từ surrogate predictions.

**Điều kiện dừng có thể kiểm tra trực tiếp từ intervals.** Cho archive được báo cáo $A_{\rm rep}$ không rỗng, là tập con $X_0$. Với $l_x=l(S_x), u_y=u(S_y)$, định nghĩa:

\[
\varepsilon_{\rm cert}=
\max_{x\in X_0}
\min_{\substack{y\in\mathcal A_{\rm rep}\\E_y\le E_x,\ T_y\le T_x}}
[\,u_y-l_x\,]_+,
\qquad \min\varnothing=+\infty. \tag{B10}
\]

Trên event B3, mỗi $x$ có witness $y$ trong archive thỏa $\mu_y-\mu_x \le u_y-l_x \le \epsilon_{\rm cert}$ và không tệ hơn $E,T$. Vì thế $\epsilon_{\rm cert} \le \epsilon_{\rm target}$ là certificate coverage **trong raw loss units**. Nếu không cần nén archive, giữ mọi ứng viên còn unresolved và lấy mẫu đến khi interval đủ hẹp; mọi điểm đã bị loại phải còn witness hợp lệ. Không chỉ kiểm tra interval width của vài elite rồi suy ra coverage toàn $X_0$.

B10 không chứng nhận từng điểm archive là true Pareto; nó chứng nhận khả năng phủ X_0. Muốn cận HV, dùng epsilon_cert/s_L nhân A_ET. Khi budget không đủ, trả về intervals, epsilon_cert hiện tại (có thể vô hạn), unresolved candidates và empirical audited front. Không gọi front là “epsilon-certified” chỉ vì đã chạy hết ngân sách.

**Hai trạng thái báo cáo khác nhau:** “interval-certified” có thể dựa vào valid low-fidelity bound; “reference-evaluated” yêu cầu L3 theo cùng giao thức. Headline empirical audited HV chỉ dùng các điểm đã đánh giá reference độc lập. Nếu lọc hoặc đổi archive sau audit, phải tính lại B10 cho chính archive cuối; không tự động chuyển certificate từ archive trước sang archive sau.

### 4.8. Promotion và stopping có thể triển khai

Tạo một archive resource variants cho mỗi tập S. Đặt phi_S(l) là HV gain của **tất cả** resource variants của S nếu loss=l so với archive tham chiếu. Một heuristic promotion là:

\[
\operatorname{score}(S,\ell)=
\frac{\phi_S(l(S))-\phi_S(u(S))}
{\widehat c(S,\ell\mid\mathcal C)+c_{\rm inference}+\varepsilon_c}. \tag{B8}
\]

Đây là độ nhạy của HV với uncertainty trên tập S chia marginal cost. epsilon_c là hằng dương có cùng đơn vị chi phí. B8 không phải expected information gain chính xác và không được tuyên bố Bayes-optimal. Nếu interval rộng nhưng kém hiệu quả vì fidelity đó không giảm bias floor, bỏ promotion ở mức đó hoặc tăng fidelity.

Dành tỷ lệ query cho exploration và kiểm tra calibration. Với mục tiêu cố định budget, có thể ưu tiên ambiguity gần front; với mục tiêu fixed confidence, tiếp tục đến coverage certificate hoặc báo không đủ budget.

Với $b_\ell < \epsilon$, để $r_{\ell,n}+b_\ell \le \epsilon$ cần cỡ mẫu bậc:

\[
n=O\!\left(\frac{L_{\max}^2}
{(\epsilon-b_\ell)^2}
\log\frac{QF_{\rm levels}n}{\delta}\right). \tag{B9}
\]

Đây là điều kiện đủ từ concentration, không phải lower bound tối ưu. Nếu $b_\ell \ge \epsilon$ thì bound này không chứng nhận bán kính $\le \epsilon$ ở một cỡ mẫu hữu hạn; nếu $b_\ell > \epsilon$ thì ngay cả giới hạn $n \to \infty$ cũng không đủ. Đó là lý do phải promotion, thay vì mãi lấy nhiều low-fidelity samples.

### 4.9. Mã giả B-SHARED-CERT

~~~text
B-SHARED-CERT(snapshot, total_budget):
    Profile target evaluator with all valid caches enabled
    Reserve independent audit/certification budget
    Discovery:
        Generate feasible candidates with A's operators and allocator
        Index candidates by selected set (or rollout prefix in B-H)
        Fit surrogate from paired data; use it only for proposals/ranking
        Promote at measured marginal cost including cache reuse and fitting
        Keep provisional predictions separate from reference records
    Freeze candidate pool X0 and certification protocol
    Certification:
        Freeze fidelity protocols; start fresh ordered replicate streams
        Initialize unmeasured set intervals to [0, L_max]
        Share each set-loss observation across all its resource variants
        Eliminate only by interval dominance B6; record witnesses
        Choose next stream/prefix via B8 plus exploration, never favorable seeds
        Select reporting archive and compute epsilon_cert by B10 over all X0
        Stop when $\epsilon_{\rm cert} \le \text{target}$ or when remaining budget is exhausted
        Audit the reporting archive at common reference fidelity
        Recompute B10 if auditing changes the final reporting archive
    Return:
        empirical independently evaluated nondominated archive
        intervals, certified eliminations, unresolved set, actual total costs
        achieved coverage bound only if its premises were verified
~~~

Nếu mục đích so sánh là khả năng khám phá miền, X_0 của từng thuật toán có thể khác nhưng certificate chỉ relative to từng pool. Để so front discovery công bằng, audit hợp các candidate rồi dùng cùng reference protocol; không biến union này thành chứng minh tối ưu toàn miền.

### 4.10. Độ phức tạp, tính mới và failure gates

Gọi Q tập, V resource variants, F mức, n_{S,ell} mẫu; chi phí chính là tổng measured c theo B1. So dominance naive O(V²J) mỗi full refresh, incremental có thể giảm tùy data structure. CI update O(1) mỗi stream observation; propagation tới variants O(V_S). Predictor fitting phải ghi riêng (GP exact thường cubic theo số training observations; model khác có chi phí khác).

Contribution candidates:

1. Quotient-space evaluation theo tập/prefix, kết hợp resource allocation giải tới tolerance công bố; exact physical Pareto envelope chỉ là đối tượng lý thuyết khi đã lấy đủ miền liên tục.
2. Promotion dựa trên marginal cache cost và tác động của một query tới nhiều Pareto candidates.
3. Finite-pool certificate chịu fidelity bias, optional stopping và common-random-number dependence đúng cách.

Các confidence bounds trên là công cụ chuẩn được suy ra cho cấu trúc này, không nên mô tả riêng Hoeffding/union bound là định lý mới mang tính đột phá. Giá trị bài báo phải đến từ cấu trúc chia sẻ thông tin và hiệu quả thực nghiệm so với baseline mạnh.

**Gate B:** nếu chi phí cache/reference thấp, fidelity correlation kém hoặc certification/audit đắt hơn phần tiết kiệm thì dừng B0, báo kết quả âm; chuyển B-H vì chi phí branching thật, không tắt cache để làm baseline chậm.

Đối chứng: A single-fidelity với cache giống hệt; fixed fidelity schedule; random promotion; uncertainty-only; MF-HVKG/MF-OSEMO thích nghi cho mixed search; proposed không shared cache cost; proposed không confidence elimination. Báo verified HV/time, certification width, false deletion, rank reversal, cost breakdown và cold/warm cache riêng.

---

## 5. Direction C: thăm dò có chi phí và quyết định hai giai đoạn

### 5.1. Trạng thái, thông tin và biến quyết định

Hidden state $\theta_k$ gồm learning statistics, tình trạng kênh/chất lượng báo cáo chưa quan sát. Controller có H_k: model, report cũ, timestamps, pin telemetry, thông tin link được phép dùng. Việc telemetry/pilot phát sinh chi phí phải được tính; không gọi perfect CSI là miễn phí.

Giai đoạn một:

\[
a_k^P=(z_k,b_k^P,f_k^P,n_k^P)=\pi^P(H_k). \tag{C1}
\]

$z_{mu}$ là gán probe và $z_m=\sum_u z_{mu} \le 1$. Phiên bản probe learning dùng $n_m^P$ là số minibatch, với $n_m^P$ nguyên và $z_m \le n_m^P \le n_{\max}^P z_m$. Như vậy probe learning có ít nhất một minibatch; khi không probe thì $n_m^P=0$. Nếu cần CSI-only probe, định nghĩa loại action riêng với workload/payload tương ứng, không cho $n=0$ nhưng vẫn nhận gradient. Phiên bản đầu có thể cố định $n_m^P$ cho client được probe.

Observation:

\[
Y_m=(\widehat F_m(w_k;n_m^P),R\widehat g_m(w_k;n_m^P),
\widehat h_{m,a_m^P},\widehat Q_m,\tau_m^{report}),\quad m\in P. \tag{C2}
\]

Các dấu mũ trong C2 đã bao hàm sampling/measurement/quantization noise; likelihood phải định nghĩa chúng một lần, không cộng thêm một noise vector không rõ đơn vị. a_m^P là UAV được z chọn và tau_m^report là timestamp. R là projection seed chung. C_m^P(n), L_m^P(n), thời gian download checkpoint và quantization bits phải profile; gradient sketch không tự mang bảo đảm differential privacy.

Probe nhận được ít nhất một gradient estimate ở đúng model version mới có learning report. Trong P1, một field hoặc toàn report có thể không đến kịp; observation space phải gồm ký hiệu thiếu/perp và success mask. Timeout vẫn bị tính phí, posterior cập nhật theo cả sự kiện không nhận report. Không được mặc định probe luôn thành công trong khi training upload có outage.

Sau probe:

\[
Q_i^+=Q_i-E_i^{opt,P}-E_i^P,\quad
\tau^+=\tau+t_{\rm opt,P}+T^P,\quad
\beta^+(\theta)\propto p(Y_P\mid\theta,a^P,\mathcal H_k)\beta^-(\theta). \tag{C3}
\]

C3 trừ cả năng lượng chờ/tính optimizer trước probe. Bayes update viết tắt ở C3 chỉ áp dụng khi theta tĩnh trong khoảng này và likelihood đã xét timestamps, missing reports. Nếu channel/state thay đổi, cần prediction rồi correction, hoặc state-space filter theo từng thời điểm nhận report. Với observation quy về thời điểm cuối pha, Delta=t_opt,P+T^P và transition kernel K_Delta, đặt:

\[
\bar\beta^+(\theta')=\int K_{\Delta}(\theta'\mid\theta,a^P,\mathcal H_k)
\,\beta^-(\theta)\,d\theta,\qquad
\beta^+(\theta')\propto
p(Y_P\mid\theta',a^P,\mathcal H_k)\bar\beta^+(\theta'). \tag{C3a}
\]

Likelihood cuối pha phải tích phân quá trình trung gian nếu reports được đo ở nhiều timestamp. Nếu Delta là stopping time phụ thuộc trạng thái/kết quả đo, chính duration cũng là observation: cần joint transition–observation kernel có xét stopping rule; không thay Delta quan sát được vào một unconditional fixed-time kernel rồi coi posterior đó là exact. Một lần Bayes update lên prior đầu vòng mà bỏ transition không đủ cho CSI cũ. Trong t_opt,T sau probe, tiếp tục trừ E_i^{opt,T} và dự báo channel tới thời điểm training; không “đóng băng thời gian” khi lập lịch lại.

Q_i trong các ràng buộc là trạng thái pin biết chính xác hoặc **lower bound đã bảo đảm**. Nếu Q_hat có measurement noise mà không có bound, chỉ thay Q_i bằng mean prediction không bảo đảm hard battery feasibility; phải thêm robust/chance model và confidence budget. E_i đã tiêu thụ cũng cần upper bound nếu chưa đo chính xác.

Bayes update chỉ đúng với likelihood/prior xác định. Ensemble prediction có uncertainty calibration thực nghiệm không mặc nhiên là Bayesian posterior. State phải lưu model-version, channel timestamp và mask đã đo; không chỉ một vector “age”.

Giai đoạn hai:

\[
a_k^T=(s_k,b_k^T,f_k^T)=\pi^T(H_k,a_k^P,Y_P). \tag{C4}
\]

Cho phép train client chưa probe; không áp $s_m \le z_m$ nếu không có lý do giao thức. Client đã giữ $w_k$ từ probe không download lại. Client được probe nhưng không train vẫn tiêu tốn năng lượng và thời gian.

### 5.2. Physical constraints hai giai đoạn

Probe tuân S9–S11 tương ứng, nhưng cho phép P rỗng, và không áp lower bound training cardinality lên P. Nếu n_m^P biến thiên, C_m^P được xác định từ n_m^P; không để workload tự do không liên quan chất lượng đo.

\[
T_k=t_{\rm opt,P}+T^P+t_{\rm opt,T}+T^T,\quad
E_i^k=E_i^P+E_i^{T\mid P}+E_i^{opt}, \tag{C5}
\]

trong đó $E_i^{\rm opt}=E_i^{\rm opt,P}+E_i^{\rm opt,T}$. Bốn khoảng opt,P; probe; opt,T; training không giao nhau. Mỗi $E_i^{\rm opt,r}$ gồm baseline của client, hover+electronics baseline của UAV trong $t_{\rm opt,r}$ và computation tăng thêm nếu nút $i$ thực thi optimizer. $E_i^P$ và $E_i^{T|P}$ chỉ tính baseline/hover trong service phase của chính mình, cùng các chi phí tăng thêm. Không dùng lại $P_{\rm idle} T_k$ trong từng phase.

$E_i^P$ gồm model download phục vụ probe, pilot, compute, upload/report, chờ và xử lý cần thiết. $E_i^{T|P}$ chỉ tính download bổ sung còn thiếu. Nếu $\mathcal{P}$ rỗng thì $T^P=E_i^P=0$, nhưng thời gian/chi phí đã dùng để quyết định “không probe” vẫn phải ghi.

\[
T_k\le T_{\max},\qquad
E_i^P+E_i^{T\mid P}+E_i^{opt}\le Q_i-Q_i^{res}. \tag{C6}
\]

Nếu channel biến đổi theo thời gian, thời điểm training sau probe dùng geometry/channel posterior cập nhật theo tau^+, không tái dùng CSI lúc trước như hoàn toàn chính xác.

Trong thiết kế an toàn, mỗi probe plan phải còn ít nhất một recourse feasible hoặc safe termination cho mọi observation trong miền bảo đảm. “Trung bình có lịch train” không đủ bảo đảm pin mỗi realization. Với channel unbounded fading, dùng hard timeout và worst-case cost của protocol để bảo vệ pin; chất lượng update vẫn stochastic.

### 5.3. Mô hình C0: Pareto của các chính sách hai giai đoạn

Ở một vòng:

\[
\min_{\pi^P,\pi^T}
\left(
\mathbb E[L_{\rm val}(w_{k+1})\mid H_k],
\mathbb E[E_k\mid H_k],
\mathbb E[T_k\mid H_k]
\right), \tag{C7}
\]

subject C1–C6 và L2–L3. Ở nhiều vòng dùng L4 cùng belief transition. Đây là constrained partially observed stochastic control problem, có trạng thái liên tục và mixed actions; exact policy optimization nói chung không khả thi ở quy mô lớn.

Dùng preference grid lambda cố định để tìm các operating points:

\[
C_\lambda(a,\theta)=\lambda_L\widetilde L(a,\theta)
+\lambda_E\widetilde E(a,\theta)+\lambda_T\widetilde T(a,\theta). \tag{C8}
\]

Dấu tilde là chia scale cố định có đơn vị tương ứng. Weighted sums có thể bỏ lỡ non-supported Pareto points; muốn khảo sát front đầy đủ hơn dùng epsilon-constraints (min loss với caps E,T) và audit từng policy. Một lần lấy lambda không đại diện “đã tối ưu toàn front”.

### 5.4. Định lý C1: giá trị thông tin và chi phí mất khả năng phục vụ

Trước hết giữ cố định action domain A0 không rỗng và cost C0 khả tích. Giả sử các minimum tồn tại và có measurable selectors, chẳng hạn action library hữu hạn; với miền liên tục cần compactness/continuity tương ứng hoặc thay min bằng inf với epsilon-optimal rules. Mọi so sánh dùng cùng conditional prior theo H. Khi kênh biến đổi trong lúc probe, có thể xem theta là hidden exogenous path trong cả khoảng so sánh; timing/resource changes đi vào C^P và observation law, không đổi prior giữa hai vế mà vẫn gọi là cùng EVSI.


\[
V_0=\min_{a\in A_0}\mathbb E[C_0(a,\theta)\mid H],\quad
V_{\rm info}(P)=\mathbb E_Y\min_{a\in A_0}
\mathbb E[C_0(a,\theta)\mid H,Y],\quad
\operatorname{EVSI}(P)=V_0-V_{\rm info}(P)\ge0. \tag{C9}
\]

**Chứng minh:** sau khi quan sát Y, controller luôn có thể bỏ qua Y và chọn prior-optimal action a0. Conditional optimum không lớn hơn conditional cost của a0; lấy kỳ vọng và dùng tower property.

Với actual recourse domain A_P(Y) và cost C^P sau khi cập nhật pin, time, DL cache:

\[
V_P=c_P+
\mathbb E_Y\min_{a\in A_P(Y)}
\mathbb E[C^P(a,\theta)\mid H,Y], \tag{C10}
\]

với c_P là expected normalized cost riêng của probe/decision stage đã tách đúng ledger. Nếu chi phí probe phụ thuộc Y, c_P ở đây là expectation tương ứng, còn pathwise constraint vẫn dùng realized cost.

Đặt:

\[
\Omega(P)=
\mathbb E_Y\min_{a\in A_P(Y)}\mathbb E[C^P(a,\theta)\mid H,Y]
-
\mathbb E_Y\min_{a\in A_0}\mathbb E[C_0(a,\theta)\mid H,Y].
\]

Khi đó đồng nhất thức:

\[
\boxed{V_0-V_P=\operatorname{EVSI}(P)-c_P-\Omega(P).} \tag{C11}
\]

Nếu $\mathcal{C}^P=\mathcal{C}_0$ và $\mathcal{A}_P(Y) \subseteq \mathcal{A}_0$ thì $\Omega \ge 0$: đây là phần mất do probe tiêu tốn pin/deadline. Nếu probe làm cache download hữu ích hoặc thay đổi physical cost, $\Omega$ có thể âm; phải dùng C10 thật, không gọi mọi $\Omega$ là “penalty dương”.

**Ví dụ số có thể kiểm tra:** có hai trạng thái equally likely. Hai hành động $a_1, a_2$ có cost $(0,1)$ và $(1,0)$; action an toàn $a_0$ cost $(0.6,0.6)$. Prior optimum $V_0=0.5$. Perfect observation cho $V_{\rm info}=0$ và $\text{EVSI}=0.5$. Probe cost $c_P=0.1$:

- Nếu cả $a_1, a_2$ còn feasible, $V_P=0.1$, $\text{gain}=0.4$.
- Nếu probe làm cả $a_1, a_2$ không còn đủ năng lượng, chỉ $a_0$ feasible, $V_P=0.7$, $\text{gain}=-0.2$ và $\Omega=0.6$.
Cùng lượng thông tin nhưng quyết định probe có thể đảo dấu. Đây là cơ chế chính cần đo trong UAV-FL.

### 5.5. Định lý C2: lợi ích recourse và quy tắc bỏ probe

Với cùng probe P, cùng posterior và cùng recourse costs, cho phép a phụ thuộc Y không tệ hơn lớp chính sách buộc một hành động cố định **nếu hành động cố định đó khả thi cho mọi Y**. Chứng minh vì lớp adaptive policies chứa lớp fixed policies. Nếu thuật toán heuristic tìm kém, performance thực nghiệm vẫn có thể kém; định lý nói về optima trong lớp.

Đặt value of perfect information trên miền cố định:

\[
\operatorname{EVPI}=
\min_a\mathbb EC_0(a,\theta)-\mathbb E_\theta\min_a C_0(a,\theta).
\]

Ta có $0 \le \text{EVSI}(P) \le \text{EVPI}$. Vế trên do thông tin hoàn hảo cho phép mô phỏng mọi rule dựa trên $Y$, rồi chọn hành động tốt nhất theo $\theta$. Nếu $\Omega \ge 0$ và $c_P \ge \text{EVPI}$ thì probe không có net gain dương. Khi không biết EVPI chính xác, một upper bound đủ dùng để loại probe quá đắt.

Trường hợp no decision change: cùng một a_star tối ưu cho mọi posterior realization, chi phí/miền không thay đổi, thì EVSI=0. Uncertainty cao của một client không tự làm probe đáng giá.

### 5.6. Không gán adaptive-submodular guarantee cho VOI tổng quát

Giả sử hidden state gồm hai independent fair bits theta1,theta2. Hành động đoán parity theta1 XOR theta2; cost=1 nếu đoán sai, 0 nếu đúng. Không quan sát có Bayes risk 1/2. Quan sát một bit vẫn risk 1/2; quan sát cả hai risk 0. Vì vậy:

- EVSI({1})=EVSI({2})=0;
- EVSI({1,2})=1/2;
- marginal của probe 2 tăng từ 0 lên 1/2 khi đã có probe 1.

Diminishing returns bị vi phạm. Ví dụ này cho thấy synergistic information có thể làm greedy probe bỏ lỡ toàn bộ giá trị. Adaptive-submodularity là lý thuyết có điều kiện [R10], không phải tính chất mặc định của FL probing.

Trong thực nghiệm nên so greedy từng client với lookahead cặp probe trên bài toán nhỏ, để phát hiện complementarity thay vì chỉ so uncertainty ranking.

### 5.7. Cận chọn policy hữu hạn bằng scenario evaluation

Để có bảo đảm có thể kiểm chứng, cố định một thư viện hữu hạn Pcal gồm N_pi **hai-stage policies hợp lệ**. Mỗi policy xác định probe plan và mapping từ observation sang training action. Mapping có thể dùng quantized reports/decision tree; mọi scenario có cùng observation bin phải dùng cùng action. Không được cho mỗi scenario nhìn hidden theta để chọn action riêng.

Đánh giá mỗi policy trên $n$ fresh i.i.d. scenarios đầy đủ $(\theta, Y, \text{execution RNG})$, với $n$ được chọn trước khi xem certification outcomes và normalized total cost $Z_\pi \in [0, C_{\max}]$. $C_{\max}$ phải là known bound, ví dụ từ bounded loss, hard $T_{\max}$ và các energy budgets hữu hạn; không dùng maximum quan sát để thay bound. Policy được xây trên design data khác, simulator đúng, và mọi policy gồm cả fallback đã tuân physical constraints.

\[
r_n=C_{\max}\sqrt{\frac{\ln(2N_\pi/\delta)}{2n}},
\quad
\Pr\left(\max_{\pi\in\mathcal P}|\widehat V_\pi-V_\pi|\le r_n\right)
\ge1-\delta. \tag{C12}
\]

Hoeffding và union bound chứng minh trực tiếp. Dùng common scenarios giữa các policies vẫn hợp lệ; independence yêu cầu giữa scenario replicates cho từng policy. C12 là **fixed-n bound**: nếu nhìn kết quả rồi tăng $n$/dừng khi có lợi, phải dùng time-uniform radius như B3 với $Q=N_\pi, F_{\rm levels}=1, L_{\max}=C_{\max}$, hoặc phân bổ failure probability theo các lần nhìn. Không tái dùng nguyên C12 cho optional stopping.

Chọn $\hat{\pi}=\arg\min \hat{V}$:

\[
V_{\widehat\pi}\le\min_{\pi\in\mathcal P}V_\pi+2r_n. \tag{C13}
\]

**Chứng minh:** $V(\hat{\pi}) \le \hat{V}(\hat{\pi})+r \le \hat{V}(\pi^*) + r \le V(\pi^*) + 2r$.

Nếu predictor/simulator có uniform expected-cost error epsilon_model trên thư viện, so với thế giới thật bound thành 2r_n+2epsilon_model. Nếu không có uniform bound này, chỉ công bố guarantee trong simulator; held-out calibration không tự chứng minh model error luôn nhỏ.

Đưa no-probe policy vào thư viện. Chỉ khuyến nghị probe khi:

\[
\widehat V_{\rm no\ probe}-\widehat V_{\rm probe}>2r_n
\quad
\text{(hoặc }2r_n+2\epsilon_{\rm model}\text{ khi có model bound)}. \tag{C14}
\]

Trên event C12, rule này không chấp nhận một probe có true cost cao hơn no-probe comparator trong cùng thư viện. Nó có thể bỏ lỡ probe tốt khi sample nhỏ; đó là trade-off thận trọng.

Phân biệt hai output: C13 áp dụng cho empirical minimizer $\hat{\pi}$. Policy cuối dùng C14 có thể chuyển từ $\hat{\pi}$ sang no-probe; khi đó bound đơn giản là $V(\pi_{\rm final}) \le \min_\pi V(\pi)+4r_n$ (cộng $4\epsilon_{\rm model}$ nếu dùng threshold có model bound), không phải tự động $2r_n$. Chứng minh: nếu chấp nhận $\hat{\pi}$ dùng C13; nếu quay về no-probe, threshold cho $\hat{V}(\text{no-probe}) \le \hat{V}(\hat{\pi})+2r_n$, rồi cộng hai sai số $r_n$. Ví dụ $r_n=0.1$, true costs $(\text{no-probe}, \text{probe})=(0.4,0)$, estimates=$(0.3,0.1)$: error mỗi estimate đúng 0.1, rule strict C14 quay về no-probe và regret $=0.4=4r_n$, vượt $2r_n$. Rule này vẫn bảo đảm không kém no-probe trên confidence event, nhưng bảo đảm gần-best-in-library yếu hơn.

“Không kém no-probe” ở đây so với no-probe policy trong **cùng controller**, đã trả chi phí chọn policy. Nếu baseline no-probe bỏ hẳn expensive policy-selection search, phải cộng chênh lệch overhead rồi so lại; C14 không tự bảo đảm thắng baseline đó.

C13 không phải regret bound so với mọi policy liên tục/POMDP tối ưu. Observation discretization, candidate library truncation và model mismatch là ba error sources riêng. Nếu quyết định lặp nhiều vòng, phân bổ $\delta_k$ sao cho $\sum_k \delta_k \le \delta_{\rm mission}$; per-round guarantee không tự là guarantee toàn episode.

**Policy được thực thi phải đúng policy đã chứng nhận.** Mapping pi^T có thể là một optimizer chạy lại theo Y, nhưng solver, hyperparameters, ngân sách runtime, tie-break, RNG law và safety fallback phải được khóa trước certification và được mô phỏng trong Z_pi. Không đánh giá một decision tree rồi sau probe tự thay bằng một vòng search khác và giữ nguyên C13–C14. Nếu đổi mapping, chỉ còn empirical/heuristic claim cho policy mới cho tới khi được đánh giá lại.

### 5.8. Thuật toán C-RECOURSE và cách dùng A/B bên trong

~~~text
Offline:
    Train predictor/observation model on authorized simulation or past data
    Validate model and uncertainty on held-out geometries/checkpoints
    Build a safe action generator and candidate probe library

For each physical round k:
    Read allowed history, battery and clock; update model-drift features
    Generate probe plans: empty, targeted singletons, small pairs, random plans
    For each plan:
        Check worst-case probe costs and safe recourse/termination
        Simulate observation scenarios using the declared belief model
        Build nonanticipative recourse rules using A's resource allocator
        Use B to allocate offline/scenario evaluation effort if useful
    Freeze each full recourse mapping, solver/RNG law, budget and safety fallback
    Evaluate fixed policy candidates on fresh common scenarios with fixed n
    Select a policy using C14 or report a heuristic if no valid certificate
    Charge optimizer-P energy/time, execute its probe, and record missing reports
    Update belief, remaining time, battery, DL cache and channel prediction
    Run the selected policy's fixed recourse solver on the actual observations
    Charge optimizer-T energy/time and propagate the state to training start
    Apply the same safety check/fallback that was included in policy evaluation
    Execute exactly one training schedule
    Aggregate successful updates; advance clock; update accessible history
~~~

Online không được gọi local-update cache do offline oracle tạo bằng toàn bộ dữ liệu hiện tại. Runtime có thể dùng predictor pretrained, simulator với authorized model, report đã trả phí và một execution thực. Nếu thử train nhiều candidate trên client thật, mỗi thử là physical action; đưa vào C5–C6.

t_opt đo trên deployment hardware, đặt hard computation budget và fallback đã kiểm tra. Waiting trong search cũng làm UAV hover, nên inference nặng có thể xóa lợi ích của probe/learning scheduler.

### 5.9. Horizon, độ phức tạp và novelty C

C-K kế thừa L4 với belief-state transition. Bellman representation đòi theta và X_obs là trạng thái Markov đủ, observation/transition kernels xác định, và class policies có measurable admissible actions; một sketch/history summary tùy ý không tự thỏa điều kiện này. Có thể dùng full history như thông tin đầu vào nếu chưa có sufficient-state model, nhưng không gọi đó là finite-state reduction đã chứng minh. Dưới các điều kiện trên, Bellman scalarized cho finite horizon là:

\[
V_k(X_{\rm obs},\beta)=
\min_{a^P}
\mathbb E_Y\left[
c_P+
\min_{a^T\in\mathcal A_P(Y)}
\mathbb E\{c_T+V_{k+1}(X_{\rm obs}',\beta')\mid Y\}
\right], \tag{C15}
\]

terminal $V_K=\lambda_L \mathbb{E}_\beta[L_{\rm val}(w_K,\theta)]/\text{scale}_L$; nếu validation function là hàm đã biết của $w_K$ thì expectation này rút thành $L_{\rm val}(w_K)$. $c_P, c_T$ chỉ chứa energy/time theo preference, gồm chi phí optimizer theo policy đã khai báo. Không cộng terminal loss tại mỗi vòng rồi gọi đó là L4. Trong C15, $c_P$ đặt trong outer expectation phải là realized/conditional stage cost nhất quán với $Y$; khác với ký hiệu expected $c_P$ viết tắt ở C10. Các chi phí ngẫu nhiên, missing report và thời gian optimizer phải nằm trong expectation/transition phù hợp.

Exact dynamic programming không khả thi ở mạng lớn; dùng limited-horizon scenario library và receding horizon, báo rõ approximation. Không khẳng định global optimality hoặc O(1/V) Lyapunov trade-off vì không xây queue model và không chứng minh drift bound.

Với N_P probe plans, N_Y observation scenarios, N_A recourse actions, chi phí naive O(N_P N_Y N_A C_eval); posterior sampling và inner search làm tăng chi phí. H-depth tree có thể tăng theo lũy thừa N_Y^H. Giới hạn N_P, dùng shortlisted pairs, reuse resource envelopes và early confidence screening; đo tất cả overhead.

Đóng góp khả dĩ:

1. Budget-eroding VOI: thông tin tốt hơn nhưng resource domain hẹp hơn, có C11 làm cơ sở giải thích.
2. Probe quality và lựa chọn training ghép qua độ bất định loss/set utility và thời điểm kênh, không chỉ xếp hạng age.
3. Certifiable selection trong policy library và điều kiện “không probe” kiểm tra được, cộng thử nghiệm episode hạch toán thật.

C9 và C12–C13 là nguyên lý/thủ thuật chuẩn, không gọi riêng chúng là novelty. Tính mới cần nằm ở policy/resource coupling, phương pháp xấp xỉ và kết quả UAV-FL so với công trình gần nhất.

---

## 6. Đánh giá tính mới và đối chiếu nghiên cứu

### 6.1. Những tuyên bố không nên dùng

Không nên viết “lần đầu dùng đa mục tiêu cho UAV-FL”, “lần đầu dùng diversity/client set”, “lần đầu dùng VOI cho client selection”, “lần đầu multi-fidelity Pareto optimization”, hoặc “thuật toán hội tụ toàn cục” chỉ vì có NSGA-II/MOEA/D.

Tra cứu ngày 28/10/2026 đã có công trình liên quan trực tiếp cả ba trục. Phạm vi đọc khác nhau được ghi bên dưới. Không tìm thấy một tổ hợp đúng y hệt trong lần tra cứu này **không phải** chứng minh không tồn tại.

### 6.2. Bảng đối chiếu gần nhất

| Công trình và phạm vi đã kiểm tra | Nội dung đã có | Hệ quả đối với đề xuất |
|---|---|---|
| FSTPO, Yang và cộng sự, DOI 10.1109/JIOT.2026.3727888; đọc PDF local, mục II và đầu III | Utility dài hạn, scheduling/resource allocation, gradient-divergence surrogate, FL phân cấp và hybrid actor–critic | Thay solver bằng MOEA chưa đủ mới. Có thể phát triển actual set-loss, hạch toán hover/time và acquisition of information; phải so cùng scope |
| DivFL, Balakrishnan và cộng sự, ICLR 2022; repository tác giả và bản workshop | Chọn tập client đại diện gradient bằng facility-location/submodular formulation | “Set-aware/diversity” đã có. A cần phân biệt matching heuristic với actual loss và resource-front structure |
| Oort, Lai và cộng sự, OSDI 2021; trang paper chính thức | Kết hợp statistical utility và tốc độ client để cải thiện time-to-accuracy | Không dùng channel greedy như baseline mạnh duy nhất |
| MF-OSEMO, Belakaria và cộng sự, AAAI 2020; trang paper chính thức | Chọn candidate và fidelity theo thông tin về front trên chi phí | “Front information gain / cost” không phải novelty của B; baseline cần thích nghi cấu trúc tập/cache |
| Hypervolume Knowledge Gradient, Daulton và cộng sự, ICML 2023; trang paper/abstract | Lookahead multiobjective BO cho partial/decoupled/multi-fidelity information | B8 chỉ là heuristic, cần đối chứng HVKG hoặc nêu lý do quy mô không chạy được |
| Kone, Kaufmann và Richert, AISTATS 2024; abstract và phần mở đầu paper | Fixed-budget Pareto set identification, elimination và error probability analysis | Confidence-based Pareto elimination đã có; đóng góp B cần cấu trúc shared query và fidelity bias |
| Yahya, Maghsudi và Stanczak, arXiv 2308.16889; abstract tác giả | UAV-FL coverage/delay với multiobjective bandit, thiếu thông tin kênh và cost-aware best-arm identification | C phải phân biệt charged statistical probing/recourse với học chất lượng action/network placement |
| Zou và cộng sự, IEEE TC 2024; xác minh metadata trên trang tác giả, chưa đọc full text | Đã có công trình mang tên Value of Information cho client selection | Không tuyên bố “VOI cho FL lần đầu”; cần lấy full text trước khi chốt novelty C |
| Matsumoto, Ishikura và Karasuyama, arXiv 2610.10174, 07/10/2026; abstract preprint | Constrained multi-fidelity multiobjective BO, acquisition thông tin về feasible high-fidelity front | Đối thủ gần cho B về formulation tổng quát; cần đọc full text, không coi preprint là nghiên cứu đã peer-review |
| Mikkola và cộng sự, AISTATS 2023; trang paper/abstract | Multi-fidelity BO khi nguồn thông tin độ tin cậy thấp | Rank reversal/unreliable low fidelity không phải vấn đề mới phát hiện ở dự án này |

Bảng này không đánh dấu “không có” cho những tính năng chưa kiểm tra full text. Những cột khác biệt là **định hướng đóng góp cần đối chiếu**, không phải cáo buộc các paper trước thiếu mọi thành phần đó.

### 6.3. Khác biệt quan trọng với paper FSTPO nền

Trong PDF FSTPO, phương trình (6) cộng utility theo từng client với penalty gradient divergence; các phương trình (14)–(15) dùng cumulative scalar utility. Bản đề xuất dùng actual post-aggregation validation loss để đánh giá learning quality, nên complementarity được đo ở outcome của tập thay vì giả định tổng score cá thể là outcome.

FSTPO còn có application task offloading độc lập với local FL training. Draft JNCA đã giới hạn lại sang scheduling FL; báo cáo giữ giới hạn đó. Nếu benchmark lại FSTPO trên simulator mới, phải gọi là **FSTPO-inspired adapted baseline**, trừ khi tái tạo đầy đủ workload và giao thức gốc.

FSTPO mục II-D loại hover khỏi objective với lý do không ảnh hưởng so sánh. Trong mô hình của báo cáo, round duration thay đổi theo lịch nên $E_{\rm hover}=P_{\rm hover} T$ thay đổi. Đây là khác biệt về system boundary/time accounting; không chỉ sửa một hằng số. Nếu hệ thống thực giữ mọi UAV trên không đến cùng fixed mission time, phần hover toàn mission có thể lại là hằng số; lúc đó không được tuyên bố giảm hover chỉ vì FL kết thúc một round sớm hơn.

### 6.4. Ba gói đóng góp có thể bảo vệ

**A — Structured set-dependent scheduling.**

- Định nghĩa outcome theo tập và cấu trúc resource equivalence classes.
- Allocator convex có chứng minh và front reduction A7.
- Guided proposals với thông tin thiếu/cũ; actual-loss validation và multi-round evaluation.

Rủi ro: nhiều thành phần là kỹ thuật chuẩn; contribution độc lập có thể còn mỏng nếu chỉ gain nhỏ. Nên xem là nền của bài B/C hoặc một bài application có hệ thống kiểm chứng mạnh.

**B — Cache-aware multi-fidelity Pareto verification.**

- Query shared theo tập/prefix và dynamic marginal evaluation cost.
- Bias-aware intervals, no false certified elimination trên finite pool.
- Xác định regime tiết kiệm thật sau cache, audit và fitting.

Rủi ro: full reference một vòng đã quá rẻ; certificate quá bảo thủ; deep model validation cost không đáng kể. Chỉ theo B nếu profiling và gate cho phép.

**C — Information acquisition with resource-constrained recourse.**

- Probe quality/cost, stale learning/channel information và remaining resource domain cùng quyết định.
- Dùng C11 để phân tích thời điểm information gain không bù nổi feasibility loss.
- Policy-library guarantee và episode evaluation qua nhiều chế độ probe cost/channel drift.

Rủi ro: posterior misspecification, CSI hết hiệu lực khi probe xong, phí download lớn, nested optimization không đáp ứng deadline. Đây cũng là những regime thất bại cần công bố.

### 6.5. Đề xuất lựa chọn cho một bài báo

Nếu chỉ viết một bài: giữ A làm nền; chọn **B hoặc C làm đóng góp trung tâm**, phần còn lại là extension/ablation. Không nên đồng thời cam kết giải tối ưu global trajectory, full-horizon POMDP, calibrated multi-fidelity, privacy và nonstationary continual learning trong một bài đầu.

Hai tên hướng mang tính mô tả, chưa phải tuyên bố novelty:

- “Cache-Aware Multi-Fidelity Pareto Scheduling for UAV-Assisted Federated Learning.”
- “Costly Information Acquisition and Resource-Constrained Recourse for UAV-Assisted Federated Learning.”

B phù hợp khi nhóm có compute/simulator tốt và muốn bài optimization. C phù hợp hơn khi có thiết bị hoặc trace thực để profile probe, communication và time budget.

---

## 7. Kế hoạch thực nghiệm và tiêu chí kiểm chứng

### 7.1. Các tầng kiểm tra

| Tầng | Cấu hình | Mục đích |
|---|---|---|
| T0 | Quadratic/smooth logistic model, 3–6 client, 1–2 UAV | Kiểm tra L6–L10, counterexamples, resource convexity, finite enumeration |
| T1 | Fashion-MNIST/small CNN, 6–20 client | Đối chiếu v1 và pipeline mới; checkpoint đầu/giữa/cuối |
| T2 | CIFAR-10 hoặc dữ liệu phù hợp ứng dụng, 50–100 client, 3–5 UAV | Scale, non-IID địa lý, expensive evaluation |
| T3 | Hardware/trace profile | DVFS, compute cycles, payload, actual goodput, hover/online inference cost |
| T4 | P1: fading, stale CSI, dropout, outages | Kiểm tra tính bền vững và falsification các giả thiết P0 |

Các quy mô trên là **đề xuất**, không phải cấu hình đã chạy hay thông số phần cứng đã đo.

### 7.2. Thiết kế dữ liệu và ngân sách

- Tổng training samples giữ cố định khi tăng số client; nếu tăng tổng data thì báo riêng.
- Dùng IID và Dirichlet non-IID; thêm geographic class skew và rare-class clients có chủ đích.
- Noise client là label corruption có mức khai báo, không mặc định “gradient lạ = noise”.
- Đặt cùng một rare client tại link tốt/xấu để tách hiệu ứng dữ liệu khỏi vị trí.
- Target weights và validation/test class distribution chốt trước. Nếu nhiệm vụ coi rare classes quan trọng, thiết kế target distribution/risk objective phù hợp, không tăng trọng số sau khi nhìn kết quả.
- Warm-up model dùng cùng protocol giữa phương pháp. Nghiên cứu từ random checkpoint và từ checkpoint đã học là hai setting riêng.
- Với episode, chạy đến K cố định hoặc resource horizon cố định; nêu rõ failure/termination. 20 optimizer runs không phải 20 vòng của cùng một FL trajectory.

### 7.3. Baselines và ablations

**A:** random feasible search, channel-efficient selection, Oort-style utility, DivFL-style representative selection; generic NSGA-II/MOEA/D; proposed guided variants. Dùng cùng allocator nếu cô lập client selection; cùng selection nếu cô lập resource optimization.

**B:** full reference với mọi cache hợp lệ; fixed fidelity ladder; random promotion; uncertainty-only; MF-HVKG/MF-OSEMO adaptation; shared-query on/off; bias bound on/off chỉ như ablation thực nghiệm, không gọi bản tắt bound là certified.

**C:** no probe, periodic probe, random probe, age-only, uncertainty-only, cost-aware VOI, probe không recourse, adaptive recourse, full-information oracle. Oracle chỉ là upper-information diagnostic, không là fair deployable competitor.

Tất cả phương pháp online nhận cùng authorized information. Nếu baseline cần gradient mới thì phải trả phí thu gradient; nếu proposed có pretrained predictor thì ghi offline data/compute budget và kiểm tra transfer.

### 7.4. Metrics

Snapshot:

- Audited HV với cùng scale/reference box; out-of-box points báo riêng.
- IGD chỉ khi có reference front đáng tin; pooled front là empirical reference.
- Feasible rate, constraints residuals, deadline/battery margins.
- Số tập client độc nhất, resource variants per set, cache hit/miss, solver time.

B:

- HV theo wall-time/GPU-s; cold-cache và warm-cache.
- Empirical coverage của intervals; false certified elimination; unresolved fraction.
- Fidelity bias/rank reversals theo checkpoint, set cardinality, data skew.
- Time cho train, validation, fitting, acquisition, certification và audit.
- Certificate relative to pool; không dùng tên “global Pareto error” cho subset benchmark.

Episode:

- Test loss/accuracy, macro-F1, rare-class recall theo round, seconds và Joules.
- Time/energy-to-target; báo cả nonattainment và dừng sớm, không chỉ mean trên runs thành công.
- Pin từng nút, return reserve, số client mỗi vòng và độ phủ participation.
- Probe bytes, download bytes, probe energy, inference time, số lần recourse đổi lịch.
- Cost model mismatch và CSI validity sau probe.
- Nếu drift: thay đổi tại cùng physical time giữa các phương pháp; dùng integrated test loss và recovery delay.

### 7.5. Thống kê và tính công bằng

Pilot tối thiểu 5 paired seeds; main study hướng tới 10 hoặc hơn, quyết định bằng observed variance và compute budget. Một seed gồm partition, geometry/trace, checkpoint và exogenous randomness. Paired runs dùng cùng trace theo physical time, không chỉ cùng round index khi tốc độ khác nhau.

Tuning tách test scenarios. Với episode, bootstrap/CI theo independent episode, không coi các vòng phụ thuộc trong cùng run là các mẫu độc lập. Audit seeds và execution seeds khác discovery. Nếu chọn lịch theo audit, audit đó trở thành selection data; cần test/final evaluation tách tiếp.

Equal budget là thực chi phí search+fit+mandatory verification với hardware/worker count cố định. Có thể trình bày search và final reporting audit riêng, nhưng tổng chi phí bắt buộc phải công bố; không để B dùng audit miễn phí nhiều hơn A.

### 7.6. Tiêu chí đạt hoặc dừng

| Gate | Điều kiện đạt | Nếu không đạt |
|---|---|---|
| A physics | ledger đúng, convex solver residual hợp lệ, enumeration khớp trong tolerance | Sửa evaluator trước khi chạy solver lớn |
| A learning | nhiều checkpoint/episode cho thấy trade-off thật, baseline mạnh | Không tuyên bố gain dựa trên một round random-init |
| B usefulness | total verified quality/cost tốt hơn reference đã cache | Bỏ tầng không hữu ích hoặc chuyển H>1 có branching thật |
| B certificate | kiểm tra đúng assumptions và empirical failure phù hợp delta | Giảm claim xuống empirical uncertainty |
| C information | gain sau probe/inference overhead, so cùng safe budgets | Chỉ ra regime no-probe tối ưu/đủ tốt |
| C deployment | không truy cập hidden fields, latency và reserve đạt | Giữ nhãn offline proof-of-concept |

---

## 8. Lộ trình triển khai kế thừa code hiện tại

### 8.1. Hiện trạng cần giữ nguyên nghĩa

v1 đã có actual local SGD, hai MOEA, one-round reference loss, cache, physical ledger và episode loop. Benchmark chính tối ưu một vòng; smoke chạy ba vòng mỗi thuật toán. Lịch thực thi trong kết quả hiện có chọn một client mặc dù cho phép 1–4. Đây là evidence về pipeline/cấu hình hiện tại, chưa chứng minh FL hội tụ hoặc solver nào tốt hơn tổng quát.

### 8.2. Công việc theo thứ tự phụ thuộc

1. **A2-physics:** tham số phần cứng theo từng nút; có profile/sweep; allocator A5 và kiểm tra đối chiếu decoder A6.
2. **A2-learning:** snapshot từ nhiều giai đoạn học; enumeration 6 client; khóa preference trước test; full episodes và client-selection diagnostics.
3. **A2-structure:** representation theo tập + association + deadline; shared reference records và ablation generic/guided.
4. **B-pilot:** profile từng fidelity khi cache bật; đo bias/rank reversal/discrepancy; quyết định B0 hay B-H.
5. **B-cert:** finite frozen pool; fresh streams; B3/B6; archive có witness và unresolved state; không sửa v1 raw-CE rồi gọi silently bounded.
6. **C-model:** explicit observation/likelihood, report payload và compute cost, DL cache, per-stage ledger.
7. **C-policy:** empty probe, singleton/pair library, physical recourse và safe fallback; independent scenario assessment.
8. **C-episode:** partial-observation API; simulator truth bị chặn khỏi controller; measured optimizer runtime; end-to-end comparisons.

Không cần rewrite v1 ngay để đưa mọi tính năng vào một phiên bản. Tách branch/version nghiên cứu mới để còn baseline tái lập.

### 8.3. API tối thiểu

~~~text
PhysicalState:
    geometry, clock, per-node hardware, per-node battery, reserve, link observations

LearningSnapshot:
    immutable checkpoint, local-work config, target weights, evaluation protocol

ControllerHistory:
    authorized reports, model versions, timestamps, observation uncertainty

ResourceSolver.solve(selected_set, association, deadline, physical_state):
    allocation, objective ledger, feasibility certificate/residuals

ReferenceEvaluator.query(snapshot, selected_set, fidelity, seed):
    loss observation, cache dependencies, measured marginal evaluation cost

BeliefModel.update(history, executed_probe, observations):
    posterior or explicitly empirical predictive state

TwoStagePolicy:
    probe plan, observation-to-training decision rule, safe fallback

EvaluationRecord:
    snapshot_id, set_id, schedule_id, fidelity, seed_id,
    physical costs, search costs, interval status, elimination witness
~~~

ReferenceEvaluator chỉ dành cho offline mode. Online mode không được resolve API này bằng cách truy cập datasets/current updates ẩn.

### 8.4. Sơ đồ kế thừa

~~~mermaid
flowchart TD
    P["Vật lý + FL + ledger + information contract"] --> A["A: chọn tập và cấp tài nguyên"]
    A --> B["B: phân bổ đánh giá và kiểm tra front"]
    P --> C["C: probe có chi phí và recourse"]
    A --> C
    B --> C
    A --> EA["Snapshot + episode benchmark"]
    B --> EB["Quality theo compute budget + confidence"]
    C --> EC["Loss cuối + tổng Joule + tổng giây"]
~~~

---

## 9. Kiểm toán các tuyên bố lý thuyết

| Kết quả | Đã chứng minh trong báo cáo | Điều kiện phải kiểm tra | Không suy ra |
|---|---|---|---|
| L6 | Descent identity từ smoothness | Segment smoothness, $\gamma \le 1/L$ | Validation/test convergence |
| L9–L10 | Stationarity bound có selection/drift/noise | Unbiased noise, independent execution selection/failure cho variance simplification | Hội tụ global optimum hoặc $D_k$ tự giảm |
| L11–L12 | Biên model staleness và residual | Known gradient/report bounds | Age theo giây đủ thay model drift |
| A2 | Learning invariance theo S | Fixed work, successful upload, correct aggregation | Invariance khi dropout phụ thuộc resource |
| A5 | Convex resource subproblem | Fixed association/channel, energy form S5–S7 | Convex toàn MINLP/quỹ đạo |
| A6–A7 | CPU optimum và Pareto reduction | Base energy, loss invariant | Exact continuous front từ lưới hữu hạn |
| B3 | Simultaneous CI | Bounded samples, valid bias bound, fixed pool/fresh streams | Ensemble spread là confidence interval |
| B6–B7, B10 | Safe dominance, additive coverage và stopping certificate | Valid intervals trên cùng target; exact E/T cho B10; archive cuối có witnesses | Global Pareto optimum ngoài pool, membership từng điểm hoặc certificate tự chuyển sang corpus khác |
| C9–C11 | EVSI và net-value identity | Định nghĩa prior/cost/domain nhất quán | Probe luôn tốt |
| C12–C14 | 2r cho empirical minimizer; 4r cho policy dùng no-probe guard | Fixed full policy/fallback, fixed n hoặc time-uniform bound, fresh iid scenarios, bounded cost, model đúng | Tự do đổi recourse sau certification, optimal POMDP hoặc real-world guarantee khi model sai |
| C3–C3a, C5 | Update pin và belief theo thời gian từng pha | Optimizer costs đã trừ, transition/observation model đúng, pin có bound | Perfect CSI hoặc hard pin safety từ mean telemetry |

Các định lý là phép suy ra có thể kiểm tra, không phải tất cả đều là phát minh mới. Mức novelty và mức correctness phải được đánh giá riêng.

---

## 10. Nguồn tham khảo và mức độ sử dụng

**R1. Research draft JNCA của project.** [PDF](JNCA_Huy.pdf). Đã đọc toàn bộ 13 trang; mục 4 phân biệt full horizon/round-level; mục 6–8 định nghĩa A/B/C. Đây là nguồn chính của phạm vi đề xuất.

**R2. Yang, Feng, Ma, Liu, Pei, Wu — FSTPO, IEEE Internet of Things Journal, accepted author version 2026.** [PDF trong project](../source%20idea/Federated_Spatio-Temporal_Policy_Learning_for_Efficient_Resource_Management_in_UAV-Assisted_IoT_Edge_Networks.pdf), [DOI](https://doi.org/10.1109/JIOT.2026.3727888). Đọc abstract, mô hình và formulation trang 3–5; dùng để đối chiếu scope, additive learning utility, offloading và hover accounting.

**R3. Al-Hourani, Kandeepan, Lardner — Optimal LAP Altitude for Maximum Coverage, IEEE Wireless Communications Letters, 2014.** [DOI](https://doi.org/10.1109/LWC.2014.2342736), [bản paper](https://picture.iczhiku.com/resource/paper/wyKFuUYeUWEHWBMx.pdf). Nguồn dạng xác suất LoS phụ thuộc góc nâng; không coi tham số môi trường là universal.

**R4. Zeng, Xu, Zhang — Energy Minimization for Wireless Communication with Rotary-Wing UAV.** [Bản tác giả](https://arxiv.org/abs/1804.02238), [full text HTML](https://arxiv.org/html/1804.02238). Nguồn mô hình propulsion và giới hạn hover/flight. Dùng mô hình vật lý, không vay bảo đảm thuật toán trajectory của paper cho bài toán FL.

**R5. Balakrishnan và cộng sự — Diverse Client Selection for Federated Learning via Submodular Maximization, ICLR 2022.** [Repository tác giả và metadata](https://github.com/melodi-lab/divfl), [bản workshop 2021](https://fl-icml.github.io/2021/papers/FL-ICML21_paper_67.pdf). Dùng để kiểm tra rằng representative set selection đã có; không đồng nhất facility-location surrogate với D(S) của báo cáo.

**R6. Lai, Zhu, Madhyastha, Chowdhury — Oort: Efficient Federated Learning via Guided Participant Selection, OSDI 2021.** [USENIX](https://www.usenix.org/conference/osdi21/presentation/lai). Nguồn baseline kết hợp learning utility và systems efficiency.

**R7. Belakaria, Deshwal, Doppa — Multi-Fidelity Multi-Objective Bayesian Optimization: An Output Space Entropy Search Approach, AAAI 2020.** [Trang paper](https://ojs.aaai.org/index.php/AAAI/article/view/6560). Nguồn MF-OSEMO và information-per-cost; trang nhà xuất bản có thông báo corrigendum 24/09/2020, cần dùng bản sửa khi tái hiện.

**R8. Daulton, Balandat, Bakshy — Hypervolume Knowledge Gradient: A Lookahead Approach for Multi-Objective Bayesian Optimization with Partial Information, ICML 2023.** [PMLR](https://proceedings.mlr.press/v202/daulton23a.html). Nguồn đối chiếu lookahead/partial-information multiobjective BO; không gán tính tối ưu của phương pháp này cho B8.

**R9. Kone, Kaufmann, Richert — Bandit Pareto Set Identification: the Fixed Budget Setting, AISTATS 2024.** [PMLR](https://proceedings.mlr.press/v238/kone24a.html). Nguồn closest theory cho finite-arm Pareto identification; báo cáo không tuyên bố kế thừa sample-optimality của paper.

**R10. Golovin, Krause — Adaptive Submodularity: Theory and Applications in Active Learning and Stochastic Optimization, JAIR 2011.** [Bản tác giả](https://arxiv.org/abs/1003.3967), [paper JAIR](https://aaai-21.aaai.org/Papers/JAIR/Vol42/JAIR4212.pdf). Nguồn giới hạn điều kiện của greedy adaptive acquisition.

**R11. Mikkola, Martinelli, Filstroff, Kaski — Multi-Fidelity Bayesian Optimization with Unreliable Information Sources, AISTATS 2023.** [PMLR](https://proceedings.mlr.press/v206/mikkola23a.html). Dùng xác định unreliable fidelity là bài toán đã tồn tại; cần full-text comparison khi viết related work.

**R12. Yahya, Maghsudi, Stanczak — Federated Learning in UAV-Enhanced Networks: Joint Coverage and Convergence Time Optimization.** [Bản tác giả, arXiv 2308.16889](https://arxiv.org/abs/2308.16889). Đã kiểm tra abstract: multiobjective bandit và cost-aware best-arm identification dưới thiếu thông tin; chưa khẳng định vắng probing/recourse chỉ từ abstract.

**R13. Zou và cộng sự — Value of Information: A Comprehensive Metric for Client Selection in Federated Edge Learning, IEEE Transactions on Computers, 2024.** [DOI](https://doi.org/10.1109/TC.2024.3355777), [trang tác giả](https://faculty.sdu.edu.cn/chengxiuzhen/zh_CN/lwcg/818975/content/421215.htm). Đã xác minh title/venue trên trang tác giả; IEEE full text bị chặn trong phiên này. Chỉ dùng làm cảnh báo overlap thuật ngữ; chưa suy diễn cơ chế bên trong.

**R14. Matsumoto, Ishikura, Karasuyama — A Unified Information-Theoretic Approach to Constrained Multi-Fidelity Multi-Objective Bayesian Optimization.** [arXiv 2610.10174](https://arxiv.org/abs/2610.10174), bản ngày 07/10/2026. Đã kiểm tra abstract; là preprint mới, không ghi nhận là peer-reviewed. Cần full-text comparison trước khi chốt B.

**R15. Howard, Ramdas, McAuliffe, Sekhon — Time-uniform, nonparametric, nonasymptotic confidence sequences, Annals of Statistics 49(2), 2021.** [Bản tác giả](https://arxiv.org/abs/1810.08240), [DOI](https://doi.org/10.1214/20-AOS1991). Nguồn phân biệt fixed-sample intervals và time-uniform confidence sequences. B3 trong báo cáo là phép union bound n² viết trực tiếp, không tuyên bố đạt các cận sắc của paper.

**R16. Boyd và Vandenberghe — Convex Optimization.** [Trang sách chính thức của tác giả](https://web.stanford.edu/~boyd/cvxbook/). Nguồn nền về convex composition, duality, Slater và KKT. Chứng minh áp dụng cụ thể cho A5 nằm trong mục 3.3; không dùng sách để suy rằng toàn MINLP hoặc MOEA có global guarantee.

**Phạm vi rà soát:** tìm nguồn gốc/nhà xuất bản/tác giả cho set-based FL selection, UAV-FL dưới thiếu thông tin, multi-fidelity Pareto search, Pareto identification, VOI và adaptive submodularity; không phải systematic review đầy đủ. Không đưa các nguồn chỉ có đoạn quảng bá hoặc tổng hợp không xác minh vào cơ sở chứng minh.

Các phép chứng minh L6, L9, A3–A7, B3, B6–B7 và C9–C14 được viết trực tiếp trong báo cáo từ các giả thiết đã nêu. Những kỹ thuật nền như descent lemma, convex composition, Hoeffding và union bound là kiến thức chuẩn; các phép ghép vào mô hình không tự tạo tính mới của bài báo.
---

## 11. Kiểm tra kỹ thuật của tài liệu trong phiên soạn

- Kiểm tra mã hóa UTF-8, cặp khối công thức, mã giả và nhãn phương trình; kiểm tra các liên kết file nội bộ.
- Kiểm tra số L6 trên 1.000 trường hợp quadratic trơn: sai số đồng nhất thức lớn nhất khoảng 1.42e−14.
- Giải một bài tài nguyên ba client bằng SciPy SLSQP và đối chiếu A6: khớp trong tolerance 1e−5; residual nhỏ nhất khoảng −1.19e−13. Các tham số dimensionless chỉ dùng kiểm tra công thức, không phải kết quả mô phỏng UAV.
- Kiểm tra phản ví dụ non-submodularity: hai marginal −0.25 và +0.25.
- Kiểm tra B7 trên 50 finite pools ngẫu nhiên có bounded loss perturbation: đều thỏa additive coverage 2 epsilon.
- Kiểm tra số ví dụ C11: probe có thể đổi từ lợi ích +0.4 sang −0.2 khi làm mất hai recourse actions.

Các kiểm tra số này chỉ giúp phát hiện lỗi công thức; **không thay thế chứng minh, kiểm định giả thiết vật lý, đánh giá thuật toán hay review độc lập**. Không chạy lại benchmark v1 và không sửa source code trong công việc soạn báo cáo này.
---

## 12. Rà soát lần 2: hiệu chỉnh và kiểm tra ngày 28/10/2026

### 12.1. Các điểm đã sửa

| Nhóm | Vấn đề của bản trước | Hiệu chỉnh |
|---|---|---|
| Physical ledger | RF power và electrical power chưa phân biệt rõ; pin sau probe chưa trừ optimizer-P | Phân biệt PA/circuit power, tách bốn khoảng thời gian và sửa C3 |
| State/observation | Static Bayes update không đủ cho channel biến đổi; thiếu failure report | Thêm C3a, timestamps, missing observations và điều kiện pin có lower bound |
| FL theory | Cận moment/variance chưa ghi rõ conditioning theo selection | Khóa $\mathcal{G}_k$, independent execution seed streams, uniform conditional moment bounds |
| Direction A | Biến d chưa có trong argmin; resource convexity cần từng node ledger | Bổ sung miền biến, fixed DL/BH assumptions, convex battery ledgers và deadline cap |
| Pareto resource sweep | Đồng năng lượng có thể cần tie-break; lưới không phải exact front | Lexicographic E rồi T, tách lý thuyết exact khỏi solver/grid tolerance |
| Cache cost | Aggregation vẫn bị tính khi hit model/loss | Sửa B2 với ba cache riêng và lookup overhead |
| B sampling | Repeated validation trên cached model có thể bị nhầm thành independent SGD replicates | Tách expected-SGD target và fixed-seed SAA; cấm cherry-pick favorable seeds |
| B target/uncertainty | CI không tự chuyển giữa validation corpora hoặc fidelity models refit | Khóa $V_{\rm cert}$/protocol; nêu bias-bound failure budget và ordered prefix sampling |
| B certificate | Thiếu stopping test cụ thể; HV raw/normalized $\epsilon$ bị lẫn | Thêm B10 cho archive cuối; sửa cận HV theo $\epsilon/\text{scale}_L$ |
| C policy guarantee | Fixed-n bound dễ bị dùng cho adaptive stopping; recourse có thể đổi sau đánh giá | Khóa full mapping/solver/fallback; phân biệt fixed-n và time-uniform |
| C decision rule | 2r chỉ cho empirical minimizer, không tự cho policy có no-probe guard | Bổ sung cận 4r và phản ví dụ; so overhead đúng với no-probe comparator |
| Scope/novelty | Một số câu có thể đọc như H>1 chắc chắn sửa single-client outcome | Giảm về giả thuyết cần kiểm nghiệm; giữ trạng thái novelty chưa được xác nhận toàn diện |

### 12.2. Kiểm tra bổ sung trong lần rà soát

- 100 finite pools ngẫu nhiên: kiểm tra witness coverage B10 và true-objective HV deficit sau chuẩn hóa scale loss.
- 10.000 trường hợp có estimation errors bị chặn: kiểm tra cận 2r của empirical minimizer, 4r của guarded policy, và so với no-probe trong cùng controller.
- Phản ví dụ số với costs (0.4,0), estimates (0.3,0.1), r=0.1 xác nhận không được dùng cận 2r cho output sau guard.
- Kiểm tra trường hợp đọc lại một cached Bernoulli loss: không tăng số independent SGD samples.
- Kiểm tra các nhánh cache hit/miss và đẳng thức pin cuối từ ledger theo pha.
- Kiểm tra lại liên kết local, nhãn phương trình, trích dẫn R1–R16, UTF-8 và cấu trúc Markdown.

Các kiểm tra đều đạt trong các trường hợp đã chạy. Chúng kiểm tra consistency và phản ví dụ, không thay thế chứng minh tổng quát. Những giới hạn còn lại: giả thiết physical/statistical phải được kiểm định; B10 chỉ cho finite pool và fixed evaluation target; C cần belief model và recourse implementation đúng; novelty vẫn cần full-text comparison với các công trình gần nhất. Không sửa hoặc chạy lại source/benchmark v1 trong lần rà soát này.