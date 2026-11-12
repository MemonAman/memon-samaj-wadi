# Memon Samaj Wadi – Booking Management System

A professional digital hall booking and management system for the Memon Samaj community.

## Project Structure

```
memon-samaj-wadi/
├── mobile/      – React Native + Expo (Customer mobile app)
├── admin/       – React + Vite (Admin web dashboard)
├── backend/     – Django REST Framework (API + business logic)
└── docs/        – Project documentation
```

## Applications

| App | Technology | Purpose |
|---|---|---|
| Mobile | React Native + Expo | Customer booking app (Android & iOS) |
| Admin | React + Vite | Samaj committee dashboard |
| Backend | Django REST Framework + PostgreSQL | Central API and business logic |

## Development Phases

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Environment & Project Setup | ✅ Complete |
| Phase 2 | Backend & PostgreSQL Database | ⏳ Pending |
| Phase 3 | Authentication System | ⏳ Pending |
| Phase 4 | Hall & Availability Calendar | ⏳ Pending |
| Phase 5 | Booking Management | ⏳ Pending |
| Phase 6 | Payment Management | ⏳ Pending |
| Phase 7 | PDF Pavti & QR Verification | ⏳ Pending |
| Phase 8 | Full Frontend–Backend Integration | ⏳ Pending |
| Phase 9 | Testing, Security & Deployment | ⏳ Pending |

## Quick Start

### Prerequisites

- Node.js v18+
- Python 3.11+
- PostgreSQL 14+
- Git

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # Fill in your values
python manage.py migrate
python manage.py runserver
```

### Admin Dashboard Setup

```bash
cd admin
npm install
npm run dev
```

### Mobile App Setup

```bash
cd mobile
npm install
npx expo start
```

## Environment Variables

See `backend/.env.example` for all required environment variables.

> **Never commit `.env` files or any secrets to Git.**

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API Documentation](docs/api-documentation.md)

## Tech Stack

- **Mobile:** React Native, Expo, Expo Router, TypeScript
- **Admin:** React, Vite, React Router, plain CSS
- **Backend:** Python, Django, Django REST Framework, JWT
- **Database:** PostgreSQL
- **Payments:** Razorpay
- **PDF:** ReportLab
- **QR:** qrcode library

---

*Built for Memon Samaj community hall booking management.*

