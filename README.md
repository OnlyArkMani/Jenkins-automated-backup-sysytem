#  Weather Dashboard

**Student Name:** [Your Name]
**Registration No:** [Your Registration Number]
**Course:** CSE3253 DevOps [PE6]
**Semester:** VI (2025–2026)
**Project Type:** Jenkins & CI/CD
**Difficulty:** Intermediate

---

## Project Overview

### Problem Statement
Developers and students need a simple, reliable weather lookup tool — but more importantly, this project demonstrates a **complete DevOps pipeline**: from writing code, to containerising it, running automated tests, and deploying it with zero-downtime rolling updates — all orchestrated through Jenkins CI/CD.

### Objectives
- [x] Build a Python Flask web application that fetches live weather data
- [x] Containerise the app using Docker with a multi-stage build
- [x] Automate testing, building, and deployment via a Jenkins Pipeline
- [x] Deploy to a local Kubernetes cluster (minikube) with liveness probes
- [x] Monitor the running application with Nagios health checks
- [x] Provide GitHub Actions as a backup CI pipeline

### Key Features
- Live weather lookup by city name (OpenWeatherMap API)
- Recent search history (SQLite)
- `/health` endpoint for K8s + Nagios probes
- Full CI/CD from code push → tested → built → deployed

---

## Technology Stack

### Core Technologies
- **Language:** Python 3.11
- **Framework:** Flask 3.x
- **Database:** SQLite (via Python `sqlite3`)
- **API:** OpenWeatherMap (free tier)

### DevOps Tools
| Tool | Purpose |
|---|---|
| Git + GitHub | Version control & backup CI trigger |
| Jenkins | Primary CI/CD pipeline (6 stages) |
| GitHub Actions | Backup CI on every push/PR |
| Docker + Docker Compose | Containerisation & multi-service orchestration |
| Kubernetes (minikube) | Production-style deployment with rolling updates |
| Nagios | HTTP availability and response-time monitoring |

---

## Getting Started

