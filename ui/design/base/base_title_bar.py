"""Базовый заголовок окна - компонент из дизайн-системы"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QPoint
from utils.icon_helper import icon
from ui.styles import StyleSheet, theme
from utils.icon_manager import get_icon
from utils.i18n import tr


class BaseTitleBar(QWidget):
    """Фреймлесс-бар с кнопками окна, стилизованный под текущую тему."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self._window = window
        self._drag_pos: QPoint | None = None
        self.setObjectName("titleBar")
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        app_icon = get_icon()
        if app_icon and not app_icon.isNull():
            self.icon_label.setPixmap(app_icon.pixmap(20, 20))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(tr("app.title"))
        self.title_label.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.btn_minimize = QPushButton()
        self.btn_minimize.setObjectName("titleBarMinimize")
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setFixedSize(34, 28)
        self.btn_minimize.clicked.connect(self._window.showMinimized)
        layout.addWidget(self.btn_minimize)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("titleBarClose")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(34, 28)
        self.btn_close.clicked.connect(self._window.close)
        layout.addWidget(self.btn_close)

        self.apply_theme()

    def apply_theme(self):
        """Применяет текущую тему к заголовку."""
        bg = theme.get_color("background_primary")
        border = theme.get_color("border")
        text = theme.get_color("text_primary")
        secondary = theme.get_color("text_secondary")
        hover = theme.get_color("accent_light")
        # Создаем rgba для error hover
        error_color = theme.get_color('error')
        error_hex = error_color.lstrip('#')
        error_r = int(error_hex[0:2], 16)
        error_g = int(error_hex[2:4], 16)
        error_b = int(error_hex[4:6], 16)
        error_hover = f"rgba({error_r}, {error_g}, {error_b}, 0.12)"

        self.setStyleSheet(
            f"""
            QWidget#titleBar {{
                background-color: {bg};
                border: none;
                border-bottom: 1px solid {border};
            }}
            QPushButton#titleBarMinimize, QPushButton#titleBarClose {{
                background-color: transparent;
                border: none;
                border-radius: {theme.get_size('border_radius_small')}px;
            }}
            QPushButton#titleBarMinimize:hover {{
                background-color: {hover};
            }}
            QPushButton#titleBarClose:hover {{
                background-color: {error_hover};
            }}
            """
        )

        self.title_label.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        self.btn_minimize.setIcon(icon("mdi.window-minimize", color=secondary).icon())
        self.btn_close.setIcon(icon("mdi.close", color=text).icon())
        
        # Обновляем иконку приложения в title bar
        app_icon = get_icon()
        if app_icon and not app_icon.isNull():
            self.icon_label.setPixmap(app_icon.pixmap(20, 20))
        
        # Принудительно обновляем весь title bar
        self.update()

    def set_title(self, text: str):
        """Обновляет отображаемый заголовок."""
        self.title_label.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            target = self.childAt(event.pos())
            if target in (self.btn_minimize, self.btn_close):
                return super().mousePressEvent(event)
            self._drag_pos = event.globalPos() - self._window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self._window.move(event.globalPos() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)



