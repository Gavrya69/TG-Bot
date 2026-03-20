## Делаем CI\CD на VPS

Заранее поставьте докер 😁👍, вы же не долбаеб

# Создать папку проекта

```bash
sudo mkdir -p /opt/tg-bot-yt-downloader
sudo chown -R $USER:$USER /opt/tg-bot-yt-downloader
```

# Настроить SSH-ключ для VPS → GitHub

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

Ну и клонируем репу. ‼️ **ВНИМАНИЕ НА ТОЧКУ В КОНЦЕ**. НУЖНО СКОПИРОВАТЬ В ТЕКУЩУЮ ДИРЕКТОРИЮ, А ТО ДЕПЛОЦ УПАДЕТ НАХУЙ
```bash
git clone REPO .   
``` 
с папку  `/opt/tg-bot-yt-downloader`

‼️ НЕ ЗАБЫВАЕМ ПРО `.env`. Пример:`.env.example`

‼️ НЕ ЗАБЫВАЕМ Сделать файл исполняемым:

```bash
chmod +x /opt/tg-bot-yt-downloader/scripts/deploy.sh
```

Теперь создадим ключ для `VPS_SSH_KEY`:

```bash
    ssh-keygen -t ed25519 -C "github-actions-vps" -f ~/.ssh/id_ed25519_actions
```

Забираем *приватный ключ* и вставляем в секрет `VPS_SSH_KEY`

```bash
cat ~/.ssh/id_ed25519_actions
```


Секреты в GitHub:

- `VPS_HOST` — IP или домен VPS

- `VPS_PORT` — SSH-порт, обычно 22

- `VPS_USER` — пользователь на VPS

- `VPS_SSH_KEY` — приватный SSH-ключ для GitHub Actions

