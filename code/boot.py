# usage: boot.py a24|a22 [top]  -> appends bootstrap sum-draws to boot_<d>.npy until 1000 rows; resumable
import sys, os, time, numpy as np
sys.argv_ = sys.argv
from analyze_lib import load, F
d = sys.argv[1]; top = len(sys.argv) > 2
pl, T, A = load(d, top_only=top)
cols = [T[k] for k in F] + [T['n']] + [A['jl'][k] for k in ('core', 'n')] + [A['md'][k] for k in ('core', 'n')]
M = np.stack(cols, 1).astype(np.float32)
fn = f'boot_{d}{"_top" if top else ""}.npy'
R = np.load(fn) if os.path.exists(fn) else np.zeros((0, M.shape[1]), np.float32)
rng = np.random.default_rng(20261120 + len(R) + (7 if d == 'a22' else 0) + (3 if top else 0))
t0 = time.time(); chunk = 50
while len(R) < 1000 and time.time() - t0 < 140:
    W = rng.poisson(1.0, size=(chunk, M.shape[0])).astype(np.float32)
    R = np.vstack([R, W @ M]); np.save(fn, R)
print(fn, len(R))
