from flask import Blueprint, jsonify, request
from models import db, Ejercicio, Progreso, SesionDia, Config
from datetime import date
from collections import defaultdict

bp = Blueprint('rutinas', __name__)

DIAS_INFO = {
    0: {'nombre': 'Lunes',     'label': 'Cadena posterior', 'duracion': '50 min',    'intensidad': 'Baja-Media', 'dot': '#7F77DD'},
    1: {'nombre': 'Martes',    'label': 'Movilidad',        'duracion': '45 min',    'intensidad': 'Baja',       'dot': '#1D9E75'},
    2: {'nombre': 'Miércoles', 'label': 'Rodilla',          'duracion': '50 min',    'intensidad': 'Media',      'dot': '#D85A30'},
    3: {'nombre': 'Jueves',    'label': 'Tren superior',    'duracion': '50 min',    'intensidad': 'Media',      'dot': '#7F77DD'},
    4: {'nombre': 'Viernes',   'label': 'Core + Tenis',     'duracion': '45-75 min', 'intensidad': 'Media',      'dot': '#BA7517'},
    5: {'nombre': 'Sábado',    'label': 'Movilidad global', 'duracion': '40 min',    'intensidad': 'Muy baja',   'dot': '#1D9E75'},
    6: {'nombre': 'Domingo',   'label': 'Recuperación',     'duracion': '30 min',    'intensidad': 'Mínima',     'dot': '#888780'},
}

TIPS = {
    0: 'El RDL y el puente de glúteos son la base de protección del LCA. El control excéntrico es donde ocurre la adaptación.',
    1: 'La rotación torácica limitada hace que el saque y el drive carguen la cervical. Hoy la liberamos.',
    2: 'VMO + propiocepción = los dos factores que más predicen ausencia de dolor en cancha.',
    3: 'Desequilibrio pecho fuerte / espalda débil = tensión cervical crónica en tenistas.',
    4: 'Viernes es el día de validación: si el core responde y la rodilla aguanta el peloteo, vas bien.',
    5: 'La respiración diafragmática baja el tono de trapecios más que cualquier masaje.',
    6: 'El domingo activo es uno de los días más útiles para la recuperación fascial.',
}


@bp.route('/api/semana')
def semana():
    """Resumen de los 7 días con estado completado."""
    hoy = date.today()
    nivel = Config.get('carga_nivel', 'medio')

    sesiones = {s.dia_id: s for s in SesionDia.query.filter(
        SesionDia.fecha >= _lunes_semana(hoy)
    ).all()}

    dias = []
    for dia_id, info in DIAS_INFO.items():
        sesion = sesiones.get(dia_id)
        dias.append({
            'dia_id':     dia_id,
            'nombre':     info['nombre'],
            'label':      info['label'],
            'duracion':   info['duracion'],
            'intensidad': info['intensidad'],
            'dot':        info['dot'],
            'completado': sesion.completada if sesion else False,
        })

    return jsonify({
        'dias':          dias,
        'nivel':         nivel,
        'fase':          Config.get('fase_actual', '2'),
        'semana_actual': Config.get('semana_actual', '1'),
        'hoy_dia_id':    _dia_id_hoy(),
    })


@bp.route('/api/rutina/<int:dia_id>')
def rutina_dia(dia_id):
    """Ejercicios detallados para un día específico."""
    if dia_id not in DIAS_INFO:
        return jsonify({'error': 'Día inválido'}), 404

    hoy = date.today()
    nivel = Config.get('carga_nivel', 'medio')

    ejercicios = Ejercicio.query.filter_by(
        dia_id=dia_id, activo=True
    ).order_by(Ejercicio.orden).all()

    # Ejercicios hechos hoy
    ids = [e.id for e in ejercicios]
    hechos_hoy = {
        p.ejercicio_id
        for p in Progreso.query.filter(
            Progreso.ejercicio_id.in_(ids),
            Progreso.fecha == hoy
        ).all()
        if p.hecho
    }

    # Agrupar por sección
    secciones = defaultdict(list)
    for e in ejercicios:
        secciones[e.seccion].append({
            **e.to_dict(nivel),
            'hecho': e.id in hechos_hoy,
        })

    sesion = SesionDia.query.filter_by(dia_id=dia_id, fecha=hoy).first()

    return jsonify({
        'dia_id':     dia_id,
        'info':       DIAS_INFO[dia_id],
        'tip':        TIPS.get(dia_id, ''),
        'nivel':      nivel,
        'secciones':  [
            {'nombre': k, 'ejercicios': v}
            for k, v in secciones.items()
        ],
        'completado': sesion.completada if sesion else False,
        'total_ex':   len(ejercicios),
        'hechos_ex':  len(hechos_hoy),
    })


def _lunes_semana(d):
    return d if d.weekday() == 0 else d.replace(day=d.day - d.weekday())

def _dia_id_hoy():
    """Convierte weekday() de Python (0=lun) al id del plan (0=lun)."""
    return date.today().weekday()  # lun=0 ... dom=6
