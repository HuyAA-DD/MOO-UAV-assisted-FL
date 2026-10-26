"""Run from this directory: python run.py --download --output results/pilot."""
from pathlib import Path
import argparse
from uavfl.config import load_config
from uavfl.experiment import compare

def main():
    parser=argparse.ArgumentParser(description="Direction A: paired NSGA-II / MOEA-D FL benchmark")
    parser.add_argument("--config",type=Path)
    parser.add_argument("--output",type=Path,default=Path("results/pilot"))
    parser.add_argument("--seeds",type=int,nargs="+",default=[101,102,103,104,105])
    parser.add_argument("--seconds",type=float)
    parser.add_argument("--rounds",type=int,default=1)
    parser.add_argument("--algorithms",nargs="+",choices=["nsga2","moead"],default=["nsga2","moead"])
    parser.add_argument("--download",action="store_true")
    args=parser.parse_args()
    if args.rounds<1 or len(set(args.seeds))!=len(args.seeds):parser.error("Positive rounds and distinct seeds required")
    cfg=load_config(args.config)
    if args.seconds is not None:cfg["search"]["seconds"]=args.seconds
    from uavfl.config import validate
    validate(cfg)
    root=Path(__file__).resolve().parent
    compare(root,args.output,cfg,args.seeds,args.rounds,args.download,tuple(args.algorithms))

if __name__=="__main__":main()
