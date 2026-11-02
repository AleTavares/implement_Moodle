# Feature: moodle-docker-aws-challenge, Property 2
# Property 2: Todos os arquivos de configuração contêm ao menos um comentário TODO
# Validates: Requirements 2.4
#
# Para qualquer arquivo de configuração (extensões: .yml, .yaml, .tf, .sh,
# .env.example) presente nos diretórios docker/ e terraform/, ele deve conter
# ao menos um comentário "# TODO:".

import pathlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Caminho raiz do repositório (sem fixture — conftest.py ainda não existe)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent

# Extensões de arquivo que devem ter pelo menos um comentário # TODO:
_CONFIG_EXTENSIONS = {".yml", ".yaml", ".tf", ".sh", ".env.example"}

# Diretórios onde os arquivos de configuração devem existir
_CONFIG_DIRS = [
    _REPO_ROOT / "docker",
    _REPO_ROOT / "terraform",
]

# Marcador de TODO obrigatório
_TODO_MARKER = "# TODO:"

# Arquivos excluídos da verificação de TODO:
# terraform/versions.tf é o único arquivo .tf pré-preenchido e funcional no template
# — não contém stubs nem marcadores # TODO: por design (ver design.md, seção 3).
_EXCLUDED_FILES = {
    _REPO_ROOT / "terraform" / "versions.tf",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_config_file(path: pathlib.Path) -> bool:
    """
    Retorna True se o arquivo tem uma extensão de configuração monitorada.
    Trata '.env.example' como extensão composta verificando o nome completo.
    """
    if path.name.endswith(".env.example"):
        return True
    return path.suffix in _CONFIG_EXTENSIONS


def _collect_config_files() -> list[pathlib.Path]:
    """
    Varre os diretórios docker/ e terraform/ recursivamente e retorna
    todos os arquivos de configuração existentes (excluindo .gitkeep,
    arquivos sem extensão reconhecida e arquivos da lista de exclusões).

    Arquivos com extensões .gitkeep ou sem extensão reconhecida são ignorados.
    Diretórios terraform/ que contêm apenas .gitkeep são tratados como vazios.

    Exclusões explícitas:
    - terraform/versions.tf: único arquivo .tf pré-preenchido e funcional;
      não contém stubs nem # TODO: por design (ver design.md, seção 3).
    """
    found: list[pathlib.Path] = []
    for base_dir in _CONFIG_DIRS:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name == ".gitkeep":
                continue
            if path in _EXCLUDED_FILES:
                continue
            if _is_config_file(path):
                found.append(path)
    return found


def _has_todo_comment(path: pathlib.Path) -> bool:
    """Retorna True se o arquivo contém ao menos uma linha com '# TODO:'."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return _TODO_MARKER in content


# ---------------------------------------------------------------------------
# Coleta feita uma única vez para toda a suite
# ---------------------------------------------------------------------------
_CONFIG_FILES = _collect_config_files()


# ---------------------------------------------------------------------------
# Property 2 — Hypothesis
# ---------------------------------------------------------------------------

# Cria a estratégia somente se houver arquivos; caso contrário usa placeholder.
_files_for_hypothesis = (
    st.sampled_from(_CONFIG_FILES)
    if _CONFIG_FILES
    else st.just(None)
)


@given(config_file=_files_for_hypothesis)
@settings(max_examples=100)
def test_config_files_have_todo_comment(config_file: pathlib.Path | None) -> None:
    """
    Property 2: Para qualquer arquivo de configuração presente nos diretórios
    docker/ e terraform/, ele deve conter ao menos um comentário '# TODO:'.

    Validates: Requirements 2.4
    """
    # Caso de lista vazia: propriedade vacuamente verdadeira
    if config_file is None:
        return

    assert _has_todo_comment(config_file), (
        f"O arquivo de configuração '{config_file.relative_to(_REPO_ROOT)}' "
        f"não contém nenhum comentário '# TODO:'. "
        f"Todos os arquivos de configuração devem guiar o aluno com ao menos "
        f"um marcador '# TODO:' indicando o que deve ser configurado ou preenchido."
    )


# ---------------------------------------------------------------------------
# Smoke tests adicionais (determinísticos)
# ---------------------------------------------------------------------------

def test_docker_directory_exists() -> None:
    """Verifica que o diretório docker/ existe."""
    assert (_REPO_ROOT / "docker").exists(), (
        "Diretório docker/ não encontrado na raiz do repositório."
    )


def test_docker_compose_has_todo() -> None:
    """Verifica especificamente que o docker-compose.yml contém # TODO:."""
    compose_path = _REPO_ROOT / "docker" / "docker-compose.yml"
    assert compose_path.exists(), f"docker-compose.yml não encontrado em: {compose_path}"
    assert _has_todo_comment(compose_path), (
        "docker-compose.yml deve conter ao menos um comentário '# TODO:'."
    )


def test_env_example_has_todo() -> None:
    """Verifica especificamente que o .env.example contém # TODO:."""
    env_path = _REPO_ROOT / "docker" / ".env.example"
    assert env_path.exists(), f".env.example não encontrado em: {env_path}"
    assert _has_todo_comment(env_path), (
        "docker/.env.example deve conter ao menos um comentário '# TODO:'."
    )


@pytest.mark.parametrize("config_file", _CONFIG_FILES if _CONFIG_FILES else [None])
def test_each_config_file_has_todo_comment(config_file: pathlib.Path | None) -> None:
    """
    Testes parametrizados que verificam cada arquivo de configuração individualmente.
    Complementam o property test com mensagens de erro mais diretas.
    """
    if config_file is None:
        pytest.skip("Nenhum arquivo de configuração encontrado nos diretórios monitorados.")
        return
    assert _has_todo_comment(config_file), (
        f"'{config_file.relative_to(_REPO_ROOT)}' não contém '# TODO:'."
    )
