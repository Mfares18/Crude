# 🔥 CrudeAI — Asphaltene Prediction Platform

A full-stack AI platform for predicting asphaltene content in crude oil using machine learning.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

### 3. Open in Browser
- 🏠 Home: http://localhost:5000
- ⚙️ Admin Dashboard: http://localhost:5000/admin
- 🔬 Prediction App: http://localhost:5000/predict

---

## 📁 Project Structure

```
asphaltene_app/
├── app.py              # Flask backend + API routes
├── requirements.txt    # Python dependencies
├── data/
│   └── C1_cleaned.xlsx # Dataset (233 crude oil samples)
├── models/             # Saved .pkl model files
│   └── training_history.json
└── templates/
    ├── index.html      # Landing page
    ├── admin.html      # Admin dashboard
    └── predict.html    # Prediction dashboard
```

---

## 🧠 ML Models Available

| Model | Type | Notes |
|-------|------|-------|
| RandomForest | Ensemble | Best default choice |
| GradientBoosting | Boosting | Good accuracy |
| ExtraTrees | Ensemble | Fast training |
| SVR | Kernel | Good for small data |
| KNN | Instance-based | Simple & fast |
| Ridge | Linear | Baseline |
| XGBoost | Boosting | Best accuracy (requires xgboost) |
| LightGBM | Boosting | Fast & accurate (requires lightgbm) |

---

## 📊 Dataset Features

| Feature | Unit | Description |
|---------|------|-------------|
| Density | g/cm³ at 15°C | Crude oil density |
| API | °API | API gravity |
| T50% (TBP) | °C | 50% boiling point |
| Kinematic Viscosity | mm²/s at 40°C | Viscosity |
| Flash Point | °C | Flash point |
| Sulphur | wt.% | Sulphur content |
| Saturates | wt.% | SARA - Saturates |
| Aromatics | wt.% | SARA - Aromatics |
| Resins | wt.% | SARA - Resins |
| **Asphaltenes** | **wt.%** | **← TARGET** |

---

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/dataset/info | Get dataset info & stats |
| POST | /api/dataset/add | Add new sample |
| POST | /api/train | Train one model |
| POST | /api/train/all | Train all models |
| GET | /api/models/list | List saved models |
| GET | /api/models/history | Training history |
| POST | /api/models/upload | Upload .pkl model |
| POST | /api/predict | Run prediction |
| GET | /api/correlations | Feature correlations |

---

## 💡 Usage Tips

1. **Start with Admin**: Train at least one model before predicting
2. **Train All**: Use "Train All Models" to compare all models at once
3. **Best Model**: RandomForest or XGBoost typically give best R² scores
4. **Upload**: You can upload a pre-trained .pkl model file
5. **Quick Samples**: Use the preset buttons (Light/Medium/Heavy/Bitumen) in the predict page
