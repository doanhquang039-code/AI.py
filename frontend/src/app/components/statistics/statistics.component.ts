import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { WebSocketService } from '../../services/websocket.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="statistics-container">
      <h2>📊 Statistics & Analytics</h2>

      <!-- Summary Cards -->
      <div class="summary-cards" *ngIf="detailedStats">
        <div class="stat-card">
          <div class="stat-icon">🤖</div>
          <div class="stat-content">
            <h3>{{detailedStats.total_models}}</h3>
            <p>Total Models</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-content">
            <h3>{{detailedStats.total_sessions}}</h3>
            <p>Training Sessions</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⚡</div>
          <div class="stat-content">
            <h3>{{detailedStats.active_sessions}}</h3>
            <p>Active Sessions</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🧪</div>
          <div class="stat-content">
            <h3>{{detailedStats.total_experiments}}</h3>
            <p>Experiments</p>
          </div>
        </div>
      </div>

      <!-- System Health -->
      <div class="health-section" *ngIf="detailedStats">
        <h3>💻 System Health</h3>
        <div class="health-grid">
          <div class="health-item">
            <label>CPU Usage</label>
            <div class="progress-bar">
              <div class="progress-fill cpu" 
                   [style.width.%]="detailedStats.system_info.cpu_usage"></div>
            </div>
            <span class="percentage">{{detailedStats.system_info.cpu_usage.toFixed(1)}}%</span>
          </div>

          <div class="health-item">
            <label>Memory Usage</label>
            <div class="progress-bar">
              <div class="progress-fill memory" 
                   [style.width.%]="detailedStats.system_info.memory_usage"></div>
            </div>
            <span class="percentage">{{detailedStats.system_info.memory_usage.toFixed(1)}}%</span>
          </div>

          <div class="health-item">
            <label>GPU Available</label>
            <div class="status-badge" [class.available]="detailedStats.system_info.gpu_available">
              {{detailedStats.system_info.gpu_available ? '✅ Yes' : '❌ No'}}
            </div>
          </div>
        </div>
      </div>

      <!-- Algorithm Performance Chart -->
      <div class="chart-section">
        <h3>🧠 Algorithm Performance Comparison</h3>
        <div class="chart-container">
          <canvas baseChart
                  [data]="algorithmChartData"
                  [options]="algorithmChartOptions"
                  [type]="'bar'">
          </canvas>
        </div>
      </div>

      <!-- Success Rate Chart -->
      <div class="chart-section">
        <h3>✅ Algorithm Success Rates</h3>
        <div class="chart-container">
          <canvas baseChart
                  [data]="successRateChartData"
                  [options]="successRateChartOptions"
                  [type]="'doughnut'">
          </canvas>
        </div>
      </div>

      <!-- Training Progress Chart -->
      <div class="chart-section">
        <h3>📈 Training Progress Over Time</h3>
        <div class="chart-container">
          <canvas baseChart
                  [data]="progressChartData"
                  [options]="progressChartOptions"
                  [type]="'line'">
          </canvas>
        </div>
      </div>

      <!-- Algorithm Details Table -->
      <div class="table-section" *ngIf="detailedStats">
        <h3>📋 Algorithm Performance Details</h3>
        <table class="stats-table">
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Avg Reward</th>
              <th>Success Rate</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let algo of getAlgorithmList()">
              <td>{{algo.name}}</td>
              <td>{{algo.avg_reward.toFixed(2)}}</td>
              <td>{{(algo.success_rate * 100).toFixed(1)}}%</td>
              <td>
                <span class="status-badge" [class.high]="algo.success_rate > 0.8">
                  {{algo.success_rate > 0.8 ? '🟢 Excellent' : algo.success_rate > 0.6 ? '🟡 Good' : '🔴 Needs Improvement'}}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Real-time Updates -->
      <div class="updates-section">
        <h3>🔄 Real-time Updates</h3>
        <div class="connection-status">
          <span class="status-indicator" [class.connected]="isWebSocketConnected">
            {{isWebSocketConnected ? '🟢 Connected' : '🔴 Disconnected'}}
          </span>
          <button class="btn btn-secondary" (click)="refreshStats()">
            🔄 Refresh
          </button>
        </div>
        <div class="last-update">
          Last updated: {{lastUpdate | date:'medium'}}
        </div>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading statistics...</p>
      </div>
    </div>
  `,
  styles: [`
    .statistics-container {
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    h2, h3 {
      color: white;
      margin-bottom: 1.5rem;
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: transform 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-5px);
    }

    .stat-icon {
      font-size: 3rem;
    }

    .stat-content h3 {
      margin: 0;
      font-size: 2.5rem;
      color: white;
    }

    .stat-content p {
      margin: 0.5rem 0 0 0;
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.9rem;
    }

    .health-section,
    .chart-section,
    .table-section,
    .updates-section {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .health-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .health-item {
      background: rgba(255, 255, 255, 0.05);
      padding: 1rem;
      border-radius: 8px;
    }

    .health-item label {
      display: block;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }

    .progress-bar {
      height: 12px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 0.5rem;
    }

    .progress-fill {
      height: 100%;
      transition: width 0.3s ease;
    }

    .progress-fill.cpu {
      background: linear-gradient(90deg, #4caf50 0%, #ff9800 50%, #f44336 100%);
    }

    .progress-fill.memory {
      background: linear-gradient(90deg, #2196f3 0%, #9c27b0 100%);
    }

    .percentage {
      color: white;
      font-size: 0.9rem;
      font-weight: 500;
    }

    .status-badge {
      display: inline-block;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.2);
      color: white;
      font-size: 0.9rem;
    }

    .status-badge.available,
    .status-badge.high {
      background: #4caf50;
    }

    .chart-container {
      position: relative;
      height: 400px;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
    }

    .stats-table {
      width: 100%;
      border-collapse: collapse;
      color: white;
    }

    .stats-table thead {
      background: rgba(255, 255, 255, 0.1);
    }

    .stats-table th,
    .stats-table td {
      padding: 1rem;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stats-table tbody tr:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    .connection-status {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .status-indicator {
      padding: 0.5rem 1rem;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.2);
      color: white;
      font-size: 0.9rem;
    }

    .status-indicator.connected {
      background: #4caf50;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    .last-update {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
    }

    .btn {
      padding: 0.5rem 1rem;
      border: none;
      border-radius: 8px;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    .loading {
      text-align: center;
      padding: 3rem;
      color: white;
    }

    .spinner {
      border: 4px solid rgba(255, 255, 255, 0.3);
      border-top: 4px solid white;
      border-radius: 50%;
      width: 50px;
      height: 50px;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class StatisticsComponent implements OnInit, OnDestroy {
  detailedStats: any = null;
  loading = false;
  lastUpdate = new Date();
  isWebSocketConnected = false;
  private wsSubscription?: Subscription;

  // Chart data
  algorithmChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{
      label: 'Average Reward',
      data: [],
      backgroundColor: 'rgba(102, 126, 234, 0.8)',
      borderColor: 'rgba(102, 126, 234, 1)',
      borderWidth: 2
    }]
  };

  successRateChartData: ChartData<'doughnut'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(76, 175, 80, 0.8)',
        'rgba(255, 152, 0, 0.8)',
        'rgba(244, 67, 54, 0.8)'
      ]
    }]
  };

  progressChartData: ChartData<'line'> = {
    labels: [],
    datasets: [{
      label: 'Training Progress',
      data: [],
      borderColor: 'rgba(102, 126, 234, 1)',
      backgroundColor: 'rgba(102, 126, 234, 0.2)',
      fill: true,
      tension: 0.4
    }]
  };

  // Chart options
  algorithmChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: 'white' }
      }
    },
    scales: {
      y: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      x: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  };

  successRateChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: { color: 'white' }
      }
    }
  };

  progressChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: 'white' }
      }
    },
    scales: {
      y: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      x: {
        ticks: { color: 'white' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  };

  constructor(
    private apiService: ApiService,
    private wsService: WebSocketService
  ) {}

  ngOnInit() {
    this.loadDetailedStats();
    this.setupWebSocket();
  }

  ngOnDestroy() {
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
    }
  }

  setupWebSocket() {
    this.isWebSocketConnected = this.wsService.isSocketConnected();
    
    // Subscribe to WebSocket messages
    this.wsSubscription = this.wsService.messages$.subscribe({
      next: (message) => {
        if (message.type === 'training_update' || message.type === 'model_update') {
          this.refreshStats();
        }
      }
    });
  }

  loadDetailedStats() {
    this.loading = true;
    this.apiService.get<any>('api/stats/detailed').subscribe({
      next: (data) => {
        this.detailedStats = data;
        this.updateCharts();
        this.lastUpdate = new Date();
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load detailed stats:', err);
        this.loading = false;
      }
    });
  }

  updateCharts() {
    if (!this.detailedStats || !this.detailedStats.algorithm_stats) {
      return;
    }

    const algorithms = Object.keys(this.detailedStats.algorithm_stats);
    const rewards = algorithms.map(algo => 
      this.detailedStats.algorithm_stats[algo].avg_reward
    );
    const successRates = algorithms.map(algo => 
      this.detailedStats.algorithm_stats[algo].success_rate * 100
    );

    // Update algorithm performance chart
    this.algorithmChartData = {
      labels: algorithms,
      datasets: [{
        label: 'Average Reward',
        data: rewards,
        backgroundColor: 'rgba(102, 126, 234, 0.8)',
        borderColor: 'rgba(102, 126, 234, 1)',
        borderWidth: 2
      }]
    };

    // Update success rate chart
    this.successRateChartData = {
      labels: algorithms,
      datasets: [{
        data: successRates,
        backgroundColor: [
          'rgba(102, 126, 234, 0.8)',
          'rgba(118, 75, 162, 0.8)',
          'rgba(76, 175, 80, 0.8)',
          'rgba(255, 152, 0, 0.8)',
          'rgba(244, 67, 54, 0.8)'
        ]
      }]
    };

    // Update progress chart (mock data)
    const episodes = Array.from({ length: 10 }, (_, i) => `Ep ${(i + 1) * 10}`);
    const progress = Array.from({ length: 10 }, (_, i) => 
      Math.random() * 50 + 30 + (i * 5)
    );

    this.progressChartData = {
      labels: episodes,
      datasets: [{
        label: 'Training Progress',
        data: progress,
        borderColor: 'rgba(102, 126, 234, 1)',
        backgroundColor: 'rgba(102, 126, 234, 0.2)',
        fill: true,
        tension: 0.4
      }]
    };
  }

  getAlgorithmList() {
    if (!this.detailedStats || !this.detailedStats.algorithm_stats) {
      return [];
    }

    return Object.keys(this.detailedStats.algorithm_stats).map(name => ({
      name,
      ...this.detailedStats.algorithm_stats[name]
    }));
  }

  refreshStats() {
    this.loadDetailedStats();
  }
}
