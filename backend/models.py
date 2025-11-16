# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class BandType(enum.Enum):
    NR2600 = "NR2600"
    NR700 = "NR700"
    NR3500 = "NR3500"
    NR2100 = "NR2100"

class CellStatus(enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"
    INACTIVE = "inactive"

class AnomalySeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NRCell(Base):
    __tablename__ = "nr_cells"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(String(50), unique=True, index=True, nullable=False)
    band = Column(String(20), nullable=False)  # NR2600, NR700
    location = Column(String(100))
    sector = Column(Integer, nullable=False)
    status = Column(String(20), default="active")
    
    # Enhanced cell attributes
    frequency = Column(Integer)  # Frequency in MHz
    bandwidth = Column(Integer)  # Bandwidth in MHz
    power = Column(Float)  # Transmit power in dBm
    azimuth = Column(Integer)  Antenna azimuth in degrees
    height = Column(Float)  # Antenna height in meters
    latitude = Column(Float)  # Geographic coordinates
    longitude = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_maintenance = Column(DateTime(timezone=True))
    
    # Relationships
    kpi_data = relationship("KpiData", back_populates="cell", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyDetection", back_populates="cell")
    
    def to_dict(self):
        return {
            "id": self.id,
            "cell_id": self.cell_id,
            "band": self.band,
            "location": self.location,
            "sector": self.sector,
            "status": self.status,
            "frequency": self.frequency,
            "bandwidth": self.bandwidth,
            "power": self.power,
            "azimuth": self.azimuth,
            "height": self.height,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None
        }

class KpiData(Base):
    __tablename__ = "kpi_data"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(String(50), ForeignKey('nr_cells.cell_id'), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 3GPP Compliant KPIs - Core Network Metrics
    downlink_ue_throughput = Column(BigInteger)  # bps (not Mbps for precision)
    downlink_prb_utilization = Column(Float)  # Percentage
    data_session_setup_success_rate = Column(Float)  # Percentage
    endc_add_setup_success_rate = Column(Float)  # Percentage
    inter_sgnb_change_success_rate = Column(Float)  # Percentage
    maximum_active_endc_user = Column(Integer)  # User count
    downlink_latency = Column(Float)  # Milliseconds
    downlink_payload = Column(Float)  # Gigabytes
    
    # Additional Technical KPIs
    uplink_ue_throughput = Column(BigInteger)  # bps
    uplink_prb_utilization = Column(Float)  # Percentage
    cqi_distribution = Column(JSON)  # Channel Quality Indicator distribution
    rssi = Column(Float)  # Received Signal Strength Indicator
    rsrp = Column(Float)  # Reference Signal Received Power
    rsrq = Column(Float)  # Reference Signal Received Quality
    sinr = Column(Float)  # Signal to Interference plus Noise Ratio
    
    # Anomaly Detection Fields
    anomaly_flags = Column(JSON)  # Dictionary of anomaly flags per KPI
    anomaly_score_overall = Column(Float)  # Overall anomaly score (0-1)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    data_source = Column(String(50), default="stream")  # stream, batch, manual
    data_quality_score = Column(Float)  # Data quality assessment (0-1)
    
    # Relationships
    cell = relationship("NRCell", back_populates="kpi_data")
    anomalies = relationship("AnomalyDetection", back_populates="kpi_record")
    
    def to_dict(self):
        return {
            "id": self.id,
            "cell_id": self.cell_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            
            # Core 3GPP KPIs
            "downlink_ue_throughput": self.downlink_ue_throughput,
            "downlink_prb_utilization": self.downlink_prb_utilization,
            "data_session_setup_success_rate": self.data_session_setup_success_rate,
            "endc_add_setup_success_rate": self.endc_add_setup_success_rate,
            "inter_sgnb_change_success_rate": self.inter_sgnb_change_success_rate,
            "maximum_active_endc_user": self.maximum_active_endc_user,
            "downlink_latency": self.downlink_latency,
            "downlink_payload": self.downlink_payload,
            
            # Additional KPIs
            "uplink_ue_throughput": self.uplink_ue_throughput,
            "uplink_prb_utilization": self.uplink_prb_utilization,
            "cqi_distribution": self.cqi_distribution,
            "rssi": self.rssi,
            "rsrp": self.rsrp,
            "rsrq": self.rsrq,
            "sinr": self.sinr,
            
            # Anomaly Information
            "anomaly_flags": self.anomaly_flags,
            "anomaly_score_overall": self.anomaly_score_overall,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            
            # Metadata
            "data_source": self.data_source,
            "data_quality_score": self.data_quality_score
        }

class AnomalyDetection(Base):
    __tablename__ = "anomaly_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    kpi_id = Column(Integer, ForeignKey('kpi_data.id'), index=True, nullable=False)
    cell_id = Column(String(50), ForeignKey('nr_cells.cell_id'), index=True, nullable=False)
    
    # Anomaly Details
    anomaly_score = Column(Float, nullable=False)  # 0-1 scale
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    kpi_type = Column(String(50), nullable=False)  # Which KPI triggered the anomaly
    kpi_value = Column(Float, nullable=False)  # Actual KPI value that caused anomaly
    threshold_low = Column(Float)  # Lower threshold
    threshold_high = Column(Float)  # Upper threshold
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True))
    
    # Resolution Information
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(50))  # Username or system that resolved it
    resolution_notes = Column(Text)
    resolution_action = Column(String(100))  # Action taken to resolve
    
    # Anomaly Context
    anomaly_reasons = Column(JSON)  # List of reason strings
    affected_kpis = Column(JSON)  # List of KPIs affected by this anomaly
    compliance_breach = Column(Boolean, default=False)  # If it breaches 3GPP compliance
    
    # Relationships
    kpi_record = relationship("KpiData", back_populates="anomalies")
    cell = relationship("NRCell", back_populates="anomalies")
    
    def to_dict(self):
        return {
            "id": self.id,
            "kpi_id": self.kpi_id,
            "cell_id": self.cell_id,
            "anomaly_score": self.anomaly_score,
            "severity": self.severity,
            "kpi_type": self.kpi_type,
            "kpi_value": self.kpi_value,
            "threshold_low": self.threshold_low,
            "threshold_high": self.threshold_high,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "resolution_action": self.resolution_action,
            "anomaly_reasons": self.anomaly_reasons,
            "affected_kpis": self.affected_kpis,
            "compliance_breach": self.compliance_breach
        }

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(JSON, nullable=False)
    description = Column(Text)
    data_type = Column(String(20))  # string, integer, float, boolean, json
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50), default="system")
    
    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "data_type": self.data_type,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by
        }

