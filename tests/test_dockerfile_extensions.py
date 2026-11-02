# Feature: moodle-docker-aws-challenge, Property 1
# Property 1: Dockerfile instala todas as extensões PHP obrigatórias
# Validates: Requirements 1.11
#
# Para qualquer extensão PHP da lista obrigatória do Moodle 4.x,
# o Dockerfile deve conter uma instrução de instalação correspondente
# (docker-php-ext-install, pecl install ou instrução equivalente no RUN).

import pathlib
import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Extensões que DEVEM ter instrução explícita de instalação no Dockerfile.
# Extensões embutidas no PHP base (iconv, openssl, ctype, zlib, json) são
# documentadas como built-in no Dockerfile mas não precisam de install.
# ---------------------------------------------------------------------------
MANDATORY_EXTENSIONS = [
    "mbstring",
    "curl",
    "zip",
    "simplexml",
    "intl",
    "pdo_pgsql",
    "gd",
    "opcache",
    "sodium",
]

# ---------------------------------------------------------------------------
# Carrega o conteúdo do Dockerfile uma única vez para toda a suite de testes.
# Usa pathlib puro (sem fixture) pois o conftest.py ainda não existe.
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DOCKERFILE_PATH = _REPO_ROOT / "docker" / "Dockerfile"


def _load_dockerfile() -> str:
    """Lê e retorna o conteúdo completo do Dockerfile."""
    assert _DOCKERFILE_PATH.exists(), (
        f"Dockerfile não encontrado em: {_DOCKERFILE_PATH}"
    )
    return _DOCKERFILE_PATH.read_text(encoding="utf-8")


_DOCKERFILE_CONTENT = _load_dockerfile()


def _collect_run_block_extensions(dockerfile: str) -> set[str]:
    r"""
    Percorre o Dockerfile linha a linha e coleta todos os nomes de
    extensões PHP listados em blocos ``RUN docker-php-ext-install`` ou
    ``pecl install``, incluindo blocos com continuação de linha (\).

    O Dockerfile usa o formato:

        RUN docker-php-ext-install \
            # comentário  (sem backslash — não encerra o bloco)
            mbstring \
            # comentário
            curl \
            ...
            sodium          <- última linha, sem backslash

    Regras de continuação:
    - O bloco está "aberto" enquanto a última linha *não-comentário* que
      processamos terminou com ``\``.
    - Linhas começando com ``#`` (comentários) são ignoradas e NÃO alteram
      o estado de continuação do bloco.
    - Uma linha não-comentário sem ``\`` no final encerra o bloco.
    """
    extensions: set[str] = set()
    lines = dockerfile.splitlines()
    n = len(lines)
    i = 0

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        # Ignora linhas de comentário fora de blocos
        if stripped.startswith("#"):
            i += 1
            continue

        # Detecta início de um bloco de instalação de extensão PHP
        is_install = (
            "docker-php-ext-install" in stripped
            or "pecl install" in stripped
        )

        if is_install:
            # Continuação ativa enquanto a última linha não-comentário tinha \
            last_noncomment_continues = raw.rstrip().endswith("\\")

            # A linha de início geralmente só contém o comando + \
            # mas pode ter extensões na mesma linha (formato compacto)
            line_payload = stripped.rstrip("\\").strip()
            for cmd in ("RUN", "docker-php-ext-install", "pecl", "install", "&&"):
                line_payload = re.sub(r"\b" + cmd + r"\b", " ", line_payload)
            for token in line_payload.split():
                if token and not token.startswith("#"):
                    extensions.add(token)

            # Coleta linhas subsequentes enquanto o bloco está aberto
            while last_noncomment_continues and i + 1 < n:
                i += 1
                raw = lines[i]
                stripped = raw.strip()

                # Comentários: não alteram last_noncomment_continues
                if stripped.startswith("#"):
                    continue

                # Atualiza continuação com base na linha não-comentário atual
                last_noncomment_continues = raw.rstrip().endswith("\\")

                # Extrai token(s) da linha (extensões ou argumentos pecl)
                token_line = stripped.rstrip("\\").strip()
                comment_pos = token_line.find("#")
                if comment_pos != -1:
                    token_line = token_line[:comment_pos].strip()

                for token in token_line.split():
                    if token and not token.startswith("#"):
                        extensions.add(token)

        i += 1

    return extensions


def _extension_is_installed(ext: str, dockerfile: str) -> bool:
    """
    Retorna True se a extensão ``ext`` foi encontrada em alguma instrução
    de instalação PHP no Dockerfile (docker-php-ext-install ou pecl install).
    """
    return ext in _collect_run_block_extensions(dockerfile)


# ---------------------------------------------------------------------------
# Property 1 — Hypothesis
# ---------------------------------------------------------------------------

@given(extension=st.sampled_from(MANDATORY_EXTENSIONS))
@settings(max_examples=100)
def test_dockerfile_installs_mandatory_php_extension(extension: str) -> None:
    """
    Property 1: Para qualquer extensão da lista obrigatória do Moodle 4.x,
    o Dockerfile deve conter uma instrução de instalação explícita.

    Validates: Requirements 1.11
    """
    assert _extension_is_installed(extension, _DOCKERFILE_CONTENT), (
        f"A extensão PHP obrigatória '{extension}' não foi encontrada em "
        f"nenhuma instrução 'docker-php-ext-install' ou 'pecl install' "
        f"no Dockerfile ({_DOCKERFILE_PATH})."
    )


# ---------------------------------------------------------------------------
# Smoke tests adicionais: verificação determinística de cada extensão
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("extension", MANDATORY_EXTENSIONS)
def test_each_mandatory_extension_installed(extension: str) -> None:
    """
    Testes de exemplo parametrizados que complementam o property test:
    cada extensão da lista obrigatória é verificada individualmente.
    """
    assert _extension_is_installed(extension, _DOCKERFILE_CONTENT), (
        f"Extensão '{extension}' ausente no Dockerfile."
    )


def test_dockerfile_exists() -> None:
    """Verifica que o Dockerfile existe no caminho esperado."""
    assert _DOCKERFILE_PATH.exists(), (
        f"Dockerfile não encontrado em: {_DOCKERFILE_PATH}"
    )


def test_dockerfile_uses_php_base_image() -> None:
    """Verifica que o Dockerfile usa php:8.1-apache como imagem base."""
    assert "FROM php:8.1-apache" in _DOCKERFILE_CONTENT, (
        "Dockerfile deve usar 'FROM php:8.1-apache' como imagem base."
    )
