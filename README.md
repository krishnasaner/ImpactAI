# ImpactAI
**Final Year Project by Krishna Saner**

ImpactAI is an advanced, AI-powered mental health support platform designed to provide immediate, compassionate, and intelligent conversational care. Acting as a bridge between individuals seeking support and mental health professionals, ImpactAI features a sophisticated architecture incorporating real-time crisis detection, multi-lingual support, and predictive severity modeling.

![ImpactAI Overview](/api/placeholder/1000/400)

## 🌟 Key Features

*   **Zenith (AI Companion):** A warm, conversational AI utilizing **Groq Cloud (Llama 3)** to provide empathetic mental health support without clinical jargon.
*   **Dual-Layer Crisis Detection:** Analyzes conversations simultaneously using LLM intent and a custom **Machine Learning (ML) Severity Model** to classify distress into *Low, Medium, High, or Crisis* states.
*   **Emergency Intervention:** Instantly detects self-harm indicators or crisis keywords across languages and triggers immediate emergency helpline routing (e.g., Tele-MANAS, AASRA).
*   **Multilingual Support:** Operates seamlessly across 12+ languages, offering culturally appropriate localizations for diverse user demographics.
*   **Secure & Private:** Comprehensive session tracking, JWT-based secure authentication, and robust end-to-end privacy for sensitive data.
*   **Modern Dashboards:** Role-based dashboards (Admin, Counselor, Student) built with a premium 'Organic Light' design system featuring glassmorphism and modern aesthetics.

## 🛠️ Technology Stack

### Frontend
*   **Framework:** React 18 with TypeScript & Vite
*   **Design/Styling:** Tailwind CSS, Shadcn UI, and Lucide Icons
*   **State & Routing:** Context API, React Router DOM
*   **Authentication:** JWT, Secure HTTP-only cookies & session storage

### Backend
*   **Framework:** FastAPI (Python)
*   **Database:** SQLite integrated with SQLAlchemy ORM (WAL mode for concurrency)
*   **AI Integration:** Groq Python SDK (Llama 3 model)
*   **Machine Learning:** Scikit-learn (Severity Prediction Model)
*   **Security:** Bcrypt (Password Hashing), Python-JOSE (JWT Management)

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (3.10+)
*   Groq API Key (for LLM backend)

For complete automated setup and local environment provisioning, refer to the [**DEVELOPMENT_SETUP.md**](DEVELOPMENT_SETUP.md) guide.

### Quick Start Overview
1.  **Backend:** Navigate to `/Backend`, set up your `venv`, run `pip install -r requirements.txt`, configure your `.env` (with `GROQ_API_KEY` and `JWT_SECRET`), and start the server with `uvicorn main:app --reload`.
2.  **Frontend:** Navigate to `/frontend`, run `npm install`, and start the Vite development server using `npm run dev`.

## 📂 Project Structure
```
ImpactAI/
├── Backend/                 # FastAPI server, ML models, SQLite database
│   ├── routes/              # Auth, Chat endpoint routers
│   ├── services/            # Groq Client, Security, ML logic
│   └── main.py              # Application entry point
├── frontend/                # React Vite Application
│   ├── src/                 
│   │   ├── components/      # Reusable UI components & ChatWidget
│   │   ├── pages/           # Routers & Views (Dashboard, Chat, Auth)
│   │   └── contexts/        # React Contexts (AuthContext, ProtectedRoutes)
├── DEVELOPMENT_SETUP.md     # Installation & Environment configuration
└── README.md                # Project documentation
```

## 📄 Licensing

This project is licensed under the MIT License. See `LICENSE` for more information.
Copyright (c) 2026 Krishna Saner.
