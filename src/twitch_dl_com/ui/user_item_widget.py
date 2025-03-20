from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                           QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import requests
from datetime import datetime
from .video_list_widget import VideoListDialog

class UserItemWidget(QFrame):
    user_deleted = pyqtSignal(str)  # ユーザー削除時のシグナル

    def __init__(self, user_details):
        super().__init__()
        self.user_details = user_details
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setFixedHeight(60)  # 高さをさらに少し縮小
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # ユーザーアイコン
        icon_label = QLabel()
        pixmap = self._load_image(user_details['user']['profile_image_url'])
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(40, 40)
        layout.addWidget(icon_label)
        
        # ユーザー名
        username_label = QLabel(user_details['user']['display_name'])
        username_label.setFixedWidth(120)
        username_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(username_label)

        # 配信/動画情報（1行に統合）
        if user_details['stream']:
            self._add_live_info(layout)
        else:
            self._add_offline_info(layout)
            
        layout.addStretch(1)  # 右端にボタンを寄せる
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        videos_button = QPushButton("動画一覧")
        videos_button.setFixedWidth(80)
        videos_button.clicked.connect(self.show_videos)
        button_layout.addWidget(videos_button)
        
        delete_button = QPushButton("削除")
        delete_button.setFixedWidth(60)
        delete_button.clicked.connect(self._on_delete)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
    def _load_image(self, url):
        response = requests.get(url)
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        return pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
        
    def _add_live_info(self, layout):
        stream = self.user_details['stream']
        status_label = QLabel("🔴 LIVE")
        status_label.setFixedWidth(60)
        layout.addWidget(status_label)
        
        title_label = QLabel(stream['title'])
        title_label.setFixedWidth(300)
        title_label.setToolTip(stream['title'])
        title_label.setTextFormat(Qt.TextFormat.PlainText)
        title_label.setTextElideMode(Qt.TextElideMode.ElideRight)
        layout.addWidget(title_label)
        
        game_label = QLabel(stream['game_name'])
        game_label.setFixedWidth(150)
        game_label.setTextElideMode(Qt.TextElideMode.ElideRight)
        layout.addWidget(game_label)
        
    def _add_offline_info(self, layout):
        video = self.user_details['latest_video']
        if video:
            status_label = QLabel("最新配信")
            status_label.setFixedWidth(60)
            layout.addWidget(status_label)
            
            title_label = QLabel(video['title'])
            title_label.setFixedWidth(300)
            title_label.setToolTip(video['title'])
            title_label.setTextFormat(Qt.TextFormat.PlainText)
            title_label.setTextElideMode(Qt.TextElideMode.ElideRight)
            layout.addWidget(title_label)
            
            game_label = QLabel(video['game_name'])
            game_label.setFixedWidth(150)
            game_label.setTextElideMode(Qt.TextElideMode.ElideRight)
            layout.addWidget(game_label)
            
            created_at = datetime.fromisoformat(video['created_at'].replace('Z', '+00:00'))
            delta = datetime.now(created_at.tzinfo) - created_at
            days = delta.days
            hours = delta.seconds // 3600
            time_label = QLabel(f"{days}日{hours}時間前")
            time_label.setFixedWidth(100)
            layout.addWidget(time_label)
            
    def _on_delete(self):
        self.user_deleted.emit(self.user_details['user']['login'])  # user_idからloginに変更
        self.deleteLater()
        
    def show_videos(self):
        dialog = VideoListDialog(self.user_details, self)
        dialog.exec()
