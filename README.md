# 🎫 IT Helpdesk Discord Bot

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pycord](https://img.shields.io/badge/Pycord-v2.0+-red.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

A lightweight, event-driven ticketing system built for Discord.

## ✨ Features
*   **Ticket Management:** Users can instantly generate support tickets using the `/ticket_create` slash command.
*   **Role-Based Access Control (RBAC):** Admin-only commands and restricted views for secure ticket resolution.
*   **Persistent Cloud Storage:** All tickets, logs, and user data are securely stored and queried via MongoDB Atlas.
*   **Audit Logging:** Automated logging of ticket creation and resolution times.
*   **High Availability:** Integrated Flask web server running on a secondary thread to keep the worker instance alive in serverless/cloud environments.
  
## 🛠️ Tech Stack
*   **Language:** Python 3.12+
*   **Framework:** Pycord 
*   **Database:** MongoDB Atlas 
*   **Web Server:** Flask 
*   **Deployment:** Render (Cloud Platform) + UptimeRobot

## 🏗️ System Architecture
This application utilizes a dual-thread approach to bypass standard cloud-hosting sleep cycles:
1.  **Thread 1 (Application Layer):** Runs the asynchronous Discord bot event loop, handling WebSocket connections and API requests.
2.  **Thread 2 (Network Layer):** Runs a lightweight Flask WSGI server bound to a dynamic environment port. This acts as a health-check endpoint for external ping services (like UptimeRobot) to prevent the host platform from suspending the container.

## 🛠️ Command Directory

| Command | Access Level | Description |
| :--- | :--- | :--- |
| `/ticket_create` | All Users | Opens an interactive modal to submit a new IT issue to the database. |
| `/ticket_view_open` | Administrator | Fetches and displays a list of all currently unresolved tickets. |
| `/ticket_resolve [ID]` | Administrator | Closes a ticket, updates the database state, and triggers a user DM. |
| `/ticket_lookup [ID]` | Administrator | Pulls a complete historical audit log for any specific ticket ID. |
| `/ticket_history` | Administrator | Displays the 5 most recently resolved tickets sorted by timestamp. |

## 🖼️ Showcase

## 🚀 Setup & Local Installation

#### 1. Clone the repository
```
git clone https://github.com/ChewShen/DiscordTicketBot.git
```

Then, navigate into the new project folder:
```bash
cd DiscordTicketBot
```

#### 2. Initialize Virtual Environment

(You can skip this if you decide to run it directly on your machine)
```bash
python -m venv venv
```

**Activate on Windows:** .\venv\Scripts\activate\
**Activate on Mac/Linux:** source venv/bin/activate

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

(You can replace the os.getenv part in the code with the keys directly if you decide to skip the environment file, but a .env file is recommended for security)

Create a .env file in the root directory and input your configuration keys:
As example:

DISCORD_TOKEN=your_discord_bot_token_here\
MONGO_URI=your_mongodb_atlas_connection_string_here\
IT_LOG=your_admin_channel_id_here

#### 5. Boot the Application
run
```bash
python main.py
```


## 📝 Changelog

### [v1.3.2] - 2026-03-31
**Fixed**
*   Upgraded global error handler (`on_application_command_error`) to properly route exception tracebacks to the `#it-logs` admin channel.
*   Resolved an `AttributeError` by correctly utilizing `await bot.fetch_channel()` to bypass empty cache issues during Discord API calls.
*   Implemented ephemeral user-facing apologies to maintain UI cleanliness during critical backend failures.

##### v1.3: Modular Architecture & Audit Logging Polish

**Architecture & Refactoring:**
* **Implemented Discord Cogs:** Refactored the monolithic `main.py` into a modular.
* **OOP Migration:** Transitioned all command logic into Object-Oriented classes (`TicketsCog`, `AdminCog`), for improve code maintainability and readability.

**Feature & UI Enhancements:**
* **Dynamic Time Localization:** Integrated Discord's native Unix Timestamp formatting (`<t:timestamp:f>`) to automatically calculate and display localise timezon for the admins.
* **Better Admin UI:** Upgraded the Admin Audit Log embed with better readability.

##### v1.2:
* Added a startup validation and error handling for lacking environment variables.
##### v1.1:
* Resolved a potential Ticket ID race condition under high concurrency by implementing MongoDB atomic counters (`$inc`) for thread-safe ID generation.
##### v1.0:
* Initial release. Implemented core CRUD functionality, RBAC, and global error handling. 