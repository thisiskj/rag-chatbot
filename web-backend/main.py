import chromadb
from chromadb.config import Settings
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from openai import OpenAI
import os
from asyncio import sleep

logger = logging.getLogger('hypercorn.error')

openai_client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
)

SYSTEM_PROMPT = """
You are a helpful assistant that has knowledge on the Django web framework
If you don't know the answer, say you don't know. Do not try to make up an answer.
"""

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

chroma_client = chromadb.HttpClient(
    host='chroma-production-e1c6.up.railway.app',
    port=443,
    ssl=True,
    settings=Settings(
        chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
        chroma_client_auth_credentials=os.environ.get("CHROMA_CLIENT_AUTH_CREDENTIALS"),
        chroma_auth_token_transport_header="X-Chroma-Token"
    )
)
collection = chroma_client.get_collection(name="django_docs")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://frontend-production-79aa.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

async def gen_func():
    for i in range(0,10):
        yield f"event: res\ndata: {i}\n\n"
        await sleep(.1)
    yield f"event: end\ndata: complete\n\n"

@app.get("/test")
async def test():
    return StreamingResponse(gen_func(), media_type="text/event-stream")


async def get_llm_response(context, q, sources):
    # logger.info(PROMPT_TEMPLATE.format(context=context, question=q))
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        temperature=1.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PROMPT_TEMPLATE.format(context=context, question=q)}
        ],
        stream=True
    )
    for chunk in response:
        for choice in chunk.choices:
            if choice.finish_reason == "stop":
                continue
            else:
                current_content = choice.delta.content
                yield f"event:res\ndata: {current_content}\n\n"

    for s in sources:
        yield f"event:src\ndata:{s}\n\n"

    yield f"event:end\ndata: complete\n\n"


@app.get("/search")
async def search(q: str = ''):
    logger.info(f"Question is {q}")
    results = collection.query(
        query_texts=[q],  # Chroma will embed this for you
        n_results=5  # how many results to return
    )

    sources = list(set([m['source'] for m in results['metadatas'][0]]))
    context = "\n".join([doc for doc in results['documents'][0]])

    return StreamingResponse(get_llm_response(context, q, sources), media_type="text/event-stream")
