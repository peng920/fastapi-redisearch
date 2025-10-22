# FastAPI Redis Vector Search

基于FastAPI和Redis的向量搜索API服务，支持文本的语义搜索功能。

## 功能特性

- 🚀 基于FastAPI的高性能API服务
- 🔍 使用Redis进行向量存储和相似性搜索
- 📝 支持文本的自动向量化
- 🌍 支持多语言文本搜索
- 📊 提供详细的搜索结果和相似度分数
- 🔧 支持单个和批量文档操作
- 🏥 健康检查和监控功能

## 项目结构

```
fastapi-redis-vector-search/
├── app/
│   ├── main.py              # FastAPI应用主文件
│   ├── models/
│   │   └── schemas.py       # Pydantic数据模型
│   ├── routers/
│   │   ├── documents.py     # 文档相关路由
│   │   └── health.py        # 健康检查路由
│   └── services/
│       ├── redis_client.py  # Redis向量搜索服务
│       └── embedding_service.py  # 文本嵌入服务
├── config/
│   └── settings.py          # 配置文件
├── requirements.txt         # Python依赖
├── run.py                  # 启动脚本
├── .env                    # 环境变量
├── docker-compose.yml      # Docker编排文件
└── README.md              # 项目说明
```

## 快速开始

### 使用Docker Compose（推荐）

1. 克隆项目并进入目录：
```bash
cd fastapi-redis-vector-search
```

2. 启动服务：
```bash
docker-compose up --build
```

3. 访问API文档：
- OpenAPI文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc

### 手动安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 确保Redis服务运行：
```bash
# 使用Docker运行Redis
docker run -d -p 6379:6379 redis/redis-stack-server:latest
```

3. 启动应用：
```bash
python run.py
```

## API使用示例

### 1. 创建文档

```bash
curl -X POST "http://localhost:8000/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "人工智能是计算机科学的一个分支"
  }'
```

### 2. 搜索相似文档

```bash
curl -X POST "http://localhost:8000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "机器学习",
    "limit": 5
  }'
```

### 3. 批量创建文档

```bash
curl -X POST "http://localhost:8000/documents/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"content": "深度学习是机器学习的一个子领域"},
      {"content": "神经网络模仿人脑的工作方式"}
    ]
  }'
```

### 4. 健康检查

```bash
curl "http://localhost:8000/health/"
```

## 配置说明

环境变量配置文件 `.env`：

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application Configuration
APP_NAME=FastAPI Redis Vector Search
APP_VERSION=1.0.0
DEBUG=True

# Vector Search Configuration
VECTOR_DIMENSION=1024
DISTANCE_METRIC=COSINE
MAX_RESULTS=10

# Embedding Model Configuration
# Options: sentence_transformers, tei
EMBEDDING_PROVIDER=tei
#EMBEDDING_MODEL_NAME=bge-m3

FORCE_RECREATE_INDEX=False

# TEI Configuration (OpenAI compatible)
TEI_API_URL=http://localhost:8001/v1/embeddings
# TEI_API_KEY=your_api_key_here
```

## API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/documents/` | 创建单个文档 |
| POST | `/documents/bulk` | 批量创建文档 |
| GET | `/documents/{doc_id}` | 获取指定文档 |
| DELETE | `/documents/{doc_id}` | 删除指定文档 |
| POST | `/documents/search` | 搜索相似文档 |
| GET | `/health/` | 健康检查 |

## 技术栈

- **FastAPI**: 现代、快速的Web框架
- **Redis**: 内存数据库，用于向量存储和搜索
- **Sentence-Transformers**: 文本嵌入模型
- **Pydantic**: 数据验证和序列化
- **Uvicorn**: ASGI服务器

## 注意事项

1. 确保Redis版本支持RediSearch模块
2. 如果使用本地embedding首次运行时会自动下载预训练模型（下载文件大小由所用模型决定）
3. 向量维度根据嵌入模型自动确定（bge-m3: 1024维）
4. 建议在生产环境中使用HTTPS和认证机制

## 许可证

MIT License