from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QScrollArea, QLabel, QFrame, QMessageBox,
                           QComboBox)
from PyQt6.QtCore import Qt, QTimer, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QDrag
import json
import os
from typing import Dict
from ..tw_api import TwitchAPI
from ..database.db_manager import DatabaseManager
from .video_list_dialog import VideoListDialog
from .user_register_dialog import UserRegisterDialog
import urllib.request

class UserPanel(QFrame):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setup_ui()
        self.setAcceptDrops(True)  # ドロップを許可

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # パネル全体の余白を設定
        layout.setSpacing(15)  # 要素間の間隔を設定
        
        # ユーザアイコンとLIVEラベルを含むレイアウト
        icon_layout = QVBoxLayout()
        
        # ユーザアイコン
        icon_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(urllib.request.urlopen(self.user_data['profile_image_url']).read())
        icon_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        icon_layout.addWidget(icon_label)
        
        # LIVE表示
        if self.user_data['is_live']:
            live_label = QLabel("LIVE")
            live_label.setStyleSheet("""
                QLabel {
                    background-color: #ff0000;
                    color: white;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """)
            live_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(live_label)
        
        layout.addLayout(icon_layout)
        
        # ユーザ情報
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)  # ラベル間の間隔を設定
        
        # 配信者名を最初に表示
        name_label = QLabel(f"{self.user_data['display_name']} ({self.user_data['login']})")
        title_label = QLabel(self.user_data['stream_title'] if self.user_data['is_live'] else self.user_data['last_title'])
        category_label = QLabel(self.user_data['game_name'])
        
        # 各ラベルのスタイル設定
        for label in [name_label, title_label, category_label]:
            label.setWordWrap(True)  # 長いテキストの折り返しを有効化
            label.setMinimumHeight(20)  # 最小の高さを設定
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(title_label)
        info_layout.addWidget(category_label)
        layout.addLayout(info_layout, stretch=1)  # 情報レイアウトを伸縮可能に設定
        
        # ボタンレイアウト
        button_layout = QVBoxLayout()
        
        # 動画一覧ボタン
        videos_button = QPushButton("動画一覧")
        videos_button.setFixedWidth(100)
        videos_button.clicked.connect(lambda: self.show_videos())
        button_layout.addWidget(videos_button)
        
        # 削除ボタン
        delete_button = QPushButton("ユーザ削除")
        delete_button.setFixedWidth(100)
        delete_button.setStyleSheet("background-color: #ffcccc;")  # 赤っぽい背景色
        delete_button.clicked.connect(self.confirm_delete)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

    def confirm_delete(self):
        reply = QMessageBox.question(
            self,
            '削除確認',
            f'ユーザー {self.user_data["display_name"]} を非表示にしますか？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # メインウィンドウの非表示ユーザーリストに追加
            main_window = self.window()
            main_window.hidden_users.add(self.user_data['id'])
            main_window.save_hidden_users()  # 非表示設定を保存
            
            self.hide()
            layout = self.parent().layout()
            layout.removeWidget(self)
            self.deleteLater()

    def show_videos(self):
        user_details = {
            'user': {
                'id': self.user_data['id'],
                'login': self.user_data['login'],
                'display_name': self.user_data['display_name']
            },
            'stream': None,  # 必要に応じて設定
            'latest_video': None  # 必要に応じて設定
        }
        dialog = VideoListDialog(user_details, self)
        dialog.exec()

    def mousePressEvent(self, event):
        if self.window().is_ordering_mode and event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.user_data['id'])
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if self.window().is_ordering_mode and event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.window().is_ordering_mode and event.mimeData().hasText():
            source_id = event.mimeData().text()
            target_id = self.user_data['id']
            self.window().swap_user_order(source_id, target_id)
            event.acceptProposedAction()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.api = TwitchAPI()
        self.sort_order = 'custom'  # デフォルトは登録順
        self.is_ordering_mode = False
        
        # 設定ファイルのパス
        self.config_dir = os.path.join(os.path.expanduser('~'), '.twitch_dl_com')
        self.hidden_users_file = os.path.join(self.config_dir, 'hidden_users.json')
        self.user_order_file = os.path.join(self.config_dir, 'user_order.json')
        self.settings_file = os.path.join(self.config_dir, 'settings.json')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 非表示ユーザーと表示順序の読み込み
        self.hidden_users = self.load_hidden_users()
        self.user_order = self.load_user_order()
        self.load_settings()
        
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(60000)  # 1分ごとに更新

    def setup_ui(self):
        self.setWindowTitle("Twitch配信チェッカー")
        self.resize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 上部のコントロールエリア
        control_layout = QHBoxLayout()
        
        # ユーザ追加ボタン
        add_button = QPushButton("ユーザ追加")
        add_button.clicked.connect(self.show_user_register)
        control_layout.addWidget(add_button)
        
        # ソート順選択（コンボボックスに変更）
        control_layout.addStretch()
        sort_label = QLabel("表示順:")
        control_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["カスタム表示順", "登録順", "最新配信順", "名前順"])
        self.sort_combo.setCurrentText(self.default_sort_order)
        self.sort_combo.currentTextChanged.connect(self.change_sort_order)
        control_layout.addWidget(self.sort_combo)
        
        # ソート順選択の横に並び替えモードボタンを追加
        self.order_mode_button = QPushButton("並び替えモード")
        self.order_mode_button.setCheckable(True)
        self.order_mode_button.clicked.connect(self.toggle_ordering_mode)
        control_layout.addWidget(self.order_mode_button)
        
        layout.addLayout(control_layout)
        
        # ユーザリストのスクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.user_list_widget = QWidget()
        self.user_list_layout = QVBoxLayout(self.user_list_widget)
        scroll.setWidget(self.user_list_widget)
        layout.addWidget(scroll)
        
        self.load_users()

    def load_users(self):
        # 既存のパネルをクリア
        while self.user_list_layout.count():
            item = self.user_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        registered_users = self.db.get_all_users()
        
        # ユーザー順序リストの更新
        current_ids = {user['id'] for user in registered_users}
        self.user_order = [uid for uid in self.user_order if uid in current_ids]
        new_ids = current_ids - set(self.user_order)
        self.user_order.extend(new_ids)
        
        user_panels = []
        
        for user in registered_users:
            # 非表示ユーザーをスキップ
            if user['id'] in self.hidden_users:
                continue
                
            try:
                user_details = self.api.get_user_details(user['id'])
                panel = UserPanel(self._merge_user_data(user, user_details), self)
                user_panels.append(panel)
            except Exception as e:
                print(f"Error loading user {user['id']}: {str(e)}")
                continue

        # ソート順に応じてパネルを並び替え
        sorted_panels = self.sort_panels(user_panels)
        
        # パネルを追加
        for panel in sorted_panels:
            self.user_list_layout.addWidget(panel)

    def sort_panels(self, panels):
        sort_type = self.sort_combo.currentText()
        if self.is_ordering_mode or sort_type == "カスタム表示順":
            return sorted(panels, 
                key=lambda p: self.user_order.index(p.user_data['id']) 
                if p.user_data['id'] in self.user_order 
                else len(self.user_order))
        elif sort_type == "最新配信順":
            return sorted(panels, 
                key=lambda p: (not p.user_data['is_live'],
                             p.user_data.get('last_stream', '0')),
                reverse=True)
        elif sort_type == "名前順":
            return sorted(panels, 
                key=lambda p: p.user_data['display_name'].lower())
        else:  # 登録順
            return panels

    def change_sort_order(self, order):
        self.default_sort_order = order
        self.save_settings()
        self.load_users()

    def _merge_user_data(self, user: Dict, details: Dict) -> Dict:
        # ユーザーの基本情報
        user_data = {
            'id': user['id'],
            'login': user['login'],
            'display_name': user['display_name'],
            'profile_image_url': user['profile_image_url'],
            'is_live': False,  # デフォルトはオフライン
            'stream_title': '',  # デフォルトタイトル
            'last_title': '',
            'game_name': ''
        }

        if details is None:
            return user_data

        # 配信中の場合
        if details.get('stream'):
            user_data.update({
                'is_live': True,
                'stream_title': details['stream']['title'],
                'game_name': details['stream']['game_name']
            })
        # 過去の配信がある場合
        elif details.get('latest_video'):
            user_data.update({
                'last_title': details['latest_video']['title'],
                'game_name': details['latest_video']['game_name'],
                'last_stream': details['latest_video']['created_at']
            })

        return user_data

    def show_user_register(self):
        dialog = UserRegisterDialog(self)
        if dialog.exec():
            self.load_users()  # ユーザリストを更新

    def update_status(self):
        self.load_users()  # ステータスを更新

    def delete_user(self, user_id: str):
        if self.db.remove_user(user_id):
            self.load_users()

    def toggle_ordering_mode(self):
        self.is_ordering_mode = self.order_mode_button.isChecked()
        if self.is_ordering_mode:
            self.sort_combo.setEnabled(False)
            self.previous_sort = self.sort_combo.currentText()
            self.sort_combo.setCurrentText("カスタム表示順")
        else:
            self.sort_combo.setEnabled(True)
            self.save_user_order()
            if self.previous_sort != "カスタム表示順":
                self.sort_combo.setCurrentText(self.previous_sort)

    def swap_user_order(self, source_id, target_id):
        if source_id == target_id:
            return
            
        source_idx = self.user_order.index(source_id)
        target_idx = self.user_order.index(target_id)
        self.user_order[source_idx], self.user_order[target_idx] = \
            self.user_order[target_idx], self.user_order[source_idx]
        
        self.load_users()

    def load_hidden_users(self):
        try:
            if os.path.exists(self.hidden_users_file):
                with open(self.hidden_users_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            print(f"Hidden users load error: {e}")
        return set()

    def save_hidden_users(self):
        try:
            with open(self.hidden_users_file, 'w') as f:
                json.dump(list(self.hidden_users), f)
        except Exception as e:
            print(f"Hidden users save error: {e}")

    def load_user_order(self):
        try:
            if os.path.exists(self.user_order_file):
                with open(self.user_order_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"User order load error: {e}")
        return []

    def save_user_order(self):
        try:
            with open(self.user_order_file, 'w') as f:
                json.dump(self.user_order, f)
        except Exception as e:
            print(f"User order save error: {e}")

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.default_sort_order = settings.get('default_sort_order', "登録順")
            else:
                self.default_sort_order = "登録順"
        except Exception as e:
            print(f"Settings load error: {e}")
            self.default_sort_order = "登録順"

    def save_settings(self):
        try:
            settings = {
                'default_sort_order': self.default_sort_order
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Settings save error: {e}")