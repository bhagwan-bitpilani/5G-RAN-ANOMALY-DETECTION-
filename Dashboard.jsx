import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Table, Tag, Spin } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { WifiOutlined, ExclamationCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [anomalies, setAnomalies] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/dashboard/combined', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setDashboardData(data);
      setAnomalies(data.anomalies || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;

  const recentAnomalies = anomalies.slice(0, 10);
  const kpiTrends = dashboardData?.kpis?.slice(0, 50) || [];

  const anomalyColumns = [
    {
      title: 'KPI Type',
      dataIndex: 'kpi_type',
      key: 'kpi_type',
    },
    {
      title: 'Score',
      dataIndex: 'anomaly_score',
      key: 'score',
      render: score => (
        <Tag color={score > 0.8 ? 'red' : score > 0.6 ? 'orange' : 'yellow'}>
          {score.toFixed(3)}
        </Tag>
      ),
    },
    {
      title: 'Detected At',
      dataIndex: 'detected_at',
      key: 'detected_at',
    },
    {
      title: 'Status',
      dataIndex: 'is_resolved',
      key: 'status',
      render: resolved => (
        <Tag color={resolved ? 'green' : 'red'}>
          {resolved ? 'Resolved' : 'Active'}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total NR Cells"
              value={dashboardData?.summary?.total_cells || 0}
              prefix={<WifiOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Anomalies (24h)"
              value={dashboardData?.summary?.anomalies_24h || 0}
              valueStyle={{ color: dashboardData?.summary?.anomalies_24h > 0 ? '#cf1322' : '#3f8600' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="System Health"
              value={dashboardData?.summary?.system_health === 'healthy' ? 'Healthy' : 'Degraded'}
              valueStyle={{ color: dashboardData?.summary?.system_health === 'healthy' ? '#3f8600' : '#cf1322' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Cells"
              value={dashboardData?.summary?.total_cells || 0}
              suffix="/ 100"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col span={12}>
          <Card title="KPI Trends" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={kpiTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="nr_ue_throughput" stroke="#8884d8" />
                <Line type="monotone" dataKey="latency" stroke="#82ca9d" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Recent Anomalies" bordered={false}>
            <Table
              dataSource={recentAnomalies}
              columns={anomalyColumns}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {recentAnomalies.length > 0 && (
        <Alert
          message={`${recentAnomalies.length} active anomalies detected`}
          type="warning"
          showIcon
          style={{ marginTop: '24px' }}
        />
      )}
    </div>
  );
};

export default Dashboard;
