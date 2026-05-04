# backend/auth — Cognito User Pool

## Deploy

```bash
sam build
sam deploy --guided --stack-name claud-auth-dev \
  --parameter-overrides Environment=dev AppName=claud \
  --capabilities CAPABILITY_IAM
```

Saídas (Outputs):
- `UserPoolId` — usar em `frontend/.env.dev` como `VITE_USER_POOL_ID`
- `UserPoolClientId` — usar como `VITE_USER_POOL_CLIENT_ID`
- `UserPoolArn` — consumido pelo stack `core` (JWT authorizer no API Gateway)

## Criar primeiro usuário (admin)

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <UserPoolId> \
  --username alex@example.com \
  --user-attributes Name=email,Value=alex@example.com Name=name,Value=Alex \
  --temporary-password "TempPass!2026"
```

Na primeira entrada, o Cognito força a troca de senha (fluxo `NEW_PASSWORD_REQUIRED`).
