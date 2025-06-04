"""拡張ユーザーパネル（ドラッグ＆ドロップ機能付き）"""

from typing import Dict
from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag
from .base_user_panel import BaseUserPanel
from ..constants import MSG_LIVE_NOW


class EnhancedUserPanel(BaseUserPanel):
    """ドラッグ＆ドロップ機能を持つ拡張ユーザーパネル"""
    
    # 追加のシグナル
    drag_started = pyqtSignal(str)  # user_id
    
    def __init__(self, user_data: Dict, parent=None):
        super().__init__(user_data, parent)
        self.setAcceptDrops(True)
    
    def mousePressEvent(self, event):
        """マウスプレスイベント（ドラッグ開始）"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 20:
            return
        
        # ドラッグ開始
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.user_id)
        drag.setMimeData(mime_data)
        
        self.drag_started.emit(self.user_id)
        drag.exec(Qt.DropAction.MoveAction)
    
    def _add_custom_info(self, layout: QVBoxLayout):
        """拡張情報を表示"""
        # 配信中の場合はタイトルを表示
        if self.user_data.get('is_live'):
            if 'stream_title' in self.user_data:
                title_label = QLabel(self.user_data['stream_title'])
                title_label.setStyleSheet("color: #333; font-size: 12px;")
                title_label.setWordWrap(True)
                title_label.setMaximumHeight(40)
                layout.addWidget(title_label)
        elif 'last_title' in self.user_data:
            # オフラインの場合は最後の配信タイトルを表示
            title_label = QLabel(self.user_data['last_title'])
            title_label.setStyleSheet("color: #666; font-size: 11px;")
            title_label.setWordWrap(True)
            title_label.setMaximumHeight(30)
            layout.addWidget(title_label)
        
        # ゲーム名を表示
        game_name = self.user_data.get('game_name')
        if game_name:
            game_label = QLabel(f"🎮 {game_name}")
            game_label.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(game_label)