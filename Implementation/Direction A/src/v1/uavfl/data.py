"""Fashion-MNIST IDX loader; disjoint splits and shared client-class preferences."""
from dataclasses import dataclass
from pathlib import Path
import gzip, hashlib, json, struct, urllib.request
import numpy as np
import torch

FILES={
 "train-images-idx3-ubyte.gz":"8d4fb7e6c68d591d4c3dfef9ec88bf0d",
 "train-labels-idx1-ubyte.gz":"25c81989df183df01b3e8a0aad5dffbe",
 "t10k-images-idx3-ubyte.gz":"bef4ecab320f06d8554ea6380940ec79",
 "t10k-labels-idx1-ubyte.gz":"bb300cfdad3c16e7a12a480ee83cd310"}
URL="https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/"

def ensure_data(root, download=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    for name,md5 in FILES.items():
        p=root/name
        if not p.exists():
            if not download:raise FileNotFoundError(f"{p}; use --download")
            with urllib.request.urlopen(URL+name,timeout=120) as response:
                content=response.read()
            if hashlib.md5(content).hexdigest()!=md5:raise ValueError("Dataset checksum mismatch")
            temporary=p.with_suffix(".download")
            temporary.write_bytes(content);temporary.replace(p)
        if hashlib.md5(p.read_bytes()).hexdigest()!=md5:
            raise ValueError(f"Corrupt Fashion-MNIST file: {p}")
    return root

def read_idx(path):
    raw=gzip.decompress(Path(path).read_bytes())
    magic,count=struct.unpack(">II",raw[:8])
    if magic==2051:
        rows,cols=struct.unpack(">II",raw[8:16])
        if (rows,cols)!=(28,28) or len(raw)!=16+count*rows*cols:raise ValueError("Invalid image IDX")
        return np.frombuffer(raw,np.uint8,offset=16).reshape(count,28,28)
    if magic==2049:
        if len(raw)!=8+count:raise ValueError("Invalid label IDX")
        return np.frombuffer(raw,np.uint8,offset=8)
    raise ValueError("Invalid IDX magic")

@dataclass
class DataBundle:
    clients: dict
    weights: np.ndarray
    fingerprint: str
    manifest: dict

def make_data(root, config, seed, clients=6):
    root=Path(root)
    images=read_idx(root/"train-images-idx3-ubyte.gz")
    labels=read_idx(root/"train-labels-idx1-ubyte.gz")
    test_images=read_idx(root/"t10k-images-idx3-ubyte.gz")
    test_labels=read_idx(root/"t10k-labels-idx1-ubyte.gz")
    dc=config["data"];rng=np.random.default_rng(seed)
    selected={key:[] for key in ("train","search","audit","test")}
    for cls in range(10):
        ids=rng.permutation(np.flatnonzero(labels==cls));start=0
        for key in ("train","search","audit"):
            size=dc[key]//10
            selected[key].extend(ids[start:start+size].tolist());start+=size
        selected["test"].extend(rng.permutation(np.flatnonzero(test_labels==cls))[:dc["test"]//10].tolist())
    # Fixed per-class client probabilities shared by every split.
    for attempt in range(100):
        pref=(np.full((10,clients),1/clients) if dc["partition"]=="iid"
              else rng.dirichlet(np.full(clients,dc["alpha"]),size=10))
        allocations={key:[[] for _ in range(clients)] for key in selected}
        for key,ids in selected.items():
            y=test_labels if key=="test" else labels
            ids=np.asarray(ids)
            for cls in range(10):
                group=rng.permutation(ids[y[ids]==cls])
                desired=pref[cls]*len(group);counts=np.floor(desired).astype(int)
                remainder=len(group)-counts.sum()
                order=np.argsort(-(desired-counts),kind="stable")
                counts[order[:remainder]]+=1
                offset=0
                for m,n in enumerate(counts):
                    allocations[key][m]=allocations[key][m]+group[offset:offset+n].tolist();offset+=n
        if all(len(ids)>0 for split in allocations.values() for ids in split):break
    else:raise ValueError("Cannot create nonempty per-client splits; increase size/alpha")
    tensors={}
    for key,groups in allocations.items():
        x,y=(test_images,test_labels) if key=="test" else (images,labels)
        tensors[key]=[]
        for ids in groups:
            idx=np.asarray(ids,int)
            xx=torch.from_numpy(x[idx].copy()).float().unsqueeze(1)/255.0
            yy=torch.from_numpy(y[idx].astype(np.int64))
            tensors[key].append((xx,yy))
    counts=np.array([len(z) for z in allocations["train"]],float)
    weights=counts/counts.sum()
    manifest={"seed":seed,"settings":dc,"client_counts":{k:[len(v) for v in a] for k,a in allocations.items()},
              "class_counts":{k:[np.bincount(z[1].numpy(),minlength=10).tolist() for z in group] for k,group in tensors.items()},
              "client_weights":weights.tolist(),"source_md5":FILES,
              "index_hashes":{k:hashlib.sha256(json.dumps(v).encode()).hexdigest() for k,v in allocations.items()}}
    # Verify source-training splits are disjoint; official test has separate provenance.
    sets=[set(selected[k]) for k in ("train","search","audit")]
    if any(sets[i]&sets[j] for i in range(3) for j in range(i)):
        raise AssertionError("Split leakage")
    fingerprint=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    manifest["fingerprint"]=fingerprint
    return DataBundle(tensors,weights,fingerprint,manifest)
