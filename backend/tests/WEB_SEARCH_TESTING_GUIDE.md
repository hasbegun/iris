# Web Search Feature - Complete Testing Guide

This guide will walk you through testing the new web search feature from scratch.

## Prerequisites

- Conda environment `iris-ml` activated
- Project directory: `/Users/innox/projects/iris`

## 🚀 Step 1: Start All Services

### 1.1 Start SearXNG (Web Search Engine)
```bash
cd /Users/innox/projects/iris
docker-compose up -d searxng
```

**Verify SearXNG is running:**
```bash
curl -s http://localhost:9090/ | head -5
```
✅ You should see HTML content from SearXNG

### 1.2 Start ML Service (YOLO Object Detection)
```bash
cd /Users/innox/projects/iris/ml-service
conda activate iris-ml
python run.py
```

**Expected output:**
- Loading YOLO models...
- Server running on port 9001

**Keep this terminal running** and open a new terminal for the next step.

### 1.3 Start Backend Service (Main API)
```bash
cd /Users/innox/projects/iris/backend
conda activate iris-ml
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

**Expected output:**
- Initializing vision agent with model: qwen2.5-coder:32b
- ✅ Vision agent (ReAct pattern) initialized successfully
- Application startup complete.
- Uvicorn running on http://0.0.0.0:9000

**Keep this terminal running**.

---

## ✅ Step 2: Verify All Services Are Running

Open a new terminal:

```bash
# Check SearXNG
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/
# Should return: 200

# Check ML Service
curl http://localhost:9001/health
# Should return: {"status":"healthy"}

# Check Backend Service
curl http://localhost:9000/api/health
# Should return: {"status":"healthy"}
```

If all return healthy/200, you're ready to test!

---

## 🧪 Step 3: Run Verification Tests

### Test 1: Search Service (Foundation Layer)
```bash
cd /Users/innox/projects/iris/backend/tests
python test_search_service.py
```

**What this tests:**
- SearXNG connection
- Search query execution
- Result parsing and formatting

**Expected result:** ✅ 4/4 tests PASSED

---

### Test 2: Web Search Tool (LangChain Tool Layer)
```bash
python test_web_search_tool.py
```

**What this tests:**
- LangChain tool interface
- Tool can be invoked with queries
- Results are properly formatted
- Tool metadata is correct

**Expected result:** ✅ 4/4 tests PASSED

---

### Test 3: Agent Integration (Agent Has Web Search)
```bash
python test_agent_web_search_integration.py
```

**What this tests:**
- web_search tool is available in agent's toolset
- Agent can access the tool

**Expected result:** ✅ PASS - web_search tool successfully integrated

---

## 🎯 Step 4: Manual Testing - Standalone Web Search

### Test 4.1: Simple Web Search via API

```bash
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "session_id": "test-session-001"
  }'
```

**What should happen:**
1. Agent receives the query
2. Agent decides to use web_search tool
3. SearXNG performs web search
4. Agent returns search results

**Expected response:**
```json
{
  "status": "success",
  "query": "What is the capital of France?",
  "response": "Search results for 'capital of France':\n\n1. Paris - Wikipedia\n   URL: https://en.wikipedia.org/wiki/Paris\n   Paris is the capital and most populous city of France...",
  "session_id": "test-session-001"
}
```

### Test 4.2: Current Information Query

```bash
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest developments in AI?",
    "session_id": "test-session-002"
  }'
```

**Expected:** Agent searches the web and returns recent AI news/information.

---

## 🎨 Step 5: Manual Testing - Vision + Web Search Integration

This is the **KEY FEATURE** - combining object detection with web search!

### Test 5.1: Detect Object → Ask About It

**Step 1:** Upload an image with a car (or any object)
```bash
# Upload a test image (replace with your image path)
curl -X POST http://localhost:9000/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/car-image.jpg" \
  -F "session_id=vision-test-001"
```

**Step 2:** Detect objects in the image
```bash
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What objects are in this image?",
    "session_id": "vision-test-001"
  }'
```

**Expected response:** "Found 1 car in the image." (or similar)

**Step 3:** Ask contextual question about detected object
```bash
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does it do?",
    "session_id": "vision-test-001"
  }'
```

**What should happen:**
1. Agent remembers "car" was detected in previous query
2. Agent constructs search query: "what is a car used for" or similar
3. Agent uses web_search tool
4. Returns information about cars from web search

**Expected response:** Information about cars (transportation, uses, etc.) from web search.

---

### Test 5.2: Another Example - Bottle

```bash
# 1. Upload image with bottle
curl -X POST http://localhost:9000/api/upload \
  -F "file=@/path/to/bottle-image.jpg" \
  -F "session_id=vision-test-002"

# 2. Detect bottle
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all objects",
    "session_id": "vision-test-002"
  }'

# 3. Ask about it
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current status of plastic bottles in recycling?",
    "session_id": "vision-test-002"
  }'
```

**Expected:** Agent searches web for current information about plastic bottle recycling.

---

## 📊 Test Results Checklist

Mark each test as you complete it:

- [ ] **Service Health Checks**
  - [ ] SearXNG (port 9090)
  - [ ] ML Service (port 9001)
  - [ ] Backend Service (port 9000)

- [ ] **Automated Tests**
  - [ ] test_search_service.py (4/4)
  - [ ] test_web_search_tool.py (4/4)
  - [ ] test_agent_web_search_integration.py (PASS)

- [ ] **Manual API Tests**
  - [ ] Standalone web search
  - [ ] Current information query
  - [ ] Vision → Object detection
  - [ ] Vision → Web search about detected object

---

## 🐛 Troubleshooting

### SearXNG not responding (port 9090)
```bash
docker-compose restart searxng
# Wait 5 seconds
curl http://localhost:9090/
```

### ML Service fails to start
- Check Ollama is running: `ollama list`
- Verify YOLO models are downloaded
- Check port 9001 is not in use: `lsof -i:9001`

### Backend service errors
- Check `.env` file has correct settings:
  - `SEARXNG_URL=http://localhost:9090`
  - `SEARXNG_ENABLED=true`
- Verify conda environment: `conda activate iris-ml`
- Check logs for specific errors

### Web search returns no results
- Test SearXNG directly: `curl "http://localhost:9090/search?q=test&format=json"`
- Check SearXNG logs: `docker logs iris-searxng`

---

## 🎯 Success Criteria

Your web search feature is working correctly if:

1. ✅ All automated tests pass
2. ✅ Agent can answer factual queries via web search
3. ✅ Agent can detect objects in images
4. ✅ Agent can search the web for information about detected objects
5. ✅ Responses are relevant and well-formatted

---

## 📝 Example Complete Test Flow

```bash
# Terminal 1: Start SearXNG
cd /Users/innox/projects/iris
docker-compose up -d searxng

# Terminal 2: Start ML Service
cd /Users/innox/projects/iris/ml-service
conda activate iris-ml
python run.py

# Terminal 3: Start Backend
cd /Users/innox/projects/iris/backend
conda activate iris-ml
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

# Terminal 4: Run Tests
cd /Users/innox/projects/iris/backend/tests
python test_search_service.py
python test_web_search_tool.py
python test_agent_web_search_integration.py

# Test web search
curl -X POST http://localhost:9000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python programming?", "session_id": "test-001"}'
```

That's it! You now have a complete vision AI system with web search integration! 🎉
