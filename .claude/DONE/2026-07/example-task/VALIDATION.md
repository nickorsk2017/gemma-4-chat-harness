# VALIDATION — example-task
validation_version: 1
author: Validator
exec_ref: 1

result: PASS

## Checks
- R1..R3: met
- A1: 6th attempt -> 429  ok
- A2: window reset via EXPIRE  ok
- A3: success path unchanged  ok

## Issues
[]   # {id,type,severity,ref,note} — empty on PASS
