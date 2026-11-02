# Rubrica de Avaliação — Moodle Docker AWS Challenge

> **Uso:** Este documento é destinado a professores e monitores responsáveis pela correção do desafio.
> A pontuação máxima é **100 pontos**, distribuídos em cinco categorias.
>
> **Critério eliminatório:** A ausência do arquivo `docs/architecture-design.md` no repositório entregue
> pelo aluno resulta em **desclassificação automática**, independentemente da pontuação nas demais categorias.



## Tabela Resumo de Pontuação

| # | Categoria | Peso |
|||::|
| 1 | Ambiente Docker local funcionando (`docker compose up`) | 20 pts |
| 2 | Infraestrutura Terraform completa e aplicável | 35 pts |
| 3 | Pipelines CI/CD funcionando | 15 pts |
| 4 | Documentação de arquitetura preenchida (`docs/architecture-design.md`) | 20 pts |
| 5 | Boas práticas de segurança | 10 pts |
| | **Total** | **100 pts** |



## Níveis de Desempenho

| Nível | Faixa de Pontuação | Descrição |
||::||
| **Insuficiente** | 0–39 pts | Entregáveis principais ausentes ou não funcionais; não demonstra compreensão mínima dos conceitos. |
| **Básico** | 40–59 pts | Alguns entregáveis presentes, mas com lacunas significativas de funcionalidade ou qualidade. |
| **Proficiente** | 60–79 pts | Maioria dos entregáveis funcional com pequenas falhas; demonstra domínio adequado dos conceitos. |
| **Avançado** | 80–100 pts | Todos os entregáveis funcionais e completos; demonstra domínio sólido e boas práticas aplicadas. |



## Critérios Detalhados

### Categoria 1 — Ambiente Docker Local (20 pts)

**Objetivo:** Verificar se o aluno consegue executar o Moodle localmente via Docker Compose sem erros.

#### Como avaliar

1. Clone o repositório do aluno.
2. Copie o arquivo `.env.example` para `.env` na raiz do projeto `docker/`.
3. Execute `docker compose up -d` a partir do diretório `docker/`.
4. Aguarde até 5 minutos e verifique o acesso em `http://localhost:8080`.

| Critério | Pontuação |
||::|
| O arquivo `docker-compose.yml` está presente e é sintaticamente válido (`docker compose config --quiet` sem erros) | 4 pts |
| Todos os contêineres atingem o estado `running` após `docker compose up -d` | 6 pts |
| A URL `http://localhost:8080` retorna HTTP 200 com a interface do Moodle | 6 pts |
| Os dados persistem em volumes Docker nomeados após reinício dos contêineres (`docker compose restart` + verificação) | 4 pts |
| **Total Categoria 1** | **20 pts** |

#### Níveis por faixa

| Nível | Faixa | Indicador |
||::||
| Insuficiente | 0–5 pts | `docker-compose.yml` ausente ou com erros de sintaxe; contêineres não sobem |
| Básico | 6–11 pts | Contêineres sobem mas Moodle não responde em `http://localhost:8080` |
| Proficiente | 12–16 pts | Moodle acessível, mas sem persistência de dados ou com configurações padrão quebradas |
| Avançado | 17–20 pts | Stack completo funcionando com persistência confirmada |



### Categoria 2 — Infraestrutura Terraform (35 pts)

**Objetivo:** Verificar se os módulos Terraform estão completos, sintaticamente corretos e criam a infraestrutura AWS esperada no AWS Learn Lab.

> **Nota:** Testar `terraform apply` real requer credenciais AWS ativas. Caso não seja possível, avalie ao menos a etapa de `terraform validate` e inspeção manual do código.

#### Como avaliar

1. Acesse o diretório `terraform/` do repositório do aluno.
2. Execute `terraform init` (com credenciais AWS configuradas, se disponíveis).
3. Execute `terraform validate` e `terraform plan`.
4. Se possível, execute `terraform apply` e verifique os recursos criados no console AWS.

| Critério | Pontuação |
||::|
| Os três módulos (`networking`, `compute`, `database`) possuem os arquivos `main.tf`, `variables.tf` e `outputs.tf` preenchidos (sem stubs vazios) | 5 pts |
| `terraform validate` passa sem erros | 5 pts |
| Módulo `networking`: VPC, subnets pública e privadas (mín. 2 AZs), IGW, route table e security groups corretos | 7 pts |
| Módulo `compute`: instância EC2 `t3.medium`, AMI Amazon Linux 2023, `user_data.sh` funcional com Docker instalado e Moodle em execução | 9 pts |
| Módulo `database`: RDS PostgreSQL 15 `db.t3.micro`, subnet group cobrindo 2 AZs, `publicly_accessible = false` | 7 pts |
| Outputs raiz exportados corretamente (`ec2_public_dns`, `rds_endpoint`, `vpc_id`) | 2 pts |
| **Total Categoria 2** | **35 pts** |

#### Níveis por faixa

| Nível | Faixa | Indicador |
||::||
| Insuficiente | 0–9 pts | Módulos com stubs não preenchidos; `terraform validate` falha |
| Básico | 10–18 pts | Um ou dois módulos implementados; `terraform validate` passa mas `terraform apply` falha |
| Proficiente | 19–27 pts | Todos os módulos implementados; infraestrutura criada com pequenos erros de configuração |
| Avançado | 28–35 pts | Infraestrutura criada com sucesso; Moodle acessível via DNS público da EC2 |



### Categoria 3 — Pipelines CI/CD (15 pts)

**Objetivo:** Verificar se os workflows do GitHub Actions estão configurados corretamente e executam sem falhas.

#### Como avaliar

