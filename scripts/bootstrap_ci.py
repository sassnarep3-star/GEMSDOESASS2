import numpy as np, rasterio, json
from scipy import ndimage
import sys; sys.path.insert(0,"src")
with rasterio.open("/tmp/candidate.tif") as ds: cand=ds.read(1)>0
with rasterio.open("/tmp/registry/champion32.tif") as ds: champ=ds.read(1)>0
with rasterio.open("/tmp/registry/champ_GEMSDOE27.tif") as ds: champ27=ds.read(1)>0
with rasterio.open("/tmp/registry/labels.tif") as ds: gt=ds.read(1)==1
with rasterio.open("/tmp/registry/sample_submission.tif") as ds: foot=np.isfinite(ds.read(1))
with rasterio.open("/tmp/g24/data/external/derived_sgmc_faults_100m_u8.tif") as ds: sg=ds.read(1)>0
sg_off=sg & (ndimage.distance_transform_edt(~gt)>3) & foot
def block_stats(pred, g, nb=8):
    H,W=g.shape; bh,bw=H//nb+1,W//nb+1
    # credit per GT px
    d=ndimage.distance_transform_edt(~pred); credit=np.clip(1-d/3,0,1)
    dd=ndimage.distance_transform_edt(~g); fpw=np.clip(1-dd/3,0,1)
    stats={}
    for by in range(nb):
        for bx in range(nb):
            ys=slice(by*bh,min(H,(by+1)*bh)); xs=slice(bx*bw,min(W,(bx+1)*bw))
            tp=float(credit[ys,xs][g[ys,xs]].sum()) if g[ys,xs].any() else 0.0
            fn=float(g[ys,xs].sum()-credit[ys,xs][g[ys,xs]].sum()) if g[ys,xs].any() else 0.0
            fp=float(fpw[ys,xs][pred[ys,xs]].sum()) if pred[ys,xs].any() else 0.0
            stats[(by,bx)]=(tp,fp,fn)
    return stats
def boot(a,b,g,rng,n=2000):
    A=block_stats(a,g); B=block_stats(b,g); keys=list(A)
    da=[];
    for _ in range(n):
        sel=rng.choice(len(keys),size=len(keys),replace=True)
        def dti(S):
            tp=sum(S[keys[i]][0] for i in sel); fp=sum(S[keys[i]][1] for i in sel); fn=sum(S[keys[i]][2] for i in sel)
            return tp/(tp+0.2*fp+0.8*fn+1e-12)
        da.append(dti(A)-dti(B))
    da=np.array(da); return {"delta_mean":round(float(da.mean()),5),"ci95":[round(float(np.percentile(da,2.5)),5),round(float(np.percentile(da,97.5)),5)],"p_delta_gt0":round(float((da>0).mean()),4)}
rng=np.random.default_rng(42)
out={"sgmc_candidate_vs_champion32":boot(cand,champ,sg_off,rng), "sgmc_candidate_vs_best_champ27":boot(cand,champ27,sg_off,rng)}
print(json.dumps(out,indent=1)); json.dump(out,open("registry/bootstrap_ci.json","w"),indent=1)
