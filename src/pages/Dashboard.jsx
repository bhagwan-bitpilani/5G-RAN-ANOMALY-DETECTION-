import React, { useState, useEffect } from 'react'
import { Box, Grid, Card, CardContent, Typography, CircularProgress } from '@mui/material'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [kpiData, setKpiData] = useState([])
  const [stats, setStats] = useState({
    totalCells: 0,
    activeCells: 0,
    avgThroughput: 0,
    anomalies: 0,
  })

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard')
      if (response.ok) {
        const data = await response.json()
        setKpiData(data.kpiData || [])
        setStats(data.stats || stats)
      } else {
        // Demo data
        loadDemoData()
      }
    } catch (error) {
      // Demo data
      loadDemoData()
    } finally {
      setLoading(false)
    }
  }

  const loadDemoData = () => {
    const demoData = Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      throughput: Math.random() * 100 + 50,
      latency: Math.random() * 20 + 10,
      packetLoss: Math.random() * 5,
    }))
    setKpiData(demoData)
    setStats({
      totalCells: 150,
      activeCells: 142,
      avgThroughput: 75.5,
      anomalies: 3,
    })
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
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Cells
              </Typography>
              <Typography variant="h4">
                {stats.totalCells}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Cells
              </Typography>
              <Typography variant="h4">
                {stats.activeCells}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Avg Throughput (Mbps)
              </Typography>
              <Typography variant="h4">
                {stats.avgThroughput.toFixed(1)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Anomalies
              </Typography>
              <Typography variant="h4" color="error">
                {stats.anomalies}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Throughput Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={kpiData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="throughput" stroke="#1976d2" name="Throughput (Mbps)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Latency & Packet Loss
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={kpiData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="latency" fill="#dc004e" name="Latency (ms)" />
                  <Bar dataKey="packetLoss" fill="#ff9800" name="Packet Loss (%)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
