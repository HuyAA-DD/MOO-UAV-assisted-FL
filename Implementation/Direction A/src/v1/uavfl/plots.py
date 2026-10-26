"""Static, exportable comparison figures from actual run artifacts."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS={"nsga2":"#be1e2d","moead":"#2675ad"}

def make_plots(output,rows,fronts,traces):
    output=Path(output)
    fig,axes=plt.subplots(1,3,figsize=(13,3.7))
    for name,color in COLORS.items():
        chosen=[r for r in fronts if r["algorithm"]==name and r["round"]==0]
        for ax,(x,y) in zip(axes,[("energy","loss"),("time","loss"),("time","energy")]):
            ax.scatter([r[x] for r in chosen],[r[y] for r in chosen],s=12,alpha=.45,color=color,label=name)
            ax.set_xlabel({"energy":"Energy (J)","time":"Time (s)","loss":"Audit loss"}[x])
            ax.set_ylabel({"energy":"Energy (J)","time":"Time (s)","loss":"Audit loss"}[y])
            ax.grid(alpha=.2)
    axes[0].legend();fig.suptitle("Audited snapshot fronts (paired scenarios; no cross-snapshot dominance)")
    fig.tight_layout();fig.savefig(output/"pareto.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.7))
    for name,color in COLORS.items():
        for seed in sorted({r["seed"] for r in traces}):
            rr=[r for r in traces if r["algorithm"]==name and r["seed"]==seed and r["round"]==0]
            if rr:axes[0].plot([r["seconds"] for r in rr],[r["search_hv"] for r in rr],color=color,alpha=.45)
        axes[0].plot([],[],color=color,label=name)
    axes[0].set(xlabel="Measured search wall time (s)",ylabel="Search-validation hypervolume")
    axes[0].legend();axes[0].grid(alpha=.2)
    for seed in sorted({r["seed"] for r in rows}):
        pair={r["algorithm"]:r for r in rows if r["seed"]==seed and r["round"]==0}
        if all(a in pair for a in COLORS):
            axes[1].plot([0,1],[pair["nsga2"]["audited_hv"],pair["moead"]["audited_hv"]],"o-",alpha=.65,label=str(seed))
    axes[1].set_xticks([0,1],["NSGA-II","MOEA/D"]);axes[1].set_ylabel("Independent audited hypervolume")
    axes[1].grid(alpha=.2);axes[1].legend(title="Paired seed",fontsize=8)
    fig.tight_layout();fig.savefig(output/"hypervolume.png",dpi=180);plt.close(fig)
