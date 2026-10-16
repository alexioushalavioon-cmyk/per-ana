from fastapi.testclient import TestClient
from app.main import app


def main() -> None:
    with TestClient(app) as client:
        case = client.post("/api/v1/cases", json={"title": "Phase 3 Actor Case", "analytical_question": "کدام بازیگران قدرت و نقش اجرایی دارند؟"}).json()
        cid = case["id"]
        source = client.post(f"/api/v1/cases/{cid}/sources", json={
            "source_type": "official", "title": "Actor source", "url": "https://example.org/actor",
            "reliability": "high", "raw_text": "وزارت ارتباطات اعلام کرد اجرای سیاست نیازمند همکاری سازمان تنظیم مقررات است."
        }).json()
        e1 = client.post(f"/api/v1/cases/{cid}/evidence", json={
            "source_id": source["id"], "claim_text": "وزارت ارتباطات مسئول هماهنگی اجرای سیاست است.",
            "claim_key": "نقش اجرایی وزارت ارتباطات", "stance": "support", "confidence": 0.92,
            "actor_mentions": ["وزارت ارتباطات", "سازمان تنظیم مقررات"]
        })
        assert e1.status_code == 201, e1.text
        e2 = client.post(f"/api/v1/cases/{cid}/evidence", json={
            "source_id": source["id"], "claim_text": "وزارت ارتباطات و فناوری اطلاعات اختیار رسمی در این حوزه دارد.",
            "claim_key": "قدرت وزارت ارتباطات", "stance": "support", "confidence": 0.9,
            "actor_mentions": ["وزارت ارتباطات و فناوری اطلاعات"]
        })
        assert e2.status_code == 201, e2.text
        canon = client.post(f"/api/v1/cases/{cid}/actors/canonicalize")
        assert canon.status_code == 200, canon.text
        actors = canon.json()["actors"]
        assert len(actors) == 3, actors

        # Merge the long ministry alias into the shorter canonical actor.
        ministry_short = next(a for a in actors if a["canonical_name"] == "وزارت ارتباطات")
        ministry_long = next(a for a in actors if a["canonical_name"] == "وزارت ارتباطات و فناوری اطلاعات")
        merged = client.post(f"/api/v1/cases/{cid}/actors/merge", json={"source_actor_id": ministry_long["id"], "target_actor_id": ministry_short["id"]})
        assert merged.status_code == 200, merged.text
        assert merged.json()["evidence_count"] == 2

        candidates = client.get(f"/api/v1/cases/{cid}/actors/duplicate-candidates")
        assert candidates.status_code == 200

        baseline = client.post(f"/api/v1/cases/{cid}/actors/{ministry_short['id']}/synthesize-baseline")
        assert baseline.status_code == 200, baseline.text
        assert len(baseline.json()["roles"]) >= 1
        assert len(baseline.json()["power"]) >= 1

        # Analyst/AI enrichment uses the same canonical component tables.
        for payload in [
            {"kind": "role", "text": "Decision Maker", "confidence": 0.9, "evidence_ids": [e1.json()["id"]], "stated_or_inferred": "evidence_backed"},
            {"kind": "power", "component_type": "network_influence", "level": "high", "rationale": "اختیار رسمی در حوزه سیاست", "confidence": 0.88, "evidence_ids": [e2.json()["id"]]},
            {"kind": "interest", "text": "حفظ نقش نهادی در اجرای سیاست", "component_type": "institutional", "importance": "high", "confidence": 0.72, "evidence_ids": [e1.json()["id"]]},
            {"kind": "position", "level": "conditional_support", "declared_position": "support", "observed_behaviour": "conditional cooperation", "confidence": 0.76, "evidence_ids": [e1.json()["id"]]},
            {"kind": "constraint", "component_type": "implementation", "text": "وابستگی به همکاری تنظیم‌گر", "level": "medium", "confidence": 0.7, "evidence_ids": [e1.json()["id"]]},
        ]:
            response = client.post(f"/api/v1/cases/{cid}/actors/{ministry_short['id']}/components", json=payload)
            assert response.status_code == 201, response.text

        regulator = next(a for a in client.get(f"/api/v1/cases/{cid}/actors").json() if a["canonical_name"] == "سازمان تنظیم مقررات")
        rel = client.post(f"/api/v1/cases/{cid}/relationships", json={
            "source_actor_id": ministry_short["id"], "target_actor_id": regulator["id"],
            "relationship_type": "implementation_dependency", "direction": "directed", "strength": "high",
            "formality": "formal", "confidence": 0.8, "evidence_ids": [e1.json()["id"]],
            "rationale": "اجرای سیاست نیازمند همکاری تنظیم‌گر است"
        })
        assert rel.status_code == 201, rel.text

        profile = client.get(f"/api/v1/cases/{cid}/actors/{ministry_short['id']}")
        assert profile.status_code == 200, profile.text
        body = profile.json()
        assert body["coverage"]["power"] in {"medium", "high"}
        assert body["coverage"]["evidence"] == "medium"
        assert len(body["relationships"]) == 1

        deep = client.post(f"/api/v1/cases/{cid}/actors/{ministry_short['id']}/deep-research")
        assert deep.status_code == 201, deep.text
        assert deep.json()["processing_level"] == "deep"

        print({
            "case_id": cid,
            "actor_count_after_merge": len(client.get(f"/api/v1/cases/{cid}/actors").json()),
            "ministry_evidence_count": merged.json()["evidence_count"],
            "power_dimensions": len(body["power"]),
            "relationships": len(body["relationships"]),
            "deep_research_plan": deep.json()["research_plan_id"],
            "actor_intelligence": "passed",
        })


if __name__ == "__main__":
    main()
