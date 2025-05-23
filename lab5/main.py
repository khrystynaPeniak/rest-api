from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.books import router as books_router
from app.routes.auth import auth_router

app = FastAPI(title="API for books", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books_router, prefix="/v1/api", tags=["Books"])
app.include_router(auth_router, prefix="/v1/api/auth", tags=["Authentication"])


@app.get("/")
def read_root():
    return {"message": "Main page"}


import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
