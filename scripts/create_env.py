"""Simple script to create .env.example file"""
with open('.env.example', 'w') as f:
    f.write("""# Login Configuration
LOGIN_PASSWORD=thermax

# Server Configuration
PORT=5000
TEST_DURATION_MINUTES=30

# Backend Configuration
BACKEND_URL=http://localhost:4000
FACTORY_CODE=factory-a
""")
print("✅ Created .env.example file")

