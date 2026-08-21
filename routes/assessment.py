import os, json, re
import anthropic
from flask import Blueprint, jsonify, request, render_template, session
from models import db, Usuario, Assessment, Ejercicio, Config, SistemaConfig

bp = Blueprint('assessment', __name__)

SKILL_PROMPT = """Eres un Coach Experto en Ciencias del Deporte especializado en programacion de entrenamiento.
Tu mision es generar una rutina semanal COMPLETA en formato MD para la aplicacion PlanifiT.

REGLAS DEL FORMATO - cada ejercicio DEBE tener exactamente estos campos:
### Nombre del ejercicio
- base: series x reps minimo
- medio: series x reps estandar
- alto: series x reps aumentado
- avanzado: series x reps maximo
- tag: keep
- nota: instruccion breve
- video: https://www.youtube.com/results?search_query=nombre+ejercicio+tecnica+correcta
- pasos:
1. Posicion inicial
2. Ejecucion fase 1
3. Punto clave
4. Error comun y correccion
5. Adaptacion o progresion

ESTRUCTURA OBLIGATORIA:
# Rutina: [Dia] - [Descripcion]
## Seccion: [Nombre seccion]
### [Ejercicio]

DIAS VALIDOS: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo

REGLAS:
- tag puede ser: keep, new, warn
- Para perdida de grasa: fuerza 2-3 dias + HIIT 1-2 dias + movilidad 1 dia
- Para fuerza: patrones empuje, traccion, bisagra, sentadilla
- Rodilla lesionada: flexion max 60 grados, tag warn
- Cervical operada: sin carga axial, tag warn
- 45 min = 8 a 11 ejercicios por dia
- SIEMPRE incluir: activacion, bloque principal, core, vuelta a la calma

Genera SOLO el bloque markdown sin texto adicional antes ni despues."""


def construir_prompt(datos):
    peso = datos.get('peso', 0)
    est = datos.get('estatura', 170)
    try:
        imc = round(peso / ((est / 100) ** 2), 1)
        cat = 'bajo peso' if imc < 18.5 else 'normal' if imc < 25 else 'sobrepeso' if imc < 30 else 'obesidad'
    except Exception:
        imc = 'ND'
        cat = ''
    try:
        fcmax = round(208 - 0.7 * int(datos.get('edad', 30)))
    except Exception:
        fcmax = 'ND'
    equipo = datos.get('equipamiento', [])
    equipo_str = ', '.join(equipo) if equipo else 'solo peso corporal'
    return (
        f"PERFIL DEL USUARIO:\n"
        f"Nombre: {datos.get('nombre', 'Usuario')} | Edad: {datos.get('edad', 'ND')} | Sexo: {datos.get('sexo', 'ND')}\n"
        f"Peso: {peso}kg | Estatura: {est}cm | IMC: {imc} ({cat})\n"
        f"FC max (Tanaka): {fcmax} bpm | FCR: {datos.get('fcr', 'ND')} | Presion: {datos.get('presion', 'ND')}\n"
        f"Lesiones: {datos.get('lesiones', 'ninguna')}\n"
        f"Actividad actual: {datos.get('nivel_actividad', 'ND')}\n"
        f"Equipamiento: {equipo_str}\n"
        f"Lugar: {datos.get('lugar', 'hogar')}\n"
        f"OBJETIVO: {datos.get('objetivo', 'bienestar general')}\n"
        f"ESTILO: {datos.get('estilo', 'funcional')}\n"
        f"Dias por semana: {datos.get('dias_semana', 3)}\n"
        f"Tiempo por sesion: {datos.get('tiempo_sesion', '45')} minutos\n"
        f"Nivel de carga inicial: {datos.get('nivel_inicial', 'medio')}\n"
    )


