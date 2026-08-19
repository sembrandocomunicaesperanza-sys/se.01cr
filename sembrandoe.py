from flask import Flask,render_template,redirect,url_for,request,session
import json
import os
import uuid
import werkzeug.utils

app=Flask(__name__)
app.secret_key="sembrando_esperanza_253"

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DB_FOLDER=os.path.join(BASE_DIR,"base_de_datos")
UPLOAD_FOLDER=os.path.join(BASE_DIR,"static","uploads")
REPORTES_FILE=os.path.join(DB_FOLDER,"reportes.json")

os.makedirs(DB_FOLDER,exist_ok=True)
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER

NOMBRES_USUARIOS=[
"Sembrando Esperanza",
"Isaac Cascante",
"Jayden Marchena",
"Samantha Mendez",
"Ismael Navarrete",
"Pruebas"
]

CONTRASENAS_RESPALDO={
"Samantha Mendez":"sam094",
"Jayden Marchena":"Marchena1007",
"Isaac Cascante":"colochos0304",
"Ismael Navarrete":"ig2230",
"Sembrando Esperanza":"adminCR",
"Pruebas":"suli.,"
}

def ruta_usuario(identificador):
    return os.path.join(DB_FOLDER,f"{identificador}.json")

def es_direccion(identificador):
    return str(identificador).strip().lower()=="sembrando esperanza"

def es_coordinador(identificador):
    return str(identificador).strip().lower()=="isaac cascante"

def obtener_rol(identificador,puesto=""):
    if es_direccion(identificador):
        return "Dirección General"
    if es_coordinador(identificador):
        return "Coordinador"
    return puesto if puesto else "Usuario"

def crear_usuario_base(identificador):
    if es_direccion(identificador):
        puesto="Dirección General"
    elif es_coordinador(identificador):
        puesto="Coordinador del Proyecto"
    else:
        puesto="Área General"
    return {
        "nombre":identificador,
        "contrasena":CONTRASENAS_RESPALDO.get(identificador,""),
        "perfil":{
            "correo":"No registrado",
            "puesto":puesto
        },
        "tareas":{
            "disponibles":[],
            "en_revision":[],
            "completadas":[]
        },
        "reuniones":[]
    }

def guardar_usuario(identificador,datos):
    with open(ruta_usuario(identificador),"w",encoding="utf-8") as f:
        json.dump(datos,f,indent=4,ensure_ascii=False)

