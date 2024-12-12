import tkinter as tk
from tkinter import messagebox
import mysql.connector
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de conexión a la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Lista global para almacenar los pedidos
pedidos = []

def obtener_pedidos(limite, offset):
    """Obtiene los pedidos de la base de datos con un límite y un offset."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                o.id_order, o.reference, o.total_paid, o.date_add, o.current_state, 
                c.firstname, c.lastname, c.email, a.address1, a.city, a.postcode 
            FROM ps_orders o
            JOIN ps_customer c ON o.id_customer = c.id_customer
            JOIN ps_address a ON o.id_address_delivery = a.id_address
            ORDER BY o.date_add DESC 
            LIMIT %s OFFSET %s;
        """
        cursor.execute(consulta, (limite, offset))
        global pedidos
        pedidos = cursor.fetchall()
        conexion.close()
        return pedidos
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
        return []

def obtener_productos(id_order):
    """Obtiene los productos asociados a un pedido."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT 
                od.product_name, od.product_quantity, od.product_price, od.product_reference
            FROM ps_order_detail od
            WHERE od.id_order = %s;
        """
        cursor.execute(consulta, (id_order,))
        productos = cursor.fetchall()
        conexion.close()
        return productos
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"No se pudo obtener los productos:\n{e}")
        return []

def mostrar_detalles(pedido):
    """Muestra los detalles de un pedido seleccionado, incluyendo los productos."""
    detalles = f"""
    Pedido ID: {pedido['id_order']}
    Referencia: {pedido['reference']}
    Total: {pedido['total_paid']} €
    Fecha: {pedido['date_add']}
    Cliente: {pedido['firstname']} {pedido['lastname']}
    Correo: {pedido['email']}
    Dirección: {pedido['address1']}, {pedido['city']} - {pedido['postcode']}
    """
    
    productos = obtener_productos(pedido['id_order'])  # Obtener los productos del pedido
    detalles_productos = "\nProductos:\n"
    for producto in productos:
        detalles_productos += f"{producto['product_name']} - Referencia: {producto['product_reference']} - Cantidad: {producto['product_quantity']} - Precio: {producto['product_price']} €\n"

    # Mostrar los productos en los detalles
    detalles += detalles_productos
    
    # Ventana emergente con detalles más grande
    detalle_ventana = tk.Toplevel()
    detalle_ventana.title("Detalles del Pedido")
    detalle_ventana.geometry("800x800")  # Aumentamos el tamaño de la ventana

    tk.Label(detalle_ventana, text=detalles, justify="left", font=("Arial", 12)).pack(padx=10, pady=10)

    # Botón para transcribir
    def transcribir():
        with open("transcripciones.txt", "a") as archivo:
            archivo.write(detalles + "\n")
        messagebox.showinfo("Transcripción", "Pedido transcrito con éxito.")

    tk.Button(detalle_ventana, text="Transcribir", command=transcribir).pack(pady=10)

def crear_interfaz():
    """Crea la interfaz gráfica principal."""
    root = tk.Tk()
    root.title("Pedidos PrestaShop")

    # Configurar tamaño de la ventana (grande y centrada)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = int(screen_width * 0.75)
    height = int(screen_height * 0.75)
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(root, text="Últimos Pedidos", font=("Arial", 16)).pack(pady=10)

    # Contenedor con barra de scroll para toda la ventana
    frame_con_scroll = tk.Frame(root)
    frame_con_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame_con_scroll, font=("Arial", 12))
    scrollbar = tk.Scrollbar(frame_con_scroll, orient="vertical", command=listbox.yview)
    listbox.config(yscrollcommand=scrollbar.set)

    # Colocamos el Listbox y el Scrollbar para que sean más cómodos de usar
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Variables para el filtro y la paginación
    limite_var = tk.IntVar(value=50)
    offset_var = tk.IntVar(value=0)

    def actualizar_lista():
        listbox.delete(0, tk.END)
        pedidos = obtener_pedidos(limite_var.get(), offset_var.get())
        for pedido in pedidos:
            texto_pedido = f"{pedido['id_order']} - {pedido['reference']} - {pedido['firstname']} {pedido['lastname']} - {pedido['total_paid']} €"
            listbox.insert(tk.END, texto_pedido)

    def on_double_click(event):
        seleccion = listbox.curselection()
        if seleccion:
            index = seleccion[0]
            pedido = pedidos[index]
            mostrar_detalles(pedido)

    listbox.bind('<Double-1>', on_double_click)

    # Filtro para seleccionar la cantidad de pedidos
    tk.Label(root, text="Paginación:", font=("Arial", 12)).pack(pady=5)
    opciones_limite = [50, 100, 150, 200]
    limite_menu = tk.OptionMenu(root, limite_var, *opciones_limite, command=lambda _: actualizar_lista())
    limite_menu.pack(pady=10)

    # Botones de paginación
    def siguiente_pagina():
        offset_var.set(offset_var.get() + limite_var.get())
        actualizar_lista()

    def pagina_anterior():
        if offset_var.get() >= limite_var.get():
            offset_var.set(offset_var.get() - limite_var.get())
        else:
            offset_var.set(0)
        actualizar_lista()

    tk.Button(root, text="Página Anterior", command=pagina_anterior, font=("Arial", 12)).pack(side="left", padx=10, pady=10)
    tk.Button(root, text="Siguiente Página", command=siguiente_pagina, font=("Arial", 12)).pack(side="right", padx=10, pady=10)

    # Inicializar la lista de pedidos
    actualizar_lista()

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()