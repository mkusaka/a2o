from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def test():
    return {"message": "Simple test working"}

@app.get("/health")
async def health():
    return {"status": "ok"}