# Campus Customs: Yale Apparel Shop + Handsome Dan Chat Assistant

MGT409 AI for Managers, Homework 4.

Campus Customs is a Yale apparel shop with an AI shopping assistant, **Handsome Dan**. Shoppers can:
- browse and filter 102 products;
- create an account and log in;
- chat about merchandise and get accurate prices and stock from the store's database;
- have the chat update the page with every matching item.

| Part | Stack |
|---|---|
| Frontend (`frontend/`) | Vite + React + TypeScript |
| Backend (`backend/`) | FastAPI + a PydanticAI agent (`agent.py`, `tools.py`, `models.py`, `prompts/prompt.md`) |
| Model | OpenAI `gpt-5.6-luna` through the Portkey gateway |
| Data | SQLite database and product images (local-only data pack, not in git) |

## Project layout

```
hw4/
├── AI_prompts.md          # every prompt used to build the project
├── requirements.txt       # Python dependencies
├── .env.example           # copy to .env and add your Portkey key
├── .gitignore
├── README.md
├── frontend/              # Vite React TypeScript app
├── backend/
│   ├── main.py            # FastAPI app: uvicorn main:app --reload --port 8000
│   ├── agent.py           # agent wiring, agent loop, audit trail
│   ├── models.py          # Pydantic / PydanticAI types
│   ├── tools.py           # tools the agent can call + database queries
│   └── prompts/
│       └── prompt.md      # system prompt
└── output/
    ├── harness.md         # full explanation of how the system works
    ├── design.md          # design decisions
    ├── usability.md       # usability improvements, with measurements
    ├── app_check.html     # live test report (open by double-clicking)
    ├── app_check_images/  # screenshots linked from app_check.html
    └── audit_trail.json   # append-only log of agent runs
```

## Setup

### 1. Place the data pack

The data pack isn't in git. Put it in a `data/` folder at the top of the project:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # product images referenced by the catalogue
```

### 2. Add your API key

```bash
cp .env.example .env
```

Then open `.env` and set `PORTKEY_API_KEY`. `.env` is ignored by git. Without a key the site still works, but the chat replies that it isn't set up yet.

### 3. Run the backend (FastAPI)

Requires Python 3.10 or newer (built and tested with 3.14). From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. `http://localhost:8000/api/health` should return `{"status":"ok"}`.

### 4. Run the frontend (Vite + React)

Requires Node.js 20.19+ or 22.12+ (built with Node 24). In a second terminal, from the project folder:

```bash
cd frontend
npm install
npm run dev
```

Open the address Vite prints, normally `http://localhost:5173`. The dev server forwards `/api` and `/images` to the backend on port 8000.

- If port 5173 is taken: `npx vite --port 5180`.
- If the backend runs on a different port: `API_URL=http://localhost:8010 npm run dev`.

## Trying it out

- **Browse:** use the Products page filters (category, color, size in stock, keywords, sort), or tap a residential college on the home page.
- **Chat:** click Handsome Dan in the bottom-right corner or the "Ask Handsome Dan" link at the top. Try:
  - "What kinds of t-shirts do you have?" (the page updates to all 25)
  - "Is this in stock in XL?" on any product page
  - "Do you have the Ice Hockey Left Chest Hoodie in a large?"
- **Accounts:** use Create Account, or log in with the data pack's example account `test@campuscustoms.yale.edu` (password: `password`). Logged-in chats are saved and come back at the next login.

## Learn more

- `output/harness.md`: architecture, specs (loop limits, result caps, model), data model, tools, safety rules and the audit trail
- `output/design.md`: design decisions
- `output/usability.md`: usability improvements, with before-and-after measurements
- `output/app_check.html`: live test with screenshots
