import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { ModelService } from '../../services/model.service';
import { TrainingService } from '../../services/training.service';
import { PerformanceStats, Statistics } from '../../models/model.model';
import { TuningSession } from '../../models/training.model';

interface SystemHealth {
  status: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  active_trainings: number;
  timestamp: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-container">
      <div class="page-heading">
        <div>
          <h2>AI Operations</h2>
          <p>Training, tuning, model inventory, and runtime health in one place.</p>
        </div>
        <button class="btn btn-secondary" (click)="loadData()" [disabled]="loading">
          {{loading ? 'Refreshing...' : 'Refresh'}}
        </button>
      </div>

      <div class="summary-cards" *ngIf="statistics">
        <button class="card" type="button" (click)="goTo('/export-import')">
          <div class="card-label">Models</div>
          <strong>{{statistics.total_models}}</strong>
          <span>Stored model files</span>
        </button>

        <button class="card" type="button" (click)="goTo('/training')">
          <div class="card-label">Sessions</div>
          <strong>{{statistics.total_training_sessions}}</strong>
          <span>Training log files</span>
        </button>

        <button class="card" type="button" (click)="goTo('/training')">
          <div class="card-label">Active</div>
          <strong>{{statistics.active_sessions}}</strong>
          <span>Running jobs</span>
        </button>

        <button class="card" type="button" (click)="goTo('/comparison')">
          <div class="card-label">Algorithms</div>
          <strong>{{statistics.algorithms.length}}</strong>
          <span>Available strategies</span>
        </button>
      </div>

      <div class="content-grid">
        <section class="panel" *ngIf="performanceStats">
          <div class="panel-header">
            <h3>Performance</h3>
            <span>Reward range</span>
          </div>

          <div class="stats-grid">
            <div class="stat-card">
              <label>Average</label>
              <strong>{{performanceStats.avg_reward | number:'1.2-2'}}</strong>
            </div>
            <div class="stat-card">
              <label>Best</label>
              <strong>{{performanceStats.max_reward | number:'1.2-2'}}</strong>
            </div>
            <div class="stat-card">
              <label>Floor</label>
              <strong>{{performanceStats.min_reward | number:'1.2-2'}}</strong>
            </div>
          </div>

          <div class="reward-bars" aria-label="Recent reward chart">
            <span
              *ngFor="let reward of performanceStats.rewards"
              [style.height.%]="reward"
              [title]="'Reward ' + (reward | number:'1.1-1')">
            </span>
          </div>
        </section>

        <section class="panel" *ngIf="systemHealth">
          <div class="panel-header">
            <h3>System Health</h3>
            <span class="status-pill">{{systemHealth.status}}</span>
          </div>

          <div class="meter-list">
            <div class="meter">
              <div><span>CPU</span><strong>{{systemHealth.cpu_usage | number:'1.1-1'}}%</strong></div>
              <progress [value]="systemHealth.cpu_usage" max="100"></progress>
            </div>
            <div class="meter">
              <div><span>Memory</span><strong>{{systemHealth.memory_usage | number:'1.1-1'}}%</strong></div>
              <progress [value]="systemHealth.memory_usage" max="100"></progress>
            </div>
            <div class="meter">
              <div><span>Disk</span><strong>{{systemHealth.disk_usage | number:'1.1-1'}}%</strong></div>
              <progress [value]="systemHealth.disk_usage" max="100"></progress>
            </div>
          </div>

          <div class="system-meta">
            <span>{{systemHealth.active_connections}} websocket connections</span>
            <span>{{systemHealth.active_trainings}} active trainings</span>
          </div>
        </section>
      </div>

      <div class="content-grid">
        <section class="panel">
          <div class="panel-header">
            <h3>Recent Tuning</h3>
            <button class="link-button" type="button" (click)="goTo('/training')">Open Training</button>
          </div>

          <div class="session-list" *ngIf="tuningSessions.length > 0; else noTuning">
            <button class="session-row" type="button" *ngFor="let session of tuningSessions.slice(0, 5)" (click)="goTo('/training')">
              <span>{{session.algorithm}} / {{session.method}}</span>
              <strong>{{session.best_trial.score | number:'1.4-4'}}</strong>
              <small>{{session.trials_completed}} trials</small>
            </button>
          </div>

          <ng-template #noTuning>
            <div class="empty-state">No tuning runs yet.</div>
          </ng-template>
        </section>

        <section class="panel" *ngIf="statistics">
          <div class="panel-header">
            <h3>Algorithms</h3>
            <span>{{statistics.last_updated | date:'shortTime'}}</span>
          </div>

          <div class="algorithms-list">
            <span class="algorithm-chip" *ngFor="let algorithm of statistics.algorithms">
              {{algorithm}}
            </span>
          </div>
        </section>
      </div>

      <div class="quick-actions">
        <button class="btn btn-primary" (click)="goTo('/training')">Start Training</button>
        <button class="btn btn-secondary" (click)="goTo('/visualization')">Open Visualization</button>
        <button class="btn btn-secondary" (click)="goTo('/iot-ai')">Open IoT AI</button>
        <button class="btn btn-secondary" (click)="goTo('/comparison')">Compare Models</button>
        <button class="btn btn-secondary" (click)="goTo('/export-import')">Import or Export</button>
      </div>

      <div class="loading" *ngIf="loading">Loading dashboard data...</div>

      <div class="error" *ngIf="error">
        <p>{{error}}</p>
        <button class="btn btn-primary" (click)="loadData()">Retry</button>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    .page-heading {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1.5rem;
      color: white;
    }

