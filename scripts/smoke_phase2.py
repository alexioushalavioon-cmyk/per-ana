from fastapi.testclient import TestClient
from app.main import app


def main() -> None:
    with TestClient(app) as client:
        case = client.post("/api/v1/cases", json={"title": "Phase 2 Research Case", "analytical_question": "چه بازیگرانی بر اجرای سیاست اثر می‌گذارند؟"}).json()
        cid = case["id"]

        plan = client.post(f"/api/v1/cases/{cid}/research-plans", json={
            "objective": "شناسایی شواهد و مواضع متعارض",
            "queries": ["sample policy actors"],
            "source_types": ["official", "news"],
            "max_sources": 12,
        })
        assert plan.status_code == 201, plan.text

        s1 = client.post(f"/api/v1/cases/{cid}/sources", json={
            "source_type": "official",
            "title": "Official statement",
            "url": "https://example.org/policy?utm_source=test",
            "publisher": "Example Ministry",
            "reliability": "high",
            "raw_text": "نهاد الف اعلام کرده است که اجرای سیاست را پشتیبانی می‌کند. این سیاست نیازمند تأمین بودجه و همکاری نهاد ب است.",
        })
        assert s1.status_code == 201, s1.text
        source1 = s1.json()

        sdup = client.post(f"/api/v1/cases/{cid}/sources", json={
            "source_type": "news",
            "title": "Republished statement",
            "url": "https://example.org/policy?utm_campaign=copy",
            "reliability": "medium",
        })
        assert sdup.status_code == 201, sdup.text
        assert sdup.json()["duplicate_of_id"] == source1["id"]

        auto = client.post(f"/api/v1/cases/{cid}/sources/{source1['id']}/extract", json={"max_claims": 5})
        assert auto.status_code == 200, auto.text
        assert len(auto.json()) >= 1

        e1 = client.post(f"/api/v1/cases/{cid}/evidence", json={
            "source_id": source1["id"],
            "claim_text": "نهاد الف از اجرای سیاست حمایت می‌کند.",
            "claim_key": "موضع نهاد الف نسبت به سیاست",
            "stance": "support",
            "confidence": 0.9,
            "actor_mentions": ["نهاد الف"],
        })
        assert e1.status_code == 201, e1.text
        assert e1.json()["actor_mentions"][0]["actor_label"] == "نهاد الف"

        s2 = client.post(f"/api/v1/cases/{cid}/sources", json={
            "source_type": "news",
            "title": "Contrary report",
            "url": "https://news.example.net/a",
            "reliability": "medium",
            "raw_text": "گزارش دیگری می‌گوید نهاد الف در مرحله اجرا با سیاست مخالفت کرده است.",
        })
        assert s2.status_code == 201, s2.text

        e2 = client.post(f"/api/v1/cases/{cid}/evidence", json={
            "source_id": s2.json()["id"],
            "claim_text": "رفتار اجرایی نهاد الف نشان‌دهنده مخالفت با سیاست است.",
            "claim_key": "موضع نهاد الف نسبت به سیاست",
            "stance": "contradict",
            "confidence": 0.8,
            "actor_mentions": ["نهاد الف"],
        })
        assert e2.status_code == 201, e2.text

        contradictions = client.get(f"/api/v1/cases/{cid}/contradictions")
        assert contradictions.status_code == 200
        assert len(contradictions.json()) == 1

        print({
            "case_id": cid,
            "research_plan": plan.json()["id"],
            "source_count": len(client.get(f"/api/v1/cases/{cid}/sources").json()),
            "evidence_count": len(client.get(f"/api/v1/cases/{cid}/evidence").json()),
            "contradiction_count": len(contradictions.json()),
            "deduplication": "passed",
        })


if __name__ == "__main__":
    main()
