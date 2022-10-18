from re import Pattern

import requests
import re

from config import Entry


class Prober:
    @staticmethod
    def probe(entry: Entry) -> bool:
        req = entry.request
        headers = [header.split(":", maxsplit=1) for header in req.headers]
        headers = {parts[0].strip(): parts[1].strip() for parts in headers}
        resp = requests.request(method=req.method, url=req.url, timeout=req.timeout_ms / 1000.0, headers=headers)
        pat = entry.response.matcher
        print(f"checking if {resp.text} matches {pat}")
        return re.compile(pat).search(resp.text) is not None
