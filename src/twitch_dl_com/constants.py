"""定数定義ファイル"""

# UI関連の定数
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 400
WINDOW_MIN_HEIGHT = 300

# アイコンサイズ
ICON_SIZE = 50
ICON_SIZE_SMALL = 30
ICON_SIZE_LARGE = 100

# ウィジェットサイズ
USER_PANEL_WIDTH = 370
USER_PANEL_HEIGHT = 120
USER_PANEL_MIN_HEIGHT = 100
PANEL_SPACING = 10

# カラムサイズ
COLUMN_TITLE_WIDTH = 300
COLUMN_STREAMER_WIDTH = 120
COLUMN_DATE_WIDTH = 150
COLUMN_DURATION_WIDTH = 80
COLUMN_GAME_WIDTH = 150
COLUMN_ACTION_WIDTH = 70

# タイマー設定
UPDATE_INTERVAL_MS = 60000  # 1分
IMAGE_LOAD_DELAY_MS = 100

# ネットワーク設定
REQUEST_TIMEOUT = 10  # 秒
MAX_RETRY_COUNT = 3
RETRY_DELAY = 1  # 秒

# API設定
TWITCH_API_BATCH_SIZE = 10
VIDEO_FETCH_LIMIT = 20

# ファイルパス
CONFIG_DIR = "config"
CACHE_DIR = ".twitch_dl_com"
SETTINGS_FILE = "settings.json"
TOKEN_CACHE_FILE = "token_cache.json"
REGISTERED_USERS_FILE = "registered_users.json"

# ファイル名パターン
VIDEO_CACHE_PATTERN = "videos_{user_id}.json"
COMMENT_FILE_PATTERN = "comments_{login}-{date}.csv"

# ボタンテキスト
BUTTON_VIDEO_LIST = "動画一覧"
BUTTON_DELETE = "削除"
BUTTON_DOWNLOAD = "ダウンロード"
BUTTON_UPDATE = "更新"
BUTTON_REGISTER = "登録"
BUTTON_CLOSE = "閉じる"

# ウィンドウタイトル
WINDOW_TITLE_MAIN = "Twitch User Manager"
WINDOW_TITLE_VIDEO_LIST = "{username}の動画"
WINDOW_TITLE_USER_REGISTER = "ユーザー登録"

# メッセージ
MSG_LOADING = "読み込み中..."
MSG_LIVE_NOW = "配信中"
MSG_ERROR_LOAD_USERS = "ユーザー情報の読み込みに失敗しました"
MSG_ERROR_DOWNLOAD_COMMENTS = "コメントのダウンロードに失敗しました: {error}"
MSG_SUCCESS_DOWNLOAD_COMMENTS = "コメントをダウンロードしました: {filename}"
MSG_CONFIRM_DELETE = "{username}を削除しますか？"
MSG_USER_NOT_FOUND = "ユーザーが見つかりませんでした"

# 時間フォーマット
TIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%SZ"
TIME_FORMAT_DISPLAY = "%Y/%m/%d %H:%M"
TIME_FORMAT_FILE = "%Y-%m-%d_%H_%M"

# 時間の単位
TIME_JUST_NOW = "たった今"
TIME_MINUTES_AGO = "{minutes}分前"
TIME_HOURS_AGO = "{hours}時間前"
TIME_DAYS_AGO = "{days}日前"

# ソート順
SORT_ORDER_LATEST = "latest"
SORT_ORDER_OLDEST = "oldest"
SORT_ORDER_NAME = "name"

# スタイルシート
STYLE_USER_PANEL = """
    QFrame {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
    }
    QFrame:hover {
        background-color: #e8e8e8;
    }
"""

STYLE_DELETE_BUTTON = """
    QPushButton {
        background-color: #ff4444;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #ff6666;
    }
"""

STYLE_VIDEO_BUTTON = """
    QPushButton {
        background-color: #9146ff;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #a970ff;
    }
"""