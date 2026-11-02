"""
Property-based tests for Terraform module stub structure.

Feature: moodle-docker-aws-challenge, Property 5
"""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Resolve workspace root relative to this file
_REPO_ROOT = Path(__file__).parent.parent

MODULES_DIR = _REPO_ROOT / "terraform" / "modules"

_terraform_exists = MODULES_DIR.exists()

# Required files that every Terraform module stub must contain
REQUIRED_FILES = ["main.tf", "variables.tf", "outputs.tf"]


# ---------------------------------------------------------------------------
# Property 5: Cada módulo Terraform stub contém os três arquivos obrigatórios
# Feature: moodle-docker-aws-challenge, Property 5
# Validates: Requirements 3.4
# ---------------------------------------------------------------------------


@given(module_name=st.sampled_from(["networking", "compute", "database"]))
@settings(max_examples=100)
def test_terraform_module_has_required_files(module_name: str) -> None:
    """
    Property 5: Cada módulo Terraform stub contém os três arquivos obrigatórios.

    For any module directory in {networking, compute, database}, the directory
    must contain main.tf, variables.tf, and outputs.tf.

    Validates: Requirements 3.4
    """
    if not _terraform_exists:
        pytest.skip(
            "terraform/modules/ não existe ainda — crie a estrutura de módulos "
            "antes de executar este teste."
        )

    module_dir = MODULES_DIR / module_name
    assert module_dir.is_dir(), (
        f"Expected module directory '{module_dir}' to exist, but it was not found."
    )

    for required_file in REQUIRED_FILES:
        file_path = module_dir / required_file
        assert file_path.is_file(), (
            f"Module '{module_name}' is missing required file '{required_file}'. "
            f"Expected path: {file_path}"
        )


# ---------------------------------------------------------------------------
# Smoke tests — verify specific required files exist for each module
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _terraform_exists, reason=(
    "terraform/modules/ não existe ainda — crie a estrutura de módulos "
    "antes de executar este teste."
))
@pytest.mark.parametrize("module_name", ["networking", "compute", "database"])
@pytest.mark.parametrize("required_file", REQUIRED_FILES)
def test_terraform_module_file_exists(module_name: str, required_file: str) -> None:
    """
    Smoke test: each required file exists for every Terraform module stub.

    Validates: Requirements 3.4
    """
    file_path = MODULES_DIR / module_name / required_file
    assert file_path.is_file(), (
        f"Missing required file '{required_file}' in module '{module_name}'. "
        f"Expected path: {file_path}"
    )
