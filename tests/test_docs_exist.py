"""
Property-based tests for required documentation file existence in docs/.

Feature: moodle-docker-aws-challenge, Property 7
"""

# Feature: moodle-docker-aws-challenge, Property 7

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Resolve workspace root relative to this file
REPO_ROOT = Path(__file__).parent.parent

DOCS_DIR = REPO_ROOT / "docs"

# Required documentation files that must exist in the docs/ directory.
REQUIRED_DOCS = [
    "architecture-design-template.md",
    "architecture.md",
    "aws-learn-lab-setup.md",
    "terraform-guide.md",
    "troubleshooting.md",
    "evaluation-rubric.md",
    "security-practices.md",
]


# ---------------------------------------------------------------------------
# Property 7: Arquivos de documentação obrigatórios existem no diretório docs/
# Feature: moodle-docker-aws-challenge, Property 7
# Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.1
# ---------------------------------------------------------------------------


@given(doc_file=st.sampled_from(REQUIRED_DOCS))
@settings(max_examples=100)
def test_required_docs_exist(doc_file: str) -> None:
    """
    Property 7: Arquivos de documentação obrigatórios existem no diretório docs/.

    For any required documentation file, the file must exist in the docs/
    directory.

    Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.1
    """
    assert DOCS_DIR.is_dir(), (
        f"Expected docs/ directory to exist at {DOCS_DIR}, but it was not found."
    )

    doc_path = DOCS_DIR / doc_file
    assert doc_path.is_file(), (
        f"Expected required documentation file '{doc_file}' to exist in docs/, "
        f"but it was not found at {doc_path}."
    )


# ---------------------------------------------------------------------------
# Smoke tests — verify each required documentation file exists individually
# ---------------------------------------------------------------------------

_docs_exists = DOCS_DIR.is_dir()


@pytest.mark.skipif(not _docs_exists, reason=(
    "docs/ directory does not exist yet — create the documentation "
    "before running this test."
))
@pytest.mark.parametrize("doc_file", REQUIRED_DOCS)
def test_doc_file_exists(doc_file: str) -> None:
    """
    Smoke test: each required documentation file exists in docs/.

    Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.1
    """
    doc_path = DOCS_DIR / doc_file
    assert doc_path.is_file(), (
        f"Missing required documentation file '{doc_file}' in docs/. "
        f"Expected path: {doc_path}"
    )