def leer_usuario(identificador):
    archivo=ruta_usuario(identificador)
    if not os.path.exists(archivo):
        return None
    try:
        with open(archivo,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def resolver_identificador(nombre):
    nombre=str(nombre).strip()
    if nombre in NOMBRES_USUARIOS:
        return nombre
    for identificador in NOMBRES_USUARIOS:
        datos=leer_usuario(identificador)
        if datos:
            nombre_json=str(datos.get("nombre","")).strip()
            if nombre_json.lower()==nombre.lower():
                return identificador
    return ""

def id_reunion(reunion):
    texto="|".join([
        str(reunion.get("creador_id",reunion.get("creador",""))),
        str(reunion.get("titulo","")),
        str(reunion.get("fecha","")),
        str(reunion.get("hora","")),
        str(reunion.get("tipo","todos"))
    ])
    return str(uuid.uuid5(uuid.NAMESPACE_URL,texto))

def normalizar_reuniones(datos):
    nuevas=[]
    for reunion in datos.get("reuniones",[]):
        if not isinstance(reunion,dict):
            continue
        creador_guardado=reunion.get("creador_id") or reunion.get("creador","")
        creador_id=resolver_identificador(creador_guardado)
        reunion["creador_id"]=creador_id
        reunion.setdefault("creador_nombre",reunion.get("creador",""))
        if creador_id:
            datos_creador=leer_usuario(creador_id)
            if datos_creador:
                reunion["creador_nombre"]=datos_creador.get("nombre",creador_id)
        reunion.setdefault("titulo","Reunión")
        reunion.setdefault("fecha","")
        reunion.setdefault("hora","")
        reunion.setdefault("url_reunion","")
        reunion.setdefault("descripcion","")
        reunion.setdefault("tipo","todos")
        reunion.setdefault("estado","programada")
        if not reunion.get("id"):
            reunion["id"]=id_reunion(reunion)
        nuevas.append(reunion)
    datos["reuniones"]=nuevas
    return datos

def cargar_usuario(identificador):
    archivo=ruta_usuario(identificador)
    if not os.path.exists(archivo):
        datos=crear_usuario_base(identificador)
        guardar_usuario(identificador,datos)
        return datos
    try:
        with open(archivo,"r",encoding="utf-8") as f:
            datos=json.load(f)
    except:
        datos=crear_usuario_base(identificador)
    datos.setdefault("nombre",identificador)
    datos.setdefault("contrasena",CONTRASENAS_RESPALDO.get(identificador,""))
    datos.setdefault("perfil",{})
    datos["perfil"].setdefault("correo","No registrado")
    if es_direccion(identificador):
        datos["perfil"]["puesto"]="Dirección General"
    elif es_coordinador(identificador):
        datos["perfil"]["puesto"]="Coordinador del Proyecto"
    else:
        datos["perfil"].setdefault("puesto","Área General")
    datos.setdefault("tareas",{})
    datos["tareas"].setdefault("disponibles",[])
    datos["tareas"].setdefault("en_revision",[])
    datos["tareas"].setdefault("completadas",[])
    datos.setdefault("reuniones",[])
    datos=normalizar_reuniones(datos)
    guardar_usuario(identificador,datos)
    return datos

def convertir_tarea(tarea,asignado,estado):
    if isinstance(tarea,dict):
        tarea.setdefault("id",str(uuid.uuid4()))
        tarea.setdefault("nombre","Tarea")
        if "fecha_nacimiento" in tarea and "fecha_entrega" not in tarea:
            tarea["fecha_entrega"]=tarea.get("fecha_nacimiento","")
        tarea.setdefault("fecha_entrega","")
        tarea.setdefault("descripcion","")
        tarea.setdefault("asignado",asignado)
        tarea.setdefault("estado",estado)
        tarea.setdefault("archivos",[])
        tarea.setdefault("archivos_revision",[])
        tarea.setdefault("comentario_revision","")
        tarea.setdefault("correccion","")
        return tarea
    texto=str(tarea)
    return {
        "id":str(uuid.uuid4()),
        "nombre":texto,
        "fecha_entrega":"",
        "descripcion":texto,
        "asignado":asignado,
        "estado":estado,
        "archivos":[],
        "archivos_revision":[],
        "comentario_revision":"",
        "correccion":""
    }

def normalizar_tareas(datos,identificador):
    disponibles=[]
    for tarea in datos["tareas"].get("disponibles",[]):
        estado=tarea.get("estado","pendiente") if isinstance(tarea,dict) else "pendiente"
        disponibles.append(convertir_tarea(tarea,identificador,estado))
    revision=[]
    for tarea in datos["tareas"].get("en_revision",[]):
        revision.append(convertir_tarea(tarea,identificador,"revision"))
    completadas=[]
    for tarea in datos["tareas"].get("completadas",[]):
        completadas.append(convertir_tarea(tarea,identificador,"completada"))
    datos["tareas"]["disponibles"]=disponibles
    datos["tareas"]["en_revision"]=revision
    datos["tareas"]["completadas"]=completadas
    return datos

def buscar_tarea(datos,tarea_id):
    for grupo in ["disponibles","en_revision","completadas"]:
        for tarea in datos["tareas"].get(grupo,[]):
            if str(tarea.get("id",""))==str(tarea_id):
                return tarea,grupo
    return None,None

def guardar_archivos(campo):
    guardados=[]
    if campo not in request.files:
        return guardados
    for archivo in request.files.getlist(campo):
        if not archivo or archivo.filename=="":
            continue
        nombre_seguro=werkzeug.utils.secure_filename(archivo.filename)
        if not nombre_seguro:
            continue
        nombre_final=f"{uuid.uuid4().hex}_{nombre_seguro}"
        archivo.save(os.path.join(app.config["UPLOAD_FOLDER"],nombre_final))
        guardados.append(nombre_final)
    return guardados

def cargar_reportes():
    if not os.path.exists(REPORTES_FILE):
        return []
    try:
        with open(REPORTES_FILE,"r",encoding="utf-8") as f:
            reportes=json.load(f)
    except:
        return []
    if not isinstance(reportes,list):
        return []
    cambio=False
    for reporte in reportes:
        if not isinstance(reporte,dict):
            continue
        if not reporte.get("id"):
            reporte["id"]=str(uuid.uuid4())
            cambio=True
        reporte.setdefault("destino","Sembrando Esperanza")
        reporte.setdefault("tipo","actividad")
        reporte.setdefault("usuario_id","")
        reporte.setdefault("usuario","")
        reporte.setdefault("titulo","Reporte")
        reporte.setdefault("fecha","")
        reporte.setdefault("hora","")
        reporte.setdefault("lugar","")
        reporte.setdefault("descripcion","")
        reporte.setdefault("resultados","")
        reporte.setdefault("beneficiados","")
        reporte.setdefault("participantes","")
        reporte.setdefault("acuerdos","")
        reporte.setdefault("documentos",[])
    if cambio:
        guardar_reportes(reportes)
    return reportes

def guardar_reportes(reportes):
    with open(REPORTES_FILE,"w",encoding="utf-8") as f:
        json.dump(reportes,f,indent=4,ensure_ascii=False)

def obtener_reuniones_visibles(identificador):
    reuniones=[]
    ids_vistos=set()
    for usuario_id in NOMBRES_USUARIOS:
        datos=cargar_usuario(usuario_id)
        for reunion in datos.get("reuniones",[]):
            reunion_id=str(reunion.get("id",""))
            if reunion_id in ids_vistos:
                continue
            tipo=reunion.get("tipo","todos")
            creador_id=reunion.get("creador_id","")
            visible=False
            if tipo=="todos":
                visible=True
            elif tipo=="coordinador":
                if identificador==creador_id:
                    visible=True
                if es_coordinador(identificador):
                    visible=True
                if es_direccion(identificador):
                    visible=True
            if visible:
                ids_vistos.add(reunion_id)
                reuniones.append(reunion)
    reuniones.sort(key=lambda r:(r.get("fecha",""),r.get("hora","")))
    return reuniones

def obtener_calendario(identificador):
    eventos=[]
    if es_direccion(identificador):
        for usuario_id in NOMBRES_USUARIOS:
            if es_direccion(usuario_id):
                continue
            datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
            for grupo in ["disponibles","en_revision","completadas"]:
                for tarea in datos["tareas"].get(grupo,[]):
                    fecha=tarea.get("fecha_entrega","")
                    if fecha:
                        eventos.append({
                            "id":tarea.get("id",""),
                            "tipo":"tarea",
                            "titulo":tarea.get("nombre","Tarea"),
                            "fecha":fecha,
                            "estado":tarea.get("estado","pendiente"),
                            "asignado":usuario_id
                        })
    else:
        datos=normalizar_tareas(cargar_usuario(identificador),identificador)
        for grupo in ["disponibles","en_revision","completadas"]:
            for tarea in datos["tareas"].get(grupo,[]):
                fecha=tarea.get("fecha_entrega","")
                if fecha:
                    eventos.append({
                        "id":tarea.get("id",""),
                        "tipo":"tarea",
                        "titulo":tarea.get("nombre","Tarea"),
                        "fecha":fecha,
                        "estado":tarea.get("estado","pendiente"),
                        "asignado":identificador
                    })
    for reunion in obtener_reuniones_visibles(identificador):
        fecha=reunion.get("fecha","")
        if fecha:
            eventos.append({
                "id":reunion.get("id",""),
                "tipo":"reunion",
                "titulo":reunion.get("titulo","Reunión"),
                "fecha":fecha,
                "hora":reunion.get("hora",""),
                "url_reunion":reunion.get("url_reunion",""),
                "estado":reunion.get("estado","programada"),
                "creador":reunion.get("creador_nombre","")
            })
    return eventos

@app.route("/")
def inicio():
    return redirect(url_for("bienvenida"))

@app.route("/bienvenida")
def bienvenida():
    return render_template("bienvenida.html")

@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html",usuarios=NOMBRES_USUARIOS)

@app.route("/password/<nombre>")
def pantalla_password(nombre):
    session.pop("usuario_id",None)
    if nombre not in NOMBRES_USUARIOS:
        return redirect(url_for("usuarios"))
    return render_template("password.html",usuario_actual=nombre)

@app.route("/verificar-password",methods=["POST"])
def verificar_password():
    identificador=request.form.get("usuario_actual","").strip()
    contrasena=request.form.get("password","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("usuarios"))
    datos=cargar_usuario(identificador)
    contrasena_correcta=datos.get(
        "contrasena",
        CONTRASENAS_RESPALDO.get(identificador,"")
    )
    if contrasena==contrasena_correcta:
        session.clear()
        session["usuario_id"]=identificador
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    return render_template(
        "password.html",
        usuario_actual=identificador,
        error="Contraseña incorrecta"
    )

@app.route("/cerrar-sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("bienvenida"))

@app.route("/inicio-sistema")
@app.route("/inicio-sistema/<nombre_usuario>")
@app.route("/inicio-sistema/<nombre_usuario>/<pestana>")
def inicio_sistema(nombre_usuario="Sembrando Esperanza",pestana="tareas"):
    identificador=session.get("usuario_id")
    if identificador not in NOMBRES_USUARIOS:
        if nombre_usuario in NOMBRES_USUARIOS:
            identificador=nombre_usuario
            session["usuario_id"]=identificador
        else:
            return redirect(url_for("usuarios"))
    direccion_general=es_direccion(identificador)
    datos_usuario=normalizar_tareas(cargar_usuario(identificador),identificador)
    guardar_usuario(identificador,datos_usuario)
    tareas=[]
    if direccion_general:
        for usuario_id in NOMBRES_USUARIOS:
            if es_direccion(usuario_id):
                continue
            datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
            tareas.extend(datos["tareas"]["disponibles"])
            tareas.extend(datos["tareas"]["en_revision"])
            tareas.extend(datos["tareas"]["completadas"])
            guardar_usuario(usuario_id,datos)
    else:
        tareas.extend(datos_usuario["tareas"]["disponibles"])
        tareas.extend(datos_usuario["tareas"]["en_revision"])
        tareas.extend(datos_usuario["tareas"]["completadas"])
    lista_usuarios=[]
    for usuario_id in NOMBRES_USUARIOS:
        datos_integrante=cargar_usuario(usuario_id)
        puesto=datos_integrante.get("perfil",{}).get("puesto","Área General")
        lista_usuarios.append({
            "identificador":usuario_id,
            "nombre":datos_integrante.get("nombre",usuario_id),
            "puesto":puesto,
            "correo":datos_integrante.get("perfil",{}).get("correo","No registrado"),
            "rol":obtener_rol(usuario_id,puesto)
        })
    puesto_usuario=datos_usuario.get("perfil",{}).get("puesto","No registrado")
    usuario_dashboard={
        "identificador":identificador,
        "nombre":datos_usuario.get("nombre",identificador),
        "correo":datos_usuario.get("perfil",{}).get("correo","No registrado"),
        "puesto":"Dirección General" if direccion_general else puesto_usuario,
        "rol":obtener_rol(identificador,puesto_usuario)
    }
    reportes=[]
    if direccion_general:
        reportes=[
            reporte
            for reporte in cargar_reportes()
            if reporte.get("destino","Sembrando Esperanza")=="Sembrando Esperanza"
        ]
    reuniones=obtener_reuniones_visibles(identificador)
    calendario=obtener_calendario(identificador)
    return render_template(
        "dashboard.html",
        pestana_activa=pestana,
        usuario=usuario_dashboard,
        usuarios=lista_usuarios,
        tareas=tareas,
        reuniones=reuniones,
        reportes=reportes,
        calendario=calendario,
        es_direccion_general=direccion_general
    )

@app.route("/crear-tarea",methods=["POST"])
def crear_tarea():
    identificador=session.get("usuario_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    if not es_direccion(identificador):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    encargado=request.form.get("asignado","").strip()
    nombre_tarea=request.form.get("nombre","").strip()
    fecha_entrega=request.form.get("fecha_entrega","").strip()
    descripcion=request.form.get("descripcion","").strip()
    if encargado not in NOMBRES_USUARIOS:
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    if es_direccion(encargado):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    datos_encargado=normalizar_tareas(cargar_usuario(encargado),encargado)
    nueva_tarea={
        "id":str(uuid.uuid4()),
        "nombre":nombre_tarea,
        "fecha_entrega":fecha_entrega,
        "descripcion":descripcion,
        "asignado":encargado,
        "estado":"pendiente",
        "archivos":guardar_archivos("archivos"),
        "archivos_revision":[],
        "comentario_revision":"",
        "correccion":""
    }
    datos_encargado["tareas"]["disponibles"].append(nueva_tarea)
    guardar_usuario(encargado,datos_encargado)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="tareas"
        )
    )

@app.route("/editar-tarea",methods=["POST"])
def editar_tarea():
    identificador=session.get("usuario_id","")
    if not es_direccion(identificador):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    tarea_id=request.form.get("tarea_id","")
    for usuario_id in NOMBRES_USUARIOS:
        datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
        tarea,grupo=buscar_tarea(datos,tarea_id)
        if not tarea:
            continue
        nuevo_asignado=request.form.get("asignado",usuario_id)
        tarea["nombre"]=request.form.get("nombre",tarea.get("nombre",""))
        tarea["fecha_entrega"]=request.form.get("fecha_entrega",tarea.get("fecha_entrega",""))
        tarea["descripcion"]=request.form.get("descripcion",tarea.get("descripcion",""))
        tarea.setdefault("archivos",[])
        tarea["archivos"].extend(guardar_archivos("archivos"))
        if (
            nuevo_asignado in NOMBRES_USUARIOS
            and nuevo_asignado!=usuario_id
            and not es_direccion(nuevo_asignado)
        ):
            datos["tareas"][grupo].remove(tarea)
            guardar_usuario(usuario_id,datos)
            datos_nuevo=normalizar_tareas(cargar_usuario(nuevo_asignado),nuevo_asignado)
            tarea["asignado"]=nuevo_asignado
            datos_nuevo["tareas"][grupo].append(tarea)
            guardar_usuario(nuevo_asignado,datos_nuevo)
        else:
            tarea["asignado"]=usuario_id
            guardar_usuario(usuario_id,datos)
        break
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="tareas"
        )
    )

