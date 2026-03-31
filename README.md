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
**<div align="center" >3 Tier System Architecture</div>**

This application implements a 3-tier architecture designed for better availability and asynchronous processing.
<div align="center"><img width="700" height="600" alt="discordbot drawio" src="https://github.com/user-attachments/assets/26eea7cf-282f-484a-9511-e91dfed76dec" /></div>

* Presentation Tier: Discord's client acts as the frontend UI, capturing user slash commands and routing them to the backend via WebSockets.
* Application Tier: Hosted on a Render cloud instance, this tier utilizes a dual-thread design. The primary thread runs the Pycord asynchronous event loop for bot logic. A secondary thread runs a lightweight Flask WSGI web server bound to a dynamic port. This Flask server acts as a continuous health-check endpoint for UptimeRobot, effectively bypassing the host platform's idle-sleep cycle.
* Database Tier: A MongoDB Atlas cluster provides persistent, NoSQL document storage, communicating with the application tier via the Motor asynchronous I/O driver.


**<div align="center" >User/End Client Pipeline</div>**
<div align="center"><img width="500" height="300" alt="discordbot drawio" src="https://github.com/user-attachments/assets/08857053-88c9-4af5-ad02-5ddec4311815" /></div>

This pipeline demonstrates the request cycle when an end-user interacts with the bot. Once a user triggers the /ticket_create slash command, Discord transmits a JSON payload via WebSockets to the Application Tier. The Pycord event listener extracts the relevant context (User ID, Server ID, input strings) and executes an asynchronous database write to MongoDB. To ensure data integrity, the system waits for the database write confirmation before rendering and dispatching the final Discord Embed to update the user's UI.

**<div align="center" >Admin Pipeline</div>**
<div align="center"><img width="500" height="300" alt="discordbot drawio" src="https://github.com/user-attachments/assets/f70af914-a60b-4b65-9e19-ee0778c59683" /></div>

This pipeline highlights the system's administrative commands and the safety nets. When an Admin triggers the /ticket_resolve command or any other admin level command, the request must pass the Role-Based Access Control (RBAC) validation check before proceeding.

Once authorized, the system queries MongoDB, validates the ticket's current state (ensuring it is open), and performs an asynchronous update. The system then generates a nortification in a designated internal channel for managerial oversight, directly notifies the original end-user of the resolution, and finally sends an ephemeral UI confirmation to the acting Admin to gracefully close the Discord interaction.

## 🛠️ Command Directory

| Command | Access Level | Description |
| :--- | :--- | :--- |
| `/ticket_create` | All Users | Opens an interactive modal to submit a new IT issue to the database. |
| `/ticket_view_open` | Administrator | Fetches and displays a list of all currently unresolved tickets. |
| `/ticket_resolve [ID]` | Administrator | Closes a ticket, updates the database state, and triggers a user DM. |
| `/ticket_lookup [ID]` | Administrator | Pulls a complete historical audit log for any specific ticket ID. |
| `/ticket_history` | Administrator | Displays the 5 most recently resolved tickets sorted by timestamp. |

## 🖼️ Showcase

### <div align="center">User's Point-Of-View</div>

1. When user request for a ticket\
   <img width="400" height="299" alt="image" src="https://github.com/user-attachments/assets/21da628a-21e4-437e-91ae-07b7abf5c6fb" />

2. When an admin solved the ticket, the user is inform by DM\
  <img width="381" height="169" alt="image" src="https://github.com/user-attachments/assets/2029127c-1dc3-433c-afdc-cb4694f96b98" />


### <div align="center" >Admin's Point-of-View</div>

1. When admin check for all ticket that is still unsolve\
   <img width="371" height="453" alt="image" src="https://github.com/user-attachments/assets/e87d5b3e-9f85-4bda-b4e8-a16707fca822" />

2. When admin solved the problem\
  <img width="336" height="136" alt="image" src="https://github.com/user-attachments/assets/cb4c93bd-e848-4600-baf0-8ef7b5eec4eb" />

3. When admin look up for the specific case by ticket id\

   **Ticket Open**\
     <img width="382" height="307" alt="auditlog1" src="https://github.com/user-attachments/assets/0339e7ec-a8d5-4001-9d0c-e26bceee3878" />\

   **Ticket Closed**\
     <img width="382" height="307" alt="auditlog2" src="https://github.com/user-attachments/assets/32261424-6ec0-45e5-bd07-96383fd5c3b2" />

4. When admin view the history (Only 5  most solved ticket will be shown, for now)\
   ![history](https://github.com/user-attachments/assets/062b2920-55b4-460a-949a-721cf215ef20)


   

### <div align="center" >IT/Audit Log's Point-of-View</div>

1. When admin solved a ticket, its informned on the log channel\
  <img width="412" height="54" alt="image" src="https://github.com/user-attachments/assets/d6c88dbe-0761-4872-8e28-974509085daa" />


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

##### v1.3.2 : Better error handler
**Fixed**
*   Upgraded global error handler (`on_application_command_error`) to properly route exception tracebacks to the `#it-logs` admin channel.
*   Resolved an `AttributeError` by correctly utilizing `await bot.fetch_channel()` to bypass empty cache issues during Discord API calls.
*   Implemented ephemeral user-facing apologies to maintain UI cleanliness during critical backend failures.

##### v1.3.1 : Added a function to prevent timeout and minor fix

**Added**
* Implemented keep_alive() Flask server thread in main.py to prevent cloud host timeout.
* Dynamically bound Flask host to Render's internal PORT environment variable to pass port-scan health checks.

**Fixed**
* Resolved Discord 10062: Unknown interaction timeout errors caused by CPU throttling.
  
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