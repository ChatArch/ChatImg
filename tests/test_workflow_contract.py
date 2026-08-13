from pathlib import Path


def test_publish_workflow_uses_trusted_publishing_with_release_guards():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" not in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "Check manual release branch" not in workflow
    assert "github.event_name == 'workflow_dispatch'" not in workflow
    assert "Check tag matches package version" in workflow
    assert "Check release commit is on default branch" in workflow
    assert 'git fetch --no-tags origin "${DEFAULT_BRANCH}:refs/remotes/origin/${DEFAULT_BRANCH}"' in workflow
    assert "Check PyPI version" in workflow
    assert "Fail when version is already on PyPI" in workflow
    assert "Stop when version is already on PyPI" not in workflow
    assert "secrets.PYPI" not in workflow
    assert "TWINE_PASSWORD" not in workflow
    assert "PYPI_API_TOKEN" not in workflow