@app.route("/eliminar-tarea",methods=["POST"])
def eliminar_tarea():
    identificador=session.get("usuario_id","")
    if not es_direccion(identificador):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    tarea_id=request.form.get("tarea_id","")
    for usuario_id in NOMBRES_USUARIOS:
        datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
        tarea,grupo=buscar_tarea(datos,tarea_id)
        if tarea:
            datos["tareas"][grupo].remove(tarea)
            guardar_usuario(usuario_id,datos)
            break
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="tareas"
        )
    )

@app.route("/completar-tarea",methods=["POST"])
def completar_tarea():
    identificador=session.get("usuario_id","")
    if not es_direccion(identificador):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="tareas"
            )
        )
    tarea_id=request.form.get("tarea_id","")
    for usuario_id in NOMBRES_USUARIOS:
        datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
        tarea,grupo=buscar_tarea(datos,tarea_id)
        if tarea:
            datos["tareas"][grupo].remove(tarea)
            tarea["estado"]="completada"
            tarea["correccion"]=""
            datos["tareas"]["completadas"].append(tarea)
            guardar_usuario(usuario_id,datos)
            break
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="tareas"
        )
    )

@app.route("/procesar-revision",methods=["POST"])
def procesar_revision():
    identificador=session.get("usuario_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    accion=request.form.get("accion")
    tarea_id=request.form.get("tarea_id")
    for usuario_id in NOMBRES_USUARIOS:
        datos=normalizar_tareas(cargar_usuario(usuario_id),usuario_id)
        tarea,grupo=buscar_tarea(datos,tarea_id)
        if not tarea:
            continue
        if accion=="enviar_revision":
            if usuario_id!=identificador:
                continue
            if grupo!="en_revision":
                datos["tareas"][grupo].remove(tarea)
            tarea["estado"]="revision"
            tarea["comentario_revision"]=request.form.get("comentario_revision","")
            tarea.setdefault("archivos_revision",[])
            tarea["archivos_revision"].extend(guardar_archivos("archivos_revision"))
            if tarea not in datos["tareas"]["en_revision"]:
                datos["tareas"]["en_revision"].append(tarea)
            guardar_usuario(usuario_id,datos)
            return redirect(
                url_for(
                    "inicio_sistema",
                    nombre_usuario=identificador,
                    pestana="tareas"
                )
            )
        if accion=="corregir_tarea" and es_direccion(identificador):
            if grupo!="disponibles":
                datos["tareas"][grupo].remove(tarea)
            tarea["estado"]="correccion"
            tarea["correccion"]=request.form.get("correccion","")
            if tarea not in datos["tareas"]["disponibles"]:
                datos["tareas"]["disponibles"].append(tarea)
            guardar_usuario(usuario_id,datos)
            return redirect(
                url_for(
                    "inicio_sistema",
                    nombre_usuario=identificador,
                    pestana="tareas"
                )
            )
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="tareas"
        )
    )

