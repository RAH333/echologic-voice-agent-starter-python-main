import os
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Try loading production environment setups
# load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
# Change the relative path to look one directory up instead of two
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# Global FastAPI handler engine instance targeted by Vercel deployment configurations
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

@app.post("/api/token")
async def generate_assemblyai_token():
    if not ASSEMBLYAI_API_KEY:
        raise HTTPException(status_code=500, detail="Missing API Key config authentication layer.")
        
    url = "https://assemblyai.com"
    headers = {"Authorization": ASSEMBLYAI_API_KEY, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"expires_in": 300}, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
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

# Mount the static directory safely to avoid breaking serverless Vercel engine routines
try:
    static_path = os.path.join(os.path.dirname(__file__), ".")
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
except Exception:
    pass

# Protected driver configuration execution wrapper layout for local Termux checks
if __name__ == "__main__":
    import uvicorn
    port_config = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host=os.getenv("HOST", "0.0.0.0"), port=port_config, reload=True)
