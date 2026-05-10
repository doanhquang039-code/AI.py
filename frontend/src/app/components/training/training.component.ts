import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TrainingService } from '../../services/training.service';
import { ModelService } from '../../services/model.service';
import { TrainingConfig, TrainingStatus } from '../../models/training.model';
import { Algorithm } from '../../models/model.model';

@Component({
  selector: 'app-training',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="training-container">
      <h2>🚀 AI Training</h2>

      <!-- Training Configuration -->
      <div class="config-section">
        <h3>⚙️ Training Configuration</h3>
        
        <form class="config-form" (ngSubmit)="startTraining()">
          <div class="form-group">
            <label>Algorithm</label>
            <select [(ngModel)]="config.algorithm" name="algorithm" required>
              <option value="">Select Algorithm</option>
              <option *ngFor="let algo of algorithms" [value]="algo.id">
                {{algo.name}}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Episodes</label>
              <input type="number" [(ngModel)]="config.episodes" name="episodes" 
                     min="1" max="10000" required>
            </div>

            <div class="form-group">
              <label>Learning Rate</label>
              <input type="number" [(ngModel)]="config.learning_rate" name="learning_rate" 
                     step="0.0001" min="0.0001" max="1" required>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Gamma (Discount Factor)</label>
              <input type="number" [(ngModel)]="config.gamma" name="gamma" 
                     step="0.01" min="0" max="1" required>
            </div>

            <div class="form-group">
              <label>Epsilon (Exploration)</label>
              <input type="number" [(ngModel)]="config.epsilon" name="epsilon" 
                     step="0.01" min="0" max="1">
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" [disabled]="isTraining">
              {{isTraining ? '⏸️ Training...' : '🚀 Start Training'}}
            </button>
            <button type="button" class="btn btn-danger" (click)="stopTraining()" 
                    [disabled]="!isTraining">
              ⏹️ Stop Training
            </button>
          </div>
        </form>
      </div>

      <!-- Training Status -->
      <div class="status-section" *ngIf="status">
        <h3>📊 Training Status</h3>
        
        <div class="status-card">
          <div class="status-header">
            <span class="status-badge" [class.active]="status.status === 'running'">
              {{status.status}}
            </span>
            <span class="episode-info">
              Episode {{status.current_episode}} / {{status.total_episodes}}
            </span>
          </div>

          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="status.progress"></div>
          </div>
          <div class="progress-text">{{status.progress}}%</div>

          <div class="metrics-grid">
            <div class="metric">
              <label>Reward</label>
              <div class="value">{{status.metrics.reward | number:'1.2-2'}}</div>
            </div>
            <div class="metric">
              <label>Loss</label>
              <div class="value">{{status.metrics.loss | number:'1.4-4'}}</div>
            </div>
            <div class="metric">
              <label>Epsilon</label>
              <div class="value">{{status.metrics.epsilon | number:'1.3-3'}}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Training History -->
      <div class="history-section">
        <h3>📜 Training History</h3>
        <button class="btn btn-secondary" (click)="loadHistory()">
          🔄 Refresh History
        </button>

        <div class="history-list" *ngIf="history.length > 0">
          <div class="history-item" *ngFor="let item of history">
            <div class="history-icon">📊</div>
            <div class="history-content">
              <div class="history-title">{{item.filename}}</div>
              <div class="history-meta">
                Episodes: {{item.episodes}} | Created: {{item.created_at}}
              </div>
            </div>
          </div>
        </div>

        <div class="empty-state" *ngIf="history.length === 0 && !loading">
          <p>No training history found</p>
        </div>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>
    </div>
  `,
  styles: [`
    .training-container {
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }

    h2, h3 {
      color: white;
      margin-bottom: 1.5rem;
    }

    .config-section,
    .status-section,
    .history-section {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .config-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-group label {
      color: rgba(255, 255, 255, 0.9);
      font-weight: 500;
    }

    .form-group input,
    .form-group select {
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      background: rgba(255, 255, 255, 0.1);
      color: white;
      font-size: 1rem;
    }

    .form-group input:focus,
    .form-group select:focus {
      outline: none;
      border-color: #667eea;
      background: rgba(255, 255, 255, 0.15);
    }

    .form-actions {
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
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

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      transform: scale(1.05);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: white;
      margin-bottom: 1rem;
    }

    .btn-danger {
      background: #f44336;
      color: white;
    }

    .status-card {
      background: rgba(255, 255, 255, 0.05);
      padding: 1.5rem;
      border-radius: 8px;
    }

    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }

    .status-badge {
      padding: 0.5rem 1rem;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.2);
      color: white;
      font-size: 0.9rem;
      text-transform: uppercase;
    }

    .status-badge.active {
      background: #4caf50;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    .episode-info {
      color: rgba(255, 255, 255, 0.8);
    }

    .progress-bar {
      height: 20px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 0.5rem;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      transition: width 0.3s ease;
    }

    .progress-text {
      text-align: center;
      color: white;
      font-weight: bold;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-top: 1.5rem;
    }

    .metric {
      text-align: center;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
    }

    .metric label {
      display: block;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }

    .metric .value {
      font-size: 1.5rem;
      font-weight: bold;
      color: white;
    }

    .history-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .history-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      transition: background 0.3s ease;
    }

    .history-item:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .history-icon {
      font-size: 2rem;
    }

    .history-content {
      flex: 1;
    }

    .history-title {
      color: white;
      font-weight: 500;
      margin-bottom: 0.25rem;
    }

    .history-meta {
      color: rgba(255, 255, 255, 0.6);
      font-size: 0.9rem;
    }

    .empty-state {
      text-align: center;
      padding: 2rem;
      color: rgba(255, 255, 255, 0.6);
    }

    .loading {
      text-align: center;
      padding: 2rem;
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
export class TrainingComponent implements OnInit {
  config: TrainingConfig = {
    algorithm: '',
    episodes: 100,
    learning_rate: 0.001,
    gamma: 0.99,
    epsilon: 0.1
  };

  status: TrainingStatus | null = null;
  algorithms: Algorithm[] = [];
  history: any[] = [];
  isTraining = false;
  loading = false;
  currentSessionId: string | null = null;

  constructor(
    private trainingService: TrainingService,
    private modelService: ModelService
  ) {}

  ngOnInit() {
    this.loadAlgorithms();
    this.loadStatus();
    this.loadHistory();
  }

  loadAlgorithms() {
    this.modelService.getAlgorithms().subscribe({
      next: (data) => {
        this.algorithms = data.algorithms;
      },
      error: (err) => console.error('Failed to load algorithms:', err)
    });
  }

  loadStatus() {
    this.trainingService.getStatus().subscribe({
      next: (data) => {
        this.status = data;
        this.isTraining = data.status === 'running';
      },
      error: (err) => console.error('Failed to load status:', err)
    });
  }

  loadHistory() {
    this.loading = true;
    this.trainingService.getHistory().subscribe({
      next: (data) => {
        this.history = data.history;
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load history:', err);
        this.loading = false;
      }
    });
  }

  startTraining() {
    if (!this.config.algorithm) {
      alert('Please select an algorithm');
      return;
    }

    this.isTraining = true;
    this.trainingService.startTraining(this.config).subscribe({
      next: (response) => {
        console.log('Training started:', response);
        this.currentSessionId = response.session_id;
        this.loadStatus();
      },
      error: (err) => {
        console.error('Failed to start training:', err);
        this.isTraining = false;
        alert('Failed to start training');
      }
    });
  }

  stopTraining() {
    if (!this.currentSessionId) {
      alert('No active training session');
      return;
    }

    this.trainingService.stopTraining(this.currentSessionId).subscribe({
      next: (response) => {
        console.log('Training stopped:', response);
        this.isTraining = false;
        this.loadStatus();
        this.loadHistory();
      },
      error: (err) => {
        console.error('Failed to stop training:', err);
        alert('Failed to stop training');
      }
    });
  }
}
