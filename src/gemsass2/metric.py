"""Distance-weighted Tversky (DTI) alpha=0.2 beta=0.8, R=3px triangular kernel.
Formulation (DrivenData #306 problem page; kernel-max form):
 TPw = sum over GT px of max-dot k(d), k(d)=max(1-d/3,0)
 FNw = sum over GT px of (1 - that credit)
 FPw = sum over dot px of (1 - max-GT k(d))
DTI = TPw / (TPw + 0.2*FPw + 0.8*FNw)
"""
import numpy as np
from scipy import ndimage

def dti_components(pred_binary, gt_binary):
    pred = pred_binary.astype(bool); gt = gt_binary.astype(bool)
    if gt.sum()==0:
        return 0.0,0.0,0.0
    # distance from each GT px to nearest dot
    if pred.sum()==0:
        return 0.0, 0.0, float(gt.sum())
    d_gt = ndimage.distance_transform_edt(~pred)
    credit = np.clip(1.0 - d_gt[gt]/3.0, 0, 1)
    tp = float(credit.sum()); fn = float((1-credit).sum())
    d_dot = ndimage.distance_transform_edt(~gt)
    fp = float(np.clip(1.0 - d_dot[pred]/3.0, 0, 1).sum())
    return tp, fp, fn

def dti(pred_binary, gt_binary):
    tp,fp,fn = dti_components(pred_binary, gt_binary)
    return tp/(tp+0.2*fp+0.8*fn+1e-12), (tp,fp,fn)
