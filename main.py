import uvicorn

from app.server import app


def run():
    uvicorn.run(
        app="app.server:app",
        host=app.settings.APP_HOST,
        port=app.settings.APP_PORT,
        reload=app.settings.DEBUG,
    )


if __name__ == "__main__":
    run()
