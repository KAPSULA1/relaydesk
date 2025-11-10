#!/bin/bash

# RelayDesk Deployment Readiness Check
# Run this script before deploying to production

echo "🔍 RelayDesk Deployment Readiness Check"
echo "========================================"
echo ""

ERRORS=0
WARNINGS=0

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ ERROR: render.yaml not found. Are you in the project root?"
    exit 1
fi

echo "📦 Checking Backend..."
echo "---"

# Check backend requirements.txt
if [ -f "backend/requirements.txt" ]; then
    echo "✅ requirements.txt exists"

    # Check for critical packages
    if grep -q "gunicorn" backend/requirements.txt; then
        echo "✅ gunicorn found"
    else
        echo "❌ ERROR: gunicorn not in requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "whitenoise" backend/requirements.txt; then
        echo "✅ whitenoise found"
    else
        echo "❌ ERROR: whitenoise not in requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "dj-database-url" backend/requirements.txt; then
        echo "✅ dj-database-url found"
    else
        echo "❌ ERROR: dj-database-url not in requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "psycopg2" backend/requirements.txt; then
        echo "✅ psycopg2 found"
    else
        echo "❌ ERROR: psycopg2 not in requirements.txt"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ ERROR: backend/requirements.txt not found"
    ERRORS=$((ERRORS + 1))
fi

# Check for production settings
if [ -f "backend/relaydesk/settings/prod.py" ]; then
    echo "✅ Production settings exist"

    # Check DEBUG=False
    if grep -q "DEBUG = False" backend/relaydesk/settings/prod.py; then
        echo "✅ DEBUG=False in production"
    else
        echo "⚠️  WARNING: DEBUG might not be False in production"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "❌ ERROR: backend/relaydesk/settings/prod.py not found"
    ERRORS=$((ERRORS + 1))
fi

# Check for middleware
if [ -f "backend/relaydesk/middleware.py" ]; then
    echo "✅ Custom middleware exists"
else
    echo "⚠️  WARNING: Custom middleware not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "🎨 Checking Frontend..."
echo "---"

# Check frontend package.json
if [ -f "frontend/package.json" ]; then
    echo "✅ package.json exists"

    if grep -q "\"next\"" frontend/package.json; then
        echo "✅ Next.js dependency found"
    else
        echo "❌ ERROR: Next.js not in package.json"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ ERROR: frontend/package.json not found"
    ERRORS=$((ERRORS + 1))
fi

# Check for .env.example
if [ -f "frontend/.env.example" ]; then
    echo "✅ Frontend .env.example exists"
else
    echo "⚠️  WARNING: frontend/.env.example not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "🔧 Checking Configuration Files..."
echo "---"

# Check render.yaml
if [ -f "render.yaml" ]; then
    echo "✅ render.yaml exists"

    # Check for critical configurations
    if grep -q "type: web" render.yaml; then
        echo "✅ Web service configured"
    else
        echo "❌ ERROR: Web service not configured in render.yaml"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "databases:" render.yaml; then
        echo "✅ Database configured"
    else
        echo "⚠️  WARNING: Database might not be configured"
        WARNINGS=$((WARNINGS + 1))
    fi

    if grep -q "type: redis" render.yaml; then
        echo "✅ Redis configured"
    else
        echo "⚠️  WARNING: Redis might not be configured"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "❌ ERROR: render.yaml not found"
    ERRORS=$((ERRORS + 1))
fi

# Check vercel.json
if [ -f "vercel.json" ]; then
    echo "✅ vercel.json exists"
else
    echo "⚠️  WARNING: vercel.json not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "🔒 Checking Security..."
echo "---"

# Check for .env files in git
if git ls-files | grep -q "\.env$"; then
    echo "❌ ERROR: .env file is tracked by git!"
    echo "   Run: git rm --cached backend/.env frontend/.env"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ .env files not tracked"
fi

# Check .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "\.env" .gitignore; then
        echo "✅ .env in .gitignore"
    else
        echo "⚠️  WARNING: .env might not be in .gitignore"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""
echo "📝 Checking Documentation..."
echo "---"

if [ -f "DEPLOYMENT.md" ]; then
    echo "✅ DEPLOYMENT.md exists"
else
    echo "⚠️  WARNING: DEPLOYMENT.md not found"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "DEPLOYMENT_CHECKLIST.md" ]; then
    echo "✅ DEPLOYMENT_CHECKLIST.md exists"
else
    echo "⚠️  WARNING: DEPLOYMENT_CHECKLIST.md not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "📊 Summary"
echo "=========="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready for deployment 🚀"
    echo ""
    echo "Next steps:"
    echo "1. Review DEPLOYMENT.md for deployment instructions"
    echo "2. Use DEPLOYMENT_CHECKLIST.md to track your progress"
    echo "3. Commit and push your code to GitHub"
    echo "4. Deploy to Render and Vercel"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  $WARNINGS warning(s) found"
    echo "   Consider fixing warnings before deploying"
    echo ""
    echo "You can proceed with deployment, but review the warnings above."
    exit 0
else
    echo "❌ $ERRORS error(s) found"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠️  $WARNINGS warning(s) found"
    fi
    echo ""
    echo "Please fix the errors above before deploying."
    exit 1
fi
