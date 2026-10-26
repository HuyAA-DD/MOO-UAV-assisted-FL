"""Pareto utilities and exact three-dimensional minimization hypervolume."""
import numpy as np

def dominates(a,b):
    return bool(np.all(a<=b) and np.any(a<b))

def nondominated_indices(values):
    y=np.asarray(values,float)
    return np.array([i for i in range(len(y))
        if not np.any(np.all(y<=y[i],axis=1)&np.any(y<y[i],axis=1))],int)

def hypervolume3(values, reference):
    ref=np.asarray(reference,float)
    y=np.asarray(values,float).reshape(-1,3)
    if len(y)==0:return 0.0
    y=y[np.isfinite(y).all(axis=1)&np.all(y<ref,axis=1)]
    if len(y)==0:return 0.0
    y=np.unique(y,axis=0);y=y[nondominated_indices(y)]
    xs=np.unique(y[:,0]);volume=0.0
    for i,x in enumerate(xs):
        width=(xs[i+1] if i+1<len(xs) else ref[0])-x
        yz=y[y[:,0]<=x,1:];yz=yz[np.argsort(yz[:,0],kind="stable")]
        z=ref[2];area=0.0
        for yy,zz in yz:
            if zz<z:area+=(ref[1]-yy)*(z-zz);z=zz
        volume+=width*area
    return float(volume)

def archive_insert(archive, candidate):
    if not candidate.physical.feasible:return archive
    y=candidate.objectives
    if any(dominates(x.objectives,y) or np.array_equal(x.objectives,y) for x in archive):
        return archive
    return [x for x in archive if not dominates(y,x.objectives)]+[candidate]
