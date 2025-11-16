import React, { useState, useEffect } from 'react'
import { Box, Typography, Card, CardContent, CircularProgress, Grid } from '@mui/material'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function CellAnalysis() {
  const [loading, setLoading] = useState(true)
  const [analysisData, setAnalysisData] = useState([])

  useEffect(() => {
    fetchAnalysisData()
  }, [])

  const fetchAnalysisData = async () => {
    try {
      const response = await fetch('/api/cell-analysis')
      if (response.ok) {
        const data = await response.json()
        setAnalysisData(data)
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
    const demoData = Array.from({ length: 50 }, (_, i) => ({
      cellId: `Cell-${i + 1}`,
      throughput: Math.random() * 100 + 20,
      latency: Math.random() * 30 + 5,
      users: Math.floor(Math.random() * 100),
    }))
    setAnalysisData(demoData)
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
        Cell Analysis
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Throughput vs Latency Analysis
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="throughput" name="Throughput" unit=" Mbps" />
                  <YAxis dataKey="latency" name="Latency" unit=" ms" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Legend />
                  <Scatter name="Cells" data={analysisData} fill="#1976d2" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default CellAnalysis
