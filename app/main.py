import os
from typing import Union

from dotenv import load_dotenv
from fastapi import FastAPI
from wakeonlan import send_magic_packet

load_dotenv()

app = FastAPI()

DEFAULT_MAC = os.getenv("DEFAULT_MAC")


@app.get("/")
async def root():
    return {"status": 200, "message": "Welcome to the Wake-on-LAN API!"}


@app.get("/wake")
async def wake_pc():
    try:
        send_magic_packet(DEFAULT_MAC)
        return {"message": "Wake-on-LAN packet sent successfully"}
    except Exception as e:
        return {"error": f"Failed to send Wake-on-LAN packet: {str(e)}"}


@app.get("/wake/{wake_addr}")
async def read_wake(wake_addr: str, q: Union[str, None] = None):
    try:
        send_magic_packet(wake_addr)
        return {
            "message": f"Wake-on-LAN packet sent successfully to {wake_addr} device!"
        }
    except Exception as e:
        return {
            "error": f"Failed to send Wake-on-LAN packet to {wake_addr} device: {str(e)}"
        }
