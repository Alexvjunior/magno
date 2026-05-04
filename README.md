# claud - Cadastro de Desocupacoes

Aplicacao web serverless na AWS para cadastro de desocupacoes de imoveis.

## Estrutura

```text
project/
├── frontend/        React + Vite + TS
├── backend/
│   ├── auth/        SAM: Cognito User Pool
│   ├── core/        SAM: API Gateway + Lambdas + DynamoDB + S3 exports
│   └── layers/      Lambda Layers
├── infra/           CloudFormation/SAM templates
└── .github/         CI/CD
```

## Rodar o frontend localmente

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173`. Com `VITE_USE_MOCK=true`, o login aceita qualquer
e-mail/senha e os cadastros ficam em `localStorage`.

## Variaveis de ambiente

- `frontend/.env.local`: uso local/mock.
- `frontend/.env.dev.example`: exemplo para rodar contra a AWS.
- Em CI/CD, os valores reais do Cognito e da API sao lidos dos outputs dos stacks.

## Deploy

Por branch:

- `dev` aciona `deploy-dev` e usa o ambiente AWS `dev`.
- `main` aciona `deploy-prod` e usa o ambiente AWS `prod`.

Os workflows aceitam variaveis do GitHub (`vars`) para sobrescrever os defaults:
`AWS_REGION`, `APP_NAME`, `AWS_DEPLOY_ROLE_ARN_DEV`, `AWS_DEPLOY_ROLE_ARN_PROD`,
`STACK_AUTH_DEV`, `STACK_CORE_DEV`, `STACK_FRONTEND_DEV`, `STACK_AUTH_PROD`,
`STACK_CORE_PROD` e `STACK_FRONTEND_PROD`.

Os workflows `deploy-dev` e `deploy-prod` publicam:

1. Cognito (`backend/auth/template.yaml`).
2. API, DynamoDB e bucket privado de exports (`backend/core/template.yaml`).
3. Frontend privado (`infra/frontend-template.yaml`).

O frontend e hospedado em um bucket S3 privado, com `BlockPublicAccess` habilitado,
e servido apenas pelo CloudFront usando Origin Access Control (OAC). O deploy faz
upload de `frontend/dist` para o bucket privado, aplica cache longo para `assets/`,
`no-cache` para `index.html`, e invalida a distribuicao CloudFront.

Depois do deploy, use o output `CloudFrontDomainName` da stack `claud-frontend-dev`
ou `claud-frontend-prod`. A URL direta do S3 deve permanecer inacessivel.

Durante o deploy, se existir um bucket legado no padrao
`claud-frontend-<env>-<account-id>`, o workflow remove a bucket policy antiga e
habilita `BlockPublicAccess` para impedir leitura publica direta.

## Validacao local

```bash
cd backend/core
pytest

cd ../../frontend
npm run lint
npm run test --if-present
npm run build:dev
npm run build:prod
```
