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


#Секреты в GitHub:

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


## Жесткий Deploy. 

Сейчас Deploy сносит все локальные изменения на vps, качает и запускает то что запушено на git. Поэтому если что-то менялди на vps локально, не забывайте сохранять.
Чтобы указать файлы которые не должны удаляться используейте `-e UR_FILE` в файле `scripts\deploy.sh`
```bash
git fetch origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"
git clean -fd -e .env
```
