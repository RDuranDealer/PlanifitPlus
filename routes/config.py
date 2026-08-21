from flask import Blueprint,jsonify,request,session
from models import db,Config,Ejercicio
bp=Blueprint('config',__name__)
NIVELES=['bajo','medio','alto','avanzado']
FASES=['1','2','3']
def uid(): return session.get('usuario_id')
@bp.route('/api/config')
def get_config():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    return jsonify({'fase_actual':Config.get(u,'fase_actual','1'),'carga_nivel':Config.get(u,'carga_nivel','medio'),'semana_actual':Config.get(u,'semana_actual','1')})
@bp.route('/api/config/carga',methods=['POST'])
def set_carga():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    nivel=request.get_json().get('nivel','').lower()
    if nivel not in NIVELES: return jsonify({'error':'Nivel inválido'}),400
    Config.set(u,'carga_nivel',nivel); return jsonify({'carga_nivel':nivel})
@bp.route('/api/config/fase',methods=['POST'])
def set_fase():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    fase=str(request.get_json().get('fase',''))
    if fase not in FASES: return jsonify({'error':'Fase inválida'}),400
    Config.set(u,'fase_actual',fase); return jsonify({'fase_actual':fase})
@bp.route('/api/config/semana',methods=['POST'])
def set_semana():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    semana=str(request.get_json().get('semana','1'))
    Config.set(u,'semana_actual',semana); return jsonify({'semana_actual':semana})
@bp.route('/api/ejercicio/<int:ej_id>/toggle',methods=['POST'])
def toggle_activo(ej_id):
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    ej=Ejercicio.query.filter_by(id=ej_id,usuario_id=u).first_or_404()
    ej.activo=not ej.activo; db.session.commit()
    return jsonify({'id':ej.id,'activo':ej.activo})
