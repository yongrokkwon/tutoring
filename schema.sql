-- 광운대 공지사항 크롤러 — DB 스키마 (1단계 MVP)
-- docs/source-spec/db-schema.txt 의 SQLite 구현본.
-- 본 구현 단계에서 _pre-impl-checklist.md §1 결정 반영:
--   · notices.url NOT NULL (영역 1 §10.1)
--   · categories.name TEXT NOT NULL UNIQUE (영역 1 §10.2)
--   · 정렬 정책: is_pinned DESC, MAX(posted_date, modified_date) DESC,
--                updated_at DESC, duid DESC

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS frequency_modes (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    key        TEXT PRIMARY KEY,
    template   TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    email               TEXT UNIQUE,
    name                TEXT,
    discord_webhook_url TEXT,
    kakao_phone         TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id        INTEGER PRIMARY KEY REFERENCES users(id),
    frequency_mode INTEGER NOT NULL DEFAULT 2
        REFERENCES frequency_modes(id)
        CHECK (frequency_mode IN (0,1,2,3)),
    is_active      INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0,1)),
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_custom_times (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    time_hhmm  TEXT NOT NULL
        CHECK (time_hhmm GLOB '[0-9][0-9]:[0-9][0-9]'
               AND time_hhmm >= '10:00'
               AND time_hhmm <= '17:00'),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, time_hhmm)
);

CREATE TABLE IF NOT EXISTS notices (
    duid          INTEGER PRIMARY KEY,
    title         TEXT NOT NULL,
    category_id   INTEGER NOT NULL REFERENCES categories(id),
    author        TEXT NOT NULL,
    posted_date   TEXT NOT NULL
        CHECK (posted_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    modified_date TEXT NOT NULL
        CHECK (modified_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    is_pinned     INTEGER NOT NULL DEFAULT 0 CHECK (is_pinned IN (0,1)),
    marked_as_new INTEGER NOT NULL DEFAULT 0 CHECK (marked_as_new IN (0,1)),
    url           TEXT NOT NULL,
    content       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attachments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    notice_duid INTEGER NOT NULL REFERENCES notices(duid),
    filename    TEXT,
    url         TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_attachments_duid ON attachments(notice_duid);

CREATE TABLE IF NOT EXISTS notification_channels (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notification_types (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notification_statuses (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    notice_duid INTEGER NOT NULL REFERENCES notices(duid),
    channel_id  INTEGER NOT NULL REFERENCES notification_channels(id),
    type_id     INTEGER NOT NULL REFERENCES notification_types(id),
    status_id   INTEGER NOT NULL REFERENCES notification_statuses(id),
    sent_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
