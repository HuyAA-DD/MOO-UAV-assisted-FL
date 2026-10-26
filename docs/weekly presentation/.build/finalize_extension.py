from pathlib import Path
p=Path('slides.tex');s=p.read_text(encoding='utf-8').replace('Phần 1: khái niệm, cách hoạt động và ví dụ FL.','Phần 1: FL, mô hình bài toán và mã giả FedAvg.').replace('\\item Phần 3: sơ đồ FSTPO và các cơ chế chính.','\\item Phần 3: sơ đồ FSTPO và các cơ chế chính.\n  \\item Phần 4: hướng mở rộng dựa trên bản thảo JNCA.')
s=s.replace('\\end{document}',r'''\begin{frame}[t]{Tài liệu bổ sung cho phần 1 và phần 4}\relax
\small
\begin{itemize}
\item McMahan và cộng sự. \emph{Communication-Efficient Learning of Deep Networks from Decentralized Data}. Bản arXiv 1602.05629v4, 26/01/2023; công bố gốc AISTATS 2017. Sec. 2, Algorithm 1 và phần thực nghiệm.\\
\url{https://arxiv.org/abs/1602.05629}
\item \emph{Information-Aware Multiobjective Evolutionary Optimization with Multi-Fidelity Evaluation for UAV-Assisted Federated Learning}. Research Working Draft, bản PDF người dùng cung cấp, 13 trang. Sec. 1--10, Algorithms 1--3.
\end{itemize}
\par\medskip
Phần 4 phân biệt đề xuất của bản thảo và ý tưởng kết hợp với FSTPO; chưa coi các giả thuyết nghiên cứu là kết quả đã kiểm chứng.
\end{frame}
\end{document}''');p.write_text(s,encoding='utf-8')
