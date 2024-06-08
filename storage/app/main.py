import os
import argparse
import logging.config
import uvicorn
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from utils.logging_config import get_logging_config
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_403_FORBIDDEN
import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


def get_args():
    parser = argparse.ArgumentParser(description="FastAPI file upload and download app")
    parser.add_argument("--data-dir", type=str, default="../data", help="Directory to store data files")
    parser.add_argument("--log-dir", type=str, default="../logs", help="Directory to store log files")
    parser.add_argument("--api-key", type=str, default="secret", help="API key for authentication")
    args, unknown = parser.parse_known_args()
    return args


args = get_args()

templates = Jinja2Templates(directory="templates")

print(args)

DATA_DIR = args.data_dir
LOG_DIR = args.log_dir
API_KEY = args.api_key
API_KEY_NAME = "api_key"

# Ensure the directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# Configure logging
logging.config.dictConfig(get_logging_config(LOG_DIR))

#log log_dir
logging.info(f"Log files will be stored in: {LOG_DIR}")


app = FastAPI()


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
async def get_api_key_ui(api_key: str = Security(api_key_query)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@app.get("/")
async def read_root():
    return {"message": "Welcome to the file upload and download service"}


@app.post("/uploadTeamConfig")
async def upload_team_config(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    logging.info(f"Received file: {file.filename}")
    team_config_dir = os.path.join(DATA_DIR, "team_configs")
    os.makedirs(team_config_dir, exist_ok=True)
    file_path = os.path.join(team_config_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename}


@app.get("/downloadTeamConfig/{config_id}")
async def download_team_config(config_id: int, api_key: str = Depends(get_api_key)):
    logging.info(f"Downloading team config file with ID: {config_id}")
    team_config_dir = os.path.join(DATA_DIR, "team_configs")
    file_path = os.path.join(team_config_dir, f"{config_id}.zip")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.post("/uploadBaseTeam")
async def upload_base_team(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    logging.info(f"Received file: {file.filename}")
    team_config_dir = os.path.join(DATA_DIR, "base_teams")
    os.makedirs(team_config_dir, exist_ok=True)
    file_path = os.path.join(team_config_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename}


@app.get("/downloadBaseTeam/{base_name}")
async def download_base_team(base_name: str, api_key: str = Depends(get_api_key)):
    logging.info(f"Downloading base team file with name: {base_name}")
    team_config_dir = os.path.join(DATA_DIR, "base_teams")
    file_path = os.path.join(team_config_dir, f"{base_name}.zip")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# UI
@app.get("/ui")
async def read_root(request: Request, api_key: str = Depends(get_api_key_ui)):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/downloadTeamConfigFromUi/{config_name}")
async def download_team_config_from_ui(config_name: str, api_key: str = Depends(get_api_key_ui)):
    logging.info(f"Downloading team config file with name: {config_name}")
    team_config_dir = os.path.join(DATA_DIR, "team_configs")
    file_path = os.path.join(team_config_dir, f"{config_name}")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/uploadTeamConfigUi", response_class=HTMLResponse)
async def upload_team_config_ui(request: Request):
    return templates.TemplateResponse("upload_team_config.html", {"request": request})


@app.post("/uploadTeamConfigUiPost", response_class=HTMLResponse)
async def upload_team_config_ui_post(request: Request, file: UploadFile = File(...), api_key: str = Form(...)):
    logging.info(f"Received file from ui: {file.filename}")
    team_config_dir = os.path.join(DATA_DIR, "team_configs")
    os.makedirs(team_config_dir, exist_ok=True)
    file_path = os.path.join(team_config_dir, file.filename)
    logging.debug(f"Writing file to: {file_path}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return templates.TemplateResponse("upload_team_config.html",
                                      {"request": request, "message": f"Successfully uploaded {file.filename}"})


@app.get("/downloadTeamConfigUi", response_class=HTMLResponse)
async def download_team_config_ui(request: Request, api_key: str = Depends(get_api_key_ui)):
    team_config_dir = os.path.join(DATA_DIR, "team_configs")
    files = [f for f in os.listdir(team_config_dir) if os.path.isfile(os.path.join(team_config_dir, f))]
    return templates.TemplateResponse("download_team_config.html", {"request": request, "files": files, "api_key": api_key})


@app.get("/downloadBaseTeamFromUi/{base_name}")
async def download_base_team_from_ui(base_name: str, api_key: str = Depends(get_api_key_ui)):
    logging.info(f"Downloading base team file with name: {base_name}")
    base_teams_dir = os.path.join(DATA_DIR, "base_teams")
    file_path = os.path.join(base_teams_dir, f"{base_name}")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/uploadBaseTeamUi", response_class=HTMLResponse)
async def upload_base_team_ui(request: Request):
    return templates.TemplateResponse("upload_base_team.html", {"request": request})


@app.post("/uploadBaseTeamUiPost", response_class=HTMLResponse)
async def upload_base_team_ui_post(request: Request, file: UploadFile = File(...), api_key: str = Form(...)):
    logging.info(f"Received file from ui: {file.filename}")
    base_teams_dir = os.path.join(DATA_DIR, "base_teams")
    os.makedirs(base_teams_dir, exist_ok=True)
    file_path = os.path.join(base_teams_dir, file.filename)
    logging.debug(f"Writing file to: {file_path}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return templates.TemplateResponse("upload_base_team.html",
                                      {"request": request, "message": f"Successfully uploaded {file.filename}"})


@app.get("/downloadBaseTeamUi", response_class=HTMLResponse)
async def download_base_team_ui(request: Request, api_key: str = Depends(get_api_key_ui)):
    base_teams_dir = os.path.join(DATA_DIR, "base_teams")
    files = [f for f in os.listdir(base_teams_dir) if os.path.isfile(os.path.join(base_teams_dir, f))]
    return templates.TemplateResponse("download_base_team.html", {"request": request, "files": files, "api_key": api_key})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)