from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()
AVATARES = ['🎾','💪','🏃','⚡','🔥','🦁','🐯','🦅','🌟','⚽']

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id=db.Column(db.Integer,primary_key=True)
    nombre=db.Column(db.String(80),nullable=False)
    avatar=db.Column(db.String(10),default='🎾')
    pin=db.Column(db.String(4),nullable=True)
    activo=db.Column(db.Boolean,default=True)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    ejercicios=db.relationship('Ejercicio',backref='usuario',lazy=True,cascade='all, delete-orphan')
    progresos=db.relationship('Progreso',backref='usuario',lazy=True,cascade='all, delete-orphan')
    sesiones=db.relationship('SesionDia',backref='usuario',lazy=True,cascade='all, delete-orphan')
    configs=db.relationship('Config',backref='usuario',lazy=True,cascade='all, delete-orphan')
    def to_dict(self):
        return {'id':self.id,'nombre':self.nombre,'avatar':self.avatar,'tiene_pin':bool(self.pin)}

class Ejercicio(db.Model):
    __tablename__ = 'ejercicios'
    id=db.Column(db.Integer,primary_key=True)
    usuario_id=db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    dia_id=db.Column(db.Integer,nullable=False)
    seccion=db.Column(db.String(120),nullable=False)
    nombre=db.Column(db.String(200),nullable=False)
    detalle_base=db.Column(db.String(300))
    detalle_medio=db.Column(db.String(300))
    detalle_alto=db.Column(db.String(300))
    detalle_avanzado=db.Column(db.String(300))
    tag=db.Column(db.String(20),default='keep')
    nota=db.Column(db.String(400))
    video_url=db.Column(db.String(500))        # URL de YouTube
    pasos=db.Column(db.Text)                    # Descripción paso a paso (texto plano con \n)
    orden=db.Column(db.Integer,default=0)
    activo=db.Column(db.Boolean,default=True)
    progresos=db.relationship('Progreso',backref='ejercicio',lazy=True)
    def detalle_para_nivel(self,nivel):
        m={'bajo':self.detalle_base,'medio':self.detalle_medio or self.detalle_base,'alto':self.detalle_alto or self.detalle_medio or self.detalle_base,'avanzado':self.detalle_avanzado or self.detalle_alto or self.detalle_medio or self.detalle_base}
        return m.get(nivel,self.detalle_base)
    def to_dict(self,nivel='medio'):
        return {'id':self.id,'nombre':self.nombre,'detalle':self.detalle_para_nivel(nivel),'tag':self.tag,'nota':self.nota,'video_url':self.video_url or '','pasos':self.pasos or '','activo':self.activo}

class Progreso(db.Model):
    __tablename__ = 'progreso'
    id=db.Column(db.Integer,primary_key=True)
    usuario_id=db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    ejercicio_id=db.Column(db.Integer,db.ForeignKey('ejercicios.id'),nullable=False)
    fecha=db.Column(db.Date,default=date.today,nullable=False)
    hecho=db.Column(db.Boolean,default=False)
    __table_args__=(db.UniqueConstraint('usuario_id','ejercicio_id','fecha',name='uq_prog'),)

class SesionDia(db.Model):
    __tablename__ = 'sesiones_dia'
    id=db.Column(db.Integer,primary_key=True)
    usuario_id=db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    fecha=db.Column(db.Date,default=date.today,nullable=False)
    dia_id=db.Column(db.Integer,nullable=False)
    completada=db.Column(db.Boolean,default=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    __table_args__=(db.UniqueConstraint('usuario_id','dia_id','fecha',name='uq_sesion'),)

class Config(db.Model):
    __tablename__ = 'config'
    id=db.Column(db.Integer,primary_key=True)
    usuario_id=db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    clave=db.Column(db.String(80),nullable=False)
    valor=db.Column(db.String(200),nullable=False)
    descripcion=db.Column(db.String(300))
    __table_args__=(db.UniqueConstraint('usuario_id','clave',name='uq_cfg'),)
    @classmethod
    def get(cls,usuario_id,clave,default=None):
        row=cls.query.filter_by(usuario_id=usuario_id,clave=clave).first()
        return row.valor if row else default
    @classmethod
    def set(cls,usuario_id,clave,valor,descripcion=None):
        row=cls.query.filter_by(usuario_id=usuario_id,clave=clave).first()
        if row: row.valor=str(valor)
        else:
            row=cls(usuario_id=usuario_id,clave=clave,valor=str(valor),descripcion=descripcion)
            db.session.add(row)
        db.session.commit()
