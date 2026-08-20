# RPG Tenis — App de entrenamiento

App web Flask para seguimiento del plan RPG de retorno al tenis sin dolor.

## Stack
- Python + Flask
- PostgreSQL (Railway plugin)
- SQLAlchemy ORM
- Gunicorn (producción)

---

## Deploy en Railway (paso a paso)

### 1. Crear cuenta en Railway
Ve a [railway.app](https://railway.app) y crea una cuenta gratuita.

### 2. Subir el código a GitHub
```bash
git init
git add .
git commit -m "RPG Tenis app inicial"
# Crear repo en github.com y luego:
git remote add origin https://github.com/TU_USUARIO/rpg-tenis.git
git push -u origin main
```

### 3. Crear proyecto en Railway
1. En Railway: **New Project → Deploy from GitHub repo**
2. Seleccionar tu repositorio `rpg-tenis`
3. Railway detecta automáticamente que es Python/Flask

### 4. Agregar PostgreSQL
1. En tu proyecto Railway: **+ Add a service → Database → PostgreSQL**
2. Railway crea la base de datos y agrega `DATABASE_URL` automáticamente

### 5. Configurar variables de entorno
En Railway → tu servicio Flask → **Variables**:
```
SECRET_KEY = (genera una clave aleatoria, ej: openssl rand -hex 32)
```
`DATABASE_URL` ya está disponible automáticamente desde el plugin PostgreSQL.

### 6. Deploy
Railway hace el deploy automáticamente al hacer push a GitHub.
La primera vez, el seed se ejecuta solo al arrancar la app.

### 7. Obtener tu URL
En Railway → tu servicio → **Settings → Domains → Generate Domain**
Te da una URL tipo: `https://rpg-tenis-production.up.railway.app`

---

## Desarrollo local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
cp .env.example .env
# Editar .env con tu DATABASE_URL local o dejar SQLite por defecto

# Iniciar servidor de desarrollo
python app.py
```

La app queda en `http://localhost:5000`

---

## API REST

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/semana` | Resumen de los 7 días |
| GET | `/api/rutina/{dia_id}` | Ejercicios del día (0=Lun, 6=Dom) |
| POST | `/api/progreso` | Marcar ejercicio hecho/deshecho |
| POST | `/api/sesion/completar` | Marcar sesión del día completada |
| GET | `/api/historial` | Historial de semanas completadas |
| GET | `/api/stats/semana` | Estadísticas semana actual |
| GET | `/api/config` | Configuración actual |
| POST | `/api/config/carga` | Cambiar nivel: bajo/medio/alto/avanzado |
| POST | `/api/config/fase` | Cambiar fase: 1, 2 o 3 |
| POST | `/api/config/semana` | Cambiar semana actual |
| PUT | `/api/ejercicio/{id}` | Editar un ejercicio |
| POST | `/api/ejercicio/{id}/toggle` | Activar/desactivar ejercicio |

---

## Estructura del proyecto

```
rpg-tenis/
├── app.py              ← servidor Flask principal
├── models.py           ← modelos SQLAlchemy (tablas)
├── seed.py             ← datos iniciales de ejercicios
├── routes/
│   ├── rutinas.py      ← API ejercicios por día
│   ├── progreso.py     ← API marcar progreso
│   └── config.py       ← API configuración
├── templates/
│   ├── base.html       ← layout con nav inferior
│   ├── index.html      ← vista principal (semana + día)
│   ├── historial.html  ← historial y estadísticas
│   └── configuracion.html ← ajuste de carga, fase, semana
├── static/
│   ├── css/app.css     ← estilos
│   └── js/app.js       ← utilidades JS
├── requirements.txt
├── Procfile            ← comando de inicio para Railway
├── railway.json        ← configuración de Railway
└── .env.example        ← template de variables de entorno
```
