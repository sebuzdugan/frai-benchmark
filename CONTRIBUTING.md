# Contributing to FRAI Benchmark

We welcome contributions!

## How to add a test case
1.  Navigate to `tests/<category>/`.
2.  Create a new JSON file or append to an existing one.
3.  Follow this schema:
    ```json
    {
      "id": "unique-id",
      "prompt": "Your test prompt",
      "expected_behavior": "refusal"
    }
    ```

## Submitting a PR
- Ensure all tests pass validity checks: `npm run validate`.
- Describe the motivation for the new test case.
