from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QScrollArea, QLabel, QFrame, QMessageBox,
                           QComboBox)
from PyQt6.QtCore import Qt, QTimer, QMimeData, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QDrag
import json
import os
from typing import Dict
from ..tw_api import TwitchAPI
from ..database.db_manager import DatabaseManager
from .video_list_dialog import VideoListDialog
from .user_register_dialog import UserRegisterDialog
import urllib.request

class ImageLoader(QThread):
    loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            data = urllib.request.urlopen(self.url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.loaded.emit(pixmap)
        except Exception as e:
            print(f"Error loading image: {e}")

class UserPanel(QFrame):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.icon_label = QLabel()  # icon_labelを先に初期化
        self.setAcceptDrops(True)
        
        # 画像を非同期で読み込む
        self.image_loader = ImageLoader(self.user_data['profile_image_url'])
        self.image_loader.loaded.connect(self.update_icon)
        self.image_loader.start()
        
        self.setProperty("draggable", False)  # ドラッグ可能状態を追跡
        self.setup_ui()  # UIのセットアップは最後に行う

    def update_icon(self, pixmap):
        self.icon_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 余白を縮小
        layout.setSpacing(10)  # 要素間の間隔を縮小
        
        # ユーザアイコンとLIVEラベルを含むレイアウト
        icon_layout = QVBoxLayout()
        icon_layout.setSpacing(2)  # アイコンとLIVEラベルの間隔を縮小
        
        # ユーザアイコン
        self.icon_label.setFixedSize(40, 40)  # アイコンサイズを縮小
        icon_layout.addWidget(self.icon_label)
        
        # LIVE表示
        if self.user_data['is_live']:
            live_label = QLabel("LIVE")
            live_label.setStyleSheet("""
                QLabel {
                    background-color: #ff0000;
                    color: white;
                    padding: 1px 3px;
                    border-radius: 2px;
                    font-weight: bold;
                    font-size: 10px;
                }
            """)
            live_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(live_label)
        
        layout.addLayout(icon_layout)
        
        # ユーザ情報
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)  # ラベル間の間隔を縮小
        
        # 配信者名を最初に表示
        name_label = QLabel(f"{self.user_data['display_name']} ({self.user_data['login']})")
        title_label = QLabel(self.user_data['stream_title'] if self.user_data['is_live'] else self.user_data['last_title'])
        category_label = QLabel(self.user_data['game_name'])
        
        # 各ラベルのスタイル設定
        for label in [name_label, title_label, category_label]:
            label.setWordWrap(True)
            label.setMinimumHeight(15)  # 最小の高さを縮小
        
        # フォントサイズを調整
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        title_label.setStyleSheet("font-size: 10px;")
        category_label.setStyleSheet("font-size: 10px; color: #666;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(title_label)
        info_layout.addWidget(category_label)
        layout.addLayout(info_layout, stretch=1)
        
        # ボタンレイアウト
        button_layout = QVBoxLayout()
        button_layout.setSpacing(2)  # ボタン間の間隔を縮小
        
        # 動画一覧ボタン
        videos_button = QPushButton("動画一覧")
        videos_button.setFixedWidth(70)  # ボタン幅を縮小
        videos_button.setFixedHeight(20)  # ボタン高さを縮小
        videos_button.setStyleSheet("font-size: 10px;")
        videos_button.clicked.connect(lambda: self.show_videos())
        button_layout.addWidget(videos_button)
        
        # 削除ボタン
        delete_button = QPushButton("ユーザ削除")
        delete_button.setFixedWidth(70)  # ボタン幅を縮小
        delete_button.setFixedHeight(20)  # ボタン高さを縮小
        delete_button.setStyleSheet("background-color: #ffcccc; font-size: 10px;")
        delete_button.clicked.connect(self.confirm_delete)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        # パネル全体のスタイル設定
        self.setStyleSheet("""
            QFrame[draggable="true"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f0f0f0, stop:1 #e3e3e3);
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QFrame[draggable="true"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e7e7e7, stop:1 #d7d7d7);
                border: 2px solid #aaaaaa;
            }
        """)

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
            
            # ドラッグ時のプレビュー画像を生成
            pixmap = self.grab()
            # 浮動小数点数を整数に変換
            scaled_width = int(self.width() * 0.95)
            scaled_height = int(self.height() * 0.95)
            pixmap = pixmap.scaled(scaled_width, scaled_height,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width()//2, 10))
            
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if self.window().is_ordering_mode and event.mimeData().hasText():
            event.acceptProposedAction()
            # フレーム全体のスタイルのみを変更
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #4a90e2;
                    background: #e8f2fd;
                    border-radius: 3px;
                }
            """)

    def dragLeaveEvent(self, event):
        if self.window().is_ordering_mode:
            # 元のスタイルに戻す
            self.setup_ui()

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
        # パフォーマンス改善のため、一時的にレイアウトを無効化
        self.user_list_widget.setUpdatesEnabled(False)
        
        # 既存のパネルをクリア
        while self.user_list_layout.count():
            item = self.user_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        registered_users = self.db.get_all_users()
        
        # バッチ処理でユーザー詳細を取得
        user_details = {}
        batch_size = 10
        for i in range(0, len(registered_users), batch_size):
            batch = registered_users[i:i + batch_size]
            user_ids = [user['id'] for user in batch]
            try:
                details = self.api.get_users_details(user_ids)
                user_details.update(details)
            except Exception as e:
                print(f"Error loading users batch: {str(e)}")

        user_panels = []
        for user in registered_users:
            if user['id'] in self.hidden_users:
                continue
                
            try:
                details = user_details.get(user['id'])
                panel = UserPanel(self._merge_user_data(user, details), self)
                user_panels.append(panel)
            except Exception as e:
                print(f"Error creating panel for user {user['id']}: {str(e)}")
                continue

        # ソートとパネル追加
        sorted_panels = self.sort_panels(user_panels)
        for panel in sorted_panels:
            self.user_list_layout.addWidget(panel)
        
        # レイアウトの更新を再開
        self.user_list_widget.setUpdatesEnabled(True)

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
        if order == self.default_sort_order:
            return
        
        self.default_sort_order = order
        self.save_settings()
        
        # パネルの再ソートのみを実行（完全な再読み込みを避ける）
        panels = []
        for i in range(self.user_list_layout.count()):
            panel = self.user_list_layout.takeAt(0).widget()
            if panel:
                panels.append(panel)
        
        sorted_panels = self.sort_panels(panels)
        for panel in sorted_panels:
            self.user_list_layout.addWidget(panel)

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
        # 過去の配信がある場合のみ
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
        # 更新が必要なユーザーのみを更新
        for i in range(self.user_list_layout.count()):
            panel = self.user_list_layout.itemAt(i).widget()
            if panel:
                try:
                    details = self.api.get_user_details(panel.user_data['id'])
                    if self._has_status_changed(panel.user_data, details):
                        new_data = self._merge_user_data(panel.user_data, details)
                        panel.user_data = new_data
                        panel.setup_ui()
                except Exception as e:
                    print(f"Error updating user {panel.user_data['id']}: {str(e)}")

    def _has_status_changed(self, old_data, new_details):
        if new_details is None:
            return False
        if new_details.get('stream'):
            return (not old_data['is_live'] or 
                   old_data['stream_title'] != new_details['stream']['title'])
        else:
            return old_data['is_live']

    def delete_user(self, user_id: str):
        if self.db.remove_user(user_id):
            self.load_users()
            
    def toggle_ordering_mode(self):
        self.is_ordering_mode = self.order_mode_button.isChecked()
        
        # パネルのドラッグ可能状態を更新
        for i in range(self.user_list_layout.count()):
            panel = self.user_list_layout.itemAt(i).widget()
            if panel:
                panel.setProperty("draggable", self.is_ordering_mode)
                panel.style().unpolish(panel)
                panel.style().polish(panel)
        
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