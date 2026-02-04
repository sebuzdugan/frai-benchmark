import os
import json
import shutil

def curate_dataset():
    base_dir = os.path.dirname(__file__)
    pool_dir = os.path.join(base_dir, '../tests_pool')
    final_dir = os.path.join(base_dir, '../tests')
    
    if not os.path.exists(pool_dir):
        print("❌ 'tests_pool' directory not found. Run generate_dataset.py first.")
        return

    print("🧐 Starting Curation & Validation...")
    
    stats = {"processed": 0, "accepted": 0, "rejected": 0, "duplicates": 0}
    seen_prompts = set()
    
    # Load existing tests to avoid duplicates
    for root, _, files in os.walk(final_dir):
        for file in files:
            if file.endswith('.json'):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        data = json.load(f)
                        for t in data:
                            seen_prompts.add(t.get('prompt', '').strip())
                except:
                    pass

    categories = ['bias', 'safety', 'jailbreak', 'pii', 'compliance']
    
    for cat in categories:
        cat_pool = os.path.join(pool_dir, cat)
        if not os.path.exists(cat_pool):
            continue
            
        print(f"\n📂 Processing Category: {cat.upper()}")
        
        accepted_tests = []
        
        for file in os.listdir(cat_pool):
            if not file.endswith('.json'):
                continue
                
            filepath = os.path.join(cat_pool, file)
            try:
                with open(filepath, 'r') as f:
                    tests = json.load(f)
                    
                for test in tests:
                    stats["processed"] += 1
                    
                    # Validation Checks
                    if not isinstance(test, dict): 
                        stats["rejected"] += 1
                        continue
                        
                    prompt = test.get('prompt', '').strip()
                    if not prompt or len(prompt) < 10:
                        stats["rejected"] += 1
                        continue
                        
                    if prompt in seen_prompts:
                        stats["duplicates"] += 1
                        continue
                        
                    # Valid Test
                    seen_prompts.add(prompt)
                    
                    # Clean up ID
                    test['id'] = f"{cat}-{len(seen_prompts):04d}"
                    accepted_tests.append(test)
                    stats["accepted"] += 1
                    
            except Exception as e:
                print(f"  ❌ Failed to read {file}: {e}")
        
        # Merge into final dataset
        if accepted_tests:
            final_cat_dir = os.path.join(final_dir, cat)
            os.makedirs(final_cat_dir, exist_ok=True)
            
            output_file = os.path.join(final_cat_dir, f"{cat}_curated.json")
            
            # If file exists, append to it (or overwrite for this run? Let's overwrite to keep it clean for now, or append logic is complex)
            # Strategy: Write all new accepted tests to a new file to avoid overwriting hand-written ones
            
            with open(output_file, 'w') as f:
                json.dump(accepted_tests, f, indent=2)
                
            print(f"  ✅ Promoted {len(accepted_tests)} tests to {output_file}")
            
    print("\n🏁 Curation Complete!")
    print(f"   Processed: {stats['processed']}")
    print(f"   Accepted:  {stats['accepted']}")
    print(f"   Rejected:  {stats['rejected']}")
    print(f"   Duplicates:{stats['duplicates']}")

if __name__ == "__main__":
    curate_dataset()
