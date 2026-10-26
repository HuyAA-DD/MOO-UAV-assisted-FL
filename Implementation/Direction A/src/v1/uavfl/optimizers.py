"""From-scratch constrained NSGA-II and MOEA/D with common variation/evaluation."""
from dataclasses import dataclass
from copy import deepcopy
import time
import numpy as np
from .metrics import dominates, archive_insert, hypervolume3
from .operators import offspring

@dataclass
class Candidate:
    genome: object
    physical: object
    objectives: np.ndarray
    evaluation_id: int
    losses: tuple

def constrained_dominates(a,b):
    if a.physical.feasible != b.physical.feasible:return a.physical.feasible
    if not a.physical.feasible:return a.physical.cv < b.physical.cv
    return dominates(a.objectives,b.objectives)

def fronts(pop):
    count=np.zeros(len(pop),int);beaten=[[] for _ in pop]
    for i in range(len(pop)):
        for j in range(i):
            if constrained_dominates(pop[i],pop[j]):beaten[i].append(j);count[j]+=1
            elif constrained_dominates(pop[j],pop[i]):beaten[j].append(i);count[i]+=1
    current=list(np.flatnonzero(count==0));result=[]
    while current:
        result.append(current);next_front=[]
        for i in current:
            for j in beaten[i]:
                count[j]-=1
                if count[j]==0:next_front.append(j)
        current=next_front
    return result

def crowding(pop,indexes):
    distance={i:0.0 for i in indexes}
    if not indexes:return distance
    # Infeasible individuals never use null/infinite learning fitness for crowding.
    if not pop[indexes[0]].physical.feasible:return distance
    y=np.array([pop[i].objectives for i in indexes])
    for j in range(3):
        order=np.argsort(y[:,j],kind="stable")
        width=y[order[-1],j]-y[order[0],j]
        if width<=0:continue
        distance[indexes[order[0]]]=float("inf")
        distance[indexes[order[-1]]]=float("inf")
        for k in range(1,len(order)-1):
            distance[indexes[order[k]]]+=(y[order[k+1],j]-y[order[k-1],j])/width
    return distance

def select_nsga(pop,size):
    selected=[]
    for front in fronts(pop):
        if len(selected)+len(front)<=size:selected.extend(front)
        else:
            cd=crowding(pop,front)
            selected.extend(sorted(front,key=lambda i:(-cd[i],pop[i].evaluation_id))[:size-len(selected)])
            break
    return [pop[i] for i in selected]

def rank_crowding(pop):
    ranks={};dist={}
    for rank,front in enumerate(fronts(pop)):
        ranks.update({i:rank for i in front});dist.update(crowding(pop,front))
    return ranks,dist

def weight_vectors(size):
    h=1
    while (h+1)*(h+2)//2<size:h+=1
    w=np.array([[i/h,j/h,(h-i-j)/h] for i in range(h+1) for j in range(h+1-i)])
    if len(w)==size:return w
    # Deterministic farthest-point subsampling retains all three vertices.
    chosen=[int(np.argmax(w[:,j])) for j in range(3)]
    while len(chosen)<size:
        d=np.min(np.linalg.norm(w[:,None,:]-w[chosen][None,:,:],axis=2),axis=1)
        d[chosen]=-1;chosen.append(int(np.argmax(d)))
    return w[chosen]

def tchebycheff(objectives,weight,ideal,scales):
    return float(np.max(np.maximum(weight,1e-6)*np.abs(objectives/scales-ideal)))

