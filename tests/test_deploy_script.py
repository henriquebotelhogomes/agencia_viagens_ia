from pathlib import Path


def test_deploy_script_requires_a_healthy_api_after_release() -> None:
    """O deploy só termina quando a API e dependências essenciais estão prontas."""
    script = Path("scripts/deploy_heroku.ps1").read_text(encoding="utf-8")

    assert "Invoke-RestMethod" in script
    assert '"$HealthUrl"' in script
    assert '$health.status -eq "ok"' in script
    assert "$health.dependencies.database" in script
    assert "$health.dependencies.queue" in script
