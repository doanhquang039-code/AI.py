import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface IoTDevice {
  id: string;
  name: string;
  zone: string;
  status: string;
  last_seen: string;
  metrics: {
    temperature: number;
    humidity: number;
    vibration: number;
    energy_kw: number;
  };
  ai: {
    anomaly_score: number;
    risk: string;
    predicted_maintenance_hours: number;
  };
}

interface TelemetryPoint {
  index: number;
  temperature: number;
  vibration: number;
  energy_kw?: number;
  anomaly_score?: number;
}

interface IoTInsight {
  title: string;
  severity: string;
  impact: string;
  recommendation: string;
}

interface FleetSummary {
  device_count: number;
  online_count: number;
  warning_count: number;
  high_risk_count: number;
  avg_anomaly_score: number;
  total_energy_kw: number;
  estimated_savings_kw: number;
  fleet_health: number;
  top_risk_device: IoTDevice;
}

interface IoTCommand {
  id: string;
  device_id: string;
  mode: string;
  target_temperature: number | null;
  status: string;
  created_at: string;
}

interface OptimizationAction {
  device_id: string;
  action: string;
  priority: string;
  expected_impact: string;
}

interface OptimizationPlan {
  plan_id: string;
  objective: string;
  confidence: number;
  estimated_savings_kw: number;
  actions: OptimizationAction[];
  created_at: string;
}

