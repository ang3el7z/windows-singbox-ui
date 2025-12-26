"""GUI updater for SingBox-UI aligned with current app structure."""

import json
import sys
import time
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Set

import requests
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont

from app.application import create_application
from config.paths import ROOT
from ui.styles import StyleSheet, theme
from ui.design import CardWidget, TitleBar
from ui.design.component import Container, TextEdit, ProgressBar, Button, Label
from utils.i18n import tr, set_language
from managers.settings import SettingsManager

GITHUB_OWNER = "ang3el7z"
GITHUB_REPO = "windows-singbox-ui"
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
        """Получает версию последнего релиза через GitHub API."""
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            tag_name = release_data.get("tag_name", "")
            # Убираем префикс 'v' если есть
            version = tag_name.lstrip("v") if tag_name else None
            return version or None
        except Exception as exc:  # noqa: BLE001
            # Логируем, но не показываем пользователю, это не критично
            return None
    
    def _download_latest_archive(self, dest: Path):
        """Скачивает архив последнего релиза."""
        # Получаем информацию о последнем релизе
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        self.status(tr("updater.connecting_to_server"))
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch release info: {exc}") from exc
        
        # Ищем архив в ассетах релиза
        assets = release_data.get("assets", [])
        archive_url = None
        for asset in assets:
            asset_name = asset.get("name", "").lower()
            # Ищем архив вида windows-singbox-ui-v-*.zip
            if asset_name.startswith("windows-singbox-ui-v-") and asset_name.endswith(".zip"):
                archive_url = asset.get("browser_download_url")
                break
        
        if not archive_url:
            raise RuntimeError("Release archive not found in latest release")
        
        # Скачиваем архив
        self.status(tr("updater.connecting_to_server"))
        response = requests.get(archive_url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        last_logged_mb = 0.0
        log_interval_mb = 10.0  # Логируем раз в 25 МБ
        
        if total_size:
            size_mb = total_size / (1024 * 1024)
            self.status(tr("updater.file_size", size_mb=f"{size_mb:.2f}"))
        
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    progress_pct = 10 + int((downloaded / total_size) * 30)
                    self.progress_signal.emit(min(progress_pct, 40))
                    downloaded_mb = downloaded / (1024 * 1024)
                    # Логируем прогресс только раз в МБ (или при завершении)
                    if downloaded_mb - last_logged_mb >= log_interval_mb or downloaded >= total_size:
                        total_mb = total_size / (1024 * 1024)
                        self.status(tr("updater.downloaded_progress", 
                                     downloaded_mb=f"{downloaded_mb:.2f}",
                                     total_mb=f"{total_mb:.2f}",
                                     progress_pct=progress_pct))
                        last_logged_mb = downloaded_mb
        
        self.status(tr("updater.download_complete"))
    
    def _extract_archive(self, zip_path: Path, extract_dir: Path):
        """Распаковывает скачанный архив."""
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    
    def _find_new_app_dir(self, extract_dir: Path) -> Path:
        """Ищет папку с собранным приложением внутри архива.
        
        Архив из релиза содержит содержимое dist/SingBox-UI/, то есть:
        - SingBox-UI.exe (в корне архива)
        - data/ (с подпапками)
        """
        # Ищем SingBox-UI.exe в распакованном архиве
        candidates = sorted(extract_dir.rglob("SingBox-UI.exe"))
        if not candidates:
            raise FileNotFoundError("SingBox-UI.exe not found in downloaded archive")
        
        # В релизном архиве SingBox-UI.exe должен быть в корне распакованной папки
        # или в одной из подпапок. Возвращаем родительскую папку exe файла.
        exe_path = candidates[0]
        return exe_path.parent
    
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
    def _is_skipped(rel_path: Path, protected: Set[Path], handled_separately: Set[Path]) -> bool:
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
    
    def _cleanup_old_updater_files(self):
        """Удаляет старые .old файлы updater.exe при запуске."""
        app_data_dir = self.app_dir / "data"
        old_updater = app_data_dir / "updater.exe.old"
        if old_updater.exists():
            try:
                old_updater.unlink()
            except Exception:
                pass  # Файл может быть заблокирован, это нормально
    
    def _update_updater_exe(self, new_app_dir: Path) -> int:
        """Обновляет data/updater.exe, включая обновление самого себя."""
        new_updater = new_app_dir / "data" / "updater.exe"
        if not new_updater.exists():
            return 0
        
        app_data_dir = self.app_dir / "data"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        app_updater = app_data_dir / "updater.exe"
        
        try:
            # Если это текущий процесс, используем переименование для обхода блокировки
            is_current_process = False
            try:
                if app_updater.exists() and app_updater.resolve() == Path(sys.executable).resolve():
                    is_current_process = True
            except Exception:
                pass
            
            if is_current_process:
                # Переименовываем старый файл в .old (это работает даже для запущенного процесса)
                old_updater = app_data_dir / "updater.exe.old"
                try:
                    if old_updater.exists():
                        old_updater.unlink()
                except Exception:
                    pass  # Игнорируем ошибки удаления старого .old файла
                
                # Переименовываем текущий updater.exe в .old
                app_updater.rename(old_updater)
                # Копируем новый updater.exe
                shutil.copy2(new_updater, app_updater)
                
                # Пытаемся удалить .old файл (может не получиться, если процесс еще работает - это нормально)
                try:
                    old_updater.unlink()
                except Exception:
                    pass  # Файл заблокирован процессом, будет удален при следующем запуске
            else:
                # Если это не текущий процесс, просто заменяем файл
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
            
            # Очистка старых .old файлов
            self._cleanup_old_updater_files()
            
            # Проверка версии
            self.status(tr("updater.progress_checking"))
            if self.current_version:
                self.status(tr("updater.current_version_label", version=self.current_version))
            self.target_version = self._fetch_remote_version()
            if self.target_version:
                self.status(tr("updater.available_version_label", version=self.target_version))
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
            self.status(tr("updater.extraction_complete"))
            self.progress_signal.emit(55)
            
            new_app_dir = self._find_new_app_dir(extract_dir)
            self._adjust_target_dir_if_needed()
            self.progress_signal.emit(60)
            
            # Остановка процессов
            self.status(tr("updater.progress_stopping"))
            self._stop_processes()
            self.status(tr("updater.processes_stopped"))
            self.progress_signal.emit(65)
            
            # Установка обновления
            self.status(tr("updater.progress_installing"))
            items_updated = self._install_update(new_app_dir)
            self.status(tr("updater.files_updated", count=items_updated))
            self.progress_signal.emit(85)
            
            # Очистка
            self.status(tr("updater.progress_cleaning"))
            self._clean_temp(temp_root)
            self.status(tr("updater.temp_files_cleaned"))
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
        
        # Фреймлесс-режим, чтобы отрисовывать собственный статус-бар
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        self.setWindowTitle("Updater")
        # Фиксированный размер окна - нельзя изменять
        self.setFixedSize(600, 300)
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
        
        central = Container()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Собственный статус-бар в стиле приложения
        self.title_bar = TitleBar(self)
        self.title_bar.set_title("Updater")
        layout.addWidget(self.title_bar)
        
        # Внутренний layout для содержимого
        content_layout = QVBoxLayout()
        # Уменьшенные отступы для компактного окна
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Карточка для окна логов (заголовок теперь в TitleBar)
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)
        
        # Окно логов - показывает что происходит
        self.logs_text = TextEdit()
        self.logs_text.setReadOnly(True)
        # Переопределяем стиль для логов updater
        self.logs_text.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {theme.get_color('background_tertiary')};
                color: {theme.get_color('text_primary')};
                border: none;
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9px;
                selection-background-color: {theme.get_color('accent_light')};
            }}
            """
        )
        card_layout.addWidget(self.logs_text, 1)  # Растягивается на доступное пространство
        
        content_layout.addWidget(card, 1)  # Карточка растягивается
        
        # Прогресс-бар - показывает общий прогресс скачивания и установки (без подложки)
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        content_layout.addWidget(self.progress_bar)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        
        self.done_button = Button(tr("updater.button_done"), variant="primary")
        self.done_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.done_button.clicked.connect(self.close)
        self.done_button.hide()
        
        self.cancel_button = Button(tr("updater.button_cancel"), variant="secondary")
        self.cancel_button.setFont(QFont("Segoe UI", 11))
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.hide()
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.done_button)
        self.button_layout.addWidget(self.cancel_button)
        content_layout.addLayout(self.button_layout)
        
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close)
        self.close_timer.setSingleShot(True)
        
        self.countdown_label = Label("", variant="secondary")
        self.countdown_label.setFont(QFont("Segoe UI", 10))
        self.countdown_label.hide()
        content_layout.addWidget(self.countdown_label)
        
        # Добавляем content_layout в основной layout
        content_widget = Container()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, 1)
        
        self.countdown_seconds = 5
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        QTimer.singleShot(500, self.start_update)
    
    def start_update(self):
        """Запускает процесс обновления."""
        # Очищаем окно логов
        self.logs_text.clear()
        self.logs_text.append(tr("updater.status_ready"))
        self.progress_bar.setValue(0)
        
        self.update_thread = UpdateThread(ROOT)
        self.update_thread.status_signal.connect(self.on_status)
        self.update_thread.progress_signal.connect(self.on_progress)
        self.update_thread.finished_signal.connect(self.on_finished)
        self.update_thread.start()
    
    def on_status(self, text: str):
        """Обновляет текст текущего действия в окне логов."""
        # Добавляем новую строку в окно логов
        self.logs_text.append(text)
        # Автоматически прокручиваем вниз
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
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
            self.logs_text.append(tr("updater.progress_complete"))
            
            self.done_button.show()
            self.cancel_button.show()
            self.countdown_label.show()
            self.countdown_seconds = 5
            self.countdown_label.setText(tr("updater.countdown_close", seconds=self.countdown_seconds))
            self.countdown_timer.start(1000)
            self.close_timer.start(5000)
        else:
            self.logs_text.append(f"{tr('updater.progress_error')}: {message}")
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

