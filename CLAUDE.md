# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
- Run all tests: `pytest`
- Run specific test: `pytest tests/extraction_test.py::test_valid_extraction`
- Run with verbose output: `pytest -v`
- Start server: `uvicorn app.main:app --reload`

## Code Style Guidelines
- **Imports**: Standard imports first, then third-party, then local modules
- **Typing**: Use type hints with Pydantic models and Python typing module
- **Models**: Follow Pydantic BaseModel for data validation
- **Naming**: 
  - snake_case for functions/variables
  - CamelCase for classes
  - UPPER_CASE for constants
- **Error Handling**: Use try-except with specific exceptions
- **API Responses**: Return dict with status codes and data/error messages
- **Function Caching**: Use `@lru_cache` for optimization where appropriate
- **Docstrings**: Add descriptive docstrings for functions and classes
- **Line Length**: Keep lines under 100 characters

## Project Structure
- FastAPI server with API endpoints in app/main.py
- LLM integration with OpenAI/Gemini APIs
- Pydantic models for API request/response validation
- PDF extraction capabilities with PyMuPDF