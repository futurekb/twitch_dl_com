"""カスタム例外クラス"""


class TwitchDLException(Exception):
    """基底例外クラス"""
    pass


class AuthenticationError(TwitchDLException):
    """認証関連のエラー"""
    pass


class APIError(TwitchDLException):
    """API呼び出し関連のエラー"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ConfigurationError(TwitchDLException):
    """設定関連のエラー"""
    pass


class NetworkError(TwitchDLException):
    """ネットワーク関連のエラー"""
    def __init__(self, message: str, retry_count: int = 0):
        super().__init__(message)
        self.retry_count = retry_count


class DownloadError(TwitchDLException):
    """ダウンロード関連のエラー"""
    pass


class UserNotFoundError(TwitchDLException):
    """ユーザーが見つからない場合のエラー"""
    def __init__(self, user_id: str):
        super().__init__(f"ユーザーが見つかりません: {user_id}")
        self.user_id = user_id


class VideoNotFoundError(TwitchDLException):
    """動画が見つからない場合のエラー"""
    def __init__(self, video_id: str):
        super().__init__(f"動画が見つかりません: {video_id}")
        self.video_id = video_id