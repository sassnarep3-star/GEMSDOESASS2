raise SystemExit('Legacy release path disabled: its partial registry and private holdout do not satisfy the current protocol. See docs/research/concurrent-main.md and scripts/check_registry.py.')

import numpy as np, rasterio, json, glob
from scipy import ndimage
import sys; sys.path.insert(0,"src")
from gemsass2.metric import dti_components
from scipy.stats import spearmanr
cand="/tmp/candidate.tif"; surf=np.load("/tmp/final_surface.npy")
with rasterio.open(cand) as ds: dots=ds.read(1)>0
with rasterio.open("/tmp/registry/labels.tif") as ds: gt=ds.read(1)==1
with rasterio.open("/tmp/registry/sample_submission.tif") as ds: foot=np.isfinite(ds.read(1))
# SGMC off-catalogue instrument
with rasterio.open("/tmp/g24/data/external/derived_sgmc_faults_100m_u8.tif") as ds: sg=ds.read(1)>0
print("sgmc raw",int(sg.sum()))
dgt=ndimage.distance_transform_edt(~gt)
sg_off = sg & (dgt>3) & foot
print("sgmc offcat >3px",int(sg_off.sum()))
def score(d, g):
    tp,fp,fn=dti_components(d,g); return round(float(tp/(tp+0.2*fp+0.8*fn+1e-12)),5)
out={"candidate_sgmc_offcat_DTI":score(dots, sg_off), "dots":int(dots.sum())}
rows=[]
for p in sorted(glob.glob("/tmp/registry/champ*.tif"))+["/tmp/registry/champion32.tif"]:
    with rasterio.open(p) as ds: a=ds.read(1)
    d=a>0
    # overlap: % our dots within 3px of theirs
    dist=ndimage.distance_transform_edt(~d)
    ov=float((dist[dots]<=3).mean()) if dots.sum() else 0
    # spearman on sampled footprint pixels (surface vs their binary)
    rng=np.random.default_rng(1); idx=rng.choice(np.where(foot.ravel())[0], size=150000, replace=False)
    rho,_=spearmanr(surf.ravel()[idx], a.ravel()[idx])
    rows.append({"file":p.split("/")[-1],"dots":int(d.sum()),"our_dot_overlap_3px":round(ov,4),"surface_spearman":round(float(rho),4),"sgmc_offcat_DTI":score(d, sg_off)})
    print(rows[-1], flush=True)
out["registry"]=rows
out["max_overlap"]=max(r["our_dot_overlap_3px"] for r in rows)
out["max_abs_spearman"]=max(abs(r["surface_spearman"]) for r in rows)
out["unique_pass_le70_rho90"] = bool(out["max_overlap"]<=0.70 and out["max_abs_spearman"]<=0.90)
json.dump(out, open("registry/uniqueness_sgmc.json","w"), indent=1)
print(json.dumps(out,indent=1))
