"""Test script for ACT parser."""
import sys
sys.path.insert(0, 'src')

from carmakit_addon.parsers.act_parser import parse_act_file

try:
    act = parse_act_file('src/static/eagle3/EAGLE3.ACT')
    print('Root:', act.root.name if act.root else None)
    print('Root model:', act.root.model_name if act.root else None)
    print('Children:', len(act.root.children) if act.root else 0)
    if act.root:
        for i, c in enumerate(act.root.children[:10]):
            print(f'  {i}: {c.name} model={c.model_name}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
