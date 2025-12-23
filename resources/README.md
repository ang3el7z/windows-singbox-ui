# Qt Resource System (QRC) для иконок

## Обзор

Иконка приложения теперь зашита в код через Qt Resource System (QRC), а не копируется как отдельный файл. Это гарантирует, что иконка всегда доступна внутри приложения, независимо от структуры файлов.

## Структура

```
resources/
 ├── app.qrc          # Описание ресурсов Qt
 └── icons/
     └── app.ico      # Иконка приложения
```

## Компиляция QRC

QRC файл компилируется в Python модуль `resources_rc.py` в корне проекта.

### Автоматическая компиляция

При сборке через PyInstaller (`.spec` файл) QRC автоматически компилируется, если `resources_rc.py` отсутствует.

### Ручная компиляция

Если нужно скомпилировать вручную:

```bash
# Windows
py -m PyQt5.pyrcc_main resources/app.qrc -o resources_rc.py

# Или через скрипт
py scripts/build_qrc.py
```

## Использование

Иконка загружается через `IconManager`:

```python
from utils.icon_manager import get_icon, set_application_icon, set_window_icon

# Получить иконку
icon = get_icon()

# Установить для приложения
set_application_icon(app)

# Установить для окна
set_window_icon(window)
```

Внутри `IconManager` используется путь Qt Resource:
```python
QIcon(":/icons/app.ico")
```

## Важно

1. **`resources_rc.py` должен быть скомпилирован** перед запуском приложения
2. **Иконка НЕ добавляется в `datas`** в `.spec` файле - она зашита через QRC
3. **`resources_rc` добавлен в `hiddenimports`** в `.spec` для PyInstaller
4. **Иконка для exe-файла** (`icon=` в EXE) остается отдельной - это иконка самого exe в проводнике

## Преимущества

✅ Иконка всегда доступна внутри приложения  
✅ Не зависит от структуры файлов после распаковки  
✅ Один источник истины для иконки  
✅ Правильная работа с AppUserModelID в Windows  
✅ Production-ready решение

