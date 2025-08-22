from __future__ import annotations

import types


class StreamlitStub(types.ModuleType):
    """Lightweight stub for the ``streamlit`` module."""

    def __init__(self) -> None:
        super().__init__("streamlit")
        self.calls: list[tuple[str, object]] = []

    def set_page_config(self, **kwargs) -> None:  # pragma: no cover - trivial
        self.calls.append(("set_page_config", kwargs))

    def title(self, text: str) -> None:
        self.calls.append(("title", text))

    def line_chart(self, data) -> None:  # pragma: no cover - data inspected in tests
        self.calls.append(("line_chart", data))

    def write(self, text: str) -> None:
        self.calls.append(("write", text))

    def markdown(self, text: str) -> None:
        self.calls.append(("markdown", text))

    def metric(self, label: str, value) -> None:  # pragma: no cover - simple
        self.calls.append(("metric", label, value))

    def subheader(self, text: str) -> None:
        self.calls.append(("subheader", text))

    def dataframe(self, data) -> None:  # pragma: no cover - data inspected in tests
        self.calls.append(("dataframe", data))

    def error(self, text: str) -> None:
        self.calls.append(("error", text))
