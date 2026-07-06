"""Prompts for image_analyzer."""

DESCRIBE_IMAGE = (
    "You are a precise visual describer. Look at the attached image ('{path}') and "
    "produce one clear caption that states the main subject, setting, and any notable "
    "actions. Be factual and avoid speculation. Set path to '{path}'."
)

DETECT_OBJECTS = (
    "You are an object detector. List every distinct object you can see in the attached "
    "image ('{path}'). For each: a short lowercase label, your confidence from 0 to 1, "
    "and a normalized bounding box [x1, y1, x2, y2] with values 0..1. Confidences and "
    "boxes are your best visual estimates. Set path to '{path}'."
)

OCR_IMAGE = (
    "You are an OCR engine. Read the attached image ('{path}') and transcribe ALL "
    "visible text exactly as written (language hint: {lang}), preserving line breaks "
    "and order; do not add, translate, or correct content. If there is no text, return "
    "an empty string. Set path to '{path}'."
)
