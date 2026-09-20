import os
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load structural variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    raise ValueError("CRITICAL ERROR: 'ASSEMBLYAI_API_KEY' is missing from the environment configuration.")

app = FastAPI(title="EchoLogic AI - AssemblyAI Voice Agent Backend")

# Permit seamless frontend communication cross-origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_origins_regex=None,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structural class schema for explicit webhook data validation
class ToolFulfillmentPayload(BaseModel):
    message_id: str
    agent_id: str
    tool: str
    arguments: dict

@app.post("/api/token")
async def generate_assemblyai_token():
    """
    Generates a secure, temporary authentication token from AssemblyAI 
    to pass down safely to the frontend client browser layer.
    """
    url = "https://assemblyai.com"
    headers = {
        "Authorization": ASSEMBLYAI_API_KEY,
        "Content-Type": "application/json"
    }
    # Token parameters configure standard 5-minute validity window
    data = {"expires_in": 300}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"AssemblyAI Token Generation Failed: {response.text}"
                )
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal connection failure: {str(e)}"
            )

@app.post("/api/fulfillment")
async def handle_agent_tools(payload: ToolFulfillmentPayload):
    """
    Central Fulfillment Engine. Captures tool invocations issued 
    by AssemblyAI when specific rules evaluate successfully.
    """
    tool_name = payload.tool
    args = payload.arguments
    
    print(f"[ACTION] Processing real-time field tool invocation: '{tool_name}'")
    print(f"[ARGUMENTS] Parsed properties: {args}")
    
    try:
        if tool_name == "log_hazardous_incident":
            # Extract arguments structured by our schema
            severity = args.get("severity")
            component = args.get("system_component")
            description = args.get("description")
            requires_dispatch = args.get("requires_dispatch", False)
            
            # TODO: Integrate your structural database/Airtable API route here
            mock_db_response = {
                "status": "SUCCESS",
                "logged_incident_id": "HZ-90412",
                "message": f"Hazard ticket raised for {component} at {severity} tier."
            }
            
            # Return strict confirmation text for the agent to say back to the user
            return JSONResponse(content={
                "output": f"Incident successfully registered into system logs. Identification token is item code {mock_db_response['logged_incident_id']}. Emergency dispatch status flag evaluated to {requires_dispatch}."
            })
            
        elif tool_name == "update_dispatch_status":
            ticket_id = args.get("ticket_id")
            status_update = args.get("status")
            notes = args.get("notes", "No extra field remarks reported.")
            
            mock_crm_response = {
                "status": "UPDATED",
                "ticket_id": ticket_id,
                "current_state": status_update
            }
            
            return JSONResponse(content={
                "output": f"Work order tracking token {ticket_id} moved to status layer {status_update}."
            })
            
        elif tool_name == "query_system_telemetry":
            asset_id = args.get("asset_id")
            metric_type = args.get("metric_type", "ALL")
            
            # Simulating live database state lookups hands-free
            mock_telemetry_data = {
                "TEMPERATURE": "74.2 degrees Celsius",
                "PRESSURE": "142 PSI",
                "VOLTAGE": "230 Volts"
            }
            
            resolved_speech_output = f"Telemetry stream scan completed for asset node {asset_id}. "
            if metric_type == "ALL":
                resolved_speech_output += f"Current temperature reads at {mock_telemetry_data['TEMPERATURE']}, system line pressure stands at {mock_telemetry_data['PRESSURE']}, and operational electrical load is at {mock_telemetry_data['VOLTAGE']}."
            else:
                resolved_speech_output += f"Requested metric {metric_type} evaluates to {mock_telemetry_data.get(metric_type, 'UNKNOWN ERROR')}."
                
            return JSONResponse(content={"output": resolved_speech_output})
            
        else:
            return JSONResponse(
                status_code=422,
                content={"output": "Execution handler route for this specific workspace tool is undefined."}
            )
            
    except Exception as error:
        print(f"[ERROR] Tool execution failed: {str(error)}")
        return JSONResponse(
            status_code=500,
            content={"output": "Workspace fulfillment systems encountered an database interface error processing this update."}
        )

# Serving static dashboard layouts out of the adjacent template folders if launched directly
try:
    app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), ".")), name="static")
except Exception:
    pass

if __name__ == "__main__":
    import uvicorn
    port_config = int(os.getenv("PORT", 8000))
    print(f"Initializing EchoLogic AI Pipeline Engine on port {port_config}...")
    uvicorn.run("server:app", host=os.getenv("HOST", "0.0.0.0"), port=port_config, reload=True)