    .page-heading h2 {
      margin: 0;
      font-size: 2rem;
    }

    .page-heading p {
      margin: 0.35rem 0 0 0;
      color: rgba(255, 255, 255, 0.78);
    }

    .summary-cards,
    .content-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .content-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .card,
    .panel {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
    }

    .card {
      cursor: pointer;
      text-align: left;
      padding: 1.25rem;
      min-height: 128px;
      transition: transform 0.2s ease, background 0.2s ease;
    }

    .card:hover {
      background: rgba(255, 255, 255, 0.16);
      transform: translateY(-2px);
    }

    .card-label,
    .panel-header span,
    .session-row small {
      color: rgba(255, 255, 255, 0.68);
      font-size: 0.86rem;
    }

    .card strong {
      display: block;
      margin: 0.4rem 0;
      font-size: 2.25rem;
      line-height: 1;
    }

    .card span {
      color: rgba(255, 255, 255, 0.78);
    }

    .panel {
      padding: 1.25rem;
      min-height: 260px;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .panel-header h3 {
      margin: 0;
      font-size: 1.2rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
      margin-bottom: 1rem;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.9rem;
      text-align: center;
    }

    .stat-card label {
      display: block;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 0.4rem;
      font-size: 0.84rem;
    }

    .stat-card strong {
      font-size: 1.35rem;
    }

    .reward-bars {
      display: flex;
      align-items: end;
      gap: 0.45rem;
      height: 116px;
      padding-top: 0.5rem;
    }

    .reward-bars span {
      flex: 1;
      min-width: 8px;
      border-radius: 6px 6px 0 0;
      background: linear-gradient(180deg, #4ade80, #22c55e);
    }

    .status-pill {
      background: rgba(34, 197, 94, 0.2);
      border: 1px solid rgba(34, 197, 94, 0.35);
      border-radius: 999px;
      color: #dcfce7;
      padding: 0.35rem 0.7rem;
      text-transform: uppercase;
    }

    .meter-list {
      display: grid;
      gap: 0.9rem;
    }

    .meter div,
    .system-meta {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      color: rgba(255, 255, 255, 0.82);
    }

    progress {
      width: 100%;
      height: 12px;
      accent-color: #4ade80;
    }

    .system-meta {
      margin-top: 1rem;
      flex-wrap: wrap;
      font-size: 0.9rem;
    }

    .session-list {
      display: grid;
      gap: 0.65rem;
    }

    .session-row {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 0.75rem;
      align-items: center;
      width: 100%;
      padding: 0.8rem;
      border: 0;
      border-radius: 8px;
      color: white;
      background: rgba(255, 255, 255, 0.06);
      text-align: left;
      cursor: pointer;
    }

    .session-row:hover {
      background: rgba(255, 255, 255, 0.12);
    }

    .algorithms-list {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .algorithm-chip {
      background: rgba(255, 255, 255, 0.14);
      border: 1px solid rgba(255, 255, 255, 0.22);
      border-radius: 8px;
      color: white;
      padding: 0.55rem 0.75rem;
    }

    .quick-actions {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-top: 1rem;
    }

    .btn,
    .link-button {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }

    .btn {
      padding: 0.75rem 1rem;
      font-size: 0.95rem;
    }

    .btn:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .btn-primary {
      background: #22c55e;
      color: #052e16;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.18);
      color: white;
    }

    .link-button {
      background: transparent;
      color: white;
      padding: 0.25rem;
    }

    .empty-state,
    .loading,
    .error {
      color: rgba(255, 255, 255, 0.76);
      padding: 1rem 0;
    }

    @media (max-width: 980px) {
      .summary-cards,
      .content-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 680px) {
      .dashboard-container {
        padding: 1rem;
      }

      .page-heading,
      .panel-header {
        flex-direction: column;
        align-items: stretch;
      }

      .summary-cards,
      .content-grid,
      .stats-grid,
      .session-row {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  statistics: Statistics | null = null;
  performanceStats: PerformanceStats | null = null;
  systemHealth: SystemHealth | null = null;
  tuningSessions: TuningSession[] = [];
  loading = false;
  error: string | null = null;

  constructor(
    private api: ApiService,
    private modelService: ModelService,
    private trainingService: TrainingService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.error = null;
    let pending = 4;
    const finish = () => {
      pending -= 1;
      this.loading = pending > 0;
    };

    this.modelService.getStatistics().subscribe({
      next: (data) => {
        this.statistics = data;
        finish();
      },
      error: (err) => {
        this.error = 'Failed to load dashboard statistics';
        console.error(err);
        finish();
      }
    });

    this.modelService.getPerformanceStats().subscribe({
      next: (data) => {
        this.performanceStats = data;
        finish();
      },
      error: (err) => {
        console.error('Failed to load performance stats:', err);
        finish();
      }
    });

    this.api.get<SystemHealth>('system/health').subscribe({
      next: (data) => {
        this.systemHealth = data;
        finish();
      },
      error: (err) => {
        console.error('Failed to load system health:', err);
        finish();
      }
    });

    this.trainingService.getTuningSessions().subscribe({
      next: (data) => {
        this.tuningSessions = data.sessions.slice().reverse();
        finish();
      },
      error: (err) => {
        console.error('Failed to load tuning sessions:', err);
        finish();
      }
    });
  }

  goTo(path: string) {
    this.router.navigateByUrl(path);
  }
}
