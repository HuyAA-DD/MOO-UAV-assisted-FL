from pathlib import Path

parts = [r'''% !TeX program = xelatex
% Biên dịch bằng XeLaTeX hai lần, hoặc: tectonic slides.tex
% Template: HUST_PPT_template_2022_RED_4x3.pptx (nền và logo gốc).
% Giữ thư mục assets/ cạnh slides.tex. Font Lato được đóng gói trong assets/fonts/.
% Các sơ đồ là mã TikZ chỉnh sửa được; biểu đồ non-IID là ví dụ minh họa.
% Phần II chứa đầy đủ (1)--(15) và các công thức không đánh số của Sec. II.
% Giữ nguyên cách viết của paper, kể cả các điểm cần lưu ý về đơn vị/C7.
\documentclass[10pt,aspectratio=43]{beamer}
\usepackage[no-math]{fontspec}
\setsansfont{Lato}[Path=assets/fonts/,Extension=.ttf,
  UprightFont=*-Regular,BoldFont=*-Bold,ItalicFont=*-Italic,BoldItalicFont=*-BoldItalic]
\setmainfont{Lato}[Path=assets/fonts/,Extension=.ttf,
  UprightFont=*-Regular,BoldFont=*-Bold,ItalicFont=*-Italic,BoldItalicFont=*-BoldItalic]
\usepackage{amsmath,amssymb,booktabs,tabularx,graphicx,tikz}
\usetikzlibrary{arrows.meta,positioning,calc,shapes.geometric}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\usefonttheme{professionalfonts}
\definecolor{HustRed}{HTML}{C00000}
\definecolor{HustBand}{HTML}{BE1E2D}
\definecolor{HustGold}{HTML}{E7A000}
\definecolor{Ink}{HTML}{292929}
\definecolor{Muted}{HTML}{666666}
\definecolor{Blue}{HTML}{2F6591}
\setbeamercolor{normal text}{fg=Ink,bg=white}
\setbeamercolor{structure}{fg=HustRed}
\setbeamercolor{frametitle}{fg=white}
\setbeamercolor{block title}{fg=HustRed,bg=white}
\setbeamercolor{block body}{fg=Ink,bg=white}
\setbeamerfont{block title}{series=\bfseries}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{itemize items}[circle]
\setbeamertemplate{sections/subsections in toc}[sections numbered]
\setbeamersize{text margin left=.55cm,text margin right=.55cm}
\setbeamertemplate{background}{\includegraphics[width=\paperwidth,height=\paperheight]{assets/hust/content.png}}
\setbeamertemplate{frametitle}{%
  \begin{tikzpicture}[remember picture,overlay]
    \node[anchor=west,text=white,inner sep=0pt,
      font=\fontsize{13.4}{15}\selectfont\bfseries]
      at ([xshift=.36cm,yshift=-.43cm]current page.north west){\insertframetitle};
  \end{tikzpicture}\vspace{.81cm}}
\setbeamertemplate{footline}{%
  \hfill\textcolor{HustRed}{\fontsize{6.2}{7}\selectfont\insertframenumber/\inserttotalframenumber}
  \hspace{.32cm}\vspace{.10cm}}
% Chừa khoảng trắng cho logo và đường kẻ chân trang trong template gốc.
\addtobeamertemplate{footline}{\vspace{.51cm}}{}
\setlength{\parskip}{.25em}
\newcommand{\source}[1]{\par\vfill{\fontsize{5.8}{7}\selectfont\color{Muted}Nguồn: #1\par}}
\newcommand{\paperref}[1]{\source{Yang và cộng sự, Sec.~#1. Số công thức theo paper gốc.}}
\newcommand{\flref}{\source{\href{https://cloud.google.com/discover/what-is-federated-learning}{Google Cloud, What is federated learning?}}}
\newcommand{\eqmeaning}[1]{\par\medskip\textcolor{HustRed}{\textbf{Ý nghĩa:}} #1\par}
\newcommand{\noteonly}[1]{\par{\footnotesize\color{Muted}#1\par}}
\newcommand{\FL}{\mathrm{FL}}
\newcommand{\tot}{\mathrm{total}}
\newcommand{\Acc}{\mathrm{Acc}}
\newcommand{\paperfile}{Federated_Spatio-Temporal_Policy_Learning_for_Efficient_Resource_Management_in_UAV-Assisted_IoT_Edge_Networks.pdf}
\tikzset{
  box/.style={draw=HustRed,fill=white,rounded corners=2pt,align=center,
    minimum height=.75cm,inner sep=5pt,font=\small},
  faint/.style={box,draw=Muted},
  flow/.style={-{Latex[length=2mm]},line width=.7pt,draw=HustRed},
  dataflow/.style={-{Latex[length=2mm]},line width=.7pt,draw=Blue},
  lab/.style={font=\scriptsize,align=center,fill=white,inner sep=2pt}
}
\newcommand{\hustpartpage}[3]{%
  {\setbeamertemplate{background}{\includegraphics[width=\paperwidth,height=\paperheight]{assets/hust/section.png}}
  \begin{frame}[plain]
    \vfill\centering
    {\color{white}\fontsize{13}{16}\selectfont PHẦN #1\par}
    \vspace{.45cm}
    {\color{white}\fontsize{22}{27}\selectfont\bfseries #2\par}
    \vspace{.45cm}
    {\color{white}\normalsize #3\par}
    \vfill
  \end{frame}}
}
\hypersetup{pdftitle={Học liên kết và quản lý tài nguyên trong mạng IoT có UAV hỗ trợ},
 pdfauthor={Tóm tắt bài báo của Xiaoteng Yang và cộng sự}}
\begin{document}

{\setbeamertemplate{background}{\includegraphics[width=\paperwidth,height=\paperheight]{assets/hust/cover.png}}
\begin{frame}[plain]
\begin{tikzpicture}[remember picture,overlay]
  \node[anchor=north west,inner sep=0pt] at ([xshift=.58cm,yshift=-.55cm]current page.north west)
    {\includegraphics[width=3.4cm]{assets/hust/logo.png}};
  \node[anchor=north west,text width=9.6cm,align=left,inner sep=0pt,text=HustRed,
    font=\fontsize{18}{22}\selectfont\bfseries]
    at ([xshift=.65cm,yshift=-1.95cm]current page.north west)
    {HỌC LIÊN KẾT VÀ\\QUẢN LÝ TÀI NGUYÊN\\TRONG MẠNG IoT CÓ UAV};
  \node[anchor=north west,text width=9.3cm,align=left,inner sep=0pt,text=HustRed,
    font=\fontsize{10.5}{14}\selectfont]
    at ([xshift=.65cm,yshift=-4.55cm]current page.north west)
    {Federated Spatio-Temporal Policy Learning\\
     for Efficient Resource Management in\\
     UAV-Assisted IoT Edge Networks};
  \node[anchor=north west,text width=8.5cm,align=left,inner sep=0pt,font=\footnotesize]
    at ([xshift=.65cm,yshift=-6.35cm]current page.north west)
    {Bài báo của Xiaoteng Yang và cộng sự\\
     IEEE Internet of Things Journal, 2026 (bản tác giả)\\
     \footnotesize DOI: \href{https://doi.org/10.1109/JIOT.2026.3727888}{10.1109/JIOT.2026.3727888}};
\end{tikzpicture}
\end{frame}}
''']