@app.route("/crear-reunion",methods=["POST"])
def crear_reunion():
    identificador=session.get("usuario_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    datos_creador=cargar_usuario(identificador)
    tipo=request.form.get("tipo_reunion","todos")
    reunion={
        "id":str(uuid.uuid4()),
        "creador_id":identificador,
        "creador_nombre":datos_creador.get("nombre",identificador),
        "titulo":request.form.get("titulo","").strip(),
        "fecha":request.form.get("fecha","").strip(),
        "hora":request.form.get("hora","").strip(),
        "url_reunion":request.form.get("url_reunion","").strip(),
        "descripcion":request.form.get("descripcion","").strip(),
        "tipo":tipo,
        "estado":"programada"
    }
    if tipo=="coordinador":
        destinatarios=[identificador,"Isaac Cascante"]
    else:
        destinatarios=NOMBRES_USUARIOS.copy()
    for usuario_id in list(dict.fromkeys(destinatarios)):
        if usuario_id not in NOMBRES_USUARIOS:
            continue
        datos=cargar_usuario(usuario_id)
        existe=any(
            str(r.get("id",""))==reunion["id"]
            for r in datos.get("reuniones",[])
        )
        if not existe:
            datos["reuniones"].append(reunion.copy())
            guardar_usuario(usuario_id,datos)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="reuniones"
        )
    )

