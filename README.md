# Chezious Bot

A FastAPI-based chatbot application with agent capabilities and API endpoints.

## Project Structure

```
app/
├── main.py              # Application entry point
├── requirements.txt     # Project dependencies
├── agent/              # Agent logic and implementations
├── api/                # API endpoints and routes
├── config/             # Configuration settings
├── database/           # Database models and connections
├── models/             # Data models
├── schemas/            # Pydantic schemas for validation
├── services/           # Business logic and services
└── utils/              # Utility functions

data/                   # Data files and resources
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r app/requirements.txt
```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Features

- FastAPI-based REST API
- Agent-based chat functionality
- Database integration
- Request/response schema validation
- Modular architecture

## Configuration

Configuration settings are managed in the `app/config/` directory. Update environment variables as needed.

## Development

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8 guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## Contributing

1. Create a feature branch
2. Commit your changes
3. Push to the repository
4. Create a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.
