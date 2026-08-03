from omega_millennium_t.r02.core import benchmark,campaign
import json
print(json.dumps({"benchmark":benchmark(),"campaign":campaign(4096)},sort_keys=True,indent=2))
