from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Api for books", version="1.0.0")

app.include_router(router, prefix="/v1/api")

@app.get("/")
def read_root():
    return {"message": "Main page"}

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)