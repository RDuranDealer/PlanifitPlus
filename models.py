from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Ejercicio(db.Model):
    __tablename__ = 'ejercicios'
    id          = db.Column(db.Integer, primary_key=True)
    dia_id      = db.Column(db.Integer, nullable=False)       # 0=Lun ... 6=Dom
    seccion     = db.Column(db.String(120), nullable=False)
    nombre      = db.Column(db.String(200), nullable=False)
    detalle_base= db.Column(db.String(300))                   # series/reps base
    detalle_medio  = db.Column(db.String(300))
    detalle_alto   = db.Column(db.String(300))
    detalle_avanzado = db.Column(db.String(300))
    tag         = db.Column(db.String(20), default='keep')    # keep | new | warn
    nota        = db.Column(db.String(400))
    orden       = db.Column(db.Integer, default=0)
    activo      = db.Column(db.Boolean, default=True)

    progresos   = db.relationship('Progreso', backref='ejercicio', lazy=True)

    def detalle_para_nivel(self, nivel):
        mapa = {
            'bajo':     self.detalle_base,
            'medio':    self.detalle_medio or self.detalle_base,
            'alto':     self.detalle_alto  or self.detalle_medio or self.detalle_base,
            'avanzado': self.detalle_avanzado or self.detalle_alto or self.detalle_medio or self.detalle_base,
        }
        return mapa.get(nivel, self.detalle_base)

    def to_dict(self, nivel='medio'):
        return {
            'id':      self.id,
            'nombre':  self.nombre,
            'detalle': self.detalle_para_nivel(nivel),
            'tag':     self.tag,
            'nota':    self.nota,
            'activo':  self.activo,
        }


class Progreso(db.Model):
    __tablename__ = 'progreso'
    id           = db.Column(db.Integer, primary_key=True)
    ejercicio_id = db.Column(db.Integer, db.ForeignKey('ejercicios.id'), nullable=False)
    fecha        = db.Column(db.Date, default=date.today, nullable=False)
    hecho        = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('ejercicio_id', 'fecha', name='uq_progreso_dia'),
    )


class SesionDia(db.Model):
    __tablename__ = 'sesiones_dia'
    id          = db.Column(db.Integer, primary_key=True)
    fecha       = db.Column(db.Date, default=date.today, nullable=False, unique=True)
    dia_id      = db.Column(db.Integer, nullable=False)
    completada  = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Config(db.Model):
    __tablename__ = 'config'
    id           = db.Column(db.Integer, primary_key=True)
    clave        = db.Column(db.String(80), unique=True, nullable=False)
    valor        = db.Column(db.String(200), nullable=False)
    descripcion  = db.Column(db.String(300))

    @classmethod
    def get(cls, clave, default=None):
        row = cls.query.filter_by(clave=clave).first()
        return row.valor if row else default

    @classmethod
    def set(cls, clave, valor, descripcion=None):
        row = cls.query.filter_by(clave=clave).first()
        if row:
            row.valor = str(valor)
        else:
            row = cls(clave=clave, valor=str(valor), descripcion=descripcion)
            db.session.add(row)
        db.session.commit()
