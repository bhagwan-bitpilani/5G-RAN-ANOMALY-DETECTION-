import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin, Alert } from 'antd'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import CellAnalysis from './pages/CellAnalysis'
import Cells from './pages/Cells'
import Upload from './pages/Upload'
import Login from './pages/Login'
import './styles/App.css'

const { Content } = Layout

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
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="Loading..." />
      </div>
    )
  }

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        {isAuthenticated && <Header onLogout={handleLogout} />}
        <Content style={{ padding: isAuthenticated ? '24px' : '0', background: '#f0f2f5' }}>
          {apiStatus === 'unreachable' && isAuthenticated && (
            <Alert
              message="Running in Demo Mode"
              description="App server is unavailable. Showing sample data."
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
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
        </Content>
      </Layout>
    </Router>
  )
}

export default App
