import uvicorn

from machine.server import machine


def run():
    uvicorn.run(
        app="machine.server:machine",
        host=machine.settings.APP_HOST,
        port=machine.settings.APP_PORT,
        reload=machine.settings.DEBUG,
    )


if __name__ == "__main__":
    run()
