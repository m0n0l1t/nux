from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Указываем папку, где лежат наши HTML-файлы
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # Передаем контекст: обязательный объект request и наш заголовок
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Мое FastAPI Приложение"}
    )
