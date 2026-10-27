#!/usr/bin/env python3
"""LANE: radiometric-magnetic alteration-edge + LiDAR-scarp HGB surface (see README/docs).
Non-fault mimic: unfaulted lithologic contacts / playa & caldera margins."""
import os, sys, json, time
import numpy as np, rasterio
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","src"))
from gemsass2.metric import dti_components
from gemsass2.writer import write_submission
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
REG="/tmp/registry"; G24="/tmp/g24/data/external"
def load_uint8():
    with rasterio.open(f"{REG}/sample_submission.tif") as ds: foot=np.isfinite(ds.read(1))
    with rasterio.open(f"{REG}/labels.tif") as ds: gt=(ds.read(1)==1)
    names=[]; bands=[]
    ln=["ex_max","ex_mean","step_max","lapneg_max","lappos_max","downface_max","upface_max","cross_max","relief","coh100","strike","valid"]
    srcs=[(f"{G24}/lidar_scarp_features_u8.tif",ln,"lidar_"),(f"{G24}/geodawn_rad_u8.tif",["K","Th","U","TC"],"rad_"),(f"{G24}/geodawn_extensions_u8.tif",["ThK","UK","UTh","TMI_up150"],"ext_")]
    for path,ns,pre in srcs:
        with rasterio.open(path) as ds:
            for i,n in enumerate(ns,1): bands.append(ds.read(i)); names.append(pre+n)
    X=np.stack(bands)  # uint8 20 x H x W
    del bands
    idx={n:i for i,n in enumerate(names)}
    der=[]
    for n in ["rad_K","rad_Th","rad_U","ext_ThK","ext_UK","ext_UTh","ext_TMI_up150"]:
        a=X[idx[n]].astype(np.float32)/255.
        gy,gx=np.gradient(a); g=np.hypot(gx,gy)
        p99=np.percentile(g[foot],99) or 1
        der.append(np.clip(g/p99*255,0,255).astype(np.uint8)); names.append("grad_"+n); del a,g
    X=np.concatenate([X,np.stack(der)]).astype(np.uint8); del der
    return X,names,foot,gt

def sample_X(X, flat_indices):
    # flat_indices into H*W; return float32 matrix
    W=X.shape[2]; rows=flat_indices//W; cols=flat_indices%W
    return X[:,rows,cols].T.astype(np.float32)/255.

def predict_surface(model, X, foot):
    H,W=foot.shape; surf=np.zeros((H,W),np.float32)
    bh=256
    for y0 in range(0,H,bh):
        y1=min(H,y0+bh); block=X[:,y0:y1,:].astype(np.float32)/255.
        b=block.reshape(X.shape[0],-1).T
        surf[y0:y1,:]=model.predict_proba(b)[:,1].reshape(y1-y0,W).astype(np.float32)
    return np.where(foot, surf, 0).astype(np.float32)

def emit(score, foot, gt_mask, budget):
    cand = foot & (ndimage.distance_transform_edt(~gt_mask)>2)
    s=np.where(cand, score, -1).astype(np.float32)
    mx=ndimage.maximum_filter(s, size=5)
    ys,xs=np.where(cand & (s==mx) & (s>0))
    order=np.argsort(-s[ys,xs]); ys,xs=ys[order],xs[order]
    H,W=s.shape; taken=np.zeros((H,W),bool); dots=np.zeros((H,W),bool); n=0
    for y,x in zip(ys,xs):
        if taken[y,x]: continue
        dots[y,x]=True; n+=1
        y0,y1=max(0,y-2),min(H,y+3); x0,x1=max(0,x-2),min(W,x+3)
        yy,xx=np.mgrid[y0:y1,x0:x1]; taken[y0:y1,x0:x1] |= ((yy-y)**2+(xx-x)**2) < 2.83**2
        if n>=budget: break
    return dots

