from fastapi.templating import Jinja2Templates
from settings import BASE_DIR
templates = Jinja2Templates(directory=f"{BASE_DIR}/templates")
