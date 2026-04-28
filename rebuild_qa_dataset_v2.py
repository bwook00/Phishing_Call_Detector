#!/usr/bin/env python3
"""Rebuild QA dataset by regenerating non-phishing splits with richer patterns."""

from __future__ import annotations

import csv
import hashlib
import random
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path("data")
VOICE_CORPUS = DATA_DIR / "voicephishing_corpus_v2.csv"
BANK_QUEUE = DATA_DIR / "bank_call_qa_template_queue.csv"
IR_QUEUE = DATA_DIR / "irrelevant_qa_template_queue.csv"
OUT_PATH = DATA_DIR / "voicephishing_qa_dataset.csv"

QUESTION = "이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라."

BANKS = ["국민은행", "신한은행", "카카오뱅크", "하나은행", "우리은행", "IBK기업은행", "토스뱅크", "농협은행"]
NAMES = ["김민수", "이서연", "박지훈", "최유나", "한재영", "문예린", "정주은", "윤하늘", "조성민", "김도윤", "오세라", "백지수", "임채린", "이찬우"]
BRANCHES = ["강남", "잠실", "연수", "홍대", "부산", "광주", "수원", "대구"]
CARD_TYPES = ["체크카드", "신용카드", "모바일카드", "프리미엄카드", "포인트카드"]
APT_DONG = ["101", "203", "307", "814", "1201", "1403"]
DOCTOR = ["박진우", "이윤서", "최은영", "한가람", "유정민"]
ORGS = ["법무팀", "행사팀", "홍보팀", "행정지원팀", "세무상담팀"]
DELIVERY_COMPANIES = ["CJ대한통운", "한진", "우체국택배", "로젠"]
DISTRICTS = ["서울시 강남구", "부산시 해운대구", "대구시 동구", "인천시 연수구", "광주시 서구", "부산시 금정구"]
ALT_BANKS = ["국민은행", "신한은행", "하나은행", "우리은행", "카카오뱅크", "토스뱅크", "농협은행", "IBK기업은행"]
PROSECUTION_OFFICES = ["서울남부지방검찰청", "서울동부지방검찰청", "인천지방검찰청", "수원지방검찰청"]
COURTS = ["서울중앙지방법원", "서울남부지방법원", "인천지방법원", "수원지방법원"]
POLICE_UNITS = ["사이버수사대", "금융범죄수사팀", "반부패수사팀", "형사4팀"]
COMPANIES = ["새한솔루션", "미래에이전시", "더원디자인", "시티로직", "메트로웍스", "에이플랩"]
AREAS = ["서울 양천구", "서울 송파구", "인천 부평구", "수원 영통구", "대전 서구", "부산 남구"]
FAMILY_ROLES = ["엄마", "아빠", "이모", "삼촌"]
RELATION_NAMES = ["서준", "하린", "도윤", "지안", "유진", "민재", "소율", "예준"]
APP_NAMES = ["보안확인 앱", "원격지원 앱", "안심점검 앱", "인증보호 앱"]
COMMON_VICTIM_ACKS = [
    "피해자: 네, 알겠습니다.",
    "피해자: 일단 이해했습니다.",
    "피해자: 네, 확인했습니다.",
]


def _replace_all(text: str, replacements: dict[str, str]) -> str:
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _regex_replace(text: str, pattern: str, repl_fn) -> str:
    return re.sub(pattern, repl_fn, text)


def _dedupe_adjacent_lines(text: str) -> str:
    lines = text.splitlines()
    deduped = []
    for line in lines:
        if deduped and deduped[-1] == line:
            continue
        deduped.append(line)
    return "\n".join(deduped)


def _bank_pair(rng: random.Random) -> tuple[str, str]:
    a = _choice(rng, ALT_BANKS)
    b = _choice(rng, [x for x in ALT_BANKS if x != a])
    return a, b


def _join_with_and(a: str, b: str) -> str:
    suffix = "과" if a[-1] in "bcdfghjklmnpqrstvwxyz" else ("과" if (ord(a[-1]) - ord("가")) % 28 else "와")
    return f"{a}{suffix} {b}"


def _with_euro(word: str) -> str:
    if word[-1] in "bcdfghjklmnpqrstvwxyz":
        return f"{word}으로"
    jong = (ord(word[-1]) - ord("가")) % 28 if "가" <= word[-1] <= "힣" else 0
    if jong == 0:
        return f"{word}로"
    if jong == 8:
        return f"{word}로"
    return f"{word}으로"


