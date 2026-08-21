import os, json, re
import anthropic
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, jsonify, request, render_template, session, current_app
from models import db, Usuario, Assessment, Ejercicio, Config, SistemaConfig

bp = Blueprint('assessment', __name__)
executor = ThreadPoolExecutor(max_workers=4)

SKILL_PROMPT = """Eres un Coach Experto en Ciencias del Deporte especializado en programación de entrenamiento.
Tu misión es generar una rutina semanal COMPLETA en formato MD para la aplicación PlanifiT.

REGLAS ABSOLUTAS DEL FORMATO:
1. Cada día empieza con: # Rutina: [Día] — [Descripción]
2. Cada sección: ## Sección: [Nombre]
3. Cada ejercicio: ### [Nombre del ejercicio]
4. Campos obligatorios de cada ejercicio (en este orden exacto):
   - base: [volumen mínimo]
   - medio: [volumen estándar]
   - alto: [volumen aumentado]
   - avanzado: [máxima intensidad]
   - tag: [keep | new | warn]
   - nota: [instrucción técnica breve]
   - video: [URL YouTube — usar búsqueda: https://www.youtube.com/results?search_query=NOMBRE+ejercicio+tecnica+correcta+español]
   - pasos:
   1. [Posición inicial]
   2. [Ejecución fase 1]
   3. [Punto clave o fase 2]
   4. [Error más común y corrección]
   5. [Adaptación para lesión declarada O progresión]

REGLAS DE PROGRAMACIÓN:
- Adaptar estructura semanal a los días disponibles del usuario
- Para pérdida de grasa: fuerza 2-3 días + HIIT
