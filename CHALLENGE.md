# Desafio: Moodle Docker AWS Challenge

## Objetivo

Ao concluir este desafio, você deve ser capaz de:

- **Subir o Moodle localmente com Docker:** executar uma instância do Moodle 4.1+ em contêineres (com PostgreSQL 15) acessível em `http://localhost:8080`, usando `docker compose up -d`.
- **Provisionar a infraestrutura na AWS com Terraform:** criar VPC, subnets públicas e privadas, security groups, uma instância EC2 e um banco RDS PostgreSQL, respeitando as restrições do AWS Learn Lab.
- **Implantar o Moodle na EC2 de forma automatizada:** via um script `user_data.sh` que instala o Docker e sobe o Moodle no boot da instância.
- **Documentar a arquitetura da sua solução:** produzir um desenho técnico (`docs/architecture-design.md`) com diagrama, descrição de componentes, justificativas e estimativa de custo.

O desafio combina dois mundos: **validação local em contêineres** e **provisionamento de nuvem com Infrastructure as Code**. O ambiente Docker local já vem pronto e funcional no template; a infraestrutura AWS é a sua implementação.

## Contexto

Este desafio é parte da Disciplina de DevOPS no Curso de ADS da UniFAAT e usa o **AWS Learn Lab** (AWS Academy) como ambiente de nuvem educacional. O Learn Lab fornece **credenciais temporárias** (válidas por aproximadamente 4 horas) e tem permissões restritas: não permite criar IAM roles ou usuários, nem utilizar Route 53, ACM (Certificate Manager) ou CloudFront. Essas restrições moldam toda a solução de infraestrutura — veja a seção [Restrições do AWS Learn Lab](#restrições-do-aws-learn-lab).

O **Moodle** é um LMS (Learning Management System) de código aberto. Aqui usamos a versão **4.1+** rodando em contêiner. A instalação local (Docker) serve como base de estudo e validação antes do deploy na nuvem; a instalação em nuvem (EC2 + RDS) demonstra o provisionamento via Terraform.

Este repositório é um **template do GitHub**. Ele entrega o ambiente Docker local funcional, a documentação completa, os workflows de CI/CD e o script de health check. A infraestrutura Terraform completa e o desenho técnico de arquitetura são **tarefas suas** — você cria a estrutura do zero.



## Entregáveis

Você deve entregar os itens abaixo. Cada um tem peso na rubrica de avaliação ([`docs/evaluation-rubric.md`](docs/evaluation-rubric.md)):

- [ ] **1. Ambiente Docker local funcional** — `docker compose up -d` sobe o Moodle em `http://localhost:8080` sem ajustes manuais adicionais (este item já vem pronto no template; você valida e, opcionalmente, customiza). — **20 pts**
- [ ] **2. Infraestrutura Terraform completa** — os três módulos (`networking`, `compute`, `database`) implementados, com `terraform validate` e `terraform plan` passando. — **35 pts**
- [ ] **3. Script `user_data.sh` funcional** — instala o Docker na EC2 e sobe o Moodle automaticamente no boot da instância. *(avaliado dentro da Categoria 2 — Infraestrutura)*
- [ ] **4. Documento de arquitetura preenchido** — `docs/architecture-design.md` gerado a partir do template [`docs/architecture-design-template.md`](docs/architecture-design-template.md), com diagrama, descrição de componentes, justificativas e estimativa de custo. — **20 pts** — ⚠️ **entrega obrigatória eliminatória**: a ausência deste arquivo desclassifica o desafio automaticamente, independentemente da pontuação nas demais categorias.
- [ ] **5. Workflows de CI/CD funcionando** — os workflows do GitHub Actions executam com sucesso, incluindo o `terraform-plan.yml` que você implementa. — **15 pts**

> **Total: 100 pontos.** Detalhes completos em [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md).



## Estrutura do Repositório

O repositório é dividido entre o que **já vem pronto** (fornecido pelo template) e o que **você deve implementar** (sua entrega).

### ✅ Já vem pronto (o template entrega)

| Caminho | Descrição | Estado |
|---|---|---|
| [`docker/`](docker/) | `Dockerfile`, `docker-compose.yml` e `.env.example` — ambiente Moodle local completo | Funcional |
| [`scripts/health-check.sh`](scripts/health-check.sh) | Script de verificação de saúde do Moodle | Funcional |
| [`.github/workflows/`](.github/workflows/) | `terraform-validate.yml`, `docker-lint.yml`, `health-check.yml` (funcionais) e `terraform-plan.yml` (stub) | 3 prontos + 1 stub |
| [`docs/`](docs/) | Guias, troubleshooting, rubrica e o **template** de arquitetura | Completo |
| [`tests/`](tests/) | Testes de propriedade que validam o próprio template | Completo |
| [`.gitignore`](.gitignore), [`README.md`](README.md), `CHALLENGE.md`, `LICENSE`, `pyproject.toml` | Arquivos raiz de configuração e documentação | Completo |

### 🛠️ Você deve implementar (sua entrega)

| O que | Onde | Como |
|---|---|---|
| Módulos Terraform funcionais | `terraform/` (estrutura completa: `versions.tf`, `main.tf`, `variables.tf`, `outputs.tf` e `modules/{networking,compute,database}/`) | Crie toda a estrutura do zero, incluindo `versions.tf` com provider AWS `~> 5.0` |
| Script de inicialização da EC2 | `terraform/modules/compute/user_data.sh` | Crie o script do zero: instalar Docker 24+, Docker Compose v2 e subir o Moodle com `docker compose up -d` |
| Documento de arquitetura | `docs/architecture-design.md` | Copie o template e preencha os blocos `<!-- TODO: -->` |
| Workflow de plan | `.github/workflows/terraform-plan.yml` | Implemente o stub com `terraform plan` acionado por `workflow_dispatch` |
| Secrets da AWS no GitHub | Configuração do repositório (Settings → Secrets) | `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` |





## Passo a Passo Sugerido

Siga este fluxo recomendado. Cada passo referencia a documentação de apoio:

1. **Configure as credenciais do AWS Learn Lab** — obtenha as credenciais temporárias no portal AWS Academy e configure o `~/.aws/credentials` (ou variáveis de ambiente). Veja [`docs/aws-learn-lab-setup.md`](docs/aws-learn-lab-setup.md).
2. **Suba o Moodle localmente com Docker** — copie `docker/.env.example` para `docker/.env`, ajuste as senhas e execute `docker compose up -d`. Valide o acesso em `http://localhost:8080`. Veja a pasta [`docker/`](docker/).
3. **Entenda a estrutura Terraform** — leia [`docs/terraform-guide.md`](docs/terraform-guide.md) para dominar `terraform init`, `plan`, `apply` e `destroy` (quando usar cada um e a saída esperada).
4. **Crie os módulos** `networking`, `compute` e `database` — crie toda a estrutura Terraform do zero dentro de `terraform/`. Use [`docs/architecture.md`](docs/architecture.md) como referência da arquitetura esperada e [`docs/terraform-guide.md`](docs/terraform-guide.md) para os comandos.
5. **Preencha o template de arquitetura** — copie [`docs/architecture-design-template.md`](docs/architecture-design-template.md) para `docs/architecture-design.md` e substitua os blocos `<!-- TODO: -->` (diagrama, componentes, justificativas e custo).
6. **Configure e teste os workflows de CI/CD** — implemente o `terraform-plan.yml`, configure os secrets `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` no GitHub e dispare os workflows manuais.
7. **Faça o deploy e valide** — execute `terraform apply`, aguarde o boot da EC2 e rode `./scripts/health-check.sh <DNS_PÚBLICO_DA_EC2>`. Consulte [`docs/troubleshooting.md`](docs/troubleshooting.md) se algo falhar.



## Restrições do AWS Learn Lab

O AWS Learn Lab tem permissões restritas. Ignorar essas restrições causa erros de `AccessDenied` no `terraform apply`. Resumo das limitações e alternativas:

| Serviço restrito | Recursos bloqueados | Alternativa no Learn Lab |
|---|---|---|
| IAM | `aws_iam_role`, `aws_iam_role_policy`, `aws_iam_user`, `aws_iam_instance_profile` | Usar o instance profile `LabRole` via **data source** (`data "aws_iam_instance_profile"`) |
| Route 53 | `aws_route53_*` | DNS público automático da EC2 (`ec2-X-X-X-X.compute-1.amazonaws.com`) |
| ACM | `aws_acm_*` | HTTP sem TLS (porta 80) é suficiente para o desafio |
| CloudFront | `aws_cloudfront_*` | Acesso direto pelo DNS público da EC2 |

> **Nunca** declare blocos `resource "aws_iam_role"`, `aws_iam_user`, `aws_route53_*`, `aws_acm_*` ou `aws_cloudfront_*` — o `terraform apply` falhará. Veja detalhes e exemplos em [`docs/aws-learn-lab-setup.md`](docs/aws-learn-lab-setup.md).



## Critérios de Avaliação

A avaliação segue a rubrica completa em [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md), totalizando **100 pontos**:

| # | Categoria | Peso |
|---|---|---|
| 1 | Ambiente Docker local funcionando (`docker compose up`) | 20 pts |
| 2 | Infraestrutura Terraform completa e aplicável | 35 pts |
| 3 | Pipelines CI/CD funcionando | 15 pts |
| 4 | Documentação de arquitetura preenchida (`docs/architecture-design.md`) | 20 pts |
| 5 | Boas práticas de segurança | 10 pts |
| | **Total** | **100 pts** |

> ⚠️ **Critério eliminatório:** a ausência do arquivo `docs/architecture-design.md` no repositório entregue resulta em **desclassificação automática**, independentemente da pontuação nas demais categorias. Este arquivo tem peso explícito de **20 pts** (Categoria 4) e sua presença é o primeiro critério verificado na correção.



## Segurança e Credenciais

As credenciais do AWS Learn Lab são pessoais e temporárias. O uso seguro delas é parte avaliada do desafio (Categoria 5 — Boas práticas de segurança).

### Rotação de credenciais

As credenciais do Learn Lab expiram automaticamente em aproximadamente **4 horas**. Para evitar interrupções durante operações longas do Terraform, **rotacione as credenciais antes de atingir 3 horas de uso** da sessão:

1. Acesse o portal AWS Academy → curso → **Learner Lab** e certifique-se de que o Lab está em execução (indicador verde).
2. Clique em **AWS Details** → **AWS CLI** e copie as três linhas de credenciais (`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`).
3. Substitua o conteúdo do arquivo `~/.aws/credentials` (ou as variáveis de ambiente) pelos novos valores e valide com `aws sts get-caller-identity`.

> **Recomendação:** inicie o `terraform apply` sempre com token recém-gerado e monitore o tempo restante no portal AWS Academy.

### Se você expor credenciais acidentalmente

Credenciais do tipo `AKIA[0-9A-Z]{16}` (chaves de acesso no formato permanente) representam risco grave se expostas em commit. Se você perceber que fez push de qualquer arquivo contendo esse padrão (ou qualquer outra credencial AWS) para o repositório:

1. **Revogue imediatamente** as credenciais no console do AWS Academy (o botão "End Lab" encerra a sessão e invalida os tokens).
2. **Reporte o incidente ao professor por e-mail**, descrevendo o que foi exposto e em qual commit.
3. Remova o commit com os dados expostos do histórico (use `git rebase` ou `git filter-branch`, com autorização do professor) e inicie uma nova sessão do Learn Lab para obter credenciais frescas.

> As credenciais do Learn Lab começam com `ASIA` (temporárias via STS) e expiram sozinhas, mas mesmo assim devem ser protegidas durante sua validade. O `.gitignore` já bloqueia `.env`, `*.pem`, `*.key`, `id_rsa`, `*.tfvars` e `terraform.tfstate` — nunca force o rastreamento desses arquivos com `git add -f`.



## Dicas

**Boas práticas**

- Mantenha todas as credenciais fora do código: use variáveis de ambiente (`.env` para Docker, `terraform.tfvars` para Terraform) e marque variáveis sensíveis com `sensitive = true`.
- Aplique o princípio do **menor privilégio**: o security group do RDS deve permitir a porta 5432 **apenas a partir do security group da EC2** (nunca `0.0.0.0/0`).
- Deixe o RDS com `publicly_accessible = false` (acesso só pela subnet privada).
- Restrinja `ssh_allowed_cidr` ao seu próprio IP em vez de `0.0.0.0/0`.
- Proteja o estado do Terraform: use backend remoto (S3 + DynamoDB para lock) para evitar conflitos em equipe.
- Rode `terraform fmt` e `terraform validate` antes de commitar — o workflow `terraform-validate.yml` faz essa checagem automaticamente.

**Armadilhas comuns**

- **Esquecer o `aws_session_token`**: no Learn Lab ele é obrigatório; sem ele, toda chamada de API falha com erro de autenticação.
- **Tentar criar IAM roles/usuários**: o Learn Lab bloqueia isso. Use `data "aws_iam_instance_profile" "lab_role"` em vez de `resource "aws_iam_role"`.
- **Usar Route 53/ACM/CloudFront**: não disponíveis no Learn Lab. Use o DNS público da EC2 e HTTP na porta 80.
- **RDS com uma única subnet**: o `aws_db_subnet_group` exige ao menos **2 AZs**; crie duas subnets privadas em AZs distintas.
- **EC2 sem LabRole**: sem o instance profile, a EC2 não consegue acessar serviços AWS. Referencie `LabRole` via data source.
- **Deixar `<!-- TODO: -->` no `architecture-design.md`**: blocos não preenchidos zeram a Categoria 4. Substitua todos eles.
- **Credenciais expiradas durante o `apply`**: se aparecer `ExpiredTokenException`, rotacione as credenciais e retome.

> Para erros específicos (porta 8080 em uso, healthcheck do DB falhando, `terraform validate` com erros de sintaxe, health-check sem resposta HTTP), consulte [`docs/troubleshooting.md`](docs/troubleshooting.md).
