from typing import List, Dict, Optional
import requests
import json
from .tw_auth import TwitchAuth
from .database.db_manager import DatabaseManager

class TwitchAPI:
    def __init__(self):
        self.auth = TwitchAuth()
        self.base_url = "https://api.twitch.tv/helix"
        self.client_id, _ = self.auth._load_credentials()
        self.load_registered_users()
        self.db = DatabaseManager()

    def _get_headers(self):
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
        
        response = requests.get(
            f"{self.base_url}/users",
            headers=self._get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()['data']
        return []  # エラー時は空リストを返す

    def get_streams(self, user_ids: List[str]) -> List[Dict]:
        """配信状態を取得"""
        params = {'user_id': user_ids}
        response = requests.get(
            f"{self.base_url}/streams",
            headers=self._get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()['data']
        raise Exception(f"Failed to get streams: {response.status_code}")

    def get_game(self, game_id: str) -> Optional[Dict]:
        """ゲーム情報を取得"""
        if not game_id:
            return None
        
        params = {'id': [game_id]}
        response = requests.get(
            f"{self.base_url}/games",
            headers=self._get_headers(),
            params=params
        )
        if response.status_code == 200:
            data = response.json()['data']
            return data[0] if data else None
        return None

    def get_videos(self, user_id: str, first: int = 20) -> List[Dict]:
        """過去の配信動画を取得"""
        params = {
            'user_id': user_id,
            'first': first,
            'type': 'archive'
        }
        response = requests.get(
            f"{self.base_url}/videos",
            headers=self._get_headers(),
            params=params
        )
        if response.status_code == 200:
            videos = response.json()['data']
            # 各動画にゲーム名を追加
            for video in videos:
                game = self.get_game(video.get('game_id'))
                video['game_name'] = game['name'] if game else ''
            return videos
        raise Exception(f"Failed to get videos: {response.status_code}")

    def search_channels(self, query: str) -> list:
        url = 'https://api.twitch.tv/helix/search/channels'
        params = {'query': query, 'first': 10}
        
        response = requests.get(
            url,
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
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
