<#
.SYNOPSIS
    Publica a aplicacao no Google Cloud Run com politicas de Scale-to-Zero (ADR-0016).

.DESCRIPTION
    Compila os containers (API, Worker e Frontend) via Google Cloud Build e publica
    no Google Cloud Run com custo zero operacional quando ocioso (--min-instances=0).

.PARAMETER ProjectId
    ID do projeto no Google Cloud. Se omitido, usa o projeto ativo do gcloud.

.PARAMETER Region
    Regiao de deploy no Google Cloud. Padrao: us-central1.

.EXAMPLE
    powershell -File scripts/deploy_gcp.ps1

.EXAMPLE
    powershell -File scripts/deploy_gcp.ps1 -ProjectId meu-projeto-gcp -Region us-central1
#>
param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null).Trim()
    if (-not $ProjectId) {
        throw "Nenhum projeto GCP especificado. Use -ProjectId ou execute 'gcloud config set project SEU_PROJECT_ID'."
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   🚀 Deploy no Google Cloud Run ($0/mês Scale-to-Zero)   " -ForegroundColor Cyan
Write-Host "   Projeto: $ProjectId" -ForegroundColor Yellow
Write-Host "   Região:  $Region" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Habilitar APIs necessárias
Write-Host "`n[1/5] Habilitando APIs essenciais (Cloud Run & Cloud Build)..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $ProjectId

# 2. Build e Deploy do Backend (API)
Write-Host "`n[2/5] Compilando e publicando a API no Cloud Run..." -ForegroundColor Cyan
$ApiImage = "gcr.io/$ProjectId/voyager-api:latest"

gcloud builds submit --project $ProjectId --tag $ApiImage --file Dockerfile .

gcloud run deploy voyager-api `
    --project $ProjectId `
    --image $ApiImage `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --port 8000 `
    --set-env-vars "APP_ENV=production"

$ApiUrl = (gcloud run services describe voyager-api --project $ProjectId --region $Region --format="value(status.url)").Trim()
Write-Host "   API publicada com sucesso em: $ApiUrl" -ForegroundColor Green

# 3. Deploy do Worker (Processamento em segundo plano)
Write-Host "`n[3/5] Publicando o Worker SAQ no Cloud Run..." -ForegroundColor Cyan
gcloud run deploy voyager-worker `
    --project $ProjectId `
    --image $ApiImage `
    --region $Region `
    --platform managed `
    --no-allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --command "saq","src.worker.settings.settings" `
    --set-env-vars "APP_ENV=production"

Write-Host "   Worker configurado com sucesso." -ForegroundColor Green

# 4. Build e Deploy do Frontend (Next.js)
Write-Host "`n[4/5] Compilando e publicando o Frontend Next.js no Cloud Run..." -ForegroundColor Cyan
$WebImage = "gcr.io/$ProjectId/voyager-web:latest"

Set-Location frontend
try {
    gcloud builds submit --project $ProjectId --tag $WebImage `
        --substitutions=_API_URL=$ApiUrl .

    gcloud run deploy voyager-web `
        --project $ProjectId `
        --image $WebImage `
        --region $Region `
        --platform managed `
        --allow-unauthenticated `
        --memory 512Mi `
        --cpu 1 `
        --min-instances 0 `
        --max-instances 2 `
        --port 3000
} finally {
    Set-Location ..
}

$WebUrl = (gcloud run services describe voyager-web --project $ProjectId --region $Region --format="value(status.url)").Trim()
Write-Host "   Frontend publicado com sucesso em: $WebUrl" -ForegroundColor Green

# 5. Validação de Saúde
Write-Host "`n[5/5] Verificando integridade da API..." -ForegroundColor Cyan
try {
    $HealthUrl = "$ApiUrl/health"
    $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 15
    Write-Host "   Health check da API ($HealthUrl): $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "   Aviso: API inicializando ou aguardando conexoes: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   ✅ Deploy no Google Cloud concluído com sucesso!" -ForegroundColor Green
Write-Host "   Frontend: $WebUrl" -ForegroundColor Cyan
Write-Host "   API Docs: $ApiUrl/docs" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
