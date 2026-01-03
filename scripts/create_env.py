"""Simple script to create .env.example file interactively"""

def get_input(prompt, default=None):
    """Get user input with optional default value"""
    if default:
        full_prompt = f"{prompt} (default: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    return value if value else default

print("=" * 50)
print("Environment Configuration Setup")
print("=" * 50)
print()

# Login Configuration
print("Login Configuration:")
login_password = get_input("Login Password", "thermax")
print()

# Server Configuration
print("Server Configuration:")
port = get_input("Port", "5000")
test_duration = get_input("Test Duration (minutes)", "31")
print()

# Backend Configuration
print("Backend Configuration:")
backend_url = get_input("Backend URL", "http://localhost:4000")
factory_code = get_input("Factory Code", "factory-a")
print()

# Create the .env.example file
with open('.env.example', 'w') as f:
    f.write(f"""# Login Configuration
LOGIN_PASSWORD={login_password}

# Server Configuration
PORT={port}
TEST_DURATION_MINUTES={test_duration}

# Backend Configuration
BACKEND_URL={backend_url}
FACTORY_CODE={factory_code}
""")

print("✅ Created .env.example file with your configuration")

