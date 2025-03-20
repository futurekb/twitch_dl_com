from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                           QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt
from ..tw_api import TwitchAPI
from ..database.db_manager import DatabaseManager

class UserRegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = TwitchAPI()
        self.db = DatabaseManager()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("ユーザ登録")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 検索バー
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ユーザ名またはIDを入力")
        self.search_input.returnPressed.connect(self.search_users)
        search_button = QPushButton("検索")
        search_button.clicked.connect(self.search_users)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 検索結果リスト
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        
        # 登録ボタン
        register_button = QPushButton("登録")
        register_button.clicked.connect(self.register_user)
        layout.addWidget(register_button)

    def search_users(self):
        query = self.search_input.text()
        if not query:
            return
            
        users = self.api.search_users(query)
        self.result_list.clear()
        
        for user in users:
            # 表示名とログイン名を組み合わせて表示
            display_text = f"{user['display_name']} ({user.get('login', 'N/A')})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, user)
            self.result_list.addItem(item)

    def register_user(self):
        current_item = self.result_list.currentItem()
        if not current_item:
            return
            
        user_data = current_item.data(Qt.ItemDataRole.UserRole)
        if self.api.register_user(user_data):
            self.accept()
        else:
            # TODO: エラーメッセージの表示
            pass
