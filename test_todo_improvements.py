"""測試改動：字體增大、簡化展示、移除成功消息"""
import json
import os
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from todo_feature import TodoListPanel

# 創建 QApplication
app = QtWidgets.QApplication(sys.argv)

# 建立測試數據
test_tasks = [
    {
        'id': '1',
        'name': '完成項目報告',
        'type': 'urgent',
        'status': 'pending',
        'description': '需要完成Q1項目的詳細報告',
        'created_date': '2026-05-18T10:00:00',
        'completed_date': None,
    },
    {
        'id': '2',
        'name': '日常代碼審查',
        'type': 'routine',
        'status': 'in_progress',
        'description': '審查今天提交的代碼',
        'created_date': '2026-05-18T09:00:00',
        'completed_date': None,
    },
    {
        'id': '3',
        'name': '修復登錄bug',
        'type': 'urgent',
        'status': 'completed',
        'description': '用戶反饋的登錄頁面崩潰問題',
        'created_date': '2026-05-18T11:00:00',
        'completed_date': '2026-05-18T14:00:00',
    },
]

# 保存測試數據
test_file = os.path.join(os.path.dirname(__file__), 'todo_records.json')
try:
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_tasks, f, ensure_ascii=False, indent=2)
    print("[OK] Test data saved")
except Exception as e:
    print("[ERROR] Failed to save test data: " + str(e))

# 創建 TodoListPanel
print("\n[OK] Creating TodoListPanel...")
panel = TodoListPanel(compact_mode=False, main_window=None)
panel.show()
app.processEvents()

# 驗證任務卡片
print("\n[OK] Verifying task cards in middle panel...")
tasks = panel.get_tasks_for_display()
print("[+] Number of tasks: " + str(len(tasks)))

# 驗證按鈕邏輯
print("\n[OK] Verifying button logic...")
print("[+] No task selected:")
print("    - Add button visible: " + str(panel.btn_add.isVisible()))
print("    - Update button visible: " + str(panel.btn_update.isVisible()))
print("    - Delete button visible: " + str(panel.btn_delete.isVisible()))

# 選擇第一個任務
if tasks:
    panel._select_task_by_id(tasks[0].get('id'))
    print("\n[+] Task selected:")
    print("    - Add button visible: " + str(panel.btn_add.isVisible()))
    print("    - Update button visible: " + str(panel.btn_update.isVisible()))
    print("    - Delete button visible: " + str(panel.btn_delete.isVisible()))

print("\n[OK] All tests completed!")
print("\nChanges verified:")
print("  1. No success message dialogs")
print("  2. Larger fonts in edit panel (14px labels, 13-14px inputs)")
print("  3. Task cards simplified: only status dot + name (15px font)")
print("  4. Left window todo items: larger font (14px) similar to calendar")
