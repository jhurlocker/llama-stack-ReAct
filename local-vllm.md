# Local Development Setup

This guide provides instructions for setting up the Llama Stack React Agent locally using:
- **Ollama** for model serving
- **Llama Stack** in a container
- **HR-API** as a Node.js application
- **React-Agent** as a Python application

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.9+ and pip
- Git



```bash
# Test the model
curl https://route-marginal-hippopotamus-modelcar-blog.apps.dev.rhoai.rh-aiservices-bu.com/v1/models 
```

## 2. Llama Stack Container Setup

### Run Llama Stack with Podman

```bash
# Remove any existing container
podman rm -f llama-stack

# Run Llama Stack container
podman run -d \
  --name llama-stack \
  -p 11011:11011 \
  -e LLAMA_STACK_PORT=11011 \
  -e INFERENCE_PROVIDER=vllm \
  -e VLLM_URL=https://route-marginal-hippopotamus-modelcar-blog.apps.dev.rhoai.rh-aiservices-bu.com/v1  \
  -e INFERENCE_MODEL=llama3-2-3b \
  llamastack/distribution-remote-vllm:0.2.9


# Check logs
podman logs -f llama-stack

## 3. HR-API Node.js Application

### Setup HR-API

```bash
# Navigate to hr-api directory
cd hr-api

# Install dependencies
npm install

# Create environment file
cat > .env << EOF
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:8501
LOG_LEVEL=info
EOF

# Start the application
npm start

# For development with auto-reload
npm run dev
```

### Test HR-API

```bash
# Test employee data
curl http://localhost:3000/api/v1/employees

# Test vacation balance
curl http://localhost:3000/api/v1/vacations/EMP001

# Test API documentation
open http://localhost:3000/api-docs

# Test health check
curl http://localhost:3000/health
```

### Available HR-API Endpoints

- `GET /api/v1/employees` - List all employees
- `GET /api/v1/employees/:id` - Get employee by ID
- `GET /api/v1/vacations` - List all vacation requests
- `GET /api/v1/vacations/:employee_id` - Get vacation balance for employee
- `POST /api/v1/vacations` - Create vacation request
- `GET /api/v1/jobs` - List job openings
- `GET /api/v1/performance/:employee_id` - Get performance data
- `GET /health` - Health check endpoint
- `GET /api-docs` - API documentation

## 4. Custom MCP Server

### Setup Custom MCP Server

```bash
# Navigate to custom-mcp-server directory
cd custom-mcp-server

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
HR_API_BASE_URL=http://localhost:3000
HR_API_KEY=test-api-key
PORT=8000
EOF
```

### Run the Custom MCP Server

```bash
# Start the MCP server
python server.py

# The server will run on port 8000 by default
# You can test it with:
curl http://localhost:8000/health
```

### Test Custom MCP Server

```bash
# Test health endpoint
curl http://localhost:8000/health


### Register MCP Server with Llama Stack

```bash
# Register the custom-hr MCP server with Llama Stack
curl -X POST -H "Content-Type: application/json" \
--data \
'{ "provider_id" : "model-context-protocol", "toolgroup_id" : "mcp::hr-api-tools", "mcp_endpoint" : { "uri" : "http://host.docker.internal:8000/sse"}}' \
 http://localhost:11011/v1/toolgroups

# Verify registration by listing toolgroups
curl http://localhost:11011/v1/toolgroups
```

### Available MCP Tools

The custom MCP server provides these tools for AI agents:

1. **get_employees** - Get list of employees with optional filtering
2. **get_employee** - Get detailed information about a specific employee
3. **get_vacation_requests** - Get vacation requests with filtering
4. **get_vacation_balance** - Get vacation balance for an employee
5. **submit_vacation_request** - Submit a new vacation request
6. **get_job_postings** - Get list of job postings with filtering
7. **get_job_details** - Get detailed job information
8. **get_performance_reviews** - Get performance reviews with filtering
9. **get_performance_analytics** - Get performance analytics and metrics

## 5. React-Agent Python Application

### Setup React-Agent

```bash
# Navigate to react-agent directory
cd react-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
LLAMA_STACK_URL=http://localhost:11011
HR_API_URL=http://localhost:3000
LOG_LEVEL=INFO
DEBUG=true
EOF
```

### Run the React-Agent

```bash
# Start the Streamlit application
streamlit run streamlit_app.py --server.port 8501

# Or run the simple agent example
python run_example.py
```

