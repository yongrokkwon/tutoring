import time
from datetime import datetime
from typing import ClassVar

import requests

from .. import config
from ..crawler.parser import ParsedNotice

HEADER_NEW = "🆕 새 공지 {count}건"
HEADER_MODIFIED = "✏️ 수정된 공지 {count}건"
HEADER_PAGE_FIRST = " ({page}/{total})"
HEADER_PAGE_CONT = " (이어서 {page}/{total})"
LINE_NEW = "· [{category}] {title}{attachment} ({date}) — [원문](<{url}>)"
LINE_MODIFIED = "· [수정] [{category}] {title}{attachment} ({date}) — [원문](<{url}>)"
ATTACHMENT_MARK = " 📎"
FOOTER = "발송 시각: {timestamp}"
TIMESTAMP_FMT = "%Y-%m-%d %H:%M"
SECTION_SEP = "\n\n"
SPLIT_THRESHOLD = 1900
SPLIT_POST_DELAY_SEC = 0.5
LINE_TRUNCATE_SUFFIX = "…"
LINE_MAX_LEN = 1800

# 분할 계산 시 헤더에 붙는 페이지 표기 + 마지막 청크 footer 영역의 예비 공간.
# 최악치: " (이어서 99/99)" ≈ 14자 + "\n\n발송 시각: YYYY-MM-DD HH:MM" ≈ 24자 + 안전 버퍼.
_PACK_RESERVE = 50


class DiscordChannel:
    channel_id: ClassVar[int] = 1

    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def send(self,
             new: list[ParsedNotice],
             modified: list[ParsedNotice],
             sent_at: datetime) -> bool:
        messages = self._build_messages(new, modified, sent_at)
        return self._post_all(messages)

    @staticmethod
    def _build_messages(new: list[ParsedNotice],
                        modified: list[ParsedNotice],
                        sent_at: datetime) -> list[str]:
        new_lines = [_truncate_line(_format_line(LINE_NEW, item, _posted))
                     for item in new]
        mod_lines = [_truncate_line(_format_line(LINE_MODIFIED, item, _modified))
                     for item in modified]
        footer_text = FOOTER.format(timestamp=sent_at.strftime(TIMESTAMP_FMT))

        # Fast-path — v1.2 방식 단일 본문이 한도 안에 들어가면 그대로 사용.
        single = _assemble_single(new_lines, len(new),
                                  mod_lines, len(modified),
                                  footer_text)
        if len(single) <= SPLIT_THRESHOLD:
            return [single]

        # 분할 경로 — 섹션별 청크.
        chunks: list[tuple[str, list[str], bool]] = []
        if new_lines:
            header_base = HEADER_NEW.format(count=len(new))
            for is_first, lines in _pack_section(new_lines, header_base):
                chunks.append((header_base, lines, is_first))
        if mod_lines:
            header_base = HEADER_MODIFIED.format(count=len(modified))
            for is_first, lines in _pack_section(mod_lines, header_base):
                chunks.append((header_base, lines, is_first))

        total = len(chunks)
        messages: list[str] = []
        for idx, (header_base, lines, is_first) in enumerate(chunks, start=1):
            if is_first:
                header = header_base + HEADER_PAGE_FIRST.format(
                    page=idx, total=total)
            else:
                header = header_base + HEADER_PAGE_CONT.format(
                    page=idx, total=total)
            body = header + "\n" + "\n".join(lines)
            if idx == total:
                body += SECTION_SEP + footer_text
            messages.append(body)
        return messages

    def _post_all(self, messages: list[str]) -> bool:
        overall = True
        for idx, msg in enumerate(messages):
            if idx > 0:
                time.sleep(SPLIT_POST_DELAY_SEC)
            if not self._post_one(msg):
                overall = False
        return overall

    def _post_one(self, content: str) -> bool:
        last_err: Exception | None = None
        for attempt in range(1, config.HTTP_RETRY_COUNT + 1):
            try:
                response = requests.post(
                    self._webhook_url,
                    json={"content": content},
                    timeout=config.HTTP_TIMEOUT_SEC,
                )
                response.raise_for_status()
                return True
            except Exception as exc:
                last_err = exc
                print(
                    f"[discord] attempt {attempt}/{config.HTTP_RETRY_COUNT} "
                    f"failed: {exc!r}"
                )
                if attempt < config.HTTP_RETRY_COUNT:
                    time.sleep(config.HTTP_RETRY_DELAY_SEC)
        print(f"[discord] 발송 최종 실패: {last_err!r}")
        return False


def _assemble_single(new_lines: list[str], new_count: int,
                     mod_lines: list[str], mod_count: int,
                     footer_text: str) -> str:
    sections: list[str] = []
    if new_lines:
        sections.append(HEADER_NEW.format(count=new_count) + "\n"
                        + "\n".join(new_lines))
    if mod_lines:
        sections.append(HEADER_MODIFIED.format(count=mod_count) + "\n"
                        + "\n".join(mod_lines))
    sections.append(footer_text)
    return SECTION_SEP.join(sections)


def _format_line(template: str, item: ParsedNotice, date_picker) -> str:
    return template.format(
        category=item.category_name,
        title=item.title,
        attachment=ATTACHMENT_MARK if item.has_attachment else "",
        date=date_picker(item),
        url=item.url,
    )


def _truncate_line(line: str) -> str:
    if len(line) <= LINE_MAX_LEN:
        return line
    return line[:LINE_MAX_LEN - len(LINE_TRUNCATE_SUFFIX)] + LINE_TRUNCATE_SUFFIX


def _pack_section(lines: list[str],
                  header_base: str) -> list[tuple[bool, list[str]]]:
    """라인 그리디 패킹. (is_first, chunk_lines) 리스트 반환."""
    budget = SPLIT_THRESHOLD - len(header_base) - _PACK_RESERVE
    chunks: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        added = len(line) + (1 if current else 0)  # 줄바꿈 1자
        if current and current_len + added > budget:
            chunks.append(current)
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += added
    if current:
        chunks.append(current)
    return [(idx == 0, c) for idx, c in enumerate(chunks)]


def _posted(item: ParsedNotice) -> str:
    return item.posted_date


def _modified(item: ParsedNotice) -> str:
    return item.modified_date
