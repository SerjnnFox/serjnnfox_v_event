# v-event.ru — сайт свадебного агентства Vinogradova Event

Статический сайт без зависимостей. Тексты — в `build.py`, свадьбы — в `data/cases.json`, фото — в `assets/img/`.

## Как править
- Тексты страниц: `build.py` (функции `build_home`, `build_dubai` и т. д.).
- Добавить свадьбу: запись в `data/cases.json` + папка `assets/img/cases/<slug>/` (`cover.webp`, `cover-sm.webp`, `01.webp`, `01-sm.webp`, …) и строка в `data/images.json`.
- Стили: `src/assets/css/style.css`, скрипты: `src/assets/js/main.js`.

## Сборка и просмотр
```bash
python3 build.py --serve
```
Откройте http://localhost:8000.

## Публикация
Каждый push в `main` собирает сайт и выкладывает его на GitHub Pages (`.github/workflows/pages.yml`).
В настройках репозитория: Settings → Pages → Source: **GitHub Actions**.

## Заявки с форм
По умолчанию форма открывает WhatsApp с заполненным текстом заявки.
Чтобы получать заявки на почту, укажите URL формы Formspree / Web3Forms в `FORM_ENDPOINT` в `build.py`.

## Фото со старого сайта
`python3 scripts/fetch_images.py` — скачивает фотографии со старого сайта на Tilda, уменьшает и сохраняет в WebP.