def main():
    raise SystemExit('Legacy release path disabled: its partial registry and private holdout do not satisfy the current protocol. See docs/research/concurrent-main.md and scripts/check_registry.py.')
    t0=time.time(); rng=np.random.default_rng(20261027)
    X,names,foot,gt=load_uint8(); print("X",X.shape,X.dtype,"gt",int(gt.sum()),flush=True)
    comp,nc=ndimage.label(gt, structure=np.ones((3,3)))
    cent=np.array(ndimage.center_of_mass(gt, comp, range(1,nc+1)))
    my,mx=np.median(cent[:,0]),np.median(cent[:,1])
    foc=(cent[:,0]>=my).astype(int)*2+(cent[:,1]>=mx).astype(int)
    fold_gt=[np.isin(comp, np.where(foc==f)[0]+1) for f in range(4)]
    dist_gt=ndimage.distance_transform_edt(~gt)
    pos_idx=np.where(gt.ravel())[0]
    neg_pool=np.where((foot & (dist_gt>3)).ravel())[0]
    results={"evaluator":"GEMSDOESASS2-HIDE-RECOVER-v1 alpha=0.2 beta=0.8 R=3px whole-component quadrant folds","canary":{},"folds":[]}
    neg_s=rng.choice(neg_pool,size=60000,replace=False); ps=pos_idx[:20000]
    Xp=sample_X(X,ps); Xn=sample_X(X,neg_s)
    for j,n in enumerate(names):
        v=np.concatenate([Xp[:,j],Xn[:,j]]); y=np.r_[np.ones(len(ps)),np.zeros(len(neg_s))]
        a=roc_auc_score(y,v); results["canary"][n]=round(float(max(a,1-a)),4)
    del Xp,Xn
    print("canary_max",max(results["canary"].values()),flush=True)
    with rasterio.open(f"{REG}/champion32.tif") as ds: champ=ds.read(1)>0
    pooled={k:[0.,0.,0.] for k in ["model20000","model37654","model44090","champion"]}
    for f in range(4):
        test_gt=fold_gt[f]; vis_gt=gt & ~test_gt
        dvis=ndimage.distance_transform_edt(~vis_gt)
        tr_pos=np.where(vis_gt.ravel())[0]
        cand_neg=np.where((foot & ~test_gt & (dvis>3)).ravel())[0]
        tr_neg=rng.choice(cand_neg,size=min(120000,len(tr_pos)*3),replace=False)
        tr=np.r_[tr_pos,tr_neg]; y=np.r_[np.ones(len(tr_pos)),np.zeros(len(tr_neg))]
        m=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.07,max_leaf_nodes=31,random_state=7)
        m.fit(sample_X(X,tr),y)
        surf=predict_surface(m,X,foot)
        row={"fold":f,"withheld_pos":int(test_gt.sum())}
        for budget,key in [(20000,"model20000"),(37654,"model37654"),(44090,"model44090")]:
            dots=emit(surf,foot,vis_gt,budget) & ~vis_gt
            tp,fp,fn=dti_components(dots,test_gt)
            for i,v in enumerate([tp,fp,fn]): pooled[key][i]+=v
            row[key]=round(float(tp/(tp+0.2*fp+0.8*fn+1e-12)),5)
        tp,fp,fn=dti_components(champ & ~vis_gt, test_gt)
        for i,v in enumerate([tp,fp,fn]): pooled["champion"][i]+=v
        row["champion"]=round(float(tp/(tp+0.2*fp+0.8*fn+1e-12)),5)
        results["folds"].append(row); print(row,flush=True); del surf
    for k,(tp,fp,fn) in pooled.items(): results[k+"_pooled_DTI"]=round(float(tp/(tp+0.2*fp+0.8*fn+1e-12)),5)
    results["withheld_pos_total"]=int(gt.sum())
    json.dump(results,open("registry/holdout_results.json","w"),indent=1)
    print(json.dumps(results,indent=1),flush=True)
    # final
    tr_neg=rng.choice(neg_pool,size=min(180000,len(pos_idx)*3),replace=False)
    tr=np.r_[pos_idx,tr_neg]; y=np.r_[np.ones(len(pos_idx)),np.zeros(len(tr_neg))]
    m=HistGradientBoostingClassifier(max_iter=200,learning_rate=0.07,max_leaf_nodes=31,random_state=7)
    m.fit(sample_X(X,tr),y)
    surf=predict_surface(m,X,foot); np.save("/tmp/final_surface.npy",surf)
    best=max(["model20000","model37654","model44090"],key=lambda k:results[k+"_pooled_DTI"])
    budget=int(best[5:]); dots=emit(surf,foot,gt,budget)
    out=np.where(foot,dots.astype(np.float32),0.).astype(np.float32)
    sha=write_submission(out,f"{REG}/sample_submission.tif","/tmp/candidate.tif")
    json.dump({"budget":budget,"best_key":best,"sha256":sha,"dots":int(dots.sum())},open("/tmp/final_choice.json","w"),indent=1)
    print("FINAL",best,budget,sha,int(dots.sum()),"elapsed_s",round(time.time()-t0),flush=True)
if __name__=="__main__": main()
