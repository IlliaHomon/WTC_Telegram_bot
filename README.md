# WTC Telegram Bot
A Python Telegram bot deployed on a cloud Linux server to handle automated interaction and data persistence. Built with production-ready architecture, featuring environment isolation, system service management for 24/7 uptime, and automated restart recovery.

## Overview & Key Highlights

- **Production-Ready Deployment**: Configured as an active systemd service on a Linux VPS, ensuring continuous operation and automatic process recovery upon system reboots or unhandled exceptions.
- **Secure Configuration Management**: Implemented environment-variable handling using .env pattern to separate secret bot tokens and sensitive data from the source code.
- **Persistent Data Architecture**: Managed local data persistence using SQLite / modular Python database modules.
- **Isolated Environment**: Built within an isolated Python Virtual Environment (venv) to ensure deterministic dependency control across development and production settings.

## Tech Stack

**Language**: Python 3
**API / Library**: python-telegram-bot
**Database**: SQLite / SQL
**Hosting & DevOps**: Linux (Ubuntu), SSH, systemd, git

## Project Architecture

WTC_Telegram_bot/
├── .gitignore       # Prevents sensitive files (.env, venv/) from being tracked
├── bot.py           # Core bot handler and interaction logic
├── database.py      # Database interface and queries
├── requirements.txt # Project dependency specifications
└── README.md        # Project overview

## Key Takeaways & Learned Concepts

### Software & Application Development
- **Asynchronous Programming:** Utilized `async`/`await` patterns in Python to handle concurrent user interactions and messaging.
- **Database Management & SQL:** Structured relational database tables to store user information, recipe categories, and user-generated content.
- **Modular Code Architecture:** Designed a maintainable project structure by separating database access methods from application handlers.
- **API & Payload Handling:** Parsed dynamic incoming requests and managed Telegram Bot API responses.

### Infrastructure & Operations
- **Linux Administration:** Managed cloud server setup, SSH connections, and directory permissions on Ubuntu.
- **Process Supervision:** Configured automated daemon services using `systemd` for fault tolerance, logging, and 24/7 uptime.
  
