# Twitch DL Com

Twitchのクリップやアーカイブ動画をダウンロードするためのPythonツール

## 機能

- Twitchクリップのダウンロード
- アーカイブ動画(VOD)のダウンロード
- ダウンロード済みファイルのスキップ機能
- 並列ダウンロード対応

## 必要要件

- Python 3.8以上
- pip

## インストール方法

```bash
git clone https://github.com/yourusername/twitch_dl_com.git
cd twitch_dl_com
pip install -r requirements.txt
```

## 使用方法

### クリップのダウンロード

```bash
source ~/venv/twitch/bin/activate
python twitch_dl.py clip <clip_url>
```

### VODのダウンロード

```bash
python twitch_dl.py vod <vod_url>
```

### オプション

- `-o, --output`: 出力ディレクトリを指定
- `-q, --quality`: 動画品質を指定 (best, 720p, 480p, etc.)
- `-t, --threads`: 並列ダウンロード数を指定

## ライセンス

MIT License

## 作者

futurekb
