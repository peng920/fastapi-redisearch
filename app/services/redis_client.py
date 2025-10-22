import redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np
from typing import List, Dict, Any, Optional
import json
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class RedisVectorSearch:
    def __init__(self):
        # 将decode_responses设置为False，避免自动解码二进制数据
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=False
        )
        self.index_name = "vector_index"
        self.prefix = "doc:"

    def create_index(self):
        """创建向量搜索索引 - 根据配置决定是否重新创建"""
        try:
            index_name_bytes = self.index_name.encode('utf-8') if isinstance(self.index_name, str) else self.index_name
            
            # 检查索引是否已存在
            try:
                self.redis_client.ft(index_name_bytes).info()
                logger.info(f"Index {self.index_name} already exists")
                
                # 如果不需要强制重新创建索引，则直接返回
                if not settings.force_recreate_index:
                    logger.info(f"force_recreate_index is False, using existing index")
                    return True
                logger.info(f"force_recreate_index is True, recreating index")
            except:
                pass
            
            # 强制删除旧索引（如果存在）
            try:
                self.redis_client.ft(index_name_bytes).dropindex(delete_documents=True)
                logger.info(f"Dropped existing index {self.index_name} to recreate with correct dimensions")
            except Exception as e:
                logger.info(f"No existing index to drop or error dropping index: {e}")
            
            # 清除所有文档数据
            try:
                pattern = f"{self.prefix}*".encode('utf-8')
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Deleted {len(keys)} existing documents")
            except Exception as e:
                logger.warning(f"Error clearing existing documents: {e}")

            # 创建向量字段
            logger.info(f"Creating index with vector dimension: {settings.vector_dimension}")
            logger.info(f"Expected vector size in bytes: {settings.vector_dimension * 4}")
            
            vector_field = VectorField(
                "vector",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": settings.vector_dimension,
                    "DISTANCE_METRIC": settings.distance_metric,
                    "INITIAL_CAP": 1000,
                    "BLOCK_SIZE": 1000
                }
            )

            # 创建文本字段
            text_field = TextField("content")
            id_field = TextField("id")

            # 确保前缀也是字节格式
            prefix_bytes = [p.encode('utf-8') if isinstance(p, str) else p for p in [self.prefix]]
            
            # 创建索引
            index_name_bytes = self.index_name.encode('utf-8') if isinstance(self.index_name, str) else self.index_name
            self.redis_client.ft(index_name_bytes).create_index(
                fields=[vector_field, text_field, id_field],
                definition=IndexDefinition(prefix=prefix_bytes, index_type=IndexType.HASH)
            )

            logger.info(f"Created index {self.index_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False

    def add_document(self, doc_id: str, content: str, vector: List[float]) -> bool:
        """添加文档到向量索引 - 确保所有字段格式正确"""
        try:
            logger.info(f"Adding document {doc_id}, vector length: {len(vector)}")
            
            # 确保key是字节格式
            key = f"{self.prefix}{doc_id}".encode('utf-8')
            logger.debug(f"Document key: {key}")

            # 确保向量是正确的格式
            vector_array = np.array(vector, dtype=np.float32)
            vector_bytes = vector_array.tobytes()
            logger.debug(f"Vector converted to bytes, length: {len(vector_bytes)} bytes")

            # 存储文档 - 确保字符串字段也是字节格式
            result = self.redis_client.hset(
                key,
                mapping={
                    b"id": doc_id.encode('utf-8'),
                    b"content": content.encode('utf-8'),
                    b"vector": vector_bytes
                }
            )
            
            logger.info(f"Added document {doc_id}, hset result: {result}")
            
            # 验证文档是否被正确存储
            stored = self.redis_client.exists(key)
            logger.info(f"Document {doc_id} exists in Redis: {stored}")
            
            return True

        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return False

    def search_similar(self, query_vector: List[float], limit: int = None) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            if limit is None:
                limit = settings.max_results

            logger.info(f"Searching with vector of length {len(query_vector)}, limit: {limit}")
            
            # 先检查Redis中是否有数据
            pattern = f"{self.prefix}*".encode('utf-8')
            keys = self.redis_client.keys(pattern)
            logger.info(f"Found {len(keys)} documents in Redis with pattern {pattern}")

            # 将查询向量转换为字节
            query_array = np.array(query_vector, dtype=np.float32)
            query_bytes = query_array.tobytes()
            logger.debug(f"Query vector bytes created: {len(query_bytes)} bytes")

            # 当decode_responses=False时，需要确保index_name也是字节
            index_name_bytes = self.index_name.encode('utf-8') if isinstance(self.index_name, str) else self.index_name
            
            # 检查索引信息
            try:
                index_info = self.redis_client.ft(index_name_bytes).info()
                logger.info(f"Index info: {index_info}")
            except Exception as e:
                logger.warning(f"Error getting index info: {e}")

            # 修改搜索查询，使用简单的查询语法
            # 使用简单的KNN搜索语法，确保与Redis配置兼容
            query_str = f"*=>[KNN {limit} @vector $query_vector AS vector_score]"
            logger.debug(f"Search query: {query_str}")
            
            q = Query(query_str)\
                .return_fields("id", "content", "vector_score")\
                .sort_by("vector_score")\
                .dialect(2)

            # 执行搜索，直接传递参数
            results = self.redis_client.ft(index_name_bytes).search(q, query_params={"query_vector": query_bytes})
            logger.info(f"Search returned {len(results.docs)} results")

            # 格式化结果 - 处理字节格式的返回数据
            documents = []
            for doc in results.docs:
                # 处理字节格式的字段
                doc_id = doc.id.decode('utf-8') if isinstance(doc.id, bytes) else doc.id
                doc_content = doc.content.decode('utf-8') if isinstance(doc.content, bytes) else doc.content
                # 尝试获取向量分数，处理不同的字段名情况
                score_value = 0.0
                if hasattr(doc, 'vector_score'):
                    score_value = float(doc.vector_score)
                elif hasattr(doc, '__vector_score'):
                    score_value = float(doc.__vector_score)
                
                documents.append({
                    "id": doc_id,
                    "content": doc_content,
                    "score": score_value
                })
                logger.debug(f"Found document: {doc_id}, score: {score_value}")

            return documents

        except Exception as e:
            logger.error(f"Error searching similar vectors: {e}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return []

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档 - 手动处理字符串解码"""
        try:
            key = f"{self.prefix}{doc_id}".encode('utf-8')
            doc = self.redis_client.hgetall(key)

            if doc:
                # 手动解码字符串字段，跳过二进制字段
                result = {}
                for field, value in doc.items():
                    # 只处理id和content字段，并确保正确解码
                    if field == b'id' and isinstance(value, bytes):
                        result['id'] = value.decode('utf-8', errors='ignore')
                    elif field == b'content' and isinstance(value, bytes):
                        result['content'] = value.decode('utf-8', errors='ignore')
                return result
            return None

        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            key = f"{self.prefix}{doc_id}"
            result = self.redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def health_check(self) -> bool:
        """检查Redis连接状态"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# 全局Redis向量搜索实例
vector_search = RedisVectorSearch()