# 5G NR KPI Monitoring Dashboard

A React-based frontend application for monitoring 5G NR (New Radio) Key Performance Indicators (KPIs).

## Technology Stack

- **Frontend Framework**: React 18.2
- **Build Tool**: Vite 4.4
- **UI Library**: Material-UI (MUI) 5.14
- **Charts**: Recharts 2.8
- **Routing**: React Router DOM 6.15
- **HTTP Client**: Axios 1.5

## Project Structure

```
/vercel/sandbox/
├── src/
│   ├── components/       # Reusable React components
│   │   └── Header.jsx
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx
│   │   ├── CellAnalysis.jsx
│   │   ├── Cells.jsx
│   │   ├── Upload.jsx
│   │   └── Login.jsx
│   ├── styles/          # CSS files
│   │   ├── App.css
│   │   └── index.css
│   ├── App.jsx          # Main App component
│   └── main.jsx         # Entry point
├── backend/             # Python backend files (separate)
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
└── package.json         # Node.js dependencies

```

## Getting Started

### Prerequisites

- Node.js 22.x
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

Build for production:
```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Features

- **Dashboard**: Real-time KPI monitoring with charts
- **Cell Analysis**: Scatter plot analysis of cell performance
- **Cells**: Tabular view of all cells with status
- **Upload**: File upload functionality for KPI data
- **Authentication**: Login/logout functionality

## API Integration

The frontend proxies API requests to the backend server (default: `http://localhost:8000`). Configure the backend URL in `vite.config.js` or via the `VITE_API_BASE_URL` environment variable.

## Demo Mode

The application includes demo mode with sample data when the backend is unavailable.

## Backend

Python backend files are located in the `backend/` directory. This is a separate component from the Node.js frontend.
