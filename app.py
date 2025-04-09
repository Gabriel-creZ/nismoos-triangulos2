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

# Configuración SMTP para reporte de errores
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'

# -----------------------------------------------------------
# Funciones para resolver triángulos (ley de senos y cosenos)
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

def resolver_triangulo(a, b, c, A, B, C):
    # Se determina el método (senos o cosenos) en base a los datos
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    if count_sides + count_angles < 3 or count_sides < 1:
        raise ValueError("Se requieren al menos 3 datos (con al menos 1 lado) para resolver el triángulo.")
    if count_angles >= 2:
        metodo = "senos"
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C,
                                      lado_a=a, lado_b=b, lado_c=c), metodo
    elif count_sides == 3:
        metodo = "cosenos"
        return calcular_triangulo_cos(a=a, b=b, c=c, A=A, B=B, C=C), metodo
    else:
        metodo = "senos"
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C,
                                      lado_a=a, lado_b=b, lado_c=c), metodo

# -----------------------------------------------------------
# Funciones adicionales: medianas (m₁, m₂, m₃), circuncentro, ortocentro, tipo de triángulo, clasificación y conversión de unidades
# -----------------------------------------------------------
def calcular_medianas(a, b, c):
    m1 = 0.5 * math.sqrt(2*(b**2 + c**2) - a**2)
    m2 = 0.5 * math.sqrt(2*(a**2 + c**2) - b**2)
    m3 = 0.5 * math.sqrt(2*(a**2 + b**2) - c**2)
    return m1, m2, m3

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
    # Se utiliza la conversión a metros y luego de metros a la unidad destino
    factores = {
        "Milímetros": 0.001,
        "Centímetros": 0.01,
        "Decímetros": 0.1,
        "Metros": 1,
        "Decámetros": 10,
        "Hectómetros": 100,
        "Kilómetros": 1000,
        "Pulgadas": 0.0254,
        "Pies": 0.3048,
        "Yardas": 0.9144,
        "Millas": 1609.34
    }
    try:
        factor_de = factores[de_unidad]
        factor_a = factores[a_unidad]
    except KeyError:
        raise ValueError("Conversión no soportada.")
    return valor * (factor_de / factor_a)

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
# Nueva función: Calcular distancias entre puntos y procedimiento completo
# -----------------------------------------------------------
def calcular_distancias(y1, x1, y2, x2, y3=None, x3=None):
    # Calcula las distancias entre dos o tres puntos
    # Se espera que las coordenadas sean numéricas y se muestran los pasos.
    procedimiento = ""
    def distancia(p1, p2):
        d = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        return d
    A = (x1, y1)
    B = (x2, y2)
    d_AB = distancia(A, B)
    procedimiento += f"Distancia AB: sqrt(({x2}-{x1})² + ({y2}-{y1})²) = sqrt({(x2-x1)**2} + {(y2-y1)**2}) = {d_AB:.2f}\n"
    if x3 is not None and y3 is not None:
        C = (x3, y3)
        d_BC = distancia(B, C)
        d_AC = distancia(A, C)
        procedimiento += f"Distancia BC: sqrt(({x3}-{x2})² + ({y3}-{y2})²) = {d_BC:.2f}\n"
        procedimiento += f"Distancia AC: sqrt(({x3}-{x1})² + ({y3}-{y1})²) = {d_AC:.2f}\n"
        return {"AB": d_AB, "BC": d_BC, "AC": d_AC}, procedimiento
    else:
        return {"AB": d_AB}, procedimiento

