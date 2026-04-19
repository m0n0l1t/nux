from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Указываем папку, где лежат наши HTML-файлы
templates = Jinja2Templates(directory="templates")

# Монтируем статические файлы (CSS, JS, изображения)
app.mount("/assets", StaticFiles(directory="templates/assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Мое FastAPI Приложение"}
    )