def frame(title, body, source=None):
    # A leading braced group is otherwise consumed as Beamer's optional subtitle.
    text = '\n\\begin{frame}[t]{'+title+'}\n\\relax\n'+body.strip()+'\n'
    if source:
        text += '\\paperref{'+source+'}\n'
    text += '\\end{frame}\n'
    parts.append(text)

def symbols(rows):
    return (r'\par\medskip{\small\renewcommand{\arraystretch}{1.3}'
            r'\begin{tabularx}{\textwidth}{@{}p{2.45cm}Y@{}}'+'\n'+
            '\\\\[.12em]\n'.join(a+' & '+b for a,b in rows)+
            '\n'+r'\end{tabularx}}')

def equation(title, number, formula, rows, meaning, source, extra=''):
    body = r'\begin{equation}'+formula+r'\tag{'+str(number)+r'}\end{equation}'
    body += symbols(rows)+r'\eqmeaning{'+meaning+'}\n'+extra
    frame(title,body,source)

frame('NỘI DUNG',r'''
\vspace{.35cm}
\tableofcontents[hideallsubsections]
\vspace{.65cm}
\begin{itemize}
  \setlength{\itemsep}{.65em}
  \item Phần 1: khái niệm, cách hoạt động và ví dụ FL.
  \item Phần 2: mô hình hệ thống và đầy đủ công thức (1)--(15).
  \item Phần 3: sơ đồ FSTPO và các cơ chế chính.
\end{itemize}
''')

parts.append(r'''
\section{Giới thiệu về federated learning}
\hustpartpage{1}{FEDERATED LEARNING}{Khái niệm, quy trình và thách thức}
''')

frame('Federated learning là gì?',r'''
Nhiều thiết bị cùng học một mô hình, giữ dữ liệu huấn luyện tại chỗ.
\par\bigskip
\renewcommand{\arraystretch}{1.5}
\begin{tabularx}{\textwidth}{@{}lYY@{}}
\toprule
 & \textbf{Tập trung} & \textbf{Liên kết (FL)}\\
\midrule
Dữ liệu & Tập hợp tại máy chủ & Lưu ở thiết bị\\
Huấn luyện & Máy chủ thực hiện & Thiết bị thực hiện\\
Trao đổi & Dữ liệu gốc & Trọng số/gradient\\
\bottomrule
\end{tabularx}
\par\bigskip
\textbf{Client:} giữ dữ liệu, huấn luyện.\\
\textbf{Server:} điều phối, tổng hợp cập nhật.
\flref
''')

