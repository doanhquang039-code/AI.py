import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface AnalyticsDataset {
  id: string;
  name: string;
  description: string;
  records: number;
  freshness: string;
}

interface AnalyticsSummary {
  dataset: string;
  records: number;
  mean: number;
  min: number;
  max: number;
  trend: number;
  anomaly_count: number;
  quality_score: number;
}

interface AnalyticsPoint {
  index?: number;
  label?: string;
  step?: number;
  value: number;
  anomaly_score?: number;
  confidence?: number;
}

interface AnalyticsRun {
  run_id: string;
  dataset: string;
  sensitivity: number;
  history: AnalyticsPoint[];
  forecast: AnalyticsPoint[];
  anomalies: AnalyticsPoint[];
  correlations: Array<{ feature: string; correlation: number }>;
  recommendations: Array<{ priority: string; title: string; action: string }>;
  generated_at: string;
}

interface AnalyticsInsight {
  title: string;
  severity: string;
  body: string;
}

@Component({
  selector: 'app-data-analytics-ai',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="analytics-container">
      <div class="page-heading">
        <div>
          <h2>Data Analytics AI</h2>
          <p>Analyze operations, IoT telemetry, and biometric identity signals with forecast and anomaly scoring.</p>
        </div>
        <button class="btn btn-secondary" type="button" (click)="loadAll()" [disabled]="loading">
          {{loading ? 'Refreshing...' : 'Refresh'}}
        </button>
      </div>

      <div class="dataset-grid">
        <button
          class="dataset-card"
          type="button"
          *ngFor="let item of datasets"
          [class.selected]="dataset === item.id"
          (click)="selectDataset(item.id)">
          <div class="dataset-topline">
            <strong>{{item.name}}</strong>
            <span>{{item.records | number}} rows</span>
          </div>
          <p>{{item.description}}</p>
          <small>{{item.freshness}}</small>
        </button>
      </div>

      <div class="summary-grid" *ngIf="summary">
        <article class="summary-card">
          <label>Mean</label>
          <strong>{{summary.mean | number:'1.1-2'}}</strong>
          <span>{{summary.records}} points</span>
        </article>
        <article class="summary-card">
          <label>Trend</label>
          <strong>{{summary.trend | number:'1.1-2'}}</strong>
          <span>{{summary.trend >= 0 ? 'upward' : 'downward'}}</span>
        </article>
        <article class="summary-card">
          <label>Anomalies</label>
          <strong>{{summary.anomaly_count}}</strong>
          <span>sensitivity {{sensitivity | number:'1.2-2'}}</span>
        </article>
        <article class="summary-card">
          <label>Quality</label>
          <strong>{{summary.quality_score | percent:'1.0-1'}}</strong>
          <span>analytics confidence</span>
        </article>
      </div>

      <section class="panel controls-panel">
        <div class="panel-header">
          <h3>Run Analysis</h3>
          <span *ngIf="run">{{run.run_id}}</span>
        </div>
        <div class="control-grid">
          <label>
            Forecast horizon
            <input type="number" min="3" max="30" [(ngModel)]="horizon" name="horizon">
          </label>
          <label>
            Sensitivity
            <input type="range" min="0.4" max="0.95" step="0.01" [(ngModel)]="sensitivity" name="sensitivity">
            <span>{{sensitivity | number:'1.2-2'}}</span>
          </label>
          <button class="btn btn-primary" type="button" (click)="runAnalysis()" [disabled]="running">
            {{running ? 'Analyzing...' : 'Run AI Analysis'}}
          </button>
        </div>
      </section>

      <div class="workspace-grid" *ngIf="run">
        <section class="panel chart-panel">
          <div class="panel-header">
            <h3>History Signal</h3>
            <span>{{run.history.length}} points</span>
          </div>
          <div class="bars">
            <span
              *ngFor="let point of run.history"
              [style.height.%]="point.value"
              [class.hot]="(point.anomaly_score || 0) >= run.sensitivity"
              [title]="point.value + ' / anomaly ' + point.anomaly_score">
            </span>
          </div>
        </section>

        <section class="panel chart-panel">
          <div class="panel-header">
            <h3>Forecast</h3>
            <span>{{run.forecast.length}} steps</span>
          </div>
          <div class="forecast-list">
            <article class="forecast-row" *ngFor="let point of run.forecast">
              <span>T+{{point.step}}</span>
              <strong>{{point.value | number:'1.1-2'}}</strong>
              <progress [value]="point.confidence || 0" max="1"></progress>
            </article>
          </div>
        </section>
      </div>

      <div class="workspace-grid" *ngIf="run">
        <section class="panel">
          <div class="panel-header">
            <h3>Correlation Drivers</h3>
            <span>{{run.correlations.length}} features</span>
          </div>
          <div class="driver-list">
            <article class="driver-row" *ngFor="let driver of run.correlations">
              <span>{{formatLabel(driver.feature)}}</span>
              <strong>{{driver.correlation | number:'1.2-2'}}</strong>
              <progress [value]="abs(driver.correlation)" max="1"></progress>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>AI Recommendations</h3>
            <span>{{run.recommendations.length}} actions</span>
          </div>
          <div class="recommendation-list">
            <article class="recommendation-card" *ngFor="let item of run.recommendations">
              <div>
                <strong>{{item.title}}</strong>
                <span [class]="'priority ' + item.priority">{{item.priority}}</span>
              </div>
              <p>{{item.action}}</p>
            </article>
          </div>
        </section>
      </div>

      <section class="panel">
        <div class="panel-header">
          <h3>Generated Insights</h3>
          <span>{{insights.length}} cards</span>
        </div>
        <div class="insight-grid">
          <article class="insight-card" *ngFor="let insight of insights">
            <span [class]="'priority ' + insight.severity">{{insight.severity}}</span>
            <strong>{{insight.title}}</strong>
            <p>{{insight.body}}</p>
          </article>
        </div>
      </section>

      <div class="error" *ngIf="error">{{error}}</div>
    </div>
  `,
  styles: [`
    .analytics-container {
      color: white;
      margin: 0 auto;
      max-width: 1440px;
      padding: 2rem;
    }

    .page-heading,
    .panel-header,
    .dataset-topline,
    .recommendation-card div {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
    }

    .page-heading {
      margin-bottom: 1.5rem;
    }

    h2,
    h3,
    p {
      margin: 0;
    }

    .page-heading p,
    .dataset-card p,
    .dataset-card small,
    .panel-header span,
    .summary-card span,
    .recommendation-card p,
    .insight-card p {
      color: rgba(255, 255, 255, 0.72);
    }

    .dataset-grid,
    .summary-grid,
    .workspace-grid,
    .insight-grid {
      display: grid;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .dataset-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .summary-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .workspace-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .insight-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .dataset-card,
    .summary-card,
    .panel {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
    }

    .dataset-card {
      cursor: pointer;
      min-height: 150px;
      padding: 1.15rem;
      text-align: left;
    }

    .dataset-card:hover,
    .dataset-card.selected {
      background: rgba(255, 255, 255, 0.17);
      border-color: rgba(45, 212, 191, 0.38);
    }

    .summary-card,
    .panel {
      padding: 1.2rem;
    }

    .summary-card label {
      color: rgba(255, 255, 255, 0.68);
      display: block;
      font-size: 0.85rem;
      margin-bottom: 0.42rem;
    }

    .summary-card strong {
      display: block;
      font-size: 2rem;
      line-height: 1;
      margin-bottom: 0.42rem;
    }

    .control-grid {
      align-items: end;
      display: grid;
      gap: 1rem;
      grid-template-columns: 180px 1fr auto;
      margin-top: 1rem;
    }

    label {
      color: rgba(255, 255, 255, 0.78);
      display: grid;
      font-size: 0.86rem;
      gap: 0.45rem;
    }

    input {
      background: rgba(15, 23, 42, 0.42);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
      min-height: 42px;
      padding: 0.65rem 0.75rem;
    }

    .btn {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 800;
      min-height: 42px;
      padding: 0.72rem 1rem;
    }

    .btn-primary {
      background: #22c55e;
      color: #052e16;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.18);
      color: white;
    }

    .btn:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .bars {
      align-items: end;
      display: flex;
      gap: 0.35rem;
      height: 220px;
      margin-top: 1rem;
    }

    .bars span {
      background: linear-gradient(180deg, #22c55e, #06b6d4);
      border-radius: 6px 6px 0 0;
      flex: 1;
      min-width: 5px;
    }

    .bars span.hot {
      background: linear-gradient(180deg, #f97316, #ef4444);
    }

    .forecast-list,
    .driver-list,
    .recommendation-list {
      display: grid;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    .forecast-row,
    .driver-row,
    .recommendation-card,
    .insight-card {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.85rem;
    }

    .forecast-row,
    .driver-row {
      align-items: center;
      display: grid;
      gap: 0.75rem;
      grid-template-columns: 80px 90px 1fr;
    }

    progress {
      accent-color: #22c55e;
      height: 10px;
      width: 100%;
    }

    .priority {
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 900;
      padding: 0.28rem 0.55rem;
      text-transform: uppercase;
    }

    .priority.high {
      background: rgba(248, 113, 113, 0.18);
      color: #fecaca;
    }

    .priority.medium {
      background: rgba(250, 204, 21, 0.16);
      color: #fde68a;
    }

    .priority.low {
      background: rgba(34, 197, 94, 0.14);
      color: #bbf7d0;
    }

    .insight-card strong {
      display: block;
      margin: 0.7rem 0 0.5rem;
    }

    .error {
      color: #fecaca;
      margin-top: 1rem;
    }

    @media (max-width: 980px) {
      .analytics-container {
        padding: 1rem;
      }

      .dataset-grid,
      .summary-grid,
      .workspace-grid,
      .insight-grid,
      .control-grid {
        grid-template-columns: 1fr;
      }

      .page-heading,
      .panel-header {
        flex-direction: column;
      }
    }
  `]
})
export class DataAnalyticsAiComponent implements OnInit {
  datasets: AnalyticsDataset[] = [];
  dataset = 'operations';
  summary: AnalyticsSummary | null = null;
  run: AnalyticsRun | null = null;
  insights: AnalyticsInsight[] = [];
  horizon = 7;
  sensitivity = 0.72;
  loading = false;
  running = false;
  error = '';
  abs = Math.abs;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadAll();
  }

  loadAll() {
    this.loading = true;
    this.error = '';
    let pending = 3;
    const finish = () => {
      pending -= 1;
      this.loading = pending > 0;
    };

    this.api.get<{ datasets: AnalyticsDataset[] }>('data-analytics/datasets').subscribe({
      next: data => {
        this.datasets = data.datasets;
        finish();
      },
      error: err => {
        console.error(err);
        this.error = 'Failed to load datasets';
        finish();
      }
    });

    this.api.get<AnalyticsSummary>(`data-analytics/summary?dataset=${this.dataset}`).subscribe({
      next: data => {
        this.summary = data;
        finish();
      },
      error: err => {
        console.error(err);
        finish();
      }
    });

    this.api.get<{ insights: AnalyticsInsight[] }>(`data-analytics/insights?dataset=${this.dataset}`).subscribe({
      next: data => {
        this.insights = data.insights;
        finish();
      },
      error: err => {
        console.error(err);
        finish();
      }
    });
  }

  selectDataset(dataset: string) {
    this.dataset = dataset;
    this.run = null;
    this.loadAll();
  }

  runAnalysis() {
    this.running = true;
    this.error = '';
    this.api.post<AnalyticsRun>('data-analytics/run', {
      dataset: this.dataset,
      horizon: Number(this.horizon),
      sensitivity: Number(this.sensitivity)
    }).subscribe({
      next: data => {
        this.run = data;
        this.running = false;
      },
      error: err => {
        console.error(err);
        this.error = 'Analysis failed';
        this.running = false;
      }
    });
  }

  formatLabel(value: string): string {
    return value.replace(/_/g, ' ');
  }
}
