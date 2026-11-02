"""
Property-based tests for docs/architecture-design-template.md sections.

Feature: moodle-docker-aws-challenge, Property 11
"""

# Feature: moodle-docker-aws-challenge, Property 11

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Resolve workspace root relative to this file
REPO_ROOT = Path(__file__).parent.parent

# Required section headings that must appear as lines in the template file
REQUIRED_SECTIONS = [
    "## Visão Geral",
    "## Diagrama de Arquitetura",
    "## Decisões de Design",
    "## Componentes",
    "## Segurança",
    "## Escalabilidade",
    "## Custo Estimado",
]

TEMPLATE_PATH = REPO_ROOT / "docs" / "architecture-design-template.md"


# ---------------------------------------------------------------------------
# Property 11: Template de arquitetura contém todas as seções obrigatórias
# Feature: moodle-docker-aws-challenge, Property 11
# Validates: Requirements 5.1, 5.2, 5.5
# ---------------------------------------------------------------------------


@given(section=st.sampled_from(REQUIRED_SECTIONS))
@settings(max_examples=100)
def test_architecture_template_contains_required_sections(section: str) -> None:
    """
    Property 11: Template de arquitetura contém todas as seções obrigatórias.

    For any required section heading in REQUIRED_SECTIONS, the file
    docs/architecture-design-template.md must contain a corresponding
    Markdown heading as a line (after stripping whitespace).

    Validates: Requirements 5.1, 5.2, 5.5
    """
    assert TEMPLATE_PATH.exists(), (
        f"Template file must exist at {TEMPLATE_PATH}"
    )

    lines = TEMPLATE_PATH.read_text(encoding="utf-8").splitlines()
    stripped_lines = [line.strip() for line in lines]

    assert section in stripped_lines, (
        f"Expected section heading '{section}' to appear as a line in "
        f"{TEMPLATE_PATH.relative_to(REPO_ROOT)}, but it was not found."
    )