frame('Một vòng học liên kết',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=3cm] (server) at (5,3.4) {Máy chủ\\Mô hình chung $\mathbf w^{(r)}$};
\node[box,text width=2.1cm] (a) at (1.3,0) {Client 1\\Dữ liệu $\mathcal D_1$};
\node[box,text width=2.1cm] (b) at (5,0) {Client 2\\Dữ liệu $\mathcal D_2$};
\node[box,text width=2.1cm] (c) at (8.7,0) {Client 3\\Dữ liệu $\mathcal D_3$};
\draw[<->,>=Latex,HustRed,line width=.7pt] (server.west) -| node[lab,pos=.25,above]{1. Phát mô hình} (a.north);
\draw[<->,>=Latex,HustRed,line width=.7pt] (server.south) -- (b.north);
\draw[<->,>=Latex,Blue,line width=.7pt] (c.north) |- node[lab,pos=.75,above]{3. Gửi cập nhật} (server.east);
\node[lab] at (5,-1) {2. Huấn luyện cục bộ};
\node[lab] at (5,4.35) {4. Tổng hợp, bắt đầu vòng tiếp theo};
\end{tikzpicture}
\par\medskip
\raggedright Chỉ cập nhật mô hình đi qua mạng; dữ liệu gốc ở client.
\flref
''')

frame('FedAvg: ví dụ tổng hợp mô hình',r'''
Với tập client tham gia $\mathcal S_r$, một cách lấy trung bình có trọng số là
\[
\mathbf w^{(r+1)}=\sum_{m\in\mathcal S_r}
\frac{n_m}{\sum_{j\in\mathcal S_r}n_j}\,\mathbf w_m^{(r+1)}.
\]
\begin{itemize}
\item $n_m$: số mẫu của client $m$; $\mathbf w_m^{(r+1)}$: tham số sau học cục bộ.
\item Client có nhiều mẫu hơn có trọng số lớn hơn.
\end{itemize}
\par\medskip
\textbf{Ví dụ minh họa với một tham số vô hướng:}
\[
n_1=100,\ w_1=2;\qquad n_2=300,\ w_2=4.
\]
\[
w_{\text{mới}}=\tfrac{100}{400}\cdot2+\tfrac{300}{400}\cdot4=3.5.
\]
\source{McMahan và cộng sự, AISTATS 2017, FedAvg. Ví dụ số tự xây dựng, không phải kết quả paper UAV.}
''')

frame('Các dạng federated learning',r'''
\renewcommand{\arraystretch}{1.6}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{3.0cm}YY@{}}
\toprule
\textbf{Dạng} & \textbf{Mẫu dữ liệu} & \textbf{Đặc trưng}\\
\midrule
Horizontal FL & Khác nhau & Giống nhau\\
Vertical FL & Trùng nhau & Khác nhau\\
Federated transfer learning & Khác nhau & Khác nhau\\
\bottomrule
\end{tabularx}
\par\bigskip
Ví dụ horizontal FL: nhiều điện thoại học mô hình dự đoán từ.
\par\medskip
Ví dụ vertical FL: các tổ chức có thuộc tính bổ sung về cùng khách hàng.
\flref
''')

frame('Non-IID: dữ liệu mỗi thiết bị khác nhau',r'''
\textbf{Ví dụ minh họa:} ba thiết bị có tỷ lệ ba lớp khác nhau.
\par\bigskip
\centering
\begin{tikzpicture}[x=.09cm,y=.9cm]
\foreach \y/\name/\aa/\bb in {2/1/70/20,1/2/15/70,0/3/20/15}{
  \node[anchor=east,font=\small] at (-5,\y+.22) {Thiết bị \name};
  \fill[HustRed] (0,\y) rectangle (\aa,\y+.45);
  \fill[HustGold] (\aa,\y) rectangle (\aa+\bb,\y+.45);
  \fill[Blue] (\aa+\bb,\y) rectangle (100,\y+.45);
}
\node[anchor=west,font=\scriptsize,text=HustRed] at (0,-.7) {Lớp A};
\node[anchor=west,font=\scriptsize,text=HustGold!80!black] at (33,-.7) {Lớp B};
\node[anchor=west,font=\scriptsize,text=Blue] at (66,-.7) {Lớp C};
\end{tikzpicture}
\par\medskip\raggedright
\begin{itemize}
\item Mỗi client có thể học theo một hướng khác nhau.
\item Chọn lặp lại một nhóm thiết bị có thể làm mô hình thiếu đại diện.
\item Paper dùng độ lệch gradient để biểu diễn khác biệt dữ liệu.
\end{itemize}
\source{McMahan và cộng sự (2017); paper UAV, Sec. I--II-B. Biểu đồ là dữ liệu minh họa tự xây dựng.}
''')

frame('Lợi ích và thách thức',r'''
\begin{columns}[T,onlytextwidth]
\column{.47\textwidth}
\textcolor{HustRed}{\textbf{Lợi ích}}
\begin{itemize}
\item Hạn chế truyền dữ liệu nhạy cảm.
\item Học từ dữ liệu phân tán.
\item Có thể giảm tải truyền dữ liệu gốc.
\end{itemize}
\column{.49\textwidth}
\textcolor{HustRed}{\textbf{Thách thức}}
\begin{itemize}
\item Dữ liệu non-IID.
\item Phần cứng, kết nối khác nhau.
\item Chi phí trao đổi nhiều vòng.
\item Cập nhật có thể rò rỉ thông tin.
\end{itemize}
\end{columns}
\par\bigskip
Có thể bổ sung secure aggregation hoặc differential privacy.
\source{Google Cloud, What is federated learning?; McMahan và cộng sự (2017), Sec. 1, 5.}
''')

parts.append(r'''
\section{System model and problem formulation}
\hustpartpage{2}{SYSTEM MODEL\\AND PROBLEM FORMULATION}{Mô hình hệ thống và bài toán tối ưu tài nguyên}
\subsection{Kiến trúc mạng và biến quyết định}
''')

frame('Kiến trúc UAV hỗ trợ IoT',r'''
\begin{columns}[c,onlytextwidth]
\column{.55\textwidth}
\includegraphics[page=3,trim=47bp 587bp 309bp 55bp,clip,width=\linewidth]{\paperfile}
\par{\scriptsize Hình 1 của paper.}
\column{.42\textwidth}
\begin{itemize}
\item Thiết bị IoT học từ dữ liệu riêng.
\item UAV mang máy chủ MEC, phục vụ offloading và tổng hợp theo cụm.
\item Máy chủ mặt đất tổng hợp giữa các UAV qua backhaul riêng.
\end{itemize}
\end{columns}
\par\medskip
\textbf{Bối cảnh:} cứu hộ, giám sát vùng xa, triển khai tạm thời khi hạ tầng cố định hạn chế.
''','I-B, II-A--B, Hình 1')

frame('Tập hợp, thời gian và vị trí',r'''
\[
\mathcal U=\{1,\ldots,U\},\quad \mathcal M=\{1,\ldots,M\},\quad
\mathcal K=\{1,\ldots,K\}.
\]
\[
\mathbf q_u^k=[x_u^k,y_u^k,H_u]^T,\qquad
\mathbf p_m^k=[x_m^k,y_m^k,0]^T.
\]
'''+symbols([
(r'$u,m,k$',r'Chỉ số UAV, thiết bị và vòng giao tiếp.'),
(r'$\mathbf q_u^k,\mathbf p_m^k$',r'Vị trí 3D của UAV và thiết bị ở vòng $k$.'),
(r'$H_u$',r'Độ cao UAV $u$ so với mặt đất.')])+r'''
\eqmeaning{Di chuyển làm khoảng cách và chất lượng kênh thay đổi theo vòng.}
\noteonly{Quỹ đạo là đầu vào của mô hình; bài toán (15) tối ưu lịch chọn, băng thông và CPU thiết bị.}
''','II-A; các định nghĩa không đánh số')

frame('Ba nhóm biến quyết định',r'''
\renewcommand{\arraystretch}{1.65}
\begin{tabularx}{\textwidth}{@{}p{2cm}Y@{}}
\toprule
\textbf{Biến} & \textbf{Quyết định}\\
\midrule
$s_{m,u}^k\in\{0,1\}$ & Có chọn thiết bị $m$ kết nối và offload đến UAV $u$ hay không?\\
$b_{m,u}^k\geq0$ & Cấp bao nhiêu băng thông uplink cho kết nối đó?\\
$f_m^k$ & Thiết bị $m$ chạy CPU ở tần số nào khi huấn luyện?\\
\bottomrule
\end{tabularx}
\par\bigskip
$s_{m,u}^k=1$: thiết bị tham gia và có liên kết với UAV $u$.\\
$s_{m,u}^k=0$: không có liên kết phục vụ giữa cặp đó.
\par\medskip
\textbf{Tham số cho trước:} công suất phát $P_m$, năng lực CPU UAV $f_u$, ngân sách $B_{\max}$.
''','II-A, II-C--F')

frame('Hai luồng công việc tại thiết bị và UAV',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=2.45cm] (train) at (1.5,2.2) {Huấn luyện FL\\Dữ liệu riêng $\mathcal D_m$};
\node[box,text width=2.45cm] (task) at (1.5,0) {Tác vụ ứng dụng\\Suy luận, xử lý cảm biến};
\node[box,text width=2.5cm] (agg) at (7.6,2.2) {UAV tổng hợp\\Mô hình trong cụm};
\node[box,text width=2.5cm] (edge) at (7.6,0) {UAV tính toán MEC\\Thực thi tác vụ};
\draw[flow] (train)--node[lab,above]{Mô hình $\mathbf w_m^k$\\Kích thước $Z$}(agg);
\draw[dataflow] (task)--node[lab,above]{Dữ liệu tác vụ\\Kích thước $v_m^k$}(edge);
\end{tikzpicture}
\par\bigskip\raggedright
\begin{itemize}
\item Dữ liệu huấn luyện gốc giữ tại thiết bị.
\item Tác vụ offload độc lập với quá trình huấn luyện FL.
\item Hai luồng cùng tiêu thụ tài nguyên uplink và được điều khiển bởi $s_{m,u}^k$.
\end{itemize}
''','II-A, II-C')

parts.append(r'\subsection{Mô hình học liên kết}'+'\n')

equation('Hàm mất mát cục bộ',1,
r'L_m(\mathbf w)=\frac{1}{D_m}\sum_{i=1}^{D_m}\ell(\mathbf w;\mathbf x_{m,i},y_{m,i}),',[
(r'$\mathcal D_m,\ D_m$',r'Tập dữ liệu của thiết bị $m$ và số mẫu trong tập.'),
(r'$\mathbf x_{m,i},y_{m,i}$',r'Đặc trưng và nhãn của mẫu thứ $i$.'),
(r'$\mathbf w\in\mathbb R^d$',r'Vector gồm $d$ tham số của mô hình.'),
(r'$\ell(\cdot)$',r'Loss trên một mẫu; $L_m$ là loss trung bình tại thiết bị.')],
r'Đo mức sai lệch của mô hình trên dữ liệu riêng của thiết bị $m$. Giá trị nhỏ hơn thể hiện mô hình khớp dữ liệu cục bộ tốt hơn.','II-B, (1)')

