from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    content: str = Field(..., min_length=1, description="文档内容")


class DocumentCreate(DocumentBase):
    id: Optional[str] = Field(None, description="文档ID，如果不提供则自动生成")


class DocumentResponse(BaseModel):
    id: str
    content: str
    score: Optional[float] = Field(None, description="相似度分数")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="搜索查询文本")
    limit: Optional[int] = Field(10, ge=1, le=100, description="返回结果数量限制")


class SearchResponse(BaseModel):
    query: str
    results: List[DocumentResponse]
    total: int
    search_time: float


class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    model_loaded: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime


class BulkDocumentCreate(BaseModel):
    documents: List[DocumentCreate] = Field(..., min_items=1, max_items=100, description="批量创建文档")


class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_ids: List[str]
    message: str