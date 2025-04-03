from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'j350z271123r'

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# Configuración SMTP para Reporte de Errores
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'

# -----------------------------------------------------------
# Funciones para resolver triángulos
# -----------------------------------------------------------
def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, 
                             lado_a=None, lado_b=None, lado_c=None):
    known_angles = [angulo_A, angulo_B, angulo_C]
    num_angles = sum(1 for x in known_angles if x is not None)
    known_sides = [lado_a, lado_b, lado_c]
    num_sides = sum(1 for x in known_sides if x is not None)
    if num_angles + num_sides < 3 or num_sides < 1:
        raise ValueError("Información insuficiente para resolver el triángulo.")
    if num_angles >= 2:
        if angulo_A is None:
            angulo_A = 180 - (angulo_B + angulo_C)
        elif angulo_B is None:
            angulo_B = 180 - (angulo_A + angulo_C)
        elif angulo_C is None:
            angulo_C = 180 - (angulo_A + angulo_B)
    if angulo_A is not None and angulo_B is not None and angulo_C is not None:
        if abs(angulo_A + angulo_B + angulo_C - 180) > 1e-5:
            raise ValueError("Los ángulos no suman 180°.")
        if angulo_A <= 0 or angulo_B <= 0 or angulo_C <= 0:
            raise ValueError("Los ángulos deben ser mayores que 0.")
    if num_angles >= 2 and num_sides >= 1:
        if lado_a is not None:
            ratio = lado_a / math.sin(math.radians(angulo_A))
            if lado_b is None:
                lado_b = ratio * math.sin(math.radians(angulo_B))
            if lado_c is None:
                lado_c = ratio * math.sin(math.radians(angulo_C))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        elif lado_b is not None:
            ratio = lado_b / math.sin(math.radians(angulo_B))
            if lado_a is None:
                lado_a = ratio * math.sin(math.radians(angulo_A))
            if lado_c is None:
                lado_c = ratio * math.sin(math.radians(angulo_C))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        elif lado_c is not None:
            ratio = lado_c / math.sin(math.radians(angulo_C))
            if lado_a is None:
                lado_a = ratio * math.sin(math.radians(angulo_A))
            if lado_b is None:
                lado_b = ratio * math.sin(math.radians(angulo_B))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
    if num_angles == 1 and num_sides == 2:
        if angulo_A is not None and lado_a is not None:
            if lado_b is not None:
                sinB = (lado_b * math.sin(math.radians(angulo_A))) / lado_a
                if sinB < -1 or sinB > 1:
                    raise ValueError("No hay solución, sin(β) fuera de rango.")
                angulo_B = math.degrees(math.asin(sinB))
                angulo_C = 180 - angulo_A - angulo_B
                lado_c = (lado_a * math.sin(math.radians(angulo_C))) / math.sin(math.radians(angulo_A))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
            elif lado_c is not None:
                sinC = (lado_c * math.sin(math.radians(angulo_A))) / lado_a
                if sinC < -1 or sinC > 1:
                    raise ValueError("No hay solución, sin(γ) fuera de rango.")
                angulo_C = math.degrees(math.asin(sinC))
                angulo_B = 180 - angulo_A - angulo_C
                lado_b = (lado_a * math.sin(math.radians(angulo_B))) / math.sin(math.radians(angulo_A))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
    raise ValueError("No se pudo determinar el triángulo con la información proporcionada.")

def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    if sum(x is not None for x in [A, B, C]) == 2:
        if A is None:
            A = 180 - B - C
        elif B is None:
            B = 180 - A - C
        elif C is None:
            C = 180 - A - B
    if all(x is not None for x in [a, b, c]):
        A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
        B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
        C = 180 - A - B
        return a, b, c, A, B, C
    if a is not None and b is not None and C is not None:
        c = math.sqrt(a**2 + b**2 - 2*a*b*math.cos(math.radians(C)))
        A = math.degrees(math.asin(a * math.sin(math.radians(C)) / c))
        B = 180 - C - A
        return a, b, c, A, B, C
    if a is not None and c is not None and B is not None:
        b = math.sqrt(a**2 + c**2 - 2*a*c*math.cos(math.radians(B)))
        A = math.degrees(math.asin(a * math.sin(math.radians(B)) / b))
        C = 180 - B - A
        return a, b, c, A, B, C
    if b is not None and c is not None and A is not None:
        a = math.sqrt(b**2 + c**2 - 2*b*c*math.cos(math.radians(A)))
        B = math.degrees(math.asin(b * math.sin(math.radians(A)) / a))
        C = 180 - A - B
        return a, b, c, A, B, C
    raise ValueError("No se pudo resolver el triángulo con la información dada.")

