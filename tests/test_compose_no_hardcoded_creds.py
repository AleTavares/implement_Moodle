# Feature: moodle-docker-aws-challenge, Property 8
# Property 8: docker-compose.yml não contém credenciais em texto literal
# Validates: Requirements 8.4
#
# Para qualquer variável de ambiente no docker-compose.yml cujo nome
# corresponda a um campo de credencial (PASSWORD, SECRET, KEY, TOKEN),
# o valor declarado deve usar interpolação de variável (${VAR_NAME}) e não
# um literal string codificado diretamente no arquivo.

import pathlib
import re

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Caminho para o docker-compose.yml (sem fixture — conftest.py ainda não existe)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent
_COMPOSE_PATH = _REPO_ROOT / "docker" / "docker-compose.yml"

# Sufixos de credenciais que indicam dados sensíveis (case-insensitive)
_CREDENTIAL_KEYWORDS = ("PASSWORD", "SECRET", "KEY", "TOKEN")

# Padrão que indica interpolação de variável de ambiente (${VAR_NAME})
_INTERPOLATION_PATTERN = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_compose() -> dict:
    """Carrega e retorna o docker-compose.yml como dicionário Python."""
    assert _COMPOSE_PATH.exists(), (
        f"docker-compose.yml não encontrado em: {_COMPOSE_PATH}"
    )
    with _COMPOSE_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _collect_credential_env_vars(compose: dict) -> list[tuple[str, str | None]]:
    """
    Percorre todos os serviços do docker-compose.yml e retorna uma lista de
    (NOME_VAR, valor_declarado) para cada variável cujo nome contém ao menos
    um dos keywords de credencial.

    Aceita tanto o formato de lista quanto o de mapeamento para `environment`.
    """
    results: list[tuple[str, str | None]] = []
    services = compose.get("services", {}) or {}

    for _service_name, service_def in services.items():
        env_section = (service_def or {}).get("environment")
        if not env_section:
            continue

        if isinstance(env_section, dict):
            items = env_section.items()
        elif isinstance(env_section, list):
            # Cada item pode ser "NAME=value" ou somente "NAME"
            parsed = {}
            for entry in env_section:
                if "=" in str(entry):
                    k, _, v = str(entry).partition("=")
                    parsed[k.strip()] = v.strip()
                else:
                    parsed[str(entry).strip()] = None
            items = parsed.items()
        else:
            continue

        for name, value in items:
            upper_name = name.upper()
            if any(keyword in upper_name for keyword in _CREDENTIAL_KEYWORDS):
                results.append((name, value))

    return results


def _value_is_safe(value: str | None) -> bool:
    """
    Retorna True se o valor é considerado seguro:
    - None / vazio (variável sem valor declarado no compose)
    - Usa interpolação ${VAR_NAME} (exatamente um placeholder, sem literal adicional)
    """
    if value is None or value == "":
        return True
    return bool(_INTERPOLATION_PATTERN.match(str(value).strip()))


# ---------------------------------------------------------------------------
# Carrega os dados uma única vez para toda a suite
# ---------------------------------------------------------------------------
_COMPOSE_DATA = _load_compose()
_CRED_VARS = _collect_credential_env_vars(_COMPOSE_DATA)


# ---------------------------------------------------------------------------
# Property 8 — Hypothesis
# ---------------------------------------------------------------------------

@given(entry=st.sampled_from(_CRED_VARS if _CRED_VARS else [("__no_cred_vars__", None)]))
@settings(max_examples=100)
def test_compose_credential_vars_use_interpolation(entry: tuple[str, str | None]) -> None:
    """
    Property 8: Para qualquer variável de ambiente no docker-compose.yml
    cujo nome contenha um keyword de credencial (PASSWORD, SECRET, KEY, TOKEN),
    o valor declarado deve usar interpolação ${VAR_NAME} e não um literal
    hardcoded.

    Validates: Requirements 8.4
    """
    # Caso especial: não há variáveis de credencial no arquivo (propriedade vacuamente verdadeira)
    if entry[0] == "__no_cred_vars__":
        return

    name, value = entry
    assert _value_is_safe(value), (
        f"A variável de credencial '{name}' no docker-compose.yml contém um "
        f"valor literal hardcoded: {value!r}. "
        f"Use interpolação de variável de ambiente no formato ${{VAR_NAME}} "
        f"em vez de valores literais."
    )


# ---------------------------------------------------------------------------
# Smoke tests adicionais (determinísticos)
# ---------------------------------------------------------------------------

def test_compose_file_exists() -> None:
    """Verifica que o docker-compose.yml existe no caminho esperado."""
    assert _COMPOSE_PATH.exists(), (
        f"docker-compose.yml não encontrado em: {_COMPOSE_PATH}"
    )


def test_compose_has_services() -> None:
    """Verifica que o docker-compose.yml declara ao menos um serviço."""
    services = _COMPOSE_DATA.get("services") or {}
    assert len(services) > 0, "docker-compose.yml deve declarar ao menos um serviço."


@pytest.mark.parametrize("name,value", _CRED_VARS if _CRED_VARS else [("__no_cred_vars__", None)])
def test_each_credential_var_uses_interpolation(name: str, value: str | None) -> None:
    """
    Testes parametrizados que verificam cada variável de credencial individualmente.
    Complementam o property test com mensagens de erro mais diretas.
    """
    if name == "__no_cred_vars__":
        return
    assert _value_is_safe(value), (
        f"Variável '{name}' tem valor literal hardcoded: {value!r}. "
        f"Use ${{VAR_NAME}} para evitar credenciais em texto claro no compose."
    )