@app.route("/finalizar-reunion",methods=["POST"])
def finalizar_reunion():
    identificador=session.get("usuario_id","")
    reunion_id=request.form.get("reunion_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    reuniones=obtener_reuniones_visibles(identificador)
    objetivo=next(
        (
            r
            for r in reuniones
            if str(r.get("id",""))==str(reunion_id)
        ),
        None
    )
    if not objetivo:
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="reuniones"
            )
        )
    if (
        objetivo.get("creador_id")!=identificador
        and not es_direccion(identificador)
    ):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="reuniones"
            )
        )
    for usuario_id in NOMBRES_USUARIOS:
        datos=cargar_usuario(usuario_id)
        cambio=False
        for reunion in datos.get("reuniones",[]):
            if str(reunion.get("id",""))==str(reunion_id):
                reunion["estado"]="finalizada"
                cambio=True
        if cambio:
            guardar_usuario(usuario_id,datos)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="reuniones"
        )
    )

@app.route("/eliminar-reunion",methods=["POST"])
def eliminar_reunion():
    identificador=session.get("usuario_id","")
    reunion_id=request.form.get("reunion_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    reuniones=obtener_reuniones_visibles(identificador)
    objetivo=next(
        (
            r
            for r in reuniones
            if str(r.get("id",""))==str(reunion_id)
        ),
        None
    )
    if not objetivo:
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="reuniones"
            )
        )
    if (
        objetivo.get("creador_id")!=identificador
        and not es_direccion(identificador)
    ):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="reuniones"
            )
        )
    for usuario_id in NOMBRES_USUARIOS:
        datos=cargar_usuario(usuario_id)
        datos["reuniones"]=[
            reunion
            for reunion in datos.get("reuniones",[])
            if str(reunion.get("id",""))!=str(reunion_id)
        ]
        guardar_usuario(usuario_id,datos)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="reuniones"
        )
    )

