import tkinter as tk
from threading import Thread
from queue import Queue
from PIL import Image, ImageTk
from json_Hilos import TextoInicio
import variablesG

tam = 380
bot_image_path = variablesG.URL + "/" + "Imagen.png"
imagen_Icono = variablesG.URL + "/" + "Imagen.png"

class ClassIG:
    def __init__(self, on_close=None):
        self.ventana = tk.Tk()
        self.ventana.title("ChatBot")
        try:
            img = Image.open(imagen_Icono)
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.ventana.iconphoto(False, photo)
            self.ventana._icon_ref = photo
        except:
            pass
        
        self.ventana.geometry("500x700")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg='#002957')

        self.main_frame = tk.Frame(self.ventana, bg='#b4bbcc')
        self.main_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg='#b4bbcc', bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set, width=380, height=500)

        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.frame = tk.Frame(self.canvas, bg='#b4bbcc')
        self.frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor='nw')

        self.frame.bind("<Configure>", self.on_frame_configure)

        self.frameEntrada = tk.Frame(self.ventana, bg='#002957')
        self.frameEntrada.pack(side='bottom', fill='x', pady=10, padx=15)

        self.entrada = tk.Entry(self.frameEntrada, bg='#D1E7DD', font=('Arial', 12), relief='flat')
        self.entrada.pack(side="left", fill='x', expand=True)
        self.entrada.bind("<Return>", self.enviar)  # Vincular la tecla "Enter" al método "enviar"
        
        self.frameHueco = tk.Frame(self.frameEntrada, bg='#002957', width=10)
        self.frameHueco.pack(side='left')

        self.boton = tk.Button(
            self.frameEntrada, 
            text="Enviar", 
            command=self.enviar, 
            bg='#002957', 
            font=('Arial', 12), 
            relief='flat', 
            fg="#ffffff",
            activebackground='#b4bbcc',
            activeforeground='#000000',
            bd=0
        )
        
        self.boton.pack(side="left")

        self.queue = Queue()
        self.process_thread = None
        self.on_close = on_close
        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        if self.on_close:
            self.on_close()
        else:
            self.ventana.destroy()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.frame_id, width=self.canvas.winfo_width())

    def enviar(self, event=None):
        mensaje = self.entrada.get()
        self.entrada.delete(0, tk.END)

        if self.process_thread is None or not self.process_thread.is_alive():
            self.process_thread = Thread(target=self.procesar_mensaje, args=(mensaje,))
            self.process_thread.start()
        else:
            self.queue.put((mensaje, "Usuario"))

    def procesar_mensaje(self, mensaje):
        # Llamar a ProcesadoDeOrdenes y pasar las funciones para subir mensajes
        from main import ProcesadoDeOrdenes
        ProcesadoDeOrdenes(mensaje, self.subir_usuario, self.subir_bot)

    def subir_usuario(self, mensaje):
        self.queue.put((mensaje, "Usuario"))
        self.ventana.after(100, self.check_queue)

    def subir_bot(self, mensaje):
        self.queue.put((mensaje, "Bot"))
        self.ventana.after(100, self.check_queue)

    def check_queue(self):
        while not self.queue.empty():
            mensaje, duenyo = self.queue.get()
            self.subir(mensaje, duenyo)

    def subir(self, mensaje: str, duenyo: str = "Usuario"):
        if duenyo == "Usuario":
            self.subir_usuario_frame(mensaje)
        elif duenyo == "Bot":
            self.subir_bot_frame(mensaje)
        elif duenyo == "Sistema":
            self.subir_Sistema_frame(mensaje)

        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.yview_moveto(1.0)

    def subir_usuario_frame(self, mensaje: str):
        user_frame = tk.Frame(
            self.frame, 
            bg='#b4bbcc'
        )
        user_label = tk.Label(
            user_frame, 
            text=mensaje, 
            bg='#D1E7DD', 
            padx=10, 
            pady=5, 
            font=('Arial', 12), 
            wraplength=tam
        )
        user_label.pack(anchor='e')
        user_frame.pack(anchor='e', pady=5, padx=20, fill='none')
        
    def subir_Sistema_frame(self, mensaje: str):
        Sistema_frame = tk.Frame(
            self.frame, 
            bg='#b4bbcc'
        )
        Sistema_label = tk.Label(
            Sistema_frame,
            text=mensaje,
            bg='#f0f0f0',
            padx=10,
            pady=5,
            font=('Arial', 12),
            wraplength=tam
        )
        Sistema_label.pack(fill='y')
        Sistema_frame.pack(pady=5, padx=20, fill='none')

    def subir_bot_frame(self, mensaje: str):
        bot_frame = tk.Frame(self.frame, bg='#b4bbcc')
        
        bot_image = Image.open(bot_image_path)
        bot_image = bot_image.resize((20, 20))  # Ajustar tamaño de la imagen
        bot_photo = ImageTk.PhotoImage(bot_image)
        
        bot_image_frame = tk.Frame(bot_frame, bg='#b4bbcc')
        
        bot_image_label = tk.Label(bot_image_frame, image=bot_photo, bg='#b4bbcc')
        bot_image_label.image = bot_photo  # Guardar una referencia para evitar que se recoja la basura

        bot_label = tk.Label(
            bot_frame,
            text=mensaje,
            bg='#F8D7DA',
            padx=10,
            pady=5,
            font=('Arial', 12),
            wraplength=tam
        )
        
        bot_image_label.pack(side='top', padx=(0, 5))
        bot_image_frame.pack(side='left')
        bot_label.pack(side='left', anchor='w')
        
        bot_frame.pack(anchor='w', pady=5, padx=20, fill='none')

    def run(self):
        self.subir(TextoInicio(), "Sistema")
        self.ventana.mainloop()

if __name__ == "__main__":
    IG = ClassIG()
    IG.run()