def resolver_triangulo(a, b, c, A, B, C, base=None, altura=None):
    # Si se proporcionan base y altura, asumimos triángulo rectángulo
    if base is not None and altura is not None:
        a_r = base
        b_r = altura
        c_r = math.sqrt(base**2 + altura**2)
        A_r = math.degrees(math.atan(altura/base))
        B_r = 90.0
        C_r = 180 - A_r - B_r
        return (a_r, b_r, c_r, A_r, B_r, C_r), "base/altura"
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    if count_sides + count_angles < 3 or count_sides < 1:
        raise ValueError("Se requieren al menos 3 datos (con al menos 1 lado) para resolver el triángulo.")
    if count_angles >= 2:
        metodo = "senos"
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, lado_a=a, lado_b=b, lado_c=c), metodo
    elif count_sides == 3:
        metodo = "cosenos"
        return calcular_triangulo_cos(a=a, b=b, c=c, A=A, B=B, C=C), metodo
    else:
        metodo = "senos"
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, lado_a=a, lado_b=b, lado_c=c), metodo

# -----------------------------------------------------------
# Funciones adicionales: medianas, circuncentro, ortocentro, tipo de triángulo, clasificación y conversión de unidades
# -----------------------------------------------------------
def calcular_medianas(a, b, c):
    m_a = 0.5 * math.sqrt(2*(b**2 + c**2) - a**2)
    m_b = 0.5 * math.sqrt(2*(a**2 + c**2) - b**2)
    m_c = 0.5 * math.sqrt(2*(a**2 + b**2) - c**2)
    return m_a, m_b, m_c

def calcular_circumradius(a, b, c, area):
    if area == 0:
        return None
    return (a * b * c) / (4 * area)

def determinar_tipo_triangulo(a, b, c):
    if abs(a - b) < 1e-5 and abs(b - c) < 1e-5:
        return "Equilátero"
    elif abs(a - b) < 1e-5 or abs(a - c) < 1e-5 or abs(b - c) < 1e-5:
        return "Isósceles"
    else:
        return "Escaleno"

def determinar_clasificacion_angulo(A, B, C):
    if abs(A - 90) < 1e-2 or abs(B - 90) < 1e-2 or abs(C - 90) < 1e-2:
        return "Rectángulo"
    elif A > 90 or B > 90 or C > 90:
        return "Obtuso"
    else:
        return "Acutángulo"

def convertir_unidades(valor, de_unidad, a_unidad):
    conversion = {
        ("mm", "cm"): 0.1,
        ("cm", "mm"): 10,
        ("cm", "m"): 0.01,
        ("m", "cm"): 100,
        ("mm", "m"): 0.001,
        ("m", "mm"): 1000
    }
    factor = conversion.get((de_unidad, a_unidad))
    if factor is None:
        raise ValueError("Conversión no soportada.")
    return valor * factor

def calcular_circuncentro(A, B, C):
    d = 2*(A[0]*(B[1]-C[1]) + B[0]*(C[1]-A[1]) + C[0]*(A[1]-B[1]))
    if abs(d) < 1e-9:
        return None
    Ux = ((A[0]**2+A[1]**2)*(B[1]-C[1]) + (B[0]**2+B[1]**2)*(C[1]-A[1]) + (C[0]**2+C[1]**2)*(A[1]-B[1]))/d
    Uy = ((A[0]**2+A[1]**2)*(C[0]-B[0]) + (B[0]**2+B[1]**2)*(A[0]-C[0]) + (C[0]**2+C[1]**2)*(B[0]-A[0]))/d
    return (Ux, Uy)

def calcular_ortocentro(A, B, C):
    U = calcular_circuncentro(A, B, C)
    if U is None:
        return None
    Hx = A[0] + B[0] + C[0] - 2*U[0]
    Hy = A[1] + B[1] + C[1] - 2*U[1]
    return (Hx, Hy)

