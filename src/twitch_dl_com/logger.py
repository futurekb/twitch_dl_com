"""ロギング設定"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "twitch_dl_com", level: int = logging.INFO) -> logging.Logger:
    """
    アプリケーション用のロガーをセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
        
    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)
    
    # 既にハンドラーがある場合は再設定しない
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # ログディレクトリの作成
    log_dir = Path.home() / ".twitch_dl_com" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（日付ごとにローテーション）
    log_file = log_dir / f"twitch_dl_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # エラー専用ファイルハンドラー
    error_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# デフォルトのロガーインスタンス
logger = setup_logger()