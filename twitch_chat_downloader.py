import argparse
import os
import time
import glob
import subprocess
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException

def is_button_truly_clickable(button_element):
    """ボタンが本当にクリック可能かどうかをさらに厳密に確認する関数"""
    try:
        # disabledかどうかチェック
        if button_element.get_attribute("disabled"):
            return False
            
        # aria-disabledの確認
        if button_element.get_attribute("aria-disabled") == "true":
            return False
            
        # classにdisabledが含まれているか確認
        class_value = button_element.get_attribute("class") or ""
        if "disabled" in class_value:
            return False
            
        # スタイルで無効化されているか確認
        style = button_element.get_attribute("style") or ""
        if "pointer-events: none" in style or "opacity: 0.5" in style:
            return False
            
        # 表示されているか確認
        if not button_element.is_displayed():
            return False
            
        return True
    except StaleElementReferenceException:
        # 要素が更新された場合
        return False

def open_folder(path):
    """ダウンロードフォルダを開く関数"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            try:
                # Chromiumでフォルダを開く
                subprocess.run(['chromium-browser', f'file://{path}'], check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # 代替手段としてnautilusを試す
                    subprocess.run(['nautilus', path], check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        # さらに代替手段としてxdg-openを試す
                        subprocess.run(['xdg-open', path], check=True)
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print(f"フォルダを開けません: {path}")
                        print(f"手動でChromiumを開き、以下のURLを入力してください: file://{path}")
                        return False
    except Exception as e:
        print(f"エラー: {e}")
        return False
    return True

# def copy_to_windows(src_path):
#     """Linuxの仮想環境からWindowsのローカル環境にファイルをコピーする関数"""
#     try:
#         # Windowsのダウンロードフォルダのパス
#         windows_path = "/mnt/c/Users/futur/Downloads/TwitchComment"
        
#         # Windowsのフォルダを作成
#         os.makedirs(windows_path, exist_ok=True)
        
#         # ファイルをコピー
#         for file in glob.glob(os.path.join(src_path, "*.csv")):
#             filename = os.path.basename(file)
#             # コロン(:)をアンダースコア(_)に置換
#             safe_filename = filename.replace(":", "_")
#             dst_file = os.path.join(windows_path, safe_filename)
            
#             try:
#                 # ファイルの存在確認
#                 if os.path.exists(file):
#                     subprocess.run(['cp', '-f', file, dst_file], check=True)
#                     print(f"ファイルをコピーしました: {dst_file}")
#                 else:
#                     print(f"元ファイルが見つかりません: {file}")
#                     continue
#             except subprocess.CalledProcessError as e:
#                 print(f"ファイルコピー中にエラーが発生: {e}")
#                 continue
        
#         return windows_path
#     except Exception as e:
#         print(f"Windowsへのコピーに失敗しました: {e}")
#         return None

def copy_to_windows(src_path):
    """Linuxの仮想環境からWindowsのローカル環境にファイルをコピーする関数"""
    try:
        # Windowsのダウンロードフォルダのパス
        windows_path = f"/mnt/c/Users/futur/Downloads/TwitchComment"
        
        # Windowsのフォルダを作成
        os.makedirs(windows_path, exist_ok=True)
        
        # ファイルをコピー
        for file in glob.glob(os.path.join(src_path, "*.csv")):
            filename = os.path.basename(file)
            dst_file = os.path.join(windows_path, filename)
            subprocess.run(['cp', file, dst_file], check=True)
            print(f"ファイルをコピーしました: {dst_file}")
        
        return windows_path
    except Exception as e:
        print(f"Windowsへのコピーに失敗しました: {e}")
        return None

def sanitize_filename(filename):
    """ファイル名から不正な文字を除去"""
    # Windowsで使用できない文字を置換
    filename = re.sub(r'[<>"/\\|?*]', '_', filename)
    # コロン(:)を別途処理
    filename = filename.replace(':', '_')
    # 文字数制限（255文字以内）
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        filename = base[:255-len(ext)] + ext
    return filename

def rename_chat_file(download_path, new_filename):
    """ダウンロードしたCSVファイルの名前を変更"""
    try:
        # 最新のCSVファイルを検索
        csv_files = glob.glob(os.path.join(download_path, "*.csv"))
        if not csv_files:
            print("CSVファイルが見つかりません")
            return None

        newest_file = max(csv_files, key=os.path.getctime)
        # TODO: ファイル名変換がおかしい。sanitize_filename
        new_filepath = os.path.join(download_path, sanitize_filename(new_filename))
        
        # ファイルが既に存在する場合は、連番を付与
        counter = 1
        base, ext = os.path.splitext(new_filepath)
        while os.path.exists(new_filepath):
            new_filepath = f"{base}_{counter}{ext}"
            counter += 1

        os.rename(newest_file, new_filepath)
        print(f"ファイル名を変更しました: {new_filepath}")
        return new_filepath
    except Exception as e:
        print(f"ファイル名の変更に失敗しました: {e}")
        return None

def main(video_url, output_filename=None):
    # ダウンロードパスの設定
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'TwitchComment')
    os.makedirs(download_path, exist_ok=True)
    print(f"ダウンロード先: {download_path}")

    # 既存のCSVファイルをクリア
    existing_files = glob.glob(os.path.join(download_path, "*.*"))
    for file in existing_files:
        try:
            os.remove(file)
            print(f"既存のファイルを削除しました: {file}")
        except Exception as e:
            print(f"ファイルの削除に失敗しました: {e}")

    # ブラウザオプションの設定
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # ヘッドレスモードを有効化
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option('prefs', {
        'download.default_directory': download_path,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True,
        'download.default_directory.conflict_policy': 'overwrite'
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.twitchchatdownloader.com")

    try:
        url_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "video-url"))
        )
        url_input.clear()  # 既存の入力をクリア
        url_input.send_keys(video_url)
        print(f"URL: {video_url}")

        # 1. 最初のボタンをクリック
        first_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(@title, 'Download chat')]"))
        )
        first_button.click()
        print("ダウンロード")
        
        # 2. 次のボタンが表示されるのを待つ
        next_button_locator = (By.XPATH, "//button[contains(@class, 'btn-primary') and @title='Export chat']")
        
        next_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(next_button_locator)
        )        
        
        # Progressが100%になるまで待機
        progress_locator = (By.XPATH, "//small[contains(@class, 'd-block') and contains(text(), 'Progress:')]")
        max_wait_time = 30  # 最大待機時間（秒）
        wait_interval = 0.5  # 確認間隔（秒）
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                progress_element = driver.find_element(*progress_locator)
                progress_text = progress_element.text.strip()
                if 'Progress: 100 % | Remaining: 0 sec' in progress_text:
                    print("ダウンロード処理が完了しました")
                    break
                print(f"ダウンロード進捗: {progress_text}")
                time.sleep(wait_interval)
            except Exception as e:
                print(f"進捗の確認中にエラー: {e}")
                time.sleep(wait_interval)
        else:
            print("進捗の確認がタイムアウトしました")
            
        # 3. カスタム待機: ボタンが本当にクリック可能になるまで待機
        max_wait_time = 5  # 最大待機時間（秒）
        wait_interval = 0.5  # 確認間隔（秒）
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 要素を再取得
                next_button = driver.find_element(*next_button_locator)
                print("next_button")

                # ボタンの状態をより詳細にチェック
                if (next_button.is_displayed() and 
                    next_button.is_enabled() and 
                    "disabled" not in next_button.get_attribute("class") and 
                    not next_button.get_attribute("disabled")):

                    # 少し待機を入れて安定させる
                    time.sleep(2)
                    break
                    
            except StaleElementReferenceException:
                print("要素が更新されました。再取得を試みます...")
                continue
                
            # 待機
            time.sleep(wait_interval)
        else:
            # whileループが正常終了しなかった場合（タイムアウト）
            raise TimeoutException("対象ビデオのダウンロード操作がタイムアウトになりました")
        
        # 4. 安全なクリック試行
        try:
            print("エクスポート")
            next_button.click()
            # ダウンロードの完了を待機
            timeout = 60  # タイムアウト時間（秒）
            start_time = time.time()

            print(f"DL開始日時: {start_time}")
            while time.time() - start_time < timeout:
                print(f"経過: {time.time()}")  # パスを確認するために追加

                # 新しいCSVファイルを検索
                csv_files = glob.glob(os.path.join(download_path, "*.csv"))
                newest_file = max(csv_files, key=os.path.getctime) if csv_files else None
                
                if newest_file and os.path.getsize(newest_file) > 0:
                    print(f"ダウンロード完了: {newest_file}")
                    if output_filename:
                        renamed_file = rename_chat_file(download_path, output_filename)
                        if renamed_file:
                            try:
                                windows_path = copy_to_windows(download_path)
                                if windows_path:
                                    print(f"ファイルコピー: {windows_path}")
                            except Exception as e:
                                print(f"Windowsへのコピーに失敗しました: {e}")
                    break
                time.sleep(1)
            else:
                print("ダウンロードがタイムアウトしました")            
        except ElementClickInterceptedException:
            print("通常のクリックが失敗しました。JavaScriptでクリックを試みます...")
            driver.execute_script("arguments[0].click();", next_button)
            print("次のボタンをJavaScriptで押下しました")
    except TimeoutException as e:
        print(f"タイムアウトエラー: {e}")
        driver.save_screenshot("timeout_error.png")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        driver.save_screenshot("error.png")
        
    finally:
        # ブラウザを閉じる
        driver.quit()

def process_urls(urls):
    """URLのリストを順番に処理する関数"""
    success_count = 0
    total_count = len([url for url in urls if url.strip()])  # 空行を除いた総数

    for url in urls:
        url = url.strip()  # 空白と改行を削除
        if url:  # 空行でない場合のみ処理
            print(f"\n=== {url} の処理を開始 ({success_count + 1}/{total_count}) ===")
            try:
                main(url)
                success_count += 1
                print(f"=== {url} の処理が完了 ===\n")
            except Exception as e:
                print(f"=== {url} の処理中にエラーが発生: {e} ===\n")
            # 連続実行時の負荷軽減のため少し待機
            time.sleep(5)

    # すべての処理が完了した後にフォルダを開く
    if success_count > 0:
        print(f"\n=== 全 {total_count} 件中 {success_count} 件の処理が完了しました ===")
        try:
            windows_dl_path = "C:\\Users\\futur\\Downloads\\TwitchComment"
            subprocess.run(['explorer.exe', windows_dl_path])
            print(f"フォルダを開きました: {windows_dl_path}")
        except Exception as e:
            print(f"フォルダを開く際にエラーが発生しました: {e}")
            print(f"手動でフォルダを確認してください: {windows_dl_path}")
    else:
        print("\n=== 正常に処理できたURLがありませんでした ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TwitchチャットをCSVでダウンロードします')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', 
                      help='TwitchのビデオURL（例：https://www.twitch.tv/videos/123456789）')
    group.add_argument('-f', '--file',
                      help='URLリストが記載されたファイルのパス（1行1URL）')
    parser.add_argument('-o', '--output', help='出力ファイル名')
    args = parser.parse_args()
    
    if args.url:
        # 単一URLの処理
        main(args.url, args.output)
    else:
        # ファイルからURLを読み込んで処理
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                urls = f.readlines()
                process_urls(urls)
        except FileNotFoundError:
            print(f"ファイルが見つかりません: {args.file}")
        except Exception as e:
            print(f"ファイルの読み込み中にエラーが発生: {e}")