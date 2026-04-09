# 🛠️ Development Setup for ImpactAI

Welcome to ImpactAI! Follow these instructions to set up your local development environment. This project is maintained by Krishna Saner.

## Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **Git**

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/krishnasaner/ImpactAI.git
cd ImpactAI
```

### 2. Backend Setup (FastAPI & SQLite)
Open a terminal in the `Backend` folder:
```bash
cd Backend
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```
Copy `.env.example` to `.env` and fill in your keys (e.g. Groq API for AI). Start the backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

For authentication in local or production environments, make sure these backend variables are set:
```env
JWT_SECRET=your-secure-jwt-secret
CORS_ORIGINS=http://localhost:8080,https://your-frontend-domain.vercel.app
FRONTEND_URL=https://your-frontend-domain.vercel.app
COOKIE_SECURE=true
COOKIE_SAMESITE=none
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-backend-domain/auth/google/callback
```

### 3. Frontend Setup (React & Vite)
Open another terminal in the `frontend` folder:
```bash
cd frontend
npm install
npm run dev
```
The frontend will start at `http://localhost:8080/`.

Set the frontend API target in production:
```env
VITE_API_URL=https://your-backend-domain
```

## Troubleshooting
- Ensure ports `5000` (Python) and `8080` (React) are free.
- Remember to configure your `.env` properly.

Happy Coding! — Krishna Saner
