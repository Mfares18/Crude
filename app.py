from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import numpy as np
import os, sys, json, joblib, warnings
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
warnings.filterwarnings('ignore')

# Resolve base dir: PyInstaller extracts to sys._MEIPASS when frozen
_BASE = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

app = FastAPI()

DATA_PATH    = os.path.join(_BASE, 'data', 'C1_cleaned.xlsx')
MODELS_DIR   = 'models'
HISTORY_FILE = os.path.join(MODELS_DIR, 'training_history.json')
os.makedirs(MODELS_DIR, exist_ok=True)

templates = Jinja2Templates(directory=os.path.join(_BASE, 'templates'))

FEATURES = [
    'Density, at 15°C, g/cm3',
    'API',
    'T50% (TBP),◦C',
    'Kin. Viscosityat 40◦C,mm2/s',
    'Flash point, °C',
    'Sulphur, wt.%',
    'Saturate, wt.%',
    'Aromatics, wt.%',
    'Resins, wt.%'
]
TARGET = 'Asphaltenes, wt.%'


# ─── Pydantic models ──────────────────────────────────────────────────────────

class AddDataRequest(BaseModel):
    model_config = {"extra": "allow"}
    name: Optional[str] = 'Unknown'

class TrainRequest(BaseModel):
    model: Optional[str] = 'RandomForest'
    test_size: Optional[float] = 0.2

class TrainAllRequest(BaseModel):
    test_size: Optional[float] = 0.2

class PredictRequest(BaseModel):
    model_config = {"extra": "allow"}
    model: Optional[str] = 'RandomForest'


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_data():
    df = pd.read_excel(DATA_PATH)
    df = df.dropna(subset=FEATURES + [TARGET])
    return df

def get_models():
    models = {
        'RandomForest': RandomForestRegressor(n_estimators=200, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=200, random_state=42),
        'ExtraTrees': ExtraTreesRegressor(n_estimators=200, random_state=42),
        'SVR': Pipeline([('scaler', StandardScaler()), ('model', SVR(kernel='rbf', C=10))]),
        'KNN': Pipeline([('scaler', StandardScaler()), ('model', KNeighborsRegressor(n_neighbors=5))]),
        'Ridge': Pipeline([('scaler', StandardScaler()), ('model', Ridge(alpha=1.0))]),
    }
    if HAS_XGB:
        models['XGBoost'] = XGBRegressor(n_estimators=200, random_state=42, verbosity=0)
    if HAS_LGB:
        models['LightGBM'] = LGBMRegressor(n_estimators=200, random_state=42, verbose=-1)
    return models

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)


# ─── Pages ────────────────────────────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get('/admin', response_class=HTMLResponse)
def admin(request: Request):
    return templates.TemplateResponse('admin.html', {'request': request})

@app.get('/predict', response_class=HTMLResponse)
def predict_page(request: Request):
    return templates.TemplateResponse('predict.html', {'request': request})


# ─── API ──────────────────────────────────────────────────────────────────────

@app.get('/api/dataset/info')
def dataset_info():
    df = load_data()
    return {
        'rows': len(df),
        'columns': df.columns.tolist(),
        'features': FEATURES,
        'target': TARGET,
        'stats': {
            col: {
                'mean': round(float(df[col].mean()), 4),
                'std': round(float(df[col].std()), 4),
                'min': round(float(df[col].min()), 4),
                'max': round(float(df[col].max()), 4),
            } for col in FEATURES + [TARGET]
        },
        'sample': df[['Petroleum designation'] + FEATURES + [TARGET]].head(20).fillna('').to_dict(orient='records')
    }

@app.post('/api/dataset/add')
def add_data(data: AddDataRequest):
    raw = data.model_dump()
    df = load_data()
    new_row = {
        'No': int(df['No'].max()) + 1,
        'Petroleum designation': raw.get('name', 'Unknown'),
    }
    for f in FEATURES + [TARGET]:
        new_row[f] = float(raw.get(f, 0))
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(DATA_PATH, index=False)
    return {'success': True, 'rows': len(df)}

@app.post('/api/train')
def train(data: TrainRequest):
    model_name = data.model
    test_size = data.test_size

    df = load_data()
    X = df[FEATURES].values
    y = df[TARGET].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    models = get_models()
    if model_name not in models:
        raise HTTPException(status_code=400, detail=f'Model {model_name} not available')

    model = models[model_name]
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

    r2 = float(r2_score(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))

    feat_imp = None
    try:
        if hasattr(model, 'feature_importances_'):
            feat_imp = dict(zip(FEATURES, [round(float(v), 4) for v in model.feature_importances_]))
        elif hasattr(model, 'named_steps'):
            inner = model.named_steps.get('model')
            if hasattr(inner, 'feature_importances_'):
                feat_imp = dict(zip(FEATURES, [round(float(v), 4) for v in inner.feature_importances_]))
            elif hasattr(inner, 'coef_'):
                coefs = np.abs(inner.coef_)
                feat_imp = dict(zip(FEATURES, [round(float(v), 4) for v in coefs / coefs.sum()]))
    except Exception:
        pass

    joblib.dump(model, os.path.join(MODELS_DIR, f'{model_name}.pkl'))

    result = {
        'model': model_name,
        'timestamp': datetime.now().isoformat(),
        'r2': round(r2, 4),
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'cv_r2_mean': round(float(cv_scores.mean()), 4),
        'cv_r2_std': round(float(cv_scores.std()), 4),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'feature_importance': feat_imp,
        'y_test': [round(float(v), 3) for v in y_test[:50]],
        'y_pred': [round(float(v), 3) for v in y_pred[:50]],
    }

    history = load_history()
    history.append(result)
    save_history(history)
    return result

@app.post('/api/train/all')
def train_all(data: TrainAllRequest = TrainAllRequest()):
    test_size = data.test_size
    df = load_data()
    X = df[FEATURES].values
    y = df[TARGET].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    models = get_models()
    results = []
    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            cv = cross_val_score(model, X, y, cv=5, scoring='r2')
            r = {
                'model': name,
                'timestamp': datetime.now().isoformat(),
                'r2': round(float(r2_score(y_test, y_pred)), 4),
                'rmse': round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
                'mae': round(float(mean_absolute_error(y_test, y_pred)), 4),
                'cv_r2_mean': round(float(cv.mean()), 4),
                'cv_r2_std': round(float(cv.std()), 4),
                'cv_r2': round(float(cv.mean()), 4),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
            }
            results.append(r)
            joblib.dump(model, os.path.join(MODELS_DIR, f'{name}.pkl'))
        except Exception as e:
            results.append({'model': name, 'error': str(e)})
    history = load_history()
    history.extend([r for r in results if 'error' not in r])
    save_history(history)
    return {'results': sorted(results, key=lambda x: x.get('r2', 0), reverse=True)}

@app.get('/api/models/list')
def list_models():
    models = []
    for f in os.listdir(MODELS_DIR):
        if f.endswith('.pkl'):
            models.append({'name': f.replace('.pkl', ''), 'file': f})
    return {'models': models}

@app.get('/api/models/history')
def get_history():
    return {'history': load_history()}

@app.post('/api/models/upload')
async def upload_model(model: UploadFile = File(...)):
    contents = await model.read()
    with open(os.path.join(MODELS_DIR, model.filename), 'wb') as f:
        f.write(contents)
    return {'success': True, 'name': model.filename}

@app.post('/api/predict')
def predict(data: PredictRequest):
    raw = data.model_dump()
    model_name = raw.get('model', 'RandomForest')
    model_path = os.path.join(MODELS_DIR, f'{model_name}.pkl')
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f'Model {model_name} not found. Please train it first.')

    model = joblib.load(model_path)
    features_in = [raw.get(f, 0) for f in FEATURES]
    X = np.array([features_in])
    pred = float(model.predict(X)[0])
    pred = max(0, pred)

    if pred < 2:
        risk = 'Low'; risk_pct = int(20 + pred * 10)
    elif pred < 5:
        risk = 'Medium'; risk_pct = int(40 + (pred - 2) * 10)
    elif pred < 10:
        risk = 'High'; risk_pct = int(70 + (pred - 5) * 3)
    else:
        risk = 'Critical'; risk_pct = min(99, int(85 + pred))

    density = float(raw.get('Density, at 15°C, g/cm3', 0.87))
    resins = float(raw.get('Resins, wt.%', 5))
    aromatics = float(raw.get('Aromatics, wt.%', 20))
    stability = round((resins + aromatics * 0.1) / (pred + 1) * density, 3) if pred > 0 else 1.5
    stability = min(2.0, max(0.1, stability))

    precip_prob = int(min(99, max(1, pred * 5 + (density - 0.85) * 100)))

    saturates = float(raw.get('Saturate, wt.%', 30))
    cii = round((pred + saturates) / (resins + aromatics + 0.001), 4) if (resins + aromatics) > 0 else 0

    return {
        'prediction': round(pred, 3),
        'risk': risk,
        'risk_pct': risk_pct,
        'stability_index': round(stability, 3),
        'precipitation_prob': precip_prob,
        'cii': round(cii, 4),
        'features_used': dict(zip(FEATURES, features_in)),
    }

@app.get('/api/correlations')
def correlations():
    df = load_data()
    corr = df[FEATURES + [TARGET]].corr()[TARGET].drop(TARGET)
    return {col: round(float(v), 4) for col, v in corr.items()}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True)
