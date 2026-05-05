import json
import sys

spec = json.load(sys.stdin)
paths = spec.get('paths', {})
for path in sorted(paths.keys()):
    print(path)
