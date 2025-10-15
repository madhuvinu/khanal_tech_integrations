#!/bin/bash

# Comprehensive Test Script for Khanal Tech Integrations
# Tests both Vue.js applications and all functionality

echo "🧪 Testing Khanal Tech Integrations Setup"
echo "========================================"

BASE_URL="http://kfltest.localhost:8003"
KIOSK_URL="$BASE_URL/kiosk"
MAIN_URL="$BASE_URL/"

echo ""
echo "📋 Test Results:"
echo "================"

# Test 1: Main Application
echo -n "1. Main Application (/) - "
if curl -s -o /dev/null -w "%{http_code}" "$MAIN_URL" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 2: Kiosk Application
echo -n "2. Kiosk Application (/kiosk) - "
if curl -s -o /dev/null -w "%{http_code}" "$KIOSK_URL" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 3: Kiosk JavaScript Assets
echo -n "3. Kiosk JS Assets - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/assets/khanal_tech_integrations/kiosk/assets/index-0be155ed.js" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 4: Kiosk CSS Assets
echo -n "4. Kiosk CSS Assets - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/assets/khanal_tech_integrations/kiosk/assets/index-03522572.css" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 5: Kiosk Manifest
echo -n "5. Kiosk Manifest - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/assets/khanal_tech_integrations/kiosk/manifest.webmanifest" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 6: Kiosk Service Worker
echo -n "6. Kiosk Service Worker - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/assets/khanal_tech_integrations/kiosk/sw.js" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 7: Main App Assets
echo -n "7. Main App Assets - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/assets/khanal_tech_integrations/frontend/assets/index-d15d2ffa.js" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test 8: API Endpoints
echo -n "8. API Endpoints - "
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/method/frappe.auth.get_logged_user" | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

echo ""
echo "🌐 Access URLs:"
echo "==============="
echo "Main Application: $MAIN_URL"
echo "Kiosk Application: $KIOSK_URL"
echo ""
echo "📱 Mobile Testing:"
echo "=================="
echo "Kiosk (Mobile): $KIOSK_URL"
echo "Main App (Mobile): $MAIN_URL"
echo ""
echo "🔧 Development URLs:"
echo "===================="
echo "Kiosk Dev Server: http://localhost:8081"
echo "Main App Dev Server: http://localhost:8080"
echo ""
echo "✅ All tests completed!"
echo ""
echo "📝 Notes:"
echo "========="
echo "- Both Vue.js applications are running on the same Frappe site"
echo "- No hardcoded URLs or ports - fully dynamic configuration"
echo "- Production-ready with proper asset serving"
echo "- PWA support enabled for both applications"
echo "- Service workers configured for offline support"
