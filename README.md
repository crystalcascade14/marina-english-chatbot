# Marina English Chatbot

An AI-powered chatbot built for an English teacher's website.

The chatbot helps website visitors find information about Marina's English lessons, available courses, English levels, teaching materials, exam preparation, lesson policies, and what to expect from classes.

It is integrated into an existing Tilda website and uses a custom knowledge base to answer questions specifically about Marina's teaching services.

## Live Website

The chatbot is integrated into:

**englishwmarina.com**

## Features

- AI-powered question answering
- Custom knowledge base stored in Supabase
- Information about General English courses from B1 to C2
- Information about books and teaching materials
- IELTS preparation information
- FCE / B2 First preparation information
- CAE / C1 Advanced preparation information
- Business English course information
- English for IT course information
- American English course information
- Job Interview course information
- Lesson format and scheduling information
- Lesson and cancellation policy information
- Responsive chatbot interface integrated into Tilda

## Architecture

The application uses the following architecture:

```text
Website Visitor
       ↓
Tilda Website
       ↓
JavaScript Chat Interface
       ↓
FastAPI Backend
       ↓
     Render
       ↓
 ┌─────────────┐
 ↓             ↓
Supabase     OpenAI API
 ↓             ↓
Knowledge    AI-generated
Base         Response
 └──────┬──────┘
        ↓
FastAPI
        ↓
Tilda Chat Interface
        ↓
Website Visitor
```

### Components

- **Tilda** — hosts the public website and chatbot interface
- **JavaScript** — sends questions from the chatbot interface to the backend and displays responses
- **FastAPI** — handles API requests, validation, chatbot logic, and communication with external services
- **Render** — hosts the FastAPI backend and makes it accessible over the internet
- **Supabase** — stores the chatbot's custom knowledge base
- **OpenAI API** — generates responses using information retrieved from the knowledge base
- **GitHub** — provides source control and connects the project to automatic deployment on Render

## How It Works

When a visitor asks a question on the website:

1. The visitor enters a question in the chatbot.
2. JavaScript sends the question to the FastAPI `/chat` endpoint.
3. FastAPI validates the request.
4. The backend searches the Supabase knowledge base for relevant information.
5. Relevant knowledge is included as context for the AI model.
6. The OpenAI API generates an answer based on that context.
7. FastAPI returns the answer to the website.
8. JavaScript displays the answer in the chatbot.

This allows the chatbot to answer questions specifically about Marina's lessons and services rather than functioning as a general-purpose chatbot.

## Security

The application includes several security controls.

### API Key Protection

API keys and other credentials are stored as server-side environment variables.

Sensitive values are not included in the frontend code and are excluded from Git using `.gitignore`.

The OpenAI API key is therefore never sent to website visitors or committed to this public repository.

### Supabase Row Level Security

Row Level Security (RLS) is enabled in Supabase.

The chatbot knowledge base currently allows public read access while preventing public users from modifying the stored knowledge.

Additional user-specific RLS policies will be implemented for private conversation data.

### CORS Protection

The FastAPI backend restricts browser requests to approved website origins.

This prevents arbitrary websites from directly using the chatbot API through browser-based requests.

### Input Validation

Chatbot questions are validated by the backend.

Input is:

- stripped of unnecessary surrounding whitespace
- rejected if empty
- limited to a maximum of 300 characters

### Rate Limiting

The `/chat` API endpoint uses IP-based rate limiting.

Clients are limited to a defined number of requests per minute. Requests exceeding the limit receive an HTTP `429 Too Many Requests` response.

This helps reduce automated abuse, excessive OpenAI API usage, and basic denial-of-service attempts.

### Error Handling

Unexpected backend errors return a generic error response rather than exposing internal application details.

This reduces the risk of leaking information about the backend, services, or configuration.

### Injection Testing

The chatbot has been tested with:

- prompt injection attempts
- SQL injection-style input
- unauthorized Supabase write attempts
- excessive API requests

User input is not directly incorporated into raw SQL queries.

## API

The FastAPI backend exposes the main chatbot endpoint:

```text
POST /chat
```

Example request:

```json
{
  "question": "What books do you use for FCE?"
}
```

Example response structure:

```json
{
  "question": "What books do you use for FCE?",
  "answer": "..."
}
```

The backend validates the request, retrieves relevant information from the knowledge base, communicates with the OpenAI API, and returns the generated answer.

## Deployment

The backend source code is stored in GitHub.

Changes follow this deployment workflow:

```text
Local Development
       ↓
Git Commit
       ↓
GitHub
       ↓
Render Auto-Deploy
       ↓
Live FastAPI Backend
```

Render automatically detects new commits pushed to the main branch and deploys the updated backend.

The public Tilda website communicates with the deployed backend through HTTPS.

## Technology Stack

- Python
- FastAPI
- OpenAI API
- Supabase
- PostgreSQL
- JavaScript
- HTML/CSS
- Tilda
- Render
- Git
- GitHub

## Current Development

The core chatbot is live and functional.

Current functionality includes:

- Live website integration
- AI-generated responses
- Custom knowledge retrieval
- Supabase database integration
- FastAPI backend
- Production deployment
- Input validation
- CORS restrictions
- Rate limiting
- Error handling
- Basic prompt injection and SQL injection testing

Planned additions include:

- User authentication
- Conversation history
- User-specific conversation storage
- Row Level Security for private user data
- Guided chatbot navigation for books, levels, exam preparation, specialized courses, and lessons
- Additional authorization and security testing
- Further refinement of chatbot responses

## Project Purpose

This project was developed as a secure AI web application project.

It combines AI functionality with web development, database integration, API design, deployment, and application security concepts.

The project is being developed incrementally, with security controls tested throughout the development process.

## Author

**crystalcascade14**

Cybersecurity student and English language instructor.