### Test React-Agent

1. Open your browser to `http://localhost:8501`
2. Try these example queries:
   - "What is the vacation balance for employee EMP001?"
   - "If user EMP001 has enough remaining vacation days, book two days off for July 2nd and 3rd, 2025"
   - "Check if EMP001 has any vacation days left, and if so, suggest when they might want to use them"

## 6. Complete Local Stack Startup

### Start All Services

```bash
# 1. Start Ollama (in terminal 1)
ollama serve

# 2. Start HR-API (in terminal 2)
cd hr-api
npm start

# 3. Start Custom MCP Server (in terminal 3)
cd custom-mcp-server
source venv/bin/activate
python server.py

# 4. Start Llama Stack (in terminal 4)
podman run -d --name llama-stack -p 11011:11011 -e LLAMA_STACK_PORT=11011 -e INFERENCE_PROVIDER=ollama -e OLLAMA_URL=http://host.containers.internal:11434 -e INFERENCE_MODEL=llama3.2:3b llamastack/distribution-ollama:latest

# 5. Start React-Agent (in terminal 5)
cd react-agent
source venv/bin/activate
streamlit run streamlit_app.py
```

### Service URLs

- **Ollama**: http://localhost:11434
- **HR-API**: http://localhost:3000
- **Custom MCP Server**: http://localhost:8000
- **Llama Stack**: http://localhost:11011
- **React-Agent**: http://localhost:8501

## 6. Development Tips

### Debugging

```bash
# Check Ollama status
ollama ps

# Check HR-API logs
npm run dev  # Shows detailed logs

# Check Custom MCP Server logs
python server.py  # Shows debug output

# Check Llama Stack logs
podman logs llama-stack

# Check React-Agent logs
streamlit run streamlit_app.py --logger.level debug
```

### Configuration

#### Ollama Model Configuration
```bash
# Use different model
ollama pull llama3.2:1b  # Smaller model
ollama pull llama3.2:7b  # Larger model

# Restart Llama Stack with new model
podman restart llama-stack
```

#### HR-API Configuration
Edit `hr-api/.env`:
```env
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:8501
LOG_LEVEL=debug
```

#### Custom MCP Server Configuration
Edit `custom-mcp-server/.env`:
```env
HR_API_BASE_URL=http://localhost:3000
HR_API_KEY=test-api-key
PORT=8000
```

#### React-Agent Configuration
Edit `react-agent/.env`:
```env
LLAMA_STACK_URL=http://localhost:11011
HR_API_URL=http://localhost:3000
LOG_LEVEL=DEBUG
STREAMLIT_SERVER_PORT=8501
```

## 7. Troubleshooting

### Common Issues

1. **Ollama Connection Issues**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Restart Ollama
   ollama serve
   ```

2. **Llama Stack Connection Issues**
   ```bash
   # Check container logs
   podman logs llama-stack
   
   # Restart container
   podman restart llama-stack
   ```

3. **HR-API Issues**
   ```bash
   # Check Node.js version
   node --version  # Should be 18+
   
   # Clear npm cache
   npm cache clean --force
   npm install
   ```

4. **Custom MCP Server Issues**
   ```bash
   # Check Python version
   python --version  # Should be 3.9+
   
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   
   # Check if HR-API is accessible
   curl http://localhost:3000/health
   ```

5. **React-Agent Issues**
   ```bash
   # Check Python version
   python --version  # Should be 3.9+
   
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

### Port Conflicts

If ports are already in use:
```bash
# Find process using port
lsof -i :11434  # Ollama
lsof -i :3000   # HR-API
lsof -i :8000   # Custom MCP Server
lsof -i :11011  # Llama Stack
lsof -i :8501   # React-Agent

# Kill process
kill -9 <PID>
```

## 8. Production Considerations

For production deployment:

1. **Security**: Configure proper CORS, authentication, and rate limiting
2. **Performance**: Use production-grade model serving with vLLM or similar
3. **Scaling**: Consider using Kubernetes for container orchestration
4. **Monitoring**: Add logging, metrics, and health checks
5. **Persistence**: Use proper databases instead of in-memory data

## 9. Next Steps

- Customize the HR-API endpoints for your specific use case
- Extend the React-Agent with additional reasoning capabilities
- Add authentication and authorization
- Implement proper error handling and logging
- Add unit and integration tests
- Set up CI/CD pipelines