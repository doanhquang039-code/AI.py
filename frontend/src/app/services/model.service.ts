import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { Model, Algorithm, Statistics, PerformanceStats } from '../models/model.model';

@Injectable({
  providedIn: 'root'
})
export class ModelService {
  constructor(private api: ApiService) {}

  getModels(): Observable<{ models: Model[] }> {
    return this.api.get<{ models: Model[] }>('models');
  }

  deleteModel(modelName: string): Observable<any> {
    return this.api.delete(`models/${modelName}`);
  }

  getExportUrl(modelName: string): string {
    return `${this.api.getBaseUrl()}/models/export/${encodeURIComponent(modelName)}`;
  }

  importModel(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.api.postForm('models/import', formData);
  }

  evaluateModel(modelName: string): Observable<any> {
    return this.api.post(`models/evaluate/${encodeURIComponent(modelName)}`, {});
  }

  compareModels(model1: string, model2: string): Observable<any> {
    return this.api.post('models/compare', { model1, model2 });
  }

  getAlgorithms(): Observable<{ algorithms: Algorithm[] }> {
    return this.api.get<{ algorithms: Algorithm[] }>('algorithms');
  }

  getStatistics(): Observable<Statistics> {
    return this.api.get<Statistics>('stats/summary');
  }

  getPerformanceStats(): Observable<PerformanceStats> {
    return this.api.get<PerformanceStats>('stats/performance');
  }
}
