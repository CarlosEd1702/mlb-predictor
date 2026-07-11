# MLB Predictor App

Sistema de predicción de resultados y props de MLB usando Monte Carlo simulation, machine learning, y seguimiento en vivo.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend/API | FastAPI (Python) |
| Modelos | XGBoost, LightGBM, scikit-learn |
| Simulación | Monte Carlo (NumPy) |
| Base de datos | PostgreSQL 16+ |
| Frontend | Expo (React Native) |
| Jobs | APScheduler |

## Setup rápido

```bash
# 1. Crear venv e instalar dependencias
python -m venv .venv
.\.venv\Scripts\activate    # Windows
pip install -e backend/[dev,ml]

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar ODDS_API_KEY en backend/.env

# 3. Correr migraciones de DB
alembic upgrade head

# 4. Iniciar backend
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /api/v1/health` — Health check
- `GET /api/v1/predicciones/hoy` — Picks del día
- `GET /api/v1/partido/{id}` — Detalle de partido
- `GET /api/v1/historial` — Historial de efectividad

## Roadmap

| Semana | Hito |
|--------|------|
| 1-2 | Pipeline de datos + DB cargada |
| 3-5 | Modelos base entrenados |
| 6-7 | Motor de simulación + edge |
| 8-10 | App Expo conectada |
| 11+ | Testing en vivo (3 meses) |
