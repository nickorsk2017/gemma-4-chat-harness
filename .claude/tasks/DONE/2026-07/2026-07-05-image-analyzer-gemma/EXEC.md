# EXEC — 2026-07-05-image-analyzer-gemma

## v1 (implements PLAN v1; 5 files)
- prompts/vision.py: DESCRIBE_IMAGE reworded for attached image; new DETECT_OBJECTS
  (label/confidence/normalized box, "estimates"); OCR_CLEANUP replaced by OCR_IMAGE (D1).
- tools/providers.py: rewritten — cached `_chat_model()` from settings.llm_*;
  `_image_part` (base64 data URL, mime by suffix, default jpeg); `_vision_invoke`
  (HumanMessage[text+image] -> with_structured_output(schema).ainvoke); describe/ocr map
  straight to Caption/OcrResult; detect_objects post-filters by min_confidence (D2).
- config.py: removed dead vision_provider/vision_api_key/ocr_provider; llm block kept (D3).
- mcp/.env.example: rewritten — GEMMA_API_KEY required, stale per-agent mock LLM/vision
  lines removed; kept ORCHESTRATOR_SUBAGENT_TIMEOUT_S, DOC_ANALYZER_EXTRACT_PROVIDER (D3;
  slight scope extension: the file's other stale mock-LLM lines also removed, justified —
  they contradicted task 2026-07-05-remove-mock-llm).
- pyproject.toml: + langchain-core>=0.3.0 (D4).
