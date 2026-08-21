import os, json, re
import anthropic
from flask import Blueprint, jsonify, request, render_template, session, current_app
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
   - video: [URL YouTube]
   - pasos:
   1. [Posición inicial]
   2. [Ejecución fase 1]
   3. [Punto clave o fase 2]
   4. [Error más común y corrección]
   5. [Adaptación para lesión O progresión]

REGLAS DE PROGRAMACIÓN:
- Adaptar estructura semanal a los días disponibles
- Para pérdida de grasa: fuerza 2-3 días + HIIT 1-2 días + movilidad 1 día
- Para fuerza/músculo: patrones empuje/tracción/bisagra/sentadilla
- Restricciones por lesión: rodilla → flexión máx 60°, tag warn; cervical → sin carga axial, tag warn
- Cantidad: 45 min = 8-11 ejercicios, 60 min = 11-15 ejercicios
- SIEMPRE: activación, bloque principal, core, vuelta a la calma

DÍAS VÁLIDOS: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo

Genera SOLO el bloque markdown, sin texto antes ni después.
"""


def construir_prompt(datos):
    peso = datos.get('peso', 0)
    est  = datos.get('estatura', 170)
    try:
        imc = round(peso/((est/100)**2), 1)
        cat = 'bajo peso' if imc<18.5 else 'normal' if imc<25 else 'sobrepeso' if imc<30 else 'obesidad'
    except:
        imc='N/D'; cat=''
    try:
        fcmax = round(208 - 0.7*int(datos.get('edad',30)))
    except:
        fcmax='N/D'
    equipo = datos.get('equipamiento', [])
    return f"""PERFIL:
Nombre: {datos.get('nombre','Usuario')} | Edad: {datos.get('edad','N/D')} | Sexo: {datos.get('sexo','N/D')}
Peso: {peso}kg | Estatura: {est}cm | IMC: {imc} ({cat})
FC máx: {fcmax} bpm | FCR: {datos.get('fcr','N/D')} | Presión: {datos.get('presion','N/D')}
Lesiones: {datos.get('lesiones','ninguna')}
Actividad: {datos.get('nivel_actividad','N/D')}
Equipamiento: {', '.join(equipo) if equipo else 'solo peso corporal'}
Lugar: {datos.get('lugar','hogar')}
OBJETIVO: {datos.get('objetivo','bienestar')}
ESTILO: {datos.get('estilo','funcional')}
Días/semana: {datos.get('dias_semana',3)} | Tiempo/sesión: {datos.get('tiempo_sesion','45')} min
Nivel inicial: {datos.get('nivel_inicial','medio')}"""


def parsear_md(texto):
    m = re.search(r'```(?:markdown)?\s*\n(.*?)```', texto, re.DOTALL)
    return m.group(1).strip() if m else texto.strip()


# ── Rutas HTML ──────────────────────────────────────────────────────────────

@bp.route('/assessment/<int:uid>')
def assessment_form(uid):
    u = Usuario.query.get_or_404(uid)
    activo = Assessment.query.filter_by(usuario_id=uid, activo=True).first()
    return render_template('assessment.html', usuario=u, assessment_activo=activo)


@bp.route('/assessment-usuario/<int:uid>')
def assessment_usuario(uid):
    from flask import redirect, url_for
    u = Usuario.query.get_or_404(uid)
    if session.get('usuario_id') != uid:
        return redirect(url_for('index'))
    activo = Assessment.query.filter_by(usuario_id=uid, activo=True).first()
    return render_template('assessment_usuario.html', usuario=u, assessment_activo=activo)


# ── API ─────────────────────────────────────────────────────────────────────

@bp.route('/api/assessment/<int:uid>', methods=['POST'])
def crear_assessment(uid):
    """Genera la rutina de forma SÍNCRONA con timeout de 300 segundos."""
    Usuario.query.get_or_404(uid)
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos requeridos'}), 400

    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})
    db.session.flush()

    asmt = Assessment(
        usuario_id = uid,
        datos      = json.dumps(datos, ensure_ascii=False),
        estado     = 'generando',
        activo     = True,
    )
    db.session.add(asmt)
    db.session.commit()

    try:
        api_key = SistemaConfig.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("API Key no configurada. Ve a Admin → Sistema.")

        prompt = f"{SKILL_PROMPT}\n\n{construir_prompt(datos)}\n\nGenera la rutina completa ahora."
        client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
        message = client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 6000,
            messages   = [{"role": "user", "content": prompt}]
        )

        md_limpio = parsear_md(message.content[0].text)

        from routes.admin import parsear_md as parsear_md_admin
        parsed = parsear_md_admin(md_limpio)
        if not parsed:
            raise ValueError(f"No se encontraron ejercicios. Preview: {md_limpio[:300]}")

        Ejercicio.query.filter_by(usuario_id=uid).delete()
        db.session.flush()
        for orden, ex in enumerate(parsed):
            db.session.add(Ejercicio(
                usuario_id=uid, dia_id=ex['dia_id'], seccion=ex['seccion'],
                nombre=ex['nombre'], detalle_base=ex.get('base',''),
                detalle_medio=ex.get('medio',''), detalle_alto=ex.get('alto',''),
                detalle_avanzado=ex.get('avanzado',''), tag=ex.get('tag','keep'),
                nota=ex.get('nota',''), video_url=ex.get('video',''),
                pasos=ex.get('pasos',''), orden=orden, activo=True,
            ))

        Config.set(uid, 'carga_nivel',   datos.get('nivel_inicial','medio'))
        Config.set(uid, 'fase_actual',   '1')
        Config.set(uid, 'semana_actual', '1')

        asmt.md_generado         = md_limpio
        asmt.ejercicios_cargados = len(parsed)
        asmt.estado              = 'listo'
        db.session.commit()

        return jsonify({
            'ok':                  True,
            'assessment_id':       asmt.id,
            'estado':              'listo',
            'ejercicios_cargados': len(parsed),
        })

    except Exception as e:
        asmt.estado    = 'error'
        asmt.error_msg = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/assessment/<int:uid>/estado/<int:aid>')
def estado_assessment(uid, aid):
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    return jsonify(asmt.to_dict())


@bp.route('/api/assessment/<int:uid>/historial')
def historial_assessments(uid):
    return jsonify([a.to_dict() for a in
