# Port Configuration

## Dynamic Port Support

The kiosk application now supports dynamic port configuration for the Frappe backend. No more hardcoded ports!

## How It Works

1. **Production Mode**: When served from Frappe directly (e.g., `/kiosk`), the app uses same-origin API calls (`/api`)
2. **Development Mode**: When running on Vite dev server (port 8081), it automatically routes to the Frappe backend

## Configuration Options

### Environment Variable (Recommended)
Create a `.env` file in the kiosk-frontend directory:

```bash
# For port 8003 (default)
VITE_FRAPPE_PORT=8003

# For port 8000
VITE_FRAPPE_PORT=8000

# For port 8001
VITE_FRAPPE_PORT=8001
```

### Automatic Detection
If no environment variable is set, the app will:
- Use port 8003 for localhost
- Use port 8000 for other hosts

## Testing Different Ports

1. **Change Frappe port**:
   ```bash
   bench --site your-site start --port 8000
   ```

2. **Set environment variable**:
   ```bash
   echo "VITE_FRAPPE_PORT=8000" > kiosk-frontend/.env
   ```

3. **Rebuild kiosk**:
   ```bash
   cd kiosk-frontend
   yarn build
   ```

4. **Copy assets**:
   ```bash
   cp -r ../khanal_tech_integrations/www/kiosk/assets/* ../khanal_tech_integrations/public/kiosk/assets/
   ```

## Benefits

✅ **No hardcoded ports** - works with any port  
✅ **Environment-specific** - different ports for dev/staging/prod  
✅ **Automatic detection** - smart defaults  
✅ **Production ready** - same-origin in production  

## Troubleshooting

If you see API connection errors:
1. Check that the Frappe backend is running on the expected port
2. Verify the `VITE_FRAPPE_PORT` environment variable
3. Rebuild the kiosk frontend after changing ports
4. Clear browser cache
