# Drunagor Companion App Backend

Welcome to the Drunagor Companion App backend! This project is designed to provide a robust and scalable backend for the Drunagor Companion App using Docker containers.

## Table of Contents

- [Overview](#overview)
- [Technologies](#technologies)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [License](#license)

## Overview

The Drunagor Companion App backend serves as the server-side component of the application. It interacts with various databases and services to provide a seamless experience for users.

## Technologies

This project utilizes the following technologies:

- **Python**: The primary programming language for backend development.
- **MongoDB**: A NoSQL database used for storing unstructured data.
- **MySQL**: A relational database used for structured data management.
- **NGINX**: A web server used to manage requests and serve static files.
- **Docker**: Containerization technology to simplify setup and deployment.

## Setup Instructions

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/Esterci/dback_end_drunagor.git
   cd back_end_drunagor
   ```

3. Build and run the Docker containers:
   ```bash
   bash build.sh
   docker-compose up
   ```

4. Access the application at `http://localhost:5000`.

## API Documentation

Documentation for the API endpoints can be found at `http://localhost:5000`. You can use tools like Postman or cURL to interact with the API.

## Deployment

To deploy the application in a production environment:

1. Ensure you have the necessary production configurations in your `.env` file.
2. Build and run the containers in detached mode:
   ```bash
   bash deploy.sh
   ```

3. Monitor the logs:
   ```bash
   docker-compose logs -f
   ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---