equation('Hàm mất mát toàn cục',2,
r'F(\mathbf w)=\sum_{m\in\mathcal M}\frac{D_m}{D_{\tot}}L_m(\mathbf w),',[
(r'$D_{\tot}=\sum_m D_m$',r'Tổng số mẫu của toàn bộ thiết bị.'),
(r'$D_m/D_{\tot}$',r'Trọng số của thiết bị $m$ trong mục tiêu học.'),
(r'$F(\mathbf w)$',r'Loss trung bình có trọng số trên toàn bộ dữ liệu phân tán.')],
r'Liên kết các mục tiêu cục bộ thành một mục tiêu học chung. Thiết bị có nhiều mẫu đóng góp nhiều hơn vào loss toàn cục.','II-B, (2)',
r'\noteonly{Mẫu của thiết bị chưa được chọn ở một vòng vẫn thuộc tập dữ liệu định nghĩa mục tiêu toàn cục.}')

equation('Cập nhật mô hình tại thiết bị',3,
r'\mathbf w_m^{(k,i)}=\mathbf w_m^{(k,i-1)}-\eta\widehat\nabla L_m(\mathbf w_m^{(k,i-1)}),',[
(r'$i\in\{1,\ldots,I\}$',r'Bước cập nhật cục bộ; $I$ là số bước SGD.'),
(r'$\eta$',r'Tốc độ học.'),
(r'$\widehat\nabla L_m$',r'Gradient ngẫu nhiên ước lượng từ dữ liệu cục bộ.')],
r'Mỗi bước điều chỉnh tham số theo hướng làm giảm loss cục bộ. Chỉ thiết bị được chọn thực hiện huấn luyện.','II-B, (3)',
r'\[\mathbf w_m^{(k,0)}=\mathbf w^{k-1},\qquad \mathbf w_m^k=\mathbf w_m^{(k,I)}.\]')

equation('Tổng hợp mô hình toàn cục',4,
r'\mathbf w^k=\frac{\sum_{u\in\mathcal U}(\sum_{m\in\mathcal M}s_{m,u}^kD_m)\mathbf w_u^k}{\sum_{u\in\mathcal U}\sum_{m\in\mathcal M}s_{m,u}^kD_m},',[
(r'$\mathbf w_u^k$',r'Mô hình UAV $u$ tổng hợp từ các thiết bị trong cụm.'),
(r'$\sum_m s_{m,u}^kD_m$',r'Tổng số mẫu của các thiết bị được UAV $u$ chọn.'),
(r'$\mathbf w^k$',r'Mô hình chung sau tổng hợp giữa các UAV.')],
r'Trọng số của mỗi UAV phản ánh lượng dữ liệu đang tham gia. Mô hình mới được phân phối ở vòng kế tiếp.','II-B, (4)',
r'\noteonly{Giả sử có ít nhất một thiết bị tham gia để mẫu số khác 0.}')

