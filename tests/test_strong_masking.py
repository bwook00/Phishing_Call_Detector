from strong_masking import PLACEHOLDER_TOKEN_MAP, apply_strong_masking


def test_apply_strong_masking_replaces_known_placeholders_with_fixed_tokens():
    text = "[기관명] [이름] [은행명] [사건번호] [주소]"

    masked = apply_strong_masking(text)

    assert masked == "uiuiufawaefiiifji qmqmzkkvvopaa bbbqrrtuuplkz xxyyqqppmmrrt aaeiioouuzzxx"


def test_apply_strong_masking_leaves_unknown_text_unchanged():
    text = "고객센터입니다. 본인 확인을 진행합니다."

    masked = apply_strong_masking(text)

    assert masked == text


def test_placeholder_token_map_values_are_unique():
    values = list(PLACEHOLDER_TOKEN_MAP.values())

    assert len(values) == len(set(values))


def test_apply_strong_masking_replaces_bundle_placeholders_with_fixed_tokens():
    text = "[기관연락처] [개인식별묶음] [사건접수식별자]"

    masked = apply_strong_masking(text)

    assert "[기관연락처]" not in masked
    assert "[개인식별묶음]" not in masked
    assert "[사건접수식별자]" not in masked
