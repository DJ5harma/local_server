# Quick Start Guide

## Windows (PowerShell)

1. **Activate virtual environment:**
   ```powershell
   .\activate.ps1
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

