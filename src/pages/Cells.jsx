import React, { useState, useEffect } from 'react'
import { Box, Typography, Card, CardContent, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip } from '@mui/material'

function Cells() {
  const [loading, setLoading] = useState(true)
  const [cells, setCells] = useState([])

  useEffect(() => {
    fetchCells()
  }, [])

  const fetchCells = async () => {
    try {
      const response = await fetch('/api/cells')
      if (response.ok) {
        const data = await response.json()
        setCells(data)
      } else {
        loadDemoData()
      }
    } catch (error) {
      loadDemoData()
    } finally {
      setLoading(false)
    }
  }

  const loadDemoData = () => {
    const demoData = Array.from({ length: 20 }, (_, i) => ({
      id: `Cell-${i + 1}`,
      status: Math.random() > 0.1 ? 'Active' : 'Inactive',
      throughput: (Math.random() * 100 + 20).toFixed(2),
      latency: (Math.random() * 30 + 5).toFixed(2),
      users: Math.floor(Math.random() * 100),
      location: `Site-${Math.floor(i / 3) + 1}`,
    }))
    setCells(demoData)
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Cells
      </Typography>
      
      <Card>
        <CardContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cell ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell align="right">Throughput (Mbps)</TableCell>
                  <TableCell align="right">Latency (ms)</TableCell>
                  <TableCell align="right">Users</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cells.map((cell) => (
                  <TableRow key={cell.id}>
                    <TableCell>{cell.id}</TableCell>
                    <TableCell>
                      <Chip 
                        label={cell.status} 
                        color={cell.status === 'Active' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{cell.location}</TableCell>
                    <TableCell align="right">{cell.throughput}</TableCell>
                    <TableCell align="right">{cell.latency}</TableCell>
                    <TableCell align="right">{cell.users}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Cells
