"""時間フォーマッターユーティリティ"""

from datetime import datetime, timezone
from typing import Optional
import re
from ..constants import (
    TIME_FORMAT_ISO, TIME_FORMAT_DISPLAY, TIME_FORMAT_FILE,
    TIME_JUST_NOW, TIME_MINUTES_AGO, TIME_HOURS_AGO, TIME_DAYS_AGO
)


class TimeFormatter:
    """時間関連のフォーマット処理を行うユーティリティクラス"""
    
    @staticmethod
    def parse_iso_time(time_str: str) -> Optional[datetime]:
        """ISO形式の時間文字列をdatetimeオブジェクトに変換"""
        if not time_str:
            return None
            
        try:
            # タイムゾーン情報を含む場合と含まない場合の両方に対応
            if time_str.endswith('Z'):
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(time_str)
        except ValueError:
            try:
                # 古い形式のフォールバック
                return datetime.strptime(time_str, TIME_FORMAT_ISO)
            except ValueError:
                return None
    
    @staticmethod
    def format_display_time(dt: datetime) -> str:
        """datetimeオブジェクトを表示用の文字列に変換"""
        if not dt:
            return ""
        return dt.strftime(TIME_FORMAT_DISPLAY)
    
    @staticmethod
    def format_file_time(dt: datetime) -> str:
        """datetimeオブジェクトをファイル名用の文字列に変換"""
        if not dt:
            return ""
        return dt.strftime(TIME_FORMAT_FILE)
    
    @staticmethod
    def get_relative_time(dt: datetime) -> str:
        """相対的な時間表現を取得（例: 5分前、2時間前）"""
        if not dt:
            return ""
            
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        diff = now - dt
        
        # 秒数で計算
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return TIME_JUST_NOW
        elif seconds < 3600:  # 1時間未満
            minutes = int(seconds / 60)
            return TIME_MINUTES_AGO.format(minutes=minutes)
        elif seconds < 86400:  # 1日未満
            hours = int(seconds / 3600)
            return TIME_HOURS_AGO.format(hours=hours)
        else:
            days = int(seconds / 86400)
            return TIME_DAYS_AGO.format(days=days)
    
    @staticmethod
    def parse_duration(duration_str: str) -> int:
        """時間文字列を秒数に変換（例: "1h30m45s" -> 5445）"""
        if not duration_str:
            return 0
            
        # ISO 8601形式の場合
        if duration_str.startswith('PT'):
            duration_str = duration_str[2:]
            
        total_seconds = 0
        
        # 時間のパターンマッチング
        patterns = [
            (r'(\d+)h', 3600),  # 時間
            (r'(\d+)m', 60),    # 分
            (r'(\d+)s', 1)      # 秒
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, duration_str, re.IGNORECASE)
            if match:
                total_seconds += int(match.group(1)) * multiplier
        
        return total_seconds
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """秒数を時間文字列に変換（例: 5445 -> "1:30:45"）"""
        if seconds <= 0:
            return "0:00"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def format_duration_from_str(duration_str: str) -> str:
        """時間文字列を別の形式に変換（例: "1h30m45s" -> "1:30:45"）"""
        seconds = TimeFormatter.parse_duration(duration_str)
        return TimeFormatter.format_duration(seconds)