def _clean_voice_text(text: str, rng: random.Random) -> str:
    text = re.sub(r"사기범: 계속 진행하겠습니다\.\n?", "", text)
    text = re.sub(r"(피해자: 네, 이해했어요\.\n){2,}", "피해자: 네, 알겠습니다.\n", text)
    text = re.sub(r"피해자: 네, 이해했어요\.", lambda m: _choice(rng, COMMON_VICTIM_ACKS), text)
    text = re.sub(r"사기범: [^\n]*중앙지방검찰청", lambda m: f"사기범: {_choice(rng, PROSECUTION_OFFICES)}", text)
    text = re.sub(r"\[[^\]]*중앙지방법원\]", lambda m: f"[{_choice(rng, COURTS)}]", text)
    text = re.sub(r"사기범: \[[^\]]*지방법원\]", lambda m: f"사기범: [{_choice(rng, COURTS)}]", text)
    text = re.sub(
        r"현재 주소는 [^,\n]+, 직장은 [^,\n]+로 조회되는데 맞습니까\?",
        lambda m: f"현재 주소는 {_choice(rng, AREAS)}, 직장은 {_choice(rng, COMPANIES)}로 조회되는데 맞습니까?",
        text,
    )
    text = re.sub(
        r"거주지는 [^,\n]+인데 집으로 가면 가족 접촉 가능성이 커서 안 됩니다\.",
        lambda m: f"거주지는 {_choice(rng, AREAS)}인데 집으로 가면 가족 접촉 가능성이 커서 안 됩니다.",
        text,
    )
    text = re.sub(
        r"(현재 주소는|거주지는) [^,\n]+(, 직장은 [^,\n]+로 조회되는데 맞습니까\?)",
        lambda m: f"{m.group(1)} {_choice(rng, AREAS)}{m.group(2)}",
        text,
    )
    text = re.sub(
        r"직장은 [^,\n]+로 조회되는데 맞습니까\?",
        lambda m: f"직장은 {_with_euro(_choice(rng, COMPANIES))} 조회되는데 맞습니까?",
        text,
    )
    text = re.sub(
        r"(직장은|근무지가) [^,\n]+(로 조회되는데 사무실에서는 수사 누설 우려가 있어 바로 자리 이탈해 주셔야 합니다\.)",
        lambda m: f"{m.group(1)} {_with_euro(_choice(rng, COMPANIES))}{m.group(2)[1:]}",
        text,
    )
    text = re.sub(
        r"현재 등록 주소 [^,\n]+와 재직 정보 [^,\n]+가 뒤늦게 최종 대조됐습니다\.",
        lambda m: f"현재 등록 주소 {_choice(rng, AREAS)}와 재직 정보 {_choice(rng, COMPANIES)}가 최종 대조됐습니다.",
        text,
    )
    text = re.sub(
        r"([가-힣A-Za-z]+은행|카카오뱅크|토스뱅크|농협|농협은행|IBK기업은행|새마을금고)와 ([가-힣A-Za-z]+은행|카카오뱅크|토스뱅크|농협|농협은행|IBK기업은행|새마을금고) 자산부터",
        lambda m: f"{_join_with_and(m.group(1), m.group(2))} 자산부터",
        text,
    )
    text = re.sub(
        r"본인 계좌를 보호하려면 ([^\n]+) 자산부터 점검하셔야 합니다\.",
        lambda m: (
            lambda a, b: f"본인 계좌를 보호하려면 {_join_with_and(a, b)} 자산부터 점검하셔야 합니다."
        )(*_bank_pair(rng)),
        text,
    )
    text = re.sub(
        r"사기범: 지금 입력한 수사 담당자 정보로 사건 접수 여부를 다시 조회해 보니, 지금은 휴대기기 보호 조치가 필요한 상태입니다\.",
        rng.choice([
            "사기범: 다시 조회해 보니 현재는 추가 보호 확인 절차가 필요한 상태입니다.",
            "사기범: 내부 확인 결과 지금은 기기 보안 점검을 같이 진행해야 하는 상황입니다.",
            "사기범: 조회상 보호 단계가 열려 있어서 본인 확인을 먼저 마쳐야 합니다.",
        ]),
        text,
    )
    text = re.sub(
        r"사기범: 맞습니다\. 일단 본인 확인만 끝내면 즉시 정지 처리 순번이 잡힙니다\.",
        rng.choice([
            "사기범: 우선 본인 확인이 끝나야 다음 보호 조치를 진행할 수 있습니다.",
            "사기범: 확인 절차만 마치면 후속 차단 단계로 넘길 수 있습니다.",
            "사기범: 지금은 본인 확인이 먼저이고, 그 다음에 정지 여부가 결정됩니다.",
        ]),
        text,
    )

    seen = set()
    cleaned = []
    for line in text.splitlines():
        line = " ".join(line.split())
        line = re.sub(r"(직장은|근무지가) ([가-힣A-Za-z]+)로 조회되는데", lambda m: f"{m.group(1)} {_with_euro(m.group(2))} 조회되는데", line)
        if line.startswith("사기범: 거주지는 ") and "집으로 가면 가족 접촉 가능성이 커서 안 됩니다." not in line:
            line = f"사기범: 거주지는 {_choice(rng, AREAS)}인데 집으로 가면 가족 접촉 가능성이 커서 안 됩니다."
        if line in {
            "사기범: 우선 확인 절차부터 이어가겠습니다.",
            "사기범: 지금 단계만 먼저 진행하겠습니다.",
            "사기범: 확인이 끝날 때까지만 안내를 이어가겠습니다.",
        }:
            continue
        if line in seen and line.startswith(("사기범:", "피해자:")):
            continue
        cleaned.append(line)
        seen.add(line)
    return "\n".join(cleaned)


def _rng(key: str) -> random.Random:
    seed = int(hashlib.sha1(key.encode("utf-8")).hexdigest()[:16], 16)
    return random.Random(seed)


def _choice(rng: random.Random, options: list[str], default: str = "") -> str:
    if not options:
        return default
    return rng.choice(options)


def _speaker_pair(medium_type: str) -> tuple[str, str]:
    if medium_type == "sms":
        return "상담센터", "고객님"
    if medium_type == "chat":
        return "상담사", "고객"
    if medium_type == "notice":
        return "알림봇", "사용자"
    return "상담원", "고객"


def _target_bounds(source: str, target_length: str) -> tuple[int, int]:
    if source == "voice":
        return {"short": (13, 15), "medium": (16, 19), "long": (21, 26)}[target_length]
    if source == "bank":
        return {"short": (12, 14), "medium": (14, 17), "long": (18, 22)}[target_length]
    return {"short": (12, 14), "medium": (14, 17), "long": (17, 20)}[target_length]


def _voice_target_length(variation_profile: str) -> str:
    m = re.search(r"interaction_length=(short|medium|long)", variation_profile)
    return m.group(1) if m else "medium"


def _normalize_turns(
    turns: list[str],
    target_min: int,
    target_max: int,
    rng: random.Random,
    a: str,
    b: str,
    context_no: str,
    source: str = "bank",
) -> list[str]:
    target = rng.randint(target_min, target_max)
    marker = f"접수코드 {context_no}"
    if marker not in "\n".join(turns):
        insert_at = 1 if len(turns) > 1 else 0
        turns = turns[:insert_at] + [f"{a}: 이번 문의는 접수코드 {context_no}로 등록돼 있습니다."] + turns[insert_at:]

    if len(turns) >= target:
        return turns[:target]

    if source == "bank":
        filler = [
            f"{b}: 혹시 제가 지금 더 해야 할 조치가 있나요?",
            f"{a}: 전화상으로는 안내만 가능하고 실제 변경은 등록된 공식 절차에서만 가능합니다.",
            f"{b}: 그럼 임의 송금이나 별도 설치 같은 건 없는 거죠?",
            f"{a}: 네, 그런 요청은 없고 앱이나 영업점 본인확인 이후에만 처리됩니다.",
            f"{b}: 처리 상태만 문자로 받으면 되겠네요.",
            f"{a}: 네, 접수 결과와 후속 절차만 순서대로 안내드리겠습니다.",
        ]
    elif source == "voice":
        filler = [
            f"{b}: 지금 바로 결정해야 하는 이유를 다시 설명해 주세요.",
            f"{a}: 확인이 늦어지면 다음 단계로 넘어갈 수 있어서 우선 지금 절차부터 안내드리는 중입니다.",
            f"{b}: 제가 직접 확인할 시간은 없는 건가요?",
            f"{a}: 직접 확인은 가능하지만 현재는 먼저 확인 단계부터 진행하셔야 합니다.",
            f"{b}: 그럼 제가 무엇부터 해야 하는지 한 번만 더 말씀해 주세요.",
            f"{a}: 네, 지금은 순서대로 확인만 진행하시면 됩니다.",
        ]
    else:
        filler = [
            f"{a}: 추가로 필요한 정보가 있으면 메시지로 바로 보내드릴게요.",
            f"{b}: 네, 확인 감사합니다. 그럼 저녁 전까지 마무리하면 될까요?",
            f"{a}: 네, 가능한 범위가 맞으면 바로 확정하겠습니다.",
            f"{b}: 혹시 변동되면 바로 다시 연락드려도 되나요?",
            f"{a}: 네, 동일 채널로만 바꿔 주세요.",
            f"{b}: 네, 이해했습니다.",
        ]

    i = 0
    while len(turns) < target:
        turns.append(filler[i % len(filler)])
        i += 1
    return turns[:target]


