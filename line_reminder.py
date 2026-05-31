"""
大賢者（Great Sage）- Line Bot 行事曆提醒模組

本模組提供 Line Bot 行事曆提醒功能：
  • 監控 calendar_events.json 中的事件
  • 在事件開始前 5 分鐘透過 Line 發送提醒
  • 後台執行緒避免阻擋主程式
  • 智慧去重複提醒（同一事件只提醒一次）
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


class LineReminderManager:
    """Line Bot 行事曆提醒管理器"""
    
    REMINDER_ADVANCE_SECONDS = 5 * 60  # 前 5 分鐘提醒
    CHECK_INTERVAL_SECONDS = 30        # 每 30 秒檢查一次
    
    def __init__(self, channel_access_token, user_id, base_dir=None):
        """
        初始化 Line 提醒管理器
        
        Args:
            channel_access_token: Line Channel Access Token
            user_id: Line User ID (要接收提醒的用戶)
            base_dir: 專案根目錄（用於讀取 calendar_events.json）
        """
        self.channel_access_token = channel_access_token
        self.user_id = user_id
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.calendar_file = self.base_dir / 'calendar_events.json'
        self.line_api_url = 'https://api.line.me/v2/bot/message/push'
        
        # 已發送過提醒的事件記錄 (用來避免重複提醒)
        # 格式: {date: {time: task}}
        self.reminded_events = {}
        
        self.is_running = False
        self.reminder_thread = None
    
    def _load_calendar_events(self):
        """載入行事曆事件"""
        try:
            if self.calendar_file.exists():
                with open(self.calendar_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Line Reminder] 載入行事曆失敗: {e}")
        return {}
    
    def _send_line_message(self, message_text):
        """透過 Line Bot 發送訊息"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.channel_access_token}'
            }
            
            payload = {
                'to': self.user_id,
                'messages': [
                    {
                        'type': 'text',
                        'text': message_text
                    }
                ]
            }
            
            response = requests.post(
                self.line_api_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[Line Reminder ✓] 提醒已發送: {message_text}")
                return True
            else:
                print(f"[Line Reminder ✗] 發送失敗 ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"[Line Reminder ✗] 發送異常: {e}")
            return False
    
    def _check_reminders(self):
        """檢查需要發送的提醒"""
        events = self._load_calendar_events()
        if not events:
            return
        
        now = datetime.now()
        today = now.date()
        
        # 檢查今天和明天的事件
        for target_date in [today, today + timedelta(days=1)]:
            date_str = target_date.isoformat()
            if date_str not in events:
                continue
            
            # 初始化該日期的提醒記錄
            if date_str not in self.reminded_events:
                self.reminded_events[date_str] = set()
            
            for event in events[date_str]:
                time_str = event.get('time', '')
                task = event.get('task', '')
                
                if not time_str or not task:
                    continue
                
                # 建立事件唯一識別符
                event_key = f"{time_str}_{task}"
                
                # 檢查是否已提醒過
                if event_key in self.reminded_events[date_str]:
                    continue
                
                try:
                    # 解析事件時間
                    event_time = datetime.combine(
                        target_date,
                        datetime.strptime(time_str, '%H:%M').time()
                    )
                    
                    # 計算提醒時間（事件前 5 分鐘）
                    remind_time = event_time - timedelta(seconds=self.REMINDER_ADVANCE_SECONDS)
                    
                    # 檢查是否在提醒時間範圍內
                    time_until_remind = (remind_time - now).total_seconds()
                    
                    # 如果在提醒時間 (前 30 秒內)，則發送提醒
                    if 0 <= time_until_remind <= self.CHECK_INTERVAL_SECONDS:
                        message = f"⏰ 5分鐘後你有「{task}」 ({time_str})"
                        if self._send_line_message(message):
                            self.reminded_events[date_str].add(event_key)
                
                except ValueError:
                    # 時間格式不正確
                    continue
    
    def start(self):
        """啟動提醒監控執行緒"""
        if self.is_running:
            print("[Line Reminder] 提醒監控已在運行中")
            return
        
        self.is_running = True
        self.reminder_thread = threading.Thread(
            target=self._reminder_loop,
            daemon=True,
            name='LineReminderThread'
        )
        self.reminder_thread.start()
        print("[Line Reminder] 啟動行事曆提醒監控")
    
    def stop(self):
        """停止提醒監控執行緒"""
        self.is_running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=2)
        print("[Line Reminder] 停止提醒監控")
    
    def _reminder_loop(self):
        """提醒檢查迴圈"""
        while self.is_running:
            try:
                self._check_reminders()
            except Exception as e:
                print(f"[Line Reminder] 檢查異常: {e}")
            
            # 每 30 秒檢查一次
            time.sleep(self.CHECK_INTERVAL_SECONDS)


def create_line_reminder(channel_access_token, user_id, base_dir=None):
    """
    建立並啟動 Line 提醒管理器
    
    Args:
        channel_access_token: Line Channel Access Token
        user_id: Line User ID
        base_dir: 專案根目錄
    
    Returns:
        LineReminderManager 實例
    """
    manager = LineReminderManager(
        channel_access_token=channel_access_token,
        user_id=user_id,
        base_dir=base_dir
    )
    return manager


if __name__ == '__main__':
    # 測試用
    import sys
    
    if len(sys.argv) != 3:
        print("用法: python line_reminder.py <channel_access_token> <user_id>")
        sys.exit(1)
    
    token = sys.argv[1]
    uid = sys.argv[2]
    
    manager = create_line_reminder(token, uid)
    manager.start()
    
    try:
        print("Line 提醒監控運行中... (按 Ctrl+C 停止)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
        print("已停止")