@Component({
  selector: 'app-iot-ai',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="iot-container">
      <div class="page-heading">
        <div>
          <h2>IoT AI Control Center</h2>
          <p>Edge telemetry, anomaly detection, and AI operations recommendations.</p>
        </div>
        <div class="heading-actions">
          <label class="toggle">
            <input type="checkbox" [(ngModel)]="autoRefresh" (change)="toggleAutoRefresh()">
            Live
          </label>
          <button class="btn btn-secondary" type="button" (click)="loadData()" [disabled]="loading">
            {{loading ? 'Refreshing...' : 'Refresh'}}
          </button>
          <button class="btn btn-primary" type="button" (click)="runOptimization()" [disabled]="optimizing">
            {{optimizing ? 'Optimizing...' : 'Optimize Fleet'}}
          </button>
        </div>
      </div>

      <div class="fleet-grid" *ngIf="fleetSummary">
        <div class="fleet-card">
          <label>Fleet Health</label>
          <strong>{{fleetSummary.fleet_health | number:'1.1-1'}}%</strong>
          <progress [value]="fleetSummary.fleet_health" max="100"></progress>
        </div>
        <div class="fleet-card">
          <label>Devices Online</label>
          <strong>{{fleetSummary.online_count}} / {{fleetSummary.device_count}}</strong>
          <span>{{fleetSummary.warning_count}} warning</span>
        </div>
        <div class="fleet-card">
          <label>Energy Load</label>
          <strong>{{fleetSummary.total_energy_kw | number:'1.1-1'}} kW</strong>
          <span>{{fleetSummary.estimated_savings_kw | number:'1.1-1'}} kW savings potential</span>
        </div>
        <div class="fleet-card">
          <label>Top Risk</label>
          <strong>{{fleetSummary.top_risk_device.name}}</strong>
          <span>{{fleetSummary.top_risk_device.ai.anomaly_score | number:'1.3-3'}} anomaly</span>
        </div>
      </div>

      <div class="device-grid">
        <button
          class="device-card"
          type="button"
          *ngFor="let device of devices"
          [class.selected]="selectedDevice?.id === device.id"
          (click)="selectDevice(device)">
          <div class="device-topline">
            <strong>{{device.name}}</strong>
            <span [class]="'risk ' + device.ai.risk">{{device.ai.risk}}</span>
          </div>
          <p>{{device.zone}}</p>
          <div class="metric-strip">
            <span>{{device.metrics.temperature | number:'1.1-1'}} C</span>
            <span>{{device.metrics.vibration | number:'1.3-3'}} vib</span>
            <span>{{device.metrics.energy_kw | number:'1.1-1'}} kW</span>
          </div>
          <progress [value]="device.ai.anomaly_score" max="1"></progress>
        </button>
      </div>

      <div class="content-grid" *ngIf="selectedDevice">
        <section class="panel">
          <div class="panel-header">
            <h3>{{selectedDevice.name}} Telemetry</h3>
            <span>{{selectedDevice.zone}}</span>
          </div>

          <div class="chart" aria-label="Temperature telemetry">
            <span
              *ngFor="let point of telemetry"
              [style.height.%]="barHeight(point.temperature)"
              [title]="'Temp ' + point.temperature">
            </span>
          </div>

          <div class="stats-grid">
            <div class="stat">
              <label>Anomaly</label>
              <strong>{{selectedDevice.ai.anomaly_score | number:'1.3-3'}}</strong>
            </div>
            <div class="stat">
              <label>Maintenance</label>
              <strong>{{selectedDevice.ai.predicted_maintenance_hours}}h</strong>
            </div>
            <div class="stat">
              <label>Status</label>
              <strong>{{selectedDevice.status}}</strong>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>AI Forecast</h3>
            <span>Next 6 intervals</span>
          </div>

          <div class="forecast-list">
            <div class="forecast-row" *ngFor="let point of forecast">
              <span>T+{{point.index - telemetry.length}}</span>
              <strong>{{point.temperature | number:'1.1-1'}} C</strong>
              <small>{{point.vibration | number:'1.3-3'}} vibration</small>
            </div>
          </div>

          <form class="control-form" (ngSubmit)="sendControl()">
            <label>Control Mode</label>
            <select [(ngModel)]="controlMode" name="control_mode">
              <option value="auto">Auto</option>
              <option value="eco">Eco</option>
              <option value="maintenance">Maintenance</option>
            </select>

            <label>Target Temperature</label>
            <input type="number" [(ngModel)]="targetTemperature" name="target_temperature" min="16" max="32" step="0.5">

            <button class="btn btn-primary" type="submit">Queue Command</button>
          </form>

          <div class="command-status" *ngIf="commandStatus">{{commandStatus}}</div>
        </section>
      </div>

      <div class="content-grid ops-grid">
        <section class="panel">
          <div class="panel-header">
            <h3>Optimization Plan</h3>
            <span *ngIf="optimizationPlan">{{optimizationPlan.confidence | percent:'1.0-0'}} confidence</span>
          </div>

          <div class="plan-summary" *ngIf="optimizationPlan; else noPlan">
            <div>
              <label>Plan</label>
              <strong>{{optimizationPlan.plan_id}}</strong>
            </div>
            <div>
              <label>Savings</label>
              <strong>{{optimizationPlan.estimated_savings_kw | number:'1.1-1'}} kW</strong>
            </div>
          </div>

          <div class="action-list" *ngIf="optimizationPlan">
            <div class="action-row" *ngFor="let action of optimizationPlan.actions">
              <span>{{action.device_id}}</span>
              <strong>{{action.action}}</strong>
              <small>{{action.expected_impact}}</small>
            </div>
          </div>

          <ng-template #noPlan>
            <div class="empty-state">Run fleet optimization to generate an AI action plan.</div>
          </ng-template>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>Command History</h3>
            <span>{{commands.length}} recent</span>
          </div>

          <div class="command-list" *ngIf="commands.length > 0; else noCommands">
            <div class="command-row" *ngFor="let command of commands.slice(0, 6)">
              <span>{{command.device_id}}</span>
              <strong>{{command.mode}}</strong>
              <small>{{command.status}}</small>
            </div>
          </div>

          <ng-template #noCommands>
            <div class="empty-state">No commands queued yet.</div>
          </ng-template>
        </section>
      </div>

      <section class="panel insights-panel">
        <div class="panel-header">
          <h3>AI Recommendations</h3>
          <span>{{insights.length}} insights</span>
        </div>

        <div class="insight-list">
          <article class="insight-card" *ngFor="let insight of insights">
            <span [class]="'severity ' + insight.severity">{{insight.severity}}</span>
            <h4>{{insight.title}}</h4>
            <p>{{insight.impact}}</p>
            <strong>{{insight.recommendation}}</strong>
          </article>
        </div>
      </section>

      <div class="error" *ngIf="error">{{error}}</div>
    </div>
  `,
  styles: [`
    .iot-container {
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
      color: white;
    }

    .page-heading,
    .panel-header,
    .device-topline {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }

    .page-heading {
      margin-bottom: 1.5rem;
    }

    .heading-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .toggle {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: rgba(255, 255, 255, 0.14);
      border-radius: 8px;
      padding: 0.65rem 0.8rem;
      font-weight: 700;
    }

    h2,
    h3,
    h4,
    p {
      margin: 0;
    }

    .page-heading p,
    .panel-header span,
    .device-card p,
    .forecast-row small {
      color: rgba(255, 255, 255, 0.7);
    }

    .device-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .fleet-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .device-card,
    .fleet-card,
    .panel,
    .insight-card {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      backdrop-filter: blur(10px);
    }

    .fleet-card {
      padding: 1rem;
    }

    .fleet-card label,
    .plan-summary label {
      display: block;
      color: rgba(255, 255, 255, 0.68);
      font-size: 0.85rem;
      margin-bottom: 0.35rem;
    }

    .fleet-card strong {
      display: block;
      font-size: 1.35rem;
      margin-bottom: 0.35rem;
      overflow-wrap: anywhere;
    }

    .fleet-card span {
      color: rgba(255, 255, 255, 0.72);
      font-size: 0.9rem;
    }

    .device-card {
      color: white;
      cursor: pointer;
      padding: 1rem;
      text-align: left;
    }

    .device-card.selected,
    .device-card:hover {
      background: rgba(255, 255, 255, 0.17);
    }

    .metric-strip {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin: 1rem 0;
      font-size: 0.85rem;
    }

    .metric-strip span,
    .risk,
    .severity {
      background: rgba(255, 255, 255, 0.14);
      border-radius: 8px;
      padding: 0.35rem 0.5rem;
    }

    .risk.low,
    .severity.low {
      color: #bbf7d0;
    }

    .risk.medium,
    .severity.medium {
      color: #fde68a;
    }

    .risk.high,
    .severity.high {
      color: #fecaca;
    }

    progress {
      width: 100%;
      height: 10px;
      accent-color: #22c55e;
    }

    .content-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .ops-grid {
      grid-template-columns: 1fr 1fr;
    }

    .panel {
      padding: 1.25rem;
    }

    .chart {
      display: flex;
      align-items: end;
      gap: 0.35rem;
      height: 190px;
      margin: 1.25rem 0;
    }

    .chart span {
      flex: 1;
      min-width: 6px;
      border-radius: 6px 6px 0 0;
      background: linear-gradient(180deg, #38bdf8, #0ea5e9);
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
    }

    .stat,
    .forecast-row {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.8rem;
    }

    .stat label {
      display: block;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 0.35rem;
    }

    .forecast-list {
      display: grid;
      gap: 0.65rem;
      margin: 1rem 0;
    }

    .forecast-row {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 0.75rem;
      align-items: center;
    }

    .plan-summary {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .action-list,
    .command-list {
      display: grid;
      gap: 0.65rem;
    }

    .action-row,
    .command-row {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 0.75rem;
      align-items: center;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.75rem;
    }

    .action-row small,
    .command-row small,
    .empty-state {
      color: rgba(255, 255, 255, 0.7);
    }

    .control-form {
      display: grid;
      gap: 0.65rem;
      margin-top: 1rem;
    }

    select,
    input {
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.25);
      border-radius: 8px;
      color: white;
      padding: 0.7rem;
    }

    .btn {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 700;
      padding: 0.75rem 1rem;
    }

    .btn-primary {
      background: #22c55e;
      color: #052e16;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.18);
      color: white;
    }

    .command-status {
      margin-top: 0.75rem;
      color: #bbf7d0;
    }

    .insight-list {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }

    .insight-card {
      padding: 1rem;
    }

    .insight-card h4 {
      margin: 0.75rem 0 0.35rem;
    }

    .insight-card p {
      color: rgba(255, 255, 255, 0.76);
      margin-bottom: 0.75rem;
    }

    .error {
      color: #fecaca;
      margin-top: 1rem;
    }

    @media (max-width: 860px) {
      .iot-container {
        padding: 1rem;
      }

      .page-heading,
      .fleet-grid,
      .content-grid,
      .stats-grid,
      .forecast-row,
      .plan-summary,
      .action-row,
      .command-row {
        grid-template-columns: 1fr;
      }

      .page-heading,
      .panel-header {
        flex-direction: column;
      }

      .heading-actions {
        justify-content: flex-start;
      }
    }
  `]
})
export class IoTAiComponent implements OnInit, OnDestroy {
  devices: IoTDevice[] = [];
  selectedDevice: IoTDevice | null = null;
  fleetSummary: FleetSummary | null = null;
  telemetry: TelemetryPoint[] = [];
  forecast: TelemetryPoint[] = [];
  insights: IoTInsight[] = [];
  commands: IoTCommand[] = [];
  optimizationPlan: OptimizationPlan | null = null;
  controlMode = 'auto';
  targetTemperature = 24;
  commandStatus = '';
  autoRefresh = false;
  optimizing = false;
  loading = false;
  error = '';
  private refreshTimer: ReturnType<typeof setInterval> | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadData();
  }

  ngOnDestroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  loadData() {
    this.loading = true;
    this.error = '';
    this.loadFleetSummary();
    this.loadCommands();

    this.api.get<{ devices: IoTDevice[] }>('iot/devices').subscribe({
      next: (data) => {
        this.devices = data.devices;
        this.selectedDevice = this.selectedDevice
          ? this.devices.find((device) => device.id === this.selectedDevice?.id) || this.devices[0]
          : this.devices[0];
        this.loadTelemetry();
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load IoT devices:', err);
        this.error = 'Failed to load IoT device data';
        this.loading = false;
      }
    });

    this.api.get<{ insights: IoTInsight[] }>('iot/insights').subscribe({
      next: (data) => {
        this.insights = data.insights;
      },
      error: (err) => console.error('Failed to load IoT insights:', err)
    });
  }

  loadFleetSummary() {
    this.api.get<FleetSummary>('iot/fleet/summary').subscribe({
      next: (data) => {
        this.fleetSummary = data;
      },
      error: (err) => console.error('Failed to load fleet summary:', err)
    });
  }

  loadCommands() {
    this.api.get<{ commands: IoTCommand[] }>('iot/commands').subscribe({
      next: (data) => {
        this.commands = data.commands;
      },
      error: (err) => console.error('Failed to load command history:', err)
    });
  }

  selectDevice(device: IoTDevice) {
    this.selectedDevice = device;
    this.commandStatus = '';
    this.loadTelemetry();
  }

  loadTelemetry() {
    if (!this.selectedDevice) {
      return;
    }

    this.api.get<{ telemetry: TelemetryPoint[]; forecast: TelemetryPoint[] }>(
      `iot/telemetry?device_id=${encodeURIComponent(this.selectedDevice.id)}&points=24`
    ).subscribe({
      next: (data) => {
        this.telemetry = data.telemetry;
        this.forecast = data.forecast;
      },
      error: (err) => console.error('Failed to load telemetry:', err)
    });
  }

  sendControl() {
    if (!this.selectedDevice) {
      return;
    }

    this.api.post<{ id: string }>('iot/control', {
      device_id: this.selectedDevice.id,
      mode: this.controlMode,
      target_temperature: this.targetTemperature
    }).subscribe({
      next: (response) => {
        this.commandStatus = `Command ${response.id} queued`;
        this.loadCommands();
      },
      error: (err) => {
        console.error('Failed to queue command:', err);
        this.commandStatus = 'Command failed';
      }
    });
  }

  runOptimization() {
    this.optimizing = true;
    this.api.post<OptimizationPlan>('iot/optimize', { objective: 'energy' }).subscribe({
      next: (plan) => {
        this.optimizationPlan = plan;
        this.optimizing = false;
      },
      error: (err) => {
        console.error('Failed to optimize IoT fleet:', err);
        this.optimizing = false;
      }
    });
  }

  toggleAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }

    if (this.autoRefresh) {
      this.refreshTimer = setInterval(() => {
        this.loadData();
      }, 8000);
    }
  }

  barHeight(value: number): number {
    return Math.max(12, Math.min(100, ((value - 15) / 30) * 100));
  }
}
