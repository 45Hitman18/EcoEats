<div align="center">

# 🌱 EcoEats

### Food Waste Redistribution & Live Logistics Routing Platform

*Bridging surplus food from donors to NGOs — powered by real-time GPS-guided volunteer delivery.*

<br/>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet.js-1.9.4-199900?style=for-the-badge&logo=leaflet&logoColor=white)
![OSRM](https://img.shields.io/badge/OSRM-Routing-4A90D9?style=for-the-badge&logo=openstreetmap&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_Accented_CSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)

![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet?style=flat-square)

</div>

---

## 📖 Overview

**EcoEats** is a state-of-the-art, Django-powered community platform designed to bridge the gap between **food donors** (restaurants, grocers) and **NGO receivers**. The platform features an integrated, real-time logistics dispatch system that coordinates verified volunteer drivers to deliver claimed cargo using live street-by-street map navigation.

<br/>

## 📑 Table of Contents

- [Key System Features](#-key-system-features)
- [System Architecture](#-system-architecture--use-case-flow)
- [Database Schema](#-database-schema-entity-relationship-diagram)
- [Technology Stack](#️-technology-stack)
- [Installation & Setup](#️-installation--running-locally)
- [Test Accounts](#-pre-configured-test-accounts)

---

## 🚀 Key System Features

<table>
<tr>
<td width="50%" valign="top">

### 👤 Donors *(Food Rescue Sources)*
- 📦 List surplus inventory with detailed **volume (kg)**, **expiry times**, and **category tags**
- 🗂️ Manage listings via an interactive inventory dashboard with **Bulk Actions** — select-all toggles to expire or delete listings in one shot
- 🚚 Initiate direct driver delivery coordination requests

</td>
<td width="50%" valign="top">

### 🏢 NGO Receivers *(Food Shelters)*
- 🛒 Browse a **live marketplace** of active surplus food listings
- ✋ Submit requests to claim surplus food items
- 🔔 Receive automatic alerts when new surplus is posted
- 🧭 Assign volunteer drivers to pending pickups via a coordination directory

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🚛 Volunteer Drivers *(Logistics Partners)*
- 🪪 Dedicated verification onboarding — Aadhar docs, license verification, vehicle parameters
- 🗺️ **Active Job Route Worksheet** tracing pickup → drop-off
- 📍 **Live Co-Navigator (Google Maps-style)** — GPS auto-pan via `navigator.geolocation.watchPosition`, close-up `zoom: 17`, true driving roads via OSRM (no straight-line polylines)
- 📤 **One-Click Location Sharing** directly into donor/receiver chat threads

</td>
<td width="50%" valign="top">

### ⚙️ System Administrators *(Moderators)*
- ✅ Audit and approve driver credentials
- ✅ Verify NGO organization paperwork
- 🛡️ Moderate listings and review system logs

</td>
</tr>
</table>

---

## 📊 System Architecture & Use Case Flow

```mermaid
flowchart TD
    Donor["👤 Donor"] -->|1. List Surplus| Inventory["📦 Surplus Pool"]
    Receiver["🏢 NGO Receiver"] -->|2. Browse & Claim| Inventory
    Receiver -->|3. Assign Driver| DriverDir["📋 Logistics Pool"]
    Driver["🚚 Volunteer Driver"] -->|4. Accept Run| DriverDir
    Driver -->|5. Launch Co-Navigator| MapOverlay["🗺️ Live GPS Routing Map"]
    MapOverlay -->|6. Share Live GPS| ChatChannel["💬 Chat Logs (AJAX)"]
    Admin["⚙️ System Admin"] -->|Verify Accounts| Driver
    Admin -->|Verify Org| Receiver
```

---

## 💾 Database Schema (Entity Relationship Diagram)

```mermaid
erDiagram
    USER {
        int id PK
        string username
        string email
        string role "donor | receiver | driver | admin"
    }

    PROFILE {
        int id PK
        int user_id FK
        string organization_name
        string phone
        boolean is_verified
        boolean is_driver_onboarded
        string vehicle_name
        string vehicle_number
        string driving_license_pdf
        string adhar_card_pdf
        float latitude
        float longitude
    }

    FOOD_LISTING {
        int id PK
        int donor_id FK
        string food_name
        string food_type
        int quantity
        datetime expiry_time
        string status "available | requested | claimed | expired"
        boolean is_deleted
    }

    FOOD_REQUEST {
        int id PK
        int listing_id FK
        int requester_id FK
        int driver_id FK
        string status "pending | approved | rejected | completed"
        string delivery_status "pending_driver | accepted | picked_up | delivered"
        string delivery_photo
    }

    MESSAGE {
        int id PK
        int sender_id FK
        int receiver_id FK
        string content
        datetime timestamp
        boolean is_read
    }

    NOTIFICATION {
        int id PK
        int user_id FK
        string notification_type
        string message
        boolean is_read
        datetime created_at
    }

    USER ||--|| PROFILE : "has profile details"
    USER ||--o{ FOOD_LISTING : "creates listings"
    USER ||--o{ FOOD_REQUEST : "claims items"
    USER ||--o{ MESSAGE : "sends messages"
    USER ||--o{ NOTIFICATION : "receives alerts"
    FOOD_LISTING ||--o{ FOOD_REQUEST : "contains requests"
```

---

## 🛠️ Technology Stack

<div align="center">

| Layer | Technology |
|:---|:---|
| **Backend** | ![Python](https://img.shields.io/badge/-Python%203.13-3776AB?logo=python&logoColor=white&style=flat-square) ![Django](https://img.shields.io/badge/-Django%205.x-092E20?logo=django&logoColor=white&style=flat-square) |
| **Database** | ![SQLite](https://img.shields.io/badge/-SQLite3-07405E?logo=sqlite&logoColor=white&style=flat-square) |
| **Map Engine** | ![Leaflet](https://img.shields.io/badge/-Leaflet.js%201.9.4-199900?logo=leaflet&logoColor=white&style=flat-square) |
| **Routing API** | ![OSRM](https://img.shields.io/badge/-Leaflet%20Routing%20Machine%203.2.12%20(OSRM)-4A90D9?logo=openstreetmap&logoColor=white&style=flat-square) |
| **Styling & UI** | Tailwind-accented Custom HSL Vanilla CSS · Google Fonts *Outfit* & *Inter* · Glassmorphic components · Dynamic transitions |

</div>

---

## ⚙️ Installation & Running Locally

**1. Clone the Repository**
```bash
git clone <repository-url>
cd ECO_EATS
```

**2. Create and Activate a Virtual Environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Perform Database Migrations**
```bash
python manage.py migrate
```

**5. Start the Local Development Server**
```bash
python manage.py runserver
```

Then open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser. 🎉

---

## 🔐 Pre-configured Test Accounts

> For validation and testing convenience, the following credentials are pre-seeded in the local database.

<div align="center">

| Role | Username | Password | Testing Scope |
|:---:|:---:|:---:|:---|
| ⚙️ **System Admin** | `admin` | `admin123` | Moderate requests, verify driver credentials and NGO paperwork |
| 📦 **Donor** | `donor` | `donor123` | List food surplus, bulk inventory management, direct logistics requests |
| 🏢 **NGO Receiver** | `ngo` | `ngo123` | Browse listings, request surplus, notifications, coordinate drivers |
| 🚚 **Volunteer Driver** | `driver` | `driver123` | Onboard license details, manage worksheets, run Live GPS Co-Navigator |

</div>

> ⚠️ **Note:** These credentials are for local development/testing only. Never use default test accounts in a production deployment.

---

<div align="center">

Made with 💚 for reducing food waste, one delivery at a time.

</div>
