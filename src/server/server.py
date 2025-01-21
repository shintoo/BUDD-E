from multiprocessing import Queue
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time

server = FastAPI()
server.state.queue = Queue()

server.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static"
)

@server.get("/", response_class=HTMLResponse)
async def get_html():
    html_file = Path("server/dashboard.html")
    return html_file.read_text()

@server.post("/control")
async def control_robot(request: Request):
    data = await request.json()
    command = data.get("command")

    server.state.queue.put(command)

    return JSONResponse(content={"message": "Command received", "command": command})

@server.get("/status")
async def robot_status(request: Request):
    return JSONResponse(content=server.state.robot.status())
