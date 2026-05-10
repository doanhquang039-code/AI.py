import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModelService } from '../../services/model.service';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';

interface ModelComparison {
  name: string;
  algorithm: string;
  episodes: number;
  avgReward: number;
  maxReward: number;
  avgLoss: number;
  trainingTime: number;
  memoryUsage: number;
}

@Component({
  selector: 'app-comparison',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective],
  templateUrl: './comparison.component.html',
  styleUrls: ['./comparison.component.scss']
})
export class ComparisonComponent implements OnInit {
  availableModels: any[] = [];
  selectedModels: string[] = [];
  comparisonData: ModelComparison[] = [];
  isLoading = false;

  // Chart configurations
  rewardChartData: ChartConfiguration['data'] = {
    labels: [],
    datasets: []
  };

  rewardChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#fff'
        }
      },
      title: {
        display: true,
        text: 'Reward Comparison',
        color: '#fff',
        font: {
          size: 16
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  };

  lossChartData: ChartConfiguration['data'] = {
    labels: [],
    datasets: []
  };

  lossChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#fff'
        }
      },
      title: {
        display: true,
        text: 'Loss Comparison',
        color: '#fff',
        font: {
          size: 16
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  };

  performanceChartData: ChartConfiguration['data'] = {
    labels: [],
    datasets: [{
      label: 'Average Reward',
      data: [],
      backgroundColor: 'rgba(76, 175, 80, 0.6)',
      borderColor: 'rgba(76, 175, 80, 1)',
      borderWidth: 2
    }]
  };

  performanceChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Performance Overview',
        color: '#fff',
        font: {
          size: 16
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      }
    }
  };

  constructor(private modelService: ModelService) {}

  ngOnInit(): void {
    this.loadAvailableModels();
  }

  async loadAvailableModels(): Promise<void> {
    this.isLoading = true;
    try {
      const response = await this.modelService.getModels().toPromise();
      this.availableModels = response.models || [];
    } catch (error) {
      console.error('Error loading models:', error);
    } finally {
      this.isLoading = false;
    }
  }

  toggleModelSelection(modelName: string): void {
    const index = this.selectedModels.indexOf(modelName);
    if (index > -1) {
      this.selectedModels.splice(index, 1);
    } else {
      if (this.selectedModels.length < 5) {
        this.selectedModels.push(modelName);
      }
    }
  }

  isModelSelected(modelName: string): boolean {
    return this.selectedModels.includes(modelName);
  }

  async compareModels(): Promise<void> {
    if (this.selectedModels.length < 2) {
      alert('Please select at least 2 models to compare');
      return;
    }

    this.isLoading = true;
    try {
      // Simulate loading comparison data
      this.comparisonData = this.selectedModels.map(modelName => {
        const model = this.availableModels.find(m => m.name === modelName);
        return {
          name: modelName,
          algorithm: model?.algorithm || 'Unknown',
          episodes: parseInt(model?.episodes || '0'),
          avgReward: Math.random() * 100,
          maxReward: Math.random() * 150,
          avgLoss: Math.random() * 2,
          trainingTime: Math.random() * 3600,
          memoryUsage: Math.random() * 1024
        };
      });

      this.updateCharts();
    } catch (error) {
      console.error('Error comparing models:', error);
    } finally {
      this.isLoading = false;
    }
  }

  private updateCharts(): void {
    // Update reward chart
    const episodes = Array.from({ length: 50 }, (_, i) => i + 1);
    this.rewardChartData = {
      labels: episodes.map(e => e.toString()),
      datasets: this.comparisonData.map((model, index) => ({
        label: model.name,
        data: episodes.map(e => Math.random() * 100 + e * 0.5),
        borderColor: this.getColor(index),
        backgroundColor: this.getColor(index, 0.1),
        fill: false,
        tension: 0.4
      }))
    };

    // Update loss chart
    this.lossChartData = {
      labels: episodes.map(e => e.toString()),
      datasets: this.comparisonData.map((model, index) => ({
        label: model.name,
        data: episodes.map(e => Math.max(0.1, 2 - e * 0.03 + Math.random() * 0.2)),
        borderColor: this.getColor(index),
        backgroundColor: this.getColor(index, 0.1),
        fill: false,
        tension: 0.4
      }))
    };

    // Update performance chart
    this.performanceChartData = {
      labels: this.comparisonData.map(m => m.name),
      datasets: [{
        label: 'Average Reward',
        data: this.comparisonData.map(m => m.avgReward),
        backgroundColor: this.comparisonData.map((_, i) => this.getColor(i, 0.6)),
        borderColor: this.comparisonData.map((_, i) => this.getColor(i)),
        borderWidth: 2
      }]
    };
  }

  private getColor(index: number, alpha: number = 1): string {
    const colors = [
      `rgba(33, 150, 243, ${alpha})`,   // Blue
      `rgba(76, 175, 80, ${alpha})`,    // Green
      `rgba(255, 193, 7, ${alpha})`,    // Yellow
      `rgba(156, 39, 176, ${alpha})`,   // Purple
      `rgba(255, 87, 34, ${alpha})`     // Orange
    ];
    return colors[index % colors.length];
  }

  clearSelection(): void {
    this.selectedModels = [];
    this.comparisonData = [];
  }

  exportComparison(): void {
    const data = {
      timestamp: new Date().toISOString(),
      models: this.comparisonData
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model-comparison-${Date.now()}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  formatTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  }

  formatMemory(mb: number): string {
    if (mb < 1024) {
      return `${mb.toFixed(2)} MB`;
    }
    return `${(mb / 1024).toFixed(2)} GB`;
  }
}
