from app import app
from models import db, Usuario, Ejercicio, Config

DATOS_EJERCICIOS = [
    # DIA 0 — Lunes
    (0,'Postura RPG + core','Postura RPG en pared','1×3 min','1×4 min','2×3 min','2×4 min','keep','Sin flexión lumbar forzada. Espalda neutra.'),
    (0,'Postura RPG + core','Puente de glúteos','3×15','4×15','4×15 + 2 seg pausa','4×20 + 2 seg pausa','keep',''),
    (0,'Postura RPG + core','Plancha frontal en codos','3×30 seg','3×40 seg','4×40 seg','4×50 seg','keep','Cuello neutro. No dejar caer la cabeza.'),
    (0,'Cadena posterior','Peso muerto rumano (RDL)','3×12 — 20 kg','3×12 — 25 kg','4×10 — 30 kg','4×10 — 35 kg','keep','Espalda neutra. Descenso 3 seg excéntrico.'),
    (0,'Cadena posterior','TRX Row','3×12','4×12','4×12 — tempo 3-1-1','4×15 — tempo 3-1-1','keep','Escápulas activas al final del recorrido.'),
    (0,'Cadena posterior','Estiramiento cadena posterior','1×2 min','1×2 min','2×2 min','2×3 min','keep',''),
    (0,'Nuevo — estabilizadores rodilla','Clamshell con banda','3×15 c/lado','3×20 c/lado','4×20 c/lado','4×25 c/lado','new','Activa glúteo medio = rótula centrada en cancha.'),
    (0,'Nuevo — estabilizadores rodilla','Mini-band side-step','3×12 pasos c/lado','3×15 pasos c/lado','4×15 pasos','4×20 pasos','new','Simula desplazamiento lateral de tenis.'),
    # DIA 1 — Martes
    (1,'Cervical y torácico','Movilidad cervical guiada','2×8 c/lado','2×10 c/lado','3×10 c/lado','3×12 c/lado','keep','C4-C5: rango libre de dolor. Nunca forzar.'),
    (1,'Cervical y torácico','Movilidad torácica en roller','1×2 min','1×3 min','2×2 min','2×3 min','keep','Foco T4-T8. No apoyar en cervical.'),
    (1,'Cervical y torácico','Rotación torácica en cuadrupedia','3×8 c/lado','3×10 c/lado','4×10 c/lado','4×12 c/lado','new','Mejora rotación de torso en drive y revés.'),
    (1,'Fuerza y estiramiento','TRX Chest Press','3×12','4×12','4×12 — tempo 2-0-2','4×15 — tempo 2-0-2','keep',''),
    (1,'Fuerza y estiramiento','Curl de bíceps','3×12 — 10 kg','3×12 — 12 kg','4×12 — 14 kg','4×12 — 16 kg','keep',''),
    (1,'Fuerza y estiramiento','Estiramiento psoas','3×40 seg c/lado','3×50 seg c/lado','4×50 seg','4×60 seg','keep','Psoas tenso = carga en rodilla. Prioridad.'),
    (1,'Fuerza y estiramiento','Respiración + elongación','1×3 min','1×4 min','2×3 min','2×4 min','keep',''),
    (1,'Nuevo — escapular para saque','TRX Y-raise','3×12','4×12','4×15','4×15 — pausa 2 seg arriba','new','Escápulas hacia columna. Prepara hombro para saque.'),
    # DIA 2 — Miércoles
    (2,'VMO y estabilidad','Mini sentadilla 20° (VMO)','3×15','4×15','4×20','4×20 — 2 seg pausa abajo','keep','Rodilla no pasa punta del pie. Detener si hay dolor.'),
    (2,'VMO y estabilidad','Abducción de cadera','3×15 c/lado','4×15 c/lado','4×20 c/lado','4×20 + banda','keep',''),
    (2,'VMO y estabilidad','Extensión de rodilla','3×15 — rango 0-60°','4×15','4×20','4×20 — excéntrico 4 seg','keep','Rango 0-60° siempre.'),
    (2,'VMO y estabilidad','Elevación de talones','3×20','3×25','4×25','4×30 — unipodal','keep',''),
    (2,'VMO y estabilidad','TRX equilibrio 1 pierna','3×30 seg c/lado','3×40 seg','4×40 seg','4×45 seg — ojos cerrados','keep',''),
    (2,'VMO y estabilidad','Hielo en rodilla post-sesión','10-15 min','10-15 min','10-15 min','10-15 min','warn','Con paño entre hielo y piel. Siempre.'),
    (2,'Nuevo — propiocepción post-LCA','Equilibrio monopodal ojos cerrados','3×20 seg c/lado','3×25 seg','4×25 seg — toalla','4×30 seg — toalla','new','Regenera feedback propioceptivo perdido con la cirugía.'),
    (2,'Nuevo — propiocepción post-LCA','Step-up lateral con pesa','3×10 c/lado — sin peso','3×10 — 5 kg','3×12 — 8 kg','4×12 — 10 kg','new','Simula paso lateral de tenis. Empuja con talón.'),
    # DIA 3 — Jueves
    (3,'Escapular (prioridad alta)','TRX Y-T-W escapular','3×10 c/posición','3×12 c/posición','4×12','4×15','keep','Sin press militar ni carga axial cervical.'),
    (3,'Escapular (prioridad alta)','Press de pecho (tumbado)','3×12 — 16 kg','3×12 — 20 kg','4×10 — 24 kg','4×10 — 28 kg','keep',''),
    (3,'Escapular (prioridad alta)','TRX Row con supinación','3×12','4×12','4×12 — tempo 3-1-1','4×15 — tempo 3-1-1','keep',''),
    (3,'Escapular (prioridad alta)','Face pull TRX','3×15','4×15','4×20','4×20 — pausa 2 seg','keep','Codos altos. Clave contra tensión cervical.'),
    (3,'Escapular (prioridad alta)','Extensión de tríceps','3×12 — 10 kg','3×12 — 12 kg','4×12 — 14 kg','4×15 — 14 kg','keep',''),
    (3,'Escapular (prioridad alta)','Postura RPG elongación','1×3 min','1×4 min','2×3 min','2×4 min','keep',''),
    (3,'Nuevo — potencia de golpe','TRX Pallof press anti-rotación','3×10 c/lado','3×12 c/lado','4×12','4×15','new','Core estable = golpes potentes sin lesionar lumbar.'),
    (3,'Nuevo — potencia de golpe','Press unilateral TRX — imitación drive','3×10 c/lado','3×12 c/lado','4×12','4×15 — explosivo','new','Patrón específico de forehand. Cabeza neutra.'),
    # DIA 4 — Viernes
    (4,'Core profundo','Respiración 360°','2×10 resp.','2×12 resp.','3×12 resp.','3×15 resp.','keep',''),
    (4,'Core profundo','Dead bug','3×10 alt.','3×12 alt.','4×12 alt.','4×15 alt. — lento','keep','Extensión contralateral lenta y controlada.'),
    (4,'Core profundo','Plancha lateral','3×25 seg c/lado','3×30 seg','4×35 seg','4×40 seg','keep','Cuello neutro.'),
    (4,'Core profundo','TRX Pallof press','3×10 c/lado','3×12 c/lado','4×12','4×15','keep',''),
    (4,'Core profundo','Farmer carry 1 mano','3×20 m c/lado','3×25 m — 16 kg','4×25 m — 20 kg','4×30 m — 24 kg','keep',''),
    (4,'Core profundo','Estiramiento lateral','2×1 min c/lado','2×90 seg','3×90 seg','3×2 min','keep',''),
    (4,'Tenis técnico (solo si 0 dolor)','Calentamiento + activación clamshell','10 min','10 min','12 min','15 min','new','No saltarse.'),
    (4,'Tenis técnico (solo si 0 dolor)','Peloteo suave desde fondo','20 min — ritmo bajo','25 min','30 min','35 min','new','Parar si dolor > 3/10. Sin excepciones.'),
    (4,'Tenis técnico (solo si 0 dolor)','Hielo en rodilla si hay calor','10-15 min','10-15 min','10-15 min','10-15 min','warn','Protocolo preventivo.'),
    # DIA 5 — Sábado
    (5,'Movilidad general','Caminata terreno plano','30 min','35 min','40 min','45 min','keep','Zapatillas con buena amortiguación.'),
    (5,'Movilidad general','Movilidad de cadera — círculos','2×8 c/lado','2×10 c/lado','3×10','3×12','keep',''),
    (5,'Movilidad general','Movilidad torácica — rotaciones sentado','2×8 c/lado','2×10 c/lado','3×10','3×12','keep',''),
    (5,'Movilidad general','Elongación cervical suave','2×30 seg c/lado','2×40 seg','3×40 seg','3×50 seg','keep','Inclinaciones laterales. Sin forzar.'),
    (5,'Cervical y fascia','Automasaje suboccipital (2 pelotas tenis)','5 min','6 min','8 min','10 min','new','Base del cráneo. Alivia tensión de trapecios.'),
    (5,'Cervical y fascia','Respiración diafragmática en decúbito','8 min','10 min','12 min','15 min','new','Exhalación prolongada. Base de la RPG.'),
    # DIA 6 — Domingo
    (6,'Posturas y automasaje','Postura de rana','3 min','4 min','5 min','5 min','keep',''),
    (6,'Posturas y automasaje',"Child's pose adaptada",'2 min','3 min','3 min','4 min','keep','Sin presión en cervical.'),
    (6,'Posturas y automasaje','Isquiotibiales en pared','2 min c/pierna','3 min c/pierna','3 min','4 min','keep',''),
    (6,'Posturas y automasaje','Automasaje pelota de tenis','5 min','8 min','10 min','12 min','keep','Pie, gemelos, glúteo.'),
    (6,'Posturas y automasaje','Respiración / meditación','5 min','8 min','10 min','10 min','keep',''),
]