# -----------------------------------------------------------
# Funciones de graficado
# -----------------------------------------------------------
def graficar_triangulo_estatico(a, b, c, A, B, C, metodo):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    
    plt.figure(figsize=(7,7))
    # Lados
    plt.plot([A_point[0], B_point[0]], [A_point[1], B_point[1]], 'b-', label=f"Lado c = {c:.2f}")
    plt.plot([A_point[0], C_point[0]], [A_point[1], C_point[1]], 'r-', label=f"Lado b = {b:.2f}")
    plt.plot([B_point[0], C_point[0]], [B_point[1], C_point[1]], 'g-', label=f"Lado a = {a:.2f}")
    # Medianas: desde A, B y C (etiquetadas mₐ, m_b, m_c)
    mid_BC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    mid_AC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    mid_AB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    plt.plot([A_point[0], mid_BC[0]], [A_point[1], mid_BC[1]], 'k--', label="mₐ")
    plt.plot([B_point[0], mid_AC[0]], [B_point[1], mid_AC[1]], 'k--', label="m_b")
    plt.plot([C_point[0], mid_AB[0]], [C_point[1], mid_AB[1]], 'k--', label="m_c")
    # Altura principal: desde C a AB (y=0)
    plt.plot([C_point[0], C_point[0]], [C_point[1], 0], 'm--', label="Altura")
    # Marcar circuncentro y ortocentro
    circ = calcular_circuncentro(A_point, B_point, C_point)
    orto = calcular_ortocentro(A_point, B_point, C_point)
    if circ:
        plt.plot(circ[0], circ[1], 'co', markersize=8, label="Circuncentro")
        plt.text(circ[0]+0.1, circ[1], "Circ.", color='cyan')
    if orto:
        plt.plot(orto[0], orto[1], 'mo', markersize=8, label="Ortocentro")
        plt.text(orto[0]+0.1, orto[1], "Orto.", color='magenta')
    # Etiquetar vértices
    plt.text(A_point[0]-0.2, A_point[1]-0.2, "A", fontsize=12)
    plt.text(B_point[0]+0.2, B_point[1]-0.2, "B", fontsize=12)
    plt.text(C_point[0], C_point[1]+0.2, "C", fontsize=12)
    
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Grafica del Triángulo")
    plt.legend()
    plt.grid(True)
    plt.axis("equal")
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    img_estatico = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close()
    return img_estatico, A_point, B_point, C_point

def graficar_triangulo_interactivo(a, b, c, A, B, C):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[A_point[0], B_point[0]], y=[A_point[1], B_point[1]],
                             mode='lines', name=f"Lado c = {c:.2f}", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=[A_point[0], C_point[0]], y=[A_point[1], C_point[1]],
                             mode='lines', name=f"Lado b = {b:.2f}", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=[B_point[0], C_point[0]], y=[B_point[1], C_point[1]],
                             mode='lines', name=f"Lado a = {a:.2f}", line=dict(color='green')))
    # Medianas
    mid_BC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    mid_AC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    mid_AB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    fig.add_trace(go.Scatter(x=[A_point[0], mid_BC[0]], y=[A_point[1], mid_BC[1]],
                             mode='lines', name="mₐ", line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=[B_point[0], mid_AC[0]], y=[B_point[1], mid_AC[1]],
                             mode='lines', name="m_b", line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=[C_point[0], mid_AB[0]], y=[C_point[1], mid_AB[1]],
                             mode='lines', name="m_c", line=dict(color='black', dash='dash')))
    # Altura principal desde C a la base
    fig.add_trace(go.Scatter(x=[C_point[0], C_point[0]], y=[C_point[1], 0],
                             mode='lines', name="Altura", line=dict(color='magenta', dash='dot')))
    # Circuncentro y ortocentro
    circ = calcular_circuncentro(A_point, B_point, C_point)
    orto = calcular_ortocentro(A_point, B_point, C_point)
    if circ:
        fig.add_trace(go.Scatter(x=[circ[0]], y=[circ[1]], mode='markers+text',
                                 marker=dict(color='cyan', size=10), text=["Circuncentro"],
                                 textposition="top right", name="Circuncentro"))
    if orto:
        fig.add_trace(go.Scatter(x=[orto[0]], y=[orto[1]], mode='markers+text',
                                 marker=dict(color='magenta', size=10), text=["Ortocentro"],
                                 textposition="top left", name="Ortocentro"))
    # Vértices
    fig.add_trace(go.Scatter(x=[A_point[0]], y=[A_point[1]], mode='markers+text',
                             text=["A"], textposition="top left", marker=dict(color='black', size=8)))
    fig.add_trace(go.Scatter(x=[B_point[0]], y=[B_point[1]], mode='markers+text',
                             text=["B"], textposition="top right", marker=dict(color='black', size=8)))
    fig.add_trace(go.Scatter(x=[C_point[0]], y=[C_point[1]], mode='markers+text',
                             text=["C"], textposition="bottom center", marker=dict(color='black', size=8)))
    fig.update_layout(title="Grafica Interactiva del Triángulo",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      legend_title="Leyenda",
                      template="plotly_white",
                      width=600, height=600,
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig.to_html(full_html=False)

# -----------------------------------------------------------
# Ruta para la Calculadora de Conversión de Unidades
# -----------------------------------------------------------
@app.route('/convertir', methods=['POST'])
def convertir():
    try:
        valor = float(request.form.get('valor'))
        de_unidad = request.form.get('de_unidad')
        a_unidad = request.form.get('a_unidad')
        resultado_conv = convertir_unidades(valor, de_unidad, a_unidad)
        flash(f"Conversión: {valor} {de_unidad} = {resultado_conv} {a_unidad}")
    except Exception as e:
        flash(str(e))
    return redirect(url_for('index'))

# -----------------------------------------------------------
# Rutas para Donar y Reportar Error
# -----------------------------------------------------------
@app.route('/donar')
def donar():
    return render_template("donar.html")

@app.route('/reporte', methods=['GET', 'POST'])
def reporte():
    if request.method == "POST":
        email = request.form.get("email")
        mensaje = request.form.get("mensaje")
        asunto = "Reporte de error - Instant Math Solver: Triángulos"
        cuerpo = f"Reporte de: {email}\n\nMensaje:\n{mensaje}"
        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            flash("Reporte enviado correctamente. ¡Gracias por tus comentarios!")
        except Exception as e:
            flash(f"Error al enviar el reporte: {e}")
        return redirect(url_for("reporte"))
    return render_template("reporte.html")

# -----------------------------------------------------------
# Ruta de login (endpoint definido para evitar BuildError)
# -----------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login_route():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'alumno' and password == 'amrd':
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos, intente de nuevo.')
            return render_template("login.html")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for('login'))

