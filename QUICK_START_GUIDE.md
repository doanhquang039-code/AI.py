# 🚀 Quick Start Guide - AI Virtual World

## ⚡ Khởi Động Nhanh (5 phút)

### Bước 1: Cài Đặt Dependencies

#### Backend (Python)
```bash
cd AI
pip install -r requirements.txt
```

#### Frontend (Angular)
```bash
cd AI/frontend
npm install
```

---

### Bước 2: Chạy Application

#### Terminal 1 - Backend API
```bash
cd AI
python -m uvicorn api.main:app --reload --port 8000
```

Hoặc dùng file batch (Windows):
```bash
cd AI
run.bat
```

#### Terminal 2 - Frontend
```bash
cd AI/frontend
npm start
```

---

### Bước 3: Truy Cập

- **Frontend Dashboard:** http://localhost:4200
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/api/health

---

## 🎮 Hướng Dẫn Sử Dụng Từng Feature

### 1. Dashboard (Trang Chủ)
**URL:** http://localhost:4200/dashboard

**Chức năng:**
- Xem tổng quan hệ thống
- Số lượng models đã train
- Training sessions history
- Quick stats

**Actions:**
- Click vào cards để xem chi tiết
- Navigate to other features

---

### 2. Training Control
**URL:** http://localhost:4200/training

**Chức năng:**
- Start/Stop training sessions
- Configure training parameters:
  - Algorithm (DQN, Q-Learning, SARSA, PPO, A2C)
  - Episodes
  - Learning rate
  - Gamma (discount factor)
  - Epsilon (exploration rate)

**Workflow:**
1. Select algorithm
2. Set parameters
3. Click "Start Training"
4. Monitor progress
5. Stop when satisfied

---

### 3. 🎮 Real-time Visualization (MỚI!)
**URL:** http://localhost:4200/visualization

**Chức năng:**
- Xem agents training LIVE
- Canvas-based 2D world
- Real-time metrics

**Controls:**
- **⏸️ Pause/Resume:** Tạm dừng/tiếp tục animation
- **📡 Sensors:** Bật/tắt sensor rays (8 hướng)
- **🎨 Trails:** Bật/tắt đường đi của agents
- **🧹 Clear Trails:** Xóa tất cả trails
- **🔄 Reset View:** Reset về trạng thái ban đầu

**Legend:**
- 🟢 **Green Circle:** Food (+10 reward)
- 🔺 **Red Triangle:** Hazard (-5 reward)
- ⬛ **Gray Square:** Obstacle
- 🔵 **Colored Circle:** Agent

**Agent Status Panel:**
- Agent ID
- Alive/Dead status
- Energy level (%)
- Current reward

**Tips:**
- Pause để xem chi tiết
- Bật Sensors để hiểu AI "nhìn" thế nào
- Trails giúp phân tích behavior patterns

---

### 4. 📊 Model Comparison (MỚI!)
**URL:** http://localhost:4200/comparison

**Chức năng:**
- So sánh 2-5 models
- Charts & metrics
- Export comparison data

**Workflow:**
1. **Select Models:**
   - Click vào model cards để chọn
   - Chọn 2-5 models
   - Selected models có checkmark ✓

2. **Compare:**
   - Click "🔍 Compare Models"
   - Xem summary table
   - Analyze charts

3. **Insights:**
   - Best Average Reward
   - Fastest Training
   - Most Memory Efficient
   - Lowest Loss

4. **Export:**
   - Click "💾 Export Comparison Data"
   - Saves JSON file với all metrics

**Charts:**
- **Reward Comparison:** Line chart theo episodes
- **Loss Comparison:** Line chart theo episodes
- **Performance Overview:** Bar chart tổng quan

**Tips:**
- So sánh cùng algorithm với different hyperparameters
- So sánh different algorithms
- Export data để báo cáo

---

### 5. 💾 Export/Import Manager (MỚI!)
**URL:** http://localhost:4200/export-import

**Chức năng:**
- Backup models & data
- Restore từ backups
- History tracking

#### Export Data

**Workflow:**
1. **Select What to Export:**
   - ☑️ Include Models
   - ☑️ Include Training Logs
   - ☑️ Include Configurations

2. **Choose Format:**
   - JSON (readable)
   - ZIP (compressed)

3. **Export:**
   - Click "📥 Export Now"
   - Progress bar shows status
   - File downloads automatically

