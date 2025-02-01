# RAG Chatbot

A retrieval augmented generaion (RAG) assisted chatbot. This bot answers questions specifically on the Python Django framework

## Local development

Backend
```
cd web-backend
source .venv/bin/activate
export OPENAI_API_KEY=...
export CHROMA_CLIENT_AUTH_CREDENTIALS=...
hypercorn main:app --reload
```

Frontend
```
cd web-frontend
npm run dev
```