import os, json, re, threading
import anthropic
from flask import Blueprint, jsonify, request, render_template, session
from models import db, Usuario, Assessment, Ejercicio, Config, SistemaConfig

bp = Blueprint('assessment', __name__)

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
    peso = datos.get('peso', 0)
    estatura_cm = datos.get('estatura', 170)
    try:
        imc = round(peso / ((estatura_cm/100)**2), 1)
        imc_cat = 'bajo peso' if imc < 18.5 else 'normal' if imc < 25 else 'sobrepeso' if imc < 30 else 'obesidad'
    except:
        imc = 'N/D'; imc_cat = ''
    try:
        edad = int(datos.get('edad', 30))
        fcmax = round(208 - 0.7 * edad)
        fcr = datos.get('fcr', '')
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

    equipo = datos.get('equipamiento', [])
    return f"""
PERFIL DEL USUARIO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre: {datos.get('nombre','Usuario')}
Edad: {datos.get('edad','N/D')} años | Sexo: {datos.get('sexo','N/D')}
Peso: {peso} kg | Estatura: {estatura_cm} cm | IMC: {imc} ({imc_cat})
FCR: {datos.get('fcr','no declarada')} | Presión: {datos.get('presion','no declarada')}
FC máx estimada (Tanaka): {fcmax} bpm
Zonas: Z1:{z1} Z2:{z2} Z3:{z3} Z4:{z4}
Lesiones: {datos.get('lesiones','ninguna')}
Actividad: {datos.get('nivel_actividad','no declarado')}
Equipamiento: {', '.join(equipo) if equipo else 'solo peso corporal'}
Lugar: {datos.get('lugar','hogar')} | Espacio: {datos.get('espacio','mediano')}
OBJETIVO: {datos.get('objetivo','bienestar general')}
ESTILO: {datos.get('estilo','funcional')}
Días/semana: {datos.get('dias_semana',3)} | Tiempo/sesión: {datos.get('tiempo_sesion','45')} min
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def parsear_md_desde_respuesta(texto: str) -> str:
    match = re.search(r'```(?:markdown)?\s*\n(.*?)```', texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto.strip()


def cargar_md_a_bd(usuario_id: int, md: str) -> int:
    from routes.admin import parsear_md
    parsed = parsear_md(md)
    if not parsed:
        raise ValueError("No se encontraron ejercicios en el MD generado")
    Ejercicio.query.filter_by(usuario_id=usuario_id).delete()
    db.session.flush()
    for orden, ex in enumerate(parsed):
        db.session.add(Ejercicio(
            usuario_id=usuario_id, dia_id=ex['dia_id'], seccion=ex['seccion'],
            nombre=ex['nombre'], detalle_base=ex.get('base',''),
            detalle_medio=ex.get('medio',''), detalle_alto=ex.get('alto',''),
            detalle_avanzado=ex.get('avanzado',''), tag=ex.get('tag','keep'),
            nota=ex.get('nota',''), video_url=ex.get('video',''),
            pasos=ex.get('pasos',''), orden=orden, activo=True,
        ))
    db.session.commit()
    return len(parsed)


def _generar_en_background(app, asmt_id: int, datos: dict):
    """Ejecuta la llamada a Claude en un thread separado."""
    with app.app_context():
        asmt = Assessment.query.get(asmt_id)
        if not asmt:
            return
        try:
            api_key = SistemaConfig.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("API Key de Claude no configurada. Ve a Admin → Sistema.")

            perfil_prompt = construir_prompt(datos)
            prompt_completo = f"{SKILL_PROMPT}\n\n{perfil_prompt}\n\nGenera ahora la rutina semanal completa en formato MD."

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt_completo}]
            )

            md_limpio = parsear_md_desde_respuesta(message.content[0].text)
            n = cargar_md_a_bd(asmt.usuario_id, md_limpio)

            Config.set(asmt.usuario_id, 'carga_nivel', datos.get('nivel_inicial', 'medio'))
            Config.set(asmt.usuario_id, 'fase_actual', '1')
            Config.set(asmt.usuario_id, 'semana_actual', '1')

            asmt.md_generado = md_limpio
            asmt.ejercicios_cargados = n
            asmt.estado = 'listo'
            db.session.commit()

        except Exception as e:
            asmt.estado = 'error'
            asmt.error_msg = str(e)
            db.session.commit()


# ── Rutas HTML ────────────────────────────────────────────────────────────────

@bp.route('/assessment/<int:uid>')
def assessment_form(uid):
    u = Usuario.query.get_or_404(uid)
    assessment_activo = Assessment.query.filter_by(usuario_id=uid, activo=True).first()
    return render_template('assessment.html', usuario=u, assessment_activo=assessment_activo)


@bp.route('/assessment-usuario/<int:uid>')
def assessment_usuario(uid):
    from flask import redirect, url_for
    u = Usuario.query.get_or_404(uid)
    if session.get('usuario_id') != uid:
        return redirect(url_for('index'))
    assessment_activo = Assessment.query.filter_by(usuario_id=uid, activo=True).first()
    return render_template('assessment_usuario.html', usuario=u, assessment_activo=assessment_activo)


# ── API Assessment ────────────────────────────────────────────────────────────

@bp.route('/api/assessment/<int:uid>', methods=['POST'])
def crear_assessment(uid):
    """Lanza la generación en background y devuelve el ID del assessment inmediatamente."""
    from flask import current_app
    Usuario.query.get_or_404(uid)
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos requeridos'}), 400

    # Marcar anteriores como inactivos
    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})
    db.session.flush()

    asmt = Assessment(
        usuario_id=uid,
        datos=json.dumps(datos, ensure_ascii=False),
        estado='generando',
        activo=True,
    )
    db.session.add(asmt)
    db.session.commit()

    # Lanzar en thread separado — responde inmediatamente al browser
    app = current_app._get_current_object()
    t = threading.Thread(target=_generar_en_background, args=(app, asmt.id, datos), daemon=True)
    t.start()

    return jsonify({'ok': True, 'assessment_id': asmt.id, 'estado': 'generando'})


@bp.route('/api/assessment/<int:uid>/estado/<int:aid>')
def estado_assessment(uid, aid):
    """Polling — el frontend consulta cada 3 seg hasta que estado=listo o error."""
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    return jsonify(asmt.to_dict())


@bp.route('/api/assessment/<int:uid>/historial')
def historial_assessments(uid):
    assessments = Assessment.query.filter_by(usuario_id=uid)\
        .order_by(Assessment.created_at.desc()).all()
    return jsonify([a.to_dict() for a in assessments])


@bp.route('/api/assessment/<int:uid>/reactivar/<int:aid>', methods=['POST'])
def reactivar_assessment(uid, aid):
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    if not asmt.md_generado:
        return jsonify({'error': 'Este assessment no tiene MD guardado'}), 400
    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})
    n = cargar_md_a_bd(uid, asmt.md_generado)
    asmt.activo = True
    asmt.ejercicios_cargados = n
    db.session.commit()
    return jsonify({'ok': True, 'ejercicios_cargados': n})
