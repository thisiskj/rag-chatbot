import chromadb
from chromadb.config import Settings
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from openai import OpenAI
import os

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
        "http://localhost:5173/",
    ],
    allow_methods=["GET"],
)

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}


async def get_llm_response(context, q):
    logger.info(PROMPT_TEMPLATE.format(context=context, question=q))
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
                yield f"data: {current_content.encode('utf-8')}\n\n"


@app.get("/search")
async def search(q: str = ''):
    logger.info(f"Question is {q}")
    results = collection.query(
        query_texts=[q],  # Chroma will embed this for you
        n_results=20  # how many results to return
    )
    context = "\n".join([doc for doc in results['documents'][0]])

    return StreamingResponse(get_llm_response(context, q), media_type="text/event-stream")
