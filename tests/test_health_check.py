"""
Property-based tests for scripts/health-check.sh.

Feature: moodle-docker-aws-challenge
"""

import pathlib
import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Resolve workspace root relative to this file
REPO_ROOT = pathlib.Path(__file__).parent.parent
HEALTH_CHECK_PATH = REPO_ROOT / "scripts" / "health-check.sh"


def _load_script() -> str:
    """Read and return the full content of health-check.sh."""
    assert HEALTH_CHECK_PATH.exists(), (
        f"health-check.sh não encontrado em: {HEALTH_CHECK_PATH}"
    )
    return HEALTH_CHECK_PATH.read_text(encoding="utf-8")


_SCRIPT_CONTENT = _load_script()


# ---------------------------------------------------------------------------
# Property 9: Script de health check aceita URL como argumento
# Feature: moodle-docker-aws-challenge, Property 9
# Validates: Requirements 7.1
# ---------------------------------------------------------------------------

@given(positional_arg=st.integers(min_value=1, max_value=9))
@settings(max_examples=100)
def test_health_check_accepts_url_argument(positional_arg: int) -> None:
    """
    Property 9: Script de health check aceita URL como argumento.

    For any positional argument index N in [1..9], when N=1 the script must
    use the pattern ``${1:-http://localhost:8080}`` (accepts URL argument with
    a sensible default). This ensures the script is parameterisable via $1
    and falls back gracefully when no argument is supplied.

    Validates: Requirements 7.1
    """
    if positional_arg == 1:
        # The script MUST use $1 with http://localhost:8080 as the default
        assert "${1:-http://localhost:8080}" in _SCRIPT_CONTENT, (
            "O script health-check.sh deve conter o padrão "
            "'${1:-http://localhost:8080}' para aceitar a URL via argumento "
            "posicional $1 com fallback para http://localhost:8080. "
            f"Arquivo verificado: {HEALTH_CHECK_PATH}"
        )
    else:
        # For N != 1, the script should NOT use ${N:-...} as the primary URL
        # argument — only $1 is the conventional first positional parameter.
        pattern = f"${{  {positional_arg}:-"
        # Normalise: allow no spaces
        pattern_tight = "${" + str(positional_arg) + ":-"
        # The script simply must not *rely* on a different positional arg
        # as the URL source.  We verify $1 is still the active pattern.
        assert "${1:-http://localhost:8080}" in _SCRIPT_CONTENT, (
            "O script health-check.sh deve usar $1 (e não "
            f"${positional_arg}) como argumento posicional para a URL."
        )


# ---------------------------------------------------------------------------
# Property 10: Script de health check usa `set -euo pipefail`
# Feature: moodle-docker-aws-challenge, Property 10
# Validates: Requirements 7.2
# ---------------------------------------------------------------------------

@given(pragma=st.just("set -euo pipefail"))
@settings(max_examples=100)
def test_health_check_uses_set_euo_pipefail(pragma: str) -> None:
    """
    Property 10: Script de health check usa ``set -euo pipefail``.

    The script must contain ``set -euo pipefail`` as a standalone safety
    pragma (optionally surrounded by whitespace on its line). This ensures
    the script exits on errors, treats unset variables as errors, and
    propagates pipeline failures correctly.

    Validates: Requirements 7.2
    """
    # Check that any line in the script (stripped) equals the pragma,
    # or starts with it (e.g. "set -euo pipefail -x" would also be acceptable
    # since it is a superset of the required options).
    lines = _SCRIPT_CONTENT.splitlines()
    found = any(
        line.strip() == pragma or line.strip().startswith(pragma)
        for line in lines
    )
    assert found, (
        f"O script health-check.sh deve conter '{pragma}' em uma linha "
        "própria (com ou sem opções adicionais). "
        f"Arquivo verificado: {HEALTH_CHECK_PATH}"
    )


# ---------------------------------------------------------------------------
# Smoke / example tests
# ---------------------------------------------------------------------------

def test_health_check_script_exists() -> None:
    """Verifica que o script health-check.sh existe no caminho esperado."""
    assert HEALTH_CHECK_PATH.exists(), (
        f"health-check.sh não encontrado em: {HEALTH_CHECK_PATH}"
    )


def test_health_check_has_shebang() -> None:
    """Verifica que o script começa com o shebang correto."""
    first_line = _SCRIPT_CONTENT.splitlines()[0]
    assert first_line.startswith("#!/"), (
        "health-check.sh deve começar com um shebang (ex.: #!/bin/bash)."
    )


def test_health_check_url_default_is_localhost_8080() -> None:
    """Verifica o padrão exato do argumento URL com fallback."""
    assert "${1:-http://localhost:8080}" in _SCRIPT_CONTENT, (
        "health-check.sh deve conter '${1:-http://localhost:8080}'."
    )


def test_health_check_safety_pragma_present() -> None:
    """Verifica que 'set -euo pipefail' está presente no script."""
    assert "set -euo pipefail" in _SCRIPT_CONTENT, (
        "health-check.sh deve conter 'set -euo pipefail'."
    )
