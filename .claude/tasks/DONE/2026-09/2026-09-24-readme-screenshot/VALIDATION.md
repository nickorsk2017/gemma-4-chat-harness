# VALIDATION — 2026-09-24-readme-screenshot
validation_version: 2
result: PASS

## v1
- A1 FAIL: docs/screenshot.png is 375591 bytes, SHA-1 1900873f...; provided image is 369821 bytes, SHA-1 90c94705.... Not byte-identical.
- A2 PASS: line 1 of README.md is the image link; relative path resolves.
- A3 PASS: README diff adds only the 2-line prepend; the other hunk predates this task.
- A4 PASS.

## v2
result: PASS
- A1 PASS: docs/screenshot.png 369821 bytes, SHA-1 90c94705..., identical to the provided image.
- A2 PASS: README.md line 1 = `![Gemma 4 chat UI](docs/screenshot.png)`.
- A3 PASS: README.md diff from this task is the 2-line prepend only.
- A4 PASS.
