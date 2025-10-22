import logging
import requests
from typing import List, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingService:
    """基于Sentence Transformer的嵌入服务"""
    def __init__(self, model_name: str):
        # 延迟导入，避免在使用TEI时也需要安装sentence-transformers
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        try:
            self.model = SentenceTransformer(model_name)
            self.np = np
            logger.info(f"SentenceTransformer model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model: {e}")
            raise

    def encode_text(self, text: str) -> List[float]:
        """将文本编码为向量"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model.get_sentence_embedding_dimension()


class TEIEmbeddingService:
    """支持OpenAI兼容格式的嵌入服务"""
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        if not api_url:
            raise ValueError("TEI API URL is required for TEI embedding service")
        
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        logger.info(f"Embedding service initialized with URL: {api_url}")

    def encode_text(self, text: str) -> List[float]:
        """将文本编码为向量"""
        return self.encode_texts([text])[0]

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本 - 支持OpenAI兼容的API格式"""
        try:
            # 使用OpenAI兼容的请求格式
            payload = {
                "input": texts,
                "model": "embedding-model"
            }
            
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            results = response.json()
            
            # 处理OpenAI兼容的响应格式
            if isinstance(results, dict) and "data" in results:
                # OpenAI格式: {"data": [{"embedding": [...], "index": 0}, ...]}
                return [item.get("embedding") for item in results["data"]]
            elif isinstance(results, list):
                return results
            elif isinstance(results, dict) and "embeddings" in results:
                return results["embeddings"]
            else:
                logger.error(f"Unexpected API response format: {results}")
                raise ValueError(f"Unexpected API response format: {results}")
                
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error with embedding API: {http_err}, Response: {response.text if 'response' in locals() else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Error encoding texts with embedding API: {e}")
            raise

    def get_dimension(self) -> int:
        """获取向量维度 - 使用配置中的值"""
        return settings.vector_dimension


def get_embedding_service() -> 'BaseEmbeddingService':
    """根据配置获取合适的嵌入服务"""
    provider = settings.embedding_provider.lower()
    
    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingService(settings.embedding_model_name)
    elif provider == "tei":
        return TEIEmbeddingService(settings.tei_api_url, settings.tei_api_key)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


# 定义基类接口
class BaseEmbeddingService:
    def encode_text(self, text: str) -> List[float]:
        raise NotImplementedError
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError
    
    def get_dimension(self) -> int:
        raise NotImplementedError


# 全局嵌入服务实例
embedding_service = get_embedding_service()