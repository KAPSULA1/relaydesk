# RelayDesk - Quick Deploy Guide

**⚡ 15-Minute Production Deployment**

## Prerequisites
- [ ] GitHub account
- [ ] Render account (free)
- [ ] Vercel account (free)

---

## Step 1: Verify (2 min)

```bash
./verify-deployment-ready.sh
```

If passes ✅, continue. If fails ❌, fix errors first.

---

## Step 2: Push to GitHub (1 min)

```bash
git add .
git commit -m "Production deployment ready"
git push origin main
```

---

## Step 3: Render Backend (6 min)

### 3.1 Create Database
1. Go to https://dashboard.render.com/
2. New + → PostgreSQL
3. Settings:
   - Name: `relaydesk-db`
   - Region: `Oregon`
   - Plan: **Free**
4. Click "Create"

### 3.2 Create Redis
1. New + → Redis
2. Settings:
   - Name: `relaydesk-redis`
   - Region: `Oregon`
   - Plan: **Free**
3. Click "Create"

### 3.3 Create Web Service
1. New + → Web Service
2. Connect GitHub → Select repository
3. Settings:
   ```
   Name: relaydesk-backend
   Region: Oregon
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   ```
4. Build Command:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput --clear
   ```
5. Start Command:
   ```bash
   gunicorn relaydesk.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4
   ```
6. Plan: **Free**

### 3.4 Add Environment Variables
```bash
DJANGO_SETTINGS_MODULE=relaydesk.settings.prod
SECRET_KEY=<click "Generate" button>
DATABASE_URL=<link from relaydesk-db service>
REDIS_URL=<link from relaydesk-redis service>
ALLOWED_HOSTS=relaydesk-backend.onrender.com
CORS_ALLOWED_ORIGINS=https://PLACEHOLDER.vercel.app
CSRF_TRUSTED_ORIGINS=https://PLACEHOLDER.vercel.app
PYTHONUNBUFFERED=1
```

⚠️ Use PLACEHOLDER for now, we'll update after Vercel deployment

7. Click "Create Web Service"

### 3.5 Run Migrations
1. Wait for deployment to complete
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py migrate
   ```

✅ **Backend URL**: Copy your URL (e.g., `https://relaydesk-backend.onrender.com`)

---

## Step 4: Vercel Frontend (4 min)

### 4.1 Import Project
1. Go to https://vercel.com/new
2. Import Git Repository → Select your repo
3. Settings:
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   ```
4. Environment Variables:
   ```bash
   NEXT_PUBLIC_API_URL=https://relaydesk-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://relaydesk-backend.onrender.com
   NEXT_PUBLIC_APP_NAME=RelayDesk
   NEXT_PUBLIC_ENV=production
   ```
   Replace `relaydesk-backend.onrender.com` with your actual Render URL

5. Click "Deploy"

✅ **Frontend URL**: Copy your URL (e.g., `https://relaydesk.vercel.app`)

---

## Step 5: Update CORS (2 min)

1. Go back to Render → Web Service → Environment
2. Update these variables with your Vercel URL:
   ```bash
   CORS_ALLOWED_ORIGINS=https://relaydesk.vercel.app
   CSRF_TRUSTED_ORIGINS=https://relaydesk.vercel.app
   ```
3. Click "Save Changes" (triggers auto-redeploy)

---

## Step 6: Test (2 min)

### Test Backend
```bash
curl https://your-backend.onrender.com/api/health/
```
Expected: `{"status": "healthy", "message": "RelayDesk API is running"}`

### Test Frontend
1. Open `https://your-frontend.vercel.app`
2. Register a new account
3. Create a chat room
4. Send a message

---

## Troubleshooting

### CSRF Error (403)
```bash
# In Render, verify these match EXACTLY:
CORS_ALLOWED_ORIGINS=https://your-actual-vercel-url.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-actual-vercel-url.vercel.app
```

### Database Error
```bash
# In Render Shell:
python manage.py migrate
```

### Redis Error
```bash
# Verify REDIS_URL is linked in Render environment variables
```

---

## Done! 🎉

Your app is live at:
- **Frontend**: https://your-frontend.vercel.app
- **Backend**: https://your-backend.onrender.com
- **API Docs**: https://your-backend.onrender.com/admin

---

## Next Steps

1. ✅ Set up monitoring: https://uptimerobot.com/
2. ✅ Add custom domain (optional)
3. ✅ Enable error tracking with Sentry (optional)

---

## Full Documentation

- **Complete Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Checklist**: [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **Summary**: [PRODUCTION_READY_SUMMARY.md](./PRODUCTION_READY_SUMMARY.md)

---

**Cost**: $0/month (100% free tier)
