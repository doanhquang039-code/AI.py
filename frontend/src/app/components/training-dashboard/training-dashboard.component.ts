import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface TrainingMetrics {
  episode: number;
  reward: number;
  loss: number;
  epsilon: number;
  steps: number;
  timestamp: number;
}

interface ModelInfo {
  name: string;
  algorithm: string;
  status: 'training' | 'paused' | 'completed';
  progress: number;
  currentEpisode: number;
  totalEpisodes: number;
  bestReward: number;
  avgReward: number;
}

@Component({
  selector: 'app-training-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './training-dashboard.component.html',
  styleUrls: ['./training-dashboard.component.css']
})
export class TrainingDashboardComponent implements OnInit, OnDestroy {
  models: ModelInfo[] = [];
  selectedModel: ModelInfo | null = null;
  trainingMetrics: TrainingMetrics[] = [];
  
  // Charts
  rewardChart: Chart | null = null;
  lossChart: Chart | null = null;
  epsilonChart: Chart | null = null;
  
  // Real-time updates
  private updateInterval: any;
  isLiveMode = true;
  
  // Training controls
  trainingConfig = {
    algorithm: 'DQN',
    episodes: 1000,
    learningRate: 0.001,
    batchSize: 32,
    gamma: 0.99
  };

  ngOnInit() {
    this.loadModels();
    this.initializeCharts();
    
    if (this.isLiveMode) {
      this.startLiveUpdates();
    }
  }

  ngOnDestroy() {
    this.stopLiveUpdates();
    this.destroyCharts();
  }

  loadModels() {
    // Mock data - replace with actual API call
    this.models = [
      {
        name: 'DQN_Agent_v1',
        algorithm: 'DQN',
        status: 'training',
        progress: 65,
        currentEpisode: 650,
        totalEpisodes: 1000,
        bestReward: 245.5,
        avgReward: 180.3
      },
      {
        name: 'PPO_Agent_v2',
        algorithm: 'PPO',
        status: 'completed',
        progress: 100,
        currentEpisode: 1000,
        totalEpisodes: 1000,
        bestReward: 312.8,
        avgReward: 265.4
      },
      {
        name: 'QLearning_Agent',
        algorithm: 'Q-Learning',
        status: 'paused',
        progress: 42,
        currentEpisode: 420,
        totalEpisodes: 1000,
        bestReward: 156.2,
        avgReward: 98.7
      }
    ];
    
    if (this.models.length > 0) {
      this.selectModel(this.models[0]);
    }
  }

  selectModel(model: ModelInfo) {
    this.selectedModel = model;
    this.loadTrainingMetrics(model.name);
    this.updateCharts();
  }

  loadTrainingMetrics(modelName: string) {
    // Mock data - replace with actual API call
    this.trainingMetrics = [];
    const numPoints = 100;
    
    for (let i = 0; i < numPoints; i++) {
      this.trainingMetrics.push({
        episode: i * 10,
        reward: 50 + Math.random() * 200 + i * 2,
        loss: 1.0 - (i / numPoints) * 0.8 + Math.random() * 0.2,
        epsilon: 1.0 - (i / numPoints) * 0.9,
        steps: 100 + Math.floor(Math.random() * 50),
        timestamp: Date.now() - (numPoints - i) * 60000
      });
    }
  }

  initializeCharts() {
    // Reward Chart
    const rewardCtx = document.getElementById('rewardChart') as HTMLCanvasElement;
    if (rewardCtx) {
      this.rewardChart = new Chart(rewardCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Reward',
            data: [],
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true },
            title: { display: true, text: 'Training Reward Over Time' }
          },
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }

    // Loss Chart
    const lossCtx = document.getElementById('lossChart') as HTMLCanvasElement;
    if (lossCtx) {
      this.lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Loss',
            data: [],
            borderColor: '#F44336',
            backgroundColor: 'rgba(244, 67, 54, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true },
            title: { display: true, text: 'Training Loss' }
          },
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }

    // Epsilon Chart
    const epsilonCtx = document.getElementById('epsilonChart') as HTMLCanvasElement;
    if (epsilonCtx) {
      this.epsilonChart = new Chart(epsilonCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Epsilon',
            data: [],
            borderColor: '#2196F3',
            backgroundColor: 'rgba(33, 150, 243, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true },
            title: { display: true, text: 'Exploration Rate (Epsilon)' }
          },
          scales: {
            y: { beginAtZero: true, max: 1 }
          }
        }
      });
    }
  }

  updateCharts() {
    if (!this.trainingMetrics.length) return;

    const episodes = this.trainingMetrics.map(m => m.episode);
    const rewards = this.trainingMetrics.map(m => m.reward);
    const losses = this.trainingMetrics.map(m => m.loss);
    const epsilons = this.trainingMetrics.map(m => m.epsilon);

    if (this.rewardChart) {
      this.rewardChart.data.labels = episodes;
      this.rewardChart.data.datasets[0].data = rewards;
      this.rewardChart.update();
    }

    if (this.lossChart) {
      this.lossChart.data.labels = episodes;
      this.lossChart.data.datasets[0].data = losses;
      this.lossChart.update();
    }

    if (this.epsilonChart) {
      this.epsilonChart.data.labels = episodes;
      this.epsilonChart.data.datasets[0].data = epsilons;
      this.epsilonChart.update();
    }
  }

  destroyCharts() {
    if (this.rewardChart) this.rewardChart.destroy();
    if (this.lossChart) this.lossChart.destroy();
    if (this.epsilonChart) this.epsilonChart.destroy();
  }

  startLiveUpdates() {
    this.updateInterval = setInterval(() => {
      if (this.selectedModel && this.selectedModel.status === 'training') {
        this.simulateNewMetric();
      }
    }, 2000);
  }

  stopLiveUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }

  simulateNewMetric() {
    const lastMetric = this.trainingMetrics[this.trainingMetrics.length - 1];
    const newMetric: TrainingMetrics = {
      episode: lastMetric.episode + 10,
      reward: lastMetric.reward + (Math.random() - 0.5) * 20,
      loss: Math.max(0.01, lastMetric.loss - 0.01 + Math.random() * 0.02),
      epsilon: Math.max(0.01, lastMetric.epsilon - 0.01),
      steps: 100 + Math.floor(Math.random() * 50),
      timestamp: Date.now()
    };

    this.trainingMetrics.push(newMetric);
    if (this.trainingMetrics.length > 100) {
      this.trainingMetrics.shift();
    }

    this.updateCharts();
  }

  startTraining() {
    if (this.selectedModel) {
      this.selectedModel.status = 'training';
      console.log('Starting training with config:', this.trainingConfig);
      // API call to start training
    }
  }

  pauseTraining() {
    if (this.selectedModel) {
      this.selectedModel.status = 'paused';
      console.log('Pausing training');
      // API call to pause training
    }
  }

  stopTraining() {
    if (this.selectedModel) {
      this.selectedModel.status = 'completed';
      console.log('Stopping training');
      // API call to stop training
    }
  }

  exportMetrics() {
    const dataStr = JSON.stringify(this.trainingMetrics, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `training_metrics_${this.selectedModel?.name}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'training': return '#4CAF50';
      case 'paused': return '#FF9800';
      case 'completed': return '#2196F3';
      default: return '#9E9E9E';
    }
  }
}
