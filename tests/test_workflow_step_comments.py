# Feature: moodle-docker-aws-challenge, Property 6
"""
Property-based tests for GitHub Actions workflow step documentation.

**Validates: Requirements 6.4**

Property 6: All steps in every workflow file have a `name:` field.
A `name:` field is used as the proxy for a descriptive comment/label
that documents what each step does.
"""

import pathlib
import yaml
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / ".github" / "workflows"


def _collect_run_steps() -> list[tuple[pathlib.Path, str, int, dict]]:
    """Return all (workflow_path, job_name, step_index, step) tuples
    where the step contains a `run:` key.
    """
    entries = []
    for wf_file in sorted(WORKFLOWS_DIR.glob("*.yml")):
        with wf_file.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            continue
        jobs = data.get("jobs") or {}
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps") or []
            for idx, step in enumerate(steps):
                if isinstance(step, dict) and "run" in step:
                    entries.append((wf_file, job_name, idx, step))
    return entries


# ---------------------------------------------------------------------------
# Property 6 — all run: steps have a name: field
# ---------------------------------------------------------------------------

RUN_STEPS = _collect_run_steps()


@pytest.mark.skipif(
    len(RUN_STEPS) == 0,
    reason="No run: steps found in .github/workflows/*.yml",
)
@given(entry=st.sampled_from(RUN_STEPS))
@settings(max_examples=100)
def test_all_run_steps_have_name(entry):
    """Property 6: every `run:` step in any workflow file must have a `name:` field.

    **Validates: Requirements 6.4**
    """
    wf_path, job_name, step_index, step = entry

    assert "name" in step, (
        f"Workflow '{wf_path.name}', job '{job_name}', step index {step_index} "
        f"has a `run:` instruction but is missing a `name:` field.\n"
        f"Step content: {step}"
    )
    assert step["name"].strip() != "", (
        f"Workflow '{wf_path.name}', job '{job_name}', step index {step_index} "
        f"has an empty `name:` field."
    )
