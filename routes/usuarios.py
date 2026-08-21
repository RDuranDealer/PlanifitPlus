from flask import Blueprint,jsonify,request,session
from models import db,Usuario,Config,AVATARES
bp=Blueprint('usuarios',__name__)
@bp.route('/api/usuarios')
def listar():
    return jsonify([u.to_dict() for u in Usuario.query.filter_by(activo=True).order_by(Usuario.created_at).all()])
@bp.route('/api/usuarios',methods=['POST'])
def crear():
    data=request.get_json(); nombre=data.get('nombre','').strip(); avatar=data.get('avatar','🎾'); pin=data.get('pin','') or None
    if not nombre: return jsonify({'error':'Nombre requerido'}),400
    if pin and (not pin.isdigit() or len(pin)!=4): return jsonify({'error':'PIN debe ser 4 dígitos'}),400
    u=Usuario(nombre=nombre,avatar=avatar,pin=pin); db.session.add(u); db.session.flush()
    for clave,valor,desc in [('fase_actual','1','Fase'),('carga_nivel','medio','Carga'),('semana_actual','1','Semana')]:
        db.session.add(Config(usuario_id=u.id,clave=clave,valor=valor,descripcion=desc))
    db.session.commit()
    return jsonify(u.to_dict()),201
@bp.route('/api/usuarios/<int:uid>/login',methods=['POST'])
def login(uid):
    data=request.get_json(); pin=data.get('pin','').strip()
    u=Usuario.query.get_or_404(uid)
    if u.pin and u.pin!=pin: return jsonify({'error':'PIN incorrecto'}),401
    session['usuario_id']=u.id
    return jsonify({'ok':True,'usuario':u.to_dict()})
@bp.route('/api/usuarios/session')
def get_session():
    uid=session.get('usuario_id')
    if not uid: return jsonify({'usuario':None})
    u=Usuario.query.get(uid)
    return jsonify({'usuario':u.to_dict() if u else None})
@bp.route('/api/usuarios/logout',methods=['POST'])
def logout():
    session.pop('usuario_id',None); return jsonify({'ok':True})
@bp.route('/api/usuarios/<int:uid>',methods=['PUT'])
def editar(uid):
    u=Usuario.query.get_or_404(uid); data=request.get_json()
    if 'nombre' in data: u.nombre=data['nombre'].strip()
    if 'avatar' in data: u.avatar=data['avatar']
    if 'pin' in data:
        pin=data['pin'] or None
        if pin and (not pin.isdigit() or len(pin)!=4): return jsonify({'error':'PIN 4 dígitos'}),400
        u.pin=pin
    db.session.commit(); return jsonify(u.to_dict())
@bp.route('/api/usuarios/<int:uid>',methods=['DELETE'])
def eliminar(uid):
    u=Usuario.query.get_or_404(uid); u.activo=False; db.session.commit()
    return jsonify({'ok':True})
@bp.route('/api/avatares')
def avatares():
    return jsonify(AVATARES)
