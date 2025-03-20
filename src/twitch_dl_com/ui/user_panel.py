from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from datetime import datetime
import urllib.request
from .video_list_dialog import VideoListDialog

class UserPanel(QFrame):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # ユーザアイコン
        icon_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(urllib.request.urlopen(self.user_data['profile_image_url']).read())
        icon_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(icon_label)
        
        # ユーザ情報
        info_layout = QVBoxLayout()
        
        # タイトルと配信状態
        if self.user_data['is_live']:
            status_text = "🔴 配信中"
            title_text = self.user_data['stream_title']
        else:
            time_ago = self._get_time_ago(self.user_data.get('last_stream'))
            status_text = f"⚫ {time_ago}"
            title_text = self.user_data['last_title']
            
        status_label = QLabel(status_text)
        title_label = QLabel(title_text)
        name_label = QLabel(f"{self.user_data['display_name']} ({self.user_data['login']})")
        category_label = QLabel(self.user_data['game_name'])
        
        info_layout.addWidget(status_label)
        info_layout.addWidget(title_label)
        info_layout.addWidget(name_label)
        info_layout.addWidget(category_label)
        layout.addLayout(info_layout)
        
        # ボタンレイアウト
        button_layout = QVBoxLayout()
        
        videos_button = QPushButton("動画一覧")
        videos_button.clicked.connect(self.show_videos)
        button_layout.addWidget(videos_button)
        
        delete_button = QPushButton("削除")
        delete_button.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

    def _get_time_ago(self, timestamp):
        if not timestamp:
            return "配信履歴なし"
            
        last_stream = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(last_stream.tzinfo)
        delta = now - last_stream
        
        if delta.days > 0:
            return f"{delta.days}日前"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}時間前"
        minutes = (delta.seconds // 60) % 60
        return f"{minutes}分前"

    def show_videos(self):
        dialog = VideoListDialog(self.user_data['id'], self)
        dialog.exec()

    def delete_user(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, '確認',
            f"{self.user_data['display_name']}を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().delete_user(self.user_data['id'])
