from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid
import time
import logging

from app.models.schemas import (
    DocumentCreate,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    BulkDocumentCreate,
    BulkOperationResponse
)
from app.services.redis_client import vector_search
from app.services.embedding_service import embedding_service

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(document: DocumentCreate):
    """创建新文档"""
    try:
        # 生成唯一ID
        doc_id = document.id or str(uuid.uuid4())

        # 生成嵌入向量
        vector = embedding_service.encode_text(document.content)

        # 存储到Redis
        success = vector_search.add_document(doc_id, document.content, vector)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store document"
            )

        return DocumentResponse(
            id=doc_id,
            content=document.content
        )

    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/bulk", response_model=BulkOperationResponse)
async def create_documents_bulk(bulk_request: BulkDocumentCreate):
    """批量创建文档"""
    success_count = 0
    failed_count = 0
    failed_ids = []

    for doc in bulk_request.documents:
        try:
            doc_id = doc.id or str(uuid.uuid4())
            vector = embedding_service.encode_text(doc.content)
            success = vector_search.add_document(doc_id, doc.content, vector)

            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(doc.id or "unknown")

        except Exception as e:
            logger.error(f"Error creating document {doc.id}: {e}")
            failed_count += 1
            failed_ids.append(doc.id or "unknown")

    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        message=f"Bulk operation completed. Success: {success_count}, Failed: {failed_count}"
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """获取指定文档"""
    try:
        doc = vector_search.get_document(doc_id)

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return DocumentResponse(**doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str):
    """删除指定文档"""
    try:
        success = vector_search.delete_document(doc_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """搜索相似文档"""
    try:
        start_time = time.time()
        logger.info(f"Search request received: query='{search_request.query}', limit={search_request.limit}")

        # 生成查询向量
        query_vector = embedding_service.encode_text(search_request.query)
        logger.info(f"Query vector generated with length: {len(query_vector)}")

        # 搜索相似文档
        results = vector_search.search_similar(query_vector, search_request.limit)
        logger.info(f"Search returned {len(results)} results")

        # 格式化结果 - 正确处理文档ID，避免前缀移除问题
        documents = []
        for result in results:
            # 确保ID格式正确，不强制移除前缀
            doc_id = result["id"]
            if doc_id.startswith("doc:"):
                doc_id = doc_id[4:]  # 仅在确实有前缀时移除
            
            documents.append(DocumentResponse(
                id=doc_id,
                content=result["content"],
                score=result["score"]
            ))
            logger.debug(f"Added document to response: {doc_id}, score: {result['score']}")

        search_time = time.time() - start_time
        logger.info(f"Search completed in {search_time:.4f} seconds")

        return SearchResponse(
            query=search_request.query,
            results=documents,
            total=len(documents),
            search_time=search_time
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        import traceback
        logger.error(f"Detailed error trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )