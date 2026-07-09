from datetime import date, timedelta

from app.models.brand import Brand
from app.models.enums import BusinessStructure, DocumentType
from app.services.onboard_service import compute_document_status, seed_checklist_for_brand, upsert_document


def test_checklist_includes_gst_for_not_incorporated_brand(db_session):
    brand = Brand(name="Test", structure=BusinessStructure.NOT_INCORPORATED)
    db_session.add(brand)
    db_session.commit()

    items = seed_checklist_for_brand(db_session, brand)

    requirements = [i.requirement for i in items]
    assert any("business structure" in r.lower() for r in requirements)
    assert any("gst" in r.lower() for r in requirements)


def test_checklist_skips_structure_step_for_incorporated_brand(db_session):
    brand = Brand(name="Test", structure=BusinessStructure.PVT_LTD)
    db_session.add(brand)
    db_session.commit()

    items = seed_checklist_for_brand(db_session, brand)

    requirements = [i.requirement for i in items]
    assert not any("decide a business structure" in r.lower() for r in requirements)


def test_checklist_adds_category_specific_items(db_session):
    brand = Brand(name="Test Food Co", category="food", structure=BusinessStructure.NOT_INCORPORATED)
    db_session.add(brand)
    db_session.commit()

    items = seed_checklist_for_brand(db_session, brand)

    assert any("fssai" in i.requirement.lower() for i in items)


def test_checklist_seeding_is_idempotent(db_session):
    brand = Brand(name="Test", structure=BusinessStructure.NOT_INCORPORATED)
    db_session.add(brand)
    db_session.commit()

    first = seed_checklist_for_brand(db_session, brand)
    second = seed_checklist_for_brand(db_session, brand)

    assert len(first) == len(second)


def test_compute_document_status_transitions():
    assert compute_document_status(None, has_file=False) == compute_document_status(None, has_file=False)
    from app.models.enums import DocumentStatus

    assert compute_document_status(None, has_file=False) == DocumentStatus.MISSING
    assert compute_document_status(None, has_file=True) == DocumentStatus.UPLOADED
    assert compute_document_status(date.today() - timedelta(days=1), has_file=True) == DocumentStatus.EXPIRED
    assert compute_document_status(date.today() + timedelta(days=10), has_file=True) == DocumentStatus.EXPIRING_SOON
    assert compute_document_status(date.today() + timedelta(days=100), has_file=True) == DocumentStatus.UPLOADED


def test_upsert_document_creates_new_version_on_reupload(db_session):
    brand = Brand(name="Test", structure=BusinessStructure.NOT_INCORPORATED)
    db_session.add(brand)
    db_session.commit()

    doc_v1 = upsert_document(
        db_session, brand, DocumentType.GST, "GST Cert", "vault/gst-v1.pdf", None, None, "27ABCDE1234F1Z5"
    )
    assert len(doc_v1.versions) == 1

    doc_v2 = upsert_document(
        db_session, brand, DocumentType.GST, "GST Cert (renewed)", "vault/gst-v2.pdf", "renewed", None, "27ABCDE1234F1Z5"
    )
    assert doc_v1.id == doc_v2.id  # same document, new version — not a duplicate record
    assert len(doc_v2.versions) == 2
    assert doc_v2.current_file_ref == "vault/gst-v2.pdf"
