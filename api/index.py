import os
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment configuration fallbacks
env_path = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

# Dynamic internal mapping check for the hackathon deployment script string
if not AGENT_ID:
    AGENT_ID = os.getenv("AGENT_ID_ECHOLOGIC_FIELD_WORKSPACE")

app = FastAPI(title="EchoLogic AI Workspace Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolFulfillmentPayload(BaseModel):
    message_id: str
    agent_id: str
    tool: str
    arguments: dict

@app.get("/")
async def serve_frontend_homepage():
    """
    Directly serves the HTML file to ensure Vercel 
    handles the index layout properly without mounting errors.
    """
    html_path = os.path.join(os.path.dirname(__file__), '../public/index.html')
    if not os.path.exists(html_path):
        return HTMLResponse(content="<h1>EchoLogic Interface Asset Loading Error</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.get("/agent")
@app.get("/api/agent")
async def get_agent_details():
    return {
        "id": AGENT_ID or "agent_76948b520894429ab188bb6253f1b924",
        "name": "EchoLogic AI Field Workspace Agent",
        "description": "Autonomous voice workspace helper context for technical field dispatches."
    }

@app.post("/api/token")
async def generate_assemblyai_token():
    # Force localized fallback fallback if Vercel dashboard sync is pending
    active_key = ASSEMBLYAI_API_KEY or "9fde391556fd42abbf2e441bad5b43f5"
    active_agent = AGENT_ID or "agent_76948b520894429ab188bb6253f1b924"
        
    url = "https://assemblyai.com"
    headers = {
        "Authorization": active_key, 
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"expires_in": 300}, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            token_data = response.json()
            token_data["agent_id"] = active_agent
            return token_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fulfillment")
async def handle_agent_tools(payload: ToolFulfillmentPayload):
    tool_name = payload.tool
    args = payload.arguments
    
    try:
        if tool_name == "log_hazardous_incident":
            component = args.get("system_component", "Unknown component")
            severity = args.get("severity", "LOW")
            requires_dispatch = args.get("requires_dispatch", False)
            return JSONResponse(content={
                "output": f"Incident successfully registered into system logs. System flag logged for {component} at {severity} priority level. Dispatch active evaluated to {requires_dispatch}."
            })
            
        elif tool_name == "update_dispatch_status":
            ticket_id = args.get("ticket_id")
            status_update = args.get("status")
            return JSONResponse(content={
                "output": f"Work order tracking status token {ticket_id} updated to operational status level {status_update}."
            })
            
        elif tool_name == "query_system_telemetry":
            asset_id = args.get("asset_id")
            metric_type = args.get("metric_type", "ALL")
            
            mock_telemetry = {"TEMPERATURE": "74.2°C", "PRESSURE": "142 PSI", "VOLTAGE": "230V"}
            speech = f"Telemetry stream scan completed for asset node {asset_id}. "
            if metric_type == "ALL":
                speech += f"Temperature is {mock_telemetry['TEMPERATURE']}, pressure is {mock_telemetry['PRESSURE']}, and electrical load is {mock_telemetry['VOLTAGE']}."
            else:
                speech += f"Requested metric {metric_type} is {mock_telemetry.get(metric_type, 'UNKNOWN')}."
            return JSONResponse(content={"output": speech})
            
        return JSONResponse(status_code=422, content={"output": "Workspace tool path matches no current active system routing rules."})
    except Exception as error:
        return JSONResponse(status_code=500, content={"output": f"Fulfillment subsystem critical operational error: {str(error)}"})
        
