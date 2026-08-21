import os, json, re, anthropic
from flask import Blueprint, jsonify, request, render_template, session
from models import db, Usuario, Assessment, Ejercicio, Config

bp = Blueprint('assessment', __name__)

# ── Skill prompt ──────────────────────────────────────────────────────────────

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
- Para pérdida de grasa: fuerza 2-3 días + HIIT 1-2 días + movilidad 1 día
- Para fuerza/músculo: patrones empuje/tracción/bisagra/sentadilla, 2x/semana por grupo
- Para retorno deportivo: estabilidad → fuerza → potencia → movimiento específico
- Para rehabilitación: solo niveles base y medio, isometría primero
- Restricciones por lesión: rodilla → flexión máx 60°, tag warn; cervical → sin carga axial, tag warn
- Cantidad de ejercicios: 45 min = 8-11 ejercicios, 60 min = 11-15 ejercicios
- SIEMPRE incluir: activación, bloque principal, core, vuelta a la calma

DÍAS VÁLIDOS (exactamente estos nombres):
Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo

Genera el MD completo ahora. Solo el bloque markdown, sin explicaciones adicionales antes ni después.
"""

def construir_prompt(datos: dict) -> str:
    """Construye el prompt personalizado con los datos del assessment."""
    
    # Calcular IMC
    peso = datos.get('peso', 0)
    estatura_cm = datos.get('estatura', 170)
    try:
        imc = round(peso / ((estatura_cm/100)**2), 1)
        imc_cat = 'bajo peso' if imc < 18.5 else 'normal' if imc < 25 else 'sobrepeso' if imc < 30 else 'obesidad'
    except:
        imc = 'N/D'; imc_cat = ''

    # Calcular FC máx (Tanaka)
    try:
        edad = int(datos.get('edad', 30))
        fcmax = round(208 - 0.7 * edad)
        fcr   = datos.get('fcr', '')
        if fcr:
            rfc = fcmax - int(fcr)
            z1 = f"{int(fcr)+int(rfc*0.50)}–{int(fcr)+int(rfc*0.60)} bpm"
            z2 = f"{int(fcr)+int(rfc*0.60)}–{int(fcr)+int(rfc*0.70)} bpm"
            z3 = f"{int(fcr)+int(rfc*0.70)}–{int(fcr)+int(rfc*0.80)} bpm"
            z4 = f"{int(fcr)+int(rfc*0.80)}–{int(fcr)+int(rfc*0.90)} bpm"
        else:
            z1 = f"{int(fcmax*0.50)}–{int(fcmax*0.60)} bpm"
            z2 = f"{int(fcmax*0.60)}–{int(fcmax*0.70)} bpm"
            z3 = f"{int(fcmax*0.70)}–{int(fcmax*0.80)} bpm"
            z4 = f"{int(fcmax*0.80)}–{int(fcmax*0.90)} bpm"
    except:
        fcmax = 'N/D'; z1=z2=z3=z4='N/D'

    lesiones   = datos.get('lesiones', 'ninguna')
    equipo     = datos.get('equipamiento', [])
    equipo_str = ', '.join(equipo) if equipo else 'solo peso corporal'
    dias       = datos.get('dias_semana', 3)
    descanso   = datos.get('dias_descanso', 'no especificados')

    perfil = f"""
PERFIL DEL USUARIO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre: {datos.get('nombre','Usuario')}
Edad: {datos.get('edad','N/D')} años | Sexo: {datos.get('sexo','N/D')}
Peso: {peso} kg | Estatura: {estatura_cm} cm | IMC: {imc} ({imc_cat})
FCR: {datos.get('fcr','no declarada')} | Presión: {datos.get('presion','no declarada')}
FC máx estimada (Tanaka): {fcmax} bpm

Zonas cardíacas:
  Z1 Recuperación: {z1}
  Z2 Aeróbico base: {z2}
  Z3 Tempo: {z3}
  Z4 Umbral: {z4}

Condiciones médicas / lesiones: {lesiones}
Nivel de actividad actual: {datos.get('nivel_actividad','no declarado')}

Equipamiento disponible: {equipo_str}
Lugar de entrenamiento: {datos.get('lugar','hogar')}
Espacio disponible: {datos.get('espacio','mediano')}

OBJETIVO: {datos.get('objetivo','bienestar general')}
ESTILO: {datos.get('estilo','funcional')}
Días de entrenamiento por semana: {dias}
Tiempo por sesión: {datos.get('tiempo_sesion','45')} minutos
Días de descanso preferidos: {descanso}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return perfil


