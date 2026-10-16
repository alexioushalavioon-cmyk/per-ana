import pytest

from app.core.config import Settings


def test_dev_auth_forbidden_in_production(tmp_path) -> None:
    cfg = Settings(
        app_env="production",
        auth_mode="dev",
        database_url="sqlite:///./test.sqlite3",
        local_storage_path=str(tmp_path),
    )
    with pytest.raises(RuntimeError, match="AUTH_MODE=dev"):
        cfg.validate_runtime()


def test_r2_requires_credentials(tmp_path) -> None:
    cfg = Settings(
        storage_backend="r2",
        database_url="sqlite:///./test.sqlite3",
        local_storage_path=str(tmp_path),
        r2_endpoint_url=None,
        r2_access_key_id=None,
        r2_secret_access_key=None,
    )
    with pytest.raises(RuntimeError, match="Missing R2 settings"):
        cfg.validate_runtime()
