from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                           QPushButton, QHeaderView, QProgressDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QSettings
from datetime import datetime, timezone, timedelta
import pyperclip
import subprocess
import asyncio
import json
import os
import csv
from concurrent.futures import ThreadPoolExecutor
from ..tw_api import TwitchAPI

class CommentDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, api, video_id):
        super().__init__()
        self.api = api
        self.video_id = video_id
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            if self.cancelled:
                return
            comments = self.api.download_comments(self.video_id, self.progress.emit)
            if not self.cancelled:
                self.finished.emit(True, f"{len(comments)}件のコメントを保存しました")
        except Exception as e:
            if not self.cancelled:
                self.finished.emit(False, f"エラーが発生しました: {str(e)}")

class DownloadMonitor(QObject):
    finished = pyqtSignal()

    def __init__(self, process):
        super().__init__()
        self.process = process

    def monitor(self):
        self.process.wait()
        self.finished.emit()

class VideoListDialog(QDialog):
    def __init__(self, user_details, parent=None):
        super().__init__(parent)
        self.api = TwitchAPI()
        self.user_details = user_details
        self.user_id = user_details['user']['id']
        self.download_threads = {}
        self.cached_videos = {}
        self.cache_file = os.path.join(
            os.path.expanduser('~'),
            '.twitch_dl_com',
            f'videos_{self.user_id}.json'
        )
        
        # キャッシュディレクトリの作成
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # コメントファイルの保存先ディレクトリを設定
        self.comments_dir = os.path.join(
            os.path.expanduser('~'),
            '.twitch_dl_com',
            'comments'
        )
        os.makedirs(self.comments_dir, exist_ok=True)
        
        self.setWindowTitle("配信動画一覧")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 動画一覧テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # カテゴリ列を削除
        self.table.setHorizontalHeaderLabels([
            "配信タイトル", "配信時間", "開始時間", "終了時間", "URLコピー", "コメント"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # テーブルの設定を追加
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        
        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # タイトル
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 配信時間
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 開始時間
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 終了時間
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # URLコピー
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # コメントDL
        
        # URLとコメントボタンの幅を固定
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        
        # 選択行の色を設定
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #e0e0e0;
                color: black;
            }
        """)
        
        layout.addWidget(self.table)
        
        self.load_videos()

        # ウィンドウ位置の復元
        settings = QSettings('TwitchDLCom', 'VideoList')
        geometry = settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
    def load_videos(self):
        self.table.setSortingEnabled(False)
        
        # キャッシュされた動画情報の読み込み
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cached_videos = json.load(f)
        except Exception as e:
            print(f"キャッシュの読み込みに失敗: {e}")
            self.cached_videos = {}

        # 最新の動画情報を取得
        try:
            videos = self.api.get_videos(self.user_id)
            # キャッシュの更新
            for video in videos:
                self.cached_videos[video['url']] = video
            
            # キャッシュの保存
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cached_videos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"動画情報の取得に失敗: {e}")
            videos = []

        # キャッシュから全ての動画を表示
        all_videos = list(self.cached_videos.values())
        self.table.setRowCount(len(all_videos))
        
        for i, video in enumerate(sorted(all_videos, key=lambda x: x['created_at'], reverse=True)):
            video_url = video['url']
            is_available = video_url in [v['url'] for v in videos] if videos else False
            
            # タイトルをUTF-8で正しく表示
            title_item = QTableWidgetItem(video['title'])
            if not is_available:
                title_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 0, title_item)
            self.table.setItem(i, 1, QTableWidgetItem(self._format_duration(video['duration'])))
            start_time = self._format_datetime(video['created_at'])
            self.table.setItem(i, 2, QTableWidgetItem(start_time))
            
            # 終了時間を計算して表示
            start_dt = datetime.fromisoformat(video['created_at'].replace('Z', '+00:00'))
            duration = self._parse_duration(video['duration'])
            end_time = start_dt + duration
            self.table.setItem(i, 3, QTableWidgetItem(self._format_datetime(end_time.isoformat())))
            
            # URLコピーボタン
            url_button = QPushButton("URLコピーする")
            url_button.clicked.connect(lambda checked, url=video['url']: self._copy_url(url))
            if not is_available:
                url_button.setEnabled(False)
                url_button.setToolTip("この動画は現在利用できません")
            self.table.setCellWidget(i, 4, url_button)
            
            dl_button = QPushButton("コメントDLする")
            end_time = datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')) + self._parse_duration(video['duration'])
            is_live = datetime.now(timezone.utc) < end_time.replace(tzinfo=timezone.utc)
            
            if is_live or not is_available:
                dl_button.setEnabled(False)
                tooltip = "配信中の動画はコメントをダウンロードできません" if is_live else "この動画は現在利用できません"
                dl_button.setToolTip(tooltip)
            else:
                dl_button.clicked.connect(lambda checked, url=video['url'], btn=dl_button: self._download_comments(url, btn))
            self.table.setCellWidget(i, 5, dl_button)
        
        self.table.setSortingEnabled(True)
            
    def _format_duration(self, duration):
        """'3h42m47s' 形式の文字列を '03:42:47' 形式に変換"""
        hours = minutes = seconds = 0
        current = ''
        
        for char in duration:
            if (char.isdigit()):
                current += char
            elif (char == 'h'):
                hours = int(current)
                current = ''
            elif (char == 'm'):
                minutes = int(current)
                current = ''
            elif (char == 's'):
                seconds = int(current)
                current = ''
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def _format_datetime(self, dt_str):
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.astimezone().strftime('%Y-%m-%d %H:%M')

    def _parse_duration(self, duration):
        """'3h42m47s' 形式の文字列をtimedeltaに変換"""
        hours = minutes = seconds = 0
        current = ''
        
        for char in duration:
            if (char.isdigit()):
                current += char
            elif (char == 'h'):
                hours = int(current)
                current = ''
            elif (char == 'm'):
                minutes = int(current)
                current = ''
            elif (char == 's'):
                seconds = int(current)
                current = ''
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def _copy_url(self, url):
        pyperclip.copy(url)
        QMessageBox.information(self, "完了", "URLをクリップボードにコピーしました")

    async def process_comments_file(self, file_path, video_url, start_time, streamer_id):
        try:
            comments = []
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # タイムスタンプの計算
                    time_parts = list(map(int, row['time'].split(':')))
                    seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
                    comment_time = start_datetime + timedelta(seconds=seconds)

                    # ユーザーIDの抽出
                    user_name = row['user_name']
                    user_id = user_name.split('(')[-1].rstrip(')')

                    comments.append((
                        video_url,
                        streamer_id,
                        user_id,
                        row['user_color'],
                        comment_time.isoformat(),
                        row['message']
                    ))

            # コメントの保存
            with ThreadPoolExecutor() as executor:
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    self.db.save_comments,
                    video_url,
                    streamer_id,
                    comments
                )

        except Exception as e:
            print(f"コメント処理エラー: {str(e)}")

    def _download_comments(self, video_url, button):
        try:
            current_row = self.table.currentRow()
            video_info = {
                'login': self.user_details['user']['login'],
                'start_time': self.table.item(current_row, 2).text().replace(' ', '_'),
                'title': self.table.item(current_row, 0).text()
            }
            
            # 出力ファイルパスの設定
            output_file = f"{video_info['login']}-{video_info['start_time']}.csv"
            output_path = os.path.join(self.comments_dir, output_file)
            
            # 保存先ディレクトリの書き込み権限を確認
            if not os.access(self.comments_dir, os.W_OK):
                raise PermissionError(f"保存先ディレクトリ {self.comments_dir} への書き込み権限がありません")
            
            button.setStyleSheet("background-color: #90EE90;")
            button.setEnabled(False)
            
            process = subprocess.Popen([
                'python', 
                '/home/mitarashi/projects/twitch_dl_com/twitch_chat_downloader.py', 
                f'--url={video_url}',
                f'--output={output_path}'
            ])
            
            # 監視スレッドの設定
            thread = QThread()
            monitor = DownloadMonitor(process)
            monitor.moveToThread(thread)
            
            monitor.finished.connect(
                lambda: asyncio.run(self.process_comments_file(
                    output_path,
                    video_url,
                    video_info['start_time'],
                    self.user_details['user']['id']
                ))
            )
            monitor.finished.connect(lambda: self._on_download_complete(button, thread, monitor))
            
            thread.started.connect(monitor.monitor)
            self.download_threads[button] = (thread, monitor)
            thread.start()
            
        except PermissionError as e:
            button.setStyleSheet("")
            button.setEnabled(True)
            QMessageBox.critical(self, "エラー", str(e))
        except Exception as e:
            button.setStyleSheet("")
            button.setEnabled(True)
            QMessageBox.critical(self, "エラー", f"ダウンロードの開始に失敗しました: {str(e)}")

    def _on_download_complete(self, button, thread, monitor):
        """ダウンロード完了時の処理"""
        button.setStyleSheet("")
        button.setEnabled(True)
        
        # スレッドのクリーンアップ
        thread.quit()
        thread.wait()
        if button in self.download_threads:
            del self.download_threads[button]

    def closeEvent(self, event):
        """ウィンドウが閉じられる時の処理"""
        # ウィンドウ位置の保存
        settings = QSettings('TwitchDLCom', 'VideoList')
        settings.setValue('geometry', self.saveGeometry())

        # 実行中のダウンロードをキャンセル
        for thread, monitor in self.download_threads.values():
            if monitor.process:
                monitor.process.terminate()
            thread.quit()
            thread.wait()
        
        self.download_threads.clear()
        event.accept()
