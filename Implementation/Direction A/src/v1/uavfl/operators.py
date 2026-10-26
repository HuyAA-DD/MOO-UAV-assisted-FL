"""Shared mixed-variable operators; optional historical set-aware proposals."""
from dataclasses import dataclass
import numpy as np
from .physics import Genome

@dataclass(frozen=True)
class HistoryReport:
    sketch: np.ndarray
    timestamp: float
    model: np.ndarray

class HistoricalGuide:
    def __init__(self, weights, reports, checkpoint, clock, settings):
        self.p=np.asarray(weights,float).copy();self.reports={}
        current=np.asarray(checkpoint,float)
        for m,report in reports.items():
            drift=np.linalg.norm(current-report.model)/max(1,np.linalg.norm(report.model))
            age=clock-report.timestamp
            if 0<=age<=settings["history_max_age"] and drift<=settings["history_max_drift"]:
                self.reports[int(m)]=report.sketch.copy()
        self.coverage=float(sum(self.p[m] for m in self.reports))
        if self.reports:
            self.reference=sum(self.p[m]*r for m,r in self.reports.items())/self.coverage
        self.attempts=0;self.fallbacks=0
    def score(self,selected):
        known=[m for m in selected if m in self.reports]
        if not known:return None
        mean=sum(self.p[m]*self.reports[m] for m in known)/self.p[known].sum()
        return float(np.sum((mean-self.reference)**2))
    def swap(self,g,scenario,rng,trials):
        self.attempts+=1
        selected=set(np.flatnonzero(g.assignment))
        inside=sorted(selected&self.reports.keys())
        outside=sorted(self.reports.keys()-selected)
        tuples=[]
        for i in inside:
            for j in outside:
                for u in np.flatnonzero(scenario.mask[j]):
                    counts=np.bincount(g.assignment,minlength=scenario.U+1)[1:].copy()
                    counts[g.assignment[i]-1]-=1;counts[u]+=1
                    if counts[u]*scenario.n["bmin"]<=scenario.n["bandwidth"]:
                        tuples.append((i,j,int(u)+1))
        if not tuples:
            self.fallbacks+=1;return None
        indexes=rng.choice(len(tuples),size=min(trials,len(tuples)),replace=False)
        options=[]
        for idx in indexes:
            i,j,u=tuples[int(idx)]
            options.append((self.score((selected-{i})|{j}),i,j,u))
        best=min(options)
        if best[0]>=self.score(selected):
            best=options[int(rng.integers(len(options)))]
        _,i,j,u=best
        child=g.copy();child.assignment[i]=0;child.assignment[j]=u
        child.weights[j]=1/max(1,(child.assignment==u).sum())
        return child

def repair(g,scenario,rng):
    g=g.copy();n=scenario.n
    for m,u in enumerate(g.assignment):
        if u and not scenario.mask[m,u-1]:g.assignment[m]=0
    for u in range(1,scenario.U+1):
        group=np.flatnonzero(g.assignment==u)
        capacity=int(np.floor(n["bandwidth"]/n["bmin"]))
        if len(group)>capacity:
            g.assignment[rng.choice(group,len(group)-capacity,replace=False)]=0
    selected=np.flatnonzero(g.assignment)
    cap=min(n["nmax"],scenario.M)
    if len(selected)>cap:g.assignment[rng.choice(selected,len(selected)-cap,replace=False)]=0
    if not np.any(g.assignment):
        pairs=np.argwhere(scenario.mask)
        if len(pairs)==0:raise ValueError("No eligible links")
        m,u=pairs[int(rng.integers(len(pairs)))];g.assignment[m]=u+1
    g.weights=np.clip(g.weights,0,1);g.xi=float(np.clip(g.xi,0,1))
    return g

def initialize(scenario,size,seed):
    rng=np.random.default_rng(seed);population=[]
    # Identical singleton and cardinality-diverse initial genomes for both optimizers.
    for m,u in np.argwhere(scenario.mask):
        if len(population)>=size:break
        a=np.zeros(scenario.M,int);a[m]=u+1
        population.append(Genome(a,np.ones(scenario.M),0.5))
    while len(population)<size:
        a=np.zeros(scenario.M,int)
        eligible=np.flatnonzero(scenario.mask.any(axis=1))
        count=int(rng.integers(1,min(len(eligible),scenario.n["nmax"])+1))
        for m in rng.choice(eligible,count,replace=False):
            a[m]=int(rng.choice(np.flatnonzero(scenario.mask[m])))+1
        population.append(repair(Genome(a,rng.random(scenario.M),float(rng.random())),scenario,rng))
    return population

def sbx(x,y,rng,eta=15):
    out=x.copy()
    for i,(a,b) in enumerate(zip(x,y)):
        if rng.random()>0.5 or abs(a-b)<1e-14:continue
        low,high=sorted((a,b));r=rng.random()
        beta=1+2*low/(high-low);alpha=2-beta**(-(eta+1))
        q=(r*alpha)**(1/(eta+1)) if r<=1/alpha else (1/(2-r*alpha))**(1/(eta+1))
        c1=0.5*((low+high)-q*(high-low))
        beta=1+2*(1-high)/(high-low);alpha=2-beta**(-(eta+1))
        q=(r*alpha)**(1/(eta+1)) if r<=1/alpha else (1/(2-r*alpha))**(1/(eta+1))
        c2=0.5*((low+high)+q*(high-low))
        out[i]=c1 if rng.random()<0.5 else c2
    return np.clip(out,0,1)

def polynomial_mutation(x,rng,eta=20):
    out=x.copy()
    for i,v in enumerate(x):
        if rng.random()>1/len(x):continue
        r=rng.random()
        if r<0.5:
            delta=(2*r+(1-2*r)*(1-v)**(eta+1))**(1/(eta+1))-1
        else:
            delta=1-(2*(1-r)+2*(r-0.5)*v**(eta+1))**(1/(eta+1))
        out[i]=np.clip(v+delta,0,1)
    return out

def offspring(g1,g2,scenario,rng,settings,guide=None):
    a=np.where(rng.random(scenario.M)<0.5,g1.assignment,g2.assignment).copy()
    real=sbx(np.r_[g1.weights,g1.xi],np.r_[g2.weights,g2.xi],rng)
    real=polynomial_mutation(real,rng)
    child=repair(Genome(a,real[:-1],float(real[-1])),scenario,rng)
    operator="generic"
    guided=None
    if guide is not None and rng.random()<settings["guided_probability"]:
        guided=guide.swap(child,scenario,rng,settings["guided_trials"])
    if guided is not None:
        child=guided;operator="historical_swap"
    else:
        selected=np.flatnonzero(child.assignment);inactive=np.flatnonzero(child.assignment==0)
        action=int(rng.integers(4))
        if action==0 and len(inactive):
            m=int(rng.choice(inactive));links=np.flatnonzero(scenario.mask[m])
            if len(links):child.assignment[m]=int(rng.choice(links))+1
        elif action==1 and len(selected)>1:
            child.assignment[int(rng.choice(selected))]=0
        elif action==2 and len(selected) and len(inactive):
            i=int(rng.choice(selected));j=int(rng.choice(inactive))
            links=np.flatnonzero(scenario.mask[j])
            if len(links):child.assignment[i]=0;child.assignment[j]=int(rng.choice(links))+1
        elif len(selected):
            m=int(rng.choice(selected));links=np.flatnonzero(scenario.mask[m])
            child.assignment[m]=int(rng.choice(links))+1
    return repair(child,scenario,rng),operator
