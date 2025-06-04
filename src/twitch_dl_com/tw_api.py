from typing import List, Dict, Optional
import requests
import json
import time
from .tw_auth import TwitchAuth
from .database.db_manager import DatabaseManager
from .exceptions import APIError, NetworkError, UserNotFoundError, VideoNotFoundError
from .constants import REQUEST_TIMEOUT, MAX_RETRY_COUNT, RETRY_DELAY
from .logger import logger

class TwitchAPI:
    def __init__(self):
        self.auth = TwitchAuth()
        self.base_url = "https://api.twitch.tv/helix"
        self.client_id, _ = self.auth._load_credentials()
        self.load_registered_users()
        self.db = DatabaseManager()

    def _get_headers(self) -> Dict[str, str]:
        """APIリクエスト用のヘッダーを取得"""
        return {
            'Authorization': f'Bearer {self.auth.get_oauth_token()}',
            'Client-Id': self.client_id
        }

    def load_registered_users(self):
        # 登録済みユーザをJSONファイルから読み込む
        self.registered_users = []
        try:
            with open('registered_users.json', 'r') as f:
                self.registered_users = json.load(f)
        except FileNotFoundError:
            pass

    def search_users(self, query: str) -> List[Dict]:
        return self.search_channels(query)

    def register_user(self, user_data: Dict) -> bool:
        try:
            # ユーザーデータを整形
            formatted_data = {
                'id': user_data['id'],
                'login': user_data['login'],
                'display_name': user_data['display_name'],
                'profile_image_url': user_data['profile_image_url']
            }
            return self.db.add_user(formatted_data)
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            return False

    def get_followed_users(self):
        # 登録済みユーザの情報を取得
        users = []
        for user_id in self.registered_users:
            user_info = self.get_user_info(user_id)
            stream_info = self.get_stream_info(user_id)
            videos = self.get_videos(user_id)
            
            user_data = {
                'id': user_id,
                'login': user_info['login'],
                'display_name': user_info['display_name'],
                'profile_image_url': user_info['profile_image_url'],
                'is_live': stream_info is not None
            }
            
            if stream_info:
                user_data.update({
                    'stream_title': stream_info['title'],
                    'game_name': stream_info['game_name']
                })
            elif videos:
                latest_video = videos[0]
                user_data.update({
                    'last_title': latest_video['title'],
                    'game_name': latest_video['game_name'],
                    'last_stream': latest_video['created_at']
                })
                
            users.append(user_data)
            
        return users

    def get_users(self, login_names: List[str]) -> List[Dict]:
        """ユーザー情報を取得"""
        # IDとログイン名の両方に対応
        if any(str(name).isdigit() for name in login_names):
            params = {'id': login_names}
        else:
            params = {'login': login_names}
        
        return self._make_request(
            'GET',
            f"{self.base_url}/users",
            params=params
        ).get('data', [])

    def get_streams(self, user_ids: List[str]) -> List[Dict]:
        """配信状態を取得"""
        params = {'user_id': user_ids}
        return self._make_request(
            'GET',
            f"{self.base_url}/streams",
            params=params
        ).get('data', [])

    def get_game(self, game_id: str) -> Optional[Dict]:
        """ゲーム情報を取得"""
        if not game_id:
            return None
        
        params = {'id': [game_id]}
        try:
            data = self._make_request(
                'GET',
                f"{self.base_url}/games",
                params=params
            ).get('data', [])
            return data[0] if data else None
        except Exception as e:
            logger.warning(f"ゲーム情報の取得に失敗: {e}")
            return None

    def get_videos(self, user_id: str, first: int = 20) -> List[Dict]:
        """過去の配信動画を取得"""
        params = {
            'user_id': user_id,
            'first': first,
            'type': 'archive'
        }
        
        videos = self._make_request(
            'GET',
            f"{self.base_url}/videos",
            params=params
        ).get('data', [])
        
        # 各動画にゲーム名を追加
        for video in videos:
            game = self.get_game(video.get('game_id'))
            video['game_name'] = game['name'] if game else ''
        
        return videos

    def search_channels(self, query: str) -> List[Dict]:
        """チャンネルを検索"""
        params = {'query': query, 'first': 10}
        
        data = self._make_request(
            'GET',
            f"{self.base_url}/search/channels",
            params=params
        )
        
        return [{
            'id': item['id'],
            'login': item['broadcaster_login'],
            'display_name': item['display_name'],
            'title': item['title'],
            'game_name': item['game_name'],
            'profile_image_url': item['thumbnail_url']
        } for item in data.get('data', [])]

    def get_user_details(self, user_id: str) -> Dict:
        """ユーザー詳細情報を取得（配信状態と最新動画を含む）"""
        users = self.get_users([user_id])
        if not users:
            return None
        user_info = users[0]
        stream_info = self.get_streams([user_id])
        videos = self.get_videos(user_id, first=1)
        
        return {
            'user': user_info,
            'stream': stream_info[0] if stream_info else None,
            'latest_video': videos[0] if videos else None
        }

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        try:
            return self.get_users([user_id])[0]
        except Exception:
            return None

    def get_stream_info(self, user_id: str) -> Optional[Dict]:
        try:
            streams = self.get_streams([user_id])
            return streams[0] if streams else None
        except Exception:
            return None

    def download_comments(self, video_id: str, progress_callback=None) -> List[Dict]:
        comments = []
        cursor = None
        total_comments = 0
        
        try:
            while True:
                params = {
                    'video_id': video_id,
                    'first': 100
                }
                if cursor:
                    params['after'] = cursor
                
                response = requests.get(
                    f"{self.base_url}/comments",
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get comments: {response.status_code}")
                
                data = response.json()
                comments.extend(data['comments'])
                total_comments = data['_total']
                
                if progress_callback:
                    progress = min(int(len(comments) / total_comments * 100), 100)
                    progress_callback(progress)
                
                if not data['_pagination'].get('cursor'):
                    break
                    
                cursor = data['_pagination']['cursor']
                
            return comments
            
        except Exception as e:
            raise Exception(f"コメントのダウンロードに失敗しました: {str(e)}")

    def get_users_details(self, user_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """複数のユーザー情報を一括で取得"""
        result = {}
        for user_id in user_ids:
            try:
                result[user_id] = self.get_user_details(user_id)
            except Exception as e:
                logger.error(f"ユーザー{user_id}の詳細情報取得エラー: {e}")
                result[user_id] = None
        return result
    
    def _make_request(self, method: str, url: str, params: Dict = None, 
                     json_data: Dict = None) -> Dict:
        """リトライロジック付きのAPIリクエストを実行"""
        for attempt in range(MAX_RETRY_COUNT):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_data,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 404:
                    raise APIError("Resource not found", status_code=404)
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"タイムアウト (試行 {attempt + 1}/{MAX_RETRY_COUNT}): {url}")
                if attempt < MAX_RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise NetworkError(f"APIリクエストがタイムアウトしました: {url}", retry_count=MAX_RETRY_COUNT)
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.info("認証トークンを再取得します")
                    self.auth._cached_token = None  # トークンキャッシュをクリア
                    if attempt < MAX_RETRY_COUNT - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                
                error_message = f"APIエラー: {e.response.status_code} - {e.response.text}"
                logger.error(error_message)
                raise APIError(error_message, status_code=e.response.status_code)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"APIリクエストエラー (試行 {attempt + 1}/{MAX_RETRY_COUNT}): {str(e)}")
                if attempt < MAX_RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise NetworkError(f"APIリクエストに失敗しました: {str(e)}", retry_count=MAX_RETRY_COUNT)
