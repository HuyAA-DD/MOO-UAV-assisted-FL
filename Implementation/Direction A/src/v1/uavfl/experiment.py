"""Paired, cold-cache experiments; independent audit and locked execution choice."""
from pathlib import Path
from copy import deepcopy
import csv, gzip, hashlib, json, platform, sys, time, subprocess
import numpy as np
import torch
from .config import load_config
from .data import ensure_data, make_data
from .learning import Reference, initial_checkpoint, CNN, seed_for
from .physics import Scenario
from .operators import initialize, HistoricalGuide, HistoryReport
from .optimizers import run_optimizer
from .metrics import hypervolume3, nondominated_indices

def plain(value):
    if isinstance(value,np.ndarray):return plain(value.tolist())
    if isinstance(value,np.generic):return plain(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [plain(v) for v in value]
    return value

def write_json(path,value):
    Path(path).write_text(json.dumps(plain(value),ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")

def write_csv(path,rows):
    if not rows:return
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def source_hashes(root):
    files=sorted((root/"uavfl").glob("*.py"))+[root/"run.py"]
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def compare(root,output,cfg,seeds,rounds=1,download=False,algorithms=("nsga2","moead")):
    root=Path(root);output=Path(output)
    if (output/"summary.json").exists():
        raise FileExistsError("Output already contains a completed experiment; choose a new --output")
    output.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(cfg["fl"]["threads"])
    torch.use_deterministic_algorithms(True)
    data_root=ensure_data(root/"data"/"fashion-mnist",download)
    # Equal process warm-up; excludes one-off PyTorch optimizer import/kernel initialization.
    warm=CNN();opt=torch.optim.SGD(warm.parameters(),lr=0.01)
    opt.zero_grad();warm(torch.zeros(2,1,28,28)).sum().backward();opt.step()
    environment={"python":sys.version,"platform":platform.platform(),"processor":platform.processor(),
                 "torch":torch.__version__,"numpy":np.__version__,"torch_threads":torch.get_num_threads(),
                 "cuda":torch.cuda.is_available(),"device":"cpu","seeds":seeds,"rounds":rounds,
                 "source_sha256":source_hashes(root)}
    try:environment["git_head"]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    except (OSError,subprocess.CalledProcessError):environment["git_head"]=None
    write_json(output/"config.json",cfg);write_json(output/"environment.json",environment)
    rows=[];all_fronts=[];all_traces=[]
    for pair_index,seed in enumerate(seeds):
        data=make_data(data_root,cfg,seed,clients=len(cfg["network"]["client_positions"]))
        write_json(output/f"data_manifest_seed{seed}.json",data.manifest)
        checkpoint=initial_checkpoint(seed)
        order=list(algorithms)
        if pair_index%2:order.reverse()
        for algorithm in order:
            scenario=Scenario(cfg,len(checkpoint))
            current=checkpoint.clone();history={};total_E=total_T=0.0
            for round_id in range(rounds):
                print(f"START seed={seed} algorithm={algorithm} round={round_id}",flush=True)
                folder=output/f"seed{seed}"/algorithm/f"round{round_id}";folder.mkdir(parents=True,exist_ok=True)
                ref=Reference(data,current,cfg,seed,snapshot=str(round_id))
                guide=HistoricalGuide(data.weights,history,current.numpy(),scenario.clock,cfg["search"])
                initial=initialize(scenario,cfg["search"]["population"],seed_for(seed,"init",round_id))
                ev,stats=run_optimizer(algorithm,initial,scenario,ref,cfg["search"],
                    seed_for(seed,"evolution",round_id),guide)
                scales=np.asarray(cfg["search"]["scales"]);pref=np.asarray(cfg["search"]["preference"]);pref/=pref.sum()
                # The execution decision is locked BEFORE audit/test are queried.
                selected=min(ev.archive,key=lambda x:(float(np.dot(pref,x.objectives/scales)),
                             x.physical.duration,x.physical.energy,x.genome.key()))
                selected_id=selected.evaluation_id
                search_archive=[]
                for candidate in ev.archive:
                    search_archive.append({"id":candidate.evaluation_id,"selected":candidate.physical.selected,
                        "objectives":candidate.objectives,"assignment":candidate.genome.assignment,
                        "weights":candidate.genome.weights,"xi":candidate.genome.xi})
                write_json(folder/"search_archive.json",search_archive)
                audit_start=time.perf_counter();audit_rows=[]
                for candidate in ev.archive:
                    result=ref.loss(candidate.physical.selected,"audit")
                    audit_rows.append({"id":candidate.evaluation_id,"selected":candidate.physical.selected,
                        "search_objectives":candidate.objectives,
                        "objectives":[result["mean"],candidate.physical.energy,candidate.physical.duration],
                        "loss_replicates":result["replicates"]})
                audit_seconds=time.perf_counter()-audit_start
                audited_values=np.asarray([r["objectives"] for r in audit_rows])
                nd=nondominated_indices(audited_values)
                front=[audit_rows[i] for i in nd]
                hv=hypervolume3(audited_values/scales,cfg["search"]["hv_reference"])
                outside=int(np.sum(~np.all(audited_values/scales<cfg["search"]["hv_reference"],axis=1)))
                write_json(folder/"audit_pool.json",audit_rows);write_json(folder/"audit_archive.json",front)
                with gzip.open(folder/"candidates.jsonl.gz","wt",encoding="utf-8") as stream:
                    for record in ev.records:stream.write(json.dumps(plain(record),allow_nan=False)+"\n")
                write_csv(folder/"trace.csv",ev.trace)
                # One independent execution seed, never the average of SAA models.
                execute_seed=seed_for(seed,"physical-execution",round_id)
                new_model=ref.execute(selected.physical.selected,execute_seed)
                test=ref.measure(new_model,"test",metrics=True)
                report_seconds=time.perf_counter()
                for m in selected.physical.selected:
                    history[m]=HistoryReport(ref.report(m,execute_seed,scenario.n["sketch_dimension"]),
                        scenario.clock+selected.physical.phases["D0"]+selected.physical.phases["D"]+
                        scenario.n["report_cycles"]/selected.physical.frequency[m],current.numpy().copy())
                report_seconds=time.perf_counter()-report_seconds
                before_clock=scenario.clock;scenario.commit_costs(selected.physical)
                total_E+=selected.physical.energy;total_T+=selected.physical.duration
                chosen_record=deepcopy(ev.records[selected_id])
                chosen_record.update({"execution_seed":execute_seed,"test":test,
                                     "clock_before":before_clock,"clock_after":scenario.clock,
                                     "client_battery_after":scenario.client_battery,
                                     "uav_battery_after":scenario.uav_battery,
                                     "selection_locked_before_audit":True})
                write_json(folder/"selected.json",chosen_record)
                row={"seed":seed,"algorithm":algorithm,"round":round_id,
                    "audited_hv":hv,"search_hv":ev.trace[-1]["search_hv"],
                    "search_seconds":stats["search_seconds"],"cpu_seconds":stats["cpu_seconds"],
                    "overrun_seconds":stats["overrun_seconds"],"audit_seconds":audit_seconds,
                    "proposals":stats["proposals"],"unique_search_sets":stats["oracle"]["set_misses"],
                    "update_cache_misses":stats["oracle"]["update_misses"],
                    "loss_cache_hits":stats["oracle"]["set_hits"],
                    "search_oracle_seconds":stats["oracle"]["seconds"],
                    "unique_audit_sets":ref.stats["audit"]["set_misses"],
                    "feasible_candidates":sum(r["feasible"] for r in ev.records),
                    "search_archive_size":len(ev.archive),"audit_archive_size":len(front),"outside_hv_box":outside,
                    "selected_clients":len(selected.physical.selected),"selected_energy_J":selected.physical.energy,
                    "selected_time_s":selected.physical.duration,"cumulative_energy_J":total_E,"cumulative_time_s":total_T,
                    "test_loss":test["loss"],"test_accuracy":test["accuracy"],"test_macro_f1":test["macro_f1"],
                    "test_class9_recall":test["class9_recall"],"history_coverage":stats["history_coverage"],
                    "guided_attempts":stats["guided_attempts"],"guided_fallbacks":stats["guided_fallbacks"],
                    "report_simulation_seconds":report_seconds}
                rows.append(row)
                write_json(folder/"stats.json",row)
                for record in front:
                    all_fronts.append({"seed":seed,"algorithm":algorithm,"round":round_id,
                        "loss":record["objectives"][0],"energy":record["objectives"][1],"time":record["objectives"][2]})
                for trace in ev.trace:all_traces.append({"seed":seed,"algorithm":algorithm,"round":round_id,**trace})
                write_json(output/"summary.partial.json",rows)
                print(f"DONE seed={seed} {algorithm} HV={hv:.6f} proposals={stats['proposals']} sets={stats['oracle']['set_misses']} audit={audit_seconds:.2f}s",flush=True)
                current=new_model
    write_json(output/"summary.json",rows);write_csv(output/"summary.csv",rows)
    write_csv(output/"fronts.csv",all_fronts);write_csv(output/"traces.csv",all_traces)
    from .plots import make_plots
    make_plots(output,rows,all_fronts,all_traces)
    return rows
