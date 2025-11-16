import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import random
import json
import sys
from typing import Dict, List, Optional

class KPISimulator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.cells = []
        
    def generate_nr_cells_excel(self, filename: str = 'nr_cells_demo.xlsx') -> None:
        """Generate dummy NR cells data for NR2600 and NR700 bands with enhanced data"""
        
        print("📱 Generating NR cells template...")
        nr2600_cells = []
        nr700_cells = []
        
        # Generate NR2600 cells (mid-band)
        for i in range(1, 51):
            nr2600_cells.append({
                'cell_id': f'NR2600_{i:03d}',
                'band': 'NR2600',
                'location': f'Sector_{(i-1)//10 + 1}',
                'sector': ((i-1) % 3) + 1,
                'latitude': round(40.7128 + (i * 0.001), 6),
                'longitude': round(-74.0060 + (i * 0.001), 6),
                'frequency': 2600,
                'bandwidth': 100,
                'power': 46,
                'azimuth': random.randint(0, 360),
                'height': random.randint(20, 50),
                'status': 'active'
            })
        
        # Generate NR700 cells (low-band)
        for i in range(1, 51):
            nr700_cells.append({
                'cell_id': f'NR700_{i:03d}',
                'band': 'NR700',
                'location': f'Sector_{(i-1)//10 + 1}',
                'sector': ((i-1) % 3) + 1,
                'latitude': round(40.7128 - (i * 0.001), 6),
                'longitude': round(-74.0060 - (i * 0.001), 6),
                'frequency': 700,
                'bandwidth': 20,
                'power': 40,
                'azimuth': random.randint(0, 360),
                'height': random.randint(25, 60),
                'status': 'active'
            })
        
        all_cells = nr2600_cells + nr700_cells
        self.cells = all_cells
        
        df = pd.DataFrame(all_cells)
        df.to_excel(filename, index=False)
        print(f"✅ Generated NR cells template with {len(all_cells)} cells (50 NR2600, 50 NR700)")
        print(f"📁 Saved as: {filename}")
        
        # Also save as CSV for easier viewing
        df.to_csv('nr_cells_demo.csv', index=False)
        print(f"📁 Also saved as: nr_cells_demo.csv")

    def login(self) -> bool:
        """Login to the backend system"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data={"username": "admin", "password": "admin"},
                timeout=10
            )
            if response.status_code == 200:
                print("🔐 Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to backend at {self.base_url}")
            print("💡 Make sure the backend is running with: docker compose up backend")
            return False
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def generate_realistic_kpi_data(self, cell_id: str) -> Dict:
        """Generate realistic 3GPP-compliant KPI data with occasional anomalies"""
        
        band = 'NR2600' if 'NR2600' in cell_id else 'NR700'
        
        # Base values for normal operation (3GPP compliant)
        if band == 'NR2600':
            base_values = {
                'downlink_ue_throughput': np.random.normal(600000000, 100000000),  # 600 ± 100 Mbps
                'downlink_prb_utilization': np.random.normal(45, 15),              # 45 ± 15%
                'data_session_setup_success_rate': np.random.normal(99.5, 0.3),    # 99.5 ± 0.3%
                'endc_add_setup_success_rate': np.random.normal(98.0, 1.0),        # 98.0 ± 1.0%
                'inter_sgnb_change_success_rate': np.random.normal(96.0, 2.0),     # 96.0 ± 2.0%
                'maximum_active_endc_user': np.random.poisson(120),                # ~120 users
                'downlink_latency': np.random.normal(8, 2),                        # 8 ± 2 ms
                'downlink_payload': np.random.normal(180, 40)                      # 180 ± 40 GB
            }
        else:  # NR700
            base_values = {
                'downlink_ue_throughput': np.random.normal(300000000, 80000000),   # 300 ± 80 Mbps
                'downlink_prb_utilization': np.random.normal(35, 12),              # 35 ± 12%
                'data_session_setup_success_rate': np.random.normal(99.2, 0.4),    # 99.2 ± 0.4%
                'endc_add_setup_success_rate': np.random.normal(97.5, 1.5),        # 97.5 ± 1.5%
                'inter_sgnb_change_success_rate': np.random.normal(95.0, 2.5),     # 95.0 ± 2.5%
                'maximum_active_endc_user': np.random.poisson(80),                 # ~80 users
                'downlink_latency': np.random.normal(12, 3),                       # 12 ± 3 ms
                'downlink_payload': np.random.normal(120, 30)                      # 120 ± 30 GB
            }

        # Introduce anomalies in 15% of cases
        is_anomaly = np.random.random() < 0.15
        
        if is_anomaly:
            # Select 1-3 KPIs to make anomalous
            anomalous_kpis = random.sample(list(base_values.keys()), random.randint(1, 3))
            
            for kpi in anomalous_kpis:
                if 'success_rate' in kpi:
                    # Reduce success rates significantly
                    base_values[kpi] *= random.uniform(0.7, 0.9)
                elif 'latency' in kpi:
                    # Increase latency significantly
                    base_values[kpi] *= random.uniform(2.0, 4.0)
                elif 'throughput' in kpi:
                    # Reduce throughput significantly
                    base_values[kpi] *= random.uniform(0.2, 0.6)
                elif kpi == 'maximum_active_endc_user':
                    # Either too many or too few users
                    if random.random() < 0.5:
                        base_values[kpi] *= random.uniform(1.8, 2.5)  # Overload
                    else:
                        base_values[kpi] *= random.uniform(0.1, 0.4)  # Underutilized
                elif kpi == 'downlink_payload':
                    base_values[kpi] *= random.uniform(0.05, 0.3)     # Very low traffic
                elif kpi == 'downlink_prb_utilization':
                    if random.random() < 0.7:
                        base_values[kpi] *= random.uniform(1.5, 2.0)  # High utilization
                    else:
                        base_values[kpi] *= random.uniform(0.1, 0.3)  # Very low utilization

        # Ensure values are within realistic bounds
        base_values['downlink_ue_throughput'] = max(1000000, base_values['downlink_ue_throughput'])  # At least 1 Mbps
        base_values['downlink_prb_utilization'] = max(0, min(100, base_values['downlink_prb_utilization']))
        base_values['data_session_setup_success_rate'] = max(0, min(100, base_values['data_session_setup_success_rate']))
        base_values['endc_add_setup_success_rate'] = max(0, min(100, base_values['endc_add_setup_success_rate']))
        base_values['inter_sgnb_change_success_rate'] = max(0, min(100, base_values['inter_sgnb_change_success_rate']))
        base_values['maximum_active_endc_user'] = max(0, base_values['maximum_active_endc_user'])
        base_values['downlink_latency'] = max(1, base_values['downlink_latency'])
        base_values['downlink_payload'] = max(0.1, base_values['downlink_payload'])

        kpi_data = {
            'cell_id': cell_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **{k: round(v, 2) for k, v in base_values.items()}
        }
        
        return kpi_data, is_anomaly

    def send_kpi_data(self, kpi_data: Dict) -> bool:
        """Send KPI data to backend"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/kpi/stream",
                json=kpi_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('anomaly_detected'):
                    print(f"🚨 ANOMALY DETECTED! Score: {result.get('anomaly_score', 0):.3f}")
                    if 'anomaly_reasons' in result:
                        for reason in result['anomaly_reasons']:
                            print(f"   ⚠️  {reason}")
                else:
                    print(f"✅ {kpi_data['cell_id']} - Normal operation")
                return True
            else:
                print(f"❌ Failed to send data: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending data: {str(e)}")
            return False

    def simulate_kpi_data_stream(self, duration_minutes: int = 30, interval_seconds: int = 5) -> None:
        """Simulate continuous KPI data streaming"""
        
        if not self.login():
            return
        
        print(f"\n📊 Starting KPI data simulation...")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Interval: {interval_seconds} seconds")
        print(f"   Cells: {len(self.cells)} total")
        print("-" * 50)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        data_points_sent = 0
        anomalies_detected = 0
        
        try:
            while time.time() < end_time:
                # Select a random cell
                cell = random.choice(self.cells)
                cell_id = cell['cell_id']
                
                # Generate KPI data
                kpi_data, is_anomaly_expected = self.generate_realistic_kpi_data(cell_id)
                
                # Send data
                success = self.send_kpi_data(kpi_data)
                
                if success:
                    data_points_sent += 1
                    if is_anomaly_expected:
                        anomalies_detected += 1
                
                # Progress indicator
                if data_points_sent % 10 == 0:
                    elapsed = time.time() - start_time
                    remaining = end_time - time.time()
                    print(f"\n📈 Progress: {data_points_sent} data points sent")
                    print(f"⏱️  Elapsed: {elapsed/60:.1f}m, Remaining: {remaining/60:.1f}m")
                    print(f"🚨 Anomalies: {anomalies_detected}/{data_points_sent} ({anomalies_detected/max(1, data_points_sent)*100:.1f}%)")
                    print("-" * 30)
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n⏹️  Simulation interrupted by user")
        
        finally:
            elapsed_total = time.time() - start_time
            print("\n" + "="*50)
            print("📊 SIMULATION SUMMARY")
            print("="*50)
            print(f"✅ Data points sent: {data_points_sent}")
            print(f"🚨 Anomalies detected: {anomalies_detected}")
            print(f"📈 Anomaly rate: {anomalies_detected/max(1, data_points_sent)*100:.1f}%")
            print(f"⏱️  Total duration: {elapsed_total/60:.1f} minutes")
            print(f"📡 Average rate: {data_points_sent/elapsed_total*60:.1f} data points/minute")

    def upload_cells_to_backend(self, filename: str = 'nr_cells_demo.xlsx') -> None:
        """Upload generated cells to backend"""
        if not self.login():
            return
            
        try:
            with open(filename, 'rb') as f:
                files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = self.session.post(f"{self.base_url}/api/upload/cells", files=files)
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Cells uploaded successfully: {result}")
            else:
                print(f"❌ Failed to upload cells: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error uploading cells: {str(e)}")

