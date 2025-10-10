"""A tiny subset of the :mod:`httpx` API used by the tests.

This project depends on :mod:`fastapi.testclient`, which in turn imports
``httpx``.  The real library is quite feature rich, but the TestClient only
relies on a very small surface area of its public API.  The production
environment for these kata style exercises does not ship with ``httpx``
installed, which means importing ``fastapi.testclient`` raises a
``RuntimeError`` before our application code is able to execute.  In order to
exercise the API contract tests we provide a lightweight, in-repository stub of
the ``httpx`` package that mimics the bits of functionality that Starlette's
TestClient expects.

This implementation focuses solely on the behaviours that show up in the test
suite:

* ``httpx.Client`` with synchronous request helpers and URL merging.
* ``httpx.BaseTransport`` and ``httpx.ByteStream`` so that Starlette can pipe
  ASGI traffic through the client.
* ``httpx.Request`` and ``httpx.Response`` objects exposing the attributes the
  TestClient reads (URL parts, headers, body accessors, etc.).
* Minimal modules for ``httpx._client`` and ``httpx._types`` that provide the
  names referenced by the real implementation.

The goal is not to be feature complete, just to accurately emulate the pieces
the tests exercise.  Keeping the stub small makes it easier to audit and avoids
pulling in a large dependency tree at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace
from typing import Any, Iterable, Iterator, Mapping
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit


class UseClientDefault:
    """Marker type used by the real httpx client API."""

    def __repr__(self) -> str:  # pragma: no cover - used for debugging only
        return "USE_CLIENT_DEFAULT"


USE_CLIENT_DEFAULT = UseClientDefault()


class BaseTransport:
    """Base transport that forwards requests to an underlying implementation."""

    def handle_request(self, request: "Request") -> "Response":  # pragma: no cover - abstract
        raise NotImplementedError

    def close(self) -> None:
        """Allow transports to clean up resources."""


class ByteStream:
    """Very small ``ByteStream`` implementation used by Starlette."""

    def __init__(self, content: bytes | bytearray | memoryview) -> None:
        self._buffer = bytes(content)

    def read(self) -> bytes:
        return self._buffer


class Headers:
    """Case-insensitive, multi-value header mapping."""

    def __init__(self, headers: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None) -> None:
        self._items: list[tuple[str, str]] = []
        if headers is None:
            return
        if isinstance(headers, Headers):
            iterable = headers.multi_items()
        elif isinstance(headers, Mapping):
            iterable: Iterable[tuple[str, Any]] = headers.items()
        else:
            iterable = headers
        for key, value in iterable:
            self._items.append((str(key).lower(), str(value)))

    def copy(self) -> "Headers":
        new = Headers()
        new._items = list(self._items)
        return new

    def get(self, key: str, default: str | None = None) -> str | None:
        key = key.lower()
        for k, v in reversed(self._items):
            if k == key:
                return v
        return default

    def update(self, headers: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> None:
        if isinstance(headers, Headers):
            iterable: Iterable[tuple[str, Any]] = headers.multi_items()
        elif isinstance(headers, Mapping):
            iterable: Iterable[tuple[str, Any]] = headers.items()
        else:
            iterable = headers
        for key, value in iterable:
            self._items.append((str(key).lower(), str(value)))

    def multi_items(self) -> list[tuple[str, str]]:
        return list(self._items)

    def items(self) -> Iterator[tuple[str, str]]:
        seen: dict[str, str] = {}
        for key, value in self._items:
            seen[key] = value
        return iter(seen.items())

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):  # pragma: no cover - defensive
            return False
        key = key.lower()
        return any(k == key for k, _ in self._items)


@dataclass
class URL:
    """Minimal representation of a URL."""

    raw: str

    def __post_init__(self) -> None:
        scheme, netloc, path, query, fragment = urlsplit(self.raw)
        # Provide sane defaults expected by Starlette's TestClient.
        self.scheme = scheme or "http"
        self._netloc = netloc.encode("ascii")
        self.path = path or "/"
        self.query = query.encode("ascii")
        raw_path = path or "/"
        if query:
            raw_path = f"{raw_path}?{query}"
        self.raw_path = raw_path.encode("ascii")

    @property
    def netloc(self) -> bytes:
        return self._netloc

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        return self.raw


class Request:
    """Simplified request object that behaves like httpx.Request."""

    def __init__(
        self,
        method: str,
        url: str,
        *,
        headers: Headers | Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
        content: bytes | str | None = None,
        data: Mapping[str, Any] | Iterable[tuple[str, Any]] | bytes | None = None,
        json_data: Any | None = None,
    ) -> None:
        self.method = method.upper()
        self.url = URL(url)
        base_headers = Headers(headers)
        body: bytes
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            if base_headers.get("content-type") is None:
                base_headers.update({"content-type": "application/json"})
        elif content is not None:
            body = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        elif data is not None:
            if isinstance(data, (bytes, bytearray)):
                body = bytes(data)
            else:
                body = urlencode(dict(data)).encode("ascii")
            if base_headers.get("content-type") is None:
                base_headers.update({"content-type": "application/x-www-form-urlencoded"})
        else:
            body = b""
        self.headers = base_headers
        self._stream = ByteStream(body)

    def read(self) -> bytes:
        return self._stream.read()


class Response:
    """Simplified HTTP response used by the tests."""

    def __init__(
        self,
        status_code: int,
        *,
        headers: Iterable[tuple[str, str]] | Mapping[str, str] | None = None,
        stream: ByteStream | bytes | None = None,
        request: Request | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = Headers(headers)
        if stream is None:
            self._content = b""
        elif isinstance(stream, ByteStream):
            self._content = stream.read()
        else:
            self._content = bytes(stream)
        self.request = request

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self._content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text or "null")

    def read(self) -> bytes:
        return self.content

    def close(self) -> None:  # pragma: no cover - API parity
        pass


class CookieJar(dict[str, str]):
    """Extremely small cookie jar that behaves like ``httpx.Cookies``."""

    def update(self, other: Mapping[str, str] | Iterable[tuple[str, str]]) -> None:  # type: ignore[override]
        if isinstance(other, Mapping):
            items = other.items()
        else:
            items = other
        for key, value in items:
            super().__setitem__(str(key), str(value))

    def __str__(self) -> str:  # pragma: no cover - helpful during debugging
        return "; ".join(f"{k}={v}" for k, v in self.items())


class Client:
    """Very small subset of the synchronous httpx.Client API."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        headers: Mapping[str, Any] | None = None,
        cookies: Mapping[str, str] | None = None,
        transport: BaseTransport | None = None,
        follow_redirects: bool | UseClientDefault = False,
        **_: Any,
    ) -> None:
        self.base_url = base_url or ""
        self._default_headers = Headers(headers)
        self._transport = transport or BaseTransport()
        self.follow_redirects = follow_redirects
        self.cookies = CookieJar()
        if cookies:
            self.cookies.update(cookies)

    # ------------------------------------------------------------------
    # Context manager helpers
    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

    # ------------------------------------------------------------------
    # Request helpers
    def request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | str | None = None,
        data: Mapping[str, Any] | Iterable[tuple[str, Any]] | bytes | None = None,
        json: Any = None,
        params: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
        headers: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
        cookies: Mapping[str, str] | Iterable[tuple[str, str]] | None = None,
        **_: Any,
    ) -> Response:
        merged_url = self._merge_url(url)
        if params:
            if isinstance(params, Mapping):
                param_items = params.items()
            else:
                param_items = params
            query = urlencode(list(param_items), doseq=True)
            scheme, netloc, path, _, fragment = urlsplit(merged_url.raw)
            merged_url = URL(urlunsplit((scheme, netloc, path, query, fragment)))

        request_headers = self._default_headers.copy()
        if cookies:
            self.cookies.update(cookies)
        if self.cookies:
            request_headers.update({"cookie": "; ".join(f"{k}={v}" for k, v in self.cookies.items())})
        if headers:
            request_headers.update(headers)

        body_data = data
        request = Request(
            method,
            merged_url.raw,
            headers=request_headers,
            content=content,
            data=body_data,
            json_data=json,
        )

        response = self._transport.handle_request(request)
        response.request = request
        return response

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request("HEAD", url, **kwargs)

    # Internal helpers -------------------------------------------------
    def _merge_url(self, url: str | URL) -> URL:
        if isinstance(url, URL):
            return url
        text = str(url)
        if text.startswith(("http://", "https://", "ws://", "wss://")):
            return URL(text)
        if self.base_url:
            merged = urljoin(self.base_url.rstrip("/"), text)
        else:
            merged = text
        return URL(merged)


# ----------------------------------------------------------------------
# Populate the private modules that Starlette expects.
_client = SimpleNamespace(UseClientDefault=UseClientDefault, USE_CLIENT_DEFAULT=USE_CLIENT_DEFAULT)
_types = SimpleNamespace(
    URLTypes=str,
    RequestContent=Any,
    RequestFiles=Any,
    QueryParamTypes=Any,
    HeaderTypes=Any,
    CookieTypes=Any,
    AuthTypes=Any,
    TimeoutTypes=Any,
)

# Expose the helper modules so ``import httpx._client`` works.
import sys as _sys

_sys.modules[__name__ + "._client"] = _client  # type: ignore[assignment]
_sys.modules[__name__ + "._types"] = _types  # type: ignore[assignment]