def parsear_md_desde_respuesta(texto: str) -> str:
    """Extrae el bloque MD limpio de la respuesta de Claude."""
    # Buscar bloque de código markdown
    match = re.search(r'```(?:markdown)?\s*\n(.*?)```', texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Si no hay bloque de código, devolver el texto completo
    return texto.strip()


def cargar_md_a_bd(usuario_id: int, md: str) -> int:
    """Parsea el MD y carga los ejercicios a la base de datos. Devuelve cantidad cargada."""
    from routes.admin import parsear_md
    parsed = parsear_md(md)
    if not parsed:
        raise ValueError("No se encontraron ejercicios en el MD generado")

    # Eliminar ejercicios anteriores
    Ejercicio.query.filter_by(usuario_id=usuario_id).delete()
    db.session.flush()

    for orden, ex in enumerate(parsed):
        db.session.add(Ejercicio(
            usuario_id       = usuario_id,
            dia_id           = ex['dia_id'],
            seccion          = ex['seccion'],
            nombre           = ex['nombre'],
            detalle_base     = ex.get('base', ''),
            detalle_medio    = ex.get('medio', ''),
            detalle_alto     = ex.get('alto', ''),
            detalle_avanzado = ex.get('avanzado', ''),
            tag              = ex.get('tag', 'keep'),
            nota             = ex.get('nota', ''),
            video_url        = ex.get('video', ''),
            pasos            = ex.get('pasos', ''),
            orden            = orden,
            activo           = True,
        ))

    db.session.commit()
    return len(parsed)


# ── Rutas HTML ────────────────────────────────────────────────────────────────

@bp.route('/assessment/<int:uid>')
def assessment_form(uid):
    """Formulario de assessment en 4 pasos."""
    u = Usuario.query.get_or_404(uid)
    assessment_activo = Assessment.query.filter_by(usuario_id=uid, activo=True).first()
    return render_template('assessment.html', usuario=u, assessment_activo=assessment_activo)


# ── API Assessment ────────────────────────────────────────────────────────────

@bp.route('/api/assessment/<int:uid>', methods=['POST'])
def crear_assessment(uid):
    """Guarda los datos del formulario, llama a Claude y carga el MD."""
    u = Usuario.query.get_or_404(uid)
    datos = request.get_json()

    if not datos:
        return jsonify({'error': 'Datos del formulario requeridos'}), 400

    # Marcar assessments anteriores como inactivos
    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})
    db.session.flush()

    # Crear nuevo assessment en estado "generando"
    asmt = Assessment(
        usuario_id = uid,
        datos      = json.dumps(datos, ensure_ascii=False),
        estado     = 'generando',
        activo     = True,
    )
    db.session.add(asmt)
    db.session.commit()

    try:
        # Construir prompt
        perfil_prompt = construir_prompt(datos)
        prompt_completo = f"{SKILL_PROMPT}\n\n{perfil_prompt}\n\nGenera ahora la rutina semanal completa en formato MD."

        # Llamar a Claude API
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada en variables de entorno")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 8000,
            messages   = [{"role": "user", "content": prompt_completo}]
        )

        respuesta = message.content[0].text
        md_limpio = parsear_md_desde_respuesta(respuesta)

        # Cargar ejercicios a la BD
        n = cargar_md_a_bd(uid, md_limpio)

        # Actualizar config del usuario con nivel medio por defecto
        Config.set(uid, 'carga_nivel',   datos.get('nivel_inicial', 'medio'))
        Config.set(uid, 'fase_actual',   '1')
        Config.set(uid, 'semana_actual', '1')

        # Guardar assessment como listo
        asmt.md_generado        = md_limpio
        asmt.ejercicios_cargados = n
        asmt.estado             = 'listo'
        db.session.commit()

        return jsonify({
            'ok':                  True,
            'assessment_id':       asmt.id,
            'ejercicios_cargados': n,
            'preview_md':          md_limpio[:500] + '...' if len(md_limpio) > 500 else md_limpio,
        })

    except Exception as e:
        asmt.estado    = 'error'
        asmt.error_msg = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/assessment/<int:uid>/historial')
def historial_assessments(uid):
    """Lista todos los assessments del usuario."""
    assessments = Assessment.query.filter_by(usuario_id=uid)\
        .order_by(Assessment.created_at.desc()).all()
    return jsonify([a.to_dict() for a in assessments])


@bp.route('/api/assessment/<int:uid>/reactivar/<int:aid>', methods=['POST'])
def reactivar_assessment(uid, aid):
    """Reactiva un assessment anterior (restaura su MD a la BD)."""
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()

    if not asmt.md_generado:
        return jsonify({'error': 'Este assessment no tiene MD guardado'}), 400

    # Desactivar el actual
    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})

    # Recargar los ejercicios del assessment seleccionado
    n = cargar_md_a_bd(uid, asmt.md_generado)

    asmt.activo              = True
    asmt.ejercicios_cargados = n
    db.session.commit()

    return jsonify({'ok': True, 'ejercicios_cargados': n})


@bp.route('/api/assessment/<int:uid>/estado/<int:aid>')
def estado_assessment(uid, aid):
    """Consulta el estado de un assessment (polling desde el frontend)."""
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    return jsonify(asmt.to_dict())
