# Ben Project - GitHub Copilot Instructions

## Project Overview

The Ben project is a Flask web application hosting a Ben Zyskowicz surname guessing game. It uses SQLite for data storage and includes a parser script to populate the database with surname variations from HTML data.

## Technology Stack & Conventions

### Backend

- **Framework**: Python Flask web application
- **Python Version**: Python 3.13
- **Database**: SQLite (ben.db) on host filesystem at `/srv/ben/ben.db`
- **Package Management**: Use `uv` for all Python dependency management
- **Code Quality**: Ruff with ALL rules enabled for syntax and style checking
- **Containerization**: Docker with docker-compose for production deployment

### Key Dependencies

- Flask for web framework
- SQLite3 for database operations
- uv for package management

### Database Population Script Dependencies

- BeautifulSoup4 and lxml for HTML parsing (used in parse_surnames.py only)

### Code Standards

- Use `uv` script notation in standalone scripts: `# /// script` blocks
- Follow Python PEP 8 conventions
- Use type hints where appropriate
- Ruff with ALL rules enabled enforces modern Python best practices

## Architecture & Deployment

### Production Environment

- **Target**: Home Raspberry Pi server
- **Location**: `/srv/ben/` directory structure
- **Database**: Host filesystem (not Docker volume)
- **Reverse Proxy**: Managed separately (not part of this project)

### File Structure

```
/srv/ben/
├── ben.db                    # SQLite database (host filesystem)
├── docker-compose.yml        # Container orchestration
├── config/
│   ├── app.env              # Environment variables
│   └── backup/              # Database backups
└── logs/                     # Application logs (mounted from container)
```

### Environment Variables

- `DATABASE_DIR`: Database file location (default: `/srv/ben`)
- `FLASK_ENV`: Environment (production/development)
- `PORT`: Application port
- `LOG_LEVEL`: Logging verbosity

## CI/CD Pipeline Guidelines

### Continuous Integration

When creating CI workflows:

- Trigger on all pushes and pull requests
- Include code quality checks (ruff/black formatting)
- Run comprehensive test suite
- Build and test Docker images on GitHub-hosted runners
- Push images to GitHub Container Registry on success

### Continuous Deployment

When creating deployment workflows:

- Trigger only on pushes to `master` branch
- Use self-hosted GitHub Actions runner on Raspberry Pi
- Pull Docker images from GitHub Container Registry (don't build locally)
- Use `docker-compose up -d` for daemon deployment
- Include health checks and rollback mechanisms
- **CRITICAL**: Never include database initialization in deployment scripts
- **CRITICAL**: Always preserve existing ben.db file during deployments

### Docker Best Practices

- Use multi-stage builds for production images
- Include `.dockerignore` for build optimization
- Mount database as host volume: `/srv/ben/ben.db:/app/data/ben.db`
- Use GitHub Container Registry for image storage
- Tag images with git commit SHA for versioning

## Development Guidelines

### Testing

- Create tests for parsing logic in `tests/test_parser.py`
- Include Flask application tests in `tests/test_app.py`
- Test database functionality in `tests/test_database.py`
- Use pytest as the testing framework
- Aim for >80% code coverage

### Database Operations

- Always use connection context managers
- Include proper error handling for database operations
- **NEVER overwrite ben.db during deployments** - preserve user guesses
- Store backups in `/srv/ben/config/backup/` before deployments
- Database setup scripts (`setup_db.py`, `parse_surnames.py`) are manual-only operations

### Security Considerations

- Use environment variables for sensitive configuration
- Implement proper SQL injection prevention (parameterized queries)
- Include dependency vulnerability scanning in CI
- Use GitHub repository secrets for deployment credentials

## Database Management

### Critical Rules

- **Database Persistence**: The `ben.db` file contains user guesses and must NEVER be overwritten
- **Manual Setup Only**: Database initialization scripts are run manually during initial setup
- **No Auto-Migration**: CI/CD should never run database setup or population scripts
- **Preserve User Data**: All deployments must maintain existing user guesses and game data

### Initial Setup (Manual Only)

```bash
# Run ONLY during initial setup - NEVER in CI/CD
uv run python setup_db.py        # Create database schema
uv run python parse_surnames.py  # Populate initial surname variations
```

### Deployment Process (Automated)

```bash
# Safe deployment commands - preserve database
cd /srv/ben
cp ben.db config/backup/ben.db.$(date +%Y%m%d_%H%M%S)  # Backup first
docker-compose pull                                     # Get new image
docker-compose up -d                                    # Restart services
```

## Project-Specific Rules

### When working with surname parsing:

- Handle multiple surnames separated by commas
- Clean HTML tags and special characters properly
- Use Windows-1252 encoding for the source HTML file
- Implement duplicate detection and handling

### When modifying Flask routes:

- Include proper error handling
- Use template rendering for HTML responses
- Implement database connection management via Flask's g object
- Follow RESTful conventions where applicable

### When updating Docker configuration:

- Ensure database path points to host filesystem
- Use uv for dependency installation in containers
- Include health check endpoints
- Configure proper logging output
- **CRITICAL**: Never include database initialization in container startup
- Database file must persist across all deployments and container restarts

## Deployment Process

### Manual Deployment Steps

1. Build and push Docker image to registry
2. SSH to Raspberry Pi
3. Navigate to `/srv/ben`
4. Pull latest image: `docker-compose pull`
5. Restart services: `docker-compose up -d`
6. Verify health: Run health checks

### Automated Deployment Requirements

- Backup database before deployment
- Pull latest Docker image
- Restart services via docker-compose
- Verify application health
- Rollback on failure
- **NEVER run database setup scripts during automated deployment**

## File Creation Guidelines

### Always include these files in new workflows:

- `.github/workflows/ci.yml` for continuous integration
- `.github/workflows/deploy-raspi.yml` for deployment
- `docker-compose.production.yml` for production setup
- Health check scripts for deployment verification

### Configuration file patterns:

- Use YAML for workflow configurations
- Use TOML for Python project configuration
- Use .env files for environment variables
- Include comprehensive error handling

## Success Metrics

- Deployment success rate: >95%
- Deployment time: <5 minutes end-to-end
- Test coverage: >80%
- Rollback time: <2 minutes when needed

## Common Commands

### Development

```bash
# Setup environment
uv sync

# Run application locally
uv run python app.py

# Run parser script
uv run parse_surnames.py

# Run tests
uv run pytest

# Database setup (MANUAL ONLY - NEVER in automated deployments)
uv run python setup_db.py        # Only during initial setup
uv run python parse_surnames.py  # Only during initial setup
```

### Production Deployment

```bash
# Deploy to production (on Raspberry Pi)
cd /srv/ben
docker-compose pull
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# IMPORTANT: Database setup is NEVER part of deployment
# ben.db must persist and contain user guesses from the game
```

---

**Note**: This project focuses on home Raspberry Pi deployment with a self-hosted GitHub Actions runner. All CI/CD implementations should prioritize simplicity while maintaining professional standards suitable for personal/hobby projects.
