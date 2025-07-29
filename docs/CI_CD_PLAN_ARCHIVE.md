# CI/CD Pipeline Plan for Ben Project

## Project Overview
The Ben project is a Flask web application that hosts a Ben Zyskowicz surname guessing game. It uses SQLite for data storage and includes a parser script to populate the database with surname variations from HTML data.

## Deployment Target
- **Primary Target**: Home Raspberry Pi server
- **Deployment Strategy**: Single-environment deployment with automated updates
- **Infrastructure**: Self-hosted GitHub Actions runner on Raspberry Pi

## Current Project Structure Analysis

### Technology Stack
- **Backend**: Python Flask web application
- **Database**: SQLite (ben.db) 
- **Frontend**: HTML templates with static assets
- **Package Management**: uv (modern Python package manager)
- **Containerization**: Docker (Dockerfile exists)
- **Dependencies**: Flask, BeautifulSoup4, lxml

### Existing Files
- `app.py` - Main Flask application
- `parse_surnames.py` - Data parsing script with uv dependencies
- `setup_db.py` - Database initialization
- `Dockerfile` - Container configuration
- `pyproject.toml` - Python project configuration
- `uv.lock` - Dependency lock file

## CI/CD Pipeline Design

### 1. Repository Structure
```
.github/
└── workflows/
    ├── ci.yml              # Continuous Integration
    └── deploy-raspi.yml    # Deployment to Raspberry Pi
scripts/
├── setup-raspi.sh         # Initial Raspberry Pi setup
├── deploy.sh              # Deployment script
└── health-check.sh        # Post-deployment verification
```

### 2. Continuous Integration (CI)
**Trigger**: On every push and pull request

**Steps**:
1. **Code Quality**
   - Python syntax check
   - Code formatting (ruff/black)
   - Import sorting (isort)
   - Type checking (mypy - optional)

2. **Testing**
   - Unit tests for parsing logic
   - Integration tests for Flask app
   - Database functionality tests
   - HTML parsing validation

3. **Security**
   - Dependency vulnerability scanning
   - Code security analysis

4. **Build Validation**
   - Docker image build test
   - Push to container registry (GitHub Container Registry)
   - uv dependency resolution
   - Application startup test

### 3. Continuous Deployment (CD)
**Trigger**: On push to `master` branch (after CI passes)

**Target**: Home Raspberry Pi server with self-hosted runner

**Deployment Process**:
1. **Pre-deployment**
   - Build and push Docker image to registry
   - Run smoke tests
   - Backup current database to `/srv/ben/config/backup`

2. **Deployment**
   - Pull latest Docker image to `/srv/ben`
   - Update docker-compose configuration if needed
   - Start/restart services via `docker-compose up -d`
   - Verify deployment

3. **Post-deployment**
   - Health check endpoints
   - Database connectivity test
   - Web interface accessibility
   - Rollback on failure

### 4. Infrastructure Requirements

#### Raspberry Pi Setup
- **Docker & Docker Compose**: Container orchestration
- **GitHub Actions Runner**: Self-hosted runner installation
- **Directory Structure**: `/srv/ben` for application files and database
- **Monitoring**: Basic health checks and logging
- **Backup Strategy**: Regular database backups to `/srv/ben/config/backup`

**Note**: Reverse proxy configuration is handled separately at the server level.

#### Services Architecture
```
┌─────────────────┐    ┌──────────────────┐
│  GitHub Actions │───▶│  Raspberry Pi    │
│  (CI/CD)        │    │                  │
│                 │    │  ┌─────────────┐ │
│ 1. Build Image  │    │  │ Ben App     │ │
│ 2. Push to      │    │  │ (Docker)    │ │
│    Registry     │    │  └─────────────┘ │
│ 3. Deploy via   │    │  /srv/ben/       │
│    SSH          │    │  ├── ben.db      │
└─────────────────┘    │  ├── docker-     │
                       │  │   compose.yml │
                       │  └── config/     │
                       └──────────────────┘
```

### 5. Configuration Management

#### Environment Variables
- `DATABASE_DIR`: Database file location (default: `/srv/ben`)
- `FLASK_ENV`: Environment (production/development)
- `PORT`: Application port
- `LOG_LEVEL`: Logging verbosity

