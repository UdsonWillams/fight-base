# Configuração do Google OAuth 2.0 para FightBase

Este guia detalha como configurar a autenticação Google OAuth 2.0 no Google Cloud Platform para o projeto FightBase.

## Pré-requisitos

- Conta Google (Gmail)
- Acesso ao [Google Cloud Console](https://console.cloud.google.com)
- Projeto FightBase rodando localmente

## Passo a Passo

### 1️⃣ Acessar o Google Cloud Console

1. Acesse: [https://console.cloud.google.com](https://console.cloud.google.com)
2. Faça login com sua conta Google

### 2️⃣ Criar um Novo Projeto

1. No topo da página, clique no **seletor de projetos**
2. Clique em **"NEW PROJECT"**
3. Preencha:
   - **Project name**: `FightBase Auth` (ou nome de sua preferência)
   - **Location**: Deixe como "No organization" (ou selecione sua organização)
4. Clique em **"CREATE"**
5. Aguarde alguns segundos e selecione o projeto criado no seletor

### 3️⃣ Habilitar APIs Necessárias

1. No menu lateral (☰), navegue para: **APIs & Services** → **Library**
2. Busque por **"Google+ API"**
3. Clique no resultado e depois em **"ENABLE"**
4. Opcionalmente, busque e habilite também **"People API"** (para informações de perfil)

### 4️⃣ Configurar OAuth Consent Screen

#### PAREI AQUI <<<<<<<<<<< >>>>>>>>>>>
#### Configuração Inicial

1. Menu lateral → **APIs & Services** → **OAuth consent screen**
2. Selecione **"External"** como User Type
3. Clique em **"CREATE"**

#### App Information

- **App name**: `FightBase`
- **User support email**: seu-email@gmail.com
- **App logo**: (opcional) Upload uma imagem 120x120px
- **Application home page**: `http://localhost:8080`
- **Developer contact information**: seu-email@gmail.com

Clique em **"SAVE AND CONTINUE"**

#### Scopes

1. Clique em **"ADD OR REMOVE SCOPES"**
2. Marque os seguintes scopes:
   - `openid`
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
3. Clique em **"UPDATE"**
4. Clique em **"SAVE AND CONTINUE"**

#### Test Users

> ⚠️ Apenas necessário se o app estiver em modo **Testing**

1. Clique em **"ADD USERS"**
2. Adicione seu email e emails de outros testadores
3. Clique em **"ADD"** e depois **"SAVE AND CONTINUE"**

#### Resumo

Revise as informações e clique em **"BACK TO DASHBOARD"**

### 5️⃣ Criar OAuth 2.0 Client ID

1. Menu lateral → **APIs & Services** → **Credentials**
2. Clique em **"+ CREATE CREDENTIALS"**
3. Selecione **"OAuth client ID"**
4. Configure:

   - **Application type**: `Web application`
   - **Name**: `FightBase Web Client`

   **Authorized JavaScript origins**:
   - `http://localhost:8080`
   - `http://localhost:8080`

   **Authorized redirect URIs** ⚠️ **IMPORTANTE**:
   - `http://localhost:8080/api/v1/auth/google/callback`

5. Clique em **"CREATE"**

### 6️⃣ Salvar Credenciais

Uma janela modal mostrará:

```
Your Client ID
123456789-abcdefg.apps.googleusercontent.com

Your Client Secret
GOCSPX-xxxxxxxxxxxxxx
```

**Copie ambos os valores!**

### 7️⃣ Configurar Variáveis de Ambiente

No arquivo `.env` do projeto FightBase, adicione:

```env
# Google OAuth 2.0
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8080/api/v1/auth/google/callback
```

> 🔒 **Segurança**: Nunca commite o arquivo `.env` no Git! Ele já está no `.gitignore`.

### 8️⃣ Testar a Configuração

1. Inicie o servidor FightBase:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Acesse: `http://localhost:8080`
3. Clique em **"Continuar com Google"**
4. Você deve ser redirecionado para a tela de login do Google

**Se aparecer erro "Error 400: redirect_uri_mismatch"**:
- Verifique se a URI no código corresponde exatamente à URI configurada no GCP
- Certifique-se de que não há espaços extras ou barras `/` a mais

## Troubleshooting

### Erro: "Access blocked: This app's request is invalid"

**Causa**: OAuth consent screen não foi configurado corretamente.

**Solução**: Volte para **OAuth consent screen** e verifique se todos os campos obrigatórios foram preenchidos.

### Erro: "This app isn't verified"

**Causa**: App em modo Testing com usuário não cadastrado.

**Solução**:
1. Adicione seu email em **Test users**
2. OU clique em "Advanced" → "Go to FightBase (unsafe)" para continuar

### Erro: "redirect_uri_mismatch"

**Causa**: A URI de callback no código não corresponde às URIs autorizadas no GCP.

**Solução**:
1. Verifique se a URI no `.env` é exatamente: `http://localhost:8080/api/v1/auth/google/callback`
2. Vá em **Credentials** → Clique no Client ID criado
3. Em **Authorized redirect URIs**, confirme que a URI está correta
4. Reinicie o servidor após alterar `.env`

### Erro: "invalid_client"

**Causa**: Client ID ou Client Secret incorretos.

**Solução**:
1. Vá em **Credentials** e copie novamente as credenciais
2. Verifique se não há espaços extras no `.env`

## Produção

Para produção, você precisará:

1. **Publicar o app**:
   - **OAuth consent screen** → **"PUBLISH APP"**
   - Preencher formulário de verificação do Google
   - Aguardar aprovação (pode levar dias/semanas)

2. **Atualizar URIs**:
   - Em **Credentials**, edite o Client ID
   - Adicione URLs de produção:
     - `https://seudominio.com`
     - `https://seudominio.com/api/v1/auth/google/callback`

3. **Atualizar `.env` de produção**:
   ```env
   GOOGLE_REDIRECT_URI=https://seudominio.com/api/v1/auth/google/callback
   ```

## Referências

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/) - Para testar fluxos OAuth
