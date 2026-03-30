# 🎫 IT Helpdesk Discord Bot

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pycord](https://img.shields.io/badge/Pycord-v2.0+-red.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

A lightweight, event-driven ticketing system built for Discord. This microservice simulates a modern corporate IT support environment, allowing employees to report technical issues via an intuitive front-end UI while providing IT administrators with a centralized, secure NoSQL database to track, audit, and resolve incidents.

## 📸 Project Previews
*(Tip: Take a screenshot of your `/ticket_create` modal and the Green/Red Embed messages in Discord, save them in an `assets` folder, and link them here!)*
* **Ticket Creation UI:** `[Screenshot Placeholder]`
* **Admin Audit Log:** `[Screenshot Placeholder]`

## 🏗️ Architecture & Tech Stack
This application implements a classic **3-Tier Client-Server Architecture** with a focus on asynchronous I/O and Role-Based Access Control (RBAC).

* **Presentation Layer (Client):** Discord UI. Utilizes Slash Commands, interactive Modals, and formatted Embeds for seamless user experience.
* **Application Layer (Middleware):** Python 3.x. Powered by the `py-cord` library for asynchronous event handling and gateway routing.
* **Data Layer (Database):** MongoDB Atlas. Stores dynamic JSON/BSON ticket objects, accessed via the async `motor` driver to prevent thread blocking during CRUD operations.

## ✨ Core Features
* **Asynchronous CRUD Operations:** Fully non-blocking database queries ensuring the bot remains responsive under load.
* **Role-Based Access Control (RBAC):** Administrative commands (`/ticket_resolve`, `/ticket_view_open`) are securely locked at the API level using Discord's native permission system.
* **Automated Audit Logging:** Real-time ticket receipts are automatically routed to a private, secure `#it-logs` channel for administrative tracking.
* **Direct Notification System:** The bot automatically DMs users upon ticket resolution, closing the communication loop.
* **Global Error Handling:** Custom `on_application_command_error` events gracefully catch and report API or database timeouts without crashing the application.
* **Timezone Localization:** Utilizes Unix timestamps to automatically localize database UTC times to the end-user's local timezone.

## 🛠️ Command Directory

| Command | Access Level | Description |
| :--- | :--- | :--- |
| `/ticket_create` | All Users | Opens an interactive modal to submit a new IT issue to the database. |
| `/ticket_view_open` | Administrator | Fetches and displays a list of all currently unresolved tickets. |
| `/ticket_resolve [ID]` | Administrator | Closes a ticket, updates the database state, and triggers a user DM. |
| `/ticket_lookup [ID]` | Administrator | Pulls a complete historical audit log for any specific ticket ID. |
| `/ticket_history` | Administrator | Displays the 5 most recently resolved tickets sorted by timestamp. |

## 🚀 Setup & Local Installation

#### 1. Clone the repository

git clone [https://github.com/ChewShen/DiscordTicketBot.git](https://github.com/ChewShen/DiscordTicketBot.git)

cd YourRepoName 

#### 2. Initialize Virtual Environment

*[You can skip this if you decide to run globally/locally/direct onto your machine]*\
```python -m venv venv```

**Activate on Windows:** .\venv\Scripts\activate\
**Activate on Mac/Linux:** source venv/bin/activate

#### 3. Install Dependencies

pip install -r requirements.txt

#### 4. Configure Environment Variables

*[You can replace the .getenv part with the key directly if you decide to skip the enviroment part]*

Create a .env file and putthe configuration needed key inside.
As example:

DISCORD_TOKEN=your_discord_bot_token_here\
MONGO_URI=your_mongodb_atlas_connection_string_here\
IT_LOG=your_admin_channel_id_here

#### 5. Boot the Application

run ```python main.py```



## 📝 Changelog
* **v1.2:** Added a startup validation and error handling for lacking environment variables.
* **v1.1:** Resolved a potential Ticket ID race condition under high concurrency by implementing MongoDB atomic counters (`$inc`) for thread-safe ID generation.
* **v1.0:** Initial release. Implemented core CRUD functionality, RBAC, and global error handling. 