### Prerequisites
- [ ] Docker Desktop v20.10+
- [ ] Git 2.30+
- [ ] Python 3.11+
- [ ] minikube (for Kubernetes deployment)
- [ ] Jenkins (local install)
- [ ] OpenWeatherMap API key (free at https://openweathermap.org/api)

### Quick Start — Docker Compose

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/devopsprojectweatherdashboard.git
cd devopsprojectweatherdashboard

# 2. Set your API key
cp .env.example .env
# Edit .env and add your OPENWEATHER_API_KEY

# 3. Start the app + Nagios
docker-compose -f infrastructure/docker/docker-compose.yml up --build

# App       → http://localhost:5000
# Nagios    → http://localhost:8080  (nagiosadmin / nagios123)
```

### Alternative — Run Locally Without Docker

```bash
cd src
pip install -r requirements.txt
export OPENWEATHER_API_KEY=your_key_here
python app.py
# → http://localhost:5000
```

---

## Project Structure

```
devopsprojectweatherdashboard/
├── README.md
├── .gitignore
├── .env.example
├── src/
│   ├── app.py                      Flask application
│   ├── requirements.txt
│   ├── templates/index.html        Dashboard UI
│   └── tests/test_app.py           14 pytest unit tests
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile              Multi-stage build
│   │   └── docker-compose.yml      App + Nagios
│   └── kubernetes/
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── deployment.yaml         2 replicas, rolling update
│       ├── service.yaml            NodePort 30500
│       └── deploy.sh               Helper script
├── pipelines/
│   ├── Jenkinsfile                 6-stage pipeline
│   └── .github/workflows/cicd.yml GitHub Actions backup
├── monitoring/
│   └── nagios/
│       ├── weather-dashboard.cfg   4 service checks
│       └── commands.cfg
└── docs/
    ├── projectplan.md
    ├── designdocument.md
    └── userguide.md
```

---

## CI/CD Pipeline

### Jenkins Pipeline Stages
```
Checkout → Lint → Test → Build Docker → Security Scan → Deploy
                                                          ├── dev   (docker-compose)
                                                          ├── staging (kubectl apply)
                                                          └── prod  (manual gate)
```

| Stage | Tool | What it checks |
|---|---|---|
| Lint | flake8 | Code style, line length |
| Test | pytest + coverage | 14 unit tests, coverage report |
| Build | docker build | Multi-stage image |
| Security Scan | Trivy | HIGH/CRITICAL CVEs |
| Deploy | kubectl / docker-compose | Environment-specific |

### Pipeline Status
![Pipeline](https://img.shields.io/badge/pipeline-passing-brightgreen)

---

## Testing

```bash
cd src
pytest tests/test_app.py -v --cov=. --cov-report=term-missing
```

14 tests covering:
- All HTTP routes (`/`, `/api/weather`, `/api/recent`, `/health`)
- Input validation (empty city, whitespace)
- Mocked API responses (success, 404, 401, timeout, connection error)
- Database persistence of searches

---

## Monitoring

Nagios monitors 4 services every 1–5 minutes:

| Check | Endpoint | Alert |
|---|---|---|
| HTTP Port 5000 | `:5000` | Port unreachable |
| Health Endpoint | `/health` | Not 200 / missing "healthy" |
| Response Time | `/health` | Warn >2s / Critical >5s |
| API Endpoint | `/api/recent` | Not 200 |

Access Nagios at `http://localhost:8080` after `docker-compose up`.

---

## Docker & Kubernetes

```bash
# Build and push
docker build -f infrastructure/docker/Dockerfile -t devopsproject/weather-dashboard:latest .

# Deploy to minikube
export OPENWEATHER_API_KEY=your_key
./infrastructure/kubernetes/deploy.sh up

# Check status
./infrastructure/kubernetes/deploy.sh status

# Get URL
./infrastructure/kubernetes/deploy.sh url
```

---

## Performance Metrics

| Metric | Target | Notes |
|---|---|---|
| Build Time | < 5 min | Jenkins full pipeline |
| Test Coverage | > 80% | pytest-cov |
| Deployment Frequency | On every push to main | |
| Health Check Interval | 1 min | Nagios |

---

## Security Measures
- [x] Non-root user in Docker container (`appuser`)
- [x] API key stored as environment variable / K8s Secret (never in code)
- [x] `.env` excluded via `.gitignore`
- [x] Trivy vulnerability scan in pipeline
- [x] Input validation on all API endpoints

---

## Git Branching Strategy

```
main
├── develop
│   ├── feature/flask-app
│   ├── feature/docker-setup
│   ├── feature/jenkins-pipeline
│   └── feature/kubernetes-deploy
└── hotfix/...
```

### Commit Convention
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Test related
- `ci:` Pipeline changes
- `chore:` Maintenance

---

## Documentation
- [Project Plan](docs/projectplan.md)
- [Design Document](docs/designdocument.md)
- [User Guide](docs/userguide.md)
- [Monitoring Setup](monitoring/README.md)

---

## Project Challenges

1. **Nagios container networking** — solved by putting both containers on a named Docker bridge network so Nagios can resolve `weather-app` by container name
2. **K8s image pull on minikube** — solved by loading the locally built image into minikube using `minikube image load` and setting `imagePullPolicy: IfNotPresent`
3. **Jenkins credentials security** — API key stored as a Jenkins credential (secret text), never in the Jenkinsfile or environment files

## Learnings
- How a `/health` endpoint ties together Docker healthchecks, K8s liveness probes, and Nagios checks
- Multi-stage Docker builds reduce image size significantly
- Jenkins `input` step for manual production approval gates
- Rolling updates in K8s keep the app running during deployments

---

## Acknowledgments
- Course Instructor: Mr. Jay Shankar Sharma
- OpenWeatherMap free tier API
- Nagios, Docker, Kubernetes open-source communities

---

