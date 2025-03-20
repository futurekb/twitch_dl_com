import json
import requests
import os
import time
from datetime import datetime, timedelta

class TwitchAuth:
    def __init__(self, cache_file='config/token_cache.json'):
        self.cache_file = cache_file
        self.settings_file = 'config/settings.json'
        self._ensure_config_exists()
        self._check_and_initialize_settings()
        self.client_id, self.client_secret = self._load_credentials()
        self._cached_token = None
        self._load_cached_token()

    def _ensure_config_exists(self):
        if not os.path.exists(self.settings_file):
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            default_settings = {
                'twitch': {
                    'client_id': '',
                    'client_secret': '',
                    '_comment': 'Twitchの開発者ポータル（https://dev.twitch.tv/console）でアプリケーションを作成し、Client IDとClient Secretを取得してください。'
                }
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=2, ensure_ascii=False)

    def _check_and_initialize_settings(self):
        with open(self.settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            if not settings.get('twitch', {}).get('client_id') or not settings.get('twitch', {}).get('client_secret'):
                raise ValueError(
                    f"Twitchの認証情報が設定されていません。\n"
                    f"以下の手順で設定してください：\n"
                    f"1. https://dev.twitch.tv/console にアクセス\n"
                    f"2. アプリケーションを作成\n"
                    f"3. 取得したClient IDとClient Secretを{self.settings_file}に設定\n"
                )

    def _load_credentials(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                twitch_settings = settings.get('twitch', {})
                client_id = twitch_settings.get('client_id')
                client_secret = twitch_settings.get('client_secret')
                
                if not client_id or not client_secret:
                    raise ValueError("client_idまたはclient_secretが設定されていません")
                    
                return client_id, client_secret
        except json.JSONDecodeError:
            raise Exception(f"設定ファイル {self.settings_file} の形式が不正です")
        except Exception as e:
            raise Exception(f"設定ファイルの読み込みに失敗しました: {str(e)}")

    def _load_cached_token(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self._cached_token = json.load(f)

    def _save_token_to_cache(self, token, expires_in):
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        cache_data = {
            'access_token': token,
            'expires_at': expires_at.timestamp()
        }
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)
        self.token = token
        self.expires_at = expires_at.timestamp()

    def _validate_cached_token(self):
        if not self._cached_token:
            return False
        
        if 'timestamp' not in self._cached_token:
            return False
            
        expiration_time = self._cached_token['timestamp'] + 14400  # 4時間
        return time.time() < expiration_time and 'access_token' in self._cached_token

    def get_oauth_token(self) -> str:
        if self._validate_cached_token():
            return self._cached_token['access_token']

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Client-ID': self.client_id
        }
        
        try:
            response = requests.post(
                'https://id.twitch.tv/oauth2/token',
                data=data,
                headers=headers
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._cached_token = {
                'access_token': token_data['access_token'],
                'timestamp': time.time()
            }
            
            # キャッシュを保存
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self._cached_token, f)
            
            return self._cached_token['access_token']
            
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to get OAuth token: {str(e)}"
            if response is not None:
                error_message += f"\nStatus: {response.status_code}"
                try:
                    error_message += f"\nResponse: {response.json()}"
                except ValueError:
                    error_message += f"\nResponse: {response.text}"
            raise Exception(error_message)

if __name__ == '__main__':
    try:
        auth = TwitchAuth()
        token = auth.get_oauth_token()
        print(f"Access token obtained: {token}")
    except Exception as e:
        print(f"Error: {e}")
