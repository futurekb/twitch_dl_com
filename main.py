import requests
import time
import os
import re
import sys
import json
from PyQt6.QtWidgets import QApplication
from twitch_dl_com.ui.main_window import MainWindow

def download_twitch_chat_csv(video_url, output_path="chat.csv"):
    print(f"開始: URL = {video_url}")
    
    # セッションを作成
    session = requests.Session()
    
    # 1. "Download Chat" のリクエストを再現
    download_url = "https://www.twitchchatdownloader.com/"
    payload = {"video_url": video_url}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    try:
        video_id = re.search(r'/videos/(\d+)', video_url)
        if video_id:
            video_id = video_id.group(1)
            print(f"抽出したvideo_id: {video_id}")
    except AttributeError:
        raise ValueError("URLから動画IDを抽出できませんでした")
    
    response = session.post(download_url, json=payload, headers=headers)

    print(f"POSTレスポンス: status_code={response.status_code}")
    print(f"POSTレスポンス: body={response.text[:200]}")  # レスポンスの最初の200文字を表示

    if response.status_code != 200:
        raise Exception("Download Chatリクエストが失敗しました")
    
    polling_url = f"https://www.twitchchatdownloader.com/video/{video_id}"

    # 2. ジョブの状態をポーリング
    status_url = polling_url
    max_retries = 10  # 最大リトライ回数
    retry_count = 0

    while retry_count < max_retries:
        try:
            status_response = session.get(status_url)
            print(f"ステータスチェック: status_code={status_response.status_code}")
            print(f"レスポンス内容: {status_response.text[:200]}")
            
            status = status_response.json().get("status")
            print(f"現在のステータス: {status}")
            
        except requests.exceptions.RequestException as e:
            print(f"リクエストエラー: {e}")
            time.sleep(5)
            retry_count += 1
            continue
        except json.JSONDecodeError as e:
            print(f"JSONパースエラー: {e}")
            print(f"受信データ: {status_response.text}")
            time.sleep(5)
            retry_count += 1
            continue
    
    # 3. CSVをダウンロード
    csv_response = session.get(csv_url)
    if csv_response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(csv_response.content)
        print(f"CSVを {output_path} に保存しました")
    else:
        raise Exception("CSVのダウンロードに失敗しました")

def main():
    # Force Qt to use X11 instead of Wayland
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()