def main():
    """Main function with interactive menu"""
    simulator = KPISimulator()
    
    print("="*60)
    print("📡 5G NR KPI Data Simulator v2.0")
    print("="*60)
    print("This tool generates realistic 3GPP-compliant KPI data")
    print("for testing the 5G NR Anomaly Detection System")
    print()
    
    while True:
        print("\n🎮 Menu:")
        print("1. Generate NR Cells Excel Template")
        print("2. Upload Cells to Backend")
        print("3. Start KPI Data Simulation")
        print("4. Quick Test (Generate + Upload + Simulate)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            filename = input("Enter filename [nr_cells_demo.xlsx]: ").strip() or 'nr_cells_demo.xlsx'
            simulator.generate_nr_cells_excel(filename)
            
        elif choice == '2':
            filename = input("Enter filename to upload [nr_cells_demo.xlsx]: ").strip() or 'nr_cells_demo.xlsx'
            simulator.upload_cells_to_backend(filename)
            
        elif choice == '3':
            try:
                duration = int(input("Enter duration in minutes [30]: ").strip() or "30")
                interval = int(input("Enter interval in seconds [5]: ").strip() or "5")
                simulator.simulate_kpi_data_stream(duration, interval)
            except ValueError:
                print("❌ Please enter valid numbers")
                
        elif choice == '4':
            print("\n🚀 Starting quick test...")
            simulator.generate_nr_cells_excel()
            print("\n⏳ Waiting 2 seconds before upload...")
            time.sleep(2)
            simulator.upload_cells_to_backend()
            print("\n⏳ Waiting 3 seconds before simulation...")
            time.sleep(3)
            simulator.simulate_kpi_data_stream(10, 3)  # 10 minutes, 3-second intervals
            
        elif choice == '5':
            print("👋 Exiting simulator. Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Simulation interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
