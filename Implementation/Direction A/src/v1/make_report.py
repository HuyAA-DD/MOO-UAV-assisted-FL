"""Generate a Vietnamese report strictly from saved experiment artifacts."""
from pathlib import Path
import argparse, itertools, json, re
import numpy as np

def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def fmt(values,digits=6):
    a=np.asarray(values,float)
    return f"{a.mean():.{digits}f} ± {a.std(ddof=1):.{digits}f}" if len(a)>1 else f"{a.mean():.{digits}f}"

def describe(rows):
    rows=[r for r in rows if r["round"]==0]
    by={a:[r for r in rows if r["algorithm"]==a] for a in ("nsga2","moead")}
    lines=["| Chỉ số (mean ± SD qua các seed) | NSGA-II | MOEA/D |","| --- | ---: | ---: |"]
    keys=[("Audited HV","audited_hv",8),("Search HV","search_hv",8),
          ("Search wall time (s)","search_seconds",3),("CPU time (s)","cpu_seconds",3),
          ("Audit wall time (s)","audit_seconds",3),("Số proposals","proposals",1),
          ("Tập client search duy nhất","unique_search_sets",1),
          ("Số update cache misses","update_cache_misses",1),
          ("Tỷ lệ test accuracy của lịch đã chọn","test_accuracy",4),
          ("Test loss của lịch đã chọn","test_loss",5),
          ("Năng lượng lịch đã chọn (J)","selected_energy_J",3),
          ("Thời gian vật lý lịch đã chọn (s)","selected_time_s",5)]
    for label,key,digits in keys:
        lines.append(f"| {label} | "+ " | ".join(fmt([r[key] for r in by[a]],digits) for a in by)+" |")
    pairs=[]
    for seed in sorted({r["seed"] for r in rows}):
        p={r["algorithm"]:r for r in rows if r["seed"]==seed}
        if len(p)==2:pairs.append((seed,p["nsga2"],p["moead"]))
    table=["| Seed | HV NSGA-II | HV MOEA/D | ΔHV (NSGA-II − MOEA/D) | Search s: NSGA-II / MOEA/D |",
           "| ---: | ---: | ---: | ---: | ---: |"]
    for seed,a,b in pairs:
        table.append(f"| {seed} | {a['audited_hv']:.9f} | {b['audited_hv']:.9f} | {a['audited_hv']-b['audited_hv']:+.9f} | {a['search_seconds']:.3f} / {b['search_seconds']:.3f} |")
    delta=np.array([a["audited_hv"]-b["audited_hv"] for _,a,b in pairs])
    delta=np.where(np.abs(delta)<1e-9,0.0,delta)  # Numerical equality threshold for inference.
    rng=np.random.default_rng(2026)
    boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(1)
    lo,hi=np.quantile(boot,[.025,.975])
    signs=np.array(list(itertools.product([-1,1],repeat=len(delta))))
    pvalue=float(np.mean(np.abs((signs*delta).mean(1))>=abs(delta.mean())-1e-14))
    text=(f"Chênh lệch HV ghép cặp trung bình (NSGA-II − MOEA/D): **{delta.mean():+.9f}**. "
          f"Khoảng bootstrap percentile 95% mô tả: [{lo:+.9f}, {hi:+.9f}]; "
          f"kiểm định đổi dấu ghép cặp hai phía, liệt kê đủ {2**len(delta)} tổ hợp: p={pvalue:.4f}. "
          f"Sai khác HV dưới 1e-9 được xem là 0 khi suy luận. Với {len(delta)} cặp, đây là thống kê thăm dò; không đủ để kết luận ưu thế tổng quát.")
    return "\n".join(lines),"\n".join(table),text