frame('Sơ đồ tổng hợp hai cấp',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=3.2cm] (global) at (5,3.9) {Máy chủ trung tâm\\$\mathbf w^k$};
\node[box,text width=2.5cm] (u1) at (2,2) {UAV 1: $\mathbf w_1^k$};
\node[box,text width=2.5cm] (u2) at (8,2) {UAV 2: $\mathbf w_2^k$};
\node[faint] (m1) at (.7,0) {$\mathbf w_1^k$ tại MID 1};
\node[faint] (m2) at (3.3,0) {$\mathbf w_2^k$ tại MID 2};
\node[faint] (m3) at (6.7,0) {$\mathbf w_3^k$ tại MID 3};
\node[faint] (m4) at (9.3,0) {$\mathbf w_4^k$ tại MID 4};
\draw[flow] (m1.north)--(u1.south west);
\draw[flow] (m2.north)--(u1.south east);
\draw[flow] (m3.north)--(u2.south west);
\draw[flow] (m4.north)--(u2.south east);
\draw[flow] (u1.north)--node[lab,left]{Trọng số dữ liệu}(global.south west);
\draw[flow] (u2.north)--node[lab,right]{Trọng số dữ liệu}(global.south east);
\end{tikzpicture}
\par\bigskip\raggedright
\textbf{Cấp 1:} thiết bị gửi mô hình cho UAV phục vụ.\\
\textbf{Cấp 2:} máy chủ hợp nhất mô hình của các UAV theo (4).
\noteonly{Sơ đồ minh họa 2 UAV và 4 MID; số nút thực tế là $U$ và $M$.}
''','II-B, (4); sơ đồ vẽ lại')

equation('Độ lệch gradient do dữ liệu non-IID',5,
r'(\delta_m^{k-1})^2=\left\|\nabla L_m(\mathbf w^{k-1})-\nabla F(\mathbf w^{k-1})\right\|^2,',[
(r'$\nabla L_m$',r'Hướng gradient thật trên dữ liệu của thiết bị $m$.'),
(r'$\nabla F$',r'Hướng gradient thật của mục tiêu toàn cục.'),
(r'$\delta_m^{k-1}$',r'Độ lệch tính tại cùng mô hình $\mathbf w^{k-1}$.')],
r'Giá trị lớn biểu thị hướng học cục bộ khác nhiều so với hướng học chung; đây là tín hiệu về sự không đồng nhất dữ liệu.','II-B, (5)')

equation('Utility của hoạt động học liên kết',6,
r'\Upsilon_{\FL}^k=\sum_{u\in\mathcal U}\sum_{m\in\mathcal M}s_{m,u}^k\frac{D_m}{D_{\tot}}\exp[-\lambda(\delta_m^{k-1})^2],',[
(r'$s_{m,u}^k$',r'Chỉ thiết bị được chọn mới đóng góp utility ở vòng $k$.'),
(r'$D_m/D_{\tot}$',r'Phản ánh quy mô dữ liệu của thiết bị.'),
(r'$\lambda>0$',r'Điều chỉnh mức phạt độ lệch gradient.')],
r'Ưu tiên thiết bị có nhiều dữ liệu và gradient ít lệch khỏi hướng toàn cục, đồng thời vẫn phải xét chi phí phục vụ.','II-B, (6)',
r'\noteonly{$\Upsilon_{\FL}^k$ là đại lượng thay thế cho lợi ích học. Accuracy thực được kiểm tra riêng bằng $\Acc^K\geq\Acc_{\mathrm{target}}$.}')

parts.append(r'\subsection{Mô hình truyền thông}'+'\n')

frame('Khối lượng dữ liệu gửi uplink',r'''
\[
\Omega_m^k=\underbrace{Z}_{\text{mô hình nén}}
             +\underbrace{v_m^k}_{\text{tác vụ offload}}.
\]
'''+symbols([
(r'$Z$',r'Kích thước mô hình sau lượng tử hóa và làm thưa gradient.'),
(r'$v_m^k$',r'Kích thước dữ liệu tác vụ ứng dụng ở vòng $k$.'),
(r'$\Omega_m^k$',r'Tổng lượng dữ liệu thiết bị cần gửi lên UAV.')])+r'''
\eqmeaning{Uplink phải tải cả cập nhật FL và dữ liệu tác vụ. Hai thành phần cùng quyết định thời gian truyền và năng lượng phát.}
\noteonly{Quy trình nén được áp dụng thống nhất cho các thiết bị; không phải biến tối ưu trong (15). Khi tính tốc độ theo bit/s, đổi mọi kích thước về bit.}
''','II-C; công thức không đánh số')

equation('Khoảng cách thiết bị--UAV',7,
r'd_{m,u}^k=\sqrt{(x_u^k-x_m^k)^2+(y_u^k-y_m^k)^2+H_u^2},',[
(r'$x_u^k,y_u^k$',r'Tọa độ ngang của UAV.'),
(r'$x_m^k,y_m^k$',r'Tọa độ thiết bị mặt đất.'),
(r'$H_u$',r'Độ cao UAV; $d_{m,u}^k$ là khoảng cách 3D.')],
r'Khoảng cách kết hợp độ lệch ngang và độ cao; thiết bị càng xa UAV thì suy hao truyền dẫn càng lớn trong mô hình kế tiếp.','II-C, (7)')

frame('Hình học của liên kết không--mặt đất',r'''
\centering
\begin{tikzpicture}[x=1cm,y=.87cm]
\coordinate (m) at (0,0);\coordinate (g) at (7,0);\coordinate (u) at (7,4);
\draw[gray] (-.5,0)--(8.3,0);
\draw[very thick,HustRed] (m)--node[lab,above,sloped]{$d_{m,u}^k$}(u);
\draw[dashed,Blue] (u)--node[lab,right]{$H_u$}(g);
\draw[<->,Muted] (0,-.65)--node[lab,below]{Khoảng cách ngang}(7,-.65);
\draw (6.7,0)--(6.7,.3)--(7,.3);
\fill[HustRed] (m) circle(2pt);\fill[HustRed] (u) circle(2pt);
\node[anchor=east,font=\small] at (-.1,.2) {MID $m$};
\node[anchor=south,font=\small] at (7,4.2) {UAV $u$};
\end{tikzpicture}
\par\medskip\raggedright
Giữ nguyên độ cao, khi UAV dịch xa thiết bị theo phương ngang thì $d_{m,u}^k$ tăng và gain $h_{m,u}^k$ giảm.
''','II-A, II-C, (7)--(8); hình minh họa hình học')

equation('Gain kênh truyền quy mô lớn',8,
r'h_{m,u}^k=\frac{\beta_0}{(d_{m,u}^k)^2},',[
(r'$h_{m,u}^k$',r'Gain công suất kênh của liên kết thiết bị--UAV.'),
(r'$\beta_0$',r'Gain tại khoảng cách tham chiếu theo quy ước paper.'),
(r'$d_{m,u}^k$',r'Khoảng cách 3D từ (7).')],
r'Paper dùng mô hình suy hao không gian tự do cho liên kết có xác suất LoS cao. Gain giảm theo bình phương khoảng cách.','II-C, (8)',
r'\noteonly{Đây là gain quy mô lớn. Fading tức thời được đưa thêm vào mô hình độ tin cậy ở (12)--(13).}')

equation('Tốc độ truyền dữ liệu uplink',9,
r'R_{m,u}^k=b_{m,u}^k\log_2\!\left(1+\frac{P_mh_{m,u}^k}{N_0b_{m,u}^k}\right),',[
(r'$b_{m,u}^k$',r'Băng thông cấp cho thiết bị (Hz).'),
(r'$P_m$',r'Công suất phát của thiết bị (W).'),
(r'$N_0$',r'Mật độ phổ công suất nhiễu (W/Hz).'),
(r'$R_{m,u}^k$',r'Tốc độ truyền khả dụng (bit/s).')],
r'Tốc độ phụ thuộc đồng thời băng thông, công suất và khoảng cách thông qua gain kênh. Tốc độ lớn giúp truyền xong nhanh hơn.','II-C, (9)',
r'\noteonly{FDMA: mỗi UAV có quỹ $B_{\max}$ riêng, các quỹ không chồng lấn để loại nhiễu đồng kênh giữa UAV.}')

parts.append(r'\subsection{Mô hình độ trễ và năng lượng}'+'\n')

frame('Huấn luyện cục bộ: thời gian và năng lượng',r'''
\[
t_m^{\mathrm{comp},k}=\frac{ID_mc_m}{f_m^k},\qquad
E_m^{\mathrm{comp},k}=\kappa_m(f_m^k)^2(ID_mc_m).
\]
'''+symbols([
(r'$I,D_m$',r'Số bước học cục bộ và số mẫu dữ liệu.'),
(r'$c_m$',r'Hệ số chi phí CPU để xử lý dữ liệu.'),
(r'$f_m^k,\kappa_m$',r'Tần số CPU và hệ số điện dung hiệu dụng của thiết bị.')])+r'''
\eqmeaning{Tăng tần số CPU làm thời gian học giảm nhưng năng lượng tính toán tăng theo bình phương tần số.}
\noteonly{Giữ nguyên công thức paper. Paper định nghĩa $D_m$ theo số mẫu nhưng ghi $c_m$ là cycles/bit; cần quy đổi mẫu sang bit để nhất quán đơn vị khi tính số.}
''','II-D; các công thức không đánh số')

frame('Truyền uplink: thời gian và năng lượng',r'''
\[
\text{Thời gian uplink khi được chọn}=\frac{\Omega_m^k}{R_{m,u}^k},
\]
\[
E_{m,u}^{\mathrm{comm},k}=s_{m,u}^kP_m\frac{\Omega_m^k}{R_{m,u}^k}.
\]
'''+symbols([
(r'$\Omega_m^k$',r'Tổng kích thước mô hình và dữ liệu tác vụ.'),
(r'$R_{m,u}^k$',r'Tốc độ uplink từ (9).'),
(r'$s_{m,u}^k$',r'Kích hoạt chi phí truyền cho cặp được chọn.')])+r'''
\eqmeaning{Năng lượng phát bằng công suất nhân thời gian. Tác vụ lớn hoặc kênh chậm làm năng lượng truyền tăng.}
\noteonly{Tỷ số được đánh giá trên liên kết hoạt động, có tốc độ dương.}
''','II-D; các biểu thức không đánh số')

frame('Tính toán biên trên UAV',r'''
\[
t_{m,u}^{\mathrm{edge},k}=\frac{v_m^kc_u}{f_u},\qquad
E_{u,m}^{\mathrm{edge},k}=\kappa_u f_u^2(v_m^kc_u).
\]
'''+symbols([
(r'$v_m^k$',r'Kích thước tác vụ thiết bị $m$ offload lên UAV.'),
(r'$c_u$',r'Số chu kỳ CPU cần xử lý một bit tác vụ.'),
(r'$f_u$',r'Năng lực xử lý CPU đa lõi tổng hợp của UAV.'),
(r'$\kappa_u$',r'Hệ số điện dung hiệu dụng của CPU UAV.')])+r'''
\eqmeaning{UAV chịu thời gian và năng lượng để thực thi tác vụ được offload. Các chi phí này chỉ phát sinh khi $s_{m,u}^k=1$.}
\noteonly{Paper xem $f_u$ là tham số cho trước, còn $f_m^k$ của thiết bị là biến tối ưu.}
''','II-D; các công thức không đánh số')

frame('Thời gian một vòng giao tiếp',r'''
\textbf{Thời gian phục vụ một thiết bị:}
\[
t_{m,u}^k=t_m^{\mathrm{comp},k}+\frac{\Omega_m^k}{R_{m,u}^k}
                  +t_{m,u}^{\mathrm{edge},k}.
\]
\begin{equation}
T^k=\max_{m\in\mathcal M,u\in\mathcal U}
\left\{s_{m,u}^k\left(t_m^{\mathrm{comp},k}
+\frac{\Omega_m^k}{R_{m,u}^k}+t_{m,u}^{\mathrm{edge},k}\right)\right\}.
\tag{10}
\end{equation}
'''+symbols([
(r'$t_{m,u}^k$',r'Tổng thời gian học, truyền và xử lý biên của một cặp.'),
(r'$T^k$',r'Viết gọn $T^k=\max_{m,u}\{s_{m,u}^kt_{m,u}^k\}$; thời gian do thiết bị được chọn chậm nhất quyết định.')])+r'''
\eqmeaning{Đồng bộ theo vòng tạo hiệu ứng ``thiết bị chậm'': một liên kết hoặc CPU chậm có thể kéo dài cả vòng.}
''','II-D, (10) và định nghĩa không đánh số')

frame('Minh họa đồng bộ theo thiết bị chậm nhất',r'''
\centering
\begin{tikzpicture}[x=.92cm,y=1cm]
\node[anchor=east,font=\small] at (0,2.2) {MID 1};
\node[anchor=east,font=\small] at (0,.9) {MID 2};
\fill[HustRed!85] (.3,1.9) rectangle (2.2,2.5);
\fill[HustGold] (2.2,1.9) rectangle (4.7,2.5);
\fill[Blue!85] (4.7,1.9) rectangle (6,2.5);
\fill[HustRed!85] (.3,.6) rectangle (3.5,1.2);
\fill[HustGold] (3.5,.6) rectangle (6.6,1.2);
\fill[Blue!85] (6.6,.6) rectangle (8.4,1.2);
\draw[dashed,Muted] (8.4,.1)--(8.4,2.9);
\node[font=\small,anchor=south] at (8.4,2.9) {$T^k$};
\draw[flow] (.3,-.1)--(9.1,-.1) node[right,font=\scriptsize]{Thời gian};
\node[lab,text=HustRed] at (1.3,-.8) {Huấn luyện};
\node[lab,text=HustGold!85!black] at (4.6,-.8) {Uplink};
\node[lab,text=Blue] at (7.6,-.8) {MEC};
\end{tikzpicture}
\par\bigskip\raggedright
\textbf{Trong ví dụ:} MID 2 quyết định thời gian hoàn thành vòng. Tăng tài nguyên cho MID 1 chưa chắc giảm $T^k$.
\noteonly{Độ dài các đoạn chỉ minh họa định tính, không phải số liệu mô phỏng.}
''','II-D, (10); sơ đồ minh họa tự xây dựng')

frame('Tổng năng lượng hệ thống',r'''
\textbf{Năng lượng phục vụ một cặp thiết bị--UAV:}
\[
E_{m,u}^k=E_m^{\mathrm{comp},k}+E_{m,u}^{\mathrm{comm},k}
                          +E_{u,m}^{\mathrm{edge},k}.
\]
\begin{equation}
E_{\tot}^k=\sum_{u\in\mathcal U}\sum_{m\in\mathcal M}s_{m,u}^kE_{m,u}^k.
\tag{11}
\end{equation}
'''+symbols([
(r'$E_{m,u}^k$',r'Gộp năng lượng học tại thiết bị, uplink và MEC.'),
(r'$s_{m,u}^k$',r'Chỉ cộng năng lượng của các cặp đang được phục vụ.')])+r'''
\eqmeaning{Đánh giá chi phí năng lượng của toàn bộ các quyết định trong một vòng, gồm cả thiết bị và CPU UAV.}
\noteonly{Giữ nguyên công thức paper: $E^{\mathrm{comm},k}$ đã chứa $s$. Với $s\in\{0,1\}$, nhân thêm $s$ ở tổng không làm thay đổi kết quả. Năng lượng bay treo không được tính vì độc lập với các biến tối ưu.}
''','II-D, (11) và định nghĩa không đánh số')

parts.append(r'\subsection{Độ tin cậy và bài toán tối ưu}'+'\n')

equation('SNR tức thời',12,
r'\gamma_{m,u}^k=\frac{P_m\widetilde h_{m,u}^k}{N_0b_{m,u}^k},',[
(r'$\widetilde h_{m,u}^k$',r'Gain tức thời có fading, phân bố mũ với trung bình $h_{m,u}^k$.'),
(r'$P_m\widetilde h_{m,u}^k$',r'Công suất tín hiệu nhận.'),
(r'$N_0b_{m,u}^k$',r'Công suất nhiễu trong băng thông được cấp.')],
r'SNR so sánh tín hiệu với nhiễu. Dù vị trí và băng thông giữ nguyên, fading vẫn có thể làm SNR biến động.','II-E, (12)',
r'\noteonly{Giải mã thành công nếu $\gamma_{m,u}^k\geq\gamma_{\mathrm{th}}$; ngược lại xảy ra outage.}')

equation('Xác suất truyền thành công',13,
r'\Gamma_{m,u}^k=\Pr(\gamma_{m,u}^k\geq\gamma_{\mathrm{th}})=\exp\!\left(-\frac{\gamma_{\mathrm{th}}N_0b_{m,u}^k}{P_mh_{m,u}^k}\right),',[
(r'$\gamma_{\mathrm{th}}$',r'Ngưỡng SNR dùng để giải mã, ở thang tuyến tính trong công thức.'),
(r'$\Gamma_{m,u}^k$',r'Xác suất thành công, nằm trong $[0,1]$.'),
(r'$\Gamma_{\min}$',r'Ngưỡng xác suất thành công tối thiểu cần đạt.')],
r'Chuyển biến động kênh ngẫu nhiên thành một chỉ tiêu độ tin cậy để đưa vào ràng buộc tối ưu.','II-E, (13)',
r'\noteonly{Với công suất phát cố định, tăng $b$ cũng tăng nhiễu trong mô hình này. $\Gamma_{\min}$ là xác suất, không phải giá trị dB.}')

equation('Utility hệ thống trong một vòng',14,
r'U^k=\omega_1\Upsilon_{\FL}^k-\omega_2E_{\tot}^k-\omega_3T^k,',[
(r'$\omega_1>0$',r'Trọng số của lợi ích học FL.'),
(r'$\omega_2>0$',r'Mức phạt tiêu thụ năng lượng.'),
(r'$\omega_3>0$',r'Mức phạt thời gian hoàn thành vòng.')],
r'Chính sách tốt cần tạo lợi ích học cao với chi phí năng lượng và độ trễ phù hợp. Tăng một thành phần có thể làm xấu thành phần khác.','II-F, (14)',
r'\noteonly{Các trọng số được hiệu chỉnh để các đại lượng khác đơn vị có thang số so sánh phù hợp.}')

frame('Bài toán tối ưu chung',r'''
{\fontsize{9}{10.5}\selectfont\setlength{\jot}{0pt}
\begin{equation}
\begin{aligned}
\max_{s_{m,u}^k,b_{m,u}^k,f_m^k}\quad &\sum_{k=1}^{K}U^k\\[-.2em]
\mathrm{s.t.}\quad
\mathrm{(C1)}\;&s_{m,u}^k\in\{0,1\},&&\forall m,u,k,\\
\mathrm{(C2)}\;&\sum_{u\in\mathcal U}s_{m,u}^k\leq1,&&\forall m,k,\\
\mathrm{(C3)}\;&\sum_{m\in\mathcal M}s_{m,u}^kb_{m,u}^k\leq B_{\max},&&\forall u,k,\\
\mathrm{(C4)}\;&b_{m,u}^k\geq0,&&\forall m,u,k,\\
\mathrm{(C5)}\;&f_m^{\min}\leq f_m^k\leq f_m^{\max},&&\forall m,k,\\
\mathrm{(C6)}\;&s_{m,u}^kt_{m,u}^k\leq T_{\max},&&\forall m,u,k,\\
\mathrm{(C7)}\;&\Gamma_{m,u}^k\geq\Gamma_{\min},&&\forall m,u,k,\\
\mathrm{(C8)}\;&\Acc^K\geq\Acc_{\mathrm{target}}.
\end{aligned}\tag{15}
\end{equation}}
\eqmeaning{Tối đa tổng utility trong $K$ vòng bằng ba nhóm biến $s,b,f_m$, đồng thời đáp ứng giới hạn tài nguyên và chất lượng dịch vụ.}
''','II-F, (15)')

frame('Ý nghĩa các ràng buộc tài nguyên',r'''
\renewcommand{\arraystretch}{1.65}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{1.4cm}Y@{}}
\toprule
\textbf{Ràng buộc} & \textbf{Giải thích ngắn}\\
\midrule
(C1) & $s$ là quyết định nhị phân: chọn hoặc không chọn.\\
(C2) & Mỗi thiết bị có thể được tối đa một UAV phục vụ trong một vòng.\\
(C3) & Tổng băng thông của các thiết bị được chọn không vượt $B_{\max}$ của UAV.\\
(C4) & Băng thông không âm.\\
(C5) & CPU thiết bị hoạt động trong khoảng phần cứng $[f_m^{\min},f_m^{\max}]$.\\
\bottomrule
\end{tabularx}
\par\medskip
Các giới hạn này xác định quyết định nào có thể thực thi trên mạng.
''','II-F, (15), (C1)--(C5)')

frame('Ý nghĩa các ràng buộc chất lượng',r'''
\renewcommand{\arraystretch}{1.7}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{1.4cm}Y@{}}
\toprule
\textbf{Ràng buộc} & \textbf{Giải thích ngắn}\\
\midrule
(C6) & Thiết bị được chọn hoàn thành dịch vụ trong $T_{\max}$.\\
(C7) & Xác suất truyền thành công đạt ít nhất $\Gamma_{\min}$.\\
(C8) & Mô hình sau $K$ vòng đạt accuracy mục tiêu trên tập validation độc lập.\\
\bottomrule
\end{tabularx}
\par\bigskip
\textbf{Lưu ý khi đọc paper:}
\begin{itemize}
\item (C7) được viết cho mọi cặp $(m,u)$, không có $s$ đi kèm.
\item $\Acc^K$ là accuracy đo thực tế; khác với utility thay thế $\Upsilon_{\FL}^k$.
\end{itemize}
''','II-B, II-F, (15), (C6)--(C8)')

frame('Sự liên kết giữa các quyết định',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=2.1cm] (s) at (1.3,3) {Chọn thiết bị\\$s$};
\node[box,text width=2.1cm] (b) at (5,3) {Băng thông\\$b$};
\node[box,text width=2.1cm] (f) at (8.7,3) {CPU thiết bị\\$f_m$};
\node[faint,text width=2.1cm] (learn) at (1.3,.6) {Dữ liệu tham gia\\$\Upsilon_{\FL}^k$};
\node[faint,text width=2.1cm] (comm) at (5,.6) {Tốc độ, độ tin cậy\\$R,\Gamma$};
\node[faint,text width=2.1cm] (time) at (8.7,.6) {Thời gian, năng lượng\\$T,E$};
\draw[flow] (s)--(learn);\draw[flow] (b)--(comm);\draw[flow] (f)--(time);
\draw[dataflow] (comm)--(time);
\draw[dataflow] (s)--node[lab,above=6mm]{Chia sẻ tài nguyên}(b);
\end{tikzpicture}
\par\bigskip\raggedright
\begin{itemize}
\item Biến nhị phân và liên tục cùng xuất hiện, các quan hệ phi tuyến.
\item Lựa chọn ở vòng hiện tại ảnh hưởng mô hình ở những vòng sau.
\end{itemize}
\textbf{Kết quả:} bài toán MINLP động, dẫn tới cách tiếp cận học chính sách FSTPO.
''','II-F--III; sơ đồ diễn giải')

