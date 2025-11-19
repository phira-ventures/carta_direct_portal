# Railway Deployment Guide - Carta Direct Portal

## Quick Fix for Current Error

Your app is crashing because Railway can't find the correct module. Follow these steps:

---

## Step 1: Add Procfile to Your Repository

Create a file named `Procfile` (no extension) in your project root with this content:

```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT
```

**Then commit and push:**
```bash
git add Procfile
git commit -m "Add Procfile for Railway deployment"
git push
```

---

## Step 2: Set Environment Variables in Railway

Go to your Railway project → Variables section and add these:

### Required Variables:

**SECRET_KEY**
```
Generate with: python -c "import secrets; print(secrets.token_hex(32))"
Example: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### Recommended Variables:

**FLASK_ENV**
```
production
```

**COMPANY_NAME**
```
Your Company Name Here
```

**ADMIN_PASSWORD**
```
YourSecurePassword123!
```

---

## Step 3: Verify Railway Configuration

### Check Build Settings:
- **Builder**: Nixpacks (default, should auto-detect Python)
- **Start Command**: Should use Procfile automatically (or manually set: `gunicorn wsgi:application --bind 0.0.0.0:$PORT`)

### Check Root Directory:
- Should be `/` (root of your repository)
- If your code is in a subdirectory, update this

---

## Step 4: Deploy

Railway should automatically redeploy after you push the Procfile. If not:
1. Go to your Railway project
2. Click "Deploy" or trigger a manual deployment

---

## Verification Steps

After deployment, check the logs for:

✅ **Success indicators:**
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
[INFO] Booting worker with pid: X
[INFO] Stockholder Portal startup
```

✅ **Admin password output (if ADMIN_PASSWORD not set):**
```
============================================================
IMPORTANT: Default admin account created!
Email: admin@company.com
Password: <random-password>
Please change this password immediately after first login!
============================================================
```

❌ **Errors to watch for:**
- `ModuleNotFoundError: No module named 'main'` → Procfile not found or incorrect
- `SECRET_KEY environment variable must be set` → Missing SECRET_KEY in Railway Variables
- Module import errors → Check requirements.txt includes all dependencies

---

## Project Structure Checklist

Your repository should have these files in the root:

```
✅ app.py
✅ wsgi.py
✅ config.py
✅ database.py
✅ forms.py
✅ requirements.txt
✅ Procfile (NEW - add this!)
✅ .env.example (not deployed, just for reference)
✅ static/
✅ templates/
❌ .env (should NOT be in git - use Railway Variables instead)
```

---

## Requirements.txt Verification

Make sure your `requirements.txt` includes:
```
Flask
Flask-Login
Flask-WTF
gunicorn
python-dotenv
Werkzeug
email-validator
```

---

## Database Location

The app uses SQLite and stores the database at:
```
instance/database.db
```

⚠️ **Important:** Railway's filesystem is ephemeral. When your app restarts, the database will be lost unless you:
1. Use Railway's Volume feature to persist `instance/` directory
2. Or migrate to Railway's PostgreSQL addon (requires code changes)

### To Add Volume (Recommended):
1. In Railway: Settings → Volumes
2. Add volume: Mount path = `/app/instance`
3. This persists your SQLite database across deploys

---

## Common Issues & Solutions

### Issue: "Worker failed to boot"
**Solution:** Check that Procfile exists and environment variables are set

### Issue: "SECRET_KEY must be set"
**Solution:** Add SECRET_KEY in Railway Variables section

### Issue: Database resets on every deploy
**Solution:** Add a Railway Volume mounted at `/app/instance`

### Issue: Port binding errors
**Solution:** The Procfile now includes `--bind 0.0.0.0:$PORT` which Railway requires

### Issue: App works locally but not on Railway
**Solution:** 
- Ensure all dependencies are in requirements.txt
- Check that no local .env file settings are required but missing in Railway Variables

---

## Post-Deployment Security Checklist

After successful deployment:

1. ✅ Access your Railway app URL
2. ✅ Login with admin credentials (from logs or your set ADMIN_PASSWORD)
3. ✅ Immediately change admin password via the interface
4. ✅ Test creating a test stockholder account
5. ✅ Test logging in as the stockholder
6. ✅ Verify SSL/HTTPS is working (Railway provides this automatically)

---

## Environment Variables Summary

| Variable | Required | Where to Set | Example |
|----------|----------|--------------|---------|
| SECRET_KEY | YES | Railway Variables | (64 char hex string) |
| FLASK_ENV | Recommended | Railway Variables | production |
| COMPANY_NAME | Recommended | Railway Variables | MyStartup Inc |
| ADMIN_PASSWORD | Optional | Railway Variables | SecurePass123! |

---

## Getting Help

If you continue to have issues:

1. **Check Railway Logs:**
   - Build logs for deployment errors
   - Deploy logs for runtime errors

2. **Verify Files:**
   - Procfile exists in root
   - requirements.txt is complete
   - wsgi.py hasn't been modified

3. **Test Locally:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variable
   export SECRET_KEY="test-key-for-local"
   
   # Test gunicorn locally
   gunicorn wsgi:application --bind 0.0.0.0:5002
   ```

---

## Next Steps After Successful Deployment

1. Set up Volume for database persistence
2. Configure custom domain (optional)
3. Set up monitoring/alerts in Railway
4. Regular database backups (if using Volume)
5. Consider migrating to PostgreSQL for production use