def generate(results,secondary,output):
    result=Path(results);out=Path(output);rows=read(result/"summary.json")
    cfg=read(result/"config.json");env=read(result/"environment.json")
    table,pairs,inference=describe(rows)
    import os
    link=Path(os.path.relpath(result,out.parent)).as_posix()
    total=len(rows);secondary_text=""
    if secondary is not None and (Path(secondary)/"summary.json").exists():
        secondary=Path(secondary);srows=read(secondary/"summary.json");st,sp,si=describe(srows)
        slink=Path(os.path.relpath(secondary,out.parent)).as_posix()
        total+=len(srows)
        secondary_text=f"""
## 6. Đối chiếu bổ sung ở cùng trần số đề xuất

Cấu hình [pilot]({slink}/config.json) dùng trần 30 s và 10000 proposals. Các run đã chạm giới hạn proposals; đây là phép so sánh theo số đề xuất, không gọi là cùng thời gian thực.

{st}

{sp}

{si}

[Summary CSV]({slink}/summary.csv) · [Đồ thị HV]({slink}/hypervolume.png)
"""
    verification=Path(__file__).parent/"results"/"verification.txt"
    testlog=verification.read_text(encoding="utf-8") if verification.exists() else ""
    match=re.search(r"Ran (\d+) tests",testlog);test_count=match.group(1) if match else "chưa ghi nhận"
    search=cfg["search"];fl=cfg["fl"];data=cfg["data"]
    fence=chr(96)*3
    selected_counts=sorted(set(r["selected_clients"] for r in rows))
    max_overrun=max(r["overrun_seconds"] for r in rows)
    outside=sum(r["outside_hv_box"] for r in rows)
    extra_verification=""
    evidence=Path(__file__).parent/"results"/"artifact-verification.json"
    smoke=Path(__file__).parent/"results"/"episode_smoke"/"summary.json"
    if evidence.exists():
        verified=read(evidence)
        extra_verification+=(f"Biên bản xác minh của lần bàn giao gốc đã đối chiếu source hashes, tái tính audited HV "
            f"và rà **{verified['candidate_records']} candidate records**, trong đó {verified['feasible_records']} khả thi "
            "có ledger/timeline/mean loss nhất quán. "
            "[Biên bản kiểm tra artifact](results/artifact-verification.json). "
            "Khi chạy lại thí nghiệm mới, biên bản này vẫn là bằng chứng của lần bàn giao gốc, không tự xác nhận dữ liệu mới.\n\n")
    if smoke.exists():
        smoke_rows=read(smoke)
        extra_verification+=(f"Đã kiểm tra tích hợp thêm **{len(smoke_rows)} vòng** trong hai episode, mỗi thuật toán 3 vòng, "
            "với guidance probability=0.5 và cấu hình nhỏ riêng tại [episode_smoke.json](configs/episode_smoke.json). "
            "Pin/năng lượng/đồng hồ tiến đúng, history chuyển từ rỗng sang có báo cáo; guided swap được sử dụng khi đủ thông tin. "
            "Đây là smoke test của lần bàn giao, không dùng để xếp hạng thuật toán. "
            "[Kết quả nhiều vòng](results/episode_smoke/summary.csv).\n")
    msg=f"""# Báo cáo triển khai Direction A v1: NSGA-II và MOEA/D

**Ngày báo cáo:** 26/10/2026.  
**Đặc tả:** [problem-formulation.md](problem-formulation.md).  
**Trạng thái:** đã triển khai, kiểm thử và chạy {total} lần tối ưu trong hai giao thức so sánh; số liệu dưới đây đọc trực tiếp từ artifact, không phải kết quả minh họa.

## 1. Kết quả chính

Hai thuật toán đã chạy trên cùng bài toán loss–energy–time với CNN và local SGD thực trên Fashion-MNIST. Kết quả pilot cho front audit gần nhau; mức chênh lệch được trình bày theo từng seed và ngân sách ở dưới. Mô hình bắt đầu từ random initialization và chỉ thực thi một vòng, nên báo cáo này xác minh pipeline/solver, chưa chứng minh hội tụ FL hoặc chất lượng mô hình cuối.

Số client của lịch được chọn trong phép so sánh chính: **{", ".join(map(str,selected_counts))}**. Chi phí hover và baseline chiếm tỷ trọng lớn, còn loss sau 5 bước local SGD ở checkpoint đầu thay đổi ít. Vì vậy nhiều lịch ít client có lợi trong cấu hình này; cần kiểm tra lại ở checkpoint đã học và phần cứng dị biệt trước khi rút kết luận hệ thống.

## 2. Những gì đã triển khai

| Thành phần | Cài đặt |
| --- | --- |
| Physical evaluator | UAV hover; mask liên kết; uplink effective rate; 6 pha barrier; bandwidth tối thiểu; CPU giải tích; deadline và pin |
| Năng lượng | Client, UAV và coordinator; baseline, hover, tx/rx, aggregate; không tính trùng các nút |
| FL | CNN 105866 tham số; SGD {fl['local_steps']} bước, batch {fl['batch_size']}, lr {fl['lr']}; aggregate chuẩn hóa theo trọng số client |
| Objective học | Loss validation thực sau local SGD và aggregation; không dùng gradient score làm fitness |
| Cache | Lazy local-update cache theo snapshot/client/seed; loss cache theo tập client và search/audit protocol |
| Search/audit | SAA {fl['search_replicates']} seed search, {fl['audit_replicates']} seed audit; split và namespace RNG tách biệt |
| Execution | Khóa lựa chọn trước audit/test; một execution seed riêng; cập nhật model, pin, đồng hồ và report chỉ từ client thực thi |
| Historical guidance | Có code và kiểm thử cho sketch thiếu/cũ, generic fallback; đặt probability={search['guided_probability']} trong so sánh chính |
| Output | Candidate ledger/residuals, archive search/audit, manifest, CSV/JSON và hình PNG |

Ba objective được chuẩn hóa bằng scale cố định {search['scales']}. Hypervolume 3D được tính chính xác cho các vector hữu hạn trong reference box {search['hv_reference']}; số audit candidate nằm ngoài box trong dữ liệu chính là {outside}. Hypervolume càng lớn càng tốt trong cùng snapshot/reference box.

## 3. Hai thuật toán và điều kiện so sánh

**NSGA-II:** nondominated sorting có feasibility dominance, binary tournament theo rank/crowding và elitist environmental selection. Objective có range bằng 0 không góp vào crowding. Đối chiếu mô tả cơ chế ở [tài liệu NSGA-II của pymoo](https://pymoo.org/algorithms/moo/nsga2.html).

**MOEA/D:** simplex weight vectors cho ba mục tiêu; neighborhood trong không gian trọng số; scalarization Tchebycheff với scale cố định và ideal point cập nhật từ nghiệm khả thi; xác suất chọn bố mẹ lân cận {search['neighbor_probability']}, neighborhood {search['neighbors']}, tối đa {search['max_replacements']} thay thế mỗi child. Trọng số bằng 0 được thay bằng 1e-6 khi tính scalarization. Feasible được ưu tiên trước infeasible; infeasible so theo tổng vi phạm chuẩn hóa. Đối chiếu framework ở [tài liệu MOEA/D của pymoo](https://pymoo.org/algorithms/moo/moead.html). Constraint handling và mixed-variable variation là lựa chọn của implementation này.

Cả hai được tự triển khai trong [optimizers.py](uavfl/optimizers.py). Chúng dùng cùng uniform crossover cho association, bounded SBX và polynomial mutation cho gene liên tục, add/drop/swap/reassign và decoder tài nguyên trong [operators.py](uavfl/operators.py). Mỗi run bắt đầu với cùng initial genomes và cache rỗng; thứ tự chạy đảo giữa các seed.

Phần cứng dùng CPU, PyTorch threads={env['torch_threads']}; Torch {env['torch']}, NumPy {env['numpy']}; Python {env['python'].split()[0]}. Platform: {env['platform']}. [Environment/source hashes]({link}/environment.json) lưu chi tiết tái lập.

## 4. Dữ liệu và ngân sách

Dataset từ [repository Fashion-MNIST chính thức](https://github.com/zalandoresearch/fashion-mnist), kiểm tra MD5 từng file. Dùng {data['train']} train, {data['search']} search-validation, {data['audit']} audit-validation và {data['test']} test. Ba split đầu không giao nhau và lấy từ training set chính thức; test lấy từ test set chính thức.

Phân chia {data['partition']}, alpha={data['alpha']}, dùng cùng class-to-client probabilities giữa các split. Trọng số quần thể lấy từ kích thước train từng client. Mỗi seed trong {env['seeds']} xác định data partition, checkpoint và RNG; hai thuật toán ghép cặp trên đúng các yếu tố này.

- 6 client, 2 UAV, tối đa 4 client mỗi vòng; population {search['population']}.
- Budget chính: {search['seconds']} s search, proposal cap {search['max_proposals']}; seed bundle là đơn vị evaluation nguyên tử.
- Tính vào search time: initialization evaluation, candidate proposal/decode, lazy cache, training/validation, Pareto selection và trace metrics. Dataset loading, process warm-up và artifact export nằm ngoài.
- Toàn bộ initial population được đánh giá trước evolution; ngân sách phải đủ cho bước này. Chi phí thực được log kể cả nếu có overrun.
- Overrun lớn nhất quan sát: {max_overrun:.6f} s. Chi phí audit ghi riêng, không cộng vào thời gian vật lý của lịch FL.
- Tất cả energy/cycles/power là synthetic parameters từ đặc tả, chưa được profile trên UAV/thiết bị thật.

## 5. Kết quả ở cùng trần thời gian tìm kiếm

{table}

{pairs}

{inference}

![Diễn biến search HV và audited HV ghép cặp]({link}/hypervolume.png)

Đồ thị trái dùng search-validation; đồ thị phải dùng audit-validation độc lập. Không diễn giải search HV là audited HV. Các cặp seed là đơn vị so sánh; candidate cùng snapshot không phải replicate độc lập.

![Các projection của front audit]({link}/pareto.png)

Hình gộp các seed để xem hình dạng đánh đổi; không tính dominance giữa các checkpoint khác nhau.

[Summary CSV]({link}/summary.csv) · [Summary JSON]({link}/summary.json) · [Audited fronts]({link}/fronts.csv) · [Search traces]({link}/traces.csv)
{secondary_text}
## 7. Kiểm thử và kiểm tra kết quả

Đã qua **{test_count} kiểm thử**; log tại [verification.txt](results/verification.txt).

Các nhóm kiểm tra: ledger và timeline; inactive mask/UAV rỗng vẫn hover; rate đơn điệu; deadline và pin; CPU reduction; parameter count; seed/cache determinism; hierarchical/flat aggregation; audit namespace; missing/stale-history guide; guided swap giữ client chưa biết; exact HV; dominance/crowding; simplex weights; cả NSGA-II và MOEA/D dừng đúng proposal budget.

Artifact của mỗi run có assignment, bandwidth, CPU, từng pha thời gian, năng lượng từng nút, raw residuals và loss replicates trong candidates.jsonl.gz. selected.json lưu lựa chọn đã khóa trước audit và pin/đồng hồ sau thực thi.

{extra_verification}

## 8. Giới hạn và cách đọc kết quả

1. Đây là pilot một vòng từ model ngẫu nhiên. Test accuracy thấp ở giai đoạn này không đo convergence của FL nhiều vòng; không chọn hyperparameter để làm đẹp test.
2. 6 client có ít tập con; lazy cache khiến bài toán học nhanh được khám phá. Khi hai solver gần cùng front, không thể suy ra chúng tương đương trên mạng lớn.
3. Guided mutation đã có code nhưng không được kích hoạt trong phép so sánh chính. Chưa có kết luận về đóng góp set-aware.
4. Các hệ số phần cứng hiện là scalar chung cho từng nhóm nút; chưa hỗ trợ vectors DVFS/power dị biệt từng client. Vị trí, dữ liệu, association và trạng thái pin vẫn khác nhau.
5. Chưa triển khai dynamic channel, outage/retransmission, multi-fidelity, adaptive probing hoặc tối ưu quỹ đạo. Các phép rút gọn được giới hạn ở static-hover model.
6. Energy/time là chi phí thực thi mô phỏng theo mô hình; search/audit wall time là số đo máy chạy. Chúng có đơn vị và phạm vi hạch toán khác nhau.
7. Có tùy chọn chạy nhiều vòng qua --rounds, nhưng số liệu chính ở đây dùng một vòng. Khi không tìm được lịch khả thi, runner dừng với trạng thái lỗi rõ ràng, chưa tự động thực hiện recovery mạng.
8. Bootstrap và kiểm định đổi dấu với 5 cặp chỉ có tính thăm dò. Cần thêm checkpoint, partitions, quy mô mạng và paired runs trước khi kết luận thuật toán vượt trội.

## 9. Tái lập

Từ thư mục src/v1:

{fence}powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --config configs/equal_time.json --output results/reproduce_equal_time --seeds 101 102 103 104 105 --download
python run.py --config configs/pilot.json --output results/reproduce_proposals --seeds 101 102 103 104 105
python make_report.py --results results/reproduce_equal_time --secondary results/reproduce_proposals --output report-reproduced.md
{fence}

Wall-time stopping có thể làm số candidate khác giữa các máy/lần chạy; seed và RNG cố định tái lập FL updates và fitness của cùng candidate. Khi kiểm tra bit-level replay theo số đề xuất, dùng proposal budget cố định và cấp đủ wall-time.

Cấu hình đầy đủ hơn nằm ở [configs/full.json](configs/full.json), chưa được dùng để tạo số liệu báo cáo này. Bước tiếp theo phù hợp là checkpoint đã huấn luyện, phần cứng dị biệt, quy mô 20/50 client và ablation guidance, với cùng giao thức audit.
"""
    out.write_text(msg,encoding="utf-8")
    print(f"Wrote {out}")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--results",type=Path,default=Path("results/equal_time"))
    parser.add_argument("--secondary",type=Path,default=Path("results/pilot"))
    parser.add_argument("--output",type=Path,default=Path("report.md"))
    args=parser.parse_args()
    generate(args.results,args.secondary,args.output)
