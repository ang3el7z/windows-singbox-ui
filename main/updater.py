"""GUI updater for SingBox-UI aligned with current app structure."""

import json
import sys
import time
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import requests
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from app.application import create_application
from config.paths import ROOT
from ui.styles import StyleSheet, theme
from utils.i18n import tr, set_language
from managers.settings import SettingsManager

GITHUB_OWNER = "ang3el7z"
GITHUB_REPO = "SingBox-UI"
GITHUB_BRANCH = "main"


def read_version_from_dir(base: Path) -> Optional[str]:
    """Читает версию приложения из папки установки."""
    data_version = base / "data" / ".version"
    if data_version.exists():
        try:
            version = data_version.read_text(encoding="utf-8").strip()
            if version:
                return version
        except Exception:
            pass
    
    root_version = base / ".version"
    if root_version.exists():
        try:
            version = root_version.read_text(encoding="utf-8").strip()
            if version:
                return version
        except Exception:
            pass
    return None


class UpdateThread(QThread):
    """Поток, выполняющий обновление."""
    
    status_signal = pyqtSignal(str)  # Текст текущего действия
    progress_signal = pyqtSignal(int)  # Процент выполнения (0-100)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(
        self,
        app_dir: Path,
        repo_owner: str = GITHUB_OWNER,
        repo_name: str = GITHUB_REPO,
        branch: str = GITHUB_BRANCH,
    ):
        super().__init__()
        self.app_dir = Path(app_dir)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.current_version = read_version_from_dir(self.app_dir)
        self.target_version: Optional[str] = None
    
    def status(self, msg: str):
        """Отправляет статус текущего действия в UI."""
        self.status_signal.emit(msg)
    
    def _fetch_remote_version(self) -> Optional[str]:
        """Читает .version из ветки main."""
        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/.version"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            version = response.text.strip()
            return version or None
        except Exception as exc:  # noqa: BLE001
            # Логируем, но не показываем пользователю, это не критично
            return None
    
    def _download_latest_archive(self, dest: Path):
        """Скачивает архив ветки main."""
        url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/{self.branch}.zip"
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    progress_pct = 10 + int((downloaded / total_size) * 30)
                    self.progress_signal.emit(min(progress_pct, 40))
    
    def _extract_archive(self, zip_path: Path, extract_dir: Path):
        """Распаковывает скачанный архив."""
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    
    def _find_new_app_dir(self, extract_dir: Path) -> Path:
        """Ищет папку с собранным приложением внутри архива."""
        candidates = sorted(extract_dir.rglob("SingBox-UI.exe"))
        if not candidates:
            raise FileNotFoundError("SingBox-UI.exe not found in downloaded archive")
        
        # Отдаем приоритет сборке в dist/SingBox-UI, если она есть
        def sort_key(path: Path):
            parts_lower = [p.lower() for p in path.parts]
            return ("dist" not in parts_lower, len(parts_lower))
        
        candidates.sort(key=sort_key)
        return candidates[0].parent
    
    def _adjust_target_dir_if_needed(self):
        """Корректирует целевую папку, если updater запущен из data/."""
        try:
            updater_dir = Path(sys.executable).parent
            if self.app_dir.resolve().is_relative_to(updater_dir) and updater_dir.name == "data":
                self.app_dir = updater_dir.parent
                self.log(f"Adjusted app directory to: {self.app_dir}")
        except Exception:
            pass
    
    def _stop_processes(self):
        """Останавливает процессы приложения и ядра sing-box."""
        for process in ("SingBox-UI.exe", "sing-box.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", process],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:  # noqa: BLE001
                pass  # Игнорируем ошибки остановки процессов
        time.sleep(1)
    
    @staticmethod
    def _is_skipped(rel_path: Path, protected: set[Path], handled_separately: set[Path]) -> bool:
        """Проверяет, нужно ли пропустить путь при копировании."""
        for protected_path in protected | handled_separately:
            if rel_path == protected_path or rel_path.is_relative_to(protected_path):
                return True
        return False
    
    def _copy_general_files(self, new_app_dir: Path) -> int:
        """Копирует все файлы, кроме защищенных и обрабатываемых отдельно."""
        protected_paths = {
            Path("data/.subscriptions"),
            Path("data/.settings"),
            Path("data/config.json"),
            Path("data/core/sing-box.exe"),
            Path("data/logs"),
        }
        handled_separately = {
            Path("data/locales"),
            Path("data/themes"),
            Path("data/updater.exe"),
        }
        
        items_copied = 0
        for src in new_app_dir.rglob("*"):
            if src.is_dir():
                continue
            rel_path = src.relative_to(new_app_dir)
            if self._is_skipped(rel_path, protected_paths, handled_separately):
                continue
            
            dest = self.app_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                if dest.exists():
                    dest.unlink()
                shutil.copy2(src, dest)
                items_copied += 1
            except Exception:  # noqa: BLE001
                pass  # Продолжаем обновление даже при ошибках отдельных файлов
        return items_copied
    
    def _copy_locales(self, new_app_dir: Path) -> int:
        """Обновляет локали в data/locales."""
        locales_src = new_app_dir / "data" / "locales"
        if not locales_src.exists():
            return 0
        
        locales_dest = self.app_dir / "data" / "locales"
        locales_dest.mkdir(parents=True, exist_ok=True)
        
        items_copied = 0
        for locale_file in locales_src.glob("*.json"):
            dest = locales_dest / locale_file.name
            shutil.copy2(locale_file, dest)
            items_copied += 1
        return items_copied
    
    def _copy_themes(self, new_app_dir: Path) -> int:
        """Обновляет темы в data/themes (не удаляя пользовательские)."""
        themes_src = new_app_dir / "data" / "themes"
        if not themes_src.exists():
            return 0
        
        themes_dest = self.app_dir / "data" / "themes"
        themes_dest.mkdir(parents=True, exist_ok=True)
        
        items_copied = 0
        for theme_file in themes_src.glob("*.json"):
            dest = themes_dest / theme_file.name
            shutil.copy2(theme_file, dest)
            items_copied += 1
        return items_copied
    
    def _merge_settings(self, new_app_dir: Path):
        """Объединяет файл .settings, сохраняя пользовательские значения."""
        new_settings = new_app_dir / "data" / ".settings"
        app_settings = self.app_dir / "data" / ".settings"
        if not new_settings.exists():
            return
        
        try:
            # Читаем существующие настройки пользователя (они имеют приоритет)
            existing_settings = {}
            if app_settings.exists():
                try:
                    existing_settings = json.loads(app_settings.read_text(encoding="utf-8"))
                except Exception:
                    existing_settings = {}
            
            # Читаем новые настройки из обновления
            try:
                new_settings_data = json.loads(new_settings.read_text(encoding="utf-8"))
            except Exception:
                return  # Если не можем прочитать новые настройки, оставляем старые
            
            # Объединяем: сначала новые (базовые), потом существующие (пользовательские перезаписывают)
            # Это сохраняет пользовательские настройки (язык, тема, и т.д.)
            merged = {**new_settings_data, **existing_settings}
            
            app_settings.parent.mkdir(parents=True, exist_ok=True)
            app_settings.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            # В случае ошибки просто не трогаем существующие настройки
            pass
    
    def _update_updater_exe(self, new_app_dir: Path) -> int:
        """Обновляет data/updater.exe, если это не текущий исполняемый файл."""
        new_updater = new_app_dir / "data" / "updater.exe"
        if not new_updater.exists():
            return 0
        
        app_data_dir = self.app_dir / "data"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        app_updater = app_data_dir / "updater.exe"
        
        try:
            if app_updater.resolve() == Path(sys.executable).resolve():
                return 0
        except Exception:
            pass
        
        try:
            if app_updater.exists():
                app_updater.unlink()
            shutil.copy2(new_updater, app_updater)
            return 1
        except Exception:  # noqa: BLE001
            return 0
    
    def _install_update(self, new_app_dir: Path) -> int:
        """Устанавливает обновление."""
        items_copied = 0
        
        self.status(tr("updater.progress_updating_files"))
        items_copied += self._copy_general_files(new_app_dir)
        self.progress_signal.emit(70)
        
        self.status(tr("updater.progress_updating_locales"))
        items_copied += self._copy_locales(new_app_dir)
        self.progress_signal.emit(75)
        
        self.status(tr("updater.progress_updating_themes"))
        items_copied += self._copy_themes(new_app_dir)
        self.progress_signal.emit(80)
        
        self._update_updater_exe(new_app_dir)
        self.progress_signal.emit(82)
        
        self.status(tr("updater.progress_merging_settings"))
        self._merge_settings(new_app_dir)
        self.progress_signal.emit(85)
        
        return items_copied
    
    def _clean_temp(self, temp_root: Path):
        """Удаляет временные файлы."""
        try:
            shutil.rmtree(temp_root, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
    
    def _start_application(self):
        """Запускает обновленное приложение."""
        new_exe = self.app_dir / "SingBox-UI.exe"
        if not new_exe.exists():
            raise FileNotFoundError(f"SingBox-UI.exe not found at {new_exe}")
        
        try:
            subprocess.Popen([str(new_exe)], cwd=str(self.app_dir))
            time.sleep(0.5)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to start application: {exc}") from exc
    
    def run(self):
        """Основной цикл обновления."""
        temp_root = Path(tempfile.mkdtemp(prefix="singbox-ui-update-"))
        try:
            self.progress_signal.emit(0)
            
            # Проверка версии
            self.status(tr("updater.progress_checking"))
            self.target_version = self._fetch_remote_version()
            self.progress_signal.emit(5)
            
            # Загрузка
            self.status(tr("updater.progress_downloading"))
            zip_path = temp_root / "singbox-ui-latest.zip"
            self._download_latest_archive(zip_path)
            self.progress_signal.emit(40)
            
            # Распаковка
            self.status(tr("updater.progress_extracting"))
            extract_dir = temp_root / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            self._extract_archive(zip_path, extract_dir)
            self.progress_signal.emit(55)
            
            new_app_dir = self._find_new_app_dir(extract_dir)
            self._adjust_target_dir_if_needed()
            self.progress_signal.emit(60)
            
            # Остановка процессов
            self.status(tr("updater.progress_stopping"))
            self._stop_processes()
            self.progress_signal.emit(65)
            
            # Установка обновления
            self.status(tr("updater.progress_installing"))
            items_updated = self._install_update(new_app_dir)
            self.progress_signal.emit(85)
            
            # Очистка
            self.status(tr("updater.progress_cleaning"))
            self._clean_temp(temp_root)
            self.progress_signal.emit(90)
            
            # Запуск приложения
            self.status(tr("updater.progress_starting"))
            self._start_application()
            self.progress_signal.emit(100)
            self.finished_signal.emit(True, tr("updater.progress_complete"))
        except Exception as exc:  # noqa: BLE001
            self.finished_signal.emit(False, str(exc))
        finally:
            if temp_root.exists():
                self._clean_temp(temp_root)


class UpdaterWindow(QMainWindow):
    """GUI окно updater с актуальной темой приложения."""
    
    def __init__(self):
        super().__init__()
        self.update_thread: Optional[UpdateThread] = None
        
        self.setWindowTitle(tr("updater.title"))
        self.setMinimumSize(640, 520)
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {theme.get_color('background_primary')};
            }}
            QWidget {{
                background-color: {theme.get_color('background_primary')};
                color: {theme.get_color('text_primary')};
            }}
            """
        )
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel(tr("updater.title"))
        title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        title.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(title)
        
        # Статус текущего действия
        self.status_label = QLabel(tr("updater.status_ready"))
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.status_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        layout.addWidget(self.status_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {theme.get_color('border')};
                border-radius: 8px;
                text-align: center;
                background-color: {theme.get_color('background_secondary')};
                color: {theme.get_color('text_primary')};
                font-family: {theme.get_font('family')};
                font-size: 11px;
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {theme.get_color('accent')};
                border-radius: 7px;
            }}
            """
        )
        layout.addWidget(self.progress_bar)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        
        self.done_button = QPushButton(tr("updater.button_done"))
        self.done_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.done_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme.get_color('accent')};
                color: {theme.get_color('background_primary')};
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                min-width: 110px;
                font-family: {theme.get_font('family')};
                font-weight: {theme.get_font('weight_semibold')};
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_hover')};
            }}
            """
        )
        self.done_button.clicked.connect(self.close)
        self.done_button.hide()
        
        self.cancel_button = QPushButton(tr("updater.button_cancel"))
        self.cancel_button.setFont(QFont("Segoe UI", 11))
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme.get_color('background_secondary')};
                color: {theme.get_color('text_primary')};
                border: 1px solid {theme.get_color('border')};
                border-radius: 8px;
                padding: 10px 24px;
                min-width: 110px;
                font-family: {theme.get_font('family')};
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_light')};
                border-color: {theme.get_color('border_hover')};
            }}
            """
        )
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.hide()
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.done_button)
        self.button_layout.addWidget(self.cancel_button)
        layout.addLayout(self.button_layout)
        
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close)
        self.close_timer.setSingleShot(True)
        
        self.countdown_label = QLabel("")
        self.countdown_label.setFont(QFont("Segoe UI", 10))
        self.countdown_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        self.countdown_label.hide()
        layout.addWidget(self.countdown_label)
        
        self.countdown_seconds = 5
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        QTimer.singleShot(500, self.start_update)
    
    def start_update(self):
        """Запускает процесс обновления."""
        self.status_label.setText(tr("updater.status_ready"))
        self.progress_bar.setValue(0)
        
        self.update_thread = UpdateThread(ROOT)
        self.update_thread.status_signal.connect(self.on_status)
        self.update_thread.progress_signal.connect(self.on_progress)
        self.update_thread.finished_signal.connect(self.on_finished)
        self.update_thread.start()
    
    def on_status(self, text: str):
        """Обновляет текст текущего действия."""
        self.status_label.setText(text)
        QApplication.processEvents()
    
    def on_progress(self, value: int):
        """Обновляет прогресс-бар."""
        self.progress_bar.setValue(value)
        QApplication.processEvents()
    
    def update_countdown(self):
        """Обработчик обратного отсчета закрытия окна."""
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(tr("updater.countdown_close", seconds=self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.hide()
            self.close()
    
    def on_finished(self, success: bool, message: str):
        """Обработка завершения обновления."""
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(tr("updater.progress_complete"))
            
            self.done_button.show()
            self.cancel_button.show()
            self.countdown_label.show()
            self.countdown_seconds = 5
            self.countdown_label.setText(tr("updater.countdown_close", seconds=self.countdown_seconds))
            self.countdown_timer.start(1000)
            self.close_timer.start(5000)
        else:
            self.status_label.setText(tr("updater.progress_error"))
            self.progress_bar.setValue(0)
            # При ошибке не закрываем окно автоматически
    

def main():
    """Точка входа в updater."""
    # Создаем приложение с применением темы
    app = create_application()
    
    # Загружаем настройки и устанавливаем язык ДО создания UI
    settings = SettingsManager()
    language = settings.get("language", "")
    if language:
        try:
            set_language(language)
        except Exception:
            # Если не удалось загрузить язык, используем английский по умолчанию
            set_language("en")
    else:
        # Если язык не выбран, используем английский по умолчанию
        set_language("en")
    
    window = UpdaterWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

