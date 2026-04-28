#!/usr/bin/env python3

from __future__ import annotations

import re

from strong_masking import apply_strong_masking


BANK_PATTERN = r"(국민은행|신한은행|하나은행|우리은행|농협은행|카카오뱅크|토스뱅크|IBK기업은행)"
NAME_PATTERN = r"([김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구민진지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모남궁탁]?[가-힣]{2,3})"
ADDRESS_PATTERN = r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n,]{0,12}(구|군|시)"
CASE_PATTERN = r"((20\d{2}[가-힣]{1,3}\d{3,6})|(20\d{2}형제\d{3,6})|(20\d{2}조사\d{3,6})|(FR-\d{5}))"
INSTITUTION_CONTACT_PATTERN = (
    r"(국민은행|신한은행|하나은행|우리은행|농협은행|카카오뱅크|토스뱅크|IBK기업은행)?\s*"
    r"(고객보호센터|계정보호팀|이상거래확인실|보안점검팀|고객센터)"
)
IDENTIFIER_BUNDLE_PATTERN = r"\[이름\]\s*고객님[^.\n]{0,20}\[주소\]"
CASE_RECEIPT_BUNDLE_PATTERN = r"사건번호는\s*\[사건번호\],\s*접수번호는\s*\[사건번호\]"


def mask_text(text: str) -> str:
    text = re.sub(BANK_PATTERN, "[은행명]", text)
    text = re.sub(ADDRESS_PATTERN, "[주소]", text)
    text = re.sub(CASE_PATTERN, "[사건번호]", text)
    text = re.sub(r"([가-힣]{2,4})\s*고객님", "[이름] 고객님", text)
    text = re.sub(r"([가-힣]{2,4})\s*씨", "[이름] 씨", text)
    text = re.sub(NAME_PATTERN + r"\s+명의", "[이름] 명의", text)
    text = re.sub(INSTITUTION_CONTACT_PATTERN, "[기관연락처]", text)
    text = re.sub(IDENTIFIER_BUNDLE_PATTERN, "[개인식별묶음]", text)
    text = re.sub(CASE_RECEIPT_BUNDLE_PATTERN, "[사건접수식별자]", text)
    return text


def strong_mask_text(text: str) -> str:
    return apply_strong_masking(mask_text(text))
