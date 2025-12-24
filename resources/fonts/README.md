# Шрифты для иконок

## Обзор

Шрифт Material Design Icons используется для отображения иконок в приложении через `utils/icon_helper.py`. Шрифт встроен в приложение через Qt Resource System (QRC).

## Как получить шрифт Material Design Icons

### Способ 1: Из установленного qtawesome (если есть)

1. Найдите шрифт в установленном пакете:
   ```bash
   python -c "import qtawesome; import os; print(os.path.dirname(qtawesome.__file__) + '/fonts')"
   ```
   - Путь обычно: `site-packages/qtawesome/fonts/materialdesignicons5-webfont-5.9.55.ttf`
   - Или: `site-packages/qtawesome/fonts/materialdesignicons6-webfont-6.9.96.ttf`

2. Скопируйте файл шрифта в эту папку:
   ```
   resources/fonts/materialdesignicons5-webfont-5.9.55.ttf
   ```

### Способ 2: Скачать напрямую

Скачайте шрифт с официального сайта Material Design Icons:
https://materialdesignicons.com/

Рекомендуется использовать версию 5.x для совместимости.

3. Пересоберите QRC:
   ```bash
   py scripts/build_qrc.py
   ```

## Использование

Шрифт загружается автоматически при первом использовании `icon_helper`:
```python
from utils.icon_helper import icon

# Использование иконок
icon("mdi.plus").icon()  # QIcon
icon("mdi.delete").pixmap(24, 24)  # QPixmap
```

**Важно:** Мы НЕ доставали отдельные файлы иконок из qtawesome! Мы:
1. Скопировали только **шрифт** (TTF файл) с символами-иконками
2. Извлекли **Unicode коды** нужных символов из charmap файла qtawesome
3. Используем эти коды для программной отрисовки иконок из шрифта

Это означает, что:
- ✅ Нет зависимости от qtawesome в runtime
- ✅ Иконки отрисовываются из встроенного шрифта
- ✅ Можно легко добавить новые иконки, добавив их коды в `MDI_ICONS`

## Добавление новых иконок

1. Найдите Unicode код нужной иконки в charmap файле Material Design Icons
2. Добавьте запись в `MDI_ICONS` в `utils/icon_helper.py`
3. Пересоберите QRC (если изменили `app.qrc`)

