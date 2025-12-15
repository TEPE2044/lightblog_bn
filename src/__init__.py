# src/utils.py
from fastapi.openapi.utils import get_openapi


def custom_openapi(app):
    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        # 保证路由已全部注册完再生成骨架
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
            "X-Payload": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Payload",
            },
        }
        app.openapi_schema = openapi_schema
        return openapi_schema

    return openapi  # ← 返回 callable
