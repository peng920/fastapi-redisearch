#!/usr/bin/env python3
"""
测试向量搜索API的示例脚本
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("🏥 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def create_test_documents():
    """创建测试文档"""
    print("📝 创建测试文档...")

    test_docs = [
        "人工智能是计算机科学的一个分支，致力于创建智能机器。",
        "机器学习是人工智能的一个子领域，使计算机能够学习。",
        "深度学习使用神经网络来模拟人脑的工作方式。",
        "自然语言处理帮助计算机理解人类语言。",
        "计算机视觉使机器能够解释和理解视觉信息。",
        "Python是一种流行的编程语言，广泛用于数据科学。",
        "JavaScript是Web开发的主要编程语言。",
        "数据科学使用统计学和机器学习来分析数据。"
    ]

    created_ids = []

    for i, content in enumerate(test_docs):
        doc_data = {"content": content}
        response = requests.post(f"{BASE_URL}/documents/", json=doc_data)

        if response.status_code == 201:
            doc_id = response.json()["id"]
            created_ids.append(doc_id)
            print(f"✅ 创建文档 {i+1}: {doc_id}")
        else:
            print(f"❌ 创建文档失败: {response.status_code} - {response.text}")

    print(f"✅ 成功创建 {len(created_ids)} 个文档")
    print()
    return created_ids


def test_search():
    """测试搜索功能"""
    print("🔍 测试搜索功能...")

    search_queries = [
        "机器学习算法",
        "编程语言",
        "数据分析和统计",
        "神经网络和AI"
    ]

    for query in search_queries:
        print(f"\n🔎 搜索: '{query}'")
        search_data = {"query": query, "limit": 3}

        response = requests.post(f"{BASE_URL}/documents/search", json=search_data)

        if response.status_code == 200:
            result = response.json()
            print(f"  搜索时间: {result['search_time']:.3f}秒")
            print(f"  结果数量: {result['total']}")

            for i, doc in enumerate(result['results']):
                print(f"  {i+1}. [分数: {doc['score']:.4f}] {doc['content']}")
        else:
            print(f"  ❌ 搜索失败: {response.status_code} - {response.text}")

    print()


def test_bulk_operations():
    """测试批量操作"""
    print("📦 测试批量创建...")

    bulk_docs = {
        "documents": [
            {"content": "区块链是一种分布式账本技术"},
            {"content": "量子计算利用量子力学原理"},
            {"content": "云计算提供按需的计算资源"}
        ]
    }

    response = requests.post(f"{BASE_URL}/documents/bulk", json=bulk_docs)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 批量创建完成:")
        print(f"   成功: {result['success_count']}")
        print(f"   失败: {result['failed_count']}")
        print(f"   消息: {result['message']}")
    else:
        print(f"❌ 批量创建失败: {response.status_code} - {response.text}")

    print()


def main():
    """主测试函数"""
    print("🚀 开始测试 FastAPI Redis Vector Search API")
    print("=" * 50)

    try:
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)

        # 测试健康检查
        test_health()

        # 创建测试文档
        create_test_documents()

        # 等待索引建立
        print("⏳ 等待索引建立...")
        time.sleep(2)

        # 测试搜索
        test_search()

        # 测试批量操作
        test_bulk_operations()

        print("✅ 所有测试完成!")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行在 http://localhost:8000")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    main()