**Export Contains:**
```json
{
  "timestamp": "2026-05-10T...",
  "version": "1.0.0",
  "models": [...],
  "trainingLogs": [...],
  "configs": {...}
}
```

#### Import Data

**Workflow:**
1. **Select Files:**
   - Click upload area
   - Or drag & drop files
   - Supports .json and .zip

2. **Review Files:**
   - See file names & sizes
   - Remove unwanted files

3. **Import:**
   - Click "📤 Import Now"
   - Progress bar shows status
   - Success notification

4. **Download Template:**
   - Click "📋 Download Template"
   - See example format

**History:**
- Recent exports list
- Recent imports list
- Clear history options

**Tips:**
- Export regularly để backup
- Import để restore sau khi reinstall
- Use template để understand format

---

## 🎯 Common Workflows

### Workflow 1: Train & Monitor
```
1. Go to Training → Start training
2. Go to Visualization → Watch live
3. Monitor agent behavior
4. Stop when satisfied
```

### Workflow 2: Compare Models
```
1. Train multiple models (different configs)
2. Go to Comparison
3. Select models to compare
4. Analyze charts & insights
5. Export comparison data
```

### Workflow 3: Backup & Restore
```
1. Go to Export/Import
2. Select what to export
3. Export data
4. Save file safely
5. Import when needed
```

### Workflow 4: Full Experiment
```
1. Export current state (backup)
2. Train new model
3. Visualize training
4. Compare with old models
5. Export best model
```

---

## 🔧 Troubleshooting

### Backend không chạy
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Try different port
python -m uvicorn api.main:app --port 8001
```

### Frontend không chạy
```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install

# Try different port
ng serve --port 4201
```

### WebSocket không connect
1. Check backend is running
2. Check URL in websocket.service.ts
3. Check browser console for errors
4. Try refresh page

### Charts không hiển thị
1. Check Chart.js installed: `npm list chart.js`
2. Reinstall: `npm install chart.js ng2-charts`
3. Clear browser cache
4. Hard refresh (Ctrl+Shift+R)

### Canvas không render
1. Check browser supports Canvas
2. Check console for errors
3. Try different browser
4. Reduce agent count

---

## 📊 Performance Tips

### Backend
- Use `--workers 4` for production
- Enable caching
- Use database instead of in-memory storage

### Frontend
- Enable production mode: `ng build --prod`
- Lazy load components
- Throttle WebSocket updates
- Limit chart data points

### Visualization
- Reduce agent count for smoother animation
- Disable trails if laggy
- Lower canvas resolution
- Use requestAnimationFrame (already implemented)

---

## 🎓 Learning Path

### Beginner
1. ✅ Start training với default settings
2. ✅ Watch visualization
3. ✅ Compare 2 models
4. ✅ Export data

### Intermediate
1. ✅ Tune hyperparameters
2. ✅ Analyze training curves
3. ✅ Compare algorithms
4. ✅ Understand reward system

### Advanced
1. ✅ Modify AI algorithms
2. ✅ Add custom metrics
3. ✅ Implement new features
4. ✅ Optimize performance

---

## 🔗 Useful Links

### Documentation
- [Full README](./README.md)
- [Build Complete Summary](./✅_BUILD_TIEP_COMPLETE_MAY_2026.md)
- [API Docs](http://localhost:8000/docs)

### External Resources
- [Angular Docs](https://angular.io/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Chart.js Docs](https://www.chartjs.org/)
- [Reinforcement Learning Intro](https://spinningup.openai.com/)

---

## 💡 Pro Tips

1. **Training:**
   - Start với ít episodes để test
   - Tăng dần episodes khi đã hiểu
   - Save models thường xuyên

2. **Visualization:**
   - Pause để analyze behavior
   - Use trails để see patterns
   - Monitor energy levels

3. **Comparison:**
   - Compare similar configs first
   - Look for consistent patterns
   - Export data for reports

4. **Export/Import:**
   - Export before major changes
   - Keep multiple backups
   - Use descriptive filenames

5. **Performance:**
   - Close unused tabs
   - Disable trails if slow
   - Reduce agent count
   - Use Chrome for best performance

---

## 🎉 You're Ready!

Bây giờ bạn đã sẵn sàng để:
- ✅ Train AI agents
- ✅ Visualize training live
- ✅ Compare models
- ✅ Backup & restore data

**Happy Training! 🚀**

---

**Need Help?**
- Check console logs (F12)
- Read error messages
- Check API docs
- Review this guide

**Version:** 2.0.0
**Last Updated:** May 10, 2026
