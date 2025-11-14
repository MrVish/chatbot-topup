# Installation Troubleshooting Guide

## Common Installation Issues and Solutions

### Issue 1: Backend - Microsoft Visual C++ Build Tools Error

**Error Message:**
```
error: Microsoft Visual C++ 14.0 or greater is required
building wheel for chroma-hnswlib (pyproject.toml) did not run successfully
```

**Cause:** The `chromadb` package requires C++ build tools to compile native extensions.

**Solutions:**

#### Option A: Install Microsoft C++ Build Tools (Recommended)
1. Download and install **Microsoft C++ Build Tools**:
   - Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Download "Build Tools for Visual Studio 2022"
   - Run the installer
   - Select "Desktop development with C++"
   - Install (requires ~7GB)

2. After installation, restart your terminal and try again:
   ```bash
   cd topup-backend
   pip install -r requirements.txt
   ```

#### Option B: Use Pre-built Wheels (Faster)
If you don't want to install build tools, use pre-built wheels:

1. Update pip and install wheel:
   ```bash
   python -m pip install --upgrade pip wheel
   ```

2. Install chromadb with pre-built binaries:
   ```bash
   pip install chromadb --only-binary :all:
   ```

3. Then install remaining requirements:
   ```bash
   pip install -r requirements.txt
   ```

#### Option C: Use Alternative Python Version
Some Python versions have better pre-built wheel support:
- Python 3.10 or 3.11 recommended (better wheel availability)
- Avoid Python 3.12+ (fewer pre-built wheels available)

**Verify Installation:**
```bash
python -c "import chromadb; print('ChromaDB installed successfully')"
```

---

### Issue 2: Frontend - Module Not Found Errors

**Error Messages:**
```
Module not found: Can't resolve '@/lib/utils'
Module not found: Can't resolve '@/components/ui/textarea'
```

**Cause:** Missing utility files or incorrect path aliases.

**Solutions:**

#### Step 1: Create Missing Utility File

Create `topup-frontend/lib/utils.ts`:
```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

#### Step 2: Verify Path Aliases in tsconfig.json

Check `topup-frontend/tsconfig.json` has correct paths:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

#### Step 3: Install Missing Dependencies

```bash
cd topup-frontend
npm install clsx tailwind-merge class-variance-authority
```

#### Step 4: Create Missing UI Component

If `textarea` component is missing, create `topup-frontend/components/ui/textarea.tsx`:
```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
```

#### Step 5: Clear Cache and Reinstall

```bash
cd topup-frontend
rm -rf node_modules .next
npm install
npm run dev
```

---

## Complete Fresh Installation Steps

### Backend Setup

1. **Install Python 3.10 or 3.11** (if not already installed)
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Install Microsoft C++ Build Tools** (Windows only)
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++"

3. **Set up backend:**
   ```bash
   cd topup-backend
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   
   # Upgrade pip
   python -m pip install --upgrade pip wheel
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy environment file
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # Linux/Mac
   
   # Edit .env and add your OPENAI_API_KEY
   
   # Generate sample data
   python scripts/generate_sample_data.py
   ```

### Frontend Setup

1. **Install Node.js 18+** (if not already installed)
   - Download from: https://nodejs.org/

2. **Set up frontend:**
   ```bash
   cd topup-frontend
   
   # Install dependencies
   npm install
   
   # Copy environment file
   copy .env.example .env.local  # Windows
   # or
   cp .env.example .env.local    # Linux/Mac
   
   # Create missing files (if needed)
   mkdir -p lib
   # Create lib/utils.ts with content from Step 1 above
   
   # Start development server
   npm run dev
   ```

---

## Verification Steps

### Backend Verification
```bash
cd topup-backend
venv\Scripts\activate  # or source venv/bin/activate
python -c "import chromadb; import fastapi; import langchain; print('All imports successful')"
```

### Frontend Verification
```bash
cd topup-frontend
npm run build
```

If build succeeds, you're good to go!

---

## Alternative: Use Docker (Easiest)

If you continue to have issues, consider using Docker:

```bash
# Backend
cd topup-backend
docker build -t topup-backend .
docker run -p 8000:8000 topup-backend

# Frontend
cd topup-frontend
docker build -t topup-frontend .
docker run -p 3000:3000 topup-frontend
```

---

## Still Having Issues?

### Check System Requirements
- **Python**: 3.10 or 3.11 (not 3.12+)
- **Node.js**: 18.0 or higher
- **RAM**: At least 4GB available
- **Disk Space**: At least 2GB free

### Common Fixes
1. **Restart your terminal** after installing build tools
2. **Run as Administrator** (Windows) if permission errors occur
3. **Disable antivirus temporarily** during installation
4. **Check firewall settings** if network errors occur
5. **Use a VPN** if package downloads are slow/failing

### Get Help
- Check the error logs in detail
- Search for the specific error message
- Check GitHub issues: https://github.com/MrVish/chatbot-topup/issues

---

## Quick Reference Commands

### Backend
```bash
# Activate environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Both
```bash
# From project root (Windows)
start_servers.bat

# From project root (Linux/Mac)
./start_servers.sh
```
