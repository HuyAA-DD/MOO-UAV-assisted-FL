# Direction A / v1

Implementation của mô hình A-REF trong [problem-formulation.md](problem-formulation.md), với hai thuật toán NSGA-II và MOEA/D để so sánh.

## Chạy

Yêu cầu Python 3.10+ và các thư viện trong requirements.txt. Chạy lệnh từ thư mục này:

    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python run.py --config configs/pilot.json --output results/my_run --download

Fashion-MNIST được tải từ repository chính thức của Zalando, kiểm tra MD5 rồi lưu trong data/fashion-mnist. Không cần torchvision hoặc pymoo. Nếu đã có dataset thì bỏ --download. Runner không ghi đè thư mục đã có summary.json.

Chạy riêng, đổi budget hoặc chạy nhiều vòng:

    python run.py --config configs/pilot.json --algorithms nsga2 --seeds 101 --seconds 30 --output results/nsga_example
    python run.py --config configs/pilot.json --rounds 3 --seeds 101 --output results/episode_example
    python run.py --config configs/full.json --output results/full --download
    python run.py --config configs/equal_time.json --output results/equal_time --download
    python make_report.py --results results/equal_time --secondary results/pilot --output report.md

Full config dùng 48000/6000/6000/10000 mẫu train/search/audit/test, population 64 và trần 300 giây mỗi lần search. Đây là cấu hình chạy tiếp; số liệu bàn giao nằm trong results/equal_time (cùng trần 15 giây) và results/pilot (10000 proposals).

## Thành phần

- uavfl/config.py: tham số, validation và cấu hình chung.
- uavfl/physics.py: static-hover network, sáu pha, CPU decoder, năng lượng từng nút và constraints.
- uavfl/data.py: Fashion-MNIST, bốn split độc lập và phân chia non-IID.
- uavfl/learning.py: CNN 105866 tham số, local SGD, aggregation, lazy cache và audit riêng.
- uavfl/operators.py: initialization, uniform association crossover, bounded SBX, polynomial mutation, generic mutation và historical guided swap tùy chọn.
- uavfl/optimizers.py: constrained NSGA-II; MOEA/D với Tchebycheff, neighborhoods và giới hạn thay thế.
- uavfl/metrics.py: Pareto archive và exact 3D hypervolume.
- uavfl/experiment.py: thí nghiệm ghép cặp, lựa chọn trước audit, thực thi một lịch và cập nhật trạng thái.
- tests/test_core.py: kiểm thử toán học, FL, cache và hai optimizer.
- report.md: cấu hình, kết quả đã chạy, giới hạn và lệnh tái lập.

## Giao thức so sánh

Hai thuật toán dùng cùng checkpoint, data partition, initial genomes, local-SGD seed bundle, mô hình tài nguyên và variation operators. Mỗi run có cache riêng bắt đầu rỗng. Thứ tự chạy thuật toán được đảo giữa các seed để giảm ảnh hưởng thứ tự.

Pilot: 6 client, 2 UAV, tối đa 4 client/vòng; 6000/600/600/1000 mẫu train/search/audit/test; Dirichlet alpha=0.5; 5 bước SGD; 3 search replicates và 10 audit replicates. Dừng khi chạm trần 30 giây hoặc 10000 proposals, tùy điều kiện nào đến trước. Toàn bộ population khởi tạo được đánh giá trước vòng tiến hóa; cần cấp đủ thời gian cho bước này. Thời gian thực và mọi overrun được lưu.

Audit dùng split và RNG khác search. Lịch được chọn từ search archive theo trọng số cố định trước khi audit/test được mở. Một execution seed độc lập tạo model thực của vòng; không lấy trung bình model từ các seed SAA.

Guided probability bằng 0 trong so sánh chính để cô lập optimizer. Có thể bật trong JSON cấu hình và chạy nhiều vòng; sketch chỉ được tạo từ client đã thực thi, không lấy từ counterfactual oracle cache. Các bài toán tối ưu vẫn là offline oracle-assisted.

## Kết quả đầu ra

- config.json, environment.json, data_manifest_seed*.json: cấu hình, version, source hashes và nguồn dữ liệu.
- summary.csv/json: các số liệu chính theo seed, thuật toán và vòng.
- fronts.csv, traces.csv, pareto.png, hypervolume.png: front audit và diễn biến search.
- seed*/algorithm/round*/candidates.jsonl.gz: tất cả candidate, ledger, constraints và objective.
- search_archive.json, audit_pool.json, audit_archive.json: ba giai đoạn archive.
- selected.json: quyết định đã khóa, test metrics và pin/đồng hồ sau thực thi.

Một resource variant cùng tập client dùng lại loss nhưng vẫn tính lại vật lý. Chỉ candidate khả thi được gọi oracle. Chi phí audit và tìm kiếm offline không cộng vào năng lượng/thời gian vật lý của lịch.

## Phạm vi v1

Đã triển khai static hover, effective rate không mất gói, fixed local work và CPU liên tục. Các hệ số phần cứng trong cấu hình v1 là scalar chung cho nhóm client/UAV; vị trí, liên kết, tập dữ liệu và pin trạng thái khác nhau. Chưa có per-node hardware parameter vectors, dynamic-channel simulator, multi-fidelity hoặc adaptive probing.

Cycles và power là tham số synthetic theo đặc tả, chưa phải số đo phần cứng. CNN/Fashion-MNIST/local SGD là thật. Pilot một vòng từ random initialization kiểm tra pipeline và solver; không chứng minh hội tụ FL hoặc tính mới của phương pháp.

Nếu không tìm thấy lịch khả thi, runner báo NO_FEASIBLE_SCHEDULE_FOUND và dừng; không tạo kết quả thành công giả. Việc sinh lại scenario hoặc recovery trong mạng thực chưa được tự động hóa.
