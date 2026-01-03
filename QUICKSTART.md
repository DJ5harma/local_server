# Quick Start Guide

## Creating Virtual Environment

### Windows (PowerShell)
```powershell
cd local_server
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Windows (CMD)
```cmd
cd local_server
python -m venv venv
venv\Scripts\activate.bat
```

### Linux/Mac
```bash
cd local_server
python3 -m venv venv
source venv/bin/activate
```

**Note:** If you get an execution policy error on Windows PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Windows (PowerShell)

1. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   # Or use the helper script if it exists:
   # .\activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Create .env file:**
   ```powershell
   python scripts\create_env.py
   # Or manually copy config\.env.example to .env
   ```

4. **Run the server:**
   ```powershell
   python run.py
   ```

5. **Access the HMI:**
   Open browser to `http://localhost:5000`

## Windows (CMD)

1. **Activate virtual environment:**
   ```cmd
   activate.bat
   ```

2. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Create .env file:**
   ```cmd
   python scripts\create_env.py
   ```

4. **Run the server:**
   ```cmd
   python run.py
   ```

## Linux/Mac

1. **Activate virtual environment:**
   ```bash
   source activate.sh
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file:**
   ```bash
   python scripts/create_env.py
   # Or manually: cp config/.env.example .env
   ```

4. **Run the server:**
   ```bash
   python run.py
   ```

## Default Login

- **Password:** `thermax` (can be changed in `.env` file)

## Deactivate Virtual Environment

When you're done, deactivate the virtual environment:
```bash
deactivate
```

