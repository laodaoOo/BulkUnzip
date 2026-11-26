"""纯界面小组件：可省略标签、状态圆点。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class ElidedLabel(QLabel):
    """单行文本，宽度不足时中部省略，悬停显示全文。"""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._full = ""
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setText(text)

    def setText(self, text: str) -> None:
        """记录全文并刷新显示。"""
        self._full = text
        self.setToolTip(text)
        self._refresh()

    def full_text(self) -> str:
        """返回未省略的全文。"""
        return self._full

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        width = max(40, self.width())
        elided = self.fontMetrics().elidedText(
            self._full, Qt.TextElideMode.ElideMiddle, width,
        )
        super().setText(elided)


class StatusDot(QLabel):
    """8px 圆点，用动态属性表达状态颜色。"""

    def __init__(self, state: str = "waiting", parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.setObjectName("statusDot")
        self.setFixedSize(8, 8)
        self.set_state(state)

    def set_state(self, state: str) -> None:
        """切换状态并刷新样式。"""
        if self.property("state") == state:
            return
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)


__all__ = ["ElidedLabel", "StatusDot"]
