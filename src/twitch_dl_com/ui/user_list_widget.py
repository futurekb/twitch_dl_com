from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from ..database.db_manager import DatabaseManager
from ..tw_api import TwitchAPI
from .user_item_widget import UserItemWidget

class UserListWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.api = TwitchAPI()
        
        # スクロール可能なウィジェットの設定
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(container)
        self.setWidgetResizable(True)
        
        self.refresh_list()

    def refresh_list(self):
        # 既存のアイテムをクリア
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 登録済みユーザーを取得して表示
        users = self.db.get_all_users()
        for user in users:
            try:
                details = self.api.get_user_details(user['twitch_id'])
                user_item = UserItemWidget(details)
                self.layout.addWidget(user_item)
            except Exception as e:
                print(f"Error loading user {user['display_name']}: {e}")
