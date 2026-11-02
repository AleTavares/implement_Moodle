# Guia de Referência do Terraform

Este documento cobre tudo que você precisa para provisionar a infraestrutura do desafio com Terraform: instalação, sequência de comandos, estrutura de módulos, configuração de variáveis e cuidados específicos do AWS Learn Lab.

---

## Índice

1. [Instalando o Terraform CLI](#1-instalando-o-terraform-cli)
2. [Sequência de Comandos](#2-sequência-de-comandos)
3. [Estrutura de Módulos](#3-estrutura-de-módulos)
4. [Passando Variáveis com terraform.tfvars](#4-passando-variáveis-com-terraformtfvars)
5. [Backend Remoto com S3 (Opcional)](#5-backend-remoto-com-s3-opcional)
6. [Avisos sobre o AWS Learn Lab](#6-avisos-sobre-o-aws-learn-lab)
7. [Fluxo de Limpeza (terraform destroy)](#7-fluxo-de-limpeza-terraform-destroy)
8. [Referência Rápida de Comandos](#8-referência-rápida-de-comandos)
9. [Diagnóstico de Problemas Comuns](#9-diagnóstico-de-problemas-comuns)

---

## 1. Instalando o Terraform CLI

### Opção A — tfenv (recomendado, gerencia múltiplas versões)

```bash
# Instalar o tfenv
git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Instalar a versão compatível com o provider AWS ~> 5.0
tfenv install 1.9.8
tfenv use 1.9.8

# Verificar
terraform -version
# Terraform v1.9.8
```

### Opção B — instalação direta (Linux x86_64)

```bash
# Baixar o binário (confira a versão mais recente em releases.hashicorp.com/terraform)
curl -O https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip
unzip terraform_1.9.8_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform -version
```

### Opção C — macOS (Homebrew)

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform -version
```

### Opção D — Windows (Chocolatey)

```powershell
choco install terraform
terraform -version
```

> **Versão mínima:** Terraform 1.5 ou superior, provider AWS `~> 5.0`. Versões anteriores do provider (4.x) podem apresentar diferenças de atributos nos recursos.

---

## 2. Sequência de Comandos

Execute os comandos abaixo **dentro do diretório `terraform/`** após preencher seus módulos e criar o arquivo `terraform.tfvars`.

### 2.1 `terraform init`

Inicializa o diretório de trabalho: baixa o provider AWS, instala os módulos locais e prepara o backend de estado.

```bash
cd terraform/
terraform init
```

Saída esperada:

```
Initializing the backend...
Initializing modules...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...

Terraform has been successfully initialized!
```

> Execute `terraform init` sempre que:
> - Clonar ou fazer fork do repositório pela primeira vez
> - Adicionar ou alterar um módulo
> - Mudar a versão do provider em `versions.tf`
> - Configurar um novo backend

### 2.2 `terraform plan`

Gera um plano de execução: mostra exatamente quais recursos serão criados, modificados ou destruídos, sem aplicar nenhuma mudança real na AWS.

```bash
terraform plan
```

Para salvar o plano em arquivo (útil para CI/CD):

```bash
terraform plan -out=tfplan
```

Saída esperada (fragmento):

```
Terraform will perform the following actions:

  # module.networking.aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block = "10.0.0.0/16"
      ...
    }

Plan: 12 to add, 0 to change, 0 to destroy.
```

> **Leia o plano antes de aplicar.** Verifique se nenhum recurso existente será destruído acidentalmente. Um `~` indica modificação no lugar; um `-` indica destruição.

### 2.3 `terraform apply`

Aplica o plano e cria os recursos na AWS. Solicita confirmação interativa antes de executar.

```bash
terraform apply
```

Para aplicar sem confirmação interativa (útil em CI após revisão):

```bash
terraform apply -auto-approve
```

Para aplicar um plano previamente salvo:

```bash
terraform apply tfplan
```

Saída esperada ao final:

```
Apply complete! Resources: 12 added, 0 changed, 0 destroyed.

Outputs:

ec2_public_dns = "ec2-X-X-X-X.compute-1.amazonaws.com"
rds_endpoint   = "moodle-db.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com:5432"
vpc_id         = "vpc-0123456789abcdef0"
```

Anote o valor de `ec2_public_dns` — você vai usá-lo no health check.

### 2.4 `terraform destroy`

Remove **todos** os recursos gerenciados pelo Terraform. Consulte a seção [Fluxo de Limpeza](#7-fluxo-de-limpeza-terraform-destroy) para detalhes.

```bash
terraform destroy
```

---

## 3. Estrutura de Módulos

O scaffolding divide a infraestrutura em três módulos independentes. Você deve preencher os stubs `# TODO:` em cada um.

```
terraform/
├── main.tf           ← instancia os 3 módulos (você preenche)
├── variables.tf      ← variáveis raiz (você preenche)
├── outputs.tf        ← outputs finais (você preenche)
├── versions.tf       ← provider AWS ~> 5.0 (pré-preenchido)
├── terraform.tfvars  ← seus valores reais (você cria a partir do .example)
├── backend.tf.example← exemplo de backend S3 (opcional)
└── modules/
    ├── networking/   ← VPC, subnets, IGW, route tables, SGs
    ├── compute/      ← EC2, key pair, user_data.sh
    └── database/     ← RDS PostgreSQL, subnet group, SG
```

### Módulo `networking`

Responsável por criar toda a camada de rede:

| Recurso | Descrição |
|---|---|
| `aws_vpc` | VPC principal com o CIDR configurável |
| `aws_subnet` (pública) | Subnet pública na AZ principal (ex.: `us-east-1a`) |
| `aws_subnet` (privada ×2) | Subnets privadas em 2 AZs para o subnet group do RDS |
| `aws_internet_gateway` | Acesso à internet para a subnet pública |
| `aws_route_table` | Tabela de rota associada à subnet pública |
| `aws_security_group` (EC2) | Permite ingresso nas portas 80 (HTTP) e 22 (SSH) |
| `aws_security_group` (RDS) | Permite ingresso na porta 5432 apenas do SG da EC2 |

**Outputs esperados do módulo:** `vpc_id`, `public_subnet_id`, `private_subnet_ids`, `ec2_security_group_id`, `rds_security_group_id`.

### Módulo `compute`

Responsável pela instância EC2 e sua inicialização:

| Recurso | Descrição |
|---|---|
| `aws_key_pair` | Par de chaves usando `var.ec2_public_key` |
| `aws_instance` | EC2 `t3.medium`, Amazon Linux 2023, na subnet pública |
| `templatefile()` | Renderiza `user_data.sh` injetando variáveis de ambiente do RDS |

O arquivo `modules/compute/user_data.sh` é o script executado no primeiro boot da EC2. Você deve implementar nele:

1. Instalação do Docker 24+ via repositório oficial (`dnf`)
2. Instalação do Docker Compose v2 como plugin Docker
3. Habilitação do serviço Docker (`systemctl enable --now docker`)
4. Clone/cópia dos arquivos Docker para `/opt/moodle/`
5. Criação do arquivo `.env` com as variáveis do RDS
6. Execução do `docker compose up -d`

**Outputs esperados do módulo:** `ec2_public_dns`, `ec2_instance_id`.

### Módulo `database`

Responsável pelo banco de dados RDS:

| Recurso | Descrição |
|---|---|
| `aws_db_subnet_group` | Agrupa as duas subnets privadas para o RDS |
| `aws_db_instance` | RDS PostgreSQL 15, `db.t3.micro`, na subnet privada |

> O RDS **não** deve ter `publicly_accessible = true`. O acesso ocorre somente pela EC2 na mesma VPC.

**Outputs esperados do módulo:** `rds_endpoint`, `rds_port`.

### Referência entre módulos em `main.tf`

```hcl
module "networking" {
  source       = "./modules/networking"
  project_name = var.project_name
  vpc_cidr     = "10.0.0.0/16"
  # ... demais variáveis
}

module "database" {
  source             = "./modules/database"
  project_name       = var.project_name
  private_subnet_ids = module.networking.private_subnet_ids
  rds_security_group = module.networking.rds_security_group_id
  # ... credenciais e nome do banco
}

module "compute" {
  source              = "./modules/compute"
  project_name        = var.project_name
  public_subnet_id    = module.networking.public_subnet_id
  ec2_security_group  = module.networking.ec2_security_group_id
  rds_endpoint        = module.database.rds_endpoint
  # ... demais variáveis
}
```

---

## 4. Passando Variáveis com terraform.tfvars

O arquivo `terraform.tfvars` é onde você define os valores das variáveis sem colocá-los diretamente no código. Ele **não deve ser commitado** (já está no `.gitignore`).

### Passo a passo

```bash
# 1. Copiar o arquivo de exemplo
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# 2. Editar com seus valores reais
nano terraform/terraform.tfvars  # ou use seu editor de preferência
```

### Exemplo de `terraform.tfvars` preenchido

```hcl
aws_region        = "us-east-1"
project_name      = "moodle-challenge"
ec2_instance_type = "t3.medium"
ec2_public_key    = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB..."  # saída de: cat ~/.ssh/id_rsa.pub
ssh_allowed_cidr  = "203.0.113.10/32"  # seu IP; evite 0.0.0.0/0 em produção
db_username       = "moodle"
db_password       = "SenhaForte#2024!"  # use senha forte; nunca commite este arquivo
db_name           = "moodle"
```

### Gerando sua chave SSH (se ainda não tiver)

```bash
ssh-keygen -t rsa -b 4096 -C "moodle-challenge" -f ~/.ssh/moodle_key
# Chave pública: ~/.ssh/moodle_key.pub
cat ~/.ssh/moodle_key.pub  # copie o conteúdo para ec2_public_key no tfvars
```

### Passando variáveis via linha de comando (alternativa)

```bash
terraform apply \
  -var="db_password=SenhaForte#2024!" \
  -var="ssh_allowed_cidr=203.0.113.10/32"
```

> **Atenção:** variáveis passadas via `-var` aparecem no histórico do shell. Prefira o arquivo `terraform.tfvars` para dados sensíveis.

---

## 5. Backend Remoto com S3 (Opcional)

Por padrão, o Terraform armazena o estado em `terraform.tfstate` localmente. O arquivo `terraform/backend.tf.example` mostra como configurar um backend remoto usando S3 + DynamoDB para lock de estado.

### Quando usar

- Trabalho em equipe (evita conflitos de estado)
- Fluxos de CI/CD que aplicam Terraform automaticamente
- Quando quiser manter histórico de estado fora do repositório

### Como ativar

```bash
# 1. Copiar o exemplo (não commite o backend.tf com valores reais)
cp terraform/backend.tf.example terraform/backend.tf

# 2. Editar com o nome do seu bucket e tabela DynamoDB
nano terraform/backend.tf
```

Exemplo de conteúdo do `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "meu-bucket-terraform-state"   # bucket S3 já existente
    key            = "moodle-challenge/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"               # tabela DynamoDB para lock
    encrypt        = true
  }
}
```

```bash
# 3. Reinicializar para migrar o estado local para o S3
terraform init -migrate-state
```

> **Restrição do AWS Learn Lab:** o bucket S3 e a tabela DynamoDB devem ser criados manualmente no console AWS antes de configurar o backend, pois o Learn Lab não permite criar esses recursos via `aws_s3_bucket` e `aws_dynamodb_table` com as permissões padrão do `LabRole` em todas as contas. Verifique se sua conta Academy tem as permissões necessárias antes de tentar automatizar a criação do backend.

---

## 6. Avisos sobre o AWS Learn Lab

O AWS Learn Lab (AWS Academy) usa um papel IAM chamado **`LabRole`** com permissões predefinidas. Isso impõe restrições importantes no Terraform.

### LabRole — como usar corretamente

Você **não** cria o `LabRole` — ele já existe na conta. Referencie-o via data source:

```hcl
data "aws_iam_instance_profile" "lab_role" {
  name = "LabRole"
}

resource "aws_instance" "moodle" {
  # ...
  iam_instance_profile = data.aws_iam_instance_profile.lab_role.name
}
```

### Recursos proibidos no Learn Lab

Os seguintes tipos de recurso **causarão erros de permissão** no `terraform apply`:

| Tipo de recurso | Motivo |
|---|---|
| `aws_iam_role` | Criação de roles IAM não permitida |
| `aws_iam_role_policy` | Anexar políticas a roles não permitido |
| `aws_iam_instance_profile` | Use o `LabRole` existente via data source |
| `aws_iam_user` | Criação de usuários IAM bloqueada |
| `aws_route53_*` | Serviço Route 53 não disponível |
| `aws_acm_*` | Certificate Manager não disponível |
| `aws_cloudfront_*` | CloudFront não disponível |

### Credenciais temporárias

As credenciais do Learn Lab expiram a cada **sessão de laboratório** (geralmente 4 horas). Você precisa atualizar suas credenciais locais a cada nova sessão.

**Via `~/.aws/credentials`:**

```ini
[default]
aws_access_key_id     = ASIA...
aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
aws_session_token     = IQoJb3JpZ2lu...  # obrigatório para credenciais temporárias (STS)
```

**Via variáveis de ambiente:**

```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AWS_SESSION_TOKEN="IQoJb3JpZ2lu..."
export AWS_DEFAULT_REGION="us-east-1"
```

> **`aws_session_token` é obrigatório.** Credenciais temporárias do STS sempre incluem um token de sessão. Se omiti-lo, o provider AWS retornará `InvalidClientTokenId`.

### Rotação de credenciais

- As credenciais expiram ao encerrar a sessão do laboratório no portal AWS Academy.
- **Recomendação:** execute `terraform destroy` antes de encerrar a sessão para evitar que recursos fiquem órfãos (e cobranças continuem no orçamento do Lab).
- Se o `terraform apply` falhar com `ExpiredTokenException`, atualize as credenciais e execute novamente.

---

## 7. Fluxo de Limpeza (terraform destroy)

> ⚠️ **Execute `terraform destroy` ao final de cada sessão de laboratório.** Recursos como EC2 e RDS consomem o crédito do AWS Learn Lab continuamente, mesmo quando parados.

### Passo a passo de limpeza

```bash
# 1. Confirmar o que será destruído (inspecione antes de confirmar)
terraform plan -destroy

# 2. Destruir todos os recursos
terraform destroy
```

O Terraform solicita confirmação:

```
Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
```

Saída esperada ao final:

```
Destroy complete! Resources: 12 destroyed.
```

### Verificação pós-destroy

Após o destroy, confirme no console AWS que os recursos foram removidos:

1. **EC2** → Instances: nenhuma instância `running` ou `stopped` do projeto
2. **RDS** → Databases: nenhuma instância do projeto
3. **VPC** → Your VPCs: VPC do projeto removida (além da VPC padrão da conta)

### Problemas comuns no destroy

| Erro | Causa | Solução |
|---|---|---|
| `DependencyViolation` na VPC | Algum recurso dependente (ex.: ENI de ELB) ainda existe | Verifique no console se há recursos não gerenciados pelo Terraform e os remova manualmente |
| `InvalidClientTokenId` | Credenciais expiradas | Atualize as credenciais do Learn Lab e execute novamente |
| `ResourceInUse` no RDS | Há conexões ativas | Aguarde ou encerre as conexões; tente o destroy novamente |
| `terraform.tfstate` desatualizado | Estado local divergiu da AWS | Execute `terraform refresh` e depois `terraform destroy` |

---

## 8. Referência Rápida de Comandos

```bash
# Inicializar (primeira vez ou após mudar módulos/provider)
terraform init

# Checar formatação dos arquivos .tf
terraform fmt -check

# Formatar automaticamente
terraform fmt

# Validar sintaxe e referências
terraform validate

# Ver o plano de execução
terraform plan

# Aplicar (com confirmação interativa)
terraform apply

# Aplicar sem confirmação (cuidado!)
terraform apply -auto-approve

# Ver os outputs após o apply
terraform output

# Ver um output específico
terraform output ec2_public_dns

# Destruir todos os recursos
terraform destroy

# Ver o plano de destruição antes de executar
terraform plan -destroy

# Listar recursos no estado atual
terraform state list

# Ver detalhes de um recurso específico no estado
terraform state show module.compute.aws_instance.moodle

# Sincronizar estado com o que existe na AWS
terraform refresh

# Inicializar sem configurar backend (útil para validação em CI)
terraform init -backend=false
```

---

## 9. Diagnóstico de Problemas Comuns

| Problema | Mensagem de erro | Solução |
|---|---|---|
| Credenciais não configuradas | `No valid credential sources found` | Configure `~/.aws/credentials` ou variáveis de ambiente; verifique se incluiu `aws_session_token` |
| Token de sessão ausente | `InvalidClientTokenId` | Inclua `aws_session_token` — credenciais do Learn Lab são temporárias (STS) |
| Credenciais expiradas | `ExpiredTokenException` | Abra uma nova sessão no portal AWS Academy e atualize as credenciais |
| Recurso IAM bloqueado | `AccessDenied creating iam_role` | Remova blocos `aws_iam_role`/`aws_iam_instance_profile` e use o data source do `LabRole` |
| Provider não inicializado | `Could not load plugin` | Execute `terraform init` no diretório `terraform/` |
| Arquivo `.tfvars` ausente | `No value for required variable` | Crie `terraform.tfvars` a partir do `terraform.tfvars.example` |
| Erro de formatação no CI | `Files not formatted` (terraform fmt) | Execute `terraform fmt` localmente e commite os arquivos corrigidos |
| EC2 não inicializou Moodle | Moodle inacessível na porta 80 | Verifique logs via `ssh ec2-user@<DNS> -i ~/.ssh/moodle_key` → `cat /var/log/user-data.log` |

---

> Para problemas não listados aqui, consulte o `docs/troubleshooting.md`. Para dúvidas sobre as restrições do AWS Learn Lab, consulte o `docs/aws-learn-lab-setup.md`.
