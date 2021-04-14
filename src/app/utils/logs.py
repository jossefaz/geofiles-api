import json
import sys
import threading
import uuid
from typing import Optional

from loguru import logger
from enum import Enum


class LogType(str, Enum):
    HTTP_REQUEST = "HTTP_REQUEST"
    HTTP_RESPONSE = "HTTP_RESPONSE"
    SQL = "SQL"


class SingletonMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._instance = None
        cls._locker = threading.Lock()

    @property
    def instance(self, *args, **kwargs):
        if self._instance is None:
            with self._locker:
                if self._instance is None:
                    self._instance = self(*args, **kwargs)
        return self._instance


class RestLogger(metaclass=SingletonMeta):
    def __init__(self):
        self._request_id = None

    @classmethod
    def init_logger(cls):
        logger.remove()
        logger.add(sys.stdout, colorize=True, format="{message}")

    @property
    def request_id(self):
        if not self._request_id:
            return None
        return str(self._request_id)

    @request_id.setter
    def request_id(self, request_id):
        try:
            self._request_id = uuid.UUID(str(request_id))
        except ValueError:
            raise ValueError("request id must be a UUID string")

    def log_http_response(self, formatted_process_time, status_code, headers):
        log = {"request_id": self.request_id, "log_type": LogType.HTTP_RESPONSE,
               "completed_in_ms": formatted_process_time,
               "status_code": status_code,
               "headers": headers}
        logger.info(json.dumps(log))

    def log_http_request(self, route, method, headers, queryparams=None):
        log = {"request_id": self.request_id, "log_type": LogType.HTTP_REQUEST, "url": str(route),
               "headers": headers}
        if queryparams:
            log["queryparams"] = str(queryparams)
        logger.info(json.dumps(log))

    def log_sql_query(self, sql_query: str, record_num: Optional[int] = None):
        log = {"request_id": self.request_id, "log_type": LogType.SQL, "query": str(sql_query)}
        if record_num:
            log["record_found"] = record_num
        logger.info(json.dumps(log))
