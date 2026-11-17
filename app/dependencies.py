"""Entrega a cada endpoint el servicio que necesita.

Los servicios se crean una sola vez, al arrancar la aplicación (ver main.py), y se
guardan en `app.state`. FastAPI llama a estas funciones en cada pedido (Depends).
En los tests, la aplicación se arma con repositorios en memoria y estas funciones
devuelven esos servicios sin cambiar nada más.
"""

from fastapi import Request

from app.avisos.service import ServicioAvisos
from app.emergencias.service import ServicioEmergencias


def servicio_de_avisos(request: Request) -> ServicioAvisos:
    return request.app.state.servicio_avisos


def servicio_de_emergencias(request: Request) -> ServicioEmergencias:
    return request.app.state.servicio_emergencias
