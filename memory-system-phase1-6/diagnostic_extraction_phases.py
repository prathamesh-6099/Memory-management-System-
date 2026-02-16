"""
Diagnostic to check why Phase 1/2 aren't catching payment reminder conversations
"""
from src.extractor import MemoryExtractor

# Sample messages from payment reminder conversations
test_messages = [
    "Hello, am I speaking with Johnson?",
    "Good afternoon, Johnson. This is Sarah calling from ABC Financial Services.",
    "I'm calling regarding your account ending in 4582.",
    "Your payment of $450 was due on February 5th.",
    "I completely understand. Life gets hectic sometimes.",
    "Would you like to make the payment now over the phone?",
    "I can make the payment right now actually.",
    "I'm reaching out about your outstanding balance of $1,200.",
    "I've been going through some financial difficulties.",
    "We can offer you a payment extension of 15 days.",
    "Can I set up a payment plan for you?",
    "Wait, $875? That doesn't sound right.",
    "I never requested any upgrade!",
    "I already paid that bill three days ago!",
    "Yes, the payment has been received and is currently being processed.",
]

def diagnose_extraction():
    """Test extraction phases on payment reminder messages"""
    extractor = MemoryExtractor()
    
    print("\n" + "="*90)
    print("EXTRACTION PHASE DIAGNOSTIC")
    print("="*90 + "\n")
    
    print(f"Stage 3 (LLM) Enabled: {extractor.stage3_enabled}")
    print(f"Stage 3 Confidence Threshold: 0.7\n")
    
    phase1_pass = 0
    phase2_extract = 0
    phase3_trigger = 0
    total = len(test_messages)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*90}")
        print(f"Message {i}: {message}")
        print(f"{'='*90}")
        
        # Check Phase 1 (Sensory Filter)
        should_process, heuristic_score = extractor.should_extract(message)
        
        print(f"\n📋 PHASE 1: Sensory Filter")
        print(f"  Heuristic Score: {heuristic_score:.3f}")
        print(f"  Threshold:       0.3")
        print(f"  Pass Phase 1:    {'✓ YES' if should_process else '✗ NO (FILTERED OUT)'}")
        
        if not should_process:
            print(f"  ⚠️  Message filtered out - never reaches Phase 2/3")
            continue
        
        phase1_pass += 1
        
        # Check Phase 2 (Pattern Matching)
        stage2_memories = extractor.classify_and_extract(message, turn_number=i)
        
        print(f"\n📋 PHASE 2: Pattern Matching")
        print(f"  Memories Found:  {len(stage2_memories)}")
        
        if stage2_memories:
            phase2_extract += 1
            for mem in stage2_memories:
                print(f"    - Type: {mem['type']}, Key: {mem['key']}, Value: {mem['value']}, Confidence: {mem['confidence']:.2f}")
            
            max_confidence = max(m['confidence'] for m in stage2_memories)
            print(f"  Max Confidence:  {max_confidence:.2f}")
            print(f"  Stage 3 Thresh:  0.7")
            
            if max_confidence < 0.7:
                print(f"  ⚠️  Low confidence → Will escalate to Phase 3 LLM")
                phase3_trigger += 1
            else:
                print(f"  ✓ High confidence → Phase 2 sufficient, no LLM needed")
        else:
            print(f"  No matches found")
            print(f"  Heuristic score: {heuristic_score:.2f} > 0.5: {heuristic_score > 0.5}")
            if heuristic_score > 0.5:
                print(f"  ⚠️  Will escalate to Phase 3 LLM (message looks important)")
                phase3_trigger += 1
            else:
                print(f"  ✓ No extraction needed")
    
    # Summary
    print("\n" + "="*90)
    print("SUMMARY")
    print("="*90 + "\n")
    
    print(f"Total Messages:              {total}")
    print(f"Phase 1 Pass (not filtered): {phase1_pass} ({phase1_pass/total*100:.1f}%)")
    print(f"Phase 2 Extracted:           {phase2_extract} ({phase2_extract/total*100:.1f}%)")
    print(f"Phase 3 LLM Triggers:        {phase3_trigger} ({phase3_trigger/total*100:.1f}%)")
    print(f"No Extraction Needed:        {total - phase1_pass} ({(total-phase1_pass)/total*100:.1f}%)")
    
    print("\n📊 KEY FINDINGS:\n")
    
    if phase1_pass < total * 0.5:
        print(f"⚠️  Phase 1 PROBLEM: {total - phase1_pass} messages ({(total-phase1_pass)/total*100:.1f}%) filtered out")
        print(f"   → Many payment reminder messages are too short or lack keywords")
        print(f"   → Need to tune SENSORY_FILTER_THRESHOLD or add payment keywords\n")
    
    if phase3_trigger > total * 0.3:
        print(f"⚠️  Phase 3 OVERUSE: {phase3_trigger} messages ({phase3_trigger/total*100:.1f}%) trigger LLM")
        print(f"   → Phase 2 patterns don't match payment reminder structure")
        print(f"   → Need patterns for: account numbers, amounts, dates, etc.\n")
    
    if phase2_extract < total * 0.3:
        print(f"⚠️  Phase 2 WEAK: Only {phase2_extract} messages ({phase2_extract/total*100:.1f}%) extracted by patterns")
        print(f"   → Pattern matching is too specific (looking for 'my name is', 'I prefer')")
        print(f"   → Payment reminders use different language ('account ending in', 'payment of')\n")
    
    print("="*90 + "\n")

if __name__ == "__main__":
    diagnose_extraction()
