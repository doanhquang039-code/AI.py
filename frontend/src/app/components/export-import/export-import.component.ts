import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModelService } from '../../services/model.service';

interface ExportConfig {
  includeModels: boolean;
  includeTrainingLogs: boolean;
  includeConfigs: boolean;
  format: 'json' | 'zip';
}

@Component({
  selector: 'app-export-import',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './export-import.component.html',
  styleUrls: ['./export-import.component.scss']
})
export class ExportImportComponent {
  exportConfig: ExportConfig = {
    includeModels: true,
    includeTrainingLogs: true,
    includeConfigs: true,
    format: 'json'
  };

  importedFiles: File[] = [];
  isExporting = false;
  isImporting = false;
  exportProgress = 0;
  importProgress = 0;
  exportHistory: any[] = [];
  importHistory: any[] = [];

  constructor(private modelService: ModelService) {
    this.loadHistory();
  }

  loadHistory(): void {
    // Load from localStorage
    const exportHistoryStr = localStorage.getItem('exportHistory');
    const importHistoryStr = localStorage.getItem('importHistory');
    
    if (exportHistoryStr) {
      this.exportHistory = JSON.parse(exportHistoryStr);
    }
    
    if (importHistoryStr) {
      this.importHistory = JSON.parse(importHistoryStr);
    }
  }

  async exportData(): Promise<void> {
    this.isExporting = true;
    this.exportProgress = 0;

    try {
      // Simulate export process
      const data: any = {
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      };

      // Export models
      if (this.exportConfig.includeModels) {
        this.exportProgress = 30;
        const models = await this.modelService.getModels().toPromise();
        data.models = models.models;
      }

      // Export training logs
      if (this.exportConfig.includeTrainingLogs) {
        this.exportProgress = 60;
        // Simulate loading logs
        data.trainingLogs = [];
      }

      // Export configs
      if (this.exportConfig.includeConfigs) {
        this.exportProgress = 90;
        data.configs = {
          worldSize: 30,
          numAgents: 4,
          learningRate: 0.001
        };
      }

      this.exportProgress = 100;

      // Create and download file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-export-${Date.now()}.json`;
      a.click();
      window.URL.revokeObjectURL(url);

      // Add to history
      const exportRecord = {
        timestamp: new Date().toISOString(),
        filename: a.download,
        size: blob.size,
        config: { ...this.exportConfig }
      };
      this.exportHistory.unshift(exportRecord);
      localStorage.setItem('exportHistory', JSON.stringify(this.exportHistory.slice(0, 10)));

      alert('Export completed successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      this.isExporting = false;
      this.exportProgress = 0;
    }
  }

  onFileSelected(event: any): void {
    const files = event.target.files;
    if (files && files.length > 0) {
      this.importedFiles = Array.from(files);
    }
  }

  async importData(): Promise<void> {
    if (this.importedFiles.length === 0) {
      alert('Please select files to import');
      return;
    }

    this.isImporting = true;
    this.importProgress = 0;

    try {
      for (let i = 0; i < this.importedFiles.length; i++) {
        const file = this.importedFiles[i];
        this.importProgress = ((i + 1) / this.importedFiles.length) * 100;

        const content = await this.readFileContent(file);
        const data = JSON.parse(content);

        // Process imported data
        console.log('Imported data:', data);

        // Add to history
        const importRecord = {
          timestamp: new Date().toISOString(),
          filename: file.name,
          size: file.size,
          itemsImported: {
            models: data.models?.length || 0,
            logs: data.trainingLogs?.length || 0,
            configs: data.configs ? 1 : 0
          }
        };
        this.importHistory.unshift(importRecord);
      }

      localStorage.setItem('importHistory', JSON.stringify(this.importHistory.slice(0, 10)));

      alert('Import completed successfully!');
      this.importedFiles = [];
    } catch (error) {
      console.error('Import error:', error);
      alert('Import failed. Please check the file format.');
    } finally {
      this.isImporting = false;
      this.importProgress = 0;
    }
  }

  private readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = (e) => reject(e);
      reader.readAsText(file);
    });
  }

  removeImportedFile(index: number): void {
    this.importedFiles.splice(index, 1);
  }

  clearExportHistory(): void {
    if (confirm('Are you sure you want to clear export history?')) {
      this.exportHistory = [];
      localStorage.removeItem('exportHistory');
    }
  }

  clearImportHistory(): void {
    if (confirm('Are you sure you want to clear import history?')) {
      this.importHistory = [];
      localStorage.removeItem('importHistory');
    }
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleString();
  }

  downloadTemplate(): void {
    const template = {
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      models: [
        {
          name: 'example_model.pt',
          algorithm: 'DQN',
          episodes: 100,
          performance: {
            avgReward: 75.5,
            maxReward: 120.0
          }
        }
      ],
      trainingLogs: [],
      configs: {
        worldSize: 30,
        numAgents: 4,
        learningRate: 0.001,
        gamma: 0.99,
        epsilon: 0.1
      }
    };

    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'import-template.json';
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
