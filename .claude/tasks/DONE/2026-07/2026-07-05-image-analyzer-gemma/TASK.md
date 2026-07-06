# TASK — 2026-07-05-image-analyzer-gemma
owner: Engineer
immutable: true

## Requirements
- R1: image_analyzer's three tools (describe_image, detect_objects, ocr_image) run through
  the real multimodal gemma model (google/gemma-4-31b-it @ NVIDIA endpoint) via the shared
  `agent_core.llm` factory and the agent's existing `llm_*` settings (GEMMA_API_KEY).
- R2: The image file is read locally and sent as a base64 data-URL content part in an
  OpenAI-style multimodal message; responses parse into existing schemas
  (Caption, DetectionResult, OcrResult) via structured output.
- R3: No mock LLM/vision fallback (same policy as 2026-07-05-remove-mock-llm): mock vision
  branches and NotImplementedError removed; dead vision_provider/vision_api_key/ocr_provider
  settings removed from config.py and mcp/.env.example.
- R4: detect_objects filters LLM detections by min_confidence in code; prompts note that
  VLM boxes/confidences are estimates. Prompts live in image_analyzer/prompts/.
- R5: tools/image_tools.py stays thin and unchanged; no hardcoded keys.

## Acceptance
- A1: (stub runtime) each provider builds the gemma model once (nvidia/gemma/NVIDIA
  base_url), sends [text, image_url(base64 data URL)] parts, returns schema-typed result;
  detect_objects drops detections below min_confidence.
- A2: No vision_provider/ocr_provider/vision_api_key refs remain in mcp/ (source check);
  changed files compile; no nvapi- in tracked files.

## Constraints
- No live network calls in validation. Scope: image_analyzer/ + mcp/.env.example only.
