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
