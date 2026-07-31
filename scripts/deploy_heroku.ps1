<#
.SYNOPSIS
    Publica a aplicacao no Heroku via Container Registry (ADR-0015).

.DESCRIPTION
    Constroi as tres imagens (web, worker, release) a partir do Dockerfile
    multi-stage e as envia ao registry do Heroku, liberando em seguida.

    Por que Container Registry e nao `git push heroku`:
      - O Git Credential Manager do Windows abre uma janela de autenticacao e
        travava a publicacao em ambiente nao-interativo.
      - O build acontece localmente, aproveitando o cache de layers. O container
        stack do Heroku nao faz cache, entao o build remoto e sempre completo.

    Por que `oci-mediatypes=false`:
      - O Docker Desktop com containerd image store grava manifests em formato
        OCI, e o registry do Heroku aceita apenas Docker manifest v2. Sem a
        flag, o push falha com `error from registry: unsupported`.

.PARAMETER App
    Nome da aplicacao no Heroku. Padrao: voyager-ia.

.PARAMETER SkipRelease
    Apenas envia as imagens, sem liberar. Util para preparar um rollout.

.EXAMPLE
    pwsh scripts/deploy_heroku.ps1

.EXAMPLE
    pwsh scripts/deploy_heroku.ps1 -App voyager-staging
#>
param(
    [string]$App = "voyager-ia",
    [switch]$SkipRelease
)

$ErrorActionPreference = "Stop"
$processTypes = @("web", "worker", "release")

Write-Host "== Autenticando no Container Registry ==" -ForegroundColor Cyan
heroku container:login
if ($LASTEXITCODE -ne 0) { throw "Falha no container:login. Rode 'heroku login' primeiro." }

foreach ($type in $processTypes) {
    Write-Host "== Build + push: $type ==" -ForegroundColor Cyan
    $target = "registry.heroku.com/$App/$type"
    $output = docker buildx build `
        --target $type `
        --provenance=false --sbom=false `
        --output "type=registry,name=$target,oci-mediatypes=false,push=true" `
        . 2>&1 | Out-String

    if ($output -notmatch "pushing manifest") {
        Write-Host $output
        throw "Push de '$type' falhou."
    }
    Write-Host "   $type enviado" -ForegroundColor Green
}

if ($SkipRelease) {
    Write-Host "Imagens enviadas. Release nao executado (-SkipRelease)." -ForegroundColor Yellow
    exit 0
}

Write-Host "== Release (a imagem 'release' aplica as migrations) ==" -ForegroundColor Cyan
heroku container:release @processTypes --app $App
if ($LASTEXITCODE -ne 0) { throw "container:release falhou." }

Write-Host "`n== Estado dos dynos ==" -ForegroundColor Cyan
heroku ps --app $App

Write-Host "`nVerifique a saude da aplicacao:" -ForegroundColor Cyan
Write-Host "  curl https://$App.herokuapp.com/health"
Write-Host "  uv run python -m scripts.e2e_smoke --base-url https://$App.herokuapp.com"
