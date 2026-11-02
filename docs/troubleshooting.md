# Guia de Solução de Problemas

Este documento cobre os problemas mais frequentes que alunos enfrentam no AWS Learn Lab e no ambiente Docker local. Cada entrada segue o padrão: **sintoma → causa provável → solução**.

---

## Sumário

1. [Problemas Docker](#1-problemas-docker)
   - [1.1 Contêiner não sobe (`docker compose up` falha)](#11-contêiner-não-sobe-docker-compose-up-falha)
   - [1.2 Healthcheck do banco de dados falha](#12-healthcheck-do-banco-de-dados-falha)
   - [1.3 Porta 8080 já está em uso](#13-porta-8080-já-está-em-uso)
   - [1.4 Variáveis de ambiente não encontradas](#14-variáveis-de-ambiente-não-encontradas)
2. [Problemas Terraform](#2-problemas-terraform)
   - [2.1 Credenciais AWS expiradas](#21-credenciais-aws-expiradas)
   - [2.2 State lock — erro ao executar `terraform apply`](#22-state-lock--erro-ao-executar-terraform-apply)
   - [2.3 `terraform validate` falha — módulo vazio ou arquivo stub](#23-terraform-validate-falha--módulo-vazio-ou-arquivo-stub)
   - [2.4 Módulo não encontrado (`Module not found`)](#24-módulo-não-encontrado-module-not-found)
   - [2.5 Erro de permissão IAM no `terraform apply`](#25-erro-de-permissão-iam-no-terraform-apply)
3. [Problemas de Conexão EC2 → RDS](#3-problemas-de-conexão-ec2--rds)
   - [3.1 EC2 não consegue se conectar ao RDS (timeout)](#31-ec2-não-consegue-se-conectar-ao-rds-timeout)
   - [3.2 Endpoint do RDS incorreto ou não resolvido](#32-endpoint-do-rds-incorreto-ou-não-resolvido)
4. [Moodle não carrega no browser](#4-moodle-não-carrega-no-browser)
   - [4.1 URL retorna "Connection refused" ou timeout](#41-url-retorna-connection-refused-ou-timeout)
   - [4.2 Página carrega mas exibe erro de banco de dados](#42-página-carrega-mas-exibe-erro-de-banco-de-dados)
   - [4.3 Health check retorna falha após 3 tentativas](#43-health-check-retorna-falha-após-3-tentativas)

---

## 1. Problemas Docker

### 1.1 Contêiner não sobe (`docker compose up` falha)

**Sintoma:**
```
Error response from daemon: Conflict. The container name "/moodle" is already in use.
```
ou
```
ERROR: for moodle  Cannot start service moodle: ...
```

**Causa provável:** Contêiner antigo ainda existe ou imagem corrompida no cache local.

**Solução:**

```bash
# Verificar estado dos contêineres
docker compose ps

# Parar e remover contêineres existentes (preserva volumes)
docker compose down

# Se o problema persistir, forçar reconstrução da imagem
docker compose build --no-cache

# Subir novamente
docker compose up -d

# Verificar logs em tempo real
docker compose logs -f
```

> **Atenção:** `docker compose down -v` remove também os volumes de dados. Use apenas se quiser reiniciar do zero.

---

### 1.2 Healthcheck do banco de dados falha

**Sintoma:**
```
service "db" didn't become healthy in time
```
ou o serviço `moodle` não sobe pois aguarda `db` ficar saudável.

**Causa provável:** O PostgreSQL ainda está inicializando, ou as variáveis de ambiente estão incorretas e o banco não consegue ser criado.

**Solução:**

```bash
# Verificar logs do serviço de banco de dados
docker compose logs db

# Verificar o status do healthcheck
docker inspect --format='{{json .State.Health}}' $(docker compose ps -q db)

# Aguardar inicialização completa (pode levar até 2 minutos na primeira vez)
docker compose up -d db
sleep 30
docker compose logs db | tail -20

# Se o banco falhar por variável incorreta, conferir o arquivo .env
cat docker/.env.example
# Verificar se as variáveis POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB estão definidas
```

---

### 1.3 Porta 8080 já está em uso

**Sintoma:**
```
Error starting userland proxy: listen tcp 0.0.0.0:8080: bind: address already in use
```

**Causa provável:** Outro processo está usando a porta 8080 no host.

**Solução:**

```bash
# Identificar o processo que ocupa a porta
sudo ss -tlnp | grep 8080
# ou
sudo lsof -i :8080

# Encerrar o processo conflitante (substitua <PID> pelo número encontrado)
kill -9 <PID>

# Alternativa: alterar a porta no docker-compose.yml para uma livre (ex: 8081)
# Edite a linha: ports: - "8081:80"

# Subir os contêineres novamente
docker compose up -d
```

---

### 1.4 Variáveis de ambiente não encontradas

**Sintoma:**
```
variable is not set. Defaulting to a blank string.
```
ou o Moodle exibe erro de configuração de banco de dados.

**Causa provável:** O arquivo `.env` não existe no diretório `docker/` e o `.env.example` não está sendo lido como fallback.

**Solução:**

```bash
# Criar o arquivo .env a partir do exemplo
cp docker/.env.example docker/.env

# Editar as senhas com valores seguros antes de subir
nano docker/.env

# Verificar se as variáveis foram carregadas
docker compose config | grep -i password
```

---

## 2. Problemas Terraform

### 2.1 Credenciais AWS expiradas

**Sintoma:**
```
Error: error configuring Terraform AWS Provider: no valid credential sources found
```
ou
```
Error: AuthFailure: AWS was not able to validate the provided access credentials
```

**Causa provável:** As credenciais temporárias do AWS Learn Lab têm validade de aproximadamente 4 horas e expiraram.

**Solução:**

```bash
# Verificar identidade atual (se falhar, as credenciais expiraram)
aws sts get-caller-identity

# Voltar ao portal AWS Academy → "AWS Details" → "AWS CLI"
# Copiar novamente as credenciais temporárias e colar em ~/.aws/credentials:
# [default]
# aws_access_key_id = ASIA...
# aws_secret_access_key = ...
# aws_session_token = ...

# Verificar novamente
aws sts get-caller-identity

# Confirmar que o Terraform usa as credenciais corretas
terraform providers
```

> **Dica:** Rotacione as credenciais antes de completar 3 horas de sessão para evitar interrupções durante o `terraform apply`.

---

### 2.2 State lock — erro ao executar `terraform apply`

**Sintoma:**
```
Error: Error locking state: Error acquiring the state lock
Lock Info:
  ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Operation: OperationTypeApply
```

**Causa provável:** Uma operação Terraform anterior foi interrompida (sessão encerrada, credenciais expiraram) sem liberar o lock na tabela DynamoDB.

**Solução:**

```bash
# Listar informações do lock
terraform force-unlock <LOCK_ID>
# Substitua <LOCK_ID> pelo ID exibido na mensagem de erro

# Verificar e confirmar com 'yes' quando solicitado
# Exemplo:
terraform force-unlock xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Após liberar o lock, verificar o estado atual
terraform show

# Executar o apply novamente
terraform apply
```

> **Atenção:** Só use `force-unlock` se tiver certeza de que nenhuma outra operação está em andamento no mesmo state.

---

### 2.3 `terraform validate` falha — módulo vazio ou arquivo stub

**Sintoma:**
```
Error: Missing required argument
  on modules/networking/main.tf line X:
  ...
```
ou
```
Error: Unsupported argument
```

**Causa provável:** O arquivo stub ainda contém apenas comentários `# TODO:` e o Terraform espera blocos funcionais ao ser chamado do `main.tf` raiz.

**Solução:**

```bash
# Validar apenas os arquivos raiz (versions.tf é o único funcional)
terraform validate

# Se a validação falhar por módulos vazios, verifique se main.tf raiz
# está instanciando módulos que ainda não foram implementados.
# Comente temporariamente os blocos module{} em terraform/main.tf para validar:

# module "networking" {
#   source = "./modules/networking"
#   ...
# }

# Após implementar cada módulo, descomente e valide novamente
terraform fmt
terraform validate
```

---

### 2.4 Módulo não encontrado (`Module not found`)

**Sintoma:**
```
Error: Module not installed
  on main.tf line X, in module "networking":
  Call to undefined module
```

**Causa provável:** `terraform init` não foi executado após adicionar ou modificar referências de módulos.

**Solução:**

```bash
# Executar init para instalar/atualizar módulos e providers
terraform init

# Se usar backend S3, inicializar sem backend para testes locais
terraform init -backend=false

# Verificar se os módulos foram reconhecidos
terraform providers

# Executar validate após init
terraform validate
```

---

### 2.5 Erro de permissão IAM no `terraform apply`

**Sintoma:**
```
Error: error creating VPC: UnauthorizedOperation: You are not authorized to perform this operation.
```
ou
```
AccessDenied: User is not authorized to perform: iam:CreateRole
```

**Causa provável:** O AWS Learn Lab não permite criação de recursos IAM (`aws_iam_role`, `aws_iam_user`) ou uso de serviços restritos (Route 53, ACM, CloudFront).

**Solução:**

```bash
# Confirmar a identidade e role ativa
aws sts get-caller-identity

# Para instâncias EC2, use LabRole via data source em vez de criar uma IAM Role:
# data "aws_iam_instance_profile" "lab_role" {
#   name = "LabRole"
# }

# Remover qualquer bloco aws_iam_role, aws_iam_role_policy ou aws_iam_instance_profile
# dos módulos Terraform. O LabRole já existe no ambiente.

# Serviços NÃO suportados no AWS Learn Lab:
# - aws_route53_* → use DNS público do EC2
# - aws_acm_*     → sem HTTPS customizado no Learn Lab
# - aws_cloudfront_* → não disponível
# - aws_iam_user  → não permitido
```

---

## 3. Problemas de Conexão EC2 → RDS

### 3.1 EC2 não consegue se conectar ao RDS (timeout)

**Sintoma:** O Moodle na EC2 exibe erro de conexão com o banco de dados, ou:
```
psql: error: connection to server at "xxx.rds.amazonaws.com" (x.x.x.x), port 5432 failed: Connection timed out
```

**Causa provável:** O Security Group do RDS não permite tráfego na porta 5432 a partir do Security Group da EC2.

**Solução:**

```bash
# Na EC2, testar conectividade com o endpoint do RDS
nc -zv <rds-endpoint> 5432
# ou
telnet <rds-endpoint> 5432

# Verificar o Security Group do RDS no console AWS:
# - Inbound Rules deve ter: porta 5432, protocolo TCP, source = Security Group da EC2

# Verificar o Security Group pelo AWS CLI
aws ec2 describe-security-groups \
  --group-ids <SG_RDS_ID> \
  --query 'SecurityGroups[*].IpPermissions'

# Se a regra estiver faltando, adicionar via CLI ou console:
aws ec2 authorize-security-group-ingress \
  --group-id <SG_RDS_ID> \
  --protocol tcp \
  --port 5432 \
  --source-group <SG_EC2_ID>
```

---

### 3.2 Endpoint do RDS incorreto ou não resolvido

**Sintoma:**
```
psql: error: could not translate host name "xxx" to address: Name or service not known
```

**Causa provável:** O endpoint do RDS está com um valor errado no arquivo `.env` da EC2, ou o output do Terraform não foi consultado após o `apply`.

**Solução:**

```bash
# Consultar o endpoint correto do RDS via Terraform
terraform output rds_endpoint

# Verificar também pelo AWS CLI
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,Endpoint.Address,Endpoint.Port]' \
  --output table

# Na EC2, verificar o conteúdo do arquivo .env:
cat /opt/moodle/.env | grep DB_HOST

# Atualizar o valor e reiniciar o Moodle
# Editar o .env com o endpoint correto, depois:
docker compose -f /opt/moodle/docker/docker-compose.yml restart moodle
```

---

## 4. Moodle não carrega no browser

### 4.1 URL retorna "Connection refused" ou timeout

**Sintoma:** O browser exibe `ERR_CONNECTION_REFUSED` ou `ERR_CONNECTION_TIMED_OUT` ao acessar o DNS público da EC2 na porta 80.

**Causa provável:** O Security Group da EC2 não libera a porta 80, ou o Docker/Moodle ainda não iniciou na instância.

**Solução:**

```bash
# Verificar se a porta 80 está liberada no Security Group da EC2
aws ec2 describe-security-groups \
  --group-ids <SG_EC2_ID> \
  --query 'SecurityGroups[*].IpPermissions'

# Conectar na EC2 via SSH e verificar se o Docker está rodando
ssh -i <chave.pem> ec2-user@<EC2_DNS>
docker compose ps
docker compose logs moodle | tail -30

# Se o Docker não iniciou, verificar logs do user_data
sudo cat /var/log/cloud-init-output.log | tail -50

# Reiniciar o ambiente Docker manualmente se necessário
cd /opt/moodle
docker compose up -d
```

---

### 4.2 Página carrega mas exibe erro de banco de dados

**Sintoma:** O Moodle abre mas exibe uma mensagem como:
```
Database connection failed. Please check your configuration.
```

**Causa provável:** As variáveis `MOODLE_DATABASE_HOST`, `MOODLE_DATABASE_USER` ou `MOODLE_DATABASE_PASSWORD` no `.env` da EC2 apontam para valores incorretos.

**Solução:**

```bash
# Verificar logs do contêiner Moodle
docker compose logs moodle | grep -i "error\|database\|failed"

# Testar a conexão com o RDS diretamente da EC2
psql -h <rds-endpoint> -U <db_user> -d <db_name> -c '\l'

# Conferir variáveis de ambiente dentro do contêiner
docker compose exec moodle env | grep -i "database\|db"

# Editar o .env com os valores corretos e recriar o contêiner
docker compose down
# (editar o .env)
docker compose up -d
```

---

### 4.3 Health check retorna falha após 3 tentativas

**Sintoma:**
```
[ERRO] Todas as 3 tentativas falharam.
Verificação que falhou: HTTP 200 em /login/index.php
Sugestão: Confirme que o Moodle terminou a instalação inicial (pode levar 5–10 min na primeira vez).
```

**Causa provável:** O Moodle ainda está realizando a instalação inicial do banco de dados — processo que pode demorar vários minutos na primeira execução.

**Solução:**

```bash
# Executar o health check com mais tempo de espera
./scripts/health-check.sh http://<EC2_DNS>

# Acompanhar o progresso da instalação nos logs
docker compose logs -f moodle | grep -i "install\|setup\|complete"

# Se já passou de 10 minutos e ainda falha, verificar:
# 1. Conectividade EC2 → RDS (ver seção 3.1)
# 2. Logs de erro do Moodle
docker compose logs moodle | grep -i "error\|fatal\|exception" | tail -20

# Verificar manualmente se o endpoint responde
curl -v http://<EC2_DNS>/login/index.php 2>&1 | head -30

# Testar presença da string Moodle na página raiz
curl -s http://<EC2_DNS> | grep -i "Moodle"
```

---

## Comandos de Diagnóstico Rápido

Use este checklist quando não souber por onde começar:

```bash
# ── Identidade AWS ──────────────────────────────────────────────
aws sts get-caller-identity

# ── Estado do Terraform ─────────────────────────────────────────
terraform show
terraform output

# ── Logs Docker (ambiente local) ────────────────────────────────
docker compose logs --tail=50

# ── Status dos contêineres ──────────────────────────────────────
docker compose ps

# ── Estado da EC2 ───────────────────────────────────────────────
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,PublicDnsName,State.Name]' \
  --output table

# ── Estado do RDS ───────────────────────────────────────────────
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address]' \
  --output table

# ── Logs de inicialização da EC2 ────────────────────────────────
aws ec2 get-console-output --instance-id <INSTANCE_ID> --output text
```

---

> Não encontrou seu problema aqui? Consulte também:
> - [`docs/aws-learn-lab-setup.md`](aws-learn-lab-setup.md) — restrições e configuração do AWS Learn Lab
> - [`docs/terraform-guide.md`](terraform-guide.md) — referência detalhada dos comandos Terraform
> - [Moodle System Requirements](https://docs.moodle.org/en/Installing_Moodle) — requisitos oficiais do Moodle
> - [AWS EC2 Troubleshooting](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html) — troubleshooting oficial da EC2