def extraer_md(texto):
    """Extrae el bloque MD de la respuesta de Claude."""
    match = re.search(r'```(?:markdown)?\s*\n(.*?)```', texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto.strip()


def cargar_ejercicios(uid, parsed):
    """Elimina ejercicios anteriores y carga los nuevos."""
    Ejercicio.query.filter_by(usuario_id=uid).delete()
    db.session.flush()
    for orden, ex in enumerate(parsed):
        db.session.add(Ejercicio(
            usuario_id=uid,
            dia_id=ex['dia_id'],
            seccion=ex['seccion'],
            nombre=ex['nombre'],
            detalle_base=ex.get('base', ''),
            detalle_medio=ex.get('medio', ''),
            detalle_alto=ex.get('alto', ''),
            detalle_avanzado=ex.get('avanzado', ''),
            tag=ex.get('tag', 'keep'),
            nota=ex.get('nota', ''),
            video_url=ex.get('video', ''),
            pasos=ex.get('pasos', ''),
            orden=orden,
            activo=True,
        ))
    db.session.commit()


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
    """Genera rutina sincrona con timeout 300 segundos."""
    Usuario.query.get_or_404(uid)
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos del formulario requeridos'}), 400

    # Marcar assessments anteriores como inactivos
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

    try:
        # Obtener API key desde BD o variable de entorno
        api_key = SistemaConfig.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("API Key no configurada. Ve a Admin → Sistema para configurarla.")

        # Llamar a Claude con timeout de 300 segundos
        prompt_completo = SKILL_PROMPT + "\n\n" + construir_prompt(datos) + "\n\nGenera la rutina completa ahora."
        client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt_completo}]
        )

        md_limpio = extraer_md(message.content[0].text)

        # Parsear MD y cargar ejercicios
        from routes.admin import parsear_md
        parsed = parsear_md(md_limpio)
        if not parsed:
            raise ValueError("No se encontraron ejercicios en el MD generado. Preview: " + md_limpio[:300])

        cargar_ejercicios(uid, parsed)

        # Actualizar configuracion del usuario
        Config.set(uid, 'carga_nivel', datos.get('nivel_inicial', 'medio'))
        Config.set(uid, 'fase_actual', '1')
        Config.set(uid, 'semana_actual', '1')

        # Guardar assessment como listo
        asmt.md_generado = md_limpio
        asmt.ejercicios_cargados = len(parsed)
        asmt.estado = 'listo'
        db.session.commit()

        return jsonify({
            'ok': True,
            'assessment_id': asmt.id,
            'estado': 'listo',
            'ejercicios_cargados': len(parsed),
        })

    except Exception as e:
        asmt.estado = 'error'
        asmt.error_msg = str(e)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/assessment/<int:uid>/estado/<int:aid>')
def estado_assessment(uid, aid):
    """Consulta estado de un assessment."""
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    return jsonify(asmt.to_dict())


@bp.route('/api/assessment/<int:uid>/historial')
def historial_assessments(uid):
    """Lista todos los assessments del usuario."""
    lista = Assessment.query.filter_by(usuario_id=uid).order_by(Assessment.created_at.desc()).all()
    resultado = [a.to_dict() for a in lista]
    return jsonify(resultado)


@bp.route('/api/assessment/<int:uid>/reactivar/<int:aid>', methods=['POST'])
def reactivar_assessment(uid, aid):
    """Reactiva un assessment anterior restaurando su MD."""
    asmt = Assessment.query.filter_by(id=aid, usuario_id=uid).first_or_404()
    if not asmt.md_generado:
        return jsonify({'error': 'Este assessment no tiene MD guardado'}), 400

    Assessment.query.filter_by(usuario_id=uid, activo=True).update({'activo': False})

    from routes.admin import parsear_md
    parsed = parsear_md(asmt.md_generado)
    if not parsed:
        return jsonify({'error': 'No se pudieron parsear los ejercicios del MD'}), 400

    cargar_ejercicios(uid, parsed)
    asmt.activo = True
    asmt.ejercicios_cargados = len(parsed)
    db.session.commit()

    return jsonify({'ok': True, 'ejercicios_cargados': len(parsed)})
