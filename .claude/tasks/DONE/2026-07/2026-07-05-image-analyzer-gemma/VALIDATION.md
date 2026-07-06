# VALIDATION — 2026-07-05-image-analyzer-gemma

## v1 — PASS
Sandbox without PyPI: py_compile + source asserts + stub runtime; no network.

- A1 PASS: all three providers invoke the gemma factory exactly once with
  {nvidia, google/gemma-4-31b-it, NVIDIA base_url, key}; message = [text part with prompt,
  image_url part with correct data:image/png;base64 payload (byte-exact round-trip)];
  results are schema-typed; detect_objects drops detections < min_confidence (0.3 filtered
  at threshold 0.5); OCR prompt carries the lang hint.
- A2 PASS: zero refs to vision_provider/vision_api_key/ocr_provider under mcp/; changed
  files compile; `git grep nvapi-` empty.
- EXEC deviation accepted: mcp/.env.example fully de-mocked (stale lines contradicted
  task 2026-07-05-remove-mock-llm) — consistent with R3 intent.

Residual risk (non-blocking): gemma's vision quality for detection boxes/OCR is a model
property, not verifiable offline; boxes are estimates by design. Smoke-test with a real
image on the keyed environment.