#### File System Layout
```
/srv/ben/
├── ben.db                    # SQLite database (host filesystem)
├── docker-compose.yml        # Container orchestration
├── config/                   # Configuration files
│   ├── app.env              # Environment variables
│   └── backup/              # Database backups
└── logs/                     # Application logs (mounted from container)
```

#### Secrets Management
- GitHub repository secrets for deployment
- SSH keys for Raspberry Pi access
- Container registry credentials (GitHub Container Registry)
- Environment variables for production deployment

## Implementation Plan

### Phase 1: Basic CI Pipeline
1. Create `.github/workflows/ci.yml`
2. Set up basic testing framework
3. Add code quality checks
4. Implement Docker build validation

### Phase 2: Raspberry Pi Setup
1. Create setup scripts for Raspberry Pi
2. Install and configure GitHub Actions runner
3. Set up Docker environment
4. Configure deployment directories (`/srv/ben` structure)
5. Set up database file permissions and backup location

### Phase 3: Deployment Pipeline
1. Create deployment workflow with container registry integration
2. Implement health checks
3. Add rollback mechanism (previous image version)
4. Set up monitoring and notifications

### Phase 4: Enhanced Features
1. Database backup/restore automation
2. Performance monitoring
3. Log aggregation
4. Security hardening

## File Creation Checklist

### GitHub Actions Workflows
- [ ] `.github/workflows/ci.yml` - Continuous Integration
- [ ] `.github/workflows/deploy-raspi.yml` - Deployment workflow

### Setup Scripts
- [ ] `scripts/setup-raspi.sh` - Raspberry Pi initial setup
- [ ] `scripts/deploy.sh` - Docker image pull and compose restart
- [ ] `scripts/health-check.sh` - Post-deployment verification
- [ ] `scripts/backup-db.sh` - Database backup automation

### Configuration Files
- [ ] `docker-compose.production.yml` - Production Docker setup with host volume mounts
- [ ] `.dockerignore` - Docker build optimization
- [ ] Update `pyproject.toml` with test dependencies
- [ ] `config/app.env` - Environment variables for production
- [ ] Container registry configuration for GitHub Container Registry

### Testing Infrastructure
- [ ] `tests/test_app.py` - Flask application tests
- [ ] `tests/test_parser.py` - Surname parser tests
- [ ] `tests/test_database.py` - Database functionality tests
- [ ] `pytest.ini` - Testing configuration

### Documentation
- [ ] `DEPLOYMENT.md` - Deployment instructions
- [ ] `DEVELOPMENT.md` - Development setup guide
- [ ] Update `README.md` with CI/CD information

## Benefits

### For Development
- **Automated Testing**: Catch issues before deployment
- **Code Quality**: Consistent formatting and standards
- **Fast Feedback**: Quick validation of changes

### For Operations
- **Reliable Deployments**: Automated, repeatable process
- **Zero Downtime**: Rolling updates with health checks
- **Easy Rollbacks**: Quick revert capability
- **Monitoring**: Health status and deployment notifications

### For Maintenance
- **Dependency Updates**: Automated security patches
- **Backup Automation**: Regular database backups
- **Documentation**: Clear deployment and troubleshooting guides

## Risk Mitigation

### Deployment Risks
- **Database Backup**: Automatic backup before deployment
- **Health Checks**: Verify application health post-deployment
- **Rollback Strategy**: Quick revert to previous version
- **Testing**: Comprehensive test suite

### Infrastructure Risks
- **Single Point of Failure**: Document manual deployment process
- **Network Issues**: Local deployment capabilities
- **Resource Constraints**: Monitor Raspberry Pi resources

## Success Metrics
- **Deployment Success Rate**: >95% successful deployments
- **Deployment Time**: <5 minutes end-to-end
- **Test Coverage**: >80% code coverage
- **Rollback Time**: <2 minutes when needed

## Next Steps
1. Review and approve this plan
2. Begin Phase 1 implementation (CI pipeline)
3. Set up Raspberry Pi infrastructure
4. Implement deployment automation
5. Add monitoring and alerting

---

**Note**: This plan focuses on home Raspberry Pi deployment as specified, providing a robust but lightweight CI/CD solution suitable for personal/hobby projects while maintaining professional standards.
