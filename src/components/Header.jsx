import React from 'react'
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material'
import { useNavigate, useLocation } from 'react-router-dom'

function Header({ onLogout }) {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Cell Analysis', path: '/cell-analysis' },
    { label: 'Cells', path: '/cells' },
    { label: 'Upload', path: '/upload' },
  ]

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 4 }}>
          5G NR Monitor
        </Typography>
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
          {menuItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              onClick={() => navigate(item.path)}
              sx={{
                fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                textDecoration: location.pathname === item.path ? 'underline' : 'none',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
        <Button color="inherit" onClick={onLogout}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  )
}

export default Header
