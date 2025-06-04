"""設定とファイル操作を管理するサービス"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..constants import (
    CONFIG_DIR, CACHE_DIR, SETTINGS_FILE, 
    REGISTERED_USERS_FILE, VIDEO_CACHE_PATTERN
)
import logging

logger = logging.getLogger(__name__)


class ConfigurationService:
    """設定ファイルとキャッシュファイルの管理を担当"""
    
    def __init__(self):
        self.config_dir = Path(CONFIG_DIR)
        self.cache_dir = Path.home() / CACHE_DIR
        self._ensure_directories()
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        self.config_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
    
    # 設定ファイル関連
    def load_settings(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        settings_path = self.config_dir / SETTINGS_FILE
        
        if not settings_path.exists():
            logger.warning("設定ファイルが存在しません。デフォルト設定を返します。")
            return self._get_default_settings()
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルの解析に失敗しました: {e}")
            return self._get_default_settings()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            return self._get_default_settings()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """設定ファイルを保存する"""
        settings_path = self.config_dir / SETTINGS_FILE
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            'twitch': {
                'client_id': '',
                'client_secret': '',
                '_comment': 'Twitchの開発者ポータル（https://dev.twitch.tv/console）でアプリケーションを作成し、Client IDとClient Secretを取得してください。'
            },
            'ui': {
                'sort_order': 'latest',
                'window_geometry': None
            }
        }
    
    # ユーザーリスト関連
    def load_registered_users(self) -> List[str]:
        """登録済みユーザーIDのリストを読み込む"""
        users_path = self.config_dir / REGISTERED_USERS_FILE
        
        if not users_path.exists():
            return []
        
        try:
            with open(users_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 後方互換性のため、リストまたは辞書形式の両方に対応
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return list(data.keys())
                else:
                    logger.warning("不正な形式の登録ユーザーファイル")
                    return []
        except Exception as e:
            logger.error(f"登録ユーザーファイルの読み込みに失敗しました: {e}")
            return []
    
    def save_registered_users(self, user_ids: List[str]) -> bool:
        """登録済みユーザーIDのリストを保存する"""
        users_path = self.config_dir / REGISTERED_USERS_FILE
        
        try:
            with open(users_path, 'w', encoding='utf-8') as f:
                json.dump(user_ids, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"登録ユーザーファイルの保存に失敗しました: {e}")
            return False
    
    # ビデオキャッシュ関連
    def load_video_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーの動画キャッシュを読み込む"""
        cache_file = self.cache_dir / VIDEO_CACHE_PATTERN.format(user_id=user_id)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"動画キャッシュの読み込みに失敗しました: {e}")
            return None
    
    def save_video_cache(self, user_id: str, data: Dict[str, Any]) -> bool:
        """ユーザーの動画キャッシュを保存する"""
        cache_file = self.cache_dir / VIDEO_CACHE_PATTERN.format(user_id=user_id)
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"動画キャッシュの保存に失敗しました: {e}")
            return False
    
    # ウィンドウ設定関連
    def load_window_geometry(self) -> Optional[Dict[str, int]]:
        """ウィンドウジオメトリを読み込む"""
        settings = self.load_settings()
        return settings.get('ui', {}).get('window_geometry')
    
    def save_window_geometry(self, geometry: Dict[str, int]) -> bool:
        """ウィンドウジオメトリを保存する"""
        settings = self.load_settings()
        
        if 'ui' not in settings:
            settings['ui'] = {}
        
        settings['ui']['window_geometry'] = geometry
        return self.save_settings(settings)
    
    # ソート設定関連
    def load_sort_order(self) -> str:
        """ソート順を読み込む"""
        settings = self.load_settings()
        return settings.get('ui', {}).get('sort_order', 'latest')
    
    def save_sort_order(self, sort_order: str) -> bool:
        """ソート順を保存する"""
        settings = self.load_settings()
        
        if 'ui' not in settings:
            settings['ui'] = {}
        
        settings['ui']['sort_order'] = sort_order
        return self.save_settings(settings)
    
    # ユーティリティメソッド
    def get_cache_dir(self) -> Path:
        """キャッシュディレクトリのパスを取得"""
        return self.cache_dir
    
    def get_config_dir(self) -> Path:
        """設定ディレクトリのパスを取得"""
        return self.config_dir
    
    def clear_video_cache(self, user_id: str = None) -> bool:
        """動画キャッシュをクリア"""
        try:
            if user_id:
                # 特定ユーザーのキャッシュをクリア
                cache_file = self.cache_dir / VIDEO_CACHE_PATTERN.format(user_id=user_id)
                if cache_file.exists():
                    cache_file.unlink()
            else:
                # 全てのキャッシュをクリア
                for cache_file in self.cache_dir.glob("videos_*.json"):
                    cache_file.unlink()
            return True
        except Exception as e:
            logger.error(f"キャッシュのクリアに失敗しました: {e}")
            return False