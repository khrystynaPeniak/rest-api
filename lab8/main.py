from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from books_routes import books_router
from auth_routes import auth_router
from database import initialize_database
from rate_limiter import check_request_limit

app = FastAPI(
    title="Personal Book Library API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()

app.include_router(books_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def welcome_endpoint(request: Request):
    await check_request_limit(request)
    return {
        "message": "Welcome to Personal Book Library API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "books": "/api/v1/books",
            "documentation": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
