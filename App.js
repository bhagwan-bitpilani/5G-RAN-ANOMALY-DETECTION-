import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Card, CardContent, Typography, Grid, Box, Chip, Alert, Button, 
  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText,
  Paper, LinearProgress, Snackbar, IconButton
} from '@mui/material';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area
} from 'recharts';
import CloseIcon from '@mui/icons-material/Close';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import './App.css';

// API base URL from environment or default
const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [kpis, setKpis] = useState({});
  const [historicalData, setHistoricalData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [anomalyScore, setAnomalyScore] = useState(0);
  const [selectedCell, setSelectedCell] = useState('NR2600_001');
  const [selectedKpis, setSelectedKpis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // Available KPI options with display names and units
  const kpiOptions = useMemo(() => [
    { id: 'downlink_ue_throughput', name: 'Downlink UE Throughput', unit: 'Mbps', higherBetter: true },
    { id: 'downlink_prb_utilization', name: 'Downlink PRB Utilization', unit: '%', higherBetter: false },
    { id: 'data_session_setup_success_rate', name: 'Data Session Success Rate', unit: '%', higherBetter: true },
    { id: 'endc_add_setup_success_rate', name: 'ENDC ADD Success Rate', unit: '%', higherBetter: true },
    { id: 'inter_sgnb_change_success_rate', name: 'Inter SgNB Success Rate', unit: '%', higherBetter: true },
    { id: 'maximum_active_endc_user', name: 'Maximum Active ENDC Users', unit: 'users', higherBetter: false },
    { id: 'downlink_latency', name: 'Downlink Latency', unit: 'ms', higherBetter: false },
    { id: 'downlink_payload', name: 'Downlink Payload', unit: 'GB', higherBetter: true }
  ], []);

  // KPI thresholds based on 3GPP standards
  const kpiThresholds = useMemo(() => ({
    'downlink_ue_throughput': { min: 50, max: 1000, higherBetter: true }, // Mbps
    'downlink_prb_utilization': { min: 5, max: 85, higherBetter: false }, // %
    'data_session_setup_success_rate': { min: 98, max: 100, higherBetter: true }, // %
    'endc_add_setup_success_rate': { min: 95, max: 100, higherBetter: true }, // %
    'inter_sgnb_change_success_rate': { min: 90, max: 100, higherBetter: true }, // %
    'maximum_active_endc_user': { min: 1, max: 200, higherBetter: false }, // users
    'downlink_latency': { min: 1, max: 20, higherBetter: false }, // ms
    'downlink_payload': { min: 0.1, max: 500, higherBetter: true } // GB
  }), []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch current metrics
      const metricsResponse = await fetch(`${API_BASE_URL}/api/current-metrics`);
      if (!metricsResponse.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await metricsResponse.json();
      
      setKpis(metricsData.kpis || {});
      setAlerts(metricsData.anomalies ? metricsData.anomalies.map(msg => ({ 
        severity: 'error', 
        message: msg 
      })) : []);
      setAnomalyScore(metricsData.anomaly_score || 0);

      // Fetch historical data for charts
      const historicalResponse = await fetch(`${API_BASE_URL}/api/historical-data`);
      if (!historicalResponse.ok) throw new Error('Failed to fetch historical data');
      const historicalData = await historicalResponse.json();
      
      setHistoricalData(historicalData.historical_data || []);

    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error.message);
      setSnackbarOpen(true);
      
      // Set fallback data for demo
      setAlerts([{ 
        severity: 'warning', 
        message: 'Using demo data - Backend connection failed' 
      }]);
      setKpis({
        downlink_ue_throughput: 750000000,
        downlink_prb_utilization: 65,
        data_session_setup_success_rate: 99.2,
        endc_add_setup_success_rate: 97.5,
        inter_sgnb_change_success_rate: 94.8,
        maximum_active_endc_user: 145,
        downlink_latency: 12.5,
        downlink_payload: 187.3,
        timestamp: new Date().toISOString(),
        cell_id: 'NR2600_001'
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleKpiSelection = (event) => {
    setSelectedKpis(event.target.value);
  };

  const triggerAnomaly = async () => {
    try {
      // Send test anomaly data to backend
      const testData = {
        cell_id: selectedCell,
        downlink_ue_throughput: 25300000, // 25.3 Mbps
        downlink_prb_utilization: 92,
        downlink_latency: 28.7,
        data_session_setup_success_rate: 85.5,
        timestamp: new Date().toISOString()
      };

      const response = await fetch(`${API_BASE_URL}/api/kpi/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Anomaly triggered:', result);
        
        // Update local state to reflect anomalies
        setAlerts(result.anomaly_reasons?.map(msg => ({ 
          severity: 'error', 
          message: msg 
        })) || []);
        setAnomalyScore(result.anomaly_score || 0.85);
        
        // Refresh data to get updated state
        setTimeout(fetchData, 1000);
      }
    } catch (error) {
      console.error('Error triggering anomaly:', error);
      // Fallback to local simulation if API fails
      const testAlerts = [
        { severity: 'error', message: 'Low throughput: 25.3 Mbps (3GPP min: 50 Mbps)' },
        { severity: 'warning', message: 'High latency: 28.7 ms (3GPP max: 20 ms)' },
        { severity: 'error', message: 'High PRB utilization: 92% (3GPP max: 85%)' }
      ];
      setAlerts(testAlerts);
      setAnomalyScore(0.85);
    }
  };

  const clearAlerts = () => {
    setAlerts([]);
    setAnomalyScore(0);
  };

  const getStatusColor = (kpiId, value) => {
    if (value === undefined || value === null) return '#757575';
    
    const threshold = kpiThresholds[kpiId];
    if (!threshold) return '#757575';
    
    const { min, max, higherBetter } = threshold;
    
    if (higherBetter) {
      return value >= min ? '#4caf50' : '#f44336';
    } else {
      return value <= max ? '#4caf50' : '#f44336';
    }
  };

  const formatKpiValue = (kpiId, value) => {
    if (value === undefined || value === null) return 'N/A';
    
    const kpiConfig = kpiOptions.find(k => k.id === kpiId);
    if (!kpiConfig) return value;

    switch (kpiId) {
      case 'downlink_ue_throughput':
        return `${(value / 1000000).toFixed(2)} ${kpiConfig.unit}`;
      case 'downlink_prb_utilization':
      case 'data_session_setup_success_rate':
      case 'endc_add_setup_success_rate':
      case 'inter_sgnb_change_success_rate':
        return `${value.toFixed(1)}${kpiConfig.unit}`;
      case 'maximum_active_endc_user':
        return `${Math.round(value)} ${kpiConfig.unit}`;
      case 'downlink_latency':
        return `${value.toFixed(1)} ${kpiConfig.unit}`;
      case 'downlink_payload':
        return `${value.toFixed(1)} ${kpiConfig.unit}`;
      default:
        return `${value} ${kpiConfig.unit || ''}`;
    }
  };

  const KPICard = React.memo(({ kpi }) => {
    const value = kpis[kpi.id];
    const threshold = kpiThresholds[kpi.id];
    const displayValue = formatKpiValue(kpi.id, value);
    const isSelected = selectedKpis.length === 0 || selectedKpis.includes(kpi.id);
    const statusColor = getStatusColor(kpi.id, value);
    
    return (
      <Card 
        sx={{ 
          height: '100%', 
          opacity: isSelected ? 1 : 0.4,
          transition: 'all 0.3s ease',
          border: isSelected ? `2px solid ${statusColor}` : '2px solid transparent',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: 3,
          }
        }}
      >
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom noWrap>
            {kpi.name}
          </Typography>
          <Typography 
            variant="h4" 
            component="div" 
            sx={{ 
              color: statusColor,
              fontWeight: 'bold'
            }}
          >
            {displayValue}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Threshold: {threshold.higherBetter ? 
              `Min ${formatKpiValue(kpi.id, threshold.min * (kpi.id === 'downlink_ue_throughput' ? 1000000 : 1))}` : 
              `Max ${formatKpiValue(kpi.id, threshold.max)}`
            }
          </Typography>
          {!isSelected && (
            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Filtered out
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  });

  // Filter historical data for selected KPIs
  const filteredHistoricalData = useMemo(() => {
    return historicalData.map(item => {
      const filteredItem = { timestamp: item.timestamp };
      const kpisToShow = selectedKpis.length > 0 ? selectedKpis : kpiOptions.map(kpi => kpi.id);
      
      kpisToShow.forEach(kpi => {
        if (item[kpi] !== undefined) {
          // Convert throughput to Mbps for better chart display
          filteredItem[kpi] = kpi === 'downlink_ue_throughput' ? item[kpi] / 1000000 : item[kpi];
        }
      });
      return filteredItem;
    });
  }, [historicalData, selectedKpis, kpiOptions]);

  // Chart configuration
  const chartConfig = useMemo(() => ({
    'downlink_ue_throughput': { color: '#8884d8', type: 'line' },
    'downlink_prb_utilization': { color: '#82ca9d', type: 'line' },
    'data_session_setup_success_rate': { color: '#ffc658', type: 'line' },
    'endc_add_setup_success_rate': { color: '#ff7300', type: 'line' },
    'inter_sgnb_change_success_rate': { color: '#413ea0', type: 'line' },
    'maximum_active_endc_user': { color: '#ff0000', type: 'bar' },
    'downlink_latency': { color: '#00ff00', type: 'area' },
    'downlink_payload': { color: '#0000ff', type: 'bar' }
  }), []);

  const renderChart = () => {
    const kpisToShow = selectedKpis.length > 0 ? selectedKpis : kpiOptions.map(kpi => kpi.id);
    
    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={filteredHistoricalData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }}
          />
          <YAxis />
          <Tooltip 
            labelFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleString();
            }}
            formatter={(value, name) => {
              const kpi = kpiOptions.find(k => k.id === name);
              return [formatKpiValue(kpi?.id, value), kpi?.name || name];
            }}
          />
          <Legend />
          {kpisToShow.map(kpiId => (
            <Line 
              key={kpiId}
              type="monotone" 
              dataKey={kpiId} 
              stroke={chartConfig[kpiId]?.color || '#000000'}
              name={kpiOptions.find(k => k.id === kpiId)?.name || kpiId}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  if (loading && historicalData.length === 0) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          5G NR KPI Monitor v2.0
        </Typography>
        <LinearProgress />
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          Loading 5G KPI data...
        </Typography>
      </Box>
    );
  }

  return (
    <div className="App">
      <Box sx={{ flexGrow: 1, p: 3 }}>
        {/* Header */}
        <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
          📊 5G NR KPI Anomaly Detection
          <Typography variant="subtitle1" color="text.secondary" align="center">
            Real-time 3GPP-compliant KPI Monitoring
          </Typography>
        </Typography>

        {/* Loading Indicator */}
        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Error Snackbar */}
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={6000}
          onClose={() => setSnackbarOpen(false)}
          message={error}
          action={
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={() => setSnackbarOpen(false)}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        />

        {/* Dashboard Header */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6">Selected Cell</Typography>
              <Typography variant="h5" color="primary" sx={{ fontWeight: 'bold' }}>
                {kpis.cell_id || selectedCell}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6">Anomaly Score</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {anomalyScore > 0.5 ? <ErrorIcon color="error" /> : 
                 anomalyScore > 0.2 ? <WarningIcon color="warning" /> : null}
                <Typography 
                  variant="h4" 
                  color={anomalyScore > 0.5 ? 'error' : anomalyScore > 0.2 ? 'warning' : 'success'}
                  sx={{ ml: 1, fontWeight: 'bold' }}
                >
                  {(anomalyScore * 100).toFixed(0)}%
                </Typography>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6">Active Alerts</Typography>
              <Typography variant="h4" color={alerts.length > 0 ? 'error' : 'success'}>
                {alerts.length}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* KPI Selection Filter */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                KPI Dashboard Filter
              </Typography>
              <Button 
                variant="outlined" 
                color="secondary" 
                onClick={triggerAnomaly}
                startIcon={<WarningIcon />}
              >
                Test Anomaly
              </Button>
            </Box>
            <FormControl fullWidth size="small">
              <InputLabel>Filter KPIs</InputLabel>
              <Select
                multiple
                value={selectedKpis}
                onChange={handleKpiSelection}
                renderValue={(selected) => 
                  selected.length === 0 ? 
                  'All KPIs' : 
                  `${selected.length} KPIs selected`
                }
                label="Filter KPIs"
              >
                {kpiOptions.map((kpi) => (
                  <MenuItem key={kpi.id} value={kpi.id}>
                    <Checkbox checked={selectedKpis.indexOf(kpi.id) > -1} />
                    <ListItemText 
                      primary={kpi.name} 
                      secondary={kpi.unit}
                    />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </CardContent>
        </Card>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">
                Active Alerts ({alerts.length})
              </Typography>
              <Button size="small" onClick={clearAlerts}>
                Clear All
              </Button>
            </Box>
            {alerts.map((alert, index) => (
              <Alert 
                key={index} 
                severity={alert.severity}
                sx={{ mb: 1 }}
                action={
                  <IconButton
                    aria-label="close"
                    color="inherit"
                    size="small"
                    onClick={() => {
                      setAlerts(prev => prev.filter((_, i) => i !== index));
                    }}
                  >
                    <CloseIcon fontSize="inherit" />
                  </IconButton>
                }
              >
                {alert.message}
              </Alert>
            ))}
          </Box>
        )}

        {/* KPI Grid */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {kpiOptions.map((kpi) => (
            <Grid item xs={12} sm={6} md={3} key={kpi.id}>
              <KPICard kpi={kpi} />
            </Grid>
          ))}
        </Grid>

        {/* Charts Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📈 Historical Trends - Last 4 Hours
            </Typography>
            {filteredHistoricalData.length > 0 ? (
              renderChart()
            ) : (
              <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="text.secondary">
                  No historical data available
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Last Updated */}
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Last updated: {kpis.timestamp ? new Date(kpis.timestamp).toLocaleString() : 'Never'}
          {' | '}
          <Button size="small" onClick={fetchData}>
            Refresh Now
          </Button>
        </Typography>
      </Box>
    </div>
  );
}

export default App;
