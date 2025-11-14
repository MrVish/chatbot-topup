# Quick Setup Guide

## Prerequisites

Before starting, ensure you have:
- **Python 3.10 or 3.11** (NOT 3.12+)
- **Node.js 18+**
- **Microsoft C++ Build Tools** (Windows only)

## Step-by-Step Setup

### 1. Install Microsoft C++ Build Tools (Windows Only)

**This is REQUIRED for the backend to work on Windows!**

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run installer
3. Select "Desktop development with C++"
4. Click Install (takes ~10 minutes, requires ~7GB)
5. **Restart your terminal after installation**

### 2. Clone Repository

```bash
git clone https://github.com/MrVish/chatbot-topup.git
cd chatbot-topup
```

### 3. Backend Setup

```bash
cd topup-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (CMD):
venv\Scripts\activate.bat
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Upgrade pip (important!)
python -m pip install --upgrade pip wheel setuptools

# Install dependencies
pip install -r requirements.txt

# If you get chromadb errors, try:
pip install chromadb --only-binary :all:
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Windows
# or
cp .env.example .env    # Linux/Mac

# Edit .env and add your OPENAI_API_KEY
# Get your key from: https://platform.openai.com/api-keys

# Generate sample data
python scripts/generate_sample_data.py
```

### 4. Frontend Setup

Open a **NEW terminal** (keep backend terminal open):

```bash
cd topup-frontend

# Install dependencies
npm install

# If you get module errors, also run:
npm install clsx tailwind-merge class-variance-authority

# Copy environment file
copy .env.example .env.local  # Windows
# or
cp .env.example .env.local    # Linux/Mac

# The .env.local should contain:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5. Start Servers

#### Option A: Use Start Script (Easiest)

From project root:
```bash
# Windows:
start_servers.bat

# Linux/Mac:
./start_servers.sh
```

#### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
cd topup-backend
venv\Scripts\activate  # or source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd topup-frontend
npm run dev
```

### 6. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### Backend Issues

**Error: "Microsoft Visual C++ 14.0 or greater is required"**
- Solution: Install C++ Build Tools (see Step 1)
- Alternative: Use Python 3.10 (better pre-built wheel support)

**Error: "chromadb installation failed"**
```bash
pip install chromadb --only-binary :all:
pip install -r requirements.txt
```

**Error: "OpenAI API key invalid"**
- Check your `.env` file has correct `OPENAI_API_KEY`
- Get key from: https://platform.openai.com/api-keys

**Error: "Database not found"**
```bash
python scripts/generate_sample_data.py
```

### Frontend Issues

**Error: "Module not found: Can't resolve '@/lib/utils'"**
```bash
# Create the file manually
mkdir lib
# Copy content from INSTALLATION_TROUBLESHOOTING.md
```

**Error: "Module not found" for any component**
```bash
rm -rf node_modules .next
npm install
npm run dev
```

**Error: "Failed to fetch"**
- Make sure backend is running on port 8000
- Check `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Verification

### Test Backend
```bash
cd topup-backend
venv\Scripts\activate
python -c "import chromadb; import fastapi; print('Backend OK')"
```

### Test Frontend
```bash
cd topup-frontend
npm run build
```

If both succeed, you're ready to go!

## Common Commands

### Backend
```bash
# Activate environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v
```

### Frontend
```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run production server
npm start
```

## Need More Help?

See `INSTALLATION_TROUBLESHOOTING.md` for detailed solutions to common issues.
