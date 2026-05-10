import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { TrainingConfig, TrainingStatus, TrainingHistory } from '../models/training.model';

@Injectable({
  providedIn: 'root'
})
export class TrainingService {
  constructor(private api: ApiService) {}

  getStatus(): Observable<TrainingStatus> {
    return this.api.get<TrainingStatus>('training/status');
  }

  startTraining(config: TrainingConfig): Observable<any> {
    return this.api.post('training/start', config);
  }

  stopTraining(sessionId: string): Observable<any> {
    return this.api.post(`training/stop/${sessionId}`, {});
  }

  getHistory(): Observable<{ history: TrainingHistory[] }> {
    return this.api.get<{ history: TrainingHistory[] }>('training/history');
  }
}