@app.route("/enviar-reporte",methods=["POST"])
def enviar_reporte():
    identificador=session.get("usuario_id","")
    if identificador not in NOMBRES_USUARIOS:
        return redirect(url_for("bienvenida"))
    datos_usuario=cargar_usuario(identificador)
    reporte={
        "id":str(uuid.uuid4()),
        "tipo":request.form.get("tipo_reporte","actividad"),
        "usuario_id":identificador,
        "usuario":datos_usuario.get("nombre",identificador),
        "destino":"Sembrando Esperanza",
        "titulo":request.form.get("titulo",""),
        "fecha":request.form.get("fecha",""),
        "hora":request.form.get("hora",""),
        "lugar":request.form.get("lugar",""),
        "descripcion":request.form.get("descripcion",""),
        "resultados":request.form.get("resultados",""),
        "beneficiados":request.form.get("beneficiados",""),
        "participantes":request.form.get("participantes",""),
        "acuerdos":request.form.get("acuerdos",""),
        "documentos":guardar_archivos("documentos")
    }
    reportes=cargar_reportes()
    reportes.append(reporte)
    guardar_reportes(reportes)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="reportes"
        )
    )

@app.route("/eliminar-reporte",methods=["POST"])
def eliminar_reporte():
    identificador=session.get("usuario_id","")
    if not es_direccion(identificador):
        return redirect(
            url_for(
                "inicio_sistema",
                nombre_usuario=identificador,
                pestana="reportes"
            )
        )
    reporte_id=request.form.get("reporte_id","")
    reportes=[
        reporte
        for reporte in cargar_reportes()
        if str(reporte.get("id",""))!=str(reporte_id)
    ]
    guardar_reportes(reportes)
    return redirect(
        url_for(
            "inicio_sistema",
            nombre_usuario=identificador,
            pestana="reportes"
        )
    )

