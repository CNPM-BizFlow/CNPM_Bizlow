# BizFlow - Digital Transformation Platform

This document provides a comprehensive overview of the BizFlow project, its architecture, and development conventions, intended to be used as a guide for Gemini AI.

## Project Overview

BizFlow is a Flask-based backend API designed to help small businesses digitize their operations. It provides a clean architecture for managing sales, inventory, customer debt, and financial reporting, with a focus on complying with Vietnamese accounting standards (Thông tư 88/2021/TT-BTC).

**Key Features:**
*   **Point of Sale (POS):** Quickly create orders.
*   **Inventory Management:** Real-time inventory tracking.
*   **Customer Relationship Management (CRM):** Manage customer information and track debt.
*   **Financial Reporting:** Generate sales and debt reports.
*   **AI-Powered Order Creation:** Uses natural language processing to create draft orders.
*   **Role-Based Access Control (RBAC):** Differentiates between Admins, Owners, and Employees.

**Technologies Used:**
*   **Backend:** Flask
*   **Database:** MySQL
*   **ORM:** SQLAlchemy
*   **Authentication:** JWT
*   **API Documentation:** Swagger (Flasgger)
*   **Containerization:** Docker

## Building and Running

### Local Development

1.  **Prerequisites:**
    *   Python 3.10+
    *   MySQL Server

2.  **Setup:**
    *   Create a MySQL database named `bizflow`.
    *   Create a `.env` file in the `src` directory with your database credentials:
        ```
        MYSQL_USER=your_user
        MYSQL_PASSWORD=your_password
        MYSQL_DATABASE=bizflow
        ```
    *   Install the required Python packages:
        ```bash
        pip install -r src/requirements.txt
        ```

3.  **Running the Application:**
    ```bash
    python src/app.py
    ```
    The application will be available at `http://localhost:9999`.

4.  **Running Tests:**
    ```bash
    pytest
    ```

### Docker

1.  **Build and Run:**
    ```bash
    docker-compose up -d --build
    ```

## Development Conventions

*   **Clean Architecture:** The project follows a clean architecture pattern, separating concerns into four main layers:
    *   `domain`: Contains the core business logic and entities.
    *   `services`: Orchestrates the business logic.
    *   `infrastructure`: Handles external concerns like databases and third-party services.
    *   `api`: Exposes the application through a RESTful API.
*   **Coding Style:** The codebase follows the PEP 8 style guide for Python.
*   **API Design:** The API is designed to be RESTful, with clear and consistent naming conventions.
*   **Error Handling:** The application uses custom exception classes to handle business-specific errors.
*   **Dependency Management:** The project uses a `requirements.txt` file to manage Python dependencies. While there is a `dependency_container.py` file, it is not currently in use.
*   **Database Migrations:** The project uses Flask-Migrate to manage database schema changes.
