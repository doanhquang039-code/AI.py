import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  TrainingConfig,
  TrainingStatus,
  TrainingHistory,
  TuningConfig,
  TuningSession,
  TuningStartResponse
} from '../models/training.model';

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

  startTuning(config: TuningConfig): Observable<TuningStartResponse> {
    return this.api.post<TuningStartResponse>('tuning/start', config);
  }

  getTuningSessions(): Observable<{ sessions: TuningSession[] }> {
    return this.api.get<{ sessions: TuningSession[] }>('tuning');
  }

  getTuningSession(tuningId: string): Observable<TuningSession> {
    return this.api.get<TuningSession>(`tuning/${tuningId}`);
  }
}
