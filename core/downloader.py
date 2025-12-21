"""Загрузка и установка SingBox"""
import requests
import zipfile
import shutil
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from config.paths import CORE_DIR, CORE_EXE
from utils.i18n import tr

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)


class DownloadThread(QThread):
    """Поток для загрузки SingBox"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def run(self):
        try:
            # Получаем последний релиз с GitHub
            api_url = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            
            # Ищем Windows x64 архив
            download_url = None
            for asset in release_data.get("assets", []):
                if "windows-amd64" in asset["name"].lower() and asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    break
            
            if not download_url:
                self.finished.emit(False, tr("download.error_not_found"))
                return
            
            # Убеждаемся что папка core существует
            CORE_DIR.mkdir(parents=True, exist_ok=True)
            log_to_file(f"Скачивание ядра в: {CORE_DIR}")
            
            # Скачиваем архив
            self.progress.emit(10)
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            zip_path = CORE_DIR / "sing-box.zip"
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress_pct = 10 + int((downloaded / total_size) * 70)
                            self.progress.emit(progress_pct)
            
            log_to_file(f"Архив скачан: {zip_path} ({zip_path.stat().st_size} байт)")
            self.progress.emit(80)
            
            # Распаковываем
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(CORE_DIR)
            
            log_to_file(f"Архив распакован в: {CORE_DIR}")
            
            # Ищем sing-box.exe в распакованных файлах
            exe_found = False
            for file in CORE_DIR.rglob("sing-box.exe"):
                if file != CORE_EXE:
                    log_to_file(f"Найден sing-box.exe: {file}, перемещаю в {CORE_EXE}")
                    if CORE_EXE.exists():
                        CORE_EXE.unlink()  # Удаляем старый если есть
                    shutil.move(str(file), str(CORE_EXE))
                    exe_found = True
                    break
            
            # Удаляем временные файлы
            zip_path.unlink(missing_ok=True)
            for item in CORE_DIR.iterdir():
                if item.is_dir() and item != CORE_DIR:
                    shutil.rmtree(item, ignore_errors=True)
                elif item.is_file() and item.name != "sing-box.exe":
                    item.unlink(missing_ok=True)
            
            self.progress.emit(100)
            
            if exe_found:
                # Проверяем что файл действительно на месте
                if CORE_EXE.exists():
                    log_to_file(f"Ядро установлено: {CORE_EXE} ({CORE_EXE.stat().st_size} байт)")
                    version = release_data.get("tag_name", "unknown")
                    self.finished.emit(True, tr("download.success_message", version=version))
                else:
                    self.finished.emit(False, tr("download.error_extract"))
            else:
                self.finished.emit(False, tr("download.error_extract"))
                
        except Exception as e:
            self.finished.emit(False, tr("download.error_general", error=str(e)))


