import React, { useState } from 'react'
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material'

function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        onLogin()
      } else {
        setError('Invalid credentials')
      }
    } catch (err) {
      // Demo mode - allow any login
      localStorage.setItem('token', 'demo-token')
      localStorage.setItem('user', JSON.stringify({ username }))
      onLogin()
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
      }}
    >
      <Card sx={{ minWidth: 400 }}>
        <CardContent>
          <Typography variant="h5" component="h1" gutterBottom align="center">
            5G NR Monitor
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom align="center" sx={{ mb: 3 }}>
            Sign in to continue
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              variant="outlined"
              margin="normal"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              variant="outlined"
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button
              fullWidth
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              sx={{ mt: 3 }}
            >
              Sign In
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Login
