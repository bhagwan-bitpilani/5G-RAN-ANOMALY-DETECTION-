import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline, Box, CircularProgress, Alert } from '@mui/material'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import CellAnalysis from './pages/CellAnalysis'
import Cells from './pages/Cells'
import Upload from './pages/Upload'
import Login from './pages/Login'
import './styles/App.css'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    checkAuthentication()
    checkAppHealth()
  }, [])

  const checkAuthentication = () => {
    const token = localStorage.getItem('token')
    if (token) {
      setIsAuthenticated(true)
    }
    setLoading(false)
  }

  const checkAppHealth = async () => {
    try {
      const response = await fetch('/api/health', { 
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.ok) {
        setApiStatus('healthy')
      } else {
        setApiStatus('unhealthy')
      }
    } catch (error) {
      console.error('App health check failed:', error)
      setApiStatus('unreachable')
    }
  }

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
          <CircularProgress size={60} />
        </Box>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
          {isAuthenticated && <Header onLogout={handleLogout} />}
          <Box sx={{ p: isAuthenticated ? 3 : 0 }}>
            {apiStatus === 'unreachable' && isAuthenticated && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Running in Demo Mode - App server is unavailable. Showing sample data.
              </Alert>
            )}
            <Routes>
              <Route 
                path="/login" 
                element={
                  isAuthenticated ? 
                  <Navigate to="/dashboard" replace /> : 
                  <Login onLogin={handleLogin} />
                } 
              />
              <Route 
                path="/dashboard" 
                element={
                  isAuthenticated ? 
                  <Dashboard /> : 
                  <Navigate to="/login" replace />
                } 
              />
              <Route 
                path="/cell-analysis" 
                element={
                  isAuthenticated ? 
                  <CellAnalysis /> : 
                  <Navigate to="/login" replace />
                } 
              />
              <Route 
                path="/cells" 
                element={
                  isAuthenticated ? 
                  <Cells /> : 
                  <Navigate to="/login" replace />
                } 
              />
              <Route 
                path="/upload" 
                element={
                  isAuthenticated ? 
                  <Upload /> : 
                  <Navigate to="/login" replace />
                } 
              />
              <Route 
                path="/" 
                element={
                  <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
                } 
              />
              <Route 
                path="*" 
                element={
                  <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
                } 
              />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  )
}

export default App
