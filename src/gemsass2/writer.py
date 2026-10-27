import rasterio, numpy as np, hashlib, json
def write_submission(arr, template_path, out_path):
    with rasterio.open(template_path) as t:
        prof = t.profile.copy()
    prof.update(driver="GTiff", count=1, dtype="float32", nodata=None, compress="deflate", tiled=True, blockxsize=256, blockysize=256)
    a = np.asarray(arr, dtype=np.float32)
    assert a.shape==(prof["height"], prof["width"]), a.shape
    assert np.isfinite(a).all() and a.min()>=0.0 and a.max()<=1.0, (a.min(), a.max())
    with rasterio.open(out_path,"w",**prof) as ds:
        ds.write(a,1)
    return hashlib.sha256(open(out_path,'rb').read()).hexdigest()