# -----------------------------------------------------------
# Funciones de graficado: estático e interactivo
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
    # Medianas: etiquetadas como m₁, m₂, m₃
    mid_AB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    mid_BC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    mid_AC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    plt.plot([C_point[0], mid_AB[0]], [C_point[1], mid_AB[1]], 'k--', label="m₁")
    plt.plot([A_point[0], mid_BC[0]], [A_point[1], mid_BC[1]], 'k--', label="m₂")
    plt.plot([B_point[0], mid_AC[0]], [B_point[1], mid_AC[1]], 'k--', label="m₃")
    # Altura vertical
    plt.plot([C_point[0], C_point[0]], [C_point[1], 0], 'm--', label="Altura")
    # Circuncentro y ortocentro
    circ = calcular_circuncentro(A_point, B_point, C_point)
    orto = calcular_ortocentro(A_point, B_point, C_point)
    if circ:
        plt.plot(circ[0], circ[1], 'co', markersize=8, label="Circuncentro")
        plt.text(circ[0]+0.1, circ[1], "Circuncentro", color='cyan')
    if orto:
        plt.plot(orto[0], orto[1], 'mo', markersize=8, label="Ortocentro")
        plt.text(orto[0]+0.1, orto[1], "Ortocentro", color='magenta')
    # Etiquetas de vértices
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
    mid_AB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    mid_BC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    mid_AC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    fig.add_trace(go.Scatter(x=[C_point[0], mid_AB[0]], y=[C_point[1], mid_AB[1]],
                             mode='lines', name="m₁", line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=[A_point[0], mid_BC[0]], y=[A_point[1], mid_BC[1]],
                             mode='lines', name="m₂", line=dict(color='black', dash='dash')))
    fig.add_trace(go.Scatter(x=[B_point[0], mid_AC[0]], y=[B_point[1], mid_AC[1]],
                             mode='lines', name="m₃", line=dict(color='black', dash='dash')))
    # Altura
    fig.add_trace(go.Scatter(x=[C_point[0], C_point[0]], y=[C_point[1], 0],
                             mode='lines', name="Altura", line=dict(color='magenta', dash='dot')))
    # Circuncentro y ortocentro con nombres correctos
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
    # Etiquetar vértices
    fig.add_trace(go.Scatter(x=[A_point[0]], y=[A_point[1]], mode='markers+text',
                             text=["Punto a"], textposition="top left", marker=dict(color='black', size=8)))
    fig.add_trace(go.Scatter(x=[B_point[0]], y=[B_point[1]], mode='markers+text',
                             text=["Punto b"], textposition="top right", marker=dict(color='black', size=8)))
    fig.add_trace(go.Scatter(x=[C_point[0]], y=[C_point[1]], mode='markers+text',
                             text=["Punto c"], textposition="bottom center", marker=dict(color='black', size=8)))
    fig.update_layout(title="Grafica Interactiva del Triángulo",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      legend_title="Leyenda",
                      template="plotly_white",
                      autosize=True,
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig.to_html(full_html=False)

# -----------------------------------------------------------
# Nueva función: Calcular distancias entre puntos con procedimiento completo
# -----------------------------------------------------------
def calcular_distancias(p1_x, p1_y, p2_x, p2_y, p3_x=None, p3_y=None):
    procedimiento = ""
    def distancia(x1, y1, x2, y2):
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return d
    AB = distancia(p1_x, p1_y, p2_x, p2_y)
    procedimiento += f"AB = sqrt(({p2_x} - {p1_x})² + ({p2_y} - {p1_y})²) = sqrt({(p2_x - p1_x)**2} + {(p2_y - p1_y)**2}) = {AB:.2f}\n"
    if p3_x is not None and p3_y is not None:
        BC = distancia(p2_x, p2_y, p3_x, p3_y)
        AC = distancia(p1_x, p1_y, p3_x, p3_y)
        procedimiento += f"BC = sqrt(({p3_x} - {p2_x})² + ({p3_y} - {p2_y})²) = {BC:.2f}\n"
        procedimiento += f"AC = sqrt(({p3_x} - {p1_x})² + ({p3_y} - {p1_y})²) = {AC:.2f}\n"
        return {"AB": AB, "BC": BC, "AC": AC}, procedimiento
    else:
        return {"AB": AB}, procedimiento

# -----------------------------------------------------------
# Integración del cálculo de distancias en la ruta principal
# -----------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            # Función auxiliar para convertir valor de texto a float
            def get_val(field):
                val = request.form.get(field)
                return float(val) if val and val.strip() != "" else None

            # Verificamos si se ingresaron coordenadas para distancias
            p1_x = get_val("p1_x")
            p1_y = get_val("p1_y")
            p2_x = get_val("p2_x")
            p2_y = get_val("p2_y")
            p3_x = get_val("p3_x")
            p3_y = get_val("p3_y")

            if p1_x is not None and p1_y is not None and p2_x is not None and p2_y is not None:
                # Modo calcular distancias (para 2 o 3 puntos)
                distancias, proc = calcular_distancias(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y)
                # También se puede calcular el triángulo (si se dieron 3 puntos) y graficarlo
                if "AC" in distancias:
                    perimetro = distancias["AB"] + distancias["BC"] + distancias["AC"]
                    s = perimetro/2
                    area = math.sqrt(s*(s-distancias["AB"])*(s-distancias["BC"])*(s-distancias["AC"]))
                    procedimiento_tri = f"Área (Herón) = sqrt({s}({s-distancias['AB']:.2f})({s-distancias['BC']:.2f})({s-distancias['AC']:.2f})) = {area:.2f}"
                else:
                    perimetro = distancias["AB"]
                    area = "N/A"
                    procedimiento_tri = ""
                # Generar gráfica interactiva basada en coordenadas
                fig = go.Figure()
                # Dibujar puntos y lados si hay 3 puntos
                fig.add_trace(go.Scatter(x=[p1_x, p2_x], y=[p1_y, p2_y],
                                         mode='lines+markers', name="Segmento AB", line=dict(color='blue')))
                if p3_x is not None and p3_y is not None:
                    fig.add_trace(go.Scatter(x=[p2_x, p3_x], y=[p2_y, p3_y],
                                             mode='lines+markers', name="Segmento BC", line=dict(color='red')))
                    fig.add_trace(go.Scatter(x=[p1_x, p3_x], y=[p1_y, p3_y],
                                             mode='lines+markers', name="Segmento AC", line=dict(color='green')))
                fig.update_layout(template="plotly_white",
                                  autosize=True,
                                  margin=dict(l=20, r=20, t=30, b=20))
                grafica_coord = fig.to_html(full_html=False)
                # Preparar resultados del modo distancias
                resultados = {
                    'modo': "Coordenadas",
                    'distancias': distancias,
                    'procedimiento': proc + "\n" + procedimiento_tri,
                    'perimetro': f"{perimetro:.2f}" if isinstance(perimetro, float) else perimetro,
                    'area': f"{area:.2f}" if isinstance(area, float) else area
                }
                return render_template("resultado.html", resultados=resultados,
                                       imagen_estatico=None, imagen_interactivo=grafica_coord)
            else:
                # Modo tradicional: calcular triángulo usando lados y ángulos
                a_val = get_val("lado_a")
                b_val = get_val("lado_b")
                c_val = get_val("lado_c")
                A_val = get_val("angulo_A")
                B_val = get_val("angulo_B")
                C_val = get_val("angulo_C")

                (res_a, res_b, res_c, res_A, res_B, res_C), metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val)
                perimetro = res_a + res_b + res_c
                s = perimetro / 2
                area = math.sqrt(s * (s - res_a) * (s - res_b) * (s - res_c))

                mediana_1, mediana_2, mediana_3 = calcular_medianas(res_a, res_b, res_c)
                circumradius = calcular_circumradius(res_a, res_b, res_c, area)
                tipo_triangulo = determinar_tipo_triangulo(res_a, res_b, res_c)
                clasificacion_angulo = determinar_clasificacion_angulo(res_A, res_B, res_C)
                altura_vertical = res_b * math.sin(math.radians(res_A))

                img_estatico, A_pt, B_pt, C_pt = graficar_triangulo_estatico(res_a, res_b, res_c, res_A, res_B, res_C, metodo)
                img_interactivo = graficar_triangulo_interactivo(res_a, res_b, res_c, res_A, res_B, res_C)
                circ = calcular_circuncentro(A_pt, B_pt, C_pt)
                orto = calcular_ortocentro(A_pt, B_pt, C_pt)

                resultados = {
                    'modo': "Triángulo",
                    'lado_a': f"{res_a:.2f}",
                    'lado_b': f"{res_b:.2f}",
                    'lado_c': f"{res_c:.2f}",
                    'angulo_A': f"{res_A:.2f}",
                    'angulo_B': f"{res_B:.2f}",
                    'angulo_C': f"{res_C:.2f}",
                    'perimetro': f"{perimetro:.2f}",
                    'area': f"{area:.2f}",
                    'mediana_1': f"{mediana_1:.2f}",
                    'mediana_2': f"{mediana_2:.2f}",
                    'mediana_3': f"{mediana_3:.2f}",
                    'circumradius': f"{circumradius:.2f}" if circumradius is not None else "N/A",
                    'tipo_triangulo': tipo_triangulo,
                    'clasificacion_angulo': clasificacion_angulo,
                    'metodo': metodo,
                    'circuncentro': f"({circ[0]:.2f}, {circ[1]:.2f})" if circ else "N/A",
                    'ortocentro': f"({orto[0]:.2f}, {orto[1]:.2f})" if orto else "N/A",
                    'altura': f"{altura_vertical:.2f}"
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