from datetime import datetime
from typing import Optional

from flask import Flask
from config import Config, Entry
from scheduler import Scheduler

app = Flask(__name__)
logging = app.logger
config: Optional[Config] = None

status = {
    "initialized": False,
}
updates = {
}


@app.route('/')
def index():
    cfg = config.config
    active_keys = {c.key for c in cfg}
    print("updates", updates)
    return {
        "status": status | {
            "time": datetime.now(),
        },
        "config": cfg,
        "entries": [u for k, u in updates.items() if k in active_keys]
    }


def handle_update(key: str, result: bool, ts: datetime):
    print(f"{ts} - got update for '{key}', result = {result}")
    updates[key] = {
        key: result,
        "ts": ts,
    }


def handle_cfg_update():
    scheduler.entries = config.config


if __name__ == '__main__':
    config = Config("./config.toml")
    scheduler = Scheduler(handle_update)
    config.on_refresh = handle_cfg_update
    scheduler.entries = config.config
    status["initialized"] = True
    app.run()
