# Moodle Docker AWS Challenge

<!-- Substitua <usuario>/<repositorio> pelo seu usuário e nome do repositório no GitHub -->
[![Terraform Validate](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/terraform-validate.yml/badge.svg)](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/terraform-validate.yml)
[![Docker Lint](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/docker-lint.yml/badge.svg)](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/docker-lint.yml)
[![Health Check](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/health-check.yml/badge.svg)](https://github.com/&lt;AleTavares&gt;/&lt;repositorio&gt;/actions/workflows/health-check.yml)

Este repositório é um **template educacional** para um desafio que combina containerização com Docker, infraestrutura como código com Terraform e deploy na nuvem AWS usando o ambiente AWS Learn Lab. O template entrega um ambiente Docker local de referência rodando Moodle 4.x com PostgreSQL 15, além do scaffolding de arquivos, documentação, pipelines de CI/CD e scripts de validação. Os módulos Terraform funcionais e o desenho técnico de arquitetura são **entregas obrigatórias do aluno**.

→ **[Leia o desafio completo](CHALLENGE.md)**


## Pré-requisitos

Antes de começar, verifique se você tem as seguintes ferramentas instaladas e configuradas:

| Ferramenta | Versão mínima | Observação |
||||
| [Docker Engine](https://docs.docker.com/get-docker/) | 24.x | Inclui o Docker Compose v2 (`docker compose`) |
| [Terraform](https://developer.hashicorp.com/terraform/install) | 1.5+ | Provider AWS `~> 5.0` |
| [AWS CLI](https://aws.amazon.com/cli/) | 2.x | Para configurar as credenciais do Learn Lab |
| [Git](https://git-scm.com/) | 2.x | Para clonar/forkar o template |
| [Python](https://www.python.org/) | 3.8+ | Para rodar os testes (`pytest` + `hypothesis`) |
| Conta AWS Learn Lab | — | Credenciais temporárias obtidas no portal AWS Academy |

> O ambiente **AWS Learn Lab** fornece credenciais temporárias com permissões restritas (sem IAM, Route 53, ACM ou CloudFront). Consulte [`docs/aws-learn-lab-setup.md`](docs/aws-learn-lab-setup.md) para configurá-las.



## Estrutura do Repositório

```
.
├── .github/
│   └── workflows/                       # Pipelines de CI/CD (GitHub Actions)
│       ├── docker-lint.yml              #   - Lint do Dockerfile (hadolint)
│       ├── health-check.yml             #   - Health check manual (workflow_dispatch)
│       ├── terraform-plan.yml           #   - Stub: terraform plan (a implementar)
│       └── terraform-validate.yml       #   - fmt-check + validate
├── docker/                              # Ambiente Docker local de referência (funcional)
│   ├── .env.example                     #   - Variáveis de ambiente documentadas
│   ├── Dockerfile                       #   - Imagem Moodle customizada (extensões PHP)
│   └── docker-compose.yml               #   - Orquestra Moodle + PostgreSQL 15
├── docs/                                # Documentação do desafio
│   ├── architecture-design-template.md  #   - Template do desenho técnico (entrega do aluno)
│   ├── architecture.md                  #   - Arquitetura de referência (gabarito)
│   ├── aws-learn-lab-setup.md           #   - Credenciais e limitações do Learn Lab
│   ├── evaluation-rubric.md             #   - Rubrica de avaliação
│   ├── security-practices.md            #   - Boas práticas de segurança
│   ├── terraform-guide.md               #   - Guia dos comandos Terraform
│   └── troubleshooting.md              #   - Problemas comuns e soluções
├── scripts/
│   └── health-check.sh                  # Verificação automatizada do Moodle
├── tests/                               # Testes de propriedade (pytest + Hypothesis)
│   ├── test_architecture_template_sections.py
│   ├── test_compose_no_hardcoded_creds.py
│   ├── test_dockerfile_extensions.py
│   ├── test_gitignore_patterns.py
│   ├── test_health_check.py
│   ├── test_terraform_module_structure.py
│   ├── test_todo_comments.py
│   └── test_workflow_step_comments.py
├── .gitignore                           # Padrões de segurança (secrets, estado, etc.)
├── CHALLENGE.md                         # Objetivos, entregas e critérios do desafio
└── README.md                            # Este arquivo (ponto de entrada)
```

> **Nota:** o diretório `terraform/` **não** faz parte do template — você o cria como parte do desafio, instanciando os módulos `networking`, `compute` e `database`. Veja a seção [Infraestrutura AWS com Terraform](#infraestrutura-aws-com-terraform) e o [`CHALLENGE.md`](CHALLENGE.md).



## Ambiente Docker Local

O template entrega um stack Docker funcional para você validar o Moodle localmente antes do deploy na AWS.

```bash
# 1. Entre no diretório docker/
cd docker

# 2. Copie o arquivo de exemplo e preencha as senhas
cp .env.example .env
#    Edite .env e substitua os valores de exemplo (POSTGRES_PASSWORD, MOODLE_PASSWORD, etc.)

# 3. Suba os contêineres (Moodle + PostgreSQL)
docker compose up -d

# 4. Acesse o Moodle no navegador
#    → http://localhost:8080
```

Comandos úteis para gerenciar o ambiente:

```bash
docker compose ps              # Verifica o status dos contêineres
docker compose logs -f moodle  # Acompanha os logs do Moodle
docker compose down            # Para e remove os contêineres
docker compose down -v         # Para e remove os contêineres E os volumes (apaga os dados)
```

O `docker-compose.yml` mapeia a porta `8080` do host para a porta `80` do contêiner Moodle e garante que o Moodle só inicia após o PostgreSQL estar saudável (`depends_on: condition: service_healthy`). Os dados são persistidos em volumes nomeados (`db_data`, `moodle_data`, `moodle_www`).

### Health Check

Após subir o ambiente (local ou na AWS), valide se o Moodle está respondendo corretamente:

```bash
./scripts/health-check.sh http://localhost:8080
# Para a instância EC2 na AWS, use o DNS público:
# ./scripts/health-check.sh http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com
```

O script realiza **3 verificações** em sequência, com até 3 tentativas (intervalo de 30s):

| Verificação | O que testa |
|||
| (a) | HTTP 200 na URL raiz |
| (b) | HTTP 200 em `/login/index.php` |
| (c) | Presença da string `Moodle` no corpo da resposta |

**Interpretando a saída:**

- **`exit 0`** com `[✓]`: Moodle saudável — as 3 verificações passaram.
- **`exit 1`** com `[✗]` + diagnóstico: falhou após 3 tentativas. O script indica qual verificação específica falhou (`raiz`, `login` ou `conteudo`) e sugere comandos de troubleshooting (`docker compose logs`, `curl`, etc.).



## Infraestrutura AWS com Terraform

O template **não** entrega os módulos Terraform funcionais — eles são sua tarefa no desafio. A estrutura esperada é composta por **3 módulos** que você cria dentro de `terraform/modules/`:

| Módulo | Recursos a provisionar |
|||
| **`networking`** | VPC, 1 subnet pública + 2 subnets privadas (AZs distintas), Internet Gateway, route tables, Security Group do EC2 (portas 80 e 22) e Security Group do RDS (porta 5432 a partir do SG do EC2) |
| **`compute`** | Instância EC2 `t3.medium` (Amazon Linux 2023), IAM instance profile `LabRole` via **data source** (não criar `aws_iam_role`), `aws_key_pair`, e `user_data.sh` injetado via `templatefile()` |
| **`database`** | `aws_db_subnet_group` (2 AZs privadas), `aws_db_instance` PostgreSQL 15 classe `db.t3.micro`, 20 GB, `publicly_accessible = false` |

Restrições importantes do AWS Learn Lab: não use `aws_route53_*`, `aws_acm_*`, `aws_cloudfront_*` nem `aws_iam_user`. O DNS público do EC2 substitui o Route 53. Veja os detalhes em [`docs/aws-learn-lab-setup.md`](docs/aws-learn-lab-setup.md).

Para a sequência completa de comandos (`init`, `plan`, `apply`, `destroy`) e exemplos de saída esperada, consulte o **[Guia do Terraform](docs/terraform-guide.md)**.



## CI/CD

O repositório inclui pipelines de GitHub Actions em `.github/workflows/`:

| Workflow | Gatilho | O que faz |
||||
| [`terraform-validate.yml`](.github/workflows/terraform-validate.yml) | `push` / `pull_request` em `main` | Executa `terraform fmt -check` e `terraform validate` (falha listando arquivos com problemas de formatação) |
| [`docker-lint.yml`](.github/workflows/docker-lint.yml) | `push` / `pull_request` em `main` | Executa `hadolint` no `docker/Dockerfile` |
| [`terraform-plan.yml`](.github/workflows/terraform-plan.yml) | `workflow_dispatch` | **Stub** com `# TODO:` — você implementa o `terraform plan` configurando os secrets `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` |
| [`health-check.yml`](.github/workflows/health-check.yml) | `workflow_dispatch` (input `moodle_url`) | Torna `health-check.sh` executável e o roda contra a URL informada |

> Cada step dos workflows contém um comentário explicativo descrevendo o que a etapa faz.



## Documentação

Toda a documentação de apoio está em `docs/`:

| Documento | Descrição |
|||
| [`docs/architecture-design-template.md`](docs/architecture-design-template.md) | Template para você preencher e entregar como `docs/architecture-design.md` (entrega obrigatória) |
| [`docs/architecture.md`](docs/architecture.md) | Arquitetura de referência da solução AWS (gabarito para professores/monitores) |
| [`docs/aws-learn-lab-setup.md`](docs/aws-learn-lab-setup.md) | Como obter credenciais temporárias do AWS Academy e as limitações do Learn Lab |
| [`docs/terraform-guide.md`](docs/terraform-guide.md) | Guia de referência dos comandos Terraform (`init`, `plan`, `apply`, `destroy`) |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Problemas comuns (porta 8080, healthcheck do DB, credenciais expiradas, etc.) e soluções |
| [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md) | Rubrica de avaliação com critérios e pontuações |
| [`docs/security-practices.md`](docs/security-practices.md) | Boas práticas de segurança (secrets, least privilege, estado do Terraform) |



## Testes

Os testes validam a estrutura e configuração do repositório usando **pytest** + **[Hypothesis](https://hypothesis.readthedocs.io/)** (property-based testing, 100 iterações por propriedade). Eles inspecionam o sistema de arquivos e **não** requerem infraestrutura AWS.

```bash
# Instale as dependências (se ainda não tiver)
pip install pytest hypothesis pyyaml

# Rode todos os testes a partir da raiz do repositório
pytest tests/ -v
```

Os testes cobrem, entre outros: extensões PHP obrigatórias no Dockerfile, ausência de credenciais literais no `docker-compose.yml`, padrões do `.gitignore`, estrutura dos módulos Terraform, comentários `# TODO:` nos arquivos de configuração, comentários nos steps dos workflows, seções do template de arquitetura e o comportamento do `health-check.sh`.



## Avaliação

A avaliação do desafio segue a rubrica detalhada em [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md), que pontua infraestrutura provisionada, Moodle acessível, segurança, documentação e o desenho técnico de arquitetura.

> **Critério eliminatório:** a ausência do arquivo `docs/architecture-design.md` (gerado por você a partir de [`docs/architecture-design-template.md`](docs/architecture-design-template.md)) resulta em desclassificação automática, independentemente da pontuação nas demais categorias.
