# MedDevice Risk Monitor

### Medical Device Failure Prediction & Risk Assessment Platform

A full-stack, production-grade medical device risk evaluation platform designed for biomedical engineers and hospital maintenance teams. Powered by an existing 13-feature **XGBoost machine learning pipeline**, **SHAP (SHapley Additive exPlanations)** explainability, and the authentic **Faulty Medical Devices Global Dataset** stored in **MySQL**.

---

## 1. Project Overview & Solution

### Problem Statement
Modern healthcare facilities manage thousands of sophisticated medical devices (cardiovascular implants, infusion pumps, radiology systems, surgical equipment). Identifying elevated failure risk before clinical operation is critical to prevent adverse patient events and costly equipment downtime.

### Solution
**MedDevice Risk Monitor** provides an AI-assisted decision-support platform that:
1. Ingests historical adverse event data, regulatory classifications, manufacturer track records, and commercial distribution parameters.
2. Runs inference through a calibrated **XGBoost Classifier** model.
3. Computes transparent risk factors via **SHAP TreeExplainer**.
4. Delivers actionable maintenance protocols (inspection frequencies, CMMS logging, safety bulletin cross-referencing).
5. Enforces role-based access control with isolated assessment records for operational personnel and global governance for administrators.

---

## 2. Technology Stack

- **Frontend**: React 18, Vite, React Router DOM, Axios, Recharts, Lucide Icons, Vanilla CSS (Light Theme Design Tokens)
- **Backend**: Python 3.12, FastAPI, SQLAlchemy ORM, Pydantic v2, PyMySQL, PyJWT, Bcrypt
- **Database**: MySQL 8.0 (`medical_device_prediction`)
- **Machine Learning**: XGBoost, scikit-learn, pandas, numpy, joblib
- **Explainable AI**: SHAP (TreeExplainer)
- **Containerization**: Docker, Docker Compose

---

## 3. System Architecture

```
                                  KAGGLE DATASET
                        (devices, events, manufacturers CSVs)
                                         |
                                         v
                            backend/scripts/import_dataset.py
                                         |
                                         v
                         +---------------+---------------+
                         |         MySQL Database        |
                         |  Data: events, mfrs, devices  |
                         |  App:  users, predictions,    |
                         |        audit_logs             |
                         +---------------+---------------+
                                         |
                                         v
+-------------------------------------------------------------------------------+
|                          FastAPI Backend (Port 8000)                          |
|  - Metadata & Historical Counts API (Real dataset counts & valid categories)  |
|  - Auth & RBAC (Admin, Biomedical Engineer, Maintenance Team)                 |
|  - Model Service (Singleton XGBoost Pipeline + 13 Features Schema)            |
|  - SHAP TreeExplainer & Human-Readable Contributing Risk Factors              |
|  - Maintenance Protocol Recommendations & Clinical Disclaimers               |
|  - Comprehensive Audit Logger                                                 |
+---------------------------------------+---------------------------------------+
                                        | REST API (JWT)
                                        v
+-------------------------------------------------------------------------------+
|                       React 18 + Vite Frontend (Port 5173)                    |
|  - Public Landing Page with Real Ingested Dataset Stats                       |
|  - Secure Authentication (JWT, Role Guards)                                   |
|  - Common Operational Dashboard (Real DB Metrics, Quick Actions)              |
|  - 13-Feature Risk Assessment Form (Empty by default, dynamic metadata selects)|
|  - Risk Score Gauge, SHAP Factors, Recommendations, Recharts comparison       |
|  - User Prediction History & Detail Modal Inspections                         |
|  - Admin Dashboard, User Management, Global Prediction Audit, Activity Logs   |
+-------------------------------------------------------------------------------+
```

---

## 4. The 13 Trained Model Features

The pre-trained XGBoost model strictly consumes these exact 13 features:

| # | Feature Name | Type | Description / Valid Examples |
|---|--------------|------|------------------------------|
| 1 | `type` | Categorical | Event type (`Field Safety Notice`, `Recall`, `Safety alert`) |
| 2 | `status` | Categorical | Regulatory status (`Completed`, `Open, Classified`, `Terminated`) |
| 3 | `classification` | Categorical | Device clinical specialty (`Cardiovascular Devices`, `Anesthesiology Devices`, etc.) |
| 4 | `risk_class` | Categorical | FDA risk class (`1`, `2`, `3`, `II`, `HDE`, `Unclassified`) |
| 5 | `country_event` | Categorical | Event country ISO code (`USA`, `DEU`, `FRA`, `GBR`, etc.) |
| 6 | `country_device` | Categorical | Device origin ISO code (`USA`, `DEU`, `FRA`, `JPN`, etc.) |
| 7 | `implanted` | Categorical | Surgical implant status (`YES` or `NO`) |
| 8 | `name_manufacturer` | Categorical | Manufacturer name (`Medtronic`, `Abbott`, `Philips`, `Baxter`, etc.) |
| 9 | `quantity_in_commerce` | Numerical | Non-negative commercial distribution units |
| 10 | `event_count` | Numerical | Historical device event count |
| 11 | `manufacturer_event_count`| Numerical | Historical manufacturer event volume |
| 12 | `event_year` | Numerical | Year of evaluation (e.g. `2025`) |
| 13 | `event_month` | Numerical | Month of evaluation (`1` to `12`) |

