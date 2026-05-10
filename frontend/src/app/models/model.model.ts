export interface Model {
  name: string;
  algorithm: string;
  agent_id: string;
  episodes: string;
  size: number;
  created_at: string;
  performance: {
    accuracy: number;
    reward: number;
  };
}

export interface Algorithm {
  id: string;
  name: string;
  description: string;
  type: string;
  complexity: string;
}

export interface Statistics {
  total_models: number;
  total_training_sessions: number;
  active_sessions: number;
  algorithms: string[];
  last_updated: string;
}

export interface PerformanceStats {
  episodes: number[];
  rewards: number[];
  losses: number[];
  avg_reward: number;
  max_reward: number;
  min_reward: number;
}
