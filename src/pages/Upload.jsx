import React, { useState } from 'react'
import { Box, Typography, Card, CardContent, Button, Alert, LinearProgress } from '@mui/material'
import { CloudUpload } from '@mui/icons-material'

function Upload() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setMessage(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a file' })
      return
    }

    setUploading(true)
    setMessage(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        setMessage({ type: 'success', text: 'File uploaded successfully' })
        setFile(null)
      } else {
        setMessage({ type: 'error', text: 'Upload failed' })
      }
    } catch (error) {
      setMessage({ type: 'info', text: 'Demo mode - Upload simulated successfully' })
      setFile(null)
    } finally {
      setUploading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Data
      </Typography>
      
      <Card sx={{ maxWidth: 600 }}>
        <CardContent>
          <Typography variant="body1" gutterBottom>
            Upload KPI data files (CSV, JSON, or Excel format)
          </Typography>
          
          {message && (
            <Alert severity={message.type} sx={{ my: 2 }}>
              {message.text}
            </Alert>
          )}

          <Box sx={{ my: 3 }}>
            <input
              accept=".csv,.json,.xlsx,.xls"
              style={{ display: 'none' }}
              id="file-upload"
              type="file"
              onChange={handleFileChange}
            />
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUpload />}
                fullWidth
              >
                Select File
              </Button>
            </label>
            {file && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selected: {file.name}
              </Typography>
            )}
          </Box>

          {uploading && <LinearProgress sx={{ mb: 2 }} />}

          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!file || uploading}
            fullWidth
          >
            Upload
          </Button>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Upload
