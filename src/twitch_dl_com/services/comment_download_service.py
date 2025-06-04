"""コメントダウンロードサービス"""

import csv
import subprocess
import os
from typing import List, Dict, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
from ..utils import TimeFormatter
from ..constants import COMMENT_FILE_PATTERN, CACHE_DIR
import logging

logger = logging.getLogger(__name__)


class CommentDownloadService:
    """Twitchコメントのダウンロードを管理するサービス"""
    
    def __init__(self):
        self.download_dir = Path.home() / CACHE_DIR / "comments"
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """ダウンロードディレクトリを作成"""
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_comments(self, video_url: str, user_login: str, 
                         progress_callback: Optional[Callable[[int], None]] = None) -> Optional[str]:
        """
        コメントをダウンロードする
        
        Args:
            video_url: Twitch動画のURL
            user_login: 配信者のログイン名
            progress_callback: 進行状況を通知するコールバック関数
            
        Returns:
            保存したファイルのパス（失敗時はNone）
        """
        try:
            # ファイル名の生成
            timestamp = TimeFormatter.format_file_time(datetime.now())
            filename = COMMENT_FILE_PATTERN.format(login=user_login, date=timestamp)
            output_path = self.download_dir / filename
            
            # twitch_chat_downloader.pyのパスを検索
            downloader_path = self._find_downloader_script()
            if not downloader_path:
                raise Exception("twitch_chat_downloader.pyが見つかりません")
            
            # ダウンロードコマンドの実行
            cmd = ['python', str(downloader_path), video_url, str(output_path)]
            
            logger.info(f"コメントダウンロードを開始: {video_url}")
            
            # プロセスの実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # プログレス更新のシミュレーション（実際のプログレスはスクリプトから取得する必要がある）
            if progress_callback:
                for i in range(0, 100, 10):
                    progress_callback(i)
                    import time
                    time.sleep(0.5)
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"ダウンロードエラー: {stderr}")
            
            if progress_callback:
                progress_callback(100)
            
            logger.info(f"コメントダウンロード完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"コメントダウンロードに失敗しました: {str(e)}")
            return None
    
    def _find_downloader_script(self) -> Optional[Path]:
        """twitch_chat_downloader.pyスクリプトを探す"""
        # 予想される場所をチェック
        possible_paths = [
            Path.cwd() / "twitch_chat_downloader.py",
            Path.cwd().parent / "twitch_chat_downloader.py",
            Path(__file__).parent.parent.parent / "twitch_chat_downloader.py",
            Path.home() / "projects" / "twitch_dl_com" / "twitch_chat_downloader.py"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def download_comments_api(self, video_id: str, comments_data: List[Dict], 
                            user_login: str) -> Optional[str]:
        """
        APIから取得したコメントデータをCSVファイルに保存
        
        Args:
            video_id: 動画ID
            comments_data: コメントデータのリスト
            user_login: 配信者のログイン名
            
        Returns:
            保存したファイルのパス（失敗時はNone）
        """
        try:
            # ファイル名の生成
            timestamp = TimeFormatter.format_file_time(datetime.now())
            filename = COMMENT_FILE_PATTERN.format(login=user_login, date=timestamp)
            output_path = self.download_dir / filename
            
            # CSVファイルへの書き込み
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'username', 'message', 'user_color']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for comment in comments_data:
                    writer.writerow({
                        'timestamp': comment.get('created_at', ''),
                        'username': comment.get('commenter', {}).get('display_name', ''),
                        'message': comment.get('message', {}).get('body', ''),
                        'user_color': comment.get('message', {}).get('user_color', '')
                    })
            
            logger.info(f"コメントをCSVに保存しました: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"CSVファイルの保存に失敗しました: {str(e)}")
            return None
    
    def get_download_dir(self) -> Path:
        """ダウンロードディレクトリのパスを取得"""
        return self.download_dir
    
    def list_downloaded_files(self, user_login: Optional[str] = None) -> List[Path]:
        """
        ダウンロード済みファイルのリストを取得
        
        Args:
            user_login: 特定のユーザーのファイルのみを取得する場合は指定
            
        Returns:
            ファイルパスのリスト
        """
        pattern = f"comments_{user_login}-*.csv" if user_login else "comments_*.csv"
        return sorted(self.download_dir.glob(pattern), reverse=True)
    
    def delete_old_files(self, days: int = 30) -> int:
        """
        指定日数より古いファイルを削除
        
        Args:
            days: 保持する日数
            
        Returns:
            削除したファイル数
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file_path in self.download_dir.glob("comments_*.csv"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"古いファイルを削除しました: {file_path}")
                except Exception as e:
                    logger.error(f"ファイルの削除に失敗しました: {file_path} - {str(e)}")
        
        return deleted_count