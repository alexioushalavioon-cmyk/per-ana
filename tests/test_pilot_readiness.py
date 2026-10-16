import json
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.services.ai import estimate_cost, generate_json, route_model


@pytest.mark.asyncio
async def test_model_router_and_openai_adapter(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    low = route_model("evidence_extraction", complexity="low")
    strong = route_model("policy_strategy", critical=True)
    assert low.model == settings.ai_model_low
    assert strong.model == settings.ai_model_strong
    assert strong.verification_required is True

    async def handler(request: httpx.Request):
        body = json.loads(request.content)
        assert body["model"] == settings.ai_model_low
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "output": [{"content": [{"type": "output_text", "text": '{"items":["ok"]}'}]}],
                "usage": {"input_tokens": 1000, "output_tokens": 100},
            },
        )

    transport = httpx.MockTransport(handler)
    result = await generate_json(
        task_type="evidence_extraction",
        complexity="low",
        instructions="test",
        input_text="test",
        schema_name="test_schema",
        schema={
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
            "required": ["items"],
            "additionalProperties": False,
        },
        transport=transport,
    )
    assert result.data == {"items": ["ok"]}
    assert result.response_id == "resp_test"
    assert result.estimated_cost_usd == estimate_cost(settings.ai_model_low, 1000, 100)


def test_supabase_rls_manifest_is_tenant_scoped():
    sql = (Path(__file__).parents[3] / "deployment" / "supabase" / "rls.sql").read_text()
    assert "enable row level security" in sql.lower()
    assert "auth.uid()" in sql
    assert "cases_owner_all" in sql
    assert "service_role" in sql
    assert "revoke all" in sql.lower()


def test_frontend_package_has_reproducible_build_script():
    package = json.loads((Path(__file__).parents[2] / "web" / "package.json").read_text())
    assert package["scripts"]["build"] == "next build"
    assert package["dependencies"]["next"] == "16.4.1"


def test_phase9_frontend_auth_is_wired_to_api():
    root = Path(__file__).parents[2] / "web"
    package = json.loads((root / "package.json").read_text())
    assert "@supabase/supabase-js" in package["dependencies"]
    api = (root / "lib" / "api.ts").read_text()
    assert "Authorization" in api
    assert "Bearer ${token}" in api
    assert "authenticatedFetch" in api
    auth_page = (root / "app" / "auth" / "page.tsx").read_text()
    assert "signInWithPassword" in auth_page
    assert "signUp" in auth_page


def test_phase9_production_deployment_contracts_exist():
    repo = Path(__file__).parents[3]
    env = (repo / "deployment" / "pilot.env.example").read_text()
    for key in [
        "AUTH_MODE=supabase", "SUPABASE_JWT_ISSUER", "STORAGE_BACKEND=r2",
        "JOB_BACKEND=redis", "AI_PROVIDER=openai", "NEXT_PUBLIC_AUTH_MODE=supabase"
    ]:
        assert key in env
    for name in ["api.toml", "worker.toml", "web.toml"]:
        assert (repo / "deployment" / "railway" / name).exists()
    api_docker = (repo / "apps" / "api" / "Dockerfile").read_text()
    web_docker = (repo / "apps" / "web" / "Dockerfile").read_text()
    assert "${PORT:-8000}" in api_docker
    assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" in web_docker


def test_phase9_jwt_verifies_issuer_configuration():
    auth = (Path(__file__).parents[1] / "app" / "core" / "auth.py").read_text()
    config = (Path(__file__).parents[1] / "app" / "core" / "config.py").read_text()
    assert "issuer=settings.supabase_jwt_issuer" in auth
    assert "supabase_jwt_issuer" in config
