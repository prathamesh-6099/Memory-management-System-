"""Quick test of distance sweep retrieval"""
import json
from src.memory_system import MemorySystem

# Initialize
ms = MemorySystem('test_distance_quick')
ms.clear_memories()

# Load and process
with open('evaluation/fixtures/distance_sweep_test.json') as f:
    data = json.load(f)

# Process all turns
for turn in data['turns']:
    if not turn.get('is_query'):
        ms.process_turn(turn['message'])

# Query
_, stats = ms.process_turn('Tell me everything you remember')
mems = stats.get('active_memories', [])

print(f"\nRetrieved {len(mems)} memories:")
for m in mems[:10]:
    turn = m.get('origin_turn', 0)
    mtype = m.get('type', 'unknown')
    content = m.get('content', '')
    print(f"  Turn {turn:4d}: {mtype:12s} - {content[:60]}")

# Check ground truth
print(f"\n\nGround truth expectations:")
for gt in data['ground_truth_memories']:
    print(f"  Turn {gt['turn']:4d} (distance={gt['test_distance']:4d}): {gt['type']:12s} - {gt['value']}")

# Check if any match
print(f"\n\nMatching analysis:")
for gt in data['ground_truth_memories']:
    found = False
    for m in mems:
        if abs(m.get('origin_turn', 0) - gt['turn']) <= 2:
            found = True
            break
    status = "✓" if found else "✗"
    print(f"  {status} Distance {gt['test_distance']:4d} (turn {gt['turn']:4d}): {found}")
