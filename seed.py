"""
Poblar la base de datos con los ejercicios del plan RPG Tenis — Fase 2.
Ejecutar una sola vez: python seed.py
"""
from app import app
from models import db, Ejercicio, Config

DIAS = [
    # DIA 0 — Lunes
    {
        'dia_id': 0, 'seccion': 'Postura RPG + core',
        'ejercicios': [
            ('Postura RPG en pared',
             '1×3 min', '1×4 min', '2×3 min', '2×4 min',
             'keep', 'Sin flexión lumbar forzada. Espalda neutra.'),
            ('Puente de glúteos',
             '3×15', '4×15', '4×15 + 2 seg pausa', '4×20 + 2 seg pausa',
             'keep', ''),
            ('Plancha frontal en codos',
             '3×30 seg', '3×40 seg', '4×40 seg', '4×50 seg',
             'keep', 'Cuello neutro. No dejar caer la cabeza.'),
        ]
    },
    {
        'dia_id': 0, 'seccion': 'Cadena posterior',
        'ejercicios': [
            ('Peso muerto rumano (RDL)',
             '3×12 — 20 kg', '3×12 — 25 kg', '4×10 — 30 kg', '4×10 — 35 kg',
             'keep', 'Espalda neutra. Descenso 3 seg excéntrico.'),
            ('TRX Row',
             '3×12', '4×12', '4×12 — tempo 3-1-1', '4×15 — tempo 3-1-1',
             'keep', 'Escápulas activas al final del recorrido.'),
            ('Estiramiento cadena posterior',
             '1×2 min', '1×2 min', '2×2 min', '2×3 min',
             'keep', ''),
        ]
    },
    {
        'dia_id': 0, 'seccion': 'Nuevo — estabilizadores rodilla',
        'ejercicios': [
            ('Clamshell con banda',
             '3×15 c/lado', '3×20 c/lado', '4×20 c/lado', '4×25 c/lado',
             'new', 'Activa glúteo medio = rótula centrada en cancha.'),
            ('Mini-band side-step',
             '3×12 pasos c/lado', '3×15 pasos c/lado', '4×15 pasos', '4×20 pasos',
             'new', 'Simula desplazamiento lateral de tenis.'),
        ]
    },

    # DIA 1 — Martes
    {
        'dia_id': 1, 'seccion': 'Cervical y torácico',
        'ejercicios': [
            ('Movilidad cervical guiada',
             '2×8 c/lado', '2×10 c/lado', '3×10 c/lado', '3×12 c/lado',
             'keep', 'C4-C5: rango libre de dolor. Nunca forzar.'),
            ('Movilidad torácica en roller',
             '1×2 min', '1×3 min', '2×2 min', '2×3 min',
             'keep', 'Foco T4-T8. No apoyar en cervical.'),
            ('Rotación torácica en cuadrupedia',
             '3×8 c/lado', '3×10 c/lado', '4×10 c/lado', '4×12 c/lado',
             'new', 'Mejora rotación de torso en drive y revés.'),
        ]
    },
    {
        'dia_id': 1, 'seccion': 'Fuerza y estiramiento',
        'ejercicios': [
            ('TRX Chest Press',
             '3×12', '4×12', '4×12 — tempo 2-0-2', '4×15 — tempo 2-0-2',
             'keep', ''),
            ('Curl de bíceps',
             '3×12 — 10 kg', '3×12 — 12 kg', '4×12 — 14 kg', '4×12 — 16 kg',
             'keep', ''),
            ('Estiramiento psoas',
             '3×40 seg c/lado', '3×50 seg c/lado', '4×50 seg', '4×60 seg',
             'keep', 'Psoas tenso = carga en rodilla. Prioridad.'),
            ('Respiración + elongación',
             '1×3 min', '1×4 min', '2×3 min', '2×4 min',
             'keep', ''),
        ]
    },
    {
        'dia_id': 1, 'seccion': 'Nuevo — escapular para saque',
        'ejercicios': [
            ('TRX Y-raise',
             '3×12', '4×12', '4×15', '4×15 — pausa 2 seg arriba',
             'new', 'Escápulas hacia columna. Prepara hombro para saque.'),
        ]
    },

    # DIA 2 — Miércoles
    {
        'dia_id': 2, 'seccion': 'VMO y estabilidad',
        'ejercicios': [
            ('Mini sentadilla 20° (VMO)',
             '3×15', '4×15', '4×20', '4×20 — 2 seg pausa abajo',
             'keep', 'Rodilla no pasa punta del pie. Detener si hay dolor.'),
            ('Abducción de cadera',
             '3×15 c/lado', '4×15 c/lado', '4×20 c/lado', '4×20 + banda',
             'keep', ''),
            ('Extensión de rodilla',
             '3×15 — rango 0-60°', '4×15', '4×20', '4×20 — excéntrico 4 seg',
             'keep', 'Rango 0-60° siempre. No forzar extensión completa.'),
            ('Elevación de talones',
             '3×20', '3×25', '4×25', '4×30 — unipodal',
             'keep', ''),
            ('TRX equilibrio 1 pierna',
             '3×30 seg c/lado', '3×40 seg', '4×40 seg', '4×45 seg — ojos cerrados',
             'keep', ''),
            ('Hielo en rodilla post-sesión',
             '10-15 min', '10-15 min', '10-15 min', '10-15 min',
             'warn', 'Con paño entre hielo y piel. Siempre.'),
        ]
    },
    {
        'dia_id': 2, 'seccion': 'Nuevo — propiocepción post-LCA',
        'ejercicios': [
            ('Equilibrio monopodal ojos cerrados',
             '3×20 seg c/lado', '3×25 seg', '4×25 seg — toalla', '4×30 seg — toalla',
             'new', 'Regenera feedback propioceptivo perdido con la cirugía.'),
            ('Step-up lateral con pesa',
             '3×10 c/lado — sin peso', '3×10 — 5 kg', '3×12 — 8 kg', '4×12 — 10 kg',
             'new', 'Simula paso lateral de tenis. Empuja con talón.'),
        ]
    },

    # DIA 3 — Jueves
    {
        'dia_id': 3, 'seccion': 'Escapular (prioridad alta)',
        'ejercicios': [
            ('TRX Y-T-W escapular',
             '3×10 c/posición', '3×12 c/posición', '4×12', '4×15',
             'keep', 'Sin press militar ni carga axial cervical.'),
            ('Press de pecho (tumbado)',
             '3×12 — 16 kg', '3×12 — 20 kg', '4×10 — 24 kg', '4×10 — 28 kg',
             'keep', ''),
            ('TRX Row con supinación',
             '3×12', '4×12', '4×12 — tempo 3-1-1', '4×15 — tempo 3-1-1',
             'keep', ''),
            ('Face pull TRX',
             '3×15', '4×15', '4×20', '4×20 — pausa 2 seg',
             'keep', 'Codos altos. Clave contra tensión cervical.'),
            ('Extensión de tríceps',
             '3×12 — 10 kg', '3×12 — 12 kg', '4×12 — 14 kg', '4×15 — 14 kg',
             'keep', ''),
            ('Postura RPG elongación',
             '1×3 min', '1×4 min', '2×3 min', '2×4 min',
             'keep', ''),
        ]
    },
    {
        'dia_id': 3, 'seccion': 'Nuevo — potencia de golpe',
        'ejercicios': [
            ('TRX Pallof press anti-rotación',
             '3×10 c/lado', '3×12 c/lado', '4×12', '4×15',
             'new', 'Core estable = golpes potentes sin lesionar lumbar.'),
            ('Press unilateral TRX — imitación drive',
             '3×10 c/lado', '3×12 c/lado', '4×12', '4×15 — explosivo',
             'new', 'Patrón específico de forehand. Cabeza neutra siempre.'),
        ]
    },

    # DIA 4 — Viernes
    {
        'dia_id': 4, 'seccion': 'Core profundo',
        'ejercicios': [
            ('Respiración 360°',
             '2×10 resp.', '2×12 resp.', '3×12 resp.', '3×15 resp.',
             'keep', ''),
            ('Dead bug',
             '3×10 alt.', '3×12 alt.', '4×12 alt.', '4×15 alt. — lento',
             'keep', 'Extensión contralateral lenta y controlada.'),
            ('Plancha lateral',
             '3×25 seg c/lado', '3×30 seg', '4×35 seg', '4×40 seg',
             'keep', 'Cuello neutro. No dejar caer la cadera.'),
            ('TRX Pallof press',
             '3×10 c/lado', '3×12 c/lado', '4×12', '4×15',
             'keep', ''),
            ('Farmer carry 1 mano',
             '3×20 m c/lado', '3×25 m — 16 kg', '4×25 m — 20 kg', '4×30 m — 24 kg',
             'keep', ''),
            ('Estiramiento lateral',
             '2×1 min c/lado', '2×90 seg', '3×90 seg', '3×2 min',
             'keep', ''),
        ]
    },
    {
        'dia_id': 4, 'seccion': 'Tenis técnico (solo si 0 dolor)',
        'ejercicios': [
            ('Calentamiento + activación clamshell',
             '10 min', '10 min', '12 min', '15 min',
             'new', 'No saltarse. Activa glúteo antes de cancha.'),
            ('Peloteo suave desde fondo',
             '20 min — ritmo bajo', '25 min', '30 min', '35 min',
             'new', 'Parar si dolor > 3/10. Sin excepciones.'),
            ('Hielo en rodilla si hay calor',
             '10-15 min', '10-15 min', '10-15 min', '10-15 min',
             'warn', 'Protocolo preventivo. No esperar que duela.'),
        ]
    },

    # DIA 5 — Sábado
    {
        'dia_id': 5, 'seccion': 'Movilidad general',
        'ejercicios': [
            ('Caminata terreno plano',
             '30 min', '35 min', '40 min', '45 min',
             'keep', 'Zapatillas con buena amortiguación.'),
            ('Movilidad de cadera — círculos',
             '2×8 c/lado', '2×10 c/lado', '3×10', '3×12',
             'keep', ''),
            ('Movilidad torácica — rotaciones sentado',
             '2×8 c/lado', '2×10 c/lado', '3×10', '3×12',
             'keep', ''),
            ('Elongación cervical suave',
             '2×30 seg c/lado', '2×40 seg', '3×40 seg', '3×50 seg',
             'keep', 'Inclinaciones laterales. Sin forzar.'),
        ]
    },
    {
        'dia_id': 5, 'seccion': 'Cervical y fascia',
        'ejercicios': [
            ('Automasaje suboccipital (2 pelotas tenis)',
             '5 min', '6 min', '8 min', '10 min',
             'new', 'Base del cráneo. Alivia tensión de trapecios.'),
            ('Respiración diafragmática en decúbito',
             '8 min', '10 min', '12 min', '15 min',
             'new', 'Exhalación prolongada. Base de la RPG.'),
        ]
    },

    # DIA 6 — Domingo
    {
        'dia_id': 6, 'seccion': 'Posturas y automasaje',
        'ejercicios': [
            ('Postura de rana',
             '3 min', '4 min', '5 min', '5 min',
             'keep', 'Cadena posterior y adductores.'),
            ("Child's pose adaptada",
             '2 min', '3 min', '3 min', '4 min',
             'keep', 'Sin presión en cervical.'),
            ('Isquiotibiales en pared',
             '2 min c/pierna', '3 min c/pierna', '3 min', '4 min',
             'keep', ''),
            ('Automasaje pelota de tenis',
             'Pie, gemelos, glúteo — 5 min', '8 min', '10 min', '12 min',
             'keep', ''),
            ('Respiración / meditación',
             '5 min', '8 min', '10 min', '10 min',
             'keep', ''),
        ]
    },
]

