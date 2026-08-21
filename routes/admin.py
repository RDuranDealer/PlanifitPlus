import os,re
from flask import Blueprint,jsonify,request,render_template,abort
from models import db,Usuario,Ejercicio,Config
bp=Blueprint('admin',__name__)
ADMIN_TOKEN=os.environ.get('ADMIN_TOKEN','rpg-admin-2024')

def check(token):
    if token!=ADMIN_TOKEN: abort(403)
def check_header():
    t=request.args.get('token') or request.headers.get('X-Admin-Token')
    if t!=ADMIN_TOKEN: abort(403)

@bp.route('/admin/<token>')
def admin_index(token):
    check(token); return render_template('admin/index.html',token=token)
@bp.route('/admin/<token>/rutinas')
def admin_rutinas(token):
    check(token); return render_template('admin/rutinas.html',token=token)
@bp.route('/admin/<token>/usuarios')
def admin_usuarios(token):
    check(token); return render_template('admin/usuarios.html',token=token)

@bp.route('/api/admin/usuarios')
def api_usuarios():
    check_header()
    return jsonify([{**u.to_dict(),'ejercicios_count':Ejercicio.query.filter_by(usuario_id=u.id).count()} for u in Usuario.query.order_by(Usuario.created_at).all()])

@bp.route('/api/admin/usuarios/<int:uid>/rutina-base',methods=['POST'])
def cargar_rutina_base(uid):
    check_header()
    Usuario.query.get_or_404(uid)
    Ejercicio.query.filter_by(usuario_id=uid).delete(); db.session.flush()
    from seed import cargar_ejercicios_usuario
    cargar_ejercicios_usuario(uid); db.session.commit()
    return jsonify({'ok':True,'ejercicios':Ejercicio.query.filter_by(usuario_id=uid).count()})

@bp.route('/api/admin/usuarios/<int:uid>/rutina-md',methods=['POST'])
def cargar_rutina_md(uid):
    check_header()
    Usuario.query.get_or_404(uid)
    if request.is_json: contenido=request.get_json().get('contenido','')
    else:
        f=request.files.get('archivo')
        if not f: return jsonify({'error':'Se requiere contenido o archivo'}),400
        contenido=f.read().decode('utf-8')
    if not contenido.strip(): return jsonify({'error':'Contenido vacío'}),400
    try: parsed=parsear_md(contenido)
    except Exception as e: return jsonify({'error':str(e)}),400
    if not parsed: return jsonify({'error':'No se encontraron ejercicios'}),400
    if request.args.get('preview')=='1': return jsonify({'ejercicios':parsed,'total':len(parsed)})
    Ejercicio.query.filter_by(usuario_id=uid).delete(); db.session.flush()
    for orden,ex in enumerate(parsed):
        db.session.add(Ejercicio(
            usuario_id=uid, dia_id=ex['dia_id'], seccion=ex['seccion'],
            nombre=ex['nombre'], detalle_base=ex.get('base',''),
            detalle_medio=ex.get('medio',''), detalle_alto=ex.get('alto',''),
            detalle_avanzado=ex.get('avanzado',''), tag=ex.get('tag','keep'),
            nota=ex.get('nota',''), video_url=ex.get('video',''),
            pasos=ex.get('pasos',''), orden=orden, activo=True
        ))
    db.session.commit()
    return jsonify({'ok':True,'ejercicios_cargados':len(parsed)})

def parsear_md(contenido):
    DIAS={'lunes':0,'martes':1,'miércoles':2,'miercoles':2,'jueves':3,'viernes':4,'sábado':5,'sabado':5,'domingo':6}
    ejercicios=[]; dia=None; sec=None; ex=None; en_pasos=False; pasos_buf=[]

    for linea in contenido.splitlines():
        linea_strip=linea.strip()
        if not linea_strip:
            if en_pasos: pasos_buf.append('')
            continue

        if linea_strip.startswith('# '):
            if ex:
                if pasos_buf: ex['pasos']='\n'.join(pasos_buf).strip()
                ejercicios.append(ex); ex=None; pasos_buf=[]; en_pasos=False
            txt=linea_strip[2:].lower()
            for k,v in DIAS.items():
                if k in txt: dia=v; break

        elif linea_strip.startswith('## '):
            sec=re.sub(r'^[Ss]ecci[oó]n:\s*','',linea_strip[3:]).strip(); en_pasos=False

        elif linea_strip.startswith('### '):
            if ex:
                if pasos_buf: ex['pasos']='\n'.join(pasos_buf).strip()
                ejercicios.append(ex)
            pasos_buf=[]; en_pasos=False
            ex={'nombre':linea_strip[4:].strip(),'dia_id':dia,'seccion':sec or 'General','tag':'keep','nota':'','video':'','pasos':''}

        elif linea_strip.startswith('- ') and ex is not None and not en_pasos:
            partes=linea_strip[2:].split(':',1)
            if len(partes)==2:
                k,v=partes[0].strip().lower(),partes[1].strip()
                if k in ('base','medio','alto','avanzado','tag','nota','video'): ex[k]=v
                elif k=='pasos': en_pasos=True  # todo lo que sigue hasta ### es pasos

        elif en_pasos and ex is not None:
            # Líneas de pasos: pueden ser numeradas o con guión
            pasos_buf.append(linea_strip)

    if ex:
        if pasos_buf: ex['pasos']='\n'.join(pasos_buf).strip()
        ejercicios.append(ex)
    return ejercicios

@bp.route('/api/admin/md-template')
def md_template():
    check_header()
    t="""# Rutina: Lunes — Cadena posterior
## Sección: Postura RPG + core

### Postura RPG en pared
- base: 1×3 min
- medio: 1×4 min
- alto: 2×3 min
- avanzado: 2×4 min
- tag: keep
- nota: Sin flexión lumbar forzada. Espalda neutra.
- video: https://www.youtube.com/watch?v=EJEMPLO
- pasos:
1. Párate de espaldas a la pared a 5 cm de distancia.
2. Apoya talones, glúteos, escápulas y nuca simultáneamente.
3. Mantén el mentón paralelo al suelo, sin empujar con la cabeza.
4. Activa el abdomen suavemente. Respira por la nariz.
5. Sostén la postura durante el tiempo indicado sin perder el contacto.

### Puente de glúteos
- base: 3×15
- medio: 4×15
- alto: 4×15 + 2 seg pausa
- avanzado: 4×20 + 2 seg pausa
- tag: keep
- nota: Contracción máxima en la cima.
- video: https://www.youtube.com/watch?v=EJEMPLO2
- pasos:
1. Acuéstate boca arriba, rodillas flexionadas a 90°, pies apoyados.
2. Activa el abdomen y presiona la zona lumbar contra el suelo.
3. Empuja con los talones y eleva las caderas hasta alinearlas con el tronco.
4. Aprieta los glúteos en la cima durante la pausa indicada.
5. Baja lentamente vértebra por vértebra.
"""
    return jsonify({'template':t})
