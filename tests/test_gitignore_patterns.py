"""
Property-based tests for .gitignore coverage of sensitive file patterns.

Feature: moodle-docker-aws-challenge
"""

import subprocess
import tempfile
import os
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Resolve workspace root relative to this file
REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Property 3: .gitignore cobre todos os padrões de arquivos sensíveis
# Feature: moodle-docker-aws-challenge, Property 3
# Validates: Requirements 2.6
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    "*.tfvars",
    "terraform.tfstate",
    "terraform.tfstate.backup",
    ".env",
    "*.pem",
    "*.key",
    "id_rsa",
]


@given(pattern=st.sampled_from(SENSITIVE_PATTERNS))
@settings(max_examples=100)
def test_gitignore_covers_sensitive_patterns(pattern: str) -> None:
    """
    Property 3: .gitignore cobre todos os padrões de arquivos sensíveis.

    For any sensitive pattern in {*.tfvars, terraform.tfstate,
    terraform.tfstate.backup, .env, *.pem, *.key, id_rsa}, the .gitignore
    file must contain a corresponding line.

    Validates: Requirements 2.6
    """
    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file must exist at the repository root"

    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    # Strip whitespace and ignore comment lines
    effective_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    assert pattern in effective_lines, (
        f"Expected pattern '{pattern}' to be present in .gitignore, "
        f"but it was not found. Effective lines: {effective_lines}"
    )


# ---------------------------------------------------------------------------
# Property 4: Git ignora arquivos com nomes sensíveis
# Feature: moodle-docker-aws-challenge, Property 4
# Validates: Requirements 2.7
# ---------------------------------------------------------------------------

# Generators for filenames matching each sensitive pattern.
# Start character must be alphanumeric to avoid git option-parsing issues
# (filenames beginning with "-" are misinterpreted as flags by git).
_safe_start = st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
_safe_rest = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_"),
    min_size=0,
    max_size=19,
)

_pem_names = st.builds(lambda a, b: f"{a}{b}.pem", _safe_start, _safe_rest)

_key_names = st.builds(lambda a, b: f"{a}{b}.key", _safe_start, _safe_rest)

_tfstate_name = st.just("terraform.tfstate")

_id_rsa_name = st.just("id_rsa")

_sensitive_filenames = st.one_of(_pem_names, _key_names, _tfstate_name, _id_rsa_name)


@given(filename=_sensitive_filenames)
@settings(max_examples=100)
def test_git_ignores_sensitive_filenames(filename: str) -> None:
    """
    Property 4: Git ignora arquivos com nomes sensíveis.

    For any filename matching patterns *.pem, *.key, id_rsa or
    terraform.tfstate, the git check-ignore command must return that file
    as ignored (exit code 0).

    Validates: Requirements 2.7
    """
    # Filenames must not contain path separators or null bytes for this test
    assume("/" not in filename and "\x00" not in filename and filename.strip() == filename)

    # We need to create the file temporarily so git check-ignore can evaluate it
    with tempfile.NamedTemporaryFile(
        dir=REPO_ROOT,
        prefix=f"_pbt_test_{filename}_",
        suffix="",
        delete=False,
    ) as tmp:
        # Rename to the exact target filename inside the repo root
        tmp_path = Path(tmp.name)

    try:
        # Move the temp file to the exact name we want to check
        target_path = REPO_ROOT / filename
        # Only proceed if it doesn't already exist (avoid clobbering real files)
        assume(not target_path.exists())
        tmp_path.rename(target_path)

        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", filename],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
        assert result.returncode == 0, (
            f"Expected git to ignore '{filename}' (exit 0 from git check-ignore), "
            f"but got exit code {result.returncode}. "
            f"stdout={result.stdout.decode()!r}, stderr={result.stderr.decode()!r}"
        )
    finally:
        # Clean up: remove created file if it still exists
        final_path = REPO_ROOT / filename
        if final_path.exists():
            final_path.unlink()
        if tmp_path.exists():
            tmp_path.unlink()
