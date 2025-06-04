"""画像ローダーユーティリティ"""

import requests
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from ..constants import REQUEST_TIMEOUT, MAX_RETRY_COUNT, RETRY_DELAY
import time
import logging

logger = logging.getLogger(__name__)


class ImageLoader:
    """同期的な画像ローダー"""
    
    @staticmethod
    def load_image(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[bytes]:
        """URLから画像データを取得"""
        if not url:
            return None
            
        for attempt in range(MAX_RETRY_COUNT):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.content
            except requests.exceptions.RequestException as e:
                logger.warning(f"画像の読み込みに失敗しました (試行 {attempt + 1}/{MAX_RETRY_COUNT}): {url} - {str(e)}")
                if attempt < MAX_RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"画像の読み込みに完全に失敗しました: {url}")
                    return None
        return None
    
    @staticmethod
    def set_image_to_label(label: QLabel, image_data: bytes, size: tuple = None):
        """ラベルに画像を設定"""
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            if size:
                pixmap = pixmap.scaled(size[0], size[1])
            
            label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"画像の設定に失敗しました: {str(e)}")


class AsyncImageLoader(QThread):
    """非同期画像ローダー（スレッド版）"""
    
    image_loaded = pyqtSignal(str, bytes)  # URL, 画像データ
    image_failed = pyqtSignal(str, str)    # URL, エラーメッセージ
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue = []
        self._running = False
    
    def add_request(self, url: str, identifier: str = None):
        """画像読み込みリクエストを追加"""
        self._queue.append((url, identifier or url))
        if not self._running:
            self.start()
    
    def run(self):
        """スレッドのメイン処理"""
        self._running = True
        
        while self._queue:
            url, identifier = self._queue.pop(0)
            
            image_data = ImageLoader.load_image(url)
            if image_data:
                self.image_loaded.emit(identifier, image_data)
            else:
                self.image_failed.emit(identifier, "画像の読み込みに失敗しました")
            
            # 短い遅延を入れて負荷を軽減
            time.sleep(0.1)
        
        self._running = False