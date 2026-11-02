# Configuração do AWS Learn Lab

Este guia descreve passo a passo como obter as credenciais temporárias do AWS Academy (Learn Lab) e configurá-las no seu ambiente local para usar com o AWS CLI e o Terraform.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Obtendo as credenciais no portal AWS Academy](#2-obtendo-as-credenciais-no-portal-aws-academy)
3. [Configurando `~/.aws/credentials`](#3-configurando-awscredentials)
4. [Configurando a região padrão (us-east-1)](#4-configurando-a-região-padrão-us-east-1)
5. [Verificando se as credenciais funcionam](#5-verificando-se-as-credenciais-funcionam)
6. [Expiração das credenciais (~4 horas)](#6-expiração-das-credenciais-4-horas)
7. [Atualizando as credenciais quando expirarem](#7-atualizando-as-credenciais-quando-expirarem)
8. [Restrições do AWS Learn Lab](#8-restrições-do-aws-learn-lab)
9. [⚠️ Nunca commite credenciais no Git](#9-️-nunca-commite-credenciais-no-git)

---

## 1. Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **AWS CLI v2** — [Instruções de instalação](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** ≥ 1.5 — [Download](https://developer.hashicorp.com/terraform/downloads)
- Acesso ao portal **AWS Academy** (credenciais fornecidas pelo professor)

Para verificar se o AWS CLI está instalado:

```bash
aws --version
# Saída esperada: aws-cli/2.x.x Python/3.x.x ...
```

---

## 2. Obtendo as credenciais no portal AWS Academy

1. Acesse [https://awsacademy.instructure.com](https://awsacademy.instructure.com) e faça login com as credenciais fornecidas pelo professor.

2. No painel do Canvas, clique no curso correspondente ao desafio.

3. No menu lateral, clique em **Modules** e depois em **Learner Lab**.

4. Na tela do Learner Lab, clique no botão **Start Lab** (botão verde). Aguarde até o indicador no canto superior esquerdo ficar **verde** (estado "Lab running").

5. Clique no link **AWS Details** (ícone de nuvem AWS no topo da tela).

6. Na janela que abre, clique em **AWS CLI** para expandir as credenciais. Você verá algo como:

   ```
   [default]
   aws_access_key_id=ASIA...
   aws_secret_access_key=xxxx...
   aws_session_token=IQoJ...muito...longo...
   ```

7. Clique em **Download PEM** se precisar da chave SSH para acessar a EC2 via terminal.

> **Atenção:** As credenciais mostradas são temporárias e expiram em aproximadamente **4 horas** após o início da sessão do Lab. Não feche o lab sem antes salvar as credenciais.

---

## 3. Configurando `~/.aws/credentials`

Você tem duas opções para configurar as credenciais.

### Opção A — Editar o arquivo diretamente (recomendado)

Abra (ou crie) o arquivo `~/.aws/credentials`:

```bash
mkdir -p ~/.aws
nano ~/.aws/credentials
```

Cole o conteúdo copiado do portal AWS Academy:

```ini
[default]
aws_access_key_id=ASIA_SUA_ACCESS_KEY_AQUI
aws_secret_access_key=SUA_SECRET_KEY_AQUI
aws_session_token=SEU_SESSION_TOKEN_MUITO_LONGO_AQUI
```

Salve o arquivo (`Ctrl+O`, `Enter`, `Ctrl+X` no nano).

> **Importante:** O `aws_session_token` é **obrigatório** no AWS Learn Lab. Sem ele, todas as chamadas de API serão rejeitadas com erro de autenticação. Em contas AWS de produção normais esse campo não é necessário, mas o Learn Lab usa credenciais de sessão temporárias (STS) que sempre exigem o token.

### Opção B — Via `aws configure`

```bash
aws configure
```

Responda às perguntas interativas:

```
AWS Access Key ID [None]: ASIA_SUA_ACCESS_KEY_AQUI
AWS Secret Access Key [None]: SUA_SECRET_KEY_AQUI
Default region name [None]: us-east-1
Default output format [None]: json
```

Em seguida, adicione manualmente o session token (o comando `aws configure` não tem campo para ele):

```bash
aws configure set aws_session_token SEU_SESSION_TOKEN_MUITO_LONGO_AQUI
```

### Opção C — Via variáveis de ambiente (alternativa ao arquivo)

Se preferir não salvar as credenciais em disco, exporte-as como variáveis de ambiente na sessão atual do terminal:

```bash
export AWS_ACCESS_KEY_ID="ASIA_SUA_ACCESS_KEY_AQUI"
export AWS_SECRET_ACCESS_KEY="SUA_SECRET_KEY_AQUI"
export AWS_SESSION_TOKEN="SEU_SESSION_TOKEN_MUITO_LONGO_AQUI"
export AWS_DEFAULT_REGION="us-east-1"
```

> As variáveis de ambiente têm prioridade sobre o arquivo `~/.aws/credentials`. Elas são perdidas ao fechar o terminal.

---

## 4. Configurando a região padrão (us-east-1)

O AWS Learn Lab opera na região **`us-east-1` (N. Virginia)**. Todos os recursos deste desafio devem ser criados nessa região.

Verifique (ou configure) a região padrão no arquivo `~/.aws/config`:

```bash
cat ~/.aws/config
```

Se o arquivo não existir ou a região estiver errada, configure:

```bash
aws configure set default.region us-east-1
```

Ou edite o arquivo diretamente:

```ini
# ~/.aws/config
[default]
region = us-east-1
output = json
```

No Terraform, a região já está configurada como padrão no arquivo `terraform/versions.tf`:

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}
```

Não altere esse valor a não ser que o professor indique outra região.

---

## 5. Verificando se as credenciais funcionam

Após configurar as credenciais, verifique se elas estão válidas:

```bash
aws sts get-caller-identity
```

Saída esperada (valores serão diferentes):

```json
{
    "UserId": "AROA....:user/vocareum",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/voclabs/user123456=..."
}
```

Se o comando retornar um JSON com `UserId`, `Account` e `Arn`, suas credenciais estão funcionando corretamente.

**Erros comuns:**

| Erro | Causa | Solução |
|---|---|---|
| `InvalidClientTokenId` | `aws_access_key_id` inválido ou copiado incorretamente | Copie as credenciais novamente do portal |
| `AuthFailure` / `ExpiredToken` | Credenciais expiradas ou `aws_session_token` incorreto | Reinicie o Lab e copie novas credenciais |
| `NoCredentialProviders` | Nenhuma credencial encontrada | Verifique se `~/.aws/credentials` existe e está no formato correto |

---

## 6. Expiração das credenciais (~4 horas)

> ⚠️ **As credenciais do AWS Learn Lab expiram automaticamente a cada ~4 horas.**

Quando a sessão expira, todas as operações do AWS CLI e do Terraform falham com o erro:

```
Error: ExpiredTokenException: The security token included in the request is expired
```

ou

```
Error: configuring Terraform AWS Provider: validating provider credentials: retrieving caller identity from STS: operation error STS: GetCallerIdentity, https response error StatusCode: 403
```

Esse comportamento é normal e esperado no ambiente educacional. Não indica erro na sua implementação.

**Recomendação:** Inicie o `terraform apply` somente quando o Lab tiver acabado de ser iniciado (token recém-gerado). Para execuções longas, monitore o tempo restante no portal AWS Academy.

---

## 7. Atualizando as credenciais quando expirarem

Sempre que as credenciais expirarem, siga este procedimento:

1. Acesse o portal AWS Academy → curso → Learner Lab.

2. Se o Lab estiver parado, clique em **Start Lab** e aguarde ficar verde.

3. Clique em **AWS Details** → **AWS CLI** e copie as três linhas de credenciais.

4. Abra o arquivo `~/.aws/credentials` e **substitua as três linhas** pelo novo conteúdo:

   ```bash
   nano ~/.aws/credentials
   ```

   Substitua os valores antigos pelos novos:

   ```ini
   [default]
   aws_access_key_id=ASIA_NOVA_ACCESS_KEY
   aws_secret_access_key=NOVA_SECRET_KEY
   aws_session_token=NOVO_SESSION_TOKEN_LONGO
   ```

5. Salve o arquivo e verifique:

   ```bash
   aws sts get-caller-identity
   ```

6. Retome o `terraform plan` ou `terraform apply` normalmente.

> **Dica:** O portal AWS Academy exibe um contador regressivo da sessão ativa. Rotacione as credenciais antes de atingir 3 horas de uso para evitar interrupções durante operações longas do Terraform.

---

## 8. Restrições do AWS Learn Lab

O AWS Learn Lab é um ambiente educacional com permissões restritas. Alguns serviços AWS **não estão disponíveis** ou têm limitações. Entender essas restrições antes de escrever o Terraform evita erros de permissão inesperados.

### 8.1 IAM — Sem criação de roles ou usuários

**Limitação:** O Learn Lab não permite criar recursos `aws_iam_role`, `aws_iam_role_policy`, `aws_iam_instance_profile` ou `aws_iam_user`.

**Alternativa:** Use o instance profile pré-existente `LabRole` via **data source**, sem criar nenhum recurso IAM:

```hcl
# Correto — busca o LabRole existente via data source
data "aws_iam_instance_profile" "lab_role" {
  name = "LabRole"
}

# Uso na instância EC2
resource "aws_instance" "moodle" {
  # ...
  iam_instance_profile = data.aws_iam_instance_profile.lab_role.name
}
```

> **Nunca** declare blocos `resource "aws_iam_role"`, `resource "aws_iam_role_policy"` ou `resource "aws_iam_instance_profile"` nos seus módulos Terraform. O `terraform apply` falhará com `AccessDenied`.

### 8.2 Route 53 — Sem DNS personalizado

**Limitação:** Recursos `aws_route53_zone`, `aws_route53_record` e similares (`aws_route53_*`) não estão disponíveis no Learn Lab.

**Alternativa:** Use o **DNS público automático da EC2**, que tem o formato:

```
ec2-X-X-X-X.compute-1.amazonaws.com
```

Por exemplo: `ec2-54-83-12-200.compute-1.amazonaws.com`

Esse endereço é gerado automaticamente pela AWS ao criar a instância com IP público e é perfeitamente funcional para acessar o Moodle no desafio.

No Terraform, exporte esse valor como output:

```hcl
output "ec2_public_dns" {
  value = aws_instance.moodle.public_dns
}
```

### 8.3 ACM (AWS Certificate Manager) — Sem certificados SSL

**Limitação:** Recursos `aws_acm_certificate`, `aws_acm_certificate_validation` e similares (`aws_acm_*`) não estão disponíveis.

**Alternativa:** Para o propósito deste desafio, o Moodle pode ser acessado via HTTP (porta 80) sem TLS. O DNS público da EC2 é suficiente para demonstrar a instalação funcional.

> Em um ambiente de produção real, você usaria ACM + ALB + Route 53 para HTTPS. No Learn Lab, o foco é na configuração da infraestrutura e da aplicação, não no certificado SSL.

### 8.4 CloudFront — Sem CDN

**Limitação:** Recursos `aws_cloudfront_distribution` e similares (`aws_cloudfront_*`) não estão disponíveis.

**Alternativa:** Acesse o Moodle diretamente pelo DNS público da EC2. Para o desafio educacional, CDN não é um requisito.

### 8.5 Resumo das restrições e alternativas

| Serviço restrito | Tipo de recurso bloqueado | Alternativa no Learn Lab |
|---|---|---|
| IAM | `aws_iam_role`, `aws_iam_role_policy`, `aws_iam_user`, `aws_iam_instance_profile` | `data "aws_iam_instance_profile"` com `LabRole` |
| Route 53 | `aws_route53_*` | DNS público automático da EC2 (`ec2-X-X-X-X.compute-1.amazonaws.com`) |
| ACM | `aws_acm_*` | HTTP sem TLS (porta 80) é suficiente para o desafio |
| CloudFront | `aws_cloudfront_*` | Acesso direto pelo DNS da EC2 |

---

## 9. ⚠️ Nunca commite credenciais no Git

> **Este é o ponto mais crítico de segurança do desafio.**

As credenciais do AWS Learn Lab são pessoais e temporárias, mas expô-las publicamente em um repositório Git é uma prática de segurança grave que deve ser evitada.

### O que nunca commitar

- O arquivo `~/.aws/credentials`
- Qualquer arquivo `.env` com valores reais preenchidos
- Arquivos `.tfvars` com senhas, chaves ou tokens
- Arquivos de chave privada (`.pem`, `.key`, `id_rsa`)

### O `.gitignore` já protege você

O repositório já inclui um `.gitignore` configurado para bloquear os arquivos mais comuns:

```gitignore
# Credenciais AWS e arquivos de ambiente
.env
*.pem
*.key
id_rsa

# Estado do Terraform (pode conter valores sensíveis em plaintext)
terraform.tfstate
terraform.tfstate.backup
*.tfvars
```

Nunca force o rastreamento desses arquivos com `git add -f` ou `--force`.

### Como verificar antes de commitar

```bash
# Verifica se algum arquivo sensível seria incluído no commit
git status

# Verifica se um arquivo específico está sendo ignorado
git check-ignore -v caminho/para/o/arquivo

# Lista todos os arquivos rastreados (nenhum .pem, .key ou .env deve aparecer)
git ls-files
```

### Se você expuser credenciais acidentalmente

1. **Revogue imediatamente** as credenciais no portal AWS Academy (botão "End Lab" encerra a sessão e invalida os tokens).
2. Notifique o professor por e-mail descrevendo o incidente.
3. Remova o commit com os dados expostos do histórico (use `git rebase` ou `git filter-branch` e faça um force push com autorização do professor).
4. Inicie uma nova sessão do Learn Lab para obter credenciais frescas.

> Credenciais do tipo `AKIA[0-9A-Z]{16}` são chaves de acesso permanentes e representam risco ainda maior se expostas. As credenciais do Learn Lab começam com `ASIA` (temporárias via STS) e expiram automaticamente, mas ainda assim devem ser protegidas durante sua validade.

---

## Referências

- [AWS CLI — Configurando credenciais](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [AWS STS — Credenciais temporárias](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html)
- [Terraform AWS Provider — Autenticação](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration)
- [AWS Academy Learner Lab — Student Guide](https://labs.vocareum.com/main/main.php)