def cargar_ejercicios_usuario(usuario_id):
    for orden, row in enumerate(DATOS_EJERCICIOS):
        dia_id, seccion, nombre, base, medio, alto, avanzado, tag, nota = row
        e = Ejercicio(
            usuario_id=usuario_id, dia_id=dia_id, seccion=seccion,
            nombre=nombre, detalle_base=base, detalle_medio=medio,
            detalle_alto=alto, detalle_avanzado=avanzado,
            tag=tag, nota=nota, orden=orden,
        )
        db.session.add(e)


def seed():
    with app.app_context():
        db.create_all()

        if Usuario.query.count() > 0:
            print("Ya existen datos. Saltando seed.")
            return

        # Crear usuario Rodrigo por defecto
        rodrigo = Usuario(nombre='Rodrigo', avatar='🎾', pin=None)
        db.session.add(rodrigo)
        db.session.flush()

        # Cargar ejercicios para Rodrigo
        cargar_ejercicios_usuario(rodrigo.id)

        # Config por defecto para Rodrigo
        for clave, valor, desc in [
            ('fase_actual',   '2',    'Fase del programa'),
            ('carga_nivel',   'alto', 'Nivel de carga'),
            ('semana_actual', '1',    'Semana actual'),
        ]:
            db.session.add(Config(usuario_id=rodrigo.id, clave=clave, valor=valor, descripcion=desc))

        db.session.commit()
        print(f"Seed completado: usuario Rodrigo + {Ejercicio.query.count()} ejercicios.")


if __name__ == '__main__':
    seed()
