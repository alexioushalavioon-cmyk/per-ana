from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.main import app
from app.models.audit import AuditEvent


def main() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/cases",
            json={
                "title": "پرونده آزمایشی مرحله اول",
                "description": "تست مسیر کامل Phase 1",
                "analytical_question": "بازیگران اصلی این مسئله چه کسانی هستند؟",
                "geographic_scope": "ایران",
                "processing_mode": "standard",
                "sensitivity": "internal",
            },
        )
        created.raise_for_status()
        case = created.json()

        fetched = client.get(f"/api/v1/cases/{case['id']}")
        fetched.raise_for_status()
        assert fetched.json()["title"] == case["title"]

        upload = client.post(
            f"/api/v1/cases/{case['id']}/files",
            files={"upload": ("source.txt", b"PER ANA evidence source", "text/plain")},
        )
        upload.raise_for_status()
        file_data = upload.json()
        assert file_data["size_bytes"] > 0
        assert file_data["ingestion_status"] == "uploaded"

        listed = client.get(f"/api/v1/cases/{case['id']}/files")
        listed.raise_for_status()
        assert any(item["id"] == file_data["id"] for item in listed.json())

    with SessionLocal() as session:
        audit_count = session.scalar(
            select(func.count()).select_from(AuditEvent).where(AuditEvent.case_id == case["id"])
        )
        assert audit_count is not None and audit_count >= 2

    print("PHASE1_SMOKE_OK")
    print(f"case_id={case['id']}")
    print(f"file_id={file_data['id']}")
    print(f"audit_events={audit_count}")


if __name__ == "__main__":
    main()
