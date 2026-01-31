"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.config import settings
from utils.logger import setup_logger, get_logger
from utils.errors import CryptoAnalysisException, ErrorResponse
from utils.rate_limiter import RateLimitMiddleware
import time
import uuid
from datetime import datetime

# Setup logger
logger = setup_logger(__name__, structured=True)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/health", "/api/health"]
)


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses with timing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": f"{process_time:.3f}s"
            },
            exc_info=True
        )
        raise


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(CryptoAnalysisException)
async def crypto_analysis_exception_handler(request: Request, exc: CryptoAnalysisException):
    """Handle custom application exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        f"Application exception: {exc.error_code.value} - {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code.value,
            "details": exc.details
        },
        exc_info=exc.original_exception if exc.original_exception else True
    )
    
    error_response = exc.to_error_response(request_id=request_id)
    
    # Determine HTTP status code based on error type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if "INVALID" in exc.error_code.value or "VALIDATION" in exc.error_code.value:
        status_code = status.HTTP_400_BAD_REQUEST
    elif "NOT_FOUND" in exc.error_code.value:
        status_code = status.HTTP_404_NOT_FOUND
    elif "AUTHENTICATION" in exc.error_code.value:
        status_code = status.HTTP_401_UNAUTHORIZED
    elif "AUTHORIZATION" in exc.error_code.value:
        status_code = status.HTTP_403_FORBIDDEN
    elif "RATE_LIMIT" in exc.error_code.value:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif "TIMEOUT" in exc.error_code.value:
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": None,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        serializable_error = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        # Convert ctx values to strings if they exist
        if "ctx" in error:
            serializable_error["ctx"] = {
                k: str(v) for k, v in error["ctx"].items()
            }
        errors.append(serializable_error)
    
    logger.warning(
        f"Validation error: {errors}",
        extra={
            "request_id": request_id,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "details": {"error": str(exc)} if settings.DEBUG else None,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    # TODO: Add database connection check
    # TODO: Add Redis connection check


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down application")


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Include Routers
# ============================================================================

from api.routes import analysis, portfolio, alarms, backtest, coins

app.include_router(analysis.router)
app.include_router(portfolio.router)
app.include_router(alarms.router)
app.include_router(backtest.router)
app.include_router(coins.router)