class SearchEvaluator:
    def __init__(self,scenario,reference,settings):
        self.scenario=scenario;self._reference=reference;self.settings=settings
        self.started=time.perf_counter();self.cpu_started=time.process_time()
        self.records=[];self.archive=[];self.trace=[];self.next_trace=0.0
        self.proposals=0
    @property
    def elapsed(self):return time.perf_counter()-self.started
    def available(self):
        return self.elapsed < self.settings["seconds"] and self.proposals<self.settings["max_proposals"]
    def evaluate(self,genome,operator):
        phy=self.scenario.evaluate(genome);values=None;losses=()
        if phy.feasible:
            result=self._reference.loss(phy.selected,"search")
            losses=tuple(result["replicates"]);values=np.array([result["mean"],phy.energy,phy.duration])
        candidate=Candidate(genome.copy(),phy,values,self.proposals,losses)
        self.proposals+=1
        self.archive=archive_insert(self.archive,candidate)
        self.records.append({"id":candidate.evaluation_id,"operator":operator,"selected":list(phy.selected),
            "assignment":genome.assignment.tolist(),"weights":genome.weights.tolist(),"xi":genome.xi,
            "feasible":phy.feasible,"cv":phy.cv,"losses":list(losses) if losses else None,
            "objectives":values.tolist() if values is not None else None,
            "bandwidth":phy.bandwidth.tolist(),"frequency":phy.frequency.tolist(),
            "phases":phy.phases,"ledger":phy.ledger,"residuals":phy.residuals,
            "wall_seconds":self.elapsed})
        if self.elapsed>=self.next_trace:self.trace_point()
        return candidate
    def trace_point(self):
        before=self.elapsed
        y=[a.objectives/np.asarray(self.settings["scales"]) for a in self.archive]
        hv=hypervolume3(y,self.settings["hv_reference"])
        self.trace.append({"seconds":before,"search_hv":hv,"proposals":self.proposals,
            "archive_size":len(self.archive),"unique_sets":self._reference.stats["search"]["set_misses"]})
        self.next_trace=self.elapsed+self.settings["trace_seconds"]
    def finish(self):
        self.trace_point()
        return {"search_seconds":self.elapsed,"cpu_seconds":time.process_time()-self.cpu_started,
                "budget_seconds":self.settings["seconds"],"overrun_seconds":max(0,self.elapsed-self.settings["seconds"]),
                "proposals":self.proposals,"oracle":deepcopy(dict(self._reference.stats["search"]))}

def run_optimizer(name,initial,scenario,reference,settings,seed,guide=None):
    if name not in ("nsga2","moead"):raise ValueError(name)
    rng=np.random.default_rng(seed)
    ev=SearchEvaluator(scenario,reference,settings)
    pop=[ev.evaluate(g,"initial") for g in initial]
    size=len(pop)
    if name=="nsga2":
        while ev.available():
            rank,cd=rank_crowding(pop)
            def tournament():
                i,j=rng.choice(size,2,replace=False)
                return pop[min((int(i),int(j)),key=lambda z:(rank[z],-cd[z],pop[z].evaluation_id))]
            children=[]
            for _ in range(size):
                if not ev.available():break
                first,second=tournament(),tournament()
                g,op=offspring(first.genome,second.genome,scenario,rng,settings,guide)
                children.append(ev.evaluate(g,op))
            if not children:break
            pop=select_nsga(pop+children,size)
    else:
        weights=weight_vectors(size)
        distances=np.linalg.norm(weights[:,None,:]-weights[None,:,:],axis=2)
        neighborhoods=np.argsort(distances,axis=1,kind="stable")[:,:min(size,max(2,settings["neighbors"]))]
        scales=np.asarray(settings["scales"])
        feasible=[x.objectives/scales for x in pop if x.physical.feasible]
        ideal=np.min(feasible,axis=0) if feasible else np.full(3,np.inf)
        while ev.available():
            for i in rng.permutation(size):
                if not ev.available():break
                pool=neighborhoods[i] if rng.random()<settings["neighbor_probability"] else np.arange(size)
                parents=rng.choice(pool,2,replace=False)
                g,op=offspring(pop[parents[0]].genome,pop[parents[1]].genome,scenario,rng,settings,guide)
                child=ev.evaluate(g,op)
                if child.physical.feasible:ideal=np.minimum(ideal,child.objectives/scales)
                replaced=0
                for j in rng.permutation(pool):
                    old=pop[j]
                    if child.physical.feasible != old.physical.feasible:
                        better=child.physical.feasible
                    elif not child.physical.feasible:better=child.physical.cv<old.physical.cv
                    else:
                        better=tchebycheff(child.objectives,weights[j],ideal,scales)<tchebycheff(old.objectives,weights[j],ideal,scales)
                    if better:
                        pop[j]=child;replaced+=1
                        if replaced>=settings["max_replacements"]:break
    stats=ev.finish()
    if not ev.archive:raise RuntimeError("NO_FEASIBLE_SCHEDULE_FOUND")
    stats["history_coverage"]=guide.coverage if guide else 0.0
    stats["guided_attempts"]=guide.attempts if guide else 0
    stats["guided_fallbacks"]=guide.fallbacks if guide else 0
    return ev,stats
