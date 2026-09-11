from pathlib import Path


def test_deploy_script_targets_gcp_cloud_run_and_validates_health() -> None:
    """O script de deploy no Google Cloud Run compila e valida a integridade da API."""
    script = Path("scripts/deploy_gcp.ps1").read_text(encoding="utf-8")

    assert "gcloud run deploy voyager-api" in script
    assert "Invoke-RestMethod" in script
    assert "$HealthUrl" in script
    assert "--min-instances 0" in script
    assert "--max-instances 2" in script
