# StatPulse

Plataforma de inteligência esportiva em tempo real (Telegram-first).
Backend reutilizável para Web / Android / iOS / API no futuro.

## Stack
Python 3.13 · FastAPI · SQLAlchemy 2.0 · SQLite · python-telegram-bot · APScheduler · Docker

## Fase 1 — Infraestrutura (atual)
- FastAPI app com `/health`
- SQLite via SQLAlchemy (schema completo em `app/models/`)
- Config tipada (`app/core/config.py`)
- Logging estruturado obrigatório (`app/core/logging.py`)
- Docker + docker-compose

## Como rodar (dev)
```bash
python -m venv .venv && source .venv/bin/activate   # ou: uv venv .venv && . .venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
# abra http://localhost:8000/health
```

## Como rodar o Bot (Fase 2)
```bash
cp .env.example .env
# preencha TELEGRAM_BOT_TOKEN no .env
python -m app.telegram.bot     # ou: statpulse-bot (script instalado)
```

## Como rodar a Coleta (Fase 3)
```bash
cp .env.example .env
# preencha API_FOOTBALL_KEY (RapidAPI) no .env
python -m app.scheduler.worker   # ou: statpulse-worker (script instalado)
# varre partidas ao vivo a cada POLL_INTERVAL_SECONDS e grava eventos no banco
```

## Como rodar (Docker)
```bash
cp .env.example .env
docker compose up --build
```

## Roadmap
F1 Infra → F2 Telegram → F3 Providers → F4 Event Engine → F5 Notification →
F6 Replay → F7 Radar → F8 Heat Check → F9 Dashboard → F10 Mobile.