@app.context_processor
def utilidades_de_fondos():
    def obtener_fondo_actual(pestana):
        """
        Detecta si el usuario entra desde celular o PC 
        y devuelve el enlace correcto de la carpeta static.
        """
        # Detecta si el agente de usuario (navegador) es un dispositivo móvil
        user_agent = request.headers.get('User-Agent', '').lower()
        es_celular = any(dispositivo in user_agent for dispositivo in ['mobile', 'android', 'iphone', 'ipad'])
        
        # Diccionario centralizado de control de fondos
        configuracion_fondos = {
            "bienvenida": "fondo_cel.png" if es_celular else "fondo_pc.png",
            "dashboard": "fondo_dashboard-cel.png" if es_celular else "fondo_dashboard-pc.png",
            "password": "fondo_login-cel.png" if es_celular else "fondo_login-pc.png",
            "usuarios": "fondo_login-cel.png" if es_celular else "fondo_login-pc.png"
        }
        
        # Obtiene el nombre del archivo asignado a la pestaña
        archivo_imagen = configuracion_fondos.get(pestana, "fondo_pc.png")
        
        # Retorna la URL oficial de Flask hacia la carpeta static
        return url_for('static', filename=archivo_imagen)

    # Registra la función de forma global para usarla en cualquier HTML
    return dict(obtener_fondo=obtener_fondo_actual)
if __name__=="__main__":
    app.run(debug=True)