"""슬라이스 2 의 자리 — 알림 영역. 1단계에서는 호출되었음을 출력만 한다."""
from ..crawler.parser import ParsedNotice


def send(new: list[ParsedNotice],
         modified: list[ParsedNotice]) -> None:
    print(
        f"[notifier:stub] 호출됨 — new={len(new)}건, modified={len(modified)}건"
    )
    for item in new:
        print(
            f"  · [신규] [{item.category_name}] {item.title} "
            f"({item.posted_date}) — {item.url}"
        )
    for item in modified:
        print(
            f"  · [수정] [{item.category_name}] {item.title} "
            f"({item.posted_date}) — {item.url}"
        )
