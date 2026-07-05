"""
Test script for data visualization widgets.
"""

import sys
import random
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ui.visualization import (
    LineChart, BarChart, FidelityDashboard, TelemetryWidget
)


def main():
    print("Data Visualization Widgets - Test Suite")
    print("=" * 70)

    # Test 1: Line Chart
    print("\n[1/4] Testing LineChart...")
    chart = LineChart(name="CPU Usage Over Time", width=60, height=15)
    chart.add_series("CPU")

    # Add sample data
    for i in range(30):
        value = 20 + random.random() * 60  # 20-80%
        chart.add_point("CPU", value)

    print(chart.render())

    # Test 2: Bar Chart
    print("\n[2/4] Testing BarChart...")
    bar_chart = BarChart(name="Test Results", width=60, height=15, orientation="horizontal")
    bar_chart.set_data({
        'Passed': 45,
        'Failed': 3,
        'Skipped': 2,
        'Total': 50
    })

    print(bar_chart.render())

    # Test 3: Fidelity Dashboard
    print("\n[3/4] Testing FidelityDashboard...")
    fidelity = FidelityDashboard(width=70)

    # Simulate operations
    fidelity.log_operation("db.query", "success", 12.5)
    fidelity.log_operation("file.upload", "success", 234.7)
    fidelity.log_operation("sim.run", "success", 856.2)
    fidelity.log_operation("ai.prompt", "failed", 45.1)
    fidelity.log_operation("event.publish", "success", 3.4)
    fidelity.data_points_logged = 1247

    print(fidelity.render())

    # Test 4: Telemetry Widget
    print("\n[4/4] Testing TelemetryWidget...")
    telemetry = TelemetryWidget(width=70)

    # Update metrics
    telemetry.update_metric('cpu', 45.2)
    telemetry.update_metric('memory', 67.8)
    telemetry.update_metric('disk', 82.5)
    telemetry.update_metric('network', 12.4)

    print(telemetry.render())

    print("\n" + "=" * 70)
    print("Data visualization widgets ready for 3D integration!")
    print("- LineChart: Time-series data with multiple series")
    print("- BarChart: Categorical data (vertical/horizontal)")
    print("- FidelityDashboard: 99.9% fidelity tracking")
    print("- TelemetryWidget: Real-time system metrics")


if __name__ == "__main__":
    main()
