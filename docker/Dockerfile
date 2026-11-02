# =============================================================================
# Dockerfile — Moodle 4.1 customizado com extensões PHP obrigatórias
# Base: php:8.1-apache (imagem oficial PHP com Apache)
#
# Referência de extensões obrigatórias:
#   https://moodledev.io/docs/gettingstarted/requirements
#
# Requisitos: 1.5 (Moodle 4.1+), 1.11 (extensões PHP obrigatórias), 2.4 (# TODO:)
# =============================================================================

FROM php:8.1-apache

# -----------------------------------------------------------------------------
# Instala as dependências de sistema necessárias para as extensões PHP
# e ferramentas utilitárias do ambiente de produção
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # pkg-config — necessário para que o configure do PHP encontre as bibliotecas
    pkg-config \
    # Dependência de oniguruma para a extensão mbstring (codificação multibyte)
    libonig-dev \
    # Dependência de libzip para a extensão zip
    libzip-dev \
    # Dependência de libicu para a extensão intl (internacionalização)
    libicu-dev \
    # Dependência de libpq para a extensão pdo_pgsql (PostgreSQL)
    libpq-dev \
    # Dependências de libpng e libjpeg para a extensão gd (imagens)
    libpng-dev \
    libjpeg-dev \
    # Dependência de libsodium para a extensão sodium (criptografia Moodle 4.1+)
    libsodium-dev \
    # Dependência de libxml2 para a extensão simplexml
    libxml2-dev \
    # Dependência de libcurl para a extensão curl
    libcurl4-openssl-dev \
    # Ferramentas de rede e utilitários gerais
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Configura e instala a extensão gd com suporte a JPEG
# (precisa de configuração prévia ao install para habilitar libjpeg)
# -----------------------------------------------------------------------------
RUN docker-php-ext-configure gd --with-jpeg

# -----------------------------------------------------------------------------
# Instala as extensões PHP obrigatórias para o Moodle 4.x
#
# Extensões NÃO instaladas aqui pois já vêm embutidas no PHP:
#   - iconv   (built-in)
#   - openssl (built-in)
#   - ctype   (built-in)
#   - zlib    (built-in)
#   - json    (built-in no PHP 8+)
# -----------------------------------------------------------------------------
RUN docker-php-ext-install \
    # Codificação multibyte de strings (obrigatório para i18n no Moodle)
    mbstring \
    # Cliente HTTP (utilizado para integração de plugins e notificações)
    curl \
    # Compressão/descompressão de arquivos ZIP (upload de plugins/cursos)
    zip \
    # Parsing de XML simples (feeds RSS e comunicação SOAP)
    simplexml \
    # Internacionalização e formatação de datas/números por locale
    intl \
    # Driver PDO para PostgreSQL (conexão com o banco de dados)
    pdo_pgsql \
    # Processamento de imagens (thumbnails, avatares de usuários)
    gd \
    # Cache de opcodes PHP (melhora performance de produção)
    opcache \
    # Funções criptográficas modernas (obrigatório no Moodle 4.1+)
    sodium

# TODO: Adicione aqui extensões PHP opcionais necessárias para plugins adicionais.
# Exemplos de extensões comuns em ambientes Moodle avançados:
#
#   RUN docker-php-ext-install xmlrpc   # Integração com sistemas externos via XML-RPC
#   RUN pecl install redis && docker-php-ext-enable redis  # Cache Redis/sessões distribuídas
#   RUN pecl install apcu  && docker-php-ext-enable apcu   # Cache local APCu (alternativa ao Redis)
#   RUN docker-php-ext-install ldap     # Autenticação via LDAP/Active Directory

# -----------------------------------------------------------------------------
# Configura o OPcache com parâmetros recomendados para o Moodle em produção
# -----------------------------------------------------------------------------
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.memory_consumption=256'; \
    echo 'opcache.interned_strings_buffer=16'; \
    echo 'opcache.max_accelerated_files=10000'; \
    echo 'opcache.revalidate_freq=60'; \
    echo 'opcache.use_cwd=1'; \
} > /usr/local/etc/php/conf.d/opcache-recommended.ini

# -----------------------------------------------------------------------------
# Configura o PHP com parâmetros recomendados para o Moodle
# (max_input_vars elevado é necessário para formulários longos do Moodle)
# -----------------------------------------------------------------------------
RUN { \
    echo 'max_input_vars=5000'; \
    echo 'post_max_size=128M'; \
    echo 'upload_max_filesize=128M'; \
    echo 'memory_limit=256M'; \
    echo 'max_execution_time=300'; \
} > /usr/local/etc/php/conf.d/moodle-recommended.ini

# -----------------------------------------------------------------------------
# Baixa e instala o Moodle 4.1 a partir do repositório oficial
# O código é extraído em /var/www/html (DocumentRoot padrão do Apache)
# -----------------------------------------------------------------------------
ENV MOODLE_VERSION=4.1

RUN curl -fsSL \
    "https://download.moodle.org/download.php/direct/stable401/moodle-latest-401.tgz" \
    -o /tmp/moodle.tgz \
    && tar -xzf /tmp/moodle.tgz -C /tmp \
    && cp -r /tmp/moodle/. /var/www/html/ \
    && rm -rf /tmp/moodle.tgz /tmp/moodle \
    && chown -R www-data:www-data /var/www/html

# -----------------------------------------------------------------------------
# Cria o diretório moodledata fora do DocumentRoot (exigido pelo Moodle)
# e ajusta permissões para o usuário do Apache
# -----------------------------------------------------------------------------
RUN mkdir -p /var/moodledata \
    && chown -R www-data:www-data /var/moodledata \
    && chmod 0770 /var/moodledata

# -----------------------------------------------------------------------------
# Cria symlink /var/www/moodledata -> /var/moodledata para que o instalador
# web do Moodle encontre o diretório no caminho padrão sem precisar de
# permissões de escrita em /var/www
# -----------------------------------------------------------------------------
RUN ln -s /var/moodledata /var/www/moodledata

# -----------------------------------------------------------------------------
# Habilita os módulos Apache necessários para o Moodle
# (rewrite é obrigatório para URLs limpas)
# -----------------------------------------------------------------------------
RUN a2enmod rewrite

# -----------------------------------------------------------------------------
# Copia o arquivo de configuração do VirtualHost customizado para o Apache
# Nota: o arquivo apache-moodle.conf é opcional; sem ele, o Apache usa o
# VirtualHost padrão que já aponta para /var/www/html
# -----------------------------------------------------------------------------
# COPY apache-moodle.conf /etc/apache2/sites-available/000-default.conf

# Porta exposta pelo contêiner (mapeada para 8080 no host via docker-compose.yml)
EXPOSE 80
