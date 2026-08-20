from flask import Blueprint, jsonify, request
from models import db, Progreso, SesionDia, Ejercicio
from datetime import date, timedelta
from sqlalchemy import func

bp = Blueprint('progreso', __name__)


@bp.route('/api/progreso', methods=['POST'])
def toggle_ejercicio():
    """Marcar o desmarcar un ejercicio como hecho."""
    data = request.get_json()
    ejercicio_id = data.get('ejercicio_id')
    fecha_str    = data.get('fecha', str(date.today()))

    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        return jsonify({'error': 'Fecha inválida'}), 400

    ejercicio = Ejercicio.query.get(ejercicio_id)
    if not ejercicio:
        return jsonify({'error': 'Ejercicio no encontrado'}), 404

    registro = Progreso.query.filter_by(
        ejercicio_id=ejercicio_id, fecha=fecha
    ).first()

    if registro:
        registro.hecho = not registro.hecho
    else:
        registro = Progreso(ejercicio_id=ejercicio_id, fecha=fecha, hecho=True)
        db.session.add(registro)

    db.session.commit()
    return jsonify({'hecho': registro.hecho, 'ejercicio_id': ejercicio_id})


@bp.route('/api/sesion/completar', methods=['POST'])
def completar_sesion():
    """Marcar o desmarcar una sesión completa."""
    data   = request.get_json()
    dia_id = data.get('dia_id')
    fecha  = date.today()

    sesion = SesionDia.query.filter_by(dia_id=dia_id, fecha=fecha).first()
    if sesion:
        sesion.completada = not sesion.completada
    else:
        sesion = SesionDia(dia_id=dia_id, fecha=fecha, completada=True)
        db.session.add(sesion)

    db.session.commit()
    return jsonify({'completada': sesion.completada, 'dia_id': dia_id})


@bp.route('/api/historial')
def historial():
    """Historial de sesiones completadas por semana (últimas 12)."""
    hoy = date.today()
    hace_12_semanas = hoy - timedelta(weeks=12)

    sesiones = SesionDia.query.filter(
        SesionDia.fecha >= hace_12_semanas,
        SesionDia.completada == True
    ).all()

    # Agrupar por semana ISO
    por_semana = {}
    for s in sesiones:
        iso = s.fecha.isocalendar()
        clave = f"{iso.year}-W{iso.week:02d}"
        por_semana.setdefault(clave, 0)
        por_semana[clave] += 1

    semanas = sorted(por_semana.items())

    # Stats globales
    total_sesiones = SesionDia.query.filter_by(completada=True).count()
    total_semanas  = len(por_semana)
    promedio       = round(sum(por_semana.values()) / total_semanas, 1) if total_semanas else 0
    mejor          = max(por_semana.values()) if por_semana else 0
    semanas_5plus  = sum(1 for v in por_semana.values() if v >= 5)

    return jsonify({
        'semanas':        [{'semana': k, 'dias': v} for k, v in semanas],
        'total_sesiones': total_sesiones,
        'total_semanas':  total_semanas,
        'promedio':       promedio,
        'mejor':          mejor,
        'semanas_5plus':  semanas_5plus,
    })


@bp.route('/api/stats/semana')
def stats_semana_actual():
    """Progreso de la semana en curso."""
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())

    sesiones_semana = SesionDia.query.filter(
        SesionDia.fecha >= lunes,
        SesionDia.completada == True
    ).count()

    ejercicios_semana = db.session.query(func.count(Progreso.id)).filter(
        Progreso.fecha >= lunes,
        Progreso.hecho == True
    ).scalar()

    return jsonify({
        'dias_completados':   sesiones_semana,
        'ejercicios_hechos':  ejercicios_semana or 0,
        'adherencia_pct':     round(sesiones_semana / 7 * 100),
        'dias_restantes':     7 - sesiones_semana,
    })
