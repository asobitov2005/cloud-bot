from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, dashboard, files, users_api, fsub, admin_settings, admins, admin_logs
from app.bot.webhook import router as webhook_router, set_dispatcher, set_bot
from app.core.config import settings


# Create FastAPI app
app = FastAPI(title="PrimeLingo Admin Panel")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for 401 on HTML pages
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Redirect to login for 401 on HTML pages"""
    if exc.status_code == 401:
        # Check if request is for HTML page (not API)
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse(url="/admin/login", status_code=303)
    # For API requests, return JSON error
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/admin", tags=["auth"])
app.include_router(dashboard.router, prefix="/admin", tags=["dashboard"])
app.include_router(files.router, prefix="/admin", tags=["files"])
app.include_router(users_api.router, prefix="/admin", tags=["users"])
app.include_router(fsub.router, prefix="/admin", tags=["fsub"])
app.include_router(admin_settings.router, prefix="/admin", tags=["settings"])
app.include_router(admins.router, prefix="/admin", tags=["admins"])  # NEW: Admin management
app.include_router(admin_logs.router, prefix="/admin", tags=["logs"])  # NEW: Audit logs

# Include webhook router (for Telegram webhook mode)
app.include_router(webhook_router, tags=["webhook"])


@app.get("/")
async def root():
    """Redirect to admin panel"""
    return RedirectResponse(url="/admin/login")


@app.get("/admin")
async def admin_root():
    """Redirect to dashboard"""
    return RedirectResponse(url="/admin/dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=settings.ADMIN_PANEL_HOST,
        port=settings.ADMIN_PANEL_PORT,
        reload=settings.DEBUG
    )


@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    from app.bot import init_bot
    from app.bot.main import set_bot_instance
    
    # Initialize bot
    bot, _ = init_bot(with_dispatcher=False)
    
    # Store bot instance for API access
    set_bot_instance(bot)
    
    # Store in app state
    app.state.bot = bot


@app.on_event("shutdown")
async def shutdown_event():
    """Close bot session on shutdown"""
    if hasattr(app.state, "bot"):
        await app.state.bot.session.close()
