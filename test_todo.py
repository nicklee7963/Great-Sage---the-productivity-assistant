"""待办清单功能测试脚本"""
import os
import json
from todo_feature import TodoListPanel

# 创建测试数据
test_tasks = [
    {
        'id': '1',
        'name': '完成项目报告',
        'type': 'urgent',
        'status': 'pending',
        'description': '需要完成Q1项目的详细报告',
        'created_date': '2026-05-18T10:00:00',
        'completed_date': None,
    },
    {
        'id': '2',
        'name': '日常代码审查',
        'type': 'routine',
        'status': 'in_progress',
        'description': '审查今天提交的代码',
        'created_date': '2026-05-18T09:00:00',
        'completed_date': None,
    },
    {
        'id': '3',
        'name': '修复登录bug',
        'type': 'urgent',
        'status': 'pending',
        'description': '用户反馈的登录页面崩溃问题',
        'created_date': '2026-05-18T11:00:00',
        'completed_date': None,
    },
    {
        'id': '4',
        'name': '更新文档',
        'type': 'routine',
        'status': 'completed',
        'description': '更新API文档',
        'created_date': '2026-05-17T14:00:00',
        'completed_date': '2026-05-18T15:00:00',
    },
]

# 测试数据保存
test_file = os.path.join(os.path.dirname(__file__), 'todo_records.json')
try:
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_tasks, f, ensure_ascii=False, indent=2)
    print(f"✓ 测试数据已保存到 {test_file}")
except Exception as e:
    print(f"✗ 保存测试数据失败: {e}")

# 测试数据加载
try:
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded_tasks = json.load(f)
    print(f"✓ 成功加载 {len(loaded_tasks)} 个测试任务")
    for task in loaded_tasks:
        print(f"  - [{task['type']}][{task['status']}] {task['name']}")
except Exception as e:
    print(f"✗ 加载测试数据失败: {e}")

# 验证常数
print(f"\n✓ TodoListPanel 常数验证:")
print(f"  - 支持的状态: {list(TodoListPanel.STATUS_NAMES.keys())}")
print(f"  - 支持的类型: {list(TodoListPanel.TYPE_NAMES.keys())}")
print(f"  - 状态颜色: {len(TodoListPanel.STATUS_COLORS)} 种")

print("\n✓ 待办清单功能模块测试完成！")
