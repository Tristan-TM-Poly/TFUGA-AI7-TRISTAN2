"""Minimal Ω-ROOTFLOW-T∞ demo: z^3 - 3z + t."""

import numpy as np

from omega_rootflow_t import audit_rootflow, continue_roots, root_jacobian, roots

start = np.array([0.0, -3.0, 0.0, 1.0])
end = np.array([1.0, -3.0, 0.0, 1.0])
rr = roots(start)
print("roots(t=0):", rr)
print("dr/da at t=0:\n", root_jacobian(start, rr))
result = continue_roots(start, end, steps=20)
print("roots(t=1):", result.final_roots)
print("audit(t=1):", audit_rootflow(end).to_dict())
