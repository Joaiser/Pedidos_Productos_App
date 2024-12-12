import tkinter as tk
from tkinter import messagebox
import mysql.connector
from dotenv import load_dotenv
import os
import unicodedata
import threading

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de conexión a la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def obtener_grupos():
    """Obtiene los grupos desde la base de datos."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT g.id_group, gl.name AS group_name
            FROM ps_group g
            JOIN ps_group_lang gl ON g.id_group = gl.id_group
            WHERE gl.id_lang = 1;
        """
        cursor.execute(consulta)
        grupos = cursor.fetchall()
        conexion.close()
        return grupos
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
        return []

def obtener_precios_especificos(id_group):
    """Obtiene los precios específicos de cada producto y sus combinaciones para un grupo."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                p.id_product, pl.name AS product_name, 
                IFNULL(pa.reference, p.reference) AS reference,
                sp.price
            FROM ps_product p
            JOIN ps_product_lang pl ON p.id_product = pl.id_product
            LEFT JOIN ps_product_attribute pa ON p.id_product = pa.id_product
            LEFT JOIN ps_specific_price sp ON (p.id_product = sp.id_product OR pa.id_product_attribute = sp.id_product_attribute) AND sp.id_group = %s
            WHERE pl.id_lang = 1
            ORDER BY p.id_product, pa.id_product_attribute, sp.id_specific_price;
        """
        cursor.execute(consulta, (id_group,))
        precios = cursor.fetchall()
        conexion.close()
        return precios
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
        return []

def eliminar_tildes(texto):
    """Elimina las tildes de una cadena de texto."""
    return ''.join(
        (c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    )

def listar_precios(precios):
    """Lista los precios específicos de los productos y sus combinaciones."""
    precios_listados = {}
    for precio in precios:
        referencia = precio['reference']
        if referencia not in precios_listados:
            precios_listados[referencia] = {
                'product_name': precio['product_name'],
                'precios': []
            }
        precios_listados[referencia]['precios'].append(precio['price'])

    detalles = ""
    for referencia, data in precios_listados.items():
        detalles += f"Referencia: {referencia} - {data['product_name']}\n"
        for precio in data['precios']:
            if precio is not None:
                detalles += f"Precio: {precio:.2f} €\n"
            else:
                detalles += "Precio: N/A\n"
        detalles += "\n"
    return detalles

def mostrar_precios(id_group):
    """Muestra los precios específicos de cada producto y sus combinaciones para un grupo en una nueva ventana."""
    precios = obtener_precios_especificos(id_group)
    detalles = listar_precios(precios)

    # Crear una nueva ventana para mostrar los precios
    detalle_ventana = tk.Toplevel()
    detalle_ventana.title("Precios Específicos")
    detalle_ventana.geometry("800x600")

    # Crear el widget de texto con barras de desplazamiento
    frame_con_scroll = tk.Frame(detalle_ventana)
    frame_con_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    global text_widget
    text_widget = tk.Text(frame_con_scroll, wrap="word", font=("Arial", 12))
    scrollbar = tk.Scrollbar(frame_con_scroll, orient="vertical", command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set)

    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Insertar los detalles en el widget de texto
    for linea in detalles.split('\n'):
        text_widget.insert(tk.END, linea + '\n')

    # Crear el botón de búsqueda
    search_button = tk.Button(detalle_ventana, text="🔍", font=("Arial", 12), command=lambda: mostrar_busqueda(detalle_ventana, id_group))
    search_button.place(x=750, y=10)

def mostrar_busqueda(ventana, id_group):
    """Muestra el campo de búsqueda y actualiza la lista de productos a medida que se escribe."""
    search_var = tk.StringVar()

    def actualizar_busqueda(*args):
        search_term = eliminar_tildes(search_var.get().lower())
        precios = obtener_precios_especificos(id_group)
        detalles = listar_precios(precios)
        text_widget.delete("1.0", tk.END)
        for linea in detalles.split('\n\n'):
            if search_term in eliminar_tildes(linea.lower()):
                text_widget.insert(tk.END, linea + '\n')

    search_var.trace("w", actualizar_busqueda)

    search_entry = tk.Entry(ventana, textvariable=search_var, font=("Arial", 12), bg="black", fg="white")
    search_entry.place(x=600, y=10)

def cargar_precios_en_hilo(id_group):
    """Carga los precios en un hilo separado para no bloquear la interfaz de usuario."""
    hilo = threading.Thread(target=mostrar_precios, args=(id_group,))
    hilo.start()

def crear_interfaz():
    """Crea la interfaz gráfica principal."""
    root = tk.Tk()
    root.title("Precios Específicos de Productos")

    # Configurar tamaño de la ventana (centrada)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = int(screen_width * 0.75)
    height = int(screen_height * 0.75)
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(root, text="Seleccione un Grupo para Ver los Precios Específicos", font=("Arial", 16)).pack(pady=20)

    # Obtener los grupos y mostrarlos en la pantalla principal
    grupos = obtener_grupos()
    frame_con_scroll = tk.Frame(root)
    frame_con_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame_con_scroll, font=("Arial", 12))
    scrollbar = tk.Scrollbar(frame_con_scroll, orient="vertical", command=listbox.yview)
    listbox.config(yscrollcommand=scrollbar.set)

    # Colocamos el Listbox y el Scrollbar para que sean más cómodos de usar
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for grupo in grupos:
        listbox.insert(tk.END, grupo['group_name'])

    def on_double_click(event):
        seleccion = listbox.curselection()
        if seleccion:
            index = seleccion[0]
            id_group = grupos[index]['id_group']
            cargar_precios_en_hilo(id_group)

    listbox.bind('<Double-1>', on_double_click)

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()