---

## 5. User Roles & Access Control

| Role | Operational Scope | Accessible Views |
|------|-------------------|------------------|
| **Biomedical Engineer** | Perform device evaluations, review SHAP factors, manage isolated personal history | `/dashboard`, `/assessment`, `/predictions`, `/profile` |
| **Maintenance Team** | Same operational workflow as Biomedical Engineer | `/dashboard`, `/assessment`, `/predictions`, `/profile` |
| **Administrator** | Manage platform users, toggle status, inspect global predictions, monitor audit trail | `/admin/dashboard`, `/admin/users`, `/admin/predictions`, `/admin/logs`, `/admin/profile` |

*Default Administrator Credentials:*
- **Email**: `admin@meddevice.local`
- **Password**: `Admin@123456`

---

## 6. Database Schema (MySQL)

### Dataset Tables (Ingested Historical Data)
- **`manufacturers`**: 31,827 records (`id`, `name`, `parent_company`, `address`, `source`)
- **`devices`**: 118,249 records (`id`, `manufacturer_id`, `name`, `classification`, `quantity_in_commerce`, `risk_class`, `country`)
- **`events`**: 124,969 records (`id`, `device_id`, `type`, `status`, `country`, `action_classification`, `event_year`, `event_month`)

### Application Tables
- **`users`**: `id`, `full_name`, `email`, `password_hash`, `role`, `is_active`, `created_at`, `updated_at`
- **`predictions`**: `id`, `user_id`, 13 model inputs, `prediction`, `prediction_label`, `risk_score`, `risk_percentage`, `risk_level`, `explanation`, `risk_factors`, `maintenance_recommendation`, `created_at`
- **`audit_logs`**: `id`, `user_id`, `action`, `description`, `ip_address`, `created_at`

---

## 7. API Reference

### Health & Information
- `GET /api/health` - Live database and model readiness check
- `GET /api/model/info` - Non-sensitive model parameters & evaluation metrics

### Authentication
- `POST /api/auth/signup` - Register Biomedical Engineer or Maintenance Team account
- `POST /api/auth/login` - Authenticate and receive JWT
- `POST /api/auth/logout` - Invalidate session & log audit trail

### Metadata & Historical Querying
- `GET /api/metadata/options` - Valid categories for dropdowns
- `GET /api/metadata/historical-counts` - Real-time calculation of `event_count` and `manufacturer_event_count` from MySQL
- `GET /api/metadata/dataset-stats` - Live counts of events, devices, and manufacturers

### Risk Assessment & Predictions
- `POST /api/predictions` - Submit 13 features for XGBoost inference and SHAP attribution
- `GET /api/predictions` - Retrieve current user's prediction history (with search/filter)
- `GET /api/predictions/{id}` - Detailed assessment view

### Administration
- `GET /api/admin/dashboard` - Platform statistics & distribution metrics
- `GET /api/admin/users` - User directory with search and role filters
- `PUT /api/admin/users/{id}/status` - Activate or deactivate user accounts
- `GET /api/admin/predictions` - Global assessment records
- `GET /api/admin/logs` - Chronological security and operational audit trail

---

## 8. Setup & Execution Guide

### Prerequisites
- Python 3.12+
- Node.js 20+
- MySQL 8.0+

### Option A: Local Native Execution (Recommended)

1. **Configure Environment Variables**:
   Ensure `backend/.env` is configured with your local MySQL credentials:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DB=medical_device_prediction
   DATABASE_URL=mysql+pymysql://root:root@localhost:3306/medical_device_prediction
   JWT_SECRET_KEY=your_secret_key
   ```

2. **Ingest Kaggle Dataset**:
   ```bash
   python backend/scripts/import_dataset.py
   ```

3. **Start FastAPI Backend**:
   ```bash
   uvicorn app.main:app --app-dir backend --reload --port 8000
   ```
   *Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)*

4. **Start React + Vite Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   *Frontend UI: [http://localhost:5173](http://localhost:5173)*

### Option B: Docker Compose Execution

```bash
docker-compose up --build -d
```

---

## 9. Running Tests

Execute the automated backend test suite:
```bash
$env:PYTHONPATH="backend"; pytest backend/tests/ -v
```

---

## 10. Clinical Decision Support Disclaimer

> **IMPORTANT NOTICE**: This platform provides decision-support risk assessment based on historical medical-device data patterns. It does not monitor real-time physical telemetry or predict specific failure timetables. It does not replace manufacturer instructions, approved hospital maintenance procedures, safety notices, recalls, or professional biomedical engineering judgment.
