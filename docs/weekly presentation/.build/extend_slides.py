from pathlib import Path
s=Path('slides.tex').read_text(encoding='utf-8')
def frame(t,b,src): return '\n\\begin{frame}[t]{'+t+'}\\relax\n\\small\n'+b+'\n\\source{'+src+'}\n\\end{frame}\n'
f='McMahan và cộng sự, 1602.05629v4, Sec. 2 và Algorithm 1 (có erratum).'
j='Information-Aware Multiobjective Evolutionary Optimization, bản thảo nghiên cứu, Sec. '
a=''
a+=frame('FedAvg: bài toán học chung',r'''Có $K$ thiết bị; thiết bị $k$ giữ tập chỉ số $\mathcal P_k$, $n_k=|\mathcal P_k|$, $n=\sum_k n_k$. Mọi thiết bị dùng cùng kiến trúc mô hình $w\in\mathbb R^d$.
\[\min_{w\in\mathbb R^d}f(w)=\frac1n\sum_{i=1}^n f_i(w)
=\sum_{k=1}^K\frac{n_k}{n}F_k(w),\qquad
F_k(w)=\frac1{n_k}\sum_{i\in\mathcal P_k}f_i(w).\]
\begin{itemize}\item $f_i(w)=\ell(x_i,y_i;w)$: lỗi dự đoán trên một mẫu.
\item $F_k$: loss trung bình cục bộ; $f$: loss trên toàn bộ dữ liệu.
\item Biến tối ưu là trọng số mô hình $w$; dữ liệu vẫn ở thiết bị.
\end{itemize}
\eqmeaning{Thiết bị nhiều mẫu có trọng số lớn hơn; mục tiêu này không mặc định cân bằng công bằng giữa các thiết bị.}''',f)
a+=frame('FedAvg: input và output',r'''\begin{tabularx}{\textwidth}{@{}p{2cm}Y@{}}\toprule
Thành phần & Nội dung\\\midrule
Input dữ liệu & Các tập $\mathcal P_k$ phân tán, kích thước $n_k$; server không cần nhận mẫu thô.\\
Input mô hình & Kiến trúc chung, hàm loss khả vi, khởi tạo $w_0$.\\
Siêu tham số & Tỷ lệ tham gia $C$, số epoch cục bộ $E$, minibatch $B$, learning rate $\eta$.\\
Output mỗi vòng & Mô hình toàn cục mới $w_{t+1}$ sau tổng hợp.\\
Output cuối & Mô hình $w_T$ để suy luận; chất lượng đánh giá trên dữ liệu kiểm tra riêng.\\\bottomrule\end{tabularx}
\eqmeaning{$T$ là ngân sách số vòng dùng khi triển khai mã giả; không phải số epoch cục bộ $E$.}''',f)
a+=frame('Objective và constraint: đọc đúng phạm vi',r'''\textbf{Objective toán học:} tối thiểu hóa empirical loss $f(w)$, thường không lồi với mạng neural.
\par\medskip
\textbf{Động cơ thiết kế:} giảm số vòng giao tiếp để đạt chất lượng mục tiêu bằng cách tăng tính toán cục bộ.
\begin{itemize}
\item Bài FedAvg không đặt một hệ ràng buộc công suất, CPU hay deadline trong bài toán $\min_w f(w)$.
\item Giả thiết thực nghiệm: tập client và dữ liệu cố định, cập nhật đồng bộ, chọn ngẫu nhiên một phần client mỗi vòng.
\item Non-IID và mất cân bằng kích thước dữ liệu là đặc tính bài toán, không phải bất đẳng thức ràng buộc.
\item Dữ liệu giữ tại client; gửi cập nhật không tự tạo bảo đảm differential privacy.
\end{itemize}''',f)
a+=frame('Mã giả FedAvg: phía server',r'''\begin{enumerate}
\item Khởi tạo mô hình chung $w_0$.
\item Với mỗi vòng $t=0,\ldots,T-1$:
\item Chọn ngẫu nhiên tập $S_t$ gồm $m=\max(\lfloor CK\rfloor,1)$ client.
\item Gửi $w_t$; chạy song song $w_{t+1}^k\leftarrow\operatorname{ClientUpdate}(k,w_t)$ với $k\in S_t$.
\item Tính $n_{S_t}=\sum_{k\in S_t}n_k$ và tổng hợp
\[w_{t+1}=\sum_{k\in S_t}\frac{n_k}{n_{S_t}}w_{t+1}^k.\]
\item Trả về $w_T$ khi hết ngân sách.
\end{enumerate}
\noteonly{Mã giả diễn giải Algorithm 1: quy ước làm tròn được ghi rõ. Bản v4 sửa mẫu số thành tổng số mẫu của các client được chọn.}''',f)
a+=frame('Mã giả FedAvg: phía client',r'''\textbf{ClientUpdate$(k,w)$}
\begin{enumerate}\item Nhận $w=w_t$ từ server; tạo các minibatch kích thước $B$ từ $\mathcal P_k$.
\item Với epoch $e=1,\ldots,E$, duyệt từng minibatch $b$:
\[w\leftarrow w-\eta\nabla\ell(w;b).\]
\item Gửi mô hình cuối $w$ về server; dữ liệu thô giữ tại chỗ.
\end{enumerate}
\eqmeaning{Mỗi client đi nhiều bước SGD từ cùng $w_t$, rồi server trung bình các điểm cuối.}
\par\medskip
$E$ lớn hoặc $B$ nhỏ làm tăng số bước local, xấp xỉ $E n_k/B$. Điều này có thể giảm giao tiếp, nhưng tăng sai lệch giữa các cập nhật khi dữ liệu khác nhau. Không nên mặc định tăng $E$ luôn tốt.''',f)
a+=frame('Từ FedAvg đến bài toán tài nguyên FSTPO',r'''\begin{itemize}
\item FedSGD với full batch và một bước local tổng hợp các gradient; FedAvg cho phép nhiều bước local trước khi giao tiếp.
\item Cùng điểm xuất phát giúp việc trung bình mô hình có ý nghĩa; trung bình các mạng khởi tạo độc lập có thể cho kết quả xấu.
\item Bài báo báo cáo giảm khoảng $10$--$100$ lần số vòng giao tiếp trong các thí nghiệm so với SGD đồng bộ; đây không phải bảo đảm cho mọi dữ liệu.
\item FedAvg chọn ngẫu nhiên client; FSTPO học chọn client và cấp băng thông/CPU trong mạng UAV.
\end{itemize}
\eqmeaning{Tầng học tối ưu $w$; tầng điều khiển tài nguyên chọn ai được học và với chi phí nào. Hai tầng liên quan nhưng có biến tối ưu khác nhau.}''',f)
s=s.replace('\\section{System model and problem formulation}',a+'\n\\section{System model and problem formulation}')
b='\\section{Hướng mở rộng dựa trên bản thảo JNCA}\n\\hustpartpage{4}{HƯỚNG MỞ RỘNG}{Chọn tập thiết bị, đa mục tiêu và đa mức đánh giá}\n'
b+=frame('Hướng mở rộng: từ utility đến chất lượng học',r'''\textbf{Xuất phát từ FSTPO:} điều khiển $s,b,f$ để cân bằng utility FL thay thế, năng lượng và thời gian.
\par\medskip
\textbf{Bản thảo JNCA đề xuất:}
\begin{itemize}\item Giữ loss validation toàn quần thể làm mục tiêu chất lượng học.
\item Xem giá trị dữ liệu theo cả tập client: dữ liệu hiếm có thể bổ trợ, gradient khác biệt cũng có thể do nhiễu.
\item Tìm tập phương án Pareto thay vì chỉ một nghiệm ứng với bộ trọng số cố định.
\item Giảm chi phí tìm kiếm bằng đánh giá đa mức; chỉ thu thập thông tin mới khi đáng chi phí.
\end{itemize}
\noteonly{Đây là working draft: các đóng góp và lợi ích cần thực nghiệm kiểm chứng.}''',j+'1--2, 4.')
b+=frame('Mô hình mở rộng: ba mục tiêu',r'''\[\min_{\pi}\mathbf J(\pi)=\left(
\mathbb E[L_{\rm val}(w_K)],\;
\mathbb E\!\left[\sum_{k=0}^{K-1}E_k\right],\;
\mathbb E\!\left[\sum_{k=0}^{K-1}T_k\right]\right).\]
\[L_{\rm val}(w)=\sum_m p_m\frac1{|\mathcal V_m|}
\sum_{\xi\in\mathcal V_m}\ell(w;\xi),\quad \sum_m p_m=1.\]
\begin{itemize}\item Input: checkpoint, lịch sử báo cáo, kênh, giới hạn tài nguyên và pin.
\item Output: tập lịch khả thi Pareto; chọn một lịch theo ưu tiên triển khai đã định trước.
\item $p_m$ cố định theo quần thể mục tiêu; không đổi chỉ vì bỏ client khó phục vụ.
\item Validation, training và test tách biệt; validation thực tế cần quyền truy cập và tính chi phí.
\end{itemize}''',j+'2.1, 4; (3), (27).')
b+=frame('Biến quyết định và ràng buộc mở rộng',r'''\textbf{Lõi ban đầu:} $x=(s,b^T,f^T)$; tùy chọn probing thêm $(z,b^P,f^P)$.
\[s_{m,u}\in\{0,1\},\quad\sum_u s_{m,u}\le1,\quad
0\le b^T_{m,u}\le B_u s_{m,u},\quad\sum_m b^T_{m,u}\le B_u.\]
\[f_m^{\min}s_m\le f_m^T\le f_m^{\max}s_m,\quad
1\le\sum_m s_m\le N_{\max}.\]
\[T_k\le T_{\max},\qquad B_i^{k+1}=B_i^k-E_i^k\ge B_i^{\rm reserve}.\]
\eqmeaning{Client không hoạt động nhận tài nguyên bằng 0; lịch phải thỏa khả dụng đường truyền, deadline và pin.}
\noteonly{JNCA ban đầu dùng quỹ đạo cho trước, FL đồng bộ; offloading ứng dụng độc lập của FSTPO chưa nằm trong lõi này. Kết hợp hai bài cần thống nhất phạm vi chi phí.}''',j+'3--4; (14)--(16), (24), (28).')
b+=frame('Hướng A: chọn tập client có tính bổ trợ',r'''\[\Delta V(m\mid S)=\widehat V(S\cup\{m\})-\widehat V(S).\]
\textbf{Ví dụ của bản thảo:} ba gradient vô hướng $(2,-2,1)$, trọng số bằng nhau; gradient quần thể $\bar g=1/3$.
\begin{itemize}\item Cặp $\{1,2\}$ trung bình bằng $0$, sai số bình phương $1/9$.
\item Cặp $\{1,3\}$ trung bình bằng $1.5$, sai số $49/36$.
\item Hai gradient rất khác nhau có thể bổ trợ tốt khi xét cùng nhau.
\end{itemize}
\textbf{Thuật toán:} sinh quần thể lịch khả thi $\to$ lai/đột biến tập client và tài nguyên $\to$ sửa ràng buộc $\to$ đánh giá $\to$ chọn theo Pareto và đa dạng.
\noteonly{Khớp gradient chỉ là proxy; phải kiểm tra loss validation. Giá trị biên có thể âm và không mặc định có tính submodular.}''',j+'2.2, 6; Algorithm 1.')
b+=frame('Hướng B: đánh giá đa mức fidelity',r'''\begin{center}\begin{tikzpicture}[node distance=.65cm]
\node[box,text width=8cm](a){Mức 1: dự đoán từ sketch và lịch sử (rẻ)};
\node[box,text width=8cm,below=of a](b){Mức 2: rollout giảm công hoặc giảm validation};
\node[box,text width=8cm,below=of b](c){Mức 3: đánh giá tham chiếu đủ công việc};
\draw[flow](a)--(b);\draw[flow](b)--(c);
\end{tikzpicture}\end{center}
Chỉ nâng mức các ứng viên có triển vọng hoặc cần khám phá; hiệu chuẩn sai lệch giữa các mức. Năng lượng/thời gian vật lý vẫn tính cho lịch đầy đủ.
\eqmeaning{Dành đánh giá đắt cho ứng viên có thể cải thiện tập Pareto; không đồng nhất fidelity với probing vật lý.}''',j+'7; (37)--(42).')
b+=frame('Mã giả tìm kiếm đa mức và kiểm chứng',r'''\begin{enumerate}\item Chốt snapshot, ngân sách tìm kiếm và ngân sách audit độc lập.
\item Sinh ứng viên; đánh giá tham chiếu một tập khởi tạo để hiệu chuẩn.
\item Lặp: lai/đột biến, sửa ràng buộc, tính chi phí vật lý và dự đoán loss rẻ.
\item Chọn ứng viên nâng fidelity theo lợi ích dự kiến trên chi phí; giữ tỷ lệ khám phá.
\item Cập nhật predictor và hai kho: dự đoán tạm thời, tham chiếu đã kiểm chứng.
\item Audit ứng viên cuối bằng cùng giao thức tham chiếu; tính lại quan hệ trội.
\item Chọn và thực thi một lịch theo ưu tiên đã khai báo.
\end{enumerate}
\noteonly{Chỉ kho tham chiếu dùng để báo cáo chất lượng Pareto. Rollout giả lập không cập nhật checkpoint nguồn và không được tính là vòng FL thực thi.}''',j+'7; Algorithm 2.')
b+=frame('Hướng C: probing và lập lịch lại',r'''\begin{center}\begin{tikzpicture}[node distance=.5cm]
\node[box,text width=8cm](a){Lịch sử $\mathcal H_k$: báo cáo cũ, kênh, pin};
\node[box,text width=8cm,below=of a](b){Chọn probe $\to$ trả chi phí $\to$ nhận thông tin mới};
\node[box,text width=8cm,below=of b](c){Cập nhật dự đoán $\to$ tối ưu lại lịch training};
\draw[flow](a)--(b);\draw[flow](b)--(c);
\end{tikzpicture}\end{center}
Probe có thể lấy loss minibatch và gradient sketch. Chọn cả phương án không probe; client vẫn có thể training mà không cần probe mới.
\eqmeaning{Thông tin đáng mua khi có khả năng thay đổi quyết định đủ để bù chi phí tải mô hình, tính toán, upload và chờ.}''',j+'2.3, 8; Algorithm 3.')
b+=frame('Đề xuất kết hợp với FSTPO',r'''\textbf{Ý tưởng tổng hợp của phần trình bày, cần kiểm chứng:}
\begin{enumerate}\item Dùng actor FSTPO sinh lịch khởi tạo khả thi cho tìm kiếm tiến hóa; bổ sung lịch ngẫu nhiên để giữ đa dạng.
\item Đánh giá lịch bằng bộ ba loss--energy--time; giữ baseline FSTPO trên cùng môi trường và ngân sách.
\item Dùng predictor đa fidelity để sàng lọc và tham chiếu để xác nhận các cải thiện.
\item Sau khi lõi ổn định, thêm tuổi thông tin và probing; mọi quyết định chỉ dùng quan sát được phép.
\end{enumerate}
\noteonly{Đây không phải thuật toán đã được hai bài chứng minh. Có thể nghiên cứu scheduler tiến hóa độc lập trước; warm-start bằng FSTPO là một ablation bổ sung.}''',j+'6--10; liên hệ với Yang và cộng sự, Sec. III.')
b+=frame('Lộ trình và tiêu chí kiểm chứng',r'''\begin{enumerate}\item Bắt đầu với 2 UAV, 6 client, cùng checkpoint; đặt client dữ liệu hiếm ở kênh yếu. Liệt kê tập con với phân bổ cố định để có mốc kiểm tra.
\item So sánh chọn ngẫu nhiên, greedy kênh, FSTPO, NSGA-II và chọn tập có tính bổ trợ trên cùng thông tin/tài nguyên.
\item Chỉ thêm đa fidelity nếu profiling chứng minh đánh giá tham chiếu đủ đắt và mức rẻ có ích.
\item Báo cáo Pareto đã audit, test accuracy/loss, rare-class recall, thời gian/năng lượng, vi phạm deadline và chi phí optimizer.
\item Ablation: bỏ set-aware, bỏ multi-fidelity, bỏ probing; so sánh với cùng chi phí tìm kiếm thực tế.
\end{enumerate}
\eqmeaning{Mục tiêu là chứng minh trade-off tốt hơn sau khi tính đủ chi phí, chưa khẳng định hiệu quả trước thực nghiệm.}''',j+'9--10.')
s=s.replace('\\begin{frame}[t]{Tài liệu tham khảo}',b+'\n\\begin{frame}[t]{Tài liệu tham khảo}')
s=s.replace('Khái niệm, quy trình và thách thức','Khái niệm, bài toán tối ưu và thuật toán FedAvg')
Path('slides.tex').write_text(s,encoding='utf-8')