1. Acesse a aba **Actions** do repositório do aluno no GitHub.
2. Verifique o histórico de execuções dos workflows em pushes recentes para `main`.
3. Para `terraform-plan.yml` e `health-check.yml`, execute manualmente via `workflow_dispatch`.

| Critério | Pontuação |
||::|
| Workflow `terraform-validate.yml` executa em push/PR para `main` e passa (`terraform fmt -check` + `terraform validate`) | 5 pts |
| Workflow `docker-lint.yml` executa em push/PR para `main` e `hadolint` não reporta erros no `Dockerfile` | 4 pts |
| Workflow `terraform-plan.yml` implementado pelo aluno com `workflow_dispatch` e executa `terraform plan` com sucesso (requer secrets configurados) | 4 pts |
| Workflow `health-check.yml` executa via `workflow_dispatch` com input `moodle_url` e o script retorna exit 0 | 2 pts |
| **Total Categoria 3** | **15 pts** |

#### Níveis por faixa

| Nível | Faixa | Indicador |
||::||
| Insuficiente | 0–4 pts | Workflows ausentes ou sem nenhuma execução bem-sucedida |
| Básico | 5–8 pts | Apenas `terraform-validate.yml` ou `docker-lint.yml` funcionando |
| Proficiente | 9–12 pts | Três dos quatro workflows funcionando corretamente |
| Avançado | 13–15 pts | Todos os quatro workflows executados e aprovados |



### Categoria 4 — Documentação de Arquitetura (20 pts)

**Objetivo:** Verificar se o aluno produziu e entregou o documento `docs/architecture-design.md` com qualidade adequada.

> ⚠️ **CRITÉRIO ELIMINATÓRIO:** A ausência de `docs/architecture-design.md` no repositório do aluno resulta em **0 pontos nesta categoria** e **desclassificação do desafio**, independentemente da pontuação nas demais categorias.

#### Como avaliar

1. Verifique a existência do arquivo `docs/architecture-design.md` (não o template — o documento preenchido pelo aluno).
2. Leia cada seção e verifique o preenchimento conforme os critérios abaixo.

| Critério | Pontuação |
||::|
| Arquivo `docs/architecture-design.md` presente no repositório (critério eliminatório) | 4 pts |
| Diagrama de arquitetura cobrindo: VPC, subnets públicas e privadas, EC2, RDS, security groups e fluxo Internet → IGW → EC2 → RDS | 6 pts |
| Seção "Decisões de Design" preenchida com justificativas técnicas reais (não apenas os valores do template) | 4 pts |
| Seção "Componentes" descrevendo cada recurso AWS provisionado (VPC, subnets, EC2, RDS, SGs) | 3 pts |
| Seção "Custo Estimado" preenchida com valores reais da AWS Pricing Calculator e link para a estimativa gerada | 3 pts |
| **Total Categoria 4** | **20 pts** |

#### Níveis por faixa

| Nível | Faixa | Indicador |
||::||
| Insuficiente | 0 pts | Arquivo `docs/architecture-design.md` ausente — desclassificação |
| Básico | 4–8 pts | Arquivo presente mas com `<!-- TODO: -->` não preenchidos; diagrama ausente ou incompleto |
| Proficiente | 9–15 pts | Todas as seções preenchidas, diagrama presente mas com componentes faltando |
| Avançado | 16–20 pts | Todas as seções completas, diagrama cobre todos os componentes obrigatórios, custo com link da calculadora |



### Categoria 5 — Boas Práticas de Segurança (10 pts)

**Objetivo:** Verificar se o aluno aplicou práticas de segurança na solução entregue.

#### Como avaliar

1. Inspecione o código Terraform e os arquivos de configuração em busca de credenciais expostas.
2. Verifique as regras de security group no código Terraform.
3. Confirme que o `.gitignore` está presente e adequado.
4. Verifique se arquivos sensíveis (`.env`, `*.tfvars`, `*.pem`) não foram commitados.

| Critério | Pontuação |
||::|
| Nenhuma credencial (senhas, tokens, access keys) exposta em texto literal em arquivos commitados | 4 pts |
| Security group do RDS com acesso restrito ao security group da EC2 (não `0.0.0.0/0`) | 2 pts |
| Variável `ssh_allowed_cidr` restrita a um CIDR específico (não `0.0.0.0/0`) ou acompanhada de comentário de aviso | 2 pts |
| Instância RDS configurada com `publicly_accessible = false` | 2 pts |
| **Total Categoria 5** | **10 pts** |

#### Níveis por faixa

| Nível | Faixa | Indicador |
||::||
| Insuficiente | 0–2 pts | Credenciais expostas em commits ou security groups totalmente abertos |
| Básico | 3–5 pts | Credenciais não expostas, mas security groups sem restrição adequada |
| Proficiente | 6–8 pts | Segurança adequada com pequenas falhas (ex.: `ssh_allowed_cidr` = `0.0.0.0/0` sem aviso) |
| Avançado | 9–10 pts | Todos os critérios de segurança atendidos |



## Checklist Rápido para o Avaliador

Use esta lista antes de iniciar a correção detalhada:

- [ ] O repositório foi entregue via fork do template original
- [ ] O arquivo `docs/architecture-design.md` **existe** no repositório (critério eliminatório)
- [ ] `docker compose up -d` funciona sem erros manuais de configuração adicionais
- [ ] `terraform validate` passa no diretório `terraform/`
- [ ] Nenhuma credencial em texto literal foi encontrada em commits (`git log --all -S "password"`)
- [ ] Os workflows do GitHub Actions têm histórico de execuções na aba Actions



## Referências

- [Moodle System Requirements](https://moodledev.io/docs/gettingstarted/requirements)
- [AWS Pricing Calculator](https://calculator.aws/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [hadolint — Dockerfile Linter](https://github.com/hadolint/hadolint)