# -----------------------------------------------------------
# Ruta principal con indicador de carga
# -----------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        flash("Calculando, por favor espere...")
        try:
            def get_val(field):
                val = request.form.get(field)
                return float(val) if val and val.strip() != "" else None
            a_val = get_val("lado_a")
            b_val = get_val("lado_b")
            c_val = get_val("lado_c")
            A_val = get_val("angulo_A")
            B_val = get_val("angulo_B")
            C_val = get_val("angulo_C")
            base_val = get_val("base")
            altura_val = get_val("altura")
            
            (res_a, res_b, res_c, res_A, res_B, res_C), metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val, base=base_val, altura=altura_val)
            perimetro = res_a + res_b + res_c
            s = perimetro / 2
            area = math.sqrt(s * (s - res_a) * (s - res_b) * (s - res_c))
            
            mediana_a, mediana_b, mediana_c = calcular_medianas(res_a, res_b, res_c)
            circumradius = calcular_circumradius(res_a, res_b, res_c, area)
            tipo_triangulo = determinar_tipo_triangulo(res_a, res_b, res_c)
            clasificacion_angulo = determinar_clasificacion_angulo(res_A, res_B, res_C)
            # Altura vertical: se calcula desde C al eje horizontal
            altura_vertical = res_b * math.sin(math.radians(res_A))
            
            img_estatico, A_pt, B_pt, C_pt = graficar_triangulo_estatico(res_a, res_b, res_c, res_A, res_B, res_C, metodo)
            img_interactivo = graficar_triangulo_interactivo(res_a, res_b, res_c, res_A, res_B, res_C)
            circ = calcular_circuncentro(A_pt, B_pt, C_pt)
            orto = calcular_ortocentro(A_pt, B_pt, C_pt)
            
            resultados = {
                'lado_a': f"{res_a:.2f}",
                'lado_b': f"{res_b:.2f}",
                'lado_c': f"{res_c:.2f}",
                'angulo_A': f"{res_A:.2f}",
                'angulo_B': f"{res_B:.2f}",
                'angulo_C': f"{res_C:.2f}",
                'perimetro': f"{perimetro:.2f}",
                'area': f"{area:.2f}",
                'mediana_a': f"{mediana_a:.2f}",
                'mediana_b': f"{mediana_b:.2f}",
                'mediana_c': f"{mediana_c:.2f}",
                'circumradius': f"{circumradius:.2f}" if circumradius is not None else "N/A",
                'tipo_triangulo': tipo_triangulo,
                'clasificacion_angulo': clasificacion_angulo,
                'metodo': metodo,
                'circuncentro': f"({circ[0]:.2f}, {circ[1]:.2f})" if circ else "N/A",
                'ortocentro': f"({orto[0]:.2f}, {orto[1]:.2f})" if orto else "N/A",
                'altura': f"{altura_vertical:.2f}",
                'conversion': ""  # La calculadora de conversión funciona por separado
            }
            return render_template("resultado.html", resultados=resultados, 
                                   imagen_estatico=img_estatico, 
                                   imagen_interactivo=img_interactivo)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template("index.html", resultados=None)

if __name__ == "__main__":
    app.run(debug=True)
