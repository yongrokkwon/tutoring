from datetime import datetime

from .. import config, db
from ..crawler.parser import ParsedNotice
from ..repository import notifications as notif_repo
from ..repository import users as users_repo
from .discord import DiscordChannel


def send(new: list[ParsedNotice],
         modified: list[ParsedNotice],
         user_id: int = config.DEFAULT_USER_ID) -> None:
    """영역 1 이 호출하는 entry. area-2-notifier.md §2.3.

    Tx1: webhook 조회 → commit
    HTTP POST (Tx 밖): 발송 시도
    Tx2: notifications batch INSERT → commit
    """
    # Tx1: webhook 조회 (짧음)
    with db.transaction() as conn:
        webhook = users_repo.get_discord_webhook(conn, user_id)

    # 시각 고정 — webhook 유무 무관
    sent_at = datetime.now()

    # HTTP POST — 트랜잭션 밖
    if webhook:
        ok = DiscordChannel(webhook).send(new, modified, sent_at)
    else:
        print("[notifier] webhook 없음 — 시도 생략")
        ok = False

    status_id = (notif_repo.STATUS_SUCCESS if ok
                 else notif_repo.STATUS_FAILED)

    # Tx2: 이력 INSERT (짧음)
    with db.transaction() as conn:
        notif_repo.insert_batch(
            conn=conn,
            user_id=user_id,
            channel_id=notif_repo.CHANNEL_DISCORD,
            new=new,
            modified=modified,
            status_id=status_id,
            sent_at=sent_at,
        )
