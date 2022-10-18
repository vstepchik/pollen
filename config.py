import dataclasses
from pathlib import Path
from typing import Callable, Any, Optional, Dict, List

import tomli
import logging
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class _FSHandler(PatternMatchingEventHandler):
    patterns = ["config.toml"]

    def __init__(
            self,
            patterns=None,
            ignore_patterns=None,
            ignore_directories=False,
            case_sensitive=False,
            update_callback: Optional[Callable[[Path], Any]] = None,
            delete_callback: Optional[Callable[[], Any]] = None,
    ):
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self._update_callback = update_callback
        self._delete_callback = delete_callback

    def on_modified(self,  event):
        self._update_callback(Path(event.src_path))

    def on_created(self,  event):
        self._update_callback(Path(event.src_path))

    def on_deleted(self,  event):
        self._delete_callback()


class Config:
    _config_path: Path
    _observer: Observer
    _config: Dict
    on_refresh: Optional[Callable[[], Any]]

    def __init__(self, path: str):
        self.on_refresh = None
        self._config_path = Path(path).absolute()
        self.load_config(self._config_path)
        watch_dir = str(self._config_path.parent)
        print(f"Watching {watch_dir}")
        event_handler = _FSHandler(update_callback=self.load_config, delete_callback=self.clear_config)
        self._observer = Observer()
        self._observer.schedule(event_handler,  path=watch_dir,  recursive=False)
        self._observer.start()

    def load_config(self, path: Path):
        print(f"loading config from {path}")
        if not path.exists():
            self._config = {}
            return

        with open(self._config_path, mode="rb") as fp:
            try:
                self._config = tomli.load(fp)
                print(f"New config: {self._config}")
                if self.on_refresh:
                    self.on_refresh()
            except tomli.TOMLDecodeError as e:
                print(f"Failed to read config:", e)
                self.clear_config()

    def clear_config(self):
        print(f"clearing config")
        self._config = {}
        if self.on_refresh:
            self.on_refresh()

    @property
    def config(self) -> List['Entry']:
        return [Entry.from_dict(k, v) for k, v in self._config.items()]


@dataclasses.dataclass
class Entry:
    key: str
    request: 'RequestSpec'
    response: 'ResponseSpec'

    @staticmethod
    def from_dict(key: str, data: dict) -> 'Entry':
        return Entry(
            key=key,
            request=RequestSpec.from_dict(data["request"]),
            response=ResponseSpec.from_dict(data["response"]),
        )


@dataclasses.dataclass
class RequestSpec:
    method: str
    url: str
    headers: List[str]
    timeout_ms: int
    interval_ms_centre: float
    interval_ms_scale: float

    @staticmethod
    def from_dict(data: dict) -> 'RequestSpec':
        return RequestSpec(
            method=data.get("method", 'GET'),
            url=data["url"],
            headers=data.get("headers", []),
            timeout_ms=int(data.get("timeout_ms", 15 * 1000)),
            interval_ms_centre=float(data.get("interval_ms_centre", 5 * 60 * 1000)),
            interval_ms_scale=float(data.get("interval_ms_scale", 60 * 1000)),
        )


@dataclasses.dataclass
class ResponseSpec:
    matcher: str

    @staticmethod
    def from_dict(data: dict) -> 'ResponseSpec':
        return ResponseSpec(
            matcher=data["matcher"],
        )

