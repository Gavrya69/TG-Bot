# Локальное развертнывание без CI\CD

*Учтите что в этом варианте `.env` копируется во внутрь контейнера. Вы можете подать переменные окружения с помощью `--env-file`.*

```bash
CONTAINER_NAME="tg-bot-yt-downloader"
IMAGE_NAME="tg-bot-yt-downloader:latest"

docker build -t "$IMAGE_NAME" .
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  "$IMAGE_NAME"
```

## Cookies (YouTube fallback)

Некоторые ролики YouTube не качаются без cookies. Бот:

1. Сначала пробует обычную загрузку
2. Если не вышло — проверяет `cookies.txt` и качает через cookies
3. Если cookies нет/просрочены — просит обновить через `/load_cookies` в ЛС

Загрузка свежих cookies (любой пользователь, только в ЛС):

1. Экспорт cookies в Netscape-формате (`cookies.txt`)
2. В ЛС боту: `/load_cookies`
3. Прислать файл документом

В Docker нужен **Node.js ≥ 22** (yt-dlp не принимает 20.x) — ставится в образе с nodejs.org.

## Клиенты YouTube

yt-dlp ходит в YouTube от имени клиента. У разных клиентов разные форматы и не у всех есть прямая ссылка на файл.

- `android`, `web`, `tv` сейчас часто оставляют прямую ссылку только на 360p. Остальное уходит в SABR, скачать это нельзя.
- `android_vr` отдаёт прямые ссылки, в том числе AV1 и VP9 выше 1080p. Cookies аккаунта этот клиент не принимает. Часть детских роликов через него не открывается.

Как бот читает ролик:

1. Сначала без cookies, клиент только `android_vr`.
2. Любой YouTube, и Shorts, и `youtu.be`. Берётся самый большой кадр меньше 50 МБ, кодек не важен. Вертикальное 1440p — это 1440×2560, фильтр только по высоте его выкидывает. Если файл больше 50 МБ, шаг вниз по обеим сторонам: 2560, 1920, 1280, 854, 640.
3. H.264 уходит в чат как видео. AV1 и VP9 уходят файлом: плеер Telegram их не показывает, а так кадр не пережимается.
4. Cookies подключаются только если шаг без cookies закончился ошибкой. Клиент при этом не фиксируется: yt-dlp выбирает сам. Так берутся ролики с возрастным ограничением. Успешный первый шаг cookies не трогает.
5. TikTok клиентов YouTube не использует, лестница по высоте прежняя. Лимит видео везде 50 МБ.

# Делаем CI\CD на VPS

Заранее поставьте докер 😁👍, вы же не долбаеб

## Создать папку проекта

```bash
sudo mkdir -p /opt/tg-bot-yt-downloader
sudo chown -R $USER:$USER /opt/tg-bot-yt-downloader
```

## Настроить SSH-ключ для VPS → GitHub

Создаем

```bash
ssh-keygen -t ed25519 -C "vps-deploy-key" -f ~/.ssh/id_ed25519_github
```

чат гпт сказал перезапустить агента по ssh, ну я хз

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github
```

КОПИРУЕМ. Его вставляем в GitHub (Deploy keys)

```bash
cat ~/.ssh/id_ed25519_github.pub
```

‼️ ЭТО НЕ `VPS_SSH_KEY`, это ключ для клонирования репозитория

Создать SSH-конфиг:

```bash
cat > ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github
  IdentitiesOnly yes
EOF
```

Проверить доступ:

```bash
ssh -T git@github.com
```

Ну и клонируем репу. ‼️ **ВНИМАНИЕ НА ТОЧКУ В КОНЦЕ**. НУЖНО СКОПИРОВАТЬ В ТЕКУЩУЮ ДИРЕКТОРИЮ, А ТО ДЕПЛОй УПАДЕТ НАХУЙ. Не забываем перейти в эту папку перед скачиванием.

```bash
cd /opt/tg-bot-yt-downloader
git clone REPO .   
```

в папку  `/opt/tg-bot-yt-downloader`

‼️ НЕ ЗАБЫВАЕМ ПРО `.env`. Пример:`.env.example`

‼️ НЕ ЗАБЫВАЕМ Сделать файл исполняемым:

```bash
chmod +x /opt/tg-bot-yt-downloader/scripts/deploy.sh
```

Теперь создадим ключ для `VPS_SSH_KEY`:

```bash
ssh-keygen -t ed25519 -C "github-actions-vps" -f ~/.ssh/id_ed25519_github_actions
```

Добавим этот ключ в доверенные к подключению

```bash
cat ~/.ssh/id_ed25519_github_actions.pub >> ~/.ssh/authorized_keys
```

Забираем **приватный ключ** и вставляем в секрет `VPS_SSH_KEY`

```bash
cat ~/.ssh/id_ed25519_github_actions
```

# Секреты в GitHub:

- `VPS_HOST` — IP или домен VPS

- `VPS_PORT` — SSH-порт, обычно 22

- `VPS_USER` — пользователь на VPS

- `VPS_SSH_KEY` — приватный SSH-ключ для GitHub Actions

# ‼️ ЭТО СТОИТ ПРОЧИТАТЬ

Ребята, docker какашка. Если вы питонист (боже успаси) то .env можно читать миллионом способов.

Можно подать его при билде контейнера с помощью  `--env-file` (в `scripts\deploy.sh`)

```bash
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  "$IMAGE_NAME"

```

Можно скопировать в `Dockerfile`

```Dockerfile
  COPY .env .env
```

‼️**Делайте что-то одно, у меня деплой падал если сразу все варианты**

## Жесткий Deploy

Сейчас Deploy сносит все локальные изменения на vps, качает и запускает то что запушено на git. Поэтому если что-то менялди на vps локально, не забывайте сохранять.
Чтобы указать файлы которые не должны удаляться используейте `-e UR_FILE` в файле `scripts\deploy.sh`

```bash
git fetch origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"
git clean -fd -e .env
```
