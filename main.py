from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API da IA Jurídica rodando na nuvem!"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # O Railway define automaticamente a porta correta
    uvicorn.run(app, host="0.0.0.0", port=port)
