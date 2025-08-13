from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import re

app = FastAPI(title="Simple Chatbot API Router with GUI")

# ------------------------
# Simulated chatbot actions
# ------------------------

def getWeather(location: str) -> str:
    location = location.title().strip()
    # Simulated forecast
    return f"Weather for {location}: 31°C, partly cloudy, light breeze."


def getJoke() -> str:
    return "Why did the developer go broke? Because they used up all their cache!"


def addNumbers(num1: float, num2: float) -> float:
    return num1 + num2


# ------------------------
# NLP / Intent Recognition
# ------------------------

INTENT_KEYWORDS = {
    "weather": ["weather", "forecast", "temperature"],
    "joke": ["joke", "funny", "make me laugh"],
    "add": ["add", "sum", "plus", "+"],
}


def identify_intent(text: str) -> str:
    t = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(k in t for k in keywords):
            return intent
    return "unknown"


def extract_params(intent: str, text: str):
    if intent == "weather":
        # Try to find a city after prepositions like "in", "at", "for"
        m = re.search(r"(?:in|at|for)\s+([a-zA-Z\s.-]{2,})$", text.strip(), flags=re.I)
        if not m:
            # fallback: last word(s) that look like a place name (letters and spaces)
            m = re.search(r"([A-Za-z][A-Za-z\s.-]{1,})$", text.strip())
        city = m.group(1).strip() if m else "your city"
        return {"location": city}

    if intent == "add":
        nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)
        if len(nums) >= 2:
            return {"num1": float(nums[0]), "num2": float(nums[1])}
        else:
            return {"error": "Please provide two numbers to add (e.g., 'add 12 and 7')."}

    return {}


def route_query(query: str):
    intent = identify_intent(query)
    params = extract_params(intent, query)

    result = None
    error = None

    if intent == "weather":
        location = params.get("location", "your city")
        result = getWeather(location)

    elif intent == "joke":
        result = getJoke()

    elif intent == "add":
        if "error" in params:
            error = params["error"]
        else:
            result = addNumbers(params["num1"], params["num2"])

    else:
        error = "Sorry, I couldn't understand. Try asking for weather, a joke, or to add numbers."

    return {
        "query": query,
        "intent": intent,
        "parameters": params,
        "result": result,
        "error": error,
    }


# ------------------------
# API
# ------------------------

class QueryIn(BaseModel):
    query: str


@app.post("/route")
async def route_endpoint(payload: QueryIn):
    return JSONResponse(route_query(payload.query))


# ------------------------
# Minimal GUI (served by FastAPI)
# ------------------------

INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Chatbot API Router • Demo GUI</title>
  <style>
    :root { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }
    body { margin: 0; background: #0f172a; color: #e2e8f0; }
    .wrap { max-width: 900px; margin: 0 auto; padding: 24px; }
    .card { background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 20px; box-shadow: 0 10px 24px rgba(0,0,0,.25); }
    h1 { margin: 0 0 8px; font-size: 24px; }
    p.muted { color: #94a3b8; margin-top: 0; }
    .row { display: flex; gap: 12px; margin-top: 16px; }
    input[type=text] { flex: 1; padding: 14px 16px; border-radius: 12px; border: 1px solid #334155; background: #0b1220; color: #e2e8f0; }
    button { padding: 14px 18px; border-radius: 12px; border: 1px solid #3b82f6; background: #1d4ed8; color: white; cursor: pointer; font-weight: 600; }
    button:disabled { opacity: .6; cursor: not-allowed; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; margin-top: 16px; }
    .panel { background: #0b1220; border: 1px solid #1f2937; border-radius: 12px; padding: 12px; min-height: 120px; }
    .panel h3 { margin: 0 0 6px; font-size: 14px; color: #93c5fd; }
    pre, code { white-space: pre-wrap; word-break: break-word; }
    .foot { margin-top: 14px; color: #94a3b8; font-size: 12px; }
    .examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .chip { font-size: 12px; padding: 6px 10px; border-radius: 999px; border: 1px solid #334155; background: #0b1220; cursor: pointer; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"card\">
      <h1>Simple Chatbot API Router</h1>
      <p class=\"muted\">Ask for weather, a joke, or ask me to add two numbers. The router will detect intent, extract parameters, and show the result.</p>

      <div class=\"examples\">
        <span class=\"chip\" data-eg=\"What's the weather in Mumbai?\">What's the weather in Mumbai?</span>
        <span class=\"chip\" data-eg=\"Tell me a joke\">Tell me a joke</span>
        <span class=\"chip\" data-eg=\"add 12 and 7\">add 12 and 7</span>
        <span class=\"chip\" data-eg=\"Can you sum 3.5 plus 6?\">Can you sum 3.5 plus 6?</span>
      </div>

      <div class=\"row\">
        <input id=\"q\" type=\"text\" placeholder=\"Type a query...\" />
        <button id=\"go\">Run</button>
      </div>

      <div class=\"grid\">
        <div class=\"panel\">
          <h3>Detected Intent</h3>
          <pre id=\"intent\">—</pre>
        </div>
        <div class=\"panel\">
          <h3>Extracted Parameters</h3>
          <pre id=\"params\">—</pre>
        </div>
        <div class=\"panel\" style=\"grid-column: span 2;\">
          <h3>Result</h3>
          <pre id=\"result\">—</pre>
        </div>
      </div>

      <div class=\"foot\">Demo purpose only. Router uses simple keyword matching and regex extraction.</div>
    </div>
  </div>

<script>
const $ = (id) => document.getElementById(id);
const q = $("q");
const go = $("go");
const intent = $("intent");
const params = $("params");
const result = $("result");

document.querySelectorAll('.chip').forEach(el => {
  el.addEventListener('click', () => { q.value = el.dataset.eg; q.focus(); });
});

async function run(){
  const query = q.value.trim();
  if(!query) return;
  go.disabled = true;
  intent.textContent = '…';
  params.textContent = '…';
  result.textContent = '…';
  try{
    const res = await fetch('/route', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query}) });
    const data = await res.json();
    intent.textContent = data.intent || 'unknown';
    const paramCopy = {...data.parameters};
    if(paramCopy && typeof paramCopy === 'object'){
      // Round numbers for display
      if('num1' in paramCopy) paramCopy.num1 = Number(paramCopy.num1);
      if('num2' in paramCopy) paramCopy.num2 = Number(paramCopy.num2);
    }
    params.textContent = JSON.stringify(paramCopy, null, 2);
    result.textContent = data.error ? `Error: ${data.error}` : (typeof data.result === 'number' ? String(data.result) : data.result);
  } catch(e){
    result.textContent = 'Failed: ' + e.message;
  } finally {
    go.disabled = false;
  }
}

go.addEventListener('click', run);
q.addEventListener('keydown', (e)=>{ if(e.key==='Enter') run(); });
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(_: Request):
    return HTMLResponse(INDEX_HTML)


# ------------------------
# Local dev entrypoint
# ------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
