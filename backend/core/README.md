# backend/core — API + Lógica de negócio

## Endpoints

| Método | Rota                          | Auth |
|--------|-------------------------------|------|
| POST   | `/desocupacoes`               | JWT  |
| GET    | `/desocupacoes?ano=&mes=`     | JWT  |
| GET    | `/desocupacoes/export?ano=&mes=` | JWT |

## Rodar testes

```bash
cd backend/core
python -m venv .venv && source .venv/bin/activate     # Linux/Mac
# .\.venv\Scripts\Activate.ps1                         # Windows
pip install pytest openpyxl boto3
pytest
```

## Deploy

Pré-requisitos:
1. Stack `auth` já deployado → temos `UserPoolId` e `UserPoolClientId`
2. Layers publicadas → temos `DepsLayerArn` e `XlsxLayerArn`

```bash
sam build
sam deploy --guided --stack-name claud-core-dev \
  --parameter-overrides \
    Environment=dev \
    UserPoolId=us-east-1_xxxxx \
    UserPoolClientId=xxxxxxxxxxxxxxxxxxxxxxxxxx \
    AwsRegion=us-east-1 \
    DepsLayerArn=arn:aws:lambda:us-east-1:...:layer:claud-deps:1 \
    XlsxLayerArn=arn:aws:lambda:us-east-1:...:layer:claud-xlsx:1 \
  --capabilities CAPABILITY_IAM
```