parts.append(r'''
\section{FSTPO framework}
\hustpartpage{3}{FSTPO FRAMEWORK}{Trực giác, sơ đồ và các công thức chính}
''')

frame('FSTPO: vòng ra quyết định',r'''
\textbf{Federated Spatio-Temporal Policy Optimization.} Mỗi UAV là một tác tử.
\par\bigskip\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=2.2cm] (obs) at (1.3,3) {Quan sát\\Kênh, dữ liệu};
\node[box,text width=2.3cm] (enc) at (5,3) {Bộ mã hóa\\Không gian--thời gian};
\node[box,text width=2.1cm] (actor) at (8.7,3) {Actor\\Chính sách};
\node[box,text width=2.2cm] (env) at (5,0) {Mạng UAV--IoT\\Thực thi $s,b,f_m$};
\node[faint,text width=2.1cm] (critic) at (1.3,0) {Critic\\Đánh giá dài hạn};
\draw[flow] (obs)--(enc);\draw[flow] (enc)--(actor);
\draw[flow] (actor.south)|-node[lab,near end,above]{Hành động}(env.east);
\draw[dataflow] (env)--node[lab,above]{Reward, cost}(critic);
\draw[dataflow] (env.north)--node[lab,right]{Trạng thái mới}(enc.south);
\end{tikzpicture}
\par\bigskip\raggedright
Actor chọn hành động. Critic đánh giá để cải thiện Actor trong giai đoạn huấn luyện.
''','III, III-B--D; sơ đồ đơn giản hóa Hình 2')

