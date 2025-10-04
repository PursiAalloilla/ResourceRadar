# 🚀 Deploy to Heroku

## Prerequisites
- Heroku CLI installed
- Docker installed
- Heroku account

## Step 1: Install Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

## Step 2: Login to Heroku
```bash
heroku login
```

## Step 3: Create Heroku App
```bash
# Create app
heroku create your-app-name

# Add container stack
heroku stack:set container -a your-app-name
```

## Step 4: Set Environment Variables
```bash
# Backend environment variables
heroku config:set DATABASE_URI=sqlite:///emergency_support.db -a your-app-name
heroku config:set OPENAI_MODEL=gpt-4o-mini -a your-app-name
heroku config:set OPENAI_API_KEY=your-openai-key -a your-app-name

# Frontend environment variables
heroku config:set REACT_APP_MAPBOX_TOKEN=pk.eyJ1IjoidnA0NTEiLCJhIjoiY21nYjltdXB5MHdkYjJqczdkdzdoMzJsbiJ9.7nq6toK2LmmlYx2wZupdVg -a your-app-name
```

## Step 5: Deploy
```bash
# Deploy using Docker
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Or deploy specific branch
git push heroku your-branch:main
```

## Step 6: Scale Dynos (Optional)
```bash
# Scale web dyno
heroku ps:scale web=1 -a your-app-name

# Check dyno status
heroku ps -a your-app-name
```

## Step 7: View Logs
```bash
heroku logs --tail -a your-app-name
```

## Step 8: Open App
```bash
heroku open -a your-app-name
```

## Important Notes:
- Heroku uses a single port (from $PORT environment variable)
- You'll need to modify the architecture to serve all services from one port
- Consider using a reverse proxy (nginx) or serve static files from the backend
- Heroku has a 500MB slug size limit
- Free tier has sleep mode after 30 minutes of inactivity
