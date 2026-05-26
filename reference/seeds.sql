-- 시드 데이터: 마스터 + MVP 1인 사용자 + 기본 설정.

INSERT OR IGNORE INTO categories (id) VALUES
    (0), (1), (2), (3), (4), (5), (6), (7), (8), (9), (10);

INSERT OR IGNORE INTO frequency_modes (id, name) VALUES
    (0, 'custom'),
    (1, 'high'),
    (2, 'medium'),
    (3, 'low');

INSERT OR IGNORE INTO notification_channels (id, name) VALUES
    (1, 'discord'),
    (2, 'kakao');

INSERT OR IGNORE INTO notification_types (id, name) VALUES
    (1, 'new'),
    (2, 'modified');

INSERT OR IGNORE INTO notification_statuses (id, name) VALUES
    (1, 'success'),
    (2, 'failed');

INSERT OR IGNORE INTO messages (key, template) VALUES
    ('ui.label.category.0',  '일반'),
    ('ui.label.category.1',  '학사'),
    ('ui.label.category.2',  '학생'),
    ('ui.label.category.3',  '봉사'),
    ('ui.label.category.4',  '등록/장학'),
    ('ui.label.category.5',  '입학'),
    ('ui.label.category.6',  '시설'),
    ('ui.label.category.7',  '병무'),
    ('ui.label.category.8',  '외부'),
    ('ui.label.category.9',  '국제교류'),
    ('ui.label.category.10', '국제학생'),
    ('ui.label.frequency.0', '기타'),
    ('ui.label.frequency.1', '고빈도'),
    ('ui.label.frequency.2', '중빈도'),
    ('ui.label.frequency.3', '저빈도');

-- MVP 1인 사용자. 디스코드 웹훅은 슬라이스 2에서 채움.
INSERT OR IGNORE INTO users (id) VALUES (1);
INSERT OR IGNORE INTO user_settings (user_id, frequency_mode, is_active)
    VALUES (1, 2, 1);
