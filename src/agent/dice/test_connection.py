#!/usr/bin/env python3
"""
测试新的数据库连接方式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice.model import DataContainer, GroupLOG, ChineseName, COCPlayer

def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")

    try:
        # 创建 DataContainer 实例
        container = DataContainer()

        print("数据库配置信息:")
        print(f"  HOST: {container.host}")
        print(f"  USER: {container.user}")
        print(f"  DB_NAME: {container.db}")
        print(f"  PORT: {container.port}")

        # 测试简单的查询
        print("\n测试查询...")
        test_query = "SELECT 1 as test_result"
        result_json = container._execute_query(test_query)
        print(f"查询结果: {result_json}")

        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_data_structures():
    """测试数据结构"""
    print("\n测试数据结构...")

    # 测试 GroupLOG
    group_log = GroupLOG(123456, True, "test message")
    print(f"GroupLOG: group_id={group_log.group_id}, log={group_log.log}, msg={group_log.msg}")

    # 测试 ChineseName
    chinese_name = ChineseName("001", "张三")
    print(f"ChineseName: id={chinese_name.id}, name={chinese_name.name}")

    # 测试 COCPlayer
    player = COCPlayer("user_001", name="测试玩家", age=25)
    print(f"COCPlayer: id={player.id}, name={player.name}, age={player.age}")

    return True

if __name__ == "__main__":
    print("开始测试新的数据库连接方式")
    print("=" * 50)

    # 测试数据结构
    test_data_structures()

    print("\n" + "=" * 50)

    # 测试数据库连接
    if test_database_connection():
        print("\n✅ 测试成功！数据库连接已改造完成")
    else:
        print("\n❌ 测试失败！请检查配置和错误信息")