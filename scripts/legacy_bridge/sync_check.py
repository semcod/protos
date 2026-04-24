"""
sync_check.py – CLI tool to check if legacy and proto schemas are in sync.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from legacy_registry import LegacySchemaRegistry
from legacy_bridge.normalizer import normalize_json_schema, normalize_proto_ast
from legacy_bridge.diff_engine import diff_fields


def main():
    reg = LegacySchemaRegistry()
    l = reg.get_latest('user.legacy', 'json_schema')
    p = reg.get_latest('user.v1', 'proto')
    
    if not l or not p:
        print("Error: Missing latest schemas for sync check.")
        sys.exit(1)
        
    lf = normalize_json_schema(l.schema_dict)
    pf = normalize_proto_ast(p.schema_dict['messages'][0])
    r = diff_fields(lf, pf)
    
    if r.readiness < 1.0:
        print(f"OUT OF SYNC: {r.readiness*100:.1f}%")
        for entry in r.entries:
            if entry.severity == "ERROR":
                print(f"  - {entry.message}")
        sys.exit(1)
        
    print("LEGACY SYNC OK")


if __name__ == "__main__":
    main()
