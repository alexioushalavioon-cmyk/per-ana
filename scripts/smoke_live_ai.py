"""Optional live AI smoke test. Requires AI_PROVIDER=openai and OPENAI_API_KEY."""
import asyncio
from app.services.ai import AIProviderUnavailable, generate_json

async def main():
    result = await generate_json(
        task_type="metadata",
        complexity="low",
        instructions="Return the supplied word exactly as value.",
        input_text="PER ANA",
        schema_name="smoke",
        schema={"type":"object","properties":{"value":{"type":"string"}},"required":["value"],"additionalProperties":False},
    )
    assert result.data.get("value")
    print({"model":result.model,"cost":result.estimated_cost_usd,"data":result.data})

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AIProviderUnavailable as exc:
        raise SystemExit(str(exc))
