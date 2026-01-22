import json
import os
import sys
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ValidationError

# Define Schema
class TestCase(BaseModel):
    id: str
    category: str = Field(pattern=r"^(bias|safety|jailbreak|pii|compliance)$")
    subcategory: str
    prompt: str
    expected_behavior: str = Field(pattern=r"^(refusal|compliant_response|neutral)$")
    reference_answer: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../tests')

def validate_files(directory: str):
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                full_path = os.path.join(root, file)
                print(f"Validating {file}...")
                
                try:
                    with open(full_path, 'r') as f:
                        content = json.load(f)
                    
                    # Validate list of test cases
                    if not isinstance(content, list):
                        raise ValueError("Root element must be a list of test cases")
                    
                    for item in content:
                        TestCase(**item)
                        
                    print(f"✅ {file} is valid.")
                
                except (ValidationError, json.JSONDecodeError, ValueError) as e:
                    print(f"❌ Validation failed for {file}: {e}")
                    sys.exit(1)

if __name__ == "__main__":
    print("Starting test validation...")
    validate_files(TESTS_DIR)
    print("Validation complete.")
