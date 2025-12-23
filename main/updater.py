"""Updater для автоматического обновления SingBox-UI"""
import sys
import time
import shutil
import subprocess
import tempfile
import zipfile
import requests
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# Определяем корневую папку приложения
if getattr(sys, 'frozen', False):
    exe_path = Path(sys.executable)
    if exe_path.parent.name == '_internal':
        ROOT = exe_path.parent.parent
    else:
        ROOT = exe_path.parent
else:
    ROOT = Path(__file__).resolve().parent.parent


class UpdateThread(QThread):
    """Поток для выполнения обновления"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, version, app_dir, repo_owner="ang3el7z", repo_name="windows-singbox-ui"):
        super().__init__()
        self.version = version
        self.app_dir = Path(app_dir)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
    
    def log(self, msg: str):
        """Отправляет сообщение в лог"""
        self.log_signal.emit(msg)
    
    def run(self):
        """Выполняет обновление"""
        try:
            self.log("=" * 60)
            self.log(f"SingBox-UI Updater v{self.version}")
            self.log("=" * 60)
            self.log("")
            
            # Шаг 1: Получаем информацию о релизе
            self.log("[1/6] Getting release information...")
            self.progress_signal.emit(5)
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            
            # Ищем архив с обновлением
            download_url = None
            archive_name = None
            for asset in release_data.get("assets", []):
                if asset["name"].endswith(".zip") and "windows-singbox-ui" in asset["name"].lower():
                    download_url = asset["browser_download_url"]
                    archive_name = asset["name"]
                    break
            
            if not download_url:
                self.finished_signal.emit(False, "Update archive not found")
                return
            
            self.log(f"Found archive: {archive_name}")
            self.progress_signal.emit(10)
            
            # Шаг 2: Скачиваем архив
            self.log("[2/6] Downloading update...")
            temp_dir = Path(tempfile.gettempdir()) / "singbox-ui-update"
            temp_dir.mkdir(exist_ok=True)
            zip_path = temp_dir / archive_name
            
            try:
                response = requests.get(download_url, stream=True, timeout=60)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_logged = 0
                log_interval = 5 * 1024 * 1024  # Логируем каждые 5 МБ
                
                self.log(f"Total size: {total_size / 1024 / 1024:.1f} MB")
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Обновляем прогресс
                            if total_size > 0:
                                progress_pct = 10 + int((downloaded / total_size) * 40)
                                self.progress_signal.emit(progress_pct)
                            
                            # Логируем только каждые 5 МБ
                            if downloaded - last_logged >= log_interval:
                                self.log(f"Downloaded: {downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB")
                                last_logged = downloaded
                
                # Финальное сообщение
                self.log(f"Download complete: {downloaded / 1024 / 1024:.1f} MB")
                self.progress_signal.emit(50)
            except requests.exceptions.RequestException as e:
                self.log(f"Download error: {e}")
                raise Exception(f"Failed to download update: {e}")
            
            # Шаг 3: Распаковываем архив
            self.log("[3/6] Extracting archive...")
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.log(f"Archive extracted to: {extract_dir}")
            self.progress_signal.emit(60)
            
            # Шаг 4: Закрываем основное приложение
            self.log("[4/6] Stopping SingBox-UI application...")
            self.progress_signal.emit(65)
            
            # Закрываем SingBox-UI.exe
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "SingBox-UI.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                self.log("SingBox-UI.exe stopped")
            except Exception as e:
                self.log(f"Warning: Could not stop SingBox-UI.exe: {e}")
            
            # Закрываем sing-box.exe
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "sing-box.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                self.log("sing-box.exe stopped")
            except Exception as e:
                self.log(f"Warning: Could not stop sing-box.exe: {e}")
            
            time.sleep(1)
            self.progress_signal.emit(70)
            
            # Шаг 5: Устанавливаем обновление
            self.log("[5/6] Installing update...")
            self.progress_signal.emit(75)
            
            # Находим папку SingBox-UI в распакованных файлах
            # Важно: ищем в системной temp папке, не в папке приложения
            new_app_dir = None
            for item in extract_dir.iterdir():
                if item.is_dir() and item.name == "SingBox-UI":
                    new_app_dir = item
                    break
            
            if not new_app_dir:
                new_app_dir = extract_dir
            
            # Проверяем, что мы не копируем в папку updater.exe
            updater_dir = Path(sys.executable).parent
            if str(self.app_dir).startswith(str(updater_dir)) and updater_dir.name == "data":
                # Если app_dir находится внутри папки с updater, используем родительскую папку
                self.app_dir = updater_dir.parent
                self.log(f"Adjusted app directory to: {self.app_dir}")
            
            self.log(f"Source directory: {new_app_dir}")
            self.log(f"Target directory: {self.app_dir}")
            
            # Файлы и папки, которые НЕ нужно обновлять (сохраняем пользовательские данные)
            protected_paths = [
                ".subscriptions",
                "core/sing-box.exe",  # Не трогаем ядро
                "logs",  # Не трогаем логи
            ]
            
            def is_protected(dest_path: Path) -> bool:
                """Проверяет, защищен ли путь"""
                dest_str = str(dest_path)
                # Проверяем только пути внутри data/
                if "data" in dest_str:
                    for protected in protected_paths:
                        if protected in dest_str:
                            return True
                return False
            
            # Копируем файлы, пропуская защищенные
            items_copied = 0
            for item in new_app_dir.iterdir():
                # Пропускаем updater.exe в корне (мы уже запущены)
                if item.name == "updater.exe" and item.is_file():
                    continue
                
                dest = self.app_dir / item.name
                
                # Проверяем защиту для корневых элементов
                if is_protected(dest):
                    self.log(f"Skipping protected: {item.name}")
                    continue
                
                try:
                    if item.is_dir():
                        # Для папок используем merge (не удаляем существующие)
                        if dest.exists():
                            # Копируем содержимое, но не удаляем существующее и пропускаем защищенные
                            for subitem in item.rglob("*"):
                                if subitem.is_file():
                                    rel_path = subitem.relative_to(item)
                                    dest_subitem = dest / rel_path
                                    
                                    # Проверяем защиту для каждого файла
                                    if is_protected(dest_subitem):
                                        continue
                                    
                                    dest_subitem.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(subitem, dest_subitem)
                                    items_copied += 1
                        else:
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                            items_copied += 1
                        self.log(f"Updated directory: {item.name}")
                    else:
                        # Для файлов просто копируем
                        if dest.exists():
                            dest.unlink()
                        shutil.copy2(item, dest)
                        items_copied += 1
                        self.log(f"Updated file: {item.name}")
                except Exception as e:
                    self.log(f"Error updating {item.name}: {e}")
            
            # Обновляем updater.exe в data (если есть)
            new_updater = new_app_dir / "data" / "updater.exe"
            if new_updater.exists():
                app_data_dir = self.app_dir / "data"
                app_data_dir.mkdir(parents=True, exist_ok=True)
                app_updater = app_data_dir / "updater.exe"
                if app_updater.resolve() != Path(sys.executable).resolve():
                    if app_updater.exists():
                        app_updater.unlink()
                    shutil.copy2(new_updater, app_updater)
                    self.log("Updated updater.exe in data/")
            
            # Обновляем локали в data/locales (merge, не удаляем пользовательские)
            new_locales = new_app_dir / "data" / "locales"
            if new_locales.exists():
                app_data_locales = self.app_dir / "data" / "locales"
                app_data_locales.mkdir(parents=True, exist_ok=True)
                # Копируем только стандартные локали, не трогаем пользовательские
                for locale_file in new_locales.glob("*.json"):
                    dest_locale = app_data_locales / locale_file.name
                    shutil.copy2(locale_file, dest_locale)
                    self.log(f"Updated locale: {locale_file.name}")
            
            # Обновляем .settings с merge (добавляем новые ключи, сохраняем существующие)
            new_settings = new_app_dir / "data" / ".settings"
            app_settings = self.app_dir / "data" / ".settings"
            if new_settings.exists():
                try:
                    import json
                    # Читаем существующие настройки
                    existing_settings = {}
                    if app_settings.exists():
                        try:
                            with open(app_settings, 'r', encoding='utf-8') as f:
                                existing_settings = json.load(f)
                        except Exception:
                            pass
                    
                    # Читаем новые настройки
                    with open(new_settings, 'r', encoding='utf-8') as f:
                        new_settings_data = json.load(f)
                    
                    # Объединяем: существующие имеют приоритет (не трогаем), новые ключи добавляются
                    merged_settings = {**new_settings_data, **existing_settings}
                    # Это означает: сначала берем новые, потом существующие перезаписывают их
                    # Таким образом существующие настройки сохраняются, а новые ключи добавляются
                    
                    # Сохраняем объединенные настройки
                    app_settings.parent.mkdir(parents=True, exist_ok=True)
                    with open(app_settings, 'w', encoding='utf-8') as f:
                        json.dump(merged_settings, f, indent=2, ensure_ascii=False)
                    
                    self.log("Updated .settings (merged with existing settings)")
                except Exception as e:
                    self.log(f"Warning: Could not merge .settings: {e}")
                    # Если не удалось merge, просто копируем новый файл
                    if app_settings.exists():
                        app_settings.unlink()
                    shutil.copy2(new_settings, app_settings)
                    self.log("Copied new .settings file")
            
            self.log(f"Update installed: {items_copied} items updated")
            self.progress_signal.emit(90)
            
            # Шаг 6: Очистка и запуск
            self.log("[6/6] Cleaning up and starting application...")
            self.progress_signal.emit(95)
            
            # Удаляем временные файлы (из системной temp папки, не из папки приложения)
            try:
                temp_update_dir = Path(tempfile.gettempdir()) / "singbox-ui-update"
                if temp_update_dir.exists():
                    shutil.rmtree(temp_update_dir, ignore_errors=True)
                    self.log("Temporary files cleaned")
            except Exception as e:
                self.log(f"Warning: Could not clean temp files: {e}")
            
            # Запускаем обновленное приложение
            new_exe = self.app_dir / "SingBox-UI.exe"
            if new_exe.exists():
                try:
                    self.log(f"Starting application: {new_exe}")
                    proc = subprocess.Popen([str(new_exe)], cwd=str(self.app_dir))
                    # Даем немного времени на запуск
                    time.sleep(0.5)
                    # Проверяем, что процесс запустился
                    if proc.poll() is None:
                        self.log("Application started successfully!")
                        self.log(f"Process ID: {proc.pid}")
                    else:
                        self.log(f"Warning: Application exited immediately with code {proc.returncode}")
                    self.progress_signal.emit(100)
                    self.finished_signal.emit(True, "Update completed successfully")
                except Exception as e:
                    self.log(f"Error starting application: {e}")
                    import traceback
                    self.log(traceback.format_exc())
                    self.finished_signal.emit(False, f"Failed to start application: {e}")
            else:
                self.log(f"ERROR: SingBox-UI.exe not found at {new_exe}")
                self.finished_signal.emit(False, f"SingBox-UI.exe not found at {new_exe}")
        
        except Exception as e:
            import traceback
            error_msg = f"Error during update: {e}\n{traceback.format_exc()}"
            self.log(error_msg)
            self.finished_signal.emit(False, str(e))


class UpdaterWindow(QMainWindow):
    """Окно updater с GUI в стиле приложения"""
    
    def __init__(self, version=None):
        super().__init__()
        self.version = version
        self.update_thread = None
        
        self.setWindowTitle("SingBox-UI Updater")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f1a;
            }
            QWidget {
                background-color: #0b0f1a;
                color: #e5e9ff;
            }
        """)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Заголовок
        title = QLabel("SingBox-UI Updater")
        title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        layout.addWidget(title)
        
        # Логи
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0,245,212,0.05);
                color: #e5e9ff;
                border-radius: 16px;
                padding: 16px;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.logs, 1)
        
        # Статус
        self.status = QLabel("Ready to update...")
        self.status.setFont(QFont("Segoe UI", 12))
        self.status.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
        layout.addWidget(self.status)
        
        # Кнопки (скрыты до завершения)
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        
        self.done_button = QPushButton("Готово")
        self.done_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.done_button.setStyleSheet("""
            QPushButton {
                background-color: #00f5d4;
                color: #0b0f1a;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #00d4b8;
            }
            QPushButton:pressed {
                background-color: #00b8a0;
            }
        """)
        self.done_button.clicked.connect(self.close)
        self.done_button.hide()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setFont(QFont("Segoe UI", 11))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: #e5e9ff;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                padding: 10px 24px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.2);
            }
        """)
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.hide()
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.done_button)
        self.button_layout.addWidget(self.cancel_button)
        layout.addLayout(self.button_layout)
        
        # Таймер для авто-закрытия
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close)
        self.close_timer.setSingleShot(True)
        self.countdown_label = QLabel("")
        self.countdown_label.setFont(QFont("Segoe UI", 10))
        self.countdown_label.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
        self.countdown_label.hide()
        layout.addWidget(self.countdown_label)
        
        self.countdown_seconds = 5
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        # Запускаем обновление
        QTimer.singleShot(500, self.start_update)
    
    def log(self, msg: str):
        """Добавляет сообщение в лог"""
        self.logs.append(msg)
        # Прокручиваем вниз
        scrollbar = self.logs.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()
    
    def start_update(self):
        """Запускает процесс обновления"""
        try:
            from config.paths import ROOT
        except ImportError:
            # Если config.paths недоступен, определяем ROOT вручную
            if getattr(sys, 'frozen', False):
                exe_path = Path(sys.executable)
                if exe_path.parent.name == '_internal':
                    ROOT = exe_path.parent.parent
                else:
                    ROOT = exe_path.parent
            else:
                ROOT = Path(__file__).resolve().parent
        
        if not self.version:
            # Если версия не передана, определяем сами
            try:
                import requests
                api_url = "https://api.github.com/repos/ang3el7z/windows-singbox-ui/releases/latest"
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                release_data = response.json()
                tag_name = release_data.get("tag_name", "")
                self.version = tag_name.lstrip('v') if tag_name.startswith('v') else tag_name
            except Exception as e:
                self.log(f"ERROR: Could not determine version: {e}")
                self.status.setText("Error: Could not determine version")
                return
        
        self.log(f"Starting update to version {self.version}...")
        self.status.setText(f"Updating to version {self.version}...")
        
        # Создаем поток обновления
        self.update_thread = UpdateThread(self.version, ROOT)
        self.update_thread.log_signal.connect(self.log)
        self.update_thread.progress_signal.connect(self.on_progress)
        self.update_thread.finished_signal.connect(self.on_finished)
        self.update_thread.start()
    
    def on_progress(self, value: int):
        """Обновляет прогресс"""
        self.status.setText(f"Progress: {value}%")
    
    def update_countdown(self):
        """Обновляет таймер обратного отсчета"""
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Окно закроется автоматически через {self.countdown_seconds} сек...")
        else:
            self.countdown_timer.stop()
            self.countdown_label.hide()
            self.close()
    
    def on_finished(self, success: bool, message: str):
        """Обработка завершения обновления"""
        if success:
            self.log("")
            self.log("=" * 60)
            self.log("Update completed successfully!")
            self.log("The application should start automatically.")
            self.log("")
            self.log("Status: OK")
            self.status.setText("Status: OK - Update completed successfully!")
            
            # Показываем кнопки и таймер
            self.done_button.show()
            self.cancel_button.show()
            self.countdown_label.show()
            self.countdown_seconds = 5
            self.countdown_label.setText(f"Окно закроется автоматически через {self.countdown_seconds} сек...")
            
            # Запускаем таймеры
            self.countdown_timer.start(1000)  # Обновляем каждую секунду
            self.close_timer.start(5000)  # Закрываем через 5 секунд
        else:
            self.log("")
            self.log("=" * 60)
            self.log(f"ERROR: {message}")
            self.log("")
            self.log("Status: ERROR - Window will NOT close automatically")
            self.status.setText("Status: ERROR - Window will NOT close automatically")
            self.log("Please check the errors above and close this window manually.")
            # При ошибке кнопки не показываем, окно остается открытым


def main():
    """Основная функция"""
    app = QApplication(sys.argv)
    
    # Получаем версию из аргументов или None
    version = sys.argv[1] if len(sys.argv) > 1 else None
    
    window = UpdaterWindow(version)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
