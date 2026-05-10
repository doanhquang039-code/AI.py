import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ModelService } from '../../services/model.service';
import { TrainingService } from '../../services/training.service';
import { Statistics, PerformanceStats } from '../../models/model.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-container">
      <h2>📊 AI Training Dashboard</h2>
      
      <!-- Summary Cards -->
      <div class="summary-cards" *ngIf="statistics">
        <div class="card">
          <div class="card-icon">🤖</div>
          <div class="card-content">
            <h3>{{statistics.total_models}}</h3>
            <p>Trained Models</p>
          </div>
        </div>
        
        <div class="card">
          <div class="card-icon">📈</div>
          <div class="card-content">
            <h3>{{statistics.total_training_sessions}}</h3>
            <p>Training Sessions</p>
          </div>
        </div>
        
        <div class="card">
          <div class="card-icon">⚡</div>
          <div class="card-content">
            <h3>{{statistics.active_sessions}}</h3>
            <p>Active Sessions</p>
          </div>
        </div>
        
        <div class="card">
          <div class="card-icon">🧠</div>
          <div class="card-content">
            <h3>{{statistics.algorithms.length}}</h3>
            <p>Algorithms</p>
          </div>
        </div>
      </div>

      <!-- Performance Overview -->
      <div class="performance-section" *ngIf="performanceStats">
        <h3>📈 Performance Overview</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <label>Average Reward</label>
            <div class="stat-value">{{performanceStats.avg_reward | number:'1.2-2'}}</div>
          </div>
          <div class="stat-card">
            <label>Max Reward</label>
            <div class="stat-value success">{{performanceStats.max_reward | number:'1.2-2'}}</div>
          </div>
          <div class="stat-card">
            <label>Min Reward</label>
            <div class="stat-value warning">{{performanceStats.min_reward | number:'1.2-2'}}</div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="quick-actions">
        <h3>⚡ Quick Actions</h3>
        <div class="action-buttons">
          <button class="btn btn-primary" (click)="navigateToTraining()">
            🚀 Start Training
          </button>
          <button class="btn btn-secondary" (click)="navigateToModels()">
            📦 View Models
          </button>
          <button class="btn btn-secondary" (click)="navigateToStats()">
            📊 Statistics
          </button>
        </div>
      </div>

      <!-- Algorithms List -->
      <div class="algorithms-section" *ngIf="statistics">
        <h3>🧠 Available Algorithms</h3>
        <div class="algorithms-list">
          <div class="algorithm-chip" *ngFor="let algo of statistics.algorithms">
            {{algo}}
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div class="loading" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading dashboard data...</p>
      </div>

      <!-- Error State -->
      <div class="error" *ngIf="error">
        <p>❌ {{error}}</p>
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

    h2 {
      color: white;
      margin-bottom: 2rem;
      font-size: 2rem;
    }

    h3 {
      color: white;
      margin-bottom: 1rem;
      font-size: 1.5rem;
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .card {
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

    .card:hover {
      transform: translateY(-5px);
    }

    .card-icon {
      font-size: 3rem;
    }

    .card-content h3 {
      margin: 0;
      font-size: 2.5rem;
      color: white;
    }

    .card-content p {
      margin: 0.5rem 0 0 0;
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.9rem;
    }

    .performance-section,
    .quick-actions,
    .algorithms-section {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      padding: 1rem;
      border-radius: 8px;
      text-align: center;
    }

    .stat-card label {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
      display: block;
      margin-bottom: 0.5rem;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: bold;
      color: white;
    }

    .stat-value.success {
      color: #4caf50;
    }

    .stat-value.warning {
      color: #ff9800;
    }

    .action-buttons {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
    }

    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .btn-primary:hover {
      transform: scale(1.05);
      box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    .algorithms-list {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .algorithm-chip {
      background: rgba(255, 255, 255, 0.2);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.9rem;
      border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .loading,
    .error {
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
export class DashboardComponent implements OnInit {
  statistics: Statistics | null = null;
  performanceStats: PerformanceStats | null = null;
  loading = false;
  error: string | null = null;

  constructor(
    private modelService: ModelService,
    private trainingService: TrainingService
  ) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.error = null;

    // Load statistics
    this.modelService.getStatistics().subscribe({
      next: (data) => {
        this.statistics = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load statistics';
        this.loading = false;
        console.error(err);
      }
    });

    // Load performance stats
    this.modelService.getPerformanceStats().subscribe({
      next: (data) => {
        this.performanceStats = data;
      },
      error: (err) => {
        console.error('Failed to load performance stats:', err);
      }
    });
  }

  navigateToTraining() {
    // Navigate to training page
    console.log('Navigate to training');
  }

  navigateToModels() {
    // Navigate to models page
    console.log('Navigate to models');
  }

  navigateToStats() {
    // Navigate to statistics page
    console.log('Navigate to statistics');
  }
}