DIAS_INFO = {
    0: {'nombre': 'Lunes',    'label': 'Cadena posterior', 'duracion': '50 min', 'intensidad': 'Baja-Media'},
    1: {'nombre': 'Martes',   'label': 'Movilidad',        'duracion': '45 min', 'intensidad': 'Baja'},
    2: {'nombre': 'Miércoles','label': 'Rodilla',          'duracion': '50 min', 'intensidad': 'Media'},
    3: {'nombre': 'Jueves',   'label': 'Tren superior',    'duracion': '50 min', 'intensidad': 'Media'},
    4: {'nombre': 'Viernes',  'label': 'Core + Tenis',     'duracion': '45-75 min', 'intensidad': 'Media'},
    5: {'nombre': 'Sábado',   'label': 'Movilidad global', 'duracion': '40 min', 'intensidad': 'Muy baja'},
    6: {'nombre': 'Domingo',  'label': 'Recuperación',     'duracion': '30 min', 'intensidad': 'Mínima'},
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


def seed():
    with app.app_context():
        db.create_all()

        # Solo poblar si no hay ejercicios
        if Ejercicio.query.count() > 0:
            print("Ya existen datos. Saltando seed.")
            return

        orden = 0
        for bloque in DIAS:
            dia_id = bloque['dia_id']
            seccion = bloque['seccion']
            for ex in bloque['ejercicios']:
                nombre, base, medio, alto, avanzado, tag, nota = ex
                e = Ejercicio(
                    dia_id=dia_id,
                    seccion=seccion,
                    nombre=nombre,
                    detalle_base=base,
                    detalle_medio=medio,
                    detalle_alto=alto,
                    detalle_avanzado=avanzado,
                    tag=tag,
                    nota=nota,
                    orden=orden,
                )
                db.session.add(e)
                orden += 1

        # Config por defecto
        defaults = [
            ('fase_actual',    '2',    'Fase del programa (1, 2 o 3)'),
            ('carga_nivel',    'alto', 'Nivel de carga: bajo | medio | alto | avanzado'),
            ('semana_actual',  '1',    'Semana dentro de la fase actual'),
        ]
        for clave, valor, desc in defaults:
            if not Config.query.filter_by(clave=clave).first():
                db.session.add(Config(clave=clave, valor=valor, descripcion=desc))

        db.session.commit()
        print(f"Seed completado: {Ejercicio.query.count()} ejercicios cargados.")


if __name__ == '__main__':
    seed()
