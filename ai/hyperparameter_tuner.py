"""
Hyperparameter Auto-Tuning System
Tự động tối ưu hyperparameters cho các thuật toán AI
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Any
import json
from dataclasses import dataclass, asdict
from enum import Enum
import time


class OptimizationMethod(Enum):
    """Phương pháp tối ưu"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"


@dataclass
class HyperparameterSpace:
    """Không gian hyperparameter"""
    name: str
    param_type: str  # "continuous", "discrete", "categorical"
    min_value: Any = None
    max_value: Any = None
    values: List[Any] = None
    log_scale: bool = False


@dataclass
class TrialResult:
    """Kết quả của một trial"""
    trial_id: int
    parameters: Dict
    score: float
    training_time: float
    additional_metrics: Dict
    timestamp: float


class HyperparameterTuner:
    """Tự động tune hyperparameters"""
    
    def __init__(self, 
                 parameter_space: List[HyperparameterSpace],
                 optimization_method: OptimizationMethod = OptimizationMethod.RANDOM_SEARCH,
                 n_trials: int = 50,
                 random_seed: int = 42):
        self.parameter_space = parameter_space
        self.optimization_method = optimization_method
        self.n_trials = n_trials
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
        
        self.trials: List[TrialResult] = []
        self.best_trial: Optional[TrialResult] = None
        self.current_trial = 0
    
    def sample_parameters(self) -> Dict:
        """Sample parameters từ space"""
        if self.optimization_method == OptimizationMethod.RANDOM_SEARCH:
            return self._random_sample()
        elif self.optimization_method == OptimizationMethod.GRID_SEARCH:
            return self._grid_sample()
        elif self.optimization_method == OptimizationMethod.BAYESIAN:
            return self._bayesian_sample()
        elif self.optimization_method == OptimizationMethod.GENETIC:
            return self._genetic_sample()
        else:
            return self._random_sample()
    
    def _random_sample(self) -> Dict:
        """Random sampling"""
        params = {}
        
        for space in self.parameter_space:
            if space.param_type == "continuous":
                if space.log_scale:
                    value = np.exp(np.random.uniform(
                        np.log(space.min_value), 
                        np.log(space.max_value)
                    ))
                else:
                    value = np.random.uniform(space.min_value, space.max_value)
                params[space.name] = float(value)
                
            elif space.param_type == "discrete":
                value = np.random.randint(space.min_value, space.max_value + 1)
                params[space.name] = int(value)
                
            elif space.param_type == "categorical":
                value = np.random.choice(space.values)
                params[space.name] = value
        
        return params
    
    def _grid_sample(self) -> Dict:
        """Grid search sampling"""
        # Simplified grid search
        if self.current_trial >= self.n_trials:
            return self._random_sample()
        
        # Generate grid points
        grid_size = int(np.ceil(self.n_trials ** (1.0 / len(self.parameter_space))))
        
        params = {}
        trial_idx = self.current_trial
        
        for space in self.parameter_space:
            if space.param_type == "continuous":
                grid_points = np.linspace(space.min_value, space.max_value, grid_size)
                idx = trial_idx % grid_size
                params[space.name] = float(grid_points[idx])
                trial_idx //= grid_size
                
            elif space.param_type == "discrete":
                grid_points = np.linspace(space.min_value, space.max_value, grid_size, dtype=int)
                idx = trial_idx % grid_size
                params[space.name] = int(grid_points[idx])
                trial_idx //= grid_size
                
            elif space.param_type == "categorical":
                idx = trial_idx % len(space.values)
                params[space.name] = space.values[idx]
                trial_idx //= len(space.values)
        
        return params
    
    def _bayesian_sample(self) -> Dict:
        """Bayesian optimization sampling (simplified)"""
        if len(self.trials) < 5:
            # Random exploration phase
            return self._random_sample()
        
        # Exploitation phase - sample around best parameters
        best_params = self.best_trial.parameters
        params = {}
        
        for space in self.parameter_space:
            if space.param_type == "continuous":
                # Add Gaussian noise around best value
                best_value = best_params[space.name]
                noise_scale = (space.max_value - space.min_value) * 0.1
                value = np.random.normal(best_value, noise_scale)
                value = np.clip(value, space.min_value, space.max_value)
                params[space.name] = float(value)
                
            elif space.param_type == "discrete":
                best_value = best_params[space.name]
                noise = np.random.randint(-2, 3)
                value = best_value + noise
                value = np.clip(value, space.min_value, space.max_value)
                params[space.name] = int(value)
                
            elif space.param_type == "categorical":
                # 80% keep best, 20% explore
                if np.random.random() < 0.8:
                    params[space.name] = best_params[space.name]
                else:
                    params[space.name] = np.random.choice(space.values)
        
        return params
    
    def _genetic_sample(self) -> Dict:
        """Genetic algorithm sampling"""
        if len(self.trials) < 10:
            return self._random_sample()
        
        # Select top 20% as parents
        sorted_trials = sorted(self.trials, key=lambda t: t.score, reverse=True)
        n_parents = max(2, len(sorted_trials) // 5)
        parents = sorted_trials[:n_parents]
        
        # Crossover
        parent1 = np.random.choice(parents)
        parent2 = np.random.choice(parents)
        
        params = {}
        for space in self.parameter_space:
            # 50% from each parent
            if np.random.random() < 0.5:
                value = parent1.parameters[space.name]
            else:
                value = parent2.parameters[space.name]
            
            # Mutation (10% chance)
            if np.random.random() < 0.1:
                if space.param_type == "continuous":
                    noise_scale = (space.max_value - space.min_value) * 0.2
                    value += np.random.normal(0, noise_scale)
                    value = np.clip(value, space.min_value, space.max_value)
                elif space.param_type == "discrete":
                    value += np.random.randint(-2, 3)
                    value = np.clip(value, space.min_value, space.max_value)
                elif space.param_type == "categorical":
                    value = np.random.choice(space.values)
            
            params[space.name] = value
        
        return params
    
    def record_trial(self, parameters: Dict, score: float, 
                    training_time: float, additional_metrics: Dict = None):
        """Ghi lại kết quả trial"""
        trial = TrialResult(
            trial_id=self.current_trial,
            parameters=parameters,
            score=score,
            training_time=training_time,
            additional_metrics=additional_metrics or {},
            timestamp=time.time()
        )
        
        self.trials.append(trial)
        
        # Update best trial
        if self.best_trial is None or score > self.best_trial.score:
            self.best_trial = trial
        
        self.current_trial += 1
    
    def optimize(self, objective_function: Callable[[Dict], Tuple[float, float, Dict]]) -> Dict:
        """
        Chạy optimization
        
        Args:
            objective_function: Function nhận parameters và trả về (score, time, metrics)
        
        Returns:
            Best parameters found
        """
        print(f"🔧 Starting hyperparameter optimization")
        print(f"   Method: {self.optimization_method.value}")
        print(f"   Trials: {self.n_trials}")
        print(f"   Parameters: {[s.name for s in self.parameter_space]}")
        
        for trial in range(self.n_trials):
            # Sample parameters
            params = self.sample_parameters()
            
            # Evaluate
            try:
                score, training_time, metrics = objective_function(params)
                self.record_trial(params, score, training_time, metrics)
                
                print(f"\n  Trial {trial + 1}/{self.n_trials}")
                print(f"    Score: {score:.4f}")
                print(f"    Time: {training_time:.2f}s")
                if self.best_trial and trial > 0:
                    print(f"    Best so far: {self.best_trial.score:.4f}")
                    
            except Exception as e:
                print(f"  Trial {trial + 1} failed: {e}")
                continue
        
        print(f"\n✅ Optimization complete!")
        print(f"   Best score: {self.best_trial.score:.4f}")
        print(f"   Best parameters: {self.best_trial.parameters}")
        
        return self.best_trial.parameters
    
    def get_optimization_history(self) -> List[Dict]:
        """Lấy lịch sử optimization"""
        return [asdict(trial) for trial in self.trials]
    
    def plot_optimization_history(self, save_path: str = None):
        """Vẽ biểu đồ optimization history"""
        try:
            import matplotlib.pyplot as plt
            
            scores = [trial.score for trial in self.trials]
            best_scores = []
            current_best = -float('inf')
            
            for score in scores:
                current_best = max(current_best, score)
                best_scores.append(current_best)
            
            plt.figure(figsize=(12, 5))
            
            # Plot 1: All scores
            plt.subplot(1, 2, 1)
            plt.plot(scores, 'o-', alpha=0.6, label='Trial scores')
            plt.plot(best_scores, 'r-', linewidth=2, label='Best score')
            plt.xlabel('Trial')
            plt.ylabel('Score')
            plt.title('Optimization Progress')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot 2: Parameter evolution (first parameter)
            if self.parameter_space:
                plt.subplot(1, 2, 2)
                param_name = self.parameter_space[0].name
                param_values = [trial.parameters[param_name] for trial in self.trials]
                plt.scatter(param_values, scores, alpha=0.6)
                plt.xlabel(param_name)
                plt.ylabel('Score')
                plt.title(f'{param_name} vs Score')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                print(f"📊 Plot saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("⚠️  matplotlib not available for plotting")
    
    def save_results(self, filepath: str):
        """Lưu kết quả optimization"""
        results = {
            "optimization_method": self.optimization_method.value,
            "n_trials": self.n_trials,
            "parameter_space": [asdict(space) for space in self.parameter_space],
            "best_trial": asdict(self.best_trial) if self.best_trial else None,
            "all_trials": self.get_optimization_history()
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to {filepath}")


class PresetTuners:
    """Preset tuners cho các thuật toán phổ biến"""
    
    @staticmethod
    def q_learning_tuner(n_trials: int = 30) -> HyperparameterTuner:
        """Tuner cho Q-Learning"""
        space = [
            HyperparameterSpace("learning_rate", "continuous", 0.001, 0.5, log_scale=True),
            HyperparameterSpace("discount_factor", "continuous", 0.9, 0.999),
            HyperparameterSpace("epsilon_start", "continuous", 0.5, 1.0),
            HyperparameterSpace("epsilon_decay", "continuous", 0.99, 0.9999),
        ]
        return HyperparameterTuner(space, OptimizationMethod.BAYESIAN, n_trials)
    
    @staticmethod
    def dqn_tuner(n_trials: int = 30) -> HyperparameterTuner:
        """Tuner cho DQN"""
        space = [
            HyperparameterSpace("learning_rate", "continuous", 0.0001, 0.01, log_scale=True),
            HyperparameterSpace("batch_size", "discrete", 16, 128),
            HyperparameterSpace("buffer_size", "discrete", 1000, 100000),
            HyperparameterSpace("target_update_freq", "discrete", 10, 1000),
            HyperparameterSpace("hidden_size", "categorical", values=[64, 128, 256, 512]),
        ]
        return HyperparameterTuner(space, OptimizationMethod.BAYESIAN, n_trials)
    
    @staticmethod
    def ppo_tuner(n_trials: int = 30) -> HyperparameterTuner:
        """Tuner cho PPO"""
        space = [
            HyperparameterSpace("learning_rate", "continuous", 0.0001, 0.01, log_scale=True),
            HyperparameterSpace("clip_epsilon", "continuous", 0.1, 0.3),
            HyperparameterSpace("value_coef", "continuous", 0.1, 1.0),
            HyperparameterSpace("entropy_coef", "continuous", 0.001, 0.1, log_scale=True),
            HyperparameterSpace("n_steps", "discrete", 128, 2048),
        ]
        return HyperparameterTuner(space, OptimizationMethod.GENETIC, n_trials)


if __name__ == "__main__":
    print("🔧 Testing Hyperparameter Tuner")
    
    # Create tuner for Q-Learning
    tuner = PresetTuners.q_learning_tuner(n_trials=20)
    
    # Mock objective function
    def mock_objective(params):
        # Simulate training
        score = (
            params["learning_rate"] * 0.5 +
            params["discount_factor"] * 0.3 +
            (1 - params["epsilon_start"]) * 0.2 +
            np.random.normal(0, 0.05)
        )
        training_time = np.random.uniform(1, 5)
        metrics = {"episodes": 100, "avg_reward": score * 100}
        return score, training_time, metrics
    
    # Run optimization
    best_params = tuner.optimize(mock_objective)
    
    print(f"\n📊 Optimization Summary:")
    print(f"   Trials completed: {len(tuner.trials)}")
    print(f"   Best score: {tuner.best_trial.score:.4f}")
    print(f"   Best parameters:")
    for key, value in best_params.items():
        print(f"     {key}: {value:.4f}" if isinstance(value, float) else f"     {key}: {value}")
    
    # Save results
    tuner.save_results("tuning_results.json")
    
    print("\n✅ Hyperparameter tuning test complete!")
