# Production Kiosk UI - Deployment Guide

## Environment Configuration

This application is designed to work across different environments without hardcoded URLs or ports.

### Automatic Configuration (Recommended)

The application automatically detects the current domain and port using `window.location.origin`, so it will work on any domain without configuration.

### Manual Configuration (Optional)

If you need to override the automatic detection, create a `.env` file:

```bash
# Copy the example file
cp env.example .env
```

Then edit `.env` with your specific values:

```env
# For development
VITE_API_TARGET=http://localhost:8000

# For production (optional - will use window.location.origin if not set)
VITE_BASE_URL=https://khanaltech.com

# For multi-site Frappe setups (optional)
VITE_SITE_NAME=your-site-name
```

## Deployment Scenarios

### 1. Local Development
```bash
# Create .env file first
cp env.example .env
# Edit .env and set VITE_API_TARGET to your Frappe server

# Then run development server
npm run dev

# Or with custom API target (one-time)
VITE_API_TARGET=http://localhost:8001 npm run dev
```

### 2. Production Deployment
```bash
# Build for production
npm run build

# The built files will work on any domain automatically
# Copy dist/ contents to your Frappe public directory
```

### 3. Different Environments

#### Development Environment
- URL: `http://dev.khanaltech.com:8000`
- Port: 8000
- **No configuration needed** - works automatically

#### Staging Environment  
- URL: `https://staging.khanaltech.com`
- Port: 443 (HTTPS)
- **No configuration needed** - works automatically

#### Production Environment
- URL: `https://khanaltech.com`
- Port: 443 (HTTPS)
- **No configuration needed** - works automatically

## How It Works

1. **Automatic URL Detection**: The app uses `window.location.origin` to get the current domain and port
2. **Environment Variables**: Optional override via `VITE_BASE_URL` environment variable
3. **Dynamic API Endpoints**: All API calls are built dynamically based on the current URL
4. **No Hardcoded Values**: No URLs, ports, or domains are hardcoded in the source code

## Testing Different Environments

To test on different domains/ports:

1. **Local with different port**:
   ```bash
   # Start your Frappe server on port 8001
   bench serve --port 8001
   
   # Access: http://localhost:8001/kiosk
   # Works automatically!
   ```

2. **Different domain**:
   ```bash
   # Add to your /etc/hosts
   echo "127.0.0.1 mycompany.local" >> /etc/hosts
   
   # Access: http://mycompany.local:8000/kiosk
   # Works automatically!
   ```

3. **HTTPS production**:
   ```bash
   # Access: https://khanaltech.com/kiosk
   # Works automatically!
   ```

## Troubleshooting

If the app doesn't work on a new environment:

1. Check browser console for errors
2. Verify the Frappe server is running on the expected port
3. Ensure the kiosk.html file is properly configured
4. Check that all asset files are accessible

The application should work on any domain/port combination without modification!
