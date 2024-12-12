import tkinter as tk
import subprocess

def abrir_app_pedidos():
    subprocess.Popen(["python", "app_pedidos.py"])

def abrir_Products():
    subprocess.Popen(["python", "products.py"])

def crear_interfaz_principal():
    root = tk.Tk()
    root.title("Página Principal")

    # Configurar tamaño de la ventana (centrada)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = 400
    height = 200
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(root, text="Seleccione una aplicación", font=("Arial", 16)).pack(pady=20)

    tk.Button(root, text="App Pedidos", command=abrir_app_pedidos, font=("Arial", 12)).pack(pady=10)
    tk.Button(root, text="App Productos", command=abrir_Products, font=("Arial", 12)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz_principal()