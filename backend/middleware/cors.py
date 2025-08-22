from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

def setup_cors(app):
    """
    Setup CORS middleware for the FastAPI app
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
