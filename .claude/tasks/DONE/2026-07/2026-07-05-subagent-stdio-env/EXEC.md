# EXEC — 2026-07-05-subagent-stdio-env
## v1
config.py: to_connection() adds "env": dict(os.environ) for stdio connections (full parent
env incl. GEMMA_API_KEY, LANGSMITH_*, PATH); http branch unchanged. 1 file.
