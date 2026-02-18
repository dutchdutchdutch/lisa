# Test Layer Classification

## Purpose

Classify every test file in the project into a **layer** so that LISA can enforce execution order, scope tests to the current story, and prevent the agent from chasing failures in the wrong layer.

## Layers

| Layer | What belongs here | Examples |
|-------|------------------|----------|
| **UNIT** | Isolated logic tests. No external dependencies, no network, no database. Pure function tests, state tests, utility tests. | `test_analysis.py`, `test_utils.py`, `test_state.py` |
| **INTEGRATION** | Tests that validate interaction between modules or services. Contract tests, API tests, pact tests, component tests. | `test_output_contracts.py`, `test_api_*.py` |

## Classification Rules (in priority order)

1. **Custom rules first.** If the project defines custom layer rules in `.lisa/config.json` under `test_layers.custom_rules`, those take absolute precedence.
2. **Path patterns.** A test file living under a path that matches a layer pattern is assigned to that layer.
   - INTEGRATION: `tests/integration/`, `tests/api/`, `tests/contract/`, `tests/pact/`, `tests/component/`
   - UNIT: `tests/unit/`, `tests/` (flat — default)
3. **Naming conventions.** A test file whose name matches a layer pattern is assigned to that layer.
   - INTEGRATION: `*_contract_test.py`, `*_pact_test.py`, `*_api_test.py`, `*_component_test.py`, `test_*_contract.py`, `test_*_pact.py`, `test_*_api.py`, `test_*_component.py`
4. **Markers/decorators.** If a Python test file contains `@pytest.mark.integration` or a class-level `layer = "integration"` attribute, classify as INTEGRATION.
5. **Default.** Any test file (`test_*.py` or `*_test.py`) that matches no INTEGRATION rule defaults to **UNIT**. A warning is emitted so the developer knows the classification was inferred.

## Integration Sub-Types

INTEGRATION tests are tagged with a sub-type when detectable:

| Sub-Type | Detection Pattern |
|----------|------------------|
| CONTRACT | Path contains `contract/` or filename contains `contract` |
| API | Path contains `api/` or filename contains `api` |
| PACT | Path contains `pact/` or filename contains `pact` |
| COMPONENT | Path contains `component/` or filename contains `component` |

Sub-types are **informational only** — the layer gate treats all INTEGRATION tests uniformly.

## Persistence

Classification results are written to `.lisa/layers.json` so that downstream commands (`lisa scope`, `lisa verify-pass`) can reference them without re-scanning.

## Agent Instructions

When asked to classify tests, think step by step:

1. Discover all test files in the project (files matching `test_*.py` or `*_test.py`).
2. For each file, apply rules in priority order: custom rules → path patterns → naming conventions → markers → default.
3. Tag INTEGRATION files with their sub-type if detectable.
4. Persist the result to `.lisa/layers.json`.
5. Report the classification grouped by layer with counts.
