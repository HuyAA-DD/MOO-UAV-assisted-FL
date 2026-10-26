"""Equations A9-A22: closed static-hover execution model, no learning oracle."""
from dataclasses import dataclass
from copy import deepcopy
import hashlib
import numpy as np

@dataclass
class Genome:
    assignment: np.ndarray
    weights: np.ndarray
    xi: float
    def copy(self):
        return Genome(self.assignment.copy(), self.weights.copy(), float(self.xi))
    def key(self):
        return hashlib.sha256(self.assignment.astype("<i8").tobytes()
            + self.weights.astype("<f8").tobytes()
            + np.array([self.xi],dtype="<f8").tobytes()).hexdigest()[:20]

@dataclass
class Physical:
    feasible: bool
    cv: float
    selected: tuple
    energy: float
    duration: float
    bandwidth: np.ndarray
    frequency: np.ndarray
    phases: dict
    ledger: dict
    residuals: dict

class Scenario:
    def __init__(self, config, model_size=105866):
        self.cfg = deepcopy(config)
        self.n = deepcopy(config["network"])
        n = self.n
        self.q = np.asarray(n["uav_positions"],float)
        self.r = np.asarray(n["client_positions"],float)
        if self.q.ndim != 2 or self.r.ndim != 2 or self.q.shape[1] != 3 or self.r.shape[1] != 3:
            raise ValueError("Positions must be Mx3/Ux3")
        if not np.isfinite(self.q).all() or not np.isfinite(self.r).all() or (self.q[:,2]<=0).any():
            raise ValueError("Invalid geometry")
        self.M, self.U = len(self.r), len(self.q)
        distance = np.linalg.norm(self.r[:,None,:]-self.q[None,:,:],axis=2)
        self.mask = distance <= n["radius"]
        self.gain = n["beta0"]/distance**2
        self.model_bits = 32*model_size
        self.report_bits = 32*n["sketch_dimension"]+n["metadata_bits"]
        self.client_bits = self.model_bits+self.report_bits
        self.cycles = n["train_cycles"]+n["report_cycles"]
        self.client_battery = np.full(self.M,n["client_battery"],float)
        self.uav_battery = np.full(self.U,n["uav_battery"],float)
        self.clock = 0.0

    def rate(self, client, uav, bandwidth):
        if np.any(np.asarray(bandwidth)<=0):
            raise ValueError("Rate requested on inactive/zero-bandwidth link")
        n = self.n
        return n["mac_efficiency"]*bandwidth*np.log1p(
            n["tx_power"]*self.gain[client,uav]/(n["coding_gap"]*n["noise_psd"]*bandwidth))/np.log(2)

    def evaluate(self, g, frequencies=None):
        n = self.n
        a = np.asarray(g.assignment)
        if a.shape!=(self.M,) or g.weights.shape!=(self.M,):
            raise ValueError("Invalid genome shape")
        if not np.isfinite(a).all() or (a!=np.floor(a)).any() or (a<0).any() or (a>self.U).any():
            raise ValueError("Invalid association")
        if not np.isfinite(g.weights).all() or (g.weights<0).any() or not np.isfinite(g.xi) or not 0<=g.xi<=1:
            raise ValueError("Invalid continuous genome")
        a = a.astype(int)
        selected = tuple(np.flatnonzero(a).tolist())
        bw = np.zeros(self.M); f = np.zeros(self.M)
        if not selected:
            return Physical(False,1.0,(),float("inf"),float("inf"),bw,f,{}, {}, {"nonempty":1.0})
        idx = np.asarray(selected); counts=np.array([(a==u+1).sum() for u in range(self.U)])
        active = counts>0
        invalid_mask = int((~self.mask[idx,a[idx]-1]).sum())
        capacity = np.maximum(0,counts*n["bmin"]-n["bandwidth"])
        if invalid_mask or np.any(capacity):
            return Physical(False,float(invalid_mask+capacity.sum()/n["bandwidth"]),selected,
                float("inf"),float("inf"),bw,f,{}, {}, {"eligibility":invalid_mask,"capacity":capacity.tolist()})
        for u in np.flatnonzero(active):
            group=np.flatnonzero(a==u+1); w=g.weights[group].copy()
            if w.sum()==0: w[:]=1
            bw[group]=n["bmin"]+(n["bandwidth"]-len(group)*n["bmin"])*w/w.sum()
        upload=np.zeros(self.M)
        upload[idx]=self.client_bits/self.rate(idx,a[idx]-1,bw[idx])
        D0=self.model_bits/n["coordinator_down_rate"]
        Du=active.astype(float)*self.model_bits/n["client_down_rate"]
        Au=active*(n["agg_setup"]+n["agg_per_client"]*counts)
        Hu=active*(self.model_bits+n["metadata_bits"]+counts*self.report_bits)/n["backhaul_rate"]
        A0=n["global_agg_setup"]+n["global_agg_per_uav"]*active.sum()
        overhead=D0+Du.max()+Au.max()+Hu.max()+A0
        dmin=np.max(self.cycles/n["fmax"]+upload[idx])
        dmax=np.max(self.cycles/n["fmin"]+upload[idx])
        cap=min(dmax,n["deadline"]-overhead)
        if frequencies is not None:
            f=np.asarray(frequencies,float).copy()
            if f.shape!=(self.M,) or not np.isfinite(f).all():
                raise ValueError("Invalid explicit CPU vector")
            if np.any(f[idx]<=0):
                raise ValueError("Active CPU must be positive")
        elif cap < dmin:
            f[idx]=n["fmax"]   # diagnostic lower-bound time; necessarily deadline-infeasible
        else:
            d=dmin+g.xi*(cap-dmin)
            f[idx]=np.maximum(n["fmin"], self.cycles/(d-upload[idx]))
        service=float(np.max(self.cycles/f[idx]+upload[idx]))
        total=float(overhead+service)
        client_base=np.full(self.M,n["client_base"]*total)
        client_compute=np.zeros(self.M);client_compute[idx]=n["kappa"]*self.cycles*f[idx]**2
        client_rx=np.zeros(self.M);client_rx[idx]=n["client_rx"]*Du[a[idx]-1]
        client_tx=n["tx_power"]*upload
        client_energy=client_base+client_compute+client_rx+client_tx
        hover=np.full(self.U,n["hover_power"]*total)
        uav_base=np.full(self.U,n["uav_base"]*total)
        uav_rx0=active*n["uav_rx"]*D0
        uav_dl=n["uav_tx"]*Du;uav_ul=active*n["uav_rx"]*service
        uav_agg=n["uav_agg"]*Au;uav_bh=n["uav_tx"]*Hu
        uav_energy=hover+uav_base+uav_rx0+uav_dl+uav_ul+uav_agg+uav_bh
        ground_parts={"base":n["coordinator_base"]*total,"downlink":n["coordinator_tx"]*D0,
                      "backhaul_rx":n["coordinator_rx"]*Hu.max(),"aggregation":n["coordinator_agg"]*A0}
        ground_energy=sum(ground_parts.values())
        residuals={"deadline":total-n["deadline"],
                   "cardinality":len(selected)-min(self.M,n["nmax"]),
                   "client_battery":(client_energy-(self.client_battery-n["client_reserve"])).tolist(),
                   "uav_battery":(uav_energy-(self.uav_battery-n["uav_reserve"])).tolist(),
                   "cpu_low":(n["fmin"]-f[idx]).tolist(),
                   "cpu_high":(f[idx]-n["fmax"]).tolist(),
                   "inactive_cpu":np.abs(f[a==0]).tolist()}
        # Tolerances: 1e-9 s, 1e-8 J, 1 Hz. Scales are fixed, never remaining battery.
        cv=max(0,(residuals["deadline"]-1e-9)/n["deadline"])+max(0,residuals["cardinality"])
        cv+=sum(max(0,(v-1e-8)/1000) for v in residuals["client_battery"])
        cv+=sum(max(0,(v-1e-8)/20000) for v in residuals["uav_battery"])
        cv+=sum(max(0,(v-1)/n["fmax"]) for key in ("cpu_low","cpu_high","inactive_cpu") for v in residuals[key])
        def arr(x): return np.asarray(x).tolist()
        ledger={"clients":arr(client_energy),"uavs":arr(uav_energy),"coordinator":float(ground_energy),
                "client_parts":{"base":arr(client_base),"compute":arr(client_compute),"rx":arr(client_rx),"tx":arr(client_tx)},
                "uav_parts":{"hover":arr(hover),"base":arr(uav_base),"rx0":arr(uav_rx0),
                             "downlink":arr(uav_dl),"uplink_rx":arr(uav_ul),"aggregation":arr(uav_agg),"backhaul":arr(uav_bh)},
                "coordinator_parts":ground_parts}
        phases={"D0":D0,"D":float(Du.max()),"service":service,"A":float(Au.max()),
                "H":float(Hu.max()),"A0":float(A0),"Du":arr(Du),"Au":arr(Au),"Hu":arr(Hu),
                "upload":arr(upload),"dmin":float(dmin),"dmax":float(dmax),"dcap":float(cap)}
        return Physical(cv==0,float(cv),selected,float(client_energy.sum()+uav_energy.sum()+ground_energy),
                        total,bw,f,phases,ledger,residuals)

    def commit_costs(self, physical):
        if not physical.feasible: raise ValueError("Cannot execute infeasible schedule")
        self.client_battery-=np.asarray(physical.ledger["clients"])
        self.uav_battery-=np.asarray(physical.ledger["uavs"])
        self.clock+=physical.duration
