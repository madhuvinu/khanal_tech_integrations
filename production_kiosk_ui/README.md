# Production Kiosk UI

A Vue.js-based production monitoring dashboard for Khanal Tech Integrations plants.

## Features

- **Multi-Plant Support**: NandhiHills, Dogsee, Mallur, Champawath, Krishnagiri
- **Real-time Dashboard**: Production metrics, efficiency tracking, and line status
- **Plant-Specific Modules**: Each plant has its own dashboard and components
- **Responsive Design**: Works on desktop and mobile devices
- **Authentication**: Plant-specific login system
- **Charts & Analytics**: Interactive charts using Chart.js

## Quick Start

### Development Server
```bash
npm run dev
```
The application will be available at: **http://localhost:3000**

### Production Build
```bash
npm run build
```

## Plant Access

1. **Main Dashboard**: http://localhost:3000
2. **Plant Login**: http://localhost:3000/login/{PlantName}
3. **Plant Dashboard**: http://localhost:3000/plant/{PlantName}

### Available Plants
- NandhiHills
- Dogsee  
- Mallur
- Champawath
- Krishnagiri

## Demo Credentials

For testing purposes, use any non-empty username and password to login.

## Project Structure

```
src/
├── views/           # Main application views
├── components/      # Reusable components
├── modules/         # Plant-specific modules
│   ├── NandhiHills/
│   ├── Dogsee/
│   ├── Mallur/
│   ├── Champawath/
│   └── Krishnagiri/
├── api/             # API configuration
├── store/           # State management
└── utils/           # Helper functions
```

## Customization

Each plant module can be customized independently:
- Add plant-specific components in `modules/{PlantName}/components/`
- Update API endpoints in `modules/{PlantName}/api/index.js`
- Modify dashboard layout in `modules/{PlantName}/Dashboard.vue`

## Technologies Used

- Vue 3 with Composition API
- Vue Router 4
- Pinia for state management
- Tailwind CSS for styling
- Chart.js for data visualization
- Vite for build tooling
