# BookMyShow Ticket Tracker

A lightweight Python script that automatically monitors BookMyShow for movie ticket availability and sends instant alerts directly to your Telegram bot when bookings open.

## 🚀 Features

* **Real-time Monitoring:** Regularly checks the availability status of targeted movies.
* **Instant Alerts:** Sends a Telegram notification the moment tickets go live.
* **State Management:** Tracks alert history locally (`alerted.json`) to prevent duplicate spam notifications.
* **Secure Configuration:** Zero hardcoded API keys; utilizes secure system environment variables.

## 📋 Prerequisites

Before running the script, ensure you have the following installed and configured:
* **Python 3.x**
* **A Telegram Bot Token** (Generated via [@BotFather](https://t.me))
* **Your Telegram Chat ID** (Can be retrieved via bots like `@userinfobot`)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd YOUR_REPOSITORY_NAME
   ```

2. **Install dependencies:**
   The script relies on standard web request and parsing libraries:
   ```bash
   pip install requests beautifulsoup4
   ```

## ⚙️ Configuration & Environment Variables

This project uses system environment variables to securely handle sensitive credentials. **Do not hardcode your tokens into the script file.**

### 1. Setting up Local Variables (Windows Command Prompt)
Run the following commands in your terminal before launching the script:
```cmd
set TG_TOKEN="your_telegram_bot_token_here"
set TG_CHAT_ID="your_telegram_chat_id_here"
```

### 2. Setting up Local Variables (Linux / Raspberry Pi Terminal)
```bash
export TG_TOKEN="your_telegram_bot_token_here"
export TG_CHAT_ID="your_telegram_chat_id_here"
```

### 3. Targeting a Movie / Theater
*(⚠️ Note to developer: Replace this placeholder block with your script's actual logic, such as a config.json snippet or CLI argument example)*
To specify which movie or cinema hall to track, pass the target URL directly as a command-line argument:
```bash
python bms_scraper.py --url "https://bookmyshow.com..."
```

## 💻 Usage

Run the script directly from your terminal:
```bash
python bms_scraper.py
```

### Running as a System Service (Raspberry Pi / Linux)
To run this continuously in the background, it is recommended to configure it as a `systemd` service:

1. **Create a service file:**
   ```bash
   sudo nano /etc/systemd/system/bms-scraper.service
   ```

2. **Paste the following configuration** (ensure you update your working directory and tokens):
   ```ini
   [Unit]
   Description=BookMyShow Ticket Scraper Service
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/BMS_REPO
   Environment="TG_TOKEN=your_bot_token"
   Environment="TG_CHAT_ID=your_chat_id"
   ExecStart=/usr/bin/python3 bms_scraper.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bms-scraper.service
   sudo systemctl start bms-scraper.service
   ```

## 🔍 Troubleshooting

* **403 Forbidden / Cloudflare Errors:** BookMyShow uses strong anti-bot protections. If your script fails to fetch data, ensure your request headers include a valid, modern browser `User-Agent`.
* **Not Receiving Telegram Alerts:** Double-check that you have initiated a chat with your bot by sending it a `/start` command first, otherwise the API will reject your message.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
