from qa_masking import mask_text, strong_mask_text


def test_mask_text_replaces_core_finance_and_identity_cues():
    text = "김민정 씨 명의 하나은행 계좌가 서울 강서구 주소로 등록됐고 사건번호는 2026형제18000입니다."

    masked = mask_text(text)

    assert "[이름]" in masked
    assert "[은행명]" in masked
    assert "[주소]" in masked
    assert "[사건번호]" in masked


def test_strong_mask_text_replaces_placeholders_with_opaque_tokens():
    text = "[이름] [은행명] [주소] [사건번호]"

    strong = strong_mask_text(text)

    assert "qmqmzkkvvopaa" in strong
    assert "bbbqrrtuuplkz" in strong
    assert "aaeiioouuzzxx" in strong
    assert "xxyyqqppmmrrt" in strong


def test_mask_text_collapses_institution_contact_bundle():
    text = "국민은행 고객보호센터 이상거래확인실입니다. 본인 확인을 진행합니다."

    masked = mask_text(text)

    assert "[기관연락처]" in masked


def test_mask_text_collapses_identifier_bundles():
    text = "김민정 고객님 주소는 서울 강서구이며 사건번호는 2026형제18000, 접수번호는 FR-12345입니다."

    masked = mask_text(text)

    assert "[개인식별묶음]" in masked
    assert "[사건접수식별자]" in masked
