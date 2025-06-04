"""ユーザーパネルの基底クラス"""

from typing import Dict, Optional
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from ..utils import ImageLoader, TimeFormatter
from ..constants import (
    ICON_SIZE, USER_PANEL_HEIGHT, USER_PANEL_WIDTH,
    BUTTON_VIDEO_LIST, BUTTON_DELETE,
    STYLE_USER_PANEL, STYLE_DELETE_BUTTON, STYLE_VIDEO_BUTTON,
    MSG_LIVE_NOW
)
import logging

logger = logging.getLogger(__name__)


class BaseUserPanel(QFrame):
    """ユーザーパネルの基底クラス"""
    
    # シグナル定義
    delete_requested = pyqtSignal(str)  # user_id
    video_list_requested = pyqtSignal(str)  # user_id
    
    def __init__(self, user_data: Dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_id = user_data.get('id', '')
        self._setup_ui()
        self._load_user_image()
    
    def _setup_ui(self):
        """UI初期化"""
        self.setStyleSheet(STYLE_USER_PANEL)
        self.setFixedHeight(USER_PANEL_HEIGHT)
        self.setMaximumWidth(USER_PANEL_WIDTH)
        
        # メインレイアウト
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # プロフィール画像
        self.image_label = QLabel()
        self.image_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)
        
        # 情報部分
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # ユーザー名
        self.name_label = QLabel(self._get_display_name())
        self.name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        # ステータス行
        self.status_label = QLabel(self._get_status_text())
        self.status_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.status_label)
        
        # 追加情報（派生クラスでカスタマイズ可能）
        self._add_custom_info(info_layout)
        
        layout.addLayout(info_layout, 1)
        
        # ボタン部分
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 動画一覧ボタン
        self.video_button = QPushButton(BUTTON_VIDEO_LIST)
        self.video_button.setStyleSheet(STYLE_VIDEO_BUTTON)
        self.video_button.clicked.connect(lambda: self.video_list_requested.emit(self.user_id))
        button_layout.addWidget(self.video_button)
        
        # 削除ボタン
        self.delete_button = QPushButton(BUTTON_DELETE)
        self.delete_button.setStyleSheet(STYLE_DELETE_BUTTON)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.user_id))
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
    
    def _get_display_name(self) -> str:
        """表示名を取得"""
        return self.user_data.get('display_name', self.user_data.get('login', 'Unknown'))
    
    def _get_status_text(self) -> str:
        """ステータステキストを取得"""
        if self.user_data.get('is_live'):
            return MSG_LIVE_NOW
        
        # 最後の配信時間を表示
        last_stream = self.user_data.get('last_stream')
        if last_stream:
            dt = TimeFormatter.parse_iso_time(last_stream)
            if dt:
                return TimeFormatter.get_relative_time(dt)
        
        return "オフライン"
    
    def _add_custom_info(self, layout: QVBoxLayout):
        """派生クラスでカスタム情報を追加するためのフック"""
        pass
    
    def _load_user_image(self):
        """ユーザー画像を読み込む"""
        url = self.user_data.get('profile_image_url')
        if not url:
            return
            
        try:
            image_data = ImageLoader.load_image(url)
            if image_data:
                ImageLoader.set_image_to_label(self.image_label, image_data, (ICON_SIZE, ICON_SIZE))
        except Exception as e:
            logger.error(f"画像の読み込みに失敗しました: {str(e)}")
    
    def update_user_data(self, user_data: Dict):
        """ユーザーデータを更新"""
        self.user_data = user_data
        self.name_label.setText(self._get_display_name())
        self.status_label.setText(self._get_status_text())
        self._load_user_image()