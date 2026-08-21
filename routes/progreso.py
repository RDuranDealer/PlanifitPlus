from flask import Blueprint,jsonify,request,session
from models import db,Progreso,SesionDia,Ejercicio
from datetime import date,timedelta
from sqlalchemy import func
bp=Blueprint('progreso',__name__)
def uid(): return session.get('usuario_id')
@bp.route('/api/progreso',methods=['POST'])
def toggle_ejercicio():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    data=request.get_json(); eid=data.get('ejercicio_id'); fecha=date.today()
    ej=Ejercicio.query.filter_by(id=eid,usuario_id=u).first()
    if not ej: return jsonify({'error':'No encontrado'}),404
    reg=Progreso.query.filter_by(usuario_id=u,ejercicio_id=eid,fecha=fecha).first()
    if reg: reg.hecho=not reg.hecho
    else:
        reg=Progreso(usuario_id=u,ejercicio_id=eid,fecha=fecha,hecho=True)
        db.session.add(reg)
    db.session.commit()
    return jsonify({'hecho':reg.hecho,'ejercicio_id':eid})
@bp.route('/api/sesion/completar',methods=['POST'])
def completar_sesion():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    data=request.get_json(); dia_id=data.get('dia_id'); fecha=date.today()
    s=SesionDia.query.filter_by(usuario_id=u,dia_id=dia_id,fecha=fecha).first()
    if s: s.completada=not s.completada
    else:
        s=SesionDia(usuario_id=u,dia_id=dia_id,fecha=fecha,completada=True)
        db.session.add(s)
    db.session.commit()
    return jsonify({'completada':s.completada,'dia_id':dia_id})
@bp.route('/api/historial')
def historial():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    hace12=date.today()-timedelta(weeks=12)
    sesiones=SesionDia.query.filter(SesionDia.usuario_id==u,SesionDia.fecha>=hace12,SesionDia.completada==True).all()
    pw={}
    for s in sesiones:
        iso=s.fecha.isocalendar(); c=f"{iso.year}-W{iso.week:02d}"; pw[c]=pw.get(c,0)+1
    sems=sorted(pw.items()); tw=len(pw)
    prom=round(sum(pw.values())/tw,1) if tw else 0
    mejor=max(pw.values()) if pw else 0
    return jsonify({'semanas':[{'semana':k,'dias':v} for k,v in sems],'total_semanas':tw,'promedio':prom,'mejor':mejor,'semanas_5plus':sum(1 for v in pw.values() if v>=5)})
@bp.route('/api/stats/semana')
def stats_semana():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday())
    dc=SesionDia.query.filter(SesionDia.usuario_id==u,SesionDia.fecha>=lunes,SesionDia.completada==True).count()
    eh=db.session.query(func.count(Progreso.id)).filter(Progreso.usuario_id==u,Progreso.fecha>=lunes,Progreso.hecho==True).scalar() or 0
    return jsonify({'dias_completados':dc,'ejercicios_hechos':eh,'adherencia_pct':round(dc/7*100),'dias_restantes':7-dc})
