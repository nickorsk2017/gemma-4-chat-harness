# SETTINGS.md — Global Config

## Limits
max_iterations: 2          # allowed FAIL re-routes; escalate when iteration >= this
escalate_to: Engineer

## Complexity Gates
LOW:    [Engineer, Executor, Validator]
MEDIUM: [Engineer, Planner, Executor, Validator]
HIGH:   [Engineer, Planner, EngineerApproval, Executor, Validator]

## Classification Rules
LOW:    files_touched <= 1 AND new_dependencies == 0 AND no_schema_change
MEDIUM: files_touched > 1 OR new_module
HIGH:   schema_change OR infra_change OR security_surface OR public_api_change

## Modes
mode: strict               # strict = artifact-only memory enforced
approval_required_for: [HIGH]
auto_advance: true         # advance stage when actor completes cleanly

## Token Optimization
verbose_artifacts: false
duplicate_context: forbidden
full_rewrites: only_if_structural
keep_version_history: true    # append ## v<n> blocks, never delete old ones
routing_source: STATE.yaml   # single source of truth
diff_style: incremental

## Defaults
default_status: PENDING
default_iteration: 0
default_stage: INIT
