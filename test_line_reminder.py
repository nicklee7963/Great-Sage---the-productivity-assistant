"""
Line Bot 行事曆提醒 - 測試腳本

此腳本可以測試 Line Bot 連接和提醒功能
"""

import json
import os
from pathlib import Path
from line_reminder import LineReminderManager

def test_line_reminder():
    """測試 Line Bot 連接"""
    
    # 讀取設定
    settings_file = Path(__file__).parent / 'pet_settings.json'
    
    if not settings_file.exists():
        print("❌ pet_settings.json 不存在")
        return
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ 讀取設定失敗: {e}")
        return
    
    token = settings.get('line_channel_access_token')
    user_id = settings.get('line_user_id')
    
    if not token:
        print("❌ 缺少 line_channel_access_token")
        print("   請在 pet_settings.json 中設定此欄位")
        return
    
    if not user_id:
        print("❌ 缺少 line_user_id")
        print("   請在 pet_settings.json 中設定此欄位")
        return
    
    print("✓ 設定已載入")
    print(f"  • Token: {token[:20]}...{token[-10:]}")
    print(f"  • User ID: {user_id}")
    
    # 建立管理器
    manager = LineReminderManager(token, user_id)
    
    # 測試發送訊息
    print("\n📤 嘗試發送測試訊息...")
    success = manager._send_line_message("🎓 大賢者 Line Bot 測試成功！")
    
    if success:
        print("✅ 測試訊息已發送！")
        print("\n提示：")
        print("  • 如果你有收到訊息，代表設定正確 ✓")
        print("  • 可以安全地啟動 python pet.py")
        print("  • Line 提醒會在行事曆事件前 5 分鐘自動發送")
    else:
        print("❌ 訊息發送失敗")
        print("\n可能的原因：")
        print("  1. Channel Access Token 不正確或已過期")
        print("  2. User ID 不正確")
        print("  3. 網際網路連接異常")
        print("\n請檢查 pet_settings.json 中的設定")

if __name__ == '__main__':
    print("=" * 50)
    print("   🎓 大賢者 - Line Bot 連接測試")
    print("=" * 50 + "\n")
    
    test_line_reminder()
    
    print("\n" + "=" * 50)
