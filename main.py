import sys
import os
from pathlib import Path
import random
import webbrowser
import json

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFrame,
    QGroupBox,
    QLabel,
    QButtonGroup,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QFont, QIcon

from HACommunicator import HACommunicator


class MovableLamp(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setFixedSize(30, 60)

        self.icon_label = QLabel("💡", self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setGeometry(0, 0, 30, 60)

        font = QFont()
        font.setPointSize(24)
        self.icon_label.setFont(font)

        self.position = (0, 0)

        self.icon_label.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                border: none;
            }
            """
        )

        self.text_label = QLabel(text, parent)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)

        self.text_label.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 10px;
            }
            """
        )

        self.text_label.setGeometry(0, 60, 150, 20)
        self.text_label.show()

        self.drag_start_pos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            diff = event.position().toPoint() - self.drag_start_pos
            new_pos = self.pos() + diff
            parent = self.parentWidget()

            if parent is not None:
                if hasattr(parent, "image_rect") and parent.image_rect is not None:
                    r = parent.image_rect
                    min_x = r.left()
                    max_x = r.left() + r.width() - self.width()
                    min_y = r.top()
                    max_y = r.top() + r.height() - self.height()
                else:
                    min_x = 0
                    max_x = parent.width() - self.width()
                    min_y = 0
                    max_y = parent.height() - self.height()

                x = max(min_x, min(new_pos.x(), max_x))
                y = max(min_y, min(new_pos.y(), max_y))
                self.move(x, y)

        super().mouseMoveEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)

        if self.text_label is not None:
            x = self.x() + self.width() // 2 - self.text_label.width() // 2
            y = self.y() + self.height()
            self.text_label.move(x, y)

    def closeEvent(self, event):
        if self.text_label is not None:
            self.text_label.deleteLater()

        super().closeEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parentWidget()

            if parent is not None and hasattr(parent, "map_widget_center_to_screen"):
                result = parent.map_widget_center_to_screen(self)

                if result is not None:
                    px, py = result
                    # print(f'Bulb "{self.text_label.text()}" Pixel: ({px}, {py})')
                    # pyautogui.moveTo(px, py)
                    self.position = (px, py)

        super().mouseReleaseEvent(event)


class LogoCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #000000;
                border: 2px solid #666;
            }
            """
        )

        self.pixmap = self.capture_screenshot()
        self.scaled_pixmap = None
        self.image_rect = None
        self.logos = []

    def capture_screenshot(self):
        screen = QApplication.primaryScreen()

        if screen is None:
            pm = QPixmap(640, 360)
            pm.fill(Qt.GlobalColor.darkGray)
            return pm

        pm = screen.grabWindow(0)

        if pm.isNull():
            pm = QPixmap(640, 360)
            pm.fill(Qt.GlobalColor.darkGray)

        return pm

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.pixmap is not None:
            self.scaled_pixmap = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            x = (self.width() - self.scaled_pixmap.width()) // 2
            y = (self.height() - self.scaled_pixmap.height()) // 2

            self.image_rect = self.scaled_pixmap.rect().translated(x, y)

        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        if self.scaled_pixmap is not None and self.image_rect is not None:
            painter.drawPixmap(self.image_rect.topLeft(), self.scaled_pixmap)

    def set_logos(self, texts):
        n = len(texts)

        if len(self.logos) > n:
            for logo in self.logos[n:]:
                logo.close()
            self.logos = self.logos[:n]

        elif len(self.logos) < n:
            for _ in range(n - len(self.logos)):
                logo = MovableLamp("", self)

                if self.image_rect is not None:
                    min_x = self.image_rect.left()
                    max_x = self.image_rect.left() + self.image_rect.width() - logo.width()
                    min_y = self.image_rect.top()
                    max_y = self.image_rect.top() + self.image_rect.height() - logo.height()

                    if max_x < min_x:
                        max_x = min_x
                    if max_y < min_y:
                        max_y = min_y

                    x = random.randint(min_x, max_x) if max_x > min_x else min_x
                    y = random.randint(min_y, max_y) if max_y > min_y else min_y
                else:
                    max_x = max(0, self.width() - logo.width())
                    max_y = max(0, self.height() - logo.height())
                    x = random.randint(0, max_x) if max_x > 0 else 0
                    y = random.randint(0, max_y) if max_y > 0 else 0

                logo.move(x, y)
                logo.show()
                self.logos.append(logo)

        for logo, text in zip(self.logos, texts):
            logo.text_label.setText(text)

    def map_widget_center_to_screen(self, widget):
        if self.pixmap is None or self.image_rect is None or self.scaled_pixmap is None:
            return None

        cx = widget.x() + widget.width() / 2.0
        cy = widget.y() + widget.height() / 2.0

        rel_x = (cx - self.image_rect.left()) / float(self.image_rect.width())
        rel_y = (cy - self.image_rect.top()) / float(self.image_rect.height())
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))

        dpr = self.pixmap.devicePixelRatio()
        screen_w = self.pixmap.width() * dpr
        screen_h = self.pixmap.height() * dpr

        px = int(round(rel_x * screen_w))
        py = int(round(rel_y * screen_h))
        return px, py


class ToggleButton(QPushButton):
    def __init__(self, text="Activate", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(40)
        self.setStyleSheet(self.style_off())

        self.clicked.connect(self.update_style)

        self.status = False

    def update_style(self):
        if self.isChecked():
            self.setStyleSheet(self.style_on())
            self.status = True
        else:
            self.setStyleSheet(self.style_off())
            self.status = False

    def style_on(self):
        return """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            font-size: 16px;
        }
        QPushButton:hover {
            border: 1px solid #eb5e28;
        }
        """

    def style_off(self):
        return """
        QPushButton {
            background-color: #403d39;
            color: white;
            border-radius: 8px;
            font-size: 16px;
        }
        QPushButton:hover {
            border: 1px solid #eb5e28;
        }
        """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Openhome Sync")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(900, 450)
        self.setStyleSheet("background-color: #131515;")

        self.base_dir = Path(os.getenv("APPDATA", Path.home())) / "OpenhomeSync"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.save_path = self.base_dir / "save.dat"

        self.timer = QTimer()
        self.timer.setInterval(100)

        self.timer.timeout.connect(self.update_light)

        self.dynamic_rows = []
        self.lamp_status = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        top_layout = QHBoxLayout()

        self.input1 = QLineEdit()
        self.input1.setPlaceholderText("https://your.ip.or.domain:8123")
        self.input2 = QLineEdit()
        self.input2.setPlaceholderText("Your token")
        for inp in (self.input1, self.input2):
            inp.setStyleSheet(
                """
                QLineEdit {
                    background-color: #403d39;
                    border-radius: 3px;
                }

                QLineEdit:focus {
                    border: 1px solid #eb5e28;
                    border-radius: 3px;
                }
                """
            )

        top_layout.addWidget(self.input1)
        top_layout.addWidget(self.input2)
        left_layout.addLayout(top_layout)

        self.input1.textChanged.connect(self.refresh_logos)
        self.input2.textChanged.connect(self.refresh_logos)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        left_layout.addWidget(line)

        self.dynamic_layout = QVBoxLayout()
        left_layout.addLayout(self.dynamic_layout)

        self.add_dynamic_row()

        left_layout.addStretch()

        select_group = QGroupBox("Mode Selector")
        select_layout = QHBoxLayout()

        self.mode_btn1 = QPushButton("Screen Mode")
        self.mode_btn2 = QPushButton("Average Mode")
        self.mode_btn3 = QPushButton("Crazy Mode")

        for btn in (self.mode_btn1, self.mode_btn2, self.mode_btn3):
            btn.setCheckable(True)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(120)
            btn.setStyleSheet(
                """
                QPushButton {
                    padding: 15px;
                    font-size: 16px;
                    border-radius: 4px;
                    background-color: #403d39;
                }
                QPushButton:checked {
                    border: 1px solid #eb5e28;
                    background-color: #252422;
                }
                """
            )
            select_layout.addWidget(btn)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.mode_btn1, 1)
        self.mode_group.addButton(self.mode_btn2, 2)
        self.mode_group.addButton(self.mode_btn3, 3)
        self.mode_btn1.setChecked(True)

        select_group.setLayout(select_layout)
        left_layout.addWidget(select_group)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        top_layout2 = QHBoxLayout()
        self.SAVE = QPushButton("SAVE")
        self.SAVE.clicked.connect(self.save_click)

        self.LOAD = QPushButton("LOAD")
        self.LOAD.clicked.connect(self.load_click)

        self.HELP = QPushButton("HELP")
        self.HELP.clicked.connect(self.help_click)

        for inp in (self.SAVE, self.LOAD, self.HELP):
            inp.setStyleSheet(
                """
                QPushButton {
                    padding: 15px;
                    font-size: 16px;
                    border-radius: 4px;
                    background-color: #403d39;
                }
                QPushButton:hover {
                    border: 1px solid #eb5e28;
                    background-color: #252422;
                }
                """
            )

        top_layout2.addWidget(self.SAVE)
        top_layout2.addWidget(self.LOAD)
        top_layout2.addWidget(self.HELP)
        right_layout.addLayout(top_layout2)

        self.logo_canvas = LogoCanvas()
        right_layout.addWidget(self.logo_canvas)

        self.toggle_btn = ToggleButton("START")
        right_layout.addWidget(self.toggle_btn)

        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 1)

        self.refresh_logos()
        self.timer.start()

    def update_light(self):
        HAComm = HACommunicator(self.input1.text(), self.input2.text(), self.collect_all_inputs(),
                                self.toggle_btn.status, self)

        if self.mode_btn1.isChecked():
            HAComm.screen_mode(self.logo_canvas.logos)
        if self.mode_btn2.isChecked():
            HAComm.average_mode()
        if self.mode_btn3.isChecked():
            HAComm.crazy_mode()

    def help_click(self):
        webbrowser.open("https://github.com/Butter-mit-Brot/Openhome-Sync")

    def save_click(self):
        save_dialog = QMessageBox()
        save_dialog.setText("Credentials and Lamps Saved Successfully!")
        save_dialog.setWindowTitle("Saved Successfully!")
        save_dialog.setIcon(QMessageBox.Icon.Information)

        save_dialog.exec()

        credentials = (self.input1.text(), self.input2.text())
        values = [e.text().strip() for _, e in self.dynamic_rows if e.text().strip()]

        with self.save_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"credentials": credentials, "lamps": values}, indent=4))

    def load_click(self):
        try:
            with self.save_path.open("r", encoding="utf-8") as f:
                js_load = json.load(f)
        except FileNotFoundError:
            return

        credentials = js_load["credentials"]
        self.input1.setText(credentials[0])
        self.input2.setText(credentials[1])

        lamps = js_load["lamps"]
        for w, e in self.dynamic_rows:
            w.setParent(None)
            w.deleteLater()
        self.dynamic_rows.clear()

        for text in lamps:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)

            line_edit = QLineEdit()
            line_edit.setPlaceholderText("Your device ID...")
            line_edit.setText(text)
            line_edit.textChanged.connect(self.refresh_logos)
            line_edit.setStyleSheet(
                """
                QLineEdit {
                    background-color: #403d39;
                    border-radius: 3px;
                }

                QLineEdit:focus {
                    border: 1px solid #eb5e28;
                    border-radius: 3px;
                }
                """
            )

            plus_button = QPushButton("+")
            plus_button.setFixedWidth(30)
            plus_button.clicked.connect(self.add_dynamic_row)

            delete_button = QPushButton("–")
            delete_button.setFixedWidth(30)
            delete_button.clicked.connect(
                lambda checked=False, w=row_widget, e=line_edit: self.delete_dynamic_row(w, e)
            )

            for btn in (plus_button, delete_button):
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #403d39;
                    }
                    QPushButton:hover {
                        border: 0.5px solid #eb5e28;
                        border-radius: 7px;
                        background-color: #252422;
                    }
                    """
                )

            row_layout.addWidget(line_edit)
            row_layout.addWidget(plus_button)
            row_layout.addWidget(delete_button)

            self.dynamic_layout.addWidget(row_widget)
            self.dynamic_rows.append((row_widget, line_edit))

        if not lamps:
            self.add_dynamic_row()

        self.refresh_logos()

    def clear_all_dynamic_rows(self):
        for row_widget, line_edit in self.dynamic_rows:
            row_widget.setParent(None)
            row_widget.deleteLater()
        self.dynamic_rows.clear()
        self.add_dynamic_row()
        self.refresh_logos()

    def add_dynamic_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Your device ID...")
        line_edit.textChanged.connect(self.refresh_logos)
        line_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #403d39;
                border-radius: 3px;
            }

            QLineEdit:focus {
                border: 1px solid #eb5e28;
                border-radius: 3px;
            }
            """
        )

        plus_button = QPushButton("+")
        plus_button.setFixedWidth(30)
        plus_button.clicked.connect(self.add_dynamic_row)

        delete_button = QPushButton("–")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(
            lambda checked=False, w=row_widget, e=line_edit: self.delete_dynamic_row(w, e)
        )

        for btn in (plus_button, delete_button):
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #403d39;
                }
                QPushButton:hover {
                    border: 0.5px solid #eb5e28;
                    border-radius: 7px;
                    background-color: #252422;
                }
                """
            )

        row_layout.addWidget(line_edit)
        row_layout.addWidget(plus_button)
        row_layout.addWidget(delete_button)

        self.dynamic_layout.addWidget(row_widget)
        self.dynamic_rows.append((row_widget, line_edit))
        self.refresh_logos()

    def delete_dynamic_row(self, row_widget, line_edit):
        if len(self.dynamic_rows) <= 1:
            line_edit.clear()
            self.refresh_logos()
            return

        self.dynamic_rows = [(w, e) for (w, e) in self.dynamic_rows if w is not row_widget]
        self.dynamic_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        self.refresh_logos()

    def collect_all_inputs(self):
        values = []
        for row_widget, edit in self.dynamic_rows:
            t = edit.text().strip()
            if t:
                values.append(t)
        return values

    def refresh_logos(self):
        if not hasattr(self, "logo_canvas") or self.logo_canvas is None:
            return
        values = self.collect_all_inputs()
        self.logo_canvas.set_logos(values)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