class KPIThresholds(Base):
    __tablename__ = "kpi_thresholds"
    
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Threshold values
    threshold_low = Column(Float, nullable=False)
    threshold_high = Column(Float, nullable=False)
    target_value = Column(Float)  # Optimal value
    is_higher_better = Column(Boolean, default=True)
    
    # 3GPP Compliance
    threegpp_reference = Column(String(100))  # 3GPP specification reference
    compliance_level = Column(String(20))  # mandatory, recommended, optional
    
    # Weight for anomaly scoring
    anomaly_weight = Column(Float, default=1.0)
    
    # Metadata
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "kpi_name": self.kpi_name,
            "display_name": self.display_name,
            "unit": self.unit,
            "threshold_low": self.threshold_low,
            "threshold_high": self.threshold_high,
            "target_value": self.target_value,
            "is_higher_better": self.is_higher_better,
            "threegpp_reference": self.threegpp_reference,
            "compliance_level": self.compliance_level,
            "anomaly_weight": self.anomaly_weight,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class AlertNotification(Base):
    __tablename__ = "alert_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(Integer, ForeignKey('anomaly_detections.id'), index=True)
    alert_type = Column(String(50), nullable=False)  # email, sms, webhook, system
    recipient = Column(String(255))  # Email, phone number, webhook URL
    subject = Column(String(200))
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="sent")  # sent, delivered, failed, read
    error_message = Column(Text)
    
    # Relationships
    anomaly = relationship("AnomalyDetection")
    
    def to_dict(self):
        return {
            "id": self.id,
            "anomaly_id": self.anomaly_id,
            "alert_type": self.alert_type,
            "recipient": self.recipient,
            "subject": self.subject,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "error_message": self.error_message
        }

class PerformanceReport(Base):
    __tablename__ = "performance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Report data
    report_data = Column(JSON)  # Structured report data
    summary = Column(Text)  # Human-readable summary
    anomalies_count = Column(Integer, default=0)
    compliance_score = Column(Float)  # Overall compliance score
    
    # Metadata
    generated_by = Column(String(50), default="system")
    file_path = Column(String(255))  # Path to stored report file
    
    def to_dict(self):
        return {
            "id": self.id,
            "report_type": self.report_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "anomalies_count": self.anomalies_count,
            "compliance_score": self.compliance_score,
            "summary": self.summary,
            "generated_by": self.generated_by,
            "file_path": self.file_path
        }

# Create database indexes for better performance
from sqlalchemy import Index

# Composite indexes for common query patterns
Index('idx_kpi_data_cell_timestamp', KpiData.cell_id, KpiData.timestamp)
Index('idx_anomalies_cell_severity', AnomalyDetection.cell_id, AnomalyDetection.severity)
Index('idx_anomalies_detected_resolved', AnomalyDetection.detected_at, AnomalyDetection.is_resolved)
Index('idx_cells_band_status', NRCell.band, NRCell.status)
