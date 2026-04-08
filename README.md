# Nail Inspo

A web app and Telegram bot for collecting and organizing nail design inspiration in one place.

---

## Demo

The product consists of two parts:

- Telegram bot for browsing and saving nail designs  
- Web gallery for viewing and managing saved inspiration  

---

## Product context

### End users
Young women (18–30) looking for manicure inspiration before visiting a nail artist.

### Problem
Users usually save nail ideas in different places:
- phone gallery  
- Pinterest boards  
- social media  
- chats  

As a result, inspiration becomes:
- scattered  
- hard to organize  
- difficult to revisit  

### Solution
Nail Inspo provides a single space where users can:
- browse nail designs via Telegram  
- save favorite ideas instantly  
- access a personal gallery on the web  
- filter and manage saved designs  

---

## Features

### Version 1 (Core functionality)
- Telegram bot:
  - `/random` — get a random nail design  
  - `/short`, `/long`, `/solid`, `/creative` — filter by tags  
  - `/save` — save current design  
  - `/my` — open personal gallery  
- Web:
  - gallery of saved designs  
  - tag-based filtering  
- Backend:
  - FastAPI + PostgreSQL  
  - persistent storage  

---

### Version 2 (Final version)
- Alias-based login (no registration required)  
- Multi-user support  
- Personal gallery per user  
- Remove saved designs directly from the website  
- Improved UI:
  - Pinterest-style layout  
  - dark/light theme  
  - clean minimal aesthetic  

---

### Not implemented (future improvements)
- recommendation system  
- uploading own designs  
- personalized suggestions  
- cloud synchronization  
- Telegram OAuth login  

---

## Usage

### Website
1. Open the website  
2. Enter your alias (Telegram username)  
3. View your saved designs  
4. Remove items by clicking the heart icon  

---

### Telegram bot

Commands:
```
/random
/short
/long
/solid
/creative
/save
/my
```

Typical flow:
1. Browse designs  
2. Save favorites  
3. Open your gallery using `/my`  

---

## Architecture

- Backend: FastAPI  
- Database: PostgreSQL  
- ORM: SQLAlchemy  
- Frontend: Jinja2 templates + CSS  
- Telegram bot: python-telegram-bot  
- Deployment: Docker Compose  

---

## Deployment

### OS
Ubuntu 24.04  

### Requirements
- Docker  
- Docker Compose  

Install dependencies:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

---

### Run the project

```bash
git clone https://github.com/Erusiaaa/se-toolkit-hackathon.git
cd se-toolkit-hackathon
cp .env.example .env
```

Edit `.env`:
- add your Telegram bot token  
- set public URL  

Then run:

```bash
docker compose up --build
```

---

### Access

Open in browser:
```
http://<VM-IP>:8000
```

---

## One-sentence pitch

Nail Inspo helps users collect and organize nail inspiration through a Telegram bot and a personal web gallery.
