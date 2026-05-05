# backend/core — API + Lógica de negócio

## Endpoints

| Método | Rota                          | Auth |
|--------|-------------------------------|------|
| POST   | `/desocupacoes`               | JWT  |
| POST   | `/imoveis`                    | JWT  |
| GET    | `/imoveis`                    | JWT  |
| GET    | `/desocupacoes?ano=&mes=`     | JWT  |
| DELETE | `/desocupacoes/{id}?dataEvento=YYYY-MM-DD` | JWT |
| GET    | `/desocupacoes/export?ano=&mes=` | JWT |

## Rodar testes

```bash
cd backend/core
python -m venv .venv && source .venv/bin/activate     # Linux/Mac
# .\.venv\Scripts\Activate.ps1                         # Windows
pip install pytest openpyxl boto3
pip install -r ../layers/deps-layer/requirements.txt
pytest
```

## Deploy

Pré-requisitos:
1. Stack `auth` já deployado → temos `UserPoolId` e `UserPoolClientId`
2. Layers publicadas → temos `DepsLayerArn` e `XlsxLayerArn`
3. Secret `GOOGLE_SERVICE_ACCOUNT_SECRET_ARN` criado no AWS Secrets Manager com
   o JSON da Service Account que tem acesso de editor na planilha Google Sheets

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
    GoogleServiceAccountSecretArn=arn:aws:secretsmanager:us-east-1:...:secret:claud/dev/google-sheets-service-account \
  --capabilities CAPABILITY_IAM
```
