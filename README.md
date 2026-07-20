# Manhwa Bot

Telegram bot for manhwa/anime content delivery.

## Deployment on Render (Webhook Mode)

This bot uses **webhook mode** instead of polling, which is the recommended approach for production deployment on platforms like Render.

### Prerequisites

1. A Telegram Bot Token (from @BotFather)
2. A Render account (https://render.com)

### Setup Steps on Render

1. **Create a New Web Service** on Render
   - Connect your GitHub repository
   - Choose the `manhwa_bot` repository

2. **Configure Build Settings**
   - **Runtime**: Docker
   - **Docker Command**: `python main.py`

3. **Set Environment Variables** in Render dashboard:
   | Variable | Value | Description |
   |----------|-------|-------------|
   | `BOT_TOKEN` | Your Telegram bot token | Get from @BotFather |
   | `ADMIN_IDS` | `8720175870` | Admin user IDs (comma-separated) |
   | `WEBHOOK_SECRET` | Any random string (e.g., `a1b2c3d4e5f6`) | Security key for webhook |
   | `PORT` | `8000` | Render sets this automatically |

4. **Deploy** — Render will build and deploy automatically

### How Webhook Works

When deployed on Render, the bot:
- Starts a web server on the assigned port
- Exposes a webhook endpoint at `/webhook/{WEBHOOK_SECRET}`
- Telegram sends updates to this endpoint
- The bot processes updates via HTTP POST requests

### Local Development (Polling Mode)

For local testing, you can use polling mode by running:

```bash
python main.py
```

### Project Structure

```
manhwa_bot/
├── main.py              # Entry point (webhook + FastAPI server)
├── config.py            # Configuration & environment variables
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container config
├── .env.example         # Environment variables template
├── database/            # SQLite database module
├── admin/               # Admin panel handlers
├── user/                # User-facing handlers
├── keyboards/           # Telegram keyboards
├── middlewares/         # Message middlewares
└── filters/             # Message filters
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | — | Telegram bot token |
| `ADMIN_IDS` | Yes | `8720175870` | Comma-separated admin user IDs |
| `WEBHOOK_SECRET` | Yes | — | Secret path segment for webhook |
| `PORT` | No | `8000` | Server port (set by Render) |
