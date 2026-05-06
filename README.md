# 🤖 AI Virtual World — Research Project

> Dự án Python mô phỏng thế giới ảo 2D với các AI agent học sinh tồn bằng  
> **Q-Learning** (Tabular) và **Deep Q-Network** (Double DQN + Dueling + PER)

---

## 📁 Cấu Trúc Dự Án

```
d:\AI\
├── main.py               # Entry point
├── config.py             # Cấu hình toàn cục
├── requirements.txt      # Dependencies
│
├── core/
│   ├── world.py          # Môi trường thế giới 2D
│   ├── agent.py          # WorldAgent (kết nối world + AI brain)
│   └── entities.py       # Food, Hazard, Obstacle
│
├── ai/
│   ├── q_learning.py     # Tabular Q-Learning
│   ├── dqn.py            # Deep Q-Network (Double + Dueling + PER)
│   └── memory.py         # ReplayBuffer + PrioritizedReplayBuffer
│
├── visualization/
│   └── renderer.py       # Pygame real-time renderer
│
├── dashboard/
│   ├── app.py            # Flask + Socket.IO server
│   ├── templates/index.html
│   └── static/           # CSS, JS
│
└── utils/
    ├── logger.py          # JSON Lines training log
    └── stats.py           # Matplotlib charts
```

---

## 🚀 Cài Đặt

```bash
# 1. Tạo virtual environment (khuyến nghị)
python -m venv venv
venv\Scripts\activate   # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# Cài PyTorch (CPU - nếu không có GPU)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Hoặc có GPU (CUDA 12.1)
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## ▶️ Chạy Dự Án

### 🎮 Chế độ Visual (Pygame)
```bash
python main.py --mode visual --episodes 500 --agents 4
```

### 🧠 Chế độ Training (Headless - không cần màn hình)
```bash
python main.py --mode train --episodes 2000 --agents 4
```

### 📊 So sánh Q-Learning vs DQN
```bash
python main.py --mode compare --episodes 300
```

### 🌐 Web Dashboard
```bash
# Terminal 1: Chạy training
python main.py --mode train

# Terminal 2: Chạy dashboard
python main.py --mode dashboard
# Truy cập: http://localhost:5000
```

---

## 🎮 Điều Khiển Pygame

| Phím | Chức năng |
|------|-----------|
| `SPACE` | Pause / Resume |
| `S` | Bật/tắt Sensor rays |
| `T` | Bật/tắt Trails |
| `↑` / `↓` | Tăng/giảm tốc độ |
| `R` | Reset world |
| `Q` / `ESC` | Thoát |

---

## 🧠 Kiến Trúc AI

### Q-Learning (Tabular)
- **State**: Rời rạc hoá (5 mức) → hashable tuple → Q-Table dict
- **Update**: `Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]`
- **Exploration**: ε-greedy với decay

### DQN (Deep Q-Network)
```
Input (27) → FC(128) → LayerNorm → ReLU
           → FC(128) → LayerNorm → ReLU  
           → FC(128) → LayerNorm → ReLU
           → [Value(1) + Advantage(9)] → Q(9)
```
- **Double DQN**: Policy net chọn action, Target net đánh giá
- **Dueling Network**: Value stream + Advantage stream
- **PER**: Prioritized Experience Replay với SumTree
- **Target Network**: Soft update (τ=0.005) mỗi step

### State Space (27 chiều)
```
[dir0_food, dir0_hazard, dir0_obstacle,   # hướng 0 (↖)
 dir1_food, dir1_hazard, dir1_obstacle,   # hướng 1 (↑)
 ...                                       # 8 hướng × 3 = 24
 energy_norm, pos_x_norm, pos_y_norm]     # + 3 = 27 tổng
```

### Reward System
| Sự kiện | Reward |
|---------|--------|
| Ăn thức ăn | +10.0 |
| Chạm hazard | -5.0 |
| Chết (energy = 0) | -20.0 |
| Mỗi bước | -0.1 |
| Sống đến cuối episode | +50.0 |
| Đâm vào tường | -1.0 (extra) |

---

## 📊 Output Files

```
logs/
  training_YYYYMMDD_HHMMSS.jsonl   # Log từng episode
  training_stats.png                # Charts cuối training
  comparison.png                    # So sánh QL vs DQN

models/
  dqn_agentN_epX.pt                 # DQN checkpoint
  ql_agentN_epX.npy                 # Q-Table checkpoint
```

---

## ⚙️ Cấu Hình (config.py)

```python
WORLD.width  = 30     # Kích thước world
WORLD.num_food = 40   # Số lượng food

DQN_CFG.lr   = 1e-3   # Learning rate
DQN_CFG.use_double_dqn = True

AGENT.num_agents = 4  # Số agents
TRAIN.num_episodes = 2000
```

---

## 🔬 Nghiên Cứu & Mở Rộng

- [ ] Multi-agent cooperative learning (agents chia sẻ memory)
- [ ] Curriculum learning (độ khó tăng dần)
- [ ] Genetic Algorithm agents (tiến hóa neural network)
- [ ] LSTM-based agents (nhớ lịch sử dài hơn)
- [ ] A3C / PPO (thuật toán policy gradient)
