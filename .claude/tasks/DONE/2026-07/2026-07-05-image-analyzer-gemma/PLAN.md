# PLAN — 2026-07-05-image-analyzer-gemma

## v1

### Design
D1. prompts/vision.py: keep DESCRIBE_IMAGE; replace unused OCR_CLEANUP with OCR_IMAGE
    (direct VLM OCR, "{lang}" hint, "return text exactly as seen"); add DETECT_OBJECTS
    (list objects with label, confidence 0..1, normalized [x1,y1,x2,y2] box; state that
    values are model estimates).
D2. tools/providers.py rewrite:
    - cached `_chat_model()` from settings.llm_* via build_chat_model (same pattern as
      web_agent/doc_analyzer).
    - `_image_part(path)`: read bytes, base64; mime from suffix (png/jpeg/webp/gif,
      default jpeg) -> {"type":"image_url","image_url":{"url":"data:<mime>;base64,<b64>"}}.
    - `_vision_invoke(prompt, path, schema)`: HumanMessage(content=[text, image part]) ->
      model.with_structured_output(schema).ainvoke([msg]).
    - describe_image -> Caption; ocr_image -> OcrResult; detect_objects -> DetectionResult
      then `detections = [d for d in r.detections if d.confidence >= min_confidence]`.
D3. config.py: drop vision_provider/vision_api_key/ocr_provider (dead); keep llm block.
    mcp/.env.example: drop IMAGE_ANALYZER_VISION_* lines, note GEMMA_API_KEY.
D4. pyproject.toml: + langchain-core>=0.3.0 (HumanMessage, BaseChatModel).

### Files touched (5)
image_analyzer/{tools/providers.py, prompts/vision.py, config.py, pyproject.toml},
mcp/.env.example

### Validation
py_compile; source asserts (A2); stub runtime for all three providers incl. base64 data-URL
content part and min_confidence filtering.
