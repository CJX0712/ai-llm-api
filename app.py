"""
AI LLM API — 本地 LLM 推理服务
FastAPI + llama-cpp-python，CPU 推理，模型权重运行时挂载。

作者：晨星
"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

MODEL_PATH = os.getenv("MODEL_PATH", "/models/model.gguf")
N_THREADS = int(os.getenv("N_THREADS", "4"))          # 小量化模型锁 2-4 线程最快（内存带宽瓶颈）
N_CTX = int(os.getenv("N_CTX", "2048"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="AI LLM API", version="1.0.0")

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(
                status_code=503,
                detail=f"model not found at {MODEL_PATH}. Mount a GGUF file and set MODEL_PATH.",
            )
        from llama_cpp import Llama

        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            verbose=False,
        )
    return _llm


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _llm is not None,
        "model_path": MODEL_PATH,
        "n_threads": N_THREADS,
        "n_ctx": N_CTX,
    }


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    engine = get_llm()
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    if req.stream:
        def gen():
            for chunk in engine.create_chat_completion(
                messages=messages,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                stream=True,
            ):
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    out = engine.create_chat_completion(
        messages=messages,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "model": os.path.basename(MODEL_PATH),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": out["choices"][0]["message"]["content"],
                },
                "finish_reason": "stop",
            }
        ],
        "usage": out.get("usage", {}),
    }


@app.post("/generate")
def generate(req: GenerateRequest):
    engine = get_llm()
    out = engine(
        prompt=req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return {
        "text": out["choices"][0]["text"],
        "usage": out.get("usage", {}),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
