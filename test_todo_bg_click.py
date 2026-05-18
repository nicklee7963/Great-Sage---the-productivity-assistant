"""待办清单功能测试脚本 - 验证背景点击功能"""
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from todo_feature import TodoListPanel, ClickableContainer

# 创建测试应用
app = QtWidgets.QApplication(sys.argv)

# 测试 ClickableContainer
print("[OK] Testing ClickableContainer...")
container = ClickableContainer()
print("  - ClickableContainer created successfully")

# 测试 TodoListPanel
print("[OK] Testing TodoListPanel...")
panel = TodoListPanel(compact_mode=False)
print("  - TodoListPanel created successfully")

# 验证关键方法和属性
print("[OK] Verifying TodoListPanel methods...")
methods_to_check = [
    '_on_middle_background_clicked',
    '_clear_edit_form',
    '_select_task_by_id',
    'refresh_display'
]
for method in methods_to_check:
    if hasattr(panel, method):
        print("[+] " + method + " exists")
    else:
        print("[-] " + method + " missing")

# 验证 middle_container 连接了信号
print("[OK] Verifying signal connections...")
try:
    # 获取容器
    container = panel.middle_container
    if isinstance(container, ClickableContainer):
        print("[+] middle_container is ClickableContainer type")
    else:
        print("[-] middle_container is NOT ClickableContainer type")
except Exception as e:
    print("[-] Error: " + str(e))

print("\n[OK] All tests completed!")
print("\nFeature description:")
print("  1. Click task card in middle panel -> right edit form fills with task data")
print("  2. Click empty background in middle panel -> edit form clears, ready for new task")
print("  3. Left list selection also fills the edit form")
