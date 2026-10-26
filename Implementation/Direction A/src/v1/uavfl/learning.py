"""Private full-reference FL oracle. No surrogate, pseudo-loss or resource proxy."""
from collections import defaultdict
import hashlib, json, time
import numpy as np
import torch
from torch import nn
from torch.nn.utils import parameters_to_vector, vector_to_parameters

def seed_for(root,*parts):
    text=json.dumps([int(root),*parts],sort_keys=True)
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],"little")%(2**63-1)

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Conv2d(1,16,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
          nn.Conv2d(16,32,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
          nn.Flatten(),nn.Linear(1568,64),nn.ReLU(),nn.Linear(64,10))
    def forward(self,x):return self.net(x)

def initial_checkpoint(seed):
    with torch.random.fork_rng():
        torch.manual_seed(seed_for(seed,"checkpoint"))
        return parameters_to_vector(CNN().parameters()).detach().clone()

def model_from(vector):
    model=CNN()
    vector_to_parameters(vector.detach().clone(),model.parameters())
    return model

class Reference:
    def __init__(self, data, checkpoint, config, root_seed, snapshot="0"):
        self._data=data
        self._checkpoint=checkpoint.detach().clone()
        self.config=config
        self.seed=root_seed
        self.snapshot=str(snapshot)
        self.weights=data.weights.copy()
        self.checkpoint_hash=hashlib.sha256(self._checkpoint.numpy().tobytes()).hexdigest()
        self.namespace=hashlib.sha256((data.fingerprint+self.checkpoint_hash+json.dumps(config["fl"],sort_keys=True)+self.snapshot).encode()).hexdigest()
        self._updates={};self._losses={};self._split_tensors={}
        self.stats=defaultdict(lambda:{"update_misses":0,"update_hits":0,"set_misses":0,"set_hits":0,"seconds":0.0})
        self.criterion=nn.CrossEntropyLoss()
    def checkpoint(self):return self._checkpoint.clone()
    def _update(self,m,phase,r):
        key=(self.namespace,phase,int(r),int(m))
        stat=self.stats[phase]
        if key in self._updates:
            stat["update_hits"]+=1
            return self._updates[key]
        stat["update_misses"]+=1
        generator=torch.Generator().manual_seed(seed_for(self.seed,self.snapshot,phase,"local",int(r),int(m)))
        model=model_from(self._checkpoint);model.train()
        opt=torch.optim.SGD(model.parameters(),lr=self.config["fl"]["lr"])
        x,y=self._data.clients["train"][m]
        for _ in range(self.config["fl"]["local_steps"]):
            idx=torch.randint(len(y),(self.config["fl"]["batch_size"],),generator=generator)
            opt.zero_grad(set_to_none=True)
            loss=self.criterion(model(x[idx]),y[idx]);loss.backward();opt.step()
        delta=parameters_to_vector(model.parameters()).detach().clone()-self._checkpoint
        self._updates[key]=delta
        return delta
    def aggregate(self, selected, phase, r):
        selected=tuple(sorted(set(int(m) for m in selected)))
        if not selected:raise ValueError("Cannot aggregate empty set")
        p=self.weights[list(selected)];p=p/p.sum()
        vector=self._checkpoint.clone()
        for m,weight in zip(selected,p):
            vector.add_(self._update(m,phase,r),alpha=float(weight))
        return vector
    def _validation(self,split):
        if split not in self._split_tensors:
            xs=[];ys=[];ws=[]
            for p,(x,y) in zip(self.weights,self._data.clients[split]):
                xs.append(x);ys.append(y);ws.append(torch.full((len(y),),float(p/len(y)),dtype=torch.float64))
            self._split_tensors[split]=(torch.cat(xs),torch.cat(ys),torch.cat(ws))
        return self._split_tensors[split]
    def measure(self, vector, split, metrics=False):
        model=model_from(vector);model.eval()
        x,y,w=self._validation(split);loss=0.0
        confusion=np.zeros((10,10),float)
        with torch.inference_mode():
            for start in range(0,len(y),256):
                end=start+256
                logits=model(x[start:end])
                ce=nn.functional.cross_entropy(logits,y[start:end],reduction="none").double()
                loss+=float((ce*w[start:end]).sum())
                if metrics:
                    truth=y[start:end].numpy();pred=logits.argmax(1).numpy()
                    np.add.at(confusion,(truth,pred),w[start:end].numpy())
        if not metrics:return loss
        tp=np.diag(confusion);den=confusion.sum(0)+confusion.sum(1)
        f1=np.divide(2*tp,den,out=np.zeros(10),where=den>0)
        return {"loss":loss,"accuracy":float(tp.sum()/confusion.sum()),
                "macro_f1":float(f1.mean()),"class9_recall":float(tp[9]/confusion[9].sum()) if confusion[9].sum() else None}
    def loss(self,selected,phase="search"):
        if phase not in ("search","audit"):raise ValueError("Only search/audit reference protocols allowed")
        selected=tuple(sorted(set(int(m) for m in selected)))
        if not selected:raise ValueError("Empty selection")
        key=(self.namespace,phase,selected)
        start=time.perf_counter();stat=self.stats[phase]
        if key in self._losses:
            stat["set_hits"]+=1
            values=self._losses[key]
        else:
            stat["set_misses"]+=1
            repeats=self.config["fl"][phase+"_replicates"]
            values=[self.measure(self.aggregate(selected,phase,r),phase) for r in range(repeats)]
            self._losses[key]=tuple(values)
        stat["seconds"]+=time.perf_counter()-start
        return {"mean":float(np.mean(values)),"replicates":list(values),
                "std":float(np.std(values,ddof=1)) if len(values)>1 else 0.0}
    def execute(self,selected,execution_seed):
        return self.aggregate(selected,"execute",int(execution_seed))
    def report(self,m,execution_seed,dimension):
        # Created only for the selected, executed clients, at the PRE-local-SGD model.
        model=model_from(self._checkpoint);x,y=self._data.clients["train"][m]
        generator=torch.Generator().manual_seed(seed_for(self.seed,self.snapshot,"report",int(execution_seed),int(m)))
        idx=torch.randint(len(y),(32,),generator=generator)
        model.zero_grad(set_to_none=True)
        self.criterion(model(x[idx]),y[idx]).backward()
        gradient=torch.cat([p.grad.detach().flatten() for p in model.parameters()])
        # Shared Rademacher projection without materializing dimension x model_size.
        projection=torch.Generator().manual_seed(seed_for(202,"projection",dimension,len(gradient)))
        sketch=torch.zeros(dimension)
        for start in range(0,len(gradient),4096):
            block=gradient[start:start+4096]
            signs=torch.randint(0,2,(dimension,len(block)),generator=projection,dtype=torch.int8).float()*2-1
            sketch+=signs@block
        return (sketch/np.sqrt(dimension)).numpy()
