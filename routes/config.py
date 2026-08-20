from flask import Blueprint, jsonify, request
from models import db, Config, Ejercicio

bp = Blueprint('config', __name__)

NIVELES_VALIDOS = ['bajo', 'medio', 'alto', 'avanzado']
FASES_VALIDAS   = ['1', '2', '3']


@bp.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'fase_actual':   Config.get('fase_actual', '2'),
        'carga_nivel':   Config.get('carga_nivel', 'medio'),
        'semana_actual': Config.get('semana_actual', '1'),
    })


@bp.route('/api/config/carga', methods=['POST'])
def set_carga():
    data  = request.get_json()
    nivel = data.get('nivel', '').lower()
    if nivel not in NIVELES_VALIDOS:
        return jsonify({'error': f'Nivel inválido. Opciones: {NIVELES_VALIDOS}'}), 400
    Config.set('carga_nivel', nivel, 'Nivel de carga de entrenamiento')
    return jsonify({'carga_nivel': nivel})


@bp.route('/api/config/fase', methods=['POST'])
def set_fase():
    data = request.get_json()
    fase = str(data.get('fase', ''))
    if fase not in FASES_VALIDAS:
        return jsonify({'error': 'Fase inválida. Opciones: 1, 2, 3'}), 400
    Config.set('fase_actual', fase)
    return jsonify({'fase_actual': fase})


@bp.route('/api/config/semana', methods=['POST'])
def set_semana():
    data   = request.get_json()
    semana = str(data.get('semana', '1'))
    Config.set('semana_actual', semana)
    return jsonify({'semana_actual': semana})


@bp.route('/api/ejercicio/<int:ej_id>/toggle', methods=['POST'])
def toggle_ejercicio_activo(ej_id):
    """Activar o desactivar un ejercicio del plan."""
    ej = Ejercicio.query.get_or_404(ej_id)
    ej.activo = not ej.activo
    db.session.commit()
    return jsonify({'id': ej.id, 'activo': ej.activo})


@bp.route('/api/ejercicio/<int:ej_id>', methods=['PUT'])
def editar_ejercicio(ej_id):
    """Editar detalles de un ejercicio (series, reps, notas)."""
    ej   = Ejercicio.query.get_or_404(ej_id)
    data = request.get_json()

    campos = ['nombre', 'detalle_base', 'detalle_medio', 'detalle_alto',
              'detalle_avanzado', 'nota', 'seccion']
    for campo in campos:
        if campo in data:
            setattr(ej, campo, data[campo])

    db.session.commit()
    return jsonify(ej.to_dict(Config.get('carga_nivel', 'medio')))