def _card_reissue(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    branch = _choice(rng, BRANCHES)
    name = _choice(rng, NAMES)
    ticket = f"{rng.randint(100000, 999999)}-{rng.randint(100, 999)}"
    ctype = _choice(rng, CARD_TYPES)
    phone = rng.randint(1000, 9999)
    card_fee = rng.choice(["6,000", "8,000", "10,000"])
    time = rng.choice(["1", "2", "3"])

    base = [
        f"{a}: {bank} 카드 재발급 센터입니다.",
        f"{b}: 네, 휴대폰 분실 이후 승인되지 않은 결제 알림도 보여서 카드 재발급이 필요합니다.",
        f"{a}: {name}님 맞으신가요? 카드번호 끝자리와 휴대폰 뒷자리 4개만 알려주세요.",
        f"{b}: 확인해요. 카드번호 끝자리는 {context_no[-4:]}이고 뒷자리는 {phone}입니다.",
        f"{a}: 현재 해외 온라인 결제는 임시 차단된 상태고 {ctype}로 재발급 접수가 가능합니다.",
        f"{b}: 수령 방식은 영업점이랑 택배 중 어떤 게 빨라요?",
        f"{a}: 영업점 수령이 가장 빠릅니다. 지금은 {branch}센터 수령 가능입니다.",
        f"{b}: 영업점에서 신분증 1부만 가져가면 되죠?",
        f"{a}: 네, 본인확인만 되면 당일 임시 발급 처리 가능합니다.",
        f"{b}: 그럼 지금 통화에서 바로 카드가 풀리거나 하진 않는 거죠?",
        f"{a}: 네, 전화로 결제 차단을 해제하지는 않고 등록된 절차에서만 처리됩니다.",
        f"{b}: 택배를 원하면 접수비가 붙나요?",
        f"{a}: 택배 발송료는 {card_fee}원이며 접수 즉시 환불 정책도 함께 안내드립니다.",
        f"{b}: 그럼 접수하고 영수증 문자 보내주세요.",
        f"{a}: 접수번호는 {ticket}입니다. 1~{time}시간 내로 상태가 바뀝니다.",
    ]

    if style == "consultative":
        base[1] = "고객: 네, 재발급하고 싶어요. 카드가 며칠 전 분실됐어요."
        base.append(f"{a}: 분실일로부터 24시간 이내 신고되어 있어 처리 우선순위가 높습니다.")
        base.append(f"{a}: {branch} 담당라인이 비슷한 접수 건도 분기해 동일 분실방지 체크를 완료했습니다.")
        base.append(f"{b}: 네, 이해했습니다.")
    elif style == "colloquial":
        base[1] = "고객: 네, 분실해서 바로 바꿔야 해요."
        base.append(f"{a}: 오늘 중에 접수 마감 전까지 잡아드릴게요.")
        base.append(f"{b}: 수고스럽네요, 근데 가능한 빨리 부탁드립니다.")
        base.append(f"{a}: 걱정말고 접수번호만 잘 보관하세요.")

    return base


def _loan_inquiry(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    name = _choice(rng, NAMES)
    branch = _choice(rng, BRANCHES)
    app_no = f"{rng.randint(2026, 2027)}-{rng.randint(100000, 999999)}"
    ticket = f"{rng.randint(200000, 299999)}"

    base = [
        f"{a}: {bank} 대출지원팀입니다. {name}님 명의 사전한도 조회 이력이 있어 본인 확인 차 연락드렸습니다.",
        f"{b}: 제가 직접 조회한 건지 헷갈려서 확인하려고요.",
        f"{a}: 현재 {app_no} 건이 접수 대기 상태로 보이고, 본인 신청이 아니면 진행이 중단됩니다.",
        f"{b}: 그럼 소득 증빙 같은 서류를 바로 내야 하나요?",
        f"{a}: 아닙니다. 우선 본인 신청 여부만 확인하고, 이후 공식 앱이나 영업점에서만 이어집니다.",
        f"{b}: 전화에서 바로 승인되거나 실행되는 건 아니죠?",
        f"{a}: 네, 통화에서는 조건 안내와 중단 접수만 가능하고 실제 실행은 불가합니다.",
        f"{b}: 영업점은 언제 방문하면 되죠?",
        f"{a}: {branch}점이면 오늘 18시까지 접수 가능하고 영업점 점검은 평일 오후입니다.",
        f"{b}: 영업일 기준 처리 시간은요?",
        f"{a}: 영업일 2~3일 내로 신청 이력 정리나 한도 조회 취소 여부가 반영됩니다.",
        f"{b}: 접수번호 알려주시겠어요?",
        f"{a}: {ticket}입니다. 추가 안내는 등록된 채널로만 발송됩니다.",
    ]

    if style == "formal":
        base.append(f"{a}: 문의하신 조건은 {branch} 본점 리스크 검토 팀에서 확정됩니다.")
        base.append(f"{a}: {ticket} 건은 금리 제안 후보 2건으로 비교 가능합니다.")
    elif style == "consultative":
        base.append(f"{b}: 제가 원래 쓰던 금리 조건과 비교표도 받으면 좋겠어요.")
        base.append(f"{a}: 오늘 자정 전까지 비교표를 정리해드리겠습니다.")
    else:
        base.append(f"{b}: 급한 일정이 있어서 간단히 설명만 부탁드려요.")
        base.append(f"{a}: 네, 간단안내 문자로 드리겠습니다.")

    return base


def _transfer_check(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    name = _choice(rng, NAMES)
    ref = f"{rng.randint(1, 999):03d}-{rng.randint(10, 99)}"
    base = [
        f"{a}: {bank} 계좌 이상거래 확인 창구입니다. 입출금 내역 조회 문의 접수 맞죠?",
        f"{b}: 네, 최근 알림이 안 맞는 부분이 있어 확인하고 싶어요.",
        f"{a}: {name}님, 고객확인을 위해 성함 마지막 네 글자와 휴대폰 앞 3자리 알려주세요.",
        f"{b}: 확인했습니다. 조회만 가능한지요?",
        f"{a}: 네, 현재는 조회와 이상 징후 설명만 가능하고 이체 실행은 불가합니다.",
        f"{b}: 승인되지 않은 항목은 어떻게 구분하나요?",
        f"{a}: 최근 7일 내 승인·미승인 건과 기기 변경 흔적은 구분해서 보내드릴 수 있습니다.",
        f"{b}: 문자로 상세 항목도 받을 수 있나요?",
        f"{a}: 가능하지만 금액 일부는 보안상 마스킹 처리됩니다.",
        f"{b}: 그럼 조회를 우선 넣어주세요.",
        f"{a}: 접수번호 {ref}로 요청 등록했습니다.",
        f"{b}: 혹시 다른 계좌로 옮겨두라는 안내가 따로 있나요?",
        f"{a}: 아닙니다. 자금 이동 요청은 없고, 고객 확인 후 필요한 경우 지급수단만 일시 제한됩니다.",
        f"{b}: 처리 완료는 보통 언제쯤?",
        f"{a}: 영업일 기준 1~2일 내로 상태 변동을 드립니다.",
    ]

    if style == "formal":
        base.append(f"{a}: 정기적인 계좌관리로 불필요한 조회 알림만 걸러두시기 바랍니다.")
        base.append(f"{a}: 오늘 상담은 {context_no} 건으로 기록 처리하였습니다.")
    elif style == "consultative":
        base.append(f"{b}: 확인되는 항목만 따로 정리해 주세요.")
        base.append(f"{a}: 네, 내역별로 구분 정렬해 보내드리겠습니다.")
    else:
        base.append(f"{b}: 네, 문자만 깔끔하게 요약되면 될 것 같아요.")
        base.append(f"{a}: 알림 톤도 평소대로 바꿔드리겠습니다.")

    return base


def _fraud_report(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    case_no = f"FR-{rng.randint(10000, 99999)}"
    name = _choice(rng, NAMES)
    base = [
        f"{a}: {bank} 비인가 거래 신고 접수 센터입니다.",
        f"{b}: 네, 제 계좌에서 비정상 접속 의심이 있어 신고하려고요.",
        f"{a}: 신고자 성함과 접수번호를 말씀해 주세요.",
        f"{b}: 성함은 {name}, 신고번호는 {case_no}입니다.",
        f"{a}: 접수했습니다. 임시로 출금 제한으로 안전 절차가 동작합니다.",
        f"{b}: 그럼 지금은 출금이 막히는 건가요?",
        f"{a}: 비정상 징후가 완화될 때까지 추가 승인 요청이 제한됩니다.",
        f"{b}: 증빙은 어떤 걸 준비하면 되죠?",
        f"{a}: 당일 거래내역 1부와 신분증 사본이면 됩니다.",
        f"{b}: 자금을 다른 안전계좌로 옮기라는 식의 안내는 아닌 거죠?",
        f"{a}: 네, 그런 절차는 없고 현재 계좌 상태 보존과 신고 접수만 진행합니다.",
        f"{b}: 접수 알림은 어떤 걸로 오나요?",
        f"{a}: 문자/앱 알림 동시 발송하고 접수번호는 {context_no}로 관리됩니다.",
        f"{b}: 네, 이해했어요.",
    ]

    if style == "formal":
        base.append(f"{a}: 접수번호는 {context_no}이며 접수창구에서 후속 조치를 연계합니다.")
        base.append(f"{a}: 추가로 앱에서 안전수칙 토글도 체크 부탁드립니다.")
    elif style == "consultative":
        base.append(f"{b}: 혹시 지금 당장 취소 가능한 거래만 걸러줄 수 있나요?")
        base.append(f"{a}: 네, 현재 접속기록 기준으로 우선순위를 분류해두겠습니다.")
    else:
        base.append(f"{b}: 오늘 바로 마무리 가능한 범위가요?")
        base.append(f"{a}: 네, 오늘 접수건은 바로 처리 큐로 넣겠습니다.")

    return base


def _limit_release(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    branch = _choice(rng, BRANCHES)
    base = [
        f"{a}: {bank} 안전점검센터입니다. 결제제한 관련 문의 건이 맞나요?",
        f"{b}: 네, 영수증이 자꾸 실패 나오고 본인 결제가 아닌 것처럼 보여서요.",
        f"{a}: 지금은 기기 변경으로 자동 제한이 걸린 상태일 수 있습니다.",
        f"{b}: 바로 해결할 수 있을까요?",
        f"{a}: 먼저 본인확인 후 2단계 제한 해제를 진행합니다.",
        f"{b}: 제일 쉬운 순서대로 알려주세요.",
        f"{a}: 앱 인증 → 휴대폰 본인 인증 → 영업점 추가 확인으로 진행됩니다.",
        f"{b}: 문자 링크로 바로 푸는 방식은 아닌 거죠?",
        f"{a}: 네, 외부 링크 접속으로 해제하지 않고 공식 앱이나 영업점 절차만 사용합니다.",
        f"{b}: 영업점은 어디가 가능한가요?",
        f"{a}: {branch}점에서 추가 확인하면 오늘 안으로 반영됩니다.",
        f"{b}: 접수 후 처리시간이 길진 않죠?",
        f"{a}: 보통 1~2시간 내 1차 복구 가능합니다.",
        f"{b}: 알겠습니다. 참고 번호 주세요.",
        f"{a}: 처리참조 번호는 {context_no}입니다.",
    ]

    if style == "colloquial":
        base.append(f"{b}: 네, 바로 진행할게요. 바빠서 딱딱한 건 피해주세요.")
        base.append(f"{a}: 네, 부담 없이 순서대로 도와드릴게요.")
    elif style == "consultative":
        base.append(f"{a}: 단말기 인증이 실패하면 영업점 방문 후 동일 절차를 적용합니다.")
        base.append(f"{b}: 오늘 내 방문으로 마칠 수 있겠네요.")
    else:
        base.append(f"{a}: 장시간 미연결 시 고객센터로 재문의해 주세요.")
        base.append(f"{b}: 네, 처리 완료되면 바로 알려주세요.")

    return base


def _product_info(rng: random.Random, a: str, b: str, style: str, context_no: str) -> list[str]:
    bank = _choice(rng, BANKS)
    branch = _choice(rng, BRANCHES)
    base = [
        f"{a}: {bank} 상품상담부입니다. 최근 문의가 많은 안심차단 서비스와 예적금 상품 안내 도와드리겠습니다.",
        f"{b}: 요즘 이상거래 걱정이 있어서 보안성 있는 상품이 궁금합니다.",
        f"{a}: 고객님 상황을 기준으로 입출금 제한 서비스와 일반 예적금 상품군을 나눠 설명드리겠습니다.",
        f"{b}: 중도해지 위약이나 출금 제한이 어떻게 다른지가 중요해요.",
        f"{a}: 안심차단 서비스는 의심거래 차단 목적이고, 예적금은 보관 목적이라 절차가 다릅니다.",
        f"{b}: 그럼 제 돈을 다른 데로 옮겨야 하는 상품은 아닌 거죠?",
        f"{a}: 네, 자금 이동을 강제하는 상품은 아니고 신청 여부만 선택하시면 됩니다.",
        f"{b}: 상담은 어디서 하면 빠를까요?",
        f"{a}: {branch}점 또는 앱 상담 중 편한 방식으로 진행 가능합니다.",
        f"{b}: 비교표와 혜택 목록 보내주세요.",
        f"{a}: 상담 예약번호는 {context_no}입니다.",
        f"{b}: 접수된 건은 10분 내로 반영되겠죠?",
        f"{a}: 네, 영업일 기준 바로 안내 가능합니다.",
    ]

    if style == "consultative":
        base.append(f"{b}: 우선 목돈이 아닌 월 납입형으로 보여주세요.")
        base.append(f"{a}: 월 납입형 비교표를 오늘 중으로 문자로 정리드리겠습니다.")
    elif style == "colloquial":
        base.append(f"{b}: 딱딱한 용어는 빼고 쉬운 말로만 해주세요.")
        base.append(f"{a}: 네, 약식으로만 깔끔히 정리드릴게요.")
    else:
        base.append(f"{a}: 투자성 상품은 위험도 설명이 별도이므로 원하시면 담당자와 별도 통화 가능합니다.")

    return base


BANK_BUILDERS = {
    "card_reissue": _card_reissue,
    "loan_inquiry": _loan_inquiry,
    "transfer_check": _transfer_check,
    "fraud_report": _fraud_report,
    "limit_release": _limit_release,
    "product_info": _product_info,
}


def _build_bank(row: dict[str, str]) -> str:
    rng = _rng(row["qa_id"])
    a, b = _speaker_pair(row["medium_type"])
    style = row["target_style"]
    builder = BANK_BUILDERS[row["scenario_type"]]
    turns = builder(rng, a, b, style, row["qa_id"])
    tmin, tmax = _target_bounds("bank", row["target_length"])
    turns = _normalize_turns(turns, tmin, tmax, _rng(row["qa_id"]), * _speaker_pair(row["medium_type"]), row["qa_id"], "bank")
    return "\n".join(turns)


def _delivery(rng, a, b, ref_no) -> list[str]:
    place = _choice(rng, DISTRICTS)
    company = _choice(rng, DELIVERY_COMPANIES)
    return [
        f"{a}: 안녕하세요, {company} 안내센터입니다.",
        f"{b}: 네, 제 주소로 배송되는 택배가 하나 있는데요.",
        f"{a}: 주문 번호와 동네를 알려주시면 확인 가능합니다.",
        f"{b}: {place} 기준으로 받겠습니다.",
        f"{a}: 보관 동의만 주시면 오늘 늦게도 문앞 전달이 가능합니다.",
        f"{b}: 공동현관 번호 입력이 필요한가요?",
        f"{a}: 기본은 동/호와 문 앞 동의면 처리됩니다.",
        f"{b}: 문자로 상태만 공유해 주세요.",
        f"{a}: 반송 전 확인 문자는 별도 알림으로 갈 수 있게 설정돼 있습니다.",
        f"{b}: 네, 알겠어요.",
    ]


def _hospital(rng, a, b, ref_no) -> list[str]:
    patient = _choice(rng, NAMES)
    return [
        f"{a}: 병원 접수팀입니다. 진료 안내입니다.",
        f"{b}: {patient}이고 진료 예약 여부를 확인하고 싶어요.",
        f"{a}: 예약일은 내일 10시입니다. 성함 확인해 주세요.",
        f"{b}: 네, 예약자 본인입니다.",
        f"{a}: 병실대기 예상시간은 15분 정도고, 건강보험증만 지참해 주세요.",
        f"{b}: 알겠습니다. 검사 동의서 양식도 보내줄 수 있나요?",
        f"{a}: 접수번호 {ref_no} 기준으로 문자 안내됩니다.",
        f"{b}: 오늘은 결제는 카드로 해도 되죠?",
        f"{a}: 결제 수단은 본인카드 또는 현금영수증 선택 가능합니다.",
        f"{b}: 감사합니다.",
    ]


def _school(rng, a, b, ref_no) -> list[str]:
    student = _choice(rng, NAMES)
    return [
        f"{a}: 학부모지원센터입니다.",
        f"{b}: {student} 자녀의 면담 일정 확인이 필요해요.",
        f"{a}: 오늘 안내는 2차 확인으로 마무리됩니다.",
        f"{b}: 오프라인으로 바뀔 수 있나요?",
        f"{a}: 원하시면 온라인으로도 전환 가능합니다.",
        f"{b}: 필요한 서류가 있나요?",
        f"{a}: 신분증 사본과 출석 확인서면 충분합니다.",
        f"{b}: 접수 코드를 문자로 받을 수 있겠죠?",
        f"{a}: 네, 코드 {ref_no}로 발송해드릴게요.",
        f"{b}: 알겠습니다. 오늘 중 완료하면 될까요?",
        f"{a}: 네, 오늘 오후 전에 처리 가능 여부를 확정해드리겠습니다.",
    ]


def _reservation(rng, a, b, ref_no) -> list[str]:
    return [
        f"{a}: 레스토랑 예약센터입니다.",
        f"{b}: 오늘 저녁 7시에 4명 예약할 수 있나요?",
        f"{a}: 가능합니다. 좌석은 창가 쪽으로 잡아드릴게요.",
        f"{b}: 메뉴는 한식 위주면 좋겠어요.",
        f"{a}: 메뉴 선호도 반영해두고 알레르기도 같이 등록합니다.",
        f"{b}: 결제 전 예약번호만 알려주세요.",
        f"{a}: {ref_no}로 접수 완료했고, 변경은 2시간 전까지 가능합니다.",
        f"{b}: 문자가 꼭 와야 해요.",
        f"{a}: 알림은 문자+앱으로 설정해두겠습니다.",
        f"{b}: 네, 감사합니다.",
    ]


def _apartment(rng, a, b, ref_no) -> list[str]:
    apt = _choice(rng, APT_DONG)
    phone = rng.randint(1000, 9999)
    return [
        f"{a}: 입주민센터입니다.",
        f"{b}: 경비실 보관 안내 건이 맞는지요.",
        f"{a}: 동호수와 휴대폰 마지막 4자리를 남겨주세요.",
        f"{b}: {apt}동 {rng.randint(100, 1200)}호, {phone}입니다.",
        f"{a}: 보관 가능 기간과 반납 동의가 확인되면 바로 처리됩니다.",
        f"{b}: 반송 전 문자를 먼저 받아보게 해주세요.",
        f"{a}: 네, 코드 {ref_no}로 등록 후 상태가 바뀝니다.",
        f"{b}: 오늘 늦게도 가능할까요?",
        f"{a}: 네, 24시간 알림을 받으시면 됩니다.",
        f"{b}: 고맙습니다.",
    ]


def _telecom(rng, a, b, ref_no) -> list[str]:
    return [
        f"{a}: 이동통신 고객센터입니다.",
        f"{b}: 데이터 플랜 변경이 가능한지요?",
        f"{a}: 사용 패턴 기준으로 2~3가지 조합이 가능합니다.",
        f"{b}: 월말 전에 전환하면 되는지 확인하고 싶어요.",
        f"{a}: 전환은 다음 달부터 반영되며 중도 해지도 가능합니다.",
        f"{b}: 추가 혜택은 어디서 확인하죠?",
        f"{a}: 안내문을 {ref_no}로 저장해두고 문자로 보내드리겠습니다.",
        f"{b}: 문자 수신 채널도 바꿀 수 있나요?",
        f"{a}: 네, 문자/앱 알림 둘 다 가능합니다.",
        f"{b}: 감사합니다.",
    ]


def _schedule(rng, a, b, ref_no) -> list[str]:
    org = _choice(rng, ORGS)
    return [
        f"{a}: {org}입니다. 일정 조율이 필요해요.",
        f"{b}: 회의 시간 후보 3개만 보내드릴게요.",
        f"{a}: 후보를 받으면 우선순위를 나눠 확정하겠습니다.",
        f"{b}: 중간에 변동이 생기면 어떻게 되나요?",
        f"{a}: 변동은 24시간 이내이면 바로 다시 배정됩니다.",
        f"{b}: 알림만 잘 받으면 됩니다.",
        f"{a}: 채널은 {ref_no}로 처리 이력에 남깁니다.",
        f"{b}: 알겠습니다.",
    ]


def _customer_service(rng, a, b, ref_no) -> list[str]:
    return [
        f"{a}: 고객센터입니다. 어떤 건이 접수됐는지 확인하겠습니다.",
        f"{b}: 주문 취소 요청 상태가 궁금해요.",
        f"{a}: 접수번호만 알려주시겠어요?",
        f"{b}: {ref_no}입니다.",
        f"{a}: 확인한 결과 처리 중이며 추가 서류는 현재 필요 없습니다.",
        f"{b}: 완결은 언제쯤인가요?",
        f"{a}: 접수 구간은 영업일 기준 1~3일입니다.",
        f"{b}: 진행 알림만 꼭 받아보고 싶어요.",
        f"{a}: 네, 문자로 진행 상태를 보낼게요.",
        f"{b}: 네, 감사합니다.",
        f"{a}: 추가 문의는 같은 채널로 계속해 주세요.",
    ]


IR_BUILDERS = {
    "delivery": _delivery,
    "hospital": _hospital,
    "school": _school,
    "reservation": _reservation,
    "apartment": _apartment,
    "telecom": _telecom,
    "schedule": _schedule,
    "customer_service": _customer_service,
}


def _build_ir(row: dict[str, str]) -> str:
    rng = _rng(row["qa_id"])
    a, b = _speaker_pair(row["medium_type"])
    builder = IR_BUILDERS[row["topic"]]
    turns = builder(rng, a, b, row["qa_id"])
    tmin, tmax = _target_bounds("irrelevant", row["target_length"])
    turns = _normalize_turns(
        turns,
        tmin,
        tmax,
        rng,
        a,
        b,
        row["qa_id"],
        "irrelevant",
    )
    return "\n".join(turns)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_voice() -> list[dict[str, str]]:
    rows = []
    for row in read_rows(VOICE_CORPUS):
        rows.append(
            {
                "qa_id": row["sample_id"],
                "source_type": "voicephishing",
                "source_sample_id": row["sample_id"],
                "question": QUESTION,
                "scenario_text": _build_voice(row),
                "ground_truth": "yes",
            }
        )
    return rows


def _voice_phrase_variants(text: str, rng: random.Random) -> str:
    variants = {
        "네, 말씀하세요.": ["네, 무슨 일이시죠?", "말씀해 보세요.", "네, 어떤 건가요?"],
        "제가 그런 계좌를 만든 적은 없습니다.": ["저는 그런 계좌를 만든 적이 없습니다.", "그 계좌는 제 것이 아닙니다.", "저는 그런 계좌를 개설한 적이 없어요."],
        "제가 직접 확인해 보겠습니다.": ["직접 확인해 보고 다시 말씀드리겠습니다.", "제가 확인한 뒤 다시 연락드리면 안 될까요?", "바로 믿기 어려워서 먼저 확인하겠습니다."],
        "알겠습니다.": ["네, 이해했습니다.", "일단 확인해 보겠습니다.", "우선 말씀은 들었습니다."],
        "어떻게 하면 되죠?": ["그러면 제가 뭘 해야 하나요?", "이제 어떤 절차로 진행되나요?", "어떻게 확인하면 되죠?"],
        "왜 저한테 이런 연락이 오죠?": ["왜 제 번호로 연락이 온 건가요?", "제가 왜 이 사건에 들어가 있죠?", "왜 제가 대상자인 거죠?"],
    }
    for src, choices in variants.items():
        if src in text:
            text = text.replace(src, rng.choice(choices), 1)
    return text


def _build_voice(row: dict[str, str]) -> str:
    original = row["scenario_text"].replace("\r", "")
    text = original
    rng = _rng(f"{row['sample_id']}-qa-remix")
    pattern = row["pattern_name"]

    replacements = {}
    for bank in ALT_BANKS:
        if bank in text:
            replacements[bank] = _choice(rng, [b for b in ALT_BANKS if b != bank], bank)
    for name in NAMES:
        if name in text:
            replacements[name] = _choice(rng, [n for n in NAMES if n != name], name)
    for area in AREAS:
        if area in text:
            replacements[area] = _choice(rng, [a for a in AREAS if a != area], area)
    for company in COMPANIES:
        if company in text:
            replacements[company] = _choice(rng, [c for c in COMPANIES if c != company], company)

    if "서울중앙지방검찰청" in text:
        replacements["서울중앙지방검찰청"] = _choice(rng, PROSECUTION_OFFICES)
    if "서울중앙지방법원" in text:
        replacements["서울중앙지방법원"] = _choice(rng, COURTS)

    text = _replace_all(text, replacements)
    text = _voice_phrase_variants(text, rng)

    text = _regex_replace(text, r"20\d{2}형제\d+", lambda m: f"{rng.choice(['2026형제', '2026금수', '2026조사'])}{rng.randint(18000, 48999)}")
    text = _regex_replace(text, r"FR-\d{5}", lambda m: f"FR-{rng.randint(10000, 99999)}")
    text = _regex_replace(text, r"\b\d{2,3}만 원\b", lambda m: f"{rng.choice([23, 35, 48, 62, 78, 95])}만 원")
    text = _regex_replace(text, r"\b\d{1,3},\d{3}원\b", lambda m: f"{rng.choice([3000, 5000, 7000, 9000]):,}원")
    text = _regex_replace(text, r"[가-힣]+중앙지방검찰청", lambda m: _choice(rng, PROSECUTION_OFFICES))
    text = _regex_replace(text, r"[가-힣]+중앙지방법원", lambda m: _choice(rng, COURTS))
    text = _regex_replace(text, r"(현재 주소는|거주지는) [^,\n]+", lambda m: f"{m.group(1)} {_choice(rng, AREAS)}")

    if pattern == "기관사칭형":
        text = text.replace("수사관입니다.", f"{_choice(rng, POLICE_UNITS)} 확인 담당입니다.", 1)
    elif pattern == "가족자녀사칭형":
        role = _choice(rng, FAMILY_ROLES)
        rel = _choice(rng, RELATION_NAMES)
        text = text.replace("엄마", role).replace("아빠", role)
        text = text.replace("친구 계좌", f"{rel} 계좌")
    elif pattern == "악성앱원격제어형":
        text = text.replace("전용 보안 앱", _choice(rng, APP_NAMES))
        text = text.replace("보안 앱", _choice(rng, APP_NAMES))
    elif pattern == "법원등기우편사칭형":
        text = text.replace("사건번호", rng.choice(["접수번호", "조회번호", "열람번호"]))
    elif pattern == "스미싱큐싱연계형":
        text = text.replace("배송 확인 링크", rng.choice(["배송 조회 링크", "재배달 확인 링크", "주소 정정 링크"]))

    lines = text.splitlines()
    if lines:
        first = lines[0]
        if first.startswith("사기범:"):
            lines[0] = first.replace("안녕하세요. ", rng.choice(["안내 먼저 드리겠습니다. ", "확인차 연락드렸습니다. ", "지금 바로 확인 부탁드립니다. "]), 1)
        elif first.startswith("문자:"):
            lines[0] = first.replace("안내", rng.choice(["확인", "조회", "통지"]), 1)

    text = "\n".join(lines)
    if text == original:
        forced = text.splitlines()
        if forced:
            if forced[0].startswith("사기범:"):
                forced[0] = forced[0] + rng.choice([" 급히 확인하셔야 합니다.", " 우선 제 설명부터 들어주십시오.", " 지금 확인 절차가 필요합니다."])
            elif len(forced) > 1 and forced[1].startswith("피해자:"):
                forced[1] = forced[1].replace("피해자:", "피해자: 잠시만요, ")
            else:
                forced.append(f"사기범: 확인이 늦어지면 절차가 더 복잡해질 수 있습니다.")
        text = "\n".join(forced)
    text = _dedupe_adjacent_lines(text)
    text = _clean_voice_text(text, rng)
    target_length = _voice_target_length(row["variation_profile"])
    tmin, tmax = _target_bounds("voice", target_length)
    turns = _normalize_turns(text.splitlines(), tmin, tmax, rng, "사기범", "피해자", row["sample_id"], "voice")
    text = "\n".join(turns)
    return text


def build_dataset() -> list[dict[str, str]]:
    voice_rows = load_voice()
    bank_rows = []
    for row in read_rows(BANK_QUEUE):
        bank_rows.append(
            {
                "qa_id": row["qa_id"],
                "source_type": "bank_call",
                "source_sample_id": row["qa_id"],
                "question": QUESTION,
                "scenario_text": _build_bank(row),
                "ground_truth": "no",
            }
        )

    ir_rows = []
    for row in read_rows(IR_QUEUE):
        ir_rows.append(
            {
                "qa_id": row["qa_id"],
                "source_type": "irrelevant",
                "source_sample_id": row["qa_id"],
                "question": QUESTION,
                "scenario_text": _build_ir(row),
                "ground_truth": "no",
            }
        )
    return voice_rows + bank_rows + ir_rows


def write_dataset(rows: list[dict[str, str]]) -> None:
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["qa_id", "source_type", "source_sample_id", "question", "scenario_text", "ground_truth"])
        writer.writeheader()
        writer.writerows(rows)


def validate(rows: list[dict[str, str]]) -> None:
    ctype = Counter(r["source_type"] for r in rows)
    cturn = Counter(len(r["scenario_text"].splitlines()) for r in rows)
    dup = len(rows) - len({r["qa_id"] for r in rows})
    print(f"rows={len(rows)}")
    print(f"source_counts={dict(ctype)}")
    print(f"qa_id_duplicates={dup}")
    print(f"turn_min={min(cturn)} turn_max={max(cturn)} bank_turn={Counter(len(r['scenario_text'].splitlines()) for r in rows if r['source_type']=='bank_call')}")
    print(f"vp_turn={Counter(len(r['scenario_text'].splitlines()) for r in rows if r['source_type']=='voicephishing')}")
    print(f"ir_turn={Counter(len(r['scenario_text'].splitlines()) for r in rows if r['source_type']=='irrelevant')}")

    bank_texts = [r["scenario_text"] for r in rows if r["source_type"] == "bank_call"]
    ir_texts = [r["scenario_text"] for r in rows if r["source_type"] == "irrelevant"]
    voice_rows = [r for r in rows if r["source_type"] == "voicephishing"]
    bank_counts = Counter(bank_texts)
    ir_counts = Counter(ir_texts)
    corpus_lookup = {r["sample_id"]: r["scenario_text"].replace("\r", "") for r in read_rows(VOICE_CORPUS)}
    voice_exact = sum(1 for r in voice_rows if corpus_lookup.get(r["source_sample_id"]) == r["scenario_text"])
    print(f"bank_dup_groups={sum(1 for c in bank_counts.values() if c > 1)}")
    print(f"ir_dup_groups={sum(1 for c in ir_counts.values() if c > 1)}")
    print(f"voice_exact_matches_with_corpus={voice_exact}")


def main() -> None:
    rows = build_dataset()
    write_dataset(rows)
    validate(rows)


if __name__ == "__main__":
    main()
