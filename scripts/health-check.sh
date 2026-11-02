#!/bin/bash
set -euo pipefail

# =============================================================================
# Moodle Health Check Script
# Verifica se o Moodle está respondendo corretamente em uma URL fornecida.
# Uso: ./health-check.sh [URL]
# Exemplo: ./health-check.sh http://localhost:8080
# =============================================================================

URL="${1:-http://localhost:8080}"

# Cores ANSI
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color (reset)

MAX_RETRIES=3
RETRY_DELAY=30
EXIT_CODE=0

# Rastreia qual verificação falhou (para diagnóstico)
FAILED_CHECK=""

# -----------------------------------------------------------------------------
# Funções auxiliares
# -----------------------------------------------------------------------------

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_failure() {
    echo -e "${RED}[✗]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[…]${NC} $1"
}

# -----------------------------------------------------------------------------
# check_health: executa as 3 verificações em sequência
# Retorna 0 se todas passaram, 1 caso contrário.
# Em caso de falha, define a variável FAILED_CHECK.
# -----------------------------------------------------------------------------

check_health() {
    local attempt="$1"
    log_info "Tentativa ${attempt}/${MAX_RETRIES} — verificando ${URL} …"

    # Verificação (a): HTTP 200 na URL raiz
    local http_root
    http_root=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${URL}" || true)
    if [[ "$http_root" != "200" ]]; then
        FAILED_CHECK="raiz"
        log_failure "Verificação (a) falhou: URL raiz retornou HTTP ${http_root} (esperado 200)"
        return 1
    fi

    # Verificação (b): HTTP 200 em /login/index.php
    local http_login
    http_login=$(curl -f -s -o /dev/null -w "%{http_code}" --max-time 10 \
        --retry 3 --retry-delay 5 "${URL}/login/index.php" || true)
    if [[ "$http_login" != "200" ]]; then
        FAILED_CHECK="login"
        log_failure "Verificação (b) falhou: /login/index.php retornou HTTP ${http_login} (esperado 200)"
        return 1
    fi

    # Verificação (c): presença da string "Moodle" no corpo da URL raiz
    local body
    body=$(curl -s --max-time 10 "${URL}" || true)
    if ! echo "$body" | grep -qi "moodle"; then
        FAILED_CHECK="conteudo"
        log_failure "Verificação (c) falhou: string 'Moodle' não encontrada no corpo da resposta"
        return 1
    fi

    return 0
}

# -----------------------------------------------------------------------------
# Diagnóstico: exibe mensagem detalhada com sugestão de troubleshooting
# -----------------------------------------------------------------------------

show_diagnosis() {
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
    echo -e "${RED} Diagnóstico: health check falhou após ${MAX_RETRIES} tentativas${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

    case "$FAILED_CHECK" in
        raiz)
            echo "  Verificação falhou: URL raiz (${URL})"
            echo "  Possíveis causas:"
            echo "    • O contêiner Moodle não está em execução."
            echo "    • A porta mapeada (ex: 8080) não está acessível."
            echo "    • O servidor ainda está inicializando (aguarde 2-3 min após 'docker compose up')."
            echo "  Sugestões:"
            echo "    $ docker compose ps"
            echo "    $ docker compose logs moodle --tail=50"
            ;;
        login)
            echo "  Verificação falhou: página de login (${URL}/login/index.php)"
            echo "  Possíveis causas:"
            echo "    • Moodle iniciou mas ainda está configurando o banco de dados."
            echo "    • Erro de conexão entre Moodle e PostgreSQL."
            echo "  Sugestões:"
            echo "    $ docker compose logs moodle --tail=50"
            echo "    $ docker compose logs db --tail=20"
            ;;
        conteudo)
            echo "  Verificação falhou: conteúdo HTML não contém 'Moodle'"
            echo "  Possíveis causas:"
            echo "    • A URL aponta para um servidor errado (proxy, página de erro, etc.)."
            echo "    • Instalação do Moodle está incompleta ou corrompida."
            echo "  Sugestões:"
            echo "    $ curl -s ${URL} | head -50"
            echo "    $ docker compose logs moodle --tail=50"
            ;;
        *)
            echo "  Falha desconhecida. Verifique os logs dos contêineres."
            echo "    $ docker compose logs --tail=50"
            ;;
    esac

    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
}

# TODO: Adicione verificações extras conforme necessário para seu ambiente.
# Exemplos de melhorias que podem ser implementadas:
#   1. Checar a página de login com credenciais reais (ex.: via curl --data com
#      usuário/senha) e validar redirecionamento para o dashboard.
#   2. Verificar se a API REST do Moodle responde: ${URL}/webservice/rest/server.php
#   3. Testar latência: garantir que o tempo de resposta seja inferior a um limite.
#   4. Enviar notificação (Slack/e-mail) em caso de falha persistente.

# -----------------------------------------------------------------------------
# Loop principal com retry
# -----------------------------------------------------------------------------

for attempt in $(seq 1 "$MAX_RETRIES"); do
    if check_health "$attempt"; then
        log_success "Moodle está respondendo em ${URL}"
        EXIT_CODE=0
        break
    else
        if [[ "$attempt" -lt "$MAX_RETRIES" ]]; then
            log_info "Aguardando ${RETRY_DELAY}s antes da próxima tentativa…"
            sleep "$RETRY_DELAY"
        else
            log_failure "Moodle não está respondendo em ${URL}"
            show_diagnosis
            EXIT_CODE=1
        fi
    fi
done

exit "$EXIT_CODE"
