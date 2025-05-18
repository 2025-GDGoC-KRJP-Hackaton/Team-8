# Tickr

> THE go-to Discord assistant from ideation to product!
> *Built for the 2025 Korea x Japan GDGoC Hackathon – The Bridge*

Welcome to Tickr, the ultimate battlefield commander for Discord projects! Forged in the crucible of the 2025 Korea x Japan GDGoC Hackathon – The Bridge, Tickr transforms your chaotic chatrooms into a war room of precision-driven tasks. Rally your indie squad, school team, or corporate legion and watch as Tickr forges scattered ideas into organized, actionable missions—right where you talk.

## ✨ Features

* 🔄 Chat-scraping and ticket generation
* 📅 Google Calendar syncing
* 🤝 Team-based assignment & accountability

## 🛠️ Installation

1. **Discord Bot Server**

   ```bash
   cd DiscordBot_server
   pnpm install
   ```
2. **AI Server**

   ```bash
   cd AI_server
   pip install -r requirements.txt
   ```

## 🛠️ Tech Stack

* **Backend & AI Server**: FastAPI for REST endpoints, Gemini for processing and storing chat data in JSON files
* **Discord Bot**: discord.js running on Node.js
* **Calendar Integration**: Google Calendar API for event creation and invite links

## 🗨️ How to Talk to the Bot

* Use `/ticket` to let Tickr scan past messages and generate a list of tasks with due dates and descriptions.
* Team members can react to a ticket with an emoji to be automatically assigned to it.
* If a ticket includes a due date, Tickr will generate a Google Calendar invite link.
* Right-click a ticket to mark it as complete and remove it from the list.
* Use `/summary` for an overview of the project: tickets, assignments, and who's responsible.

## 👥 Team

* **Brilliant Aksan** – Project Management, UX Design
* **Hoyeong Choi** – JS Bot Development
* **Cedric Purwanto** – Calendar Integration, Prompt Engineering
* **Jaemin Kim** – Backend, Prompt Engineering

## 🏁 Submission Info

This project was built and submitted as part of the
2025 Korea x Japan GDGoC Hackathon – The Bridge.

Hosted by Google Developer Groups on Campus Waseda University, Yonsei University, Tokyo University, and Korea University, this event brings together students from Korea and Japan to build tech that bridges cultures, ideas, and communities.
