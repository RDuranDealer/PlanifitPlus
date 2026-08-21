from flask import Blueprint,jsonify,session
from models import db,Ejercicio,Progreso,SesionDia,Config
from datetime import date,timedelta
from collections import defaultdict
bp=Blueprint('rutinas',__name__)
DIAS_INFO={0:{'nombre':'Lunes','label':'Cadena posterior','duracion':'50 min','intensidad':'Baja-Media','dot':'#7F77DD'},1:{'nombre':'Martes','label':'Movilidad','duracion':'45 min','intensidad':'Baja','dot':'#1D9E75'},2:{'nombre':'Miércoles','label':'Rodilla','duracion':'50 min','intensidad':'Media','dot':'#D85A30'},3:{'nombre':'Jueves','label':'Tren superior','duracion':'50 min','intensidad':'Media','dot':'#7F77DD'},4:{'nombre':'Viernes','label':'Core + Tenis','duracion':'45-75 min','intensidad':'Media','dot':'#BA7517'},5:{'nombre':'Sábado','label':'Movilidad global','duracion':'40 min','intensidad':'Muy baja','dot':'#1D9E75'},6:{'nombre':'Domingo','label':'Recuperación','duracion':'30 min','intensidad':'Mínima','dot':'#888780'}}
TIPS={0:'El RDL y el puente de glúteos son la base de protección del LCA.',1:'La rotación torácica limitada hace que el saque y el drive carguen la cervical.',2:'VMO + propiocepción = los dos factores que más predicen ausencia de dolor en cancha.',3:'Desequilibrio pecho fuerte / espalda débil = tensión cervical crónica en tenistas.',4:'Viernes es el día de validación.',5:'La respiración diafragmática baja el tono de trapecios más que cualquier masaje.',6:'El domingo activo es uno de los días más útiles para la recuperación fascial.'}
def uid(): return session.get('usuario_id')
@bp.route('/api/semana')
def semana():
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday()); nivel=Config.get(u,'carga_nivel','medio')
    ses={s.dia_id:s for s in SesionDia.query.filter(SesionDia.usuario_id==u,SesionDia.fecha>=lunes).all()}
    dias=[{'dia_id':di,'nombre':info['nombre'],'label':info['label'],'duracion':info['duracion'],'intensidad':info['intensidad'],'dot':info['dot'],'completado':ses[di].completada if di in ses else False} for di,info in DIAS_INFO.items()]
    return jsonify({'dias':dias,'nivel':nivel,'fase':Config.get(u,'fase_actual','1'),'semana_actual':Config.get(u,'semana_actual','1'),'hoy_dia_id':hoy.weekday()})
@bp.route('/api/rutina/<int:dia_id>')
def rutina_dia(dia_id):
    u=uid()
    if not u: return jsonify({'error':'Sin sesión'}),401
    if dia_id not in DIAS_INFO: return jsonify({'error':'Día inválido'}),404
    hoy=date.today(); nivel=Config.get(u,'carga_nivel','medio')
    ejercicios=Ejercicio.query.filter_by(usuario_id=u,dia_id=dia_id,activo=True).order_by(Ejercicio.orden).all()
    ids=[e.id for e in ejercicios]
    hechos={p.ejercicio_id for p in Progreso.query.filter(Progreso.usuario_id==u,Progreso.ejercicio_id.in_(ids),Progreso.fecha==hoy).all() if p.hecho}
    secs=defaultdict(list)
    for e in ejercicios: secs[e.seccion].append({**e.to_dict(nivel),'hecho':e.id in hechos})
    ses=SesionDia.query.filter_by(usuario_id=u,dia_id=dia_id,fecha=hoy).first()
    return jsonify({'dia_id':dia_id,'info':DIAS_INFO[dia_id],'tip':TIPS.get(dia_id,''),'nivel':nivel,'secciones':[{'nombre':k,'ejercicios':v} for k,v in secs.items()],'completado':ses.completada if ses else False,'total_ex':len(ejercicios),'hechos_ex':len(hechos)})
