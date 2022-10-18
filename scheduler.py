import time
from datetime import datetime
from threading import Thread
from typing import List, Dict, Set, Callable, Any, Iterable, Mapping

import numpy as np

from config import Entry
from prober import Prober


class Scheduler:
    _entries: Dict[str, Entry]
    _scheduled: Set[str]
    _task_callback: Callable[[str, bool, datetime], Any]

    def __init__(self, task_callback: Callable[[str, bool, datetime], Any]):
        self._entries = {}
        self._scheduled = set()
        self._task_callback = task_callback

    @property
    def entries(self) -> List[Entry]:
        return list(self._entries.values())

    @entries.setter
    def entries(self, value: List[Entry]):
        self._entries = {e.key: e for e in value}
        self._update()

    def _update(self):
        to_schedule = self._entries.keys() - self._scheduled
        print(f"new entries to schedule: {to_schedule}")
        for en in to_schedule:
            self._schedule(self._entries[en])

    def _schedule(self, entry: Entry):
        task = _Task(entry=entry, callback=self._complete_callback, name=entry.key)
        task.start()
        self._scheduled.add(entry.key)

    def _complete_callback(self, key: str, result: bool, ts: datetime):
        try:
            self._scheduled.remove(key)
        except KeyError:
            pass

        if key in self._entries:
            print(f"rescheduling {key}")
            self._schedule(self._entries[key])
        else:
            print(f"not rescheduling {key}")
        self._task_callback(key, result, ts)


class _Task(Thread):
    _entry: Entry
    _callback: Callable[[str, bool, datetime], Any]

    def __init__(self, entry: Entry, callback: Callable[[str, bool, datetime], Any], name: str | None = ...) -> None:
        super().__init__(name=name, daemon=False)
        self._entry = entry
        self._callback = callback

    def run(self) -> None:
        self._delay()
        print(f"{self.name} probing")
        result = self._probe()
        print(f"{self.name} got response matching: {result}")
        self._callback(self._entry.key, result, datetime.now())

    def _delay(self):
        req = self._entry.request
        delay = np.random.normal(loc=req.interval_ms_centre, scale=req.interval_ms_scale) / 1000.0
        delay = max(1.337, delay)
        print(f"{self.name} is sleeping for {delay} sec")
        time.sleep(delay)
        print(f"{self.name} woke up")

    def _probe(self) -> bool:
        try:
            return Prober.probe(self._entry)
        except Exception as e:
            print(e)
            return False
