# AI LLM API

<p align="center">
  <a href="https://github.com/CJX0712/ai-llm-api/actions/workflows/build.yml"><img src="https://github.com/CJX0712/ai-llm-api/actions/workflows/build.yml/badge.svg" alt="ci"></a>
  <a href="https://github.com/CJX0712/ai-llm-api/releases"><img src="https://img.shields.io/github/v/release/CJX0712/ai-llm-api?sort=semver" alt="release"></a>
  <img src="https://img.shields.io/badge/author-%E6%99%A8%E6%98%9F-1f6feb" alt="author">
</p>

端到端可运行的本地 LLM 推理服务。FastAPI + llama-cpp-python，CPU 推理，镜像自动推送到 GitHub Packages (`ghcr.io`)。

作者：晨星

## 架构

```
HTTP 请求
   │
   ▼
FastAPI (uvicorn, :8000)
   │  懒加载
   ▼
llama-cpp-python ── 加载 /models/*.gguf (运行时挂载，不打包进镜像)
   │  CPU 多线程推理 (n_threads 锁 2-4)
   ▼
GGUF 量化模型
```

- 模型权重**运行时挂载**，镜像本身不含权重 → 守住 GitHub Packages 免费 500 MB 额度
- push 到 `main` 分支触发 GitHub Actions：自动 `docker build` + 推送镜像到 `ghcr.io/cjx0712/ai-llm-api`

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查，返回模型加载状态 |
| POST | `/v1/chat/completions` | OpenAI 风格对话，支持 `stream:true` SSE |
| POST | `/generate` | 单次续写补全 |

## 本地运行

```bash
mkdir -p models
cp your-model.gguf models/model.gguf        # 放一个 GGUF 量化模型
docker compose up --build
curl http://localhost:8000/health
```

推理示例：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}],"max_tokens":128}'
```

## 从 GitHub Packages 拉取镜像

```bash
docker pull ghcr.io/cjx0712/ai-llm-api:latest
docker run -p 8000:8000 -v $(pwd)/models:/models:ro ghcr.io/cjx0712/ai-llm-api:latest
```

> 拉取私有包需先 `docker login ghcr.io`（用带 `read:packages` 的 PAT）。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MODEL_PATH` | `/models/model.gguf` | GGUF 模型路径 |
| `N_THREADS` | `4` | 推理线程数（小模型锁 2-4 最快） |
| `N_CTX` | `2048` | 上下文窗口 |

## 部署到 GitHub Packages

`git push origin main` 即触发 Actions 自动构建并把镜像推送到 `ghcr.io/cjx0712/ai-llm-api`。
