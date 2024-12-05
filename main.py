import openai
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.responses import JSONResponse
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_SECRET_KEY')

app = FastAPI()

templates = Jinja2Templates(directory="templates")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


chat_log = [{'role': 'system',
             'content': 'Di chistes.'
             }]


@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

        try:
            # Llamada a OpenAI sin stream
            response = openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=chat_log,
                temperature=1,
            )

            # Obtener la respuesta completa (sin fragmentos)
            ai_response = response.choices[0].message.content

            # Enviar la respuesta completa al cliente
            await websocket.send_text(ai_response)

            # Guardar la respuesta en el historial
            chat_responses.append(ai_response)

        except Exception as e:
            # Obtener el traceback completo
            error_details = traceback.format_exc()
            
            # Enviar el mensaje de error detallado al websocket
            await websocket.send_text(f'Error: {error_details}')
            
            # Imprimir el traceback completo en la consola para depuración
            print(error_details)
            break




@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=chat_log,
        temperature=0.8
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=JSONResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):

    # Llamar a la API de OpenAI para generar la imagen
    response = openai.images.generate(
        prompt=user_input,
        n=1,
        size="512x512"
    )

    # Obtener la URL de la imagen generada
    image_url = response.data[0].url

    # Retornar la URL de la imagen en formato JSON
    return JSONResponse(content={"image_url": image_url})














