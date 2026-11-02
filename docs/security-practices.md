# Boas Práticas de Segurança

Este guia descreve as boas práticas de segurança aplicadas no Moodle Docker AWS Challenge. O objetivo é que os alunos aprendam, desde o primeiro contato com o repositório-template, a não expor credenciais e a seguir o **princípio do menor privilégio** (least privilege) ao provisionar infraestrutura na AWS.

A segurança aqui é didática e prática: cada seção mostra o **porquê** da prática, seguido de exemplos de código Terraform comentados com a abordagem correta e a abordagem incorreta a evitar.

---

## Índice

1. [Gerenciamento de Credenciais](#1-gerenciamento-de-credenciais)
2. [Security Groups — princípio do menor privilégio](#2-security-groups--princípio-do-menor-privilégio)
3. [.gitignore — padrões ignorados e porquê](#3-gitignore--padrões-ignorados-e-porquê)
4. [Variáveis Sensitive no Terraform](#4-variáveis-sensitive-no-terraform)
5. [RDS `publicly_accessible = false`](#5-rds-publicly_accessible--false)
6. [LabRole via data source (sem criar IAM roles)](#6-labrole-via-data-source-sem-criar-iam-roles)
7. [Proteção do estado do Terraform](#7-proteção-do-estado-do-terraform)
8. [Rotação de credenciais no AWS Learn Lab](#8-rotação-de-credenciais-no-aws-learn-lab)
9. [Checklist de segurança](#9-checklist-de-segurança)
10. [Referências](#10-referências)

---

## 1. Gerenciamento de Credenciais

A regra fundamental: **nunca codifique secrets diretamente no código** (hardcode). Senhas de banco de dados, chaves de acesso AWS, chaves SSH privadas e tokens de sessão devem sempre ser fornecidos por fora do repositório, via variáveis de ambiente ou arquivos de configuração **ignorados pelo Git**.

### 1.1 Ambiente Docker local — arquivo `.env`

No ambiente Docker, todas as credenciais do banco de dados e do Moodle são declaradas no arquivo `docker/.env` (copiado a partir de `docker/.env.example`). O `docker-compose.yml` carrega esses valores via `env_file` e os repassa aos contêineres por **interpolação** (`${VAR_NAME}`), sem nunca escrever o valor da senha em texto literal no YAML.

Isso atende ao critério de aceitação **8.4**: o `docker-compose.yml` não contém credenciais de banco de dados diretamente; tudo é referenciado via variáveis de ambiente.

**Correto — interpolação de variável no `docker-compose.yml`:**

```yaml
services:
  moodle:
    environment:
      # O valor é lido do .env em tempo de execução, nunca escrito em texto literal
      - MOODLE_DATABASE_PASSWORD=${MOODLE_DATABASE_PASSWORD}
      - MOODLE_PASSWORD=${MOODLE_PASSWORD}
```

**Errado — senha em texto literal no `docker-compose.yml`:**

```yaml
# ❌ NUNCA faça isso: a senha fica visível no Git e no histórico de versões
services:
  moodle:
    environment:
      - MOODLE_DATABASE_PASSWORD=Admin1234!
```

O arquivo `docker/.env.example` contém apenas valores de exemplo (`changeme_strong_password`) e um comentário `# TODO:` orientando a cópia para `.env` e a substituição das senhas. O `.env` real **é ignorado pelo Git** (ver seção 3).

### 1.2 Terraform — arquivo `terraform.tfvars`

No Terraform, os valores de variáveis sensíveis (senha do RDS, conteúdo da chave pública, CIDR de SSH) são fornecidos no arquivo `terraform.tfvars`, que também **é ignorado pelo Git**. O repositório entrega apenas o `terraform/terraform.tfvars.example` com os nomes das variáveis e comentários `# TODO:`, sem valores preenchidos.

**Correto — `.tfvars.example` sem valores reais:**

```hcl
# terraform/terraform.tfvars.example
# TODO: Preencha os valores abaixo antes de executar terraform apply

aws_region        = ""   # TODO: Região AWS (ex: "us-east-1")
ec2_public_key    = ""   # TODO: Conteúdo da chave pública OpenSSH (ssh-rsa AAAA...)
db_username       = ""   # TODO: Usuário do banco de dados RDS
db_password       = ""   # TODO: Senha do banco de dados RDS (use senha forte)
ssh_allowed_cidr  = ""   # TODO: CIDR autorizado para SSH (restrinja ao seu IP em produção)
```

**Errado — valores reais de exemplo em qualquer arquivo versionado:**

```hcl
# ❌ NUNCA coloque valores reais no .tfvars.example ou em qualquer .tf commitado
db_password = "M!nhaS3nhaReal123"
ec2_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB...chave-real..."
```

> Os valores reais vivem apenas no seu `terraform.tfvars` local (ignorado pelo Git). Consulte também `docs/aws-learn-lab-setup.md` para o procedimento de obtenção e rotação das credenciais temporárias do Learn Lab.

---

## 2. Security Groups — princípio do menor privilégio

Security Groups controlam o tráfego de rede para dentro (ingress) e para fora (egress) dos recursos. O **princípio do menor privilégio** determina que cada recurso exponha apenas as portas e origens estritamente necessárias — nada de `0.0.0.0/0` em portas de gerenciamento sem uma justificativa muito forte.

Neste desafio há dois Security Groups principais:

| Security Group | Porta | Origem permitida (ingress) | Justificativa |
|---|---|---|---|
| **SG da EC2** | 80 (HTTP) | `0.0.0.0/0` | Moodle precisa ser acessível pela Internet |
| **SG da EC2** | 22 (SSH) | `var.ssh_allowed_cidr` (restrinja ao seu IP) | Acesso administrativo restrito |
| **SG do RDS** | 5432 (PostgreSQL) | Apenas o **SG da EC2** | O banco só é acessível a partir da aplicação |

### 2.1 RDS acessível apenas a partir do SG da EC2

O RDS nunca deve aceitar conexões diretas da Internet. O ingress da porta 5432 deve referenciar o **ID do Security Group da EC2** como origem — não um bloco CIDR aberto.

**Correto — origem é o Security Group da EC2:**

```hcl
# Security Group do RDS — só permite PostgreSQL a partir do SG da EC2
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Permite acesso ao PostgreSQL apenas a partir do SG da EC2"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL a partir do SG da EC2 (least privilege)"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    # Origem = o Security Group da EC2, não um CIDR aberto
    security_groups  = [var.ec2_security_group_id]
  }

  egress {
    description = "Bloqueia tráfego de saída desnecessário (menor privilégio)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # ajuste em produção conforme necessário
  }
}
```

**Errado — RDS aberto para a Internet:**

```hcl
# ❌ NUNCA exponha o RDS para 0.0.0.0/0 — qualquer origem pode tentar conectar
resource "aws_security_group" "rds" {
  # ...
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # abre o banco para toda a Internet
  }
}
```

Ao usar `security_groups = [var.ec2_security_group_id]` como origem, a AWS permite o tráfego apenas se vier de uma instância associada àquele Security Group — exatamente o fluxo `Internet → IGW → EC2 → RDS` da arquitetura de referência.

### 2.2 SSH restrito ao seu próprio IP (`ssh_allowed_cidr`)

A porta 22 (SSH) não deve ficar aberta para `0.0.0.0/0` em produção. O stub `terraform/modules/compute/variables.tf` orienta a declarar a variável `ssh_allowed_cidr` com valor padrão `0.0.0.0/0`, mas com um **aviso explícito de segurança** na `description` recomendando restringir o CIDR ao IP do aluno (critério **8.2**).

**Correto — `description` com aviso de segurança e uso da variável no ingress:**

```hcl
# terraform/modules/compute/variables.tf
# TODO: Declare a variável ssh_allowed_cidr conforme abaixo.
variable "ssh_allowed_cidr" {
  type    = string
  default = "0.0.0.0/0"
  description = "CIDR autorizado para acesso SSH à EC2. " \
    "AVISO DE SEGURANÇA: o valor padrão 0.0.0.0/0 permite SSH de qualquer origem; " \
    "restrinja ao seu próprio IP público (ex: 203.0.113.10/32) em ambiente de produção."
}

# SG da EC2 usando a variável no ingress da porta 22
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP público (Moodle)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH restrito ao CIDR configurado (menor privilégio)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr] # restrinja ao seu IP em produção
  }
}
```

**Errado — SSH aberto para a Internet em produção:**

```hcl
# ❌ Permite tentativas de brute-force SSH de qualquer origem
resource "aws_security_group" "ec2" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # nunca use isso em produção
  }
}
```

Para descobrir o seu IP público e restringir o acesso:

```bash
curl -s https://checkip.amazonaws.com
# Exemplo de saída: 203.0.113.10
# Use no terraform.tfvars: ssh_allowed_cidr = "203.0.113.10/32"
```

> O padrão `0.0.0.0/0` existe apenas como conveniência do desafio educacional. Em qualquer ambiente que não seja de estudo, substitua-o pelo seu IP específico (`/32`).

---

## 3. .gitignore — padrões ignorados e porquê

O repositório inclui um `.gitignore` pré-configurado (critério **2.6**) que impede o rastreamento acidental de arquivos sensíveis. Antes de qualquer commit, o Git impede a inclusão de arquivos não-rastreados correspondentes aos padrões abaixo (critério **2.7**).

| Padrão ignorado | Por que ignorar |
|---|---|
| `.env` (e `.env.*`, exceto `.env.example`) | Contém senhas reais do Docker/Moodle. O `.env.example` é mantido (`!.env.example`) porque tem apenas valores de exemplo. |
| `*.tfvars` | Contém valores reais das variáveis Terraform (senhas, chaves, CIDRs). Apenas `*.tfvars.example` é versionado. |
| `terraform.tfstate` | O arquivo de estado do Terraform pode armazenar valores sensíveis em texto literal (senhas, mesmo com `sensitive = true`, aparecem no estado se forem atributos de recurso). |
| `terraform.tfstate.backup` | Cópia de segurança do estado — mesma exposição que o `terraform.tfstate`. |
| `*.pem` | Chaves privadas (ex: par de chaves SSH da AWS Academy). |
| `*.key` | Chaves privadas de uso geral. |
| `id_rsa` | Chave privada SSH padrão do usuário. |

Trecho do `.gitignore` do repositório:

```gitignore
# dotenv environment variable files
.env
.env.*
!.env.example

# Terraform — arquivos sensíveis e de estado
*.tfvars
terraform.tfstate
terraform.tfstate.backup

# Credenciais e chaves privadas
*.pem
*.key
id_rsa
```

### Como verificar se um arquivo está protegido

```bash
# git check-ignore confirma que o Git ignora um arquivo (saída = caminho ignorado)
git check-ignore -v docker/.env
# Saída esperada: .gitignore:N:.env  docker/.env

# git ls-files lista apenas arquivos rastreados — nenhum .pem, .key ou .env deve aparecer
git ls-files | grep -E '\.(pem|key|env)$|id_rsa|tfstate$|tfvars$'
# Saída esperada: vazia (nada rastreado)
```

Se `git check-ignore` retornar o caminho do arquivo, ele está protegido. Nunca use `git add -f` para forçar o rastreamento desses arquivos.

---

## 4. Variáveis Sensitive no Terraform

Variáveis marcadas como `sensitive = true` não são exibidas em texto literal na saída do `terraform plan` e `terraform apply`. Isso evita que senhas apareçam no terminal ou em logs de CI. **Marcar como `sensitive` não criptografa o valor** — ele ainda é gravado no arquivo de estado (por isso o `terraform.tfstate` também é ignorado pelo Git, ver seção 3).

As variáveis que devem ser marcadas como `sensitive` neste desafio são:

| Variável | Por que é sensível |
|---|---|
| `db_password` | Senha do banco RDS |
| `db_username` | Identificador de acesso ao banco |
| `ec2_public_key` | Conteúdo da chave pública OpenSSH usada no `aws_key_pair` |

> O critério **9.3** determina que `ec2_public_key` seja do tipo `string`, sem valor padrão, com `description` informando que o valor deve ser uma chave pública no formato OpenSSH, e usada para criar o recurso `aws_key_pair`.

**Correto — variáveis com `sensitive = true` e sem valor padrão:**

```hcl
# terraform/modules/database/variables.tf
# TODO: Declare db_password e db_username como sensitive.
variable "db_username" {
  type      = string
  sensitive = true
  # sem default — o aluno deve fornecer via terraform.tfvars
  description = "Usuário master do banco de dados RDS (sensível)."
}

variable "db_password" {
  type      = string
  sensitive = true
  # sem default — senha forte fornecida via terraform.tfvars
  description = "Senha master do banco de dados RDS (sensível). Use senha forte."
}

# terraform/modules/compute/variables.tf
# TODO: Declare ec2_public_key conforme o critério 9.3.
variable "ec2_public_key" {
  type      = string
  sensitive = true
  # sem default — o aluno fornece via terraform.tfvars
  description = "Conteúdo da chave pública no formato OpenSSH (ex: ssh-rsa AAAA...). " \
    "Usada para criar o recurso aws_key_pair."
}
```

**Uso correto no recurso — repassando a variável sensível:**

```hcl
resource "aws_key_pair" "moodle" {
  key_name   = "${var.project_name}-key"
  public_key = var.ec2_public_key # valor sensível, não exibido no plan
}

resource "aws_db_instance" "moodle" {
  # ...
  username = var.db_username # sensível
  password = var.db_password  # sensível
}
```

**Errado — variável de senha sem `sensitive`:**

```hcl
# ❌ A senha aparece em texto literal na saída do terraform plan/apply
variable "db_password" {
  type    = string
  default = "Admin1234!" # valor padrão codificado e visível — duplo erro
}
```

> Mesmo com `sensitive = true`, **nunca** defina `default` para senhas. Sem `default`, o Terraform exige que o valor venha do `terraform.tfvars` (ignorado pelo Git) ou de outra fonte externa, o que força a boa prática.

---

## 5. RDS `publicly_accessible = false`

O atributo `publicly_accessible = false` na `aws_db_instance` garante que o RDS **não receba um IP público** e só possa ser acessado de dentro da VPC. Combinado com o Security Group que aceita 5432 apenas do SG da EC2 (seção 2.1), o banco fica isolado da Internet.

O stub `terraform/modules/database/main.tf` orienta a criar a instância RDS com `publicly_accessible = false` (critério referenciado em **8.1**).

**Correto — RDS privado, sem IP público:**

```hcl
resource "aws_db_instance" "moodle" {
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  db_name              = var.db_name
  username             = var.db_username          # sensível
  password             = var.db_password          # sensível
  db_subnet_group_name = aws_db_subnet_group.moodle.name
  vpc_security_group_ids = [var.security_group_id] # SG do RDS (5432 só da EC2)

  # Importante: mantém o RDS privado, sem IP público
  publicly_accessible = false

  skip_final_snapshot = true # simplifica o desafio educacional
}
```

**Errado — RDS público:**

```hcl
# ❌ publicly_accessible = true atribui um IP público ao RDS,
#    expondo o banco à Internet mesmo com Security Group
resource "aws_db_instance" "moodle" {
  # ...
  publicly_accessible = true
}
```

### Por que isso importa

- `publicly_accessible = false` significa que a instância RDS não recebe um IP público roteável pela Internet, mesmo que esteja em uma subnet que rotearia para o IGW.
- Combinado com o RDS em **subnets privadas** (sem rota direta para o Internet Gateway) e o Security Group restrito ao SG da EC2, o banco só é alcançável a partir da aplicação Moodle — exatamente o fluxo `Internet → IGW → EC2 → RDS` da arquitetura de referência.
- Mesmo que alguém descubra o endpoint do RDS, não consegue conectar diretamente pela Internet; precisa primeiro comprometer a EC2, que por sua vez tem o SSH restrito ao seu IP (seção 2.2).

> Defensiva em profundidade (defense in depth): não confie em uma única camada. Use `publicly_accessible = false` **e** subnet privada **e** Security Group restrito — juntos.

---

## 6. LabRole via data source (sem criar IAM roles)

O AWS Learn Lab não permite criar recursos IAM (`aws_iam_role`, `aws_iam_role_policy`, `aws_iam_instance_profile`, `aws_iam_user`). Tentar criá-los faz o `terraform apply` falhar com `AccessDenied`.

A alternativa é usar o instance profile `LabRole` **pré-existente** via **data source** (`data "aws_iam_instance_profile"`), sem declarar nenhum bloco `resource` de IAM (critério **9.1**). Isso é também uma aplicação do menor privilégio: em vez de criar uma role nova com permissões amplas, reutilizamos a role controlada pelo ambiente do Learn Lab.

**Correto — `LabRole` via data source:**

```hcl
# terraform/modules/compute/main.tf
# TODO: Busque o LabRole existente via data source — NÃO crie aws_iam_role.
data "aws_iam_instance_profile" "lab_role" {
  name = "LabRole"
}

resource "aws_instance" "moodle" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = var.ec2_instance_type
  subnet_id            = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name             = aws_key_pair.moodle.key_name
  iam_instance_profile = data.aws_iam_instance_profile.lab_role.name # LabRole existente
  user_data            = templatefile("${path.module}/user_data.sh", {})
}
```

**Errado — tentar criar IAM role no Learn Lab:**

```hcl
# ❌ AccessDenied no Learn Lab — estes recursos são bloqueados
resource "aws_iam_role" "ec2_role" {
  name = "moodle-ec2-role"
  # ...
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "moodle-ec2-profile"
  role = aws_iam_role.ec2_role.name
  # ...
}
```

> Consulte `docs/aws-learn-lab-setup.md` para a lista completa de serviços restritos (Route 53, ACM, CloudFront, IAM Users) e suas alternativas no Learn Lab.

---

## 7. Proteção do estado do Terraform

O arquivo `terraform.tfstate` armazena o estado dos recursos provisionados e **pode conter valores sensíveis em texto literal** (senhas e atributos de recurso, mesmo com `sensitive = true` na variável). Por isso o `.gitignore` ignora `terraform.tfstate` e `terraform.tfstate.backup` (seção 3).

Em ambientes de equipe ou produção, o estado deve ser armazenado remotamente com:

- **Backend S3** — armazena o estado em um bucket S3 (com versionamento e criptografia habilitados).
- **Lock via DynamoDB** — impede execuções concorrentes de `terraform apply` que corromperiam o estado.

O repositório entrega `terraform/backend.tf.example` demonstrando essa sintaxe, comentado, para o aluno adaptar.

**Exemplo comentado — backend S3 com lock DynamoDB:**

```hcl
# terraform/backend.tf.example
# TODO: Renomeie para backend.tf e ajuste os nomes do bucket e tabela.
terraform {
  backend "s3" {
    bucket         = "moodle-challenge-tfstate" # bucket para guardar o estado
    key            = "terraform.tfstate"        # caminho do estado dentro do bucket
    region         = "us-east-1"
    dynamodb_table = "moodle-challenge-locks"   # tabela para lock de estado
    encrypt         = true                      # criptografa o estado em repouso
  }
}
```

> No AWS Learn Lab, o provisionamento de um bucket S3 e tabela DynamoDB pode não ser viável por restrições de permissão. Nesse caso, o aluno pode usar o backend local (padrão) e garantir que o `terraform.tfstate` nunca seja commitado — o que já é garantido pelo `.gitignore`. A configuração de backend remoto é importante como aprendizado de boa prática para ambientes reais.

---

## 8. Rotação de credenciais no AWS Learn Lab

As credenciais do AWS Learn Lab são temporárias (STS, prefixo `ASIA`) e expiram em aproximadamente 4 horas. O `CHALLENGE.md` orienta a rotação com ao menos 3 passos e a recomendação de rotacionar **antes de atingir 3 horas de uso** da sessão (critério **8.3**).

Resumo do procedimento de rotação (detalhado em `docs/aws-learn-lab-setup.md`):

1. Acesse o portal AWS Academy → curso → Learner Lab → **AWS Details** → **AWS CLI**.
2. Copie as três linhas de credenciais (`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`).
3. Substitua o conteúdo de `~/.aws/credentials` pelos novos valores e valide com `aws sts get-caller-identity`.

### Se expor credenciais acidentalmente

Se um arquivo contendo o padrão de chave de acesso permanente `AKIA[0-9A-Z]{16}` for enviado para o repositório (critério **8.5**):

1. **Revogue imediatamente** as credenciais no console do AWS Academy (botão "End Lab" encerra a sessão).
2. Reporte o incidente ao professor por e-mail.
3. Remova o commit com os dados expostos do histórico (`git rebase`/`git filter-branch`, com autorização).

> Credenciais `ASIA...` (temporárias) expiram sozinhas, mas devem ser protegidas durante sua validade. Credenciais `AKIA...` (permanentes) representam risco muito maior se expostas e exigem revogação imediata.

---

## 9. Checklist de segurança

Antes de marcar o desafio como concluído, confirme cada item:

- [ ] Nenhuma senha aparece em texto literal no `docker/docker-compose.yml` (tudo via `${VAR}`).
- [ ] `docker/.env` (com valores reais) **não** está versionado no Git (`git check-ignore docker/.env` retorna o caminho).
- [ ] `terraform.tfvars` (com valores reais) **não** está versionado no Git.
- [ ] `terraform.tfstate` e `terraform.tfstate.backup` **não** estão versionados no Git.
- [ ] `db_password` e `ec2_public_key` declarados com `sensitive = true` e sem `default`.
- [ ] SG do RDS aceita a porta 5432 apenas a partir do SG da EC2 (origem = `security_groups`).
- [ ] `ssh_allowed_cidr` restrito ao seu IP (`/32`) em produção — não `0.0.0.0/0`.
- [ ] `aws_db_instance` com `publicly_accessible = false`.
- [ ] `LabRole` referenciado via `data "aws_iam_instance_profile"` — nenhum bloco `resource "aws_iam_*"`.
- [ ] Nenhum recurso `aws_route53_*`, `aws_acm_*`, `aws_cloudfront_*` ou `aws_iam_user` no código Terraform.
- [ ] `git ls-files` não retorna nenhum `.pem`, `.key`, `.env` (real) ou `tfstate`.

---

## 10. Referências

- [Terraform — Sensitive Values in State](https://developer.hashicorp.com/terraform/language/state/sensitive-data)
- [Terraform — Backend Configuration (S3)](https://developer.hashicorp.com/terraform/language/backend/s3)
- [AWS — Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
- [AWS RDS — `publicly_accessible`](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html)
- [AWS STS — Credenciais temporárias](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html)
- [OWASP — Least Privilege](https://owasp.org/www-community/attacks/Principle_of_Least_Privilege)
- Configuração do AWS Learn Lab — [`docs/aws-learn-lab-setup.md`](./aws-learn-lab-setup.md)
- Guia de comandos Terraform — [`docs/terraform-guide.md`](./terraform-guide.md)
