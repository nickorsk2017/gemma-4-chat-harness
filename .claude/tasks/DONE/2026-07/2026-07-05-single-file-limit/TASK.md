# TASK — 2026-07-05-single-file-limit
owner: Engineer
immutable: true

## Requirements
- R1: At most ONE file can be attached/sent per message, end to end.
- R2: UI: the composer holds a single attachment; picking another file replaces it.
  Prompt-mandatory rule unchanged.
- R3: Client service and gateway both reject requests with more than one file
  (defense in depth); error text is clear.

## Acceptance
- A1: MessageInput has no `multiple`, keeps max one file; replacement works (source check).
- A2: chatService throws on >1 file before any fetch; gateway /api/chat/files returns a
  Failed envelope on >1 file (stub runtime).
- A3: tsc --noEmit passes; python files compile.
