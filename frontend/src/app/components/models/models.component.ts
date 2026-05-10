import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModelService } from '../../services/model.service';
import { Model } from '../../models/model.model';

@Component({
  selector: 'app-models',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="models-container">
      <h2>📦 Model Management</h2>

      <!-- Actions Bar -->
      <div class="actions-bar">
        <button class="btn btn-primary" (click)="loadModels()">
          🔄 Refresh
        </button>
        <button class="btn btn-secondary" (click)="showImportDialog = true">
          📥 Import Model
        </button>
        <div class="search-box">
          <input type="text" [(ngModel)]="searchTerm" placeholder="Search models..." 
                 (input)="filterModels()">
        </div>
      </div>

      <!-- Models Grid -->
      <div class="models-grid" *ngIf="filteredModels.length > 0">
        <div class="model-card" *ngFor="let model of filteredModels">
          <div class="model-header">
            <div class="model-icon">🤖</div>
            <div class="model-info">
              <h3>{{model.name}}</h3>
              <span class="algorithm-badge">{{model.algorithm}}</span>
            </div>
          </div>

          <div class="model-details">
            <div class="detail-row">
              <span class="label">Episodes:</span>
              <span class="value">{{model.episodes}}</span>
            </div>
            <div class="detail-row">
              <span class="label">Size:</span>
              <span class="value">{{formatSize(model.size)}}</span>
            </div>
            <div class="detail-row">
              <span class="label">Created:</span>
              <span class="value">{{formatDate(model.created_at)}}</span>
            </div>
          </div>

          <div class="model-performance">
            <div class="performance-item">
              <label>Accuracy</label>
              <div class="progress-bar">
                <div class="progress-fill" [style.width.%]="model.performance.accuracy * 100"></div>
              </div>
              <span class="percentage">{{(model.performance.accuracy * 100).toFixed(1)}}%</span>
            </div>
            <div class="performance-item">
              <label>Reward</label>
              <div class="reward-value">{{model.performance.reward.toFixed(2)}}</div>
            </div>
          </div>

          <div class="model-actions">
            <button class="btn-icon" (click)="exportModel(model.name)" title="Export">
              📥
            </button>
            <button class="btn-icon" (click)="evaluateModel(model.name)" title="Evaluate">
              📊
            </button>
            <button class="btn-icon" (click)="selectForComparison(model)" title="Compare">
              ⚖️
            </button>
            <button class="btn-icon danger" (click)="deleteModel(model.name)" title="Delete">
              🗑️
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div class="empty-state" *ngIf="filteredModels.length === 0 && !loading">
        <div class="empty-icon">📦</div>
        <p>No models found</p>
        <button class="btn btn-primary" (click)="loadModels()">Refresh</button>
      </div>

      <!-- Model Comparison -->
      <div class="comparison-section" *ngIf="selectedModels.length === 2">
        <h3>⚖️ Model Comparison</h3>
        <div class="comparison-grid">
          <div class="comparison-card" *ngFor="let model of selectedModels">
            <h4>{{model.name}}</h4>
            <p>Algorithm: {{model.algorithm}}</p>
            <p>Accuracy: {{(model.performance.accuracy * 100).toFixed(1)}}%</p>
            <p>Reward: {{model.performance.reward.toFixed(2)}}</p>
          </div>
        </div>
        <button class="btn btn-primary" (click)="compareModels()">
          Compare Models
        </button>
        <button class="btn btn-secondary" (click)="clearSelection()">
          Clear Selection
        </button>
      </div>

      <!-- Import Dialog -->
      <div class="dialog-overlay" *ngIf="showImportDialog" (click)="showImportDialog = false">
        <div class="dialog" (click)="$event.stopPropagation()">
          <h3>📥 Import Model</h3>
          <input type="file" (change)="onFileSelected($event)" accept=".pt,.npy">
          <div class="dialog-actions">
            <button class="btn btn-secondary" (click)="showImportDialog = false">Cancel</button>
            <button class="btn btn-primary" (click)="importModel()" [disabled]="!selectedFile">
              Import
            </button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading models...</p>
      </div>
    </div>
  `,
  styles: [`
    .models-container {
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    h2, h3 {
      color: white;
      margin-bottom: 1.5rem;
    }

    .actions-bar {
      display: flex;
      gap: 1rem;
      margin-bottom: 2rem;
      align-items: center;
    }

    .search-box {
      flex: 1;
      max-width: 300px;
    }

    .search-box input {
      width: 100%;
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.3);
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }

    .models-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 1.5rem;
    }

    .model-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: transform 0.3s ease;
    }

    .model-card:hover {
      transform: translateY(-5px);
    }

    .model-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .model-icon {
      font-size: 3rem;
    }

    .model-info h3 {
      margin: 0 0 0.5rem 0;
      font-size: 1.2rem;
      color: white;
    }

    .algorithm-badge {
      background: rgba(102, 126, 234, 0.3);
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 12px;
      font-size: 0.85rem;
    }

    .model-details {
      margin: 1rem 0;
    }

    .detail-row {
      display: flex;
      justify-content: space-between;
      padding: 0.5rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .detail-row .label {
      color: rgba(255, 255, 255, 0.7);
    }

    .detail-row .value {
      color: white;
      font-weight: 500;
    }

    .model-performance {
      margin: 1rem 0;
    }

    .performance-item {
      margin-bottom: 1rem;
    }

    .performance-item label {
      display: block;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }

    .progress-bar {
      height: 8px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 0.25rem;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      transition: width 0.3s ease;
    }

    .percentage {
      color: white;
      font-size: 0.9rem;
    }

    .reward-value {
      font-size: 1.5rem;
      font-weight: bold;
      color: #4caf50;
    }

    .model-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .btn-icon {
      flex: 1;
      padding: 0.5rem;
      border: none;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.1);
      color: white;
      font-size: 1.2rem;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-icon:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: scale(1.1);
    }

    .btn-icon.danger:hover {
      background: #f44336;
    }

    .comparison-section {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 1.5rem;
      margin-top: 2rem;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .comparison-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin: 1rem 0;
    }

    .comparison-card {
      background: rgba(255, 255, 255, 0.05);
      padding: 1rem;
      border-radius: 8px;
    }

    .comparison-card h4 {
      color: white;
      margin-bottom: 0.5rem;
    }

    .comparison-card p {
      color: rgba(255, 255, 255, 0.8);
      margin: 0.25rem 0;
    }

    .dialog-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }

    .dialog {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(20px);
      border-radius: 12px;
      padding: 2rem;
      min-width: 400px;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .dialog h3 {
      margin-top: 0;
    }

    .dialog input[type="file"] {
      width: 100%;
      padding: 1rem;
      margin: 1rem 0;
      border-radius: 8px;
      border: 2px dashed rgba(255, 255, 255, 0.3);
      background: rgba(255, 255, 255, 0.05);
      color: white;
    }

    .dialog-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
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

    .btn-secondary {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      color: white;
    }

    .empty-icon {
      font-size: 5rem;
      margin-bottom: 1rem;
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
export class ModelsComponent implements OnInit {
  models: Model[] = [];
  filteredModels: Model[] = [];
  selectedModels: Model[] = [];
  searchTerm = '';
  loading = false;
  showImportDialog = false;
  selectedFile: File | null = null;

  constructor(private modelService: ModelService) {}

  ngOnInit() {
    this.loadModels();
  }

  loadModels() {
    this.loading = true;
    this.modelService.getModels().subscribe({
      next: (data) => {
        this.models = data.models;
        this.filteredModels = this.models;
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load models:', err);
        this.loading = false;
      }
    });
  }

  filterModels() {
    if (!this.searchTerm) {
      this.filteredModels = this.models;
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredModels = this.models.filter(model =>
      model.name.toLowerCase().includes(term) ||
      model.algorithm.toLowerCase().includes(term)
    );
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }

  exportModel(modelName: string) {
    window.open(`http://localhost:8000/api/models/export/${modelName}`, '_blank');
  }

  evaluateModel(modelName: string) {
    console.log('Evaluate model:', modelName);
    alert(`Evaluating model: ${modelName}`);
  }

  selectForComparison(model: Model) {
    if (this.selectedModels.includes(model)) {
      this.selectedModels = this.selectedModels.filter(m => m !== model);
    } else if (this.selectedModels.length < 2) {
      this.selectedModels.push(model);
    } else {
      alert('You can only compare 2 models at a time');
    }
  }

  compareModels() {
    if (this.selectedModels.length !== 2) {
      alert('Please select exactly 2 models to compare');
      return;
    }

    console.log('Comparing models:', this.selectedModels);
    alert(`Comparing ${this.selectedModels[0].name} vs ${this.selectedModels[1].name}`);
  }

  clearSelection() {
    this.selectedModels = [];
  }

  deleteModel(modelName: string) {
    if (!confirm(`Are you sure you want to delete ${modelName}?`)) {
      return;
    }

    this.modelService.deleteModel(modelName).subscribe({
      next: () => {
        this.loadModels();
        alert(`Model ${modelName} deleted successfully`);
      },
      error: (err) => {
        console.error('Failed to delete model:', err);
        alert('Failed to delete model');
      }
    });
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  importModel() {
    if (!this.selectedFile) {
      alert('Please select a file');
      return;
    }

    console.log('Importing model:', this.selectedFile.name);
    this.showImportDialog = false;
    this.selectedFile = null;
    alert('Model import feature coming soon!');
  }
}
