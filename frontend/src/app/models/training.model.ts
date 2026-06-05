export interface TrainingConfig {
  algorithm: string;
  episodes: number;
  learning_rate: number;
  gamma: number;
  epsilon?: number;
}

export interface TrainingStatus {
  status: string;
  current_episode: number;
  total_episodes: number;
  progress: number;
  metrics: {
    reward: number;
    loss: number;
    epsilon: number;
  };
}

export interface TrainingSession {
  id: string;
  config: TrainingConfig;
  status: string;
  started_at: string;
  stopped_at?: string;
  current_episode: number;
  total_episodes: number;
}

export interface TrainingHistory {
  filename: string;
  episodes: number;
  last_episode: any;
  created_at: string;
}

export interface TuningConfig {
  algorithm: string;
  method: string;
  trials: number;
  episodes: number;
}

export interface TuningTrial {
  trial_id: number;
  parameters: Record<string, string | number>;
  score: number;
  training_time: number;
  additional_metrics: Record<string, number>;
  timestamp: number;
}

export interface TuningSession {
  id: string;
  algorithm: string;
  method: string;
  status: string;
  started_at: string;
  duration_seconds: number;
  trials_requested: number;
  trials_completed: number;
  best_trial: TuningTrial;
  history: TuningTrial[];
}

export interface TuningStartResponse {
  tuning_id: string;
  message: string;
  algorithm: string;
  best_trial: TuningTrial;
  trials_completed: number;
}