frame('Trạng thái và hành động của UAV',r'''
\begin{equation}
\mathbf s_u^k=(\mathbf H_u^{k-\tau:k},\mathbf D_u^k,
\boldsymbol\delta_u^{k-1},B_{\mathrm{rem}}^k).
\tag{21}
\end{equation}
'''+symbols([
(r'$\mathbf H_u^{k-\tau:k}$',r'Lịch sử kênh trong cửa sổ thời gian.'),
(r'$\mathbf D_u^k$',r'Khoảng cách đến các thiết bị.'),
(r'$\boldsymbol\delta_u^{k-1}$',r'Thông tin độ lệch gradient, phản ánh non-IID.'),
(r'$B_{\mathrm{rem}}^k$',r'Băng thông còn lại.')])+r'''
\eqmeaning{UAV quan sát cả điều kiện truyền thông và thông tin liên quan tới dữ liệu trước khi chọn $s,b,f_m$.}
\noteonly{$\mathbf s_u^k$ là vector trạng thái; $s_{m,u}^k$ là biến chọn thiết bị.}
''','III-B, (21)')

frame('Bộ mã hóa hai kênh',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[faint,text width=2.4cm] (phy) at (1.4,2) {Kênh vật lý\\Gain, khoảng cách};
\node[faint,text width=2.4cm] (fed) at (1.4,0) {Kênh dữ liệu\\Độ lệch gradient};
\node[box,text width=2.5cm] (gat) at (5.2,2) {Graph attention\\và LSTM};
\node[box,text width=2.5cm] (gcn) at (5.2,0) {Graph\\convolution};
\node[box,text width=1.5cm] (mix) at (9,1) {Cổng trộn\\$\mathbf g^k$};
\draw[flow] (phy)--(gat);\draw[flow] (fed)--(gcn);
\draw[flow] (gat.east)-|(mix.north);\draw[flow] (gcn.east)-|(mix.south);
\end{tikzpicture}
\begin{equation}
\mathbf E_u^k=\mathbf g^k\odot\mathbf h_{u,\mathrm{phy}}^k
+(1-\mathbf g^k)\odot\mathbf h_{u,\mathrm{fed}}^k.
\tag{20}
\end{equation}
\eqmeaning{Trộn đặc trưng vật lý và dữ liệu thành biểu diễn chung cho Actor--Critic. $\odot$ là phép nhân theo phần tử.}
''','III-A, (16)--(20), Thuật toán 1')

frame('Học hành động rời rạc và liên tục',r'''
\centering
\begin{tikzpicture}[x=1cm,y=1cm]
\node[box,text width=2.2cm] (actor) at (1.3,1.5) {Actor\\Từ đặc trưng $\mathbf E_u^k$};
\node[box,text width=2.8cm] (disc) at (6.2,2.9) {Gumbel--Softmax\\Chọn thiết bị $s$};
\node[box,text width=2.8cm] (cont) at (6.2,.1) {Phân bố Beta\\Băng thông $b$, CPU $f_m$};
\draw[flow] (actor.north)|-(disc.west);
\draw[flow] (actor.south)|-(cont.west);
\draw[dataflow] (disc)--node[lab,right]{Mask theo thiết bị được chọn}(cont);
\end{tikzpicture}
\par\bigskip\raggedright
\begin{itemize}
\item Khi học: làm mềm lựa chọn rời rạc để truyền gradient.
\item Khi suy luận: dùng argmax để lấy quyết định chọn cứng.
\item Mask gắn phân bổ tài nguyên với quyết định chọn thiết bị.
\end{itemize}
''','III-B, (22) và mô tả hành động liên tục')

frame('PPO có xử lý ràng buộc',r'''
\textbf{Reward:} dùng utility $U^k$ trong (14).\\
\textbf{Cost:} đo vi phạm độ trễ và độ tin cậy.
\begin{equation}
\widehat A_{\mathrm{total}}^k=\widehat A_r^k
-\lambda_1\widehat A_{c,1}^k-\lambda_2\widehat A_{c,2}^k.
\tag{27}
\end{equation}
\begin{itemize}
\setlength{\itemsep}{.5em}
\item $\widehat A_r$: hành động tốt hơn mức kỳ vọng về reward bao nhiêu.
\item $\widehat A_{c,i}$: mức bất lợi xét theo chi phí vi phạm.
\item $\lambda_i$: tăng mức phạt khi vi phạm vượt ngưỡng cho phép.
\end{itemize}
\eqmeaning{PPO cải thiện chính sách bằng cách cân đối lợi ích với vi phạm; cập nhật được giới hạn để tránh thay đổi quá mạnh.}
\noteonly{RL xử lý chi phí tích lũy kỳ vọng; cơ chế này không trực tiếp bảo đảm accuracy (C8) ở mọi lần chạy.}
''','III-C--D, (23)--(28)')

frame('Chia sẻ chính sách giữa các UAV',r'''
\[
a_u=\frac{\sum_m s_{m,u}^k}{\sum_{i\in\mathcal U}\sum_m s_{m,i}^k},
\qquad \theta_{\mathrm{glob}}=\sum_u a_u\theta_u.
\]
\[
\theta_u\leftarrow\tau\theta_{\mathrm{glob}}+(1-\tau)\theta_u.
\]
'''+symbols([
(r'$\theta_u$',r'Tham số Actor của UAV $u$.'),
(r'$a_u$',r'Trọng số theo số thiết bị đang được UAV phục vụ.'),
(r'$\tau$',r'Hệ số cập nhật mềm; chia sẻ mỗi $E_{\mathrm{share}}$ episode.')])+r'''
\eqmeaning{Các UAV học hỏi chính sách của nhau, đồng thời giữ một phần thích nghi cục bộ.}
\noteonly{Đổi ký hiệu trọng số từ $w_u$ trong paper thành $a_u$ trên slide để tránh nhầm với mô hình FL $\mathbf w_u^k$.}
''','III-D, Thuật toán 2; công thức chia sẻ chính sách')

frame('Hai mô hình và hai giai đoạn hoạt động',r'''
\renewcommand{\arraystretch}{1.45}
\begin{tabularx}{\textwidth}{@{}p{2.1cm}YY@{}}
\toprule
 & \textbf{Mô hình FL $\mathbf w$} & \textbf{Chính sách $\theta_u$}\\
\midrule
Mục đích & Học tác vụ từ dữ liệu thiết bị & Chọn lịch và phân bổ tài nguyên\\
Nơi học & Thiết bị IoT & Các tác tử UAV\\
Tổng hợp & Theo lượng dữ liệu & Theo số thiết bị phục vụ\\
\bottomrule
\end{tabularx}
\par\bigskip
\textbf{Offline:} huấn luyện FSTPO trong môi trường mô phỏng.\\[.45em]
\textbf{Online:} UAV chạy Actor đã học để đưa ra $s,b,f_m$ trong các vòng FL thực thi.
\par\medskip
\textbf{Điểm chính:} FSTPO học cách quản lý tài nguyên cho hoạt động FL và offloading.
''','II-B, III, III-D')

frame('Tài liệu tham khảo',r'''
\small
\begin{enumerate}
\setlength{\itemsep}{.8em}
\item Google Cloud. \emph{Federated learning: a guide to what it is and how it works}.\\
{\scriptsize\url{https://cloud.google.com/discover/what-is-federated-learning}}\\
Truy cập ngày 15/10/2026.
\item X. Yang, J. Feng, L. Ma, L. Liu, Q. Pei và C. Wu.\\
\emph{Federated Spatio-Temporal Policy Learning for Efficient Resource Management in UAV-Assisted IoT Edge Networks}.\\
IEEE Internet of Things Journal, bản tác giả được chấp nhận, 2026.\\
{\scriptsize\url{https://doi.org/10.1109/JIOT.2026.3727888}}
\item H. B. McMahan và cộng sự. \emph{Communication-Efficient Learning of Deep Networks from Decentralized Data}. AISTATS, 2017.\\
{\scriptsize\url{https://proceedings.mlr.press/v54/mcmahan17a.html}}
\end{enumerate}
''')

parts.append('\n\\end{document}\n')
Path('slides.tex').write_text(''.join(parts),encoding='utf-8')
print('Wrote slides.tex:', ''.join(parts).count(r'\begin{frame}'), 'literal frames plus 3 section dividers.')
