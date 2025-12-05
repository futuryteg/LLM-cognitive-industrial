import json
from variablesG import URL
import os
from datetime import datetime

archivoDatos = 'datos.txt'
archivoConfig = 'config.json'
archivoConversacion = 'conversacion.json'

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def ExtraerDatosConfig():
    """Función para extraer los datos de la configuración, estos datos se encuentran en el archivo config.json"""
    
    with open(URL + '/' + archivoConfig) as config_file:
        data = json.load(config_file)
        return data

def ExtraerPalabraAct():
    """Función para extraer la palabra de activación, estos datos se encuentran en el archivo config.json"""
    
    data = ExtraerDatosConfig()
    return data['CHATGPT']['PALABRA_ACTIVACION']

def GuardarConversacion(Datos : dict):
    """Función para extraer la conversación del archivo de texto, 
    estos datos se encuentran en el archivo conversacion.txt"""    
    
    with open(URL + '/' + archivoConversacion, 'w') as archivo:
        json.dump(Datos, archivo, indent=4)
    
def GuardarEnArchivo(valores : dict):
    """Función para guardar los datos en un archivo de texto, estos datos se encuentran en el archivo datos.txt"""
    
    DatosGuardar = {}
    
    DatosGuardar["FECHA"] = str(datetime.now().strftime("%Y_%m_%d -> %H:%M"))
    DatosGuardar["VARIABLES"] = valores
        
    with open(URL + '/' + archivoDatos, 'w') as archivo:
        json.dump(DatosGuardar, archivo, indent=4)
        
def ActualizarDatos( * , Asistente : id = None, Almacen : id = None):
    """Funcion que accede a la configuración y guarda el id del asistente"""
    
    datos = ExtraerDatosConfig()
    
    if Asistente != None:
        datos['CHATGPT']['ASISTENTE'] = Asistente
    if Almacen != None:
        datos['CHATGPT']['ALMACEN'] = Almacen
    datos['CHATGPT']['NUMERO ARCHIVOS'] = ContarArchivos()
    datos['CHATGPT']['ARCHIVOS'] = VerArchivos()
    
    with open(URL + '/' + archivoConfig, 'w') as archivo:
        json.dump(datos, archivo, indent=4)
        
def TextoInicio():
    """Función para mostrar el texto de inicio"""
    text = ExtraerDatosConfig()['IG']['TextoInicio']
    return text.replace("PalabraReservada",ExtraerPalabraAct())

def VerArchivos():
    def AnalizarArchivo(ruta : str, archivo : str):
        """Función para analizar un archivo y obtener sus datos"""
        ArchivosPermitidos = ExtraerDatosConfig()['CHATGPT']['TIPOS']
        Datos = {"URL": archivo}
        for tipo in ArchivosPermitidos:
            if archivo.endswith(tipo):
                Datos["TIPO"] = tipo.upper().replace(".","")
                break
            elif '.' not in archivo:
                Datos["TIPO"] = "CARPETA"
                break
        return Datos

    def AnalizarCarpeta(carpeta : str, url : str):
        c = {"URL": carpeta + "/", "TIPO": "CARPETA", "ARCHIVOS": {}}
        for c1 in os.listdir(url):
            if os.path.isdir(url + "/" + c1):
                c["ARCHIVOS"][LN(c1)] = AnalizarCarpeta(c1, url + "/" + c1)
            else:
                c["ARCHIVOS"][LN(c1)] = AnalizarArchivo(url + "/", c1)
        return c

    def LN(nombre : str):
        return nombre.upper().split(".")[0]  

    Carpeta = {}
    Carp = ExtraerDatosConfig()['CHATGPT']['CARPETASDATOS']
    for C in os.listdir(URL):
        if os.path.isdir(URL + "/" + C) and C.upper() in Carp:
            Carpeta[LN(C)] = AnalizarCarpeta(C, URL + "/" + C)
    
    return Carpeta
    
def ContarArchivos():
    """Funcion para contar los archivos que se encuentran en la carpeta"""
    sum = 0
    for carpeta in ExtraerDatosConfig()['CHATGPT']['CARPETASDATOS']:
        for _, _, archivos in os.walk(URL + "/" + carpeta):
            if ExtraerDatosConfig()['CHATGPT']['ARCHIVOCOMUN'] in archivos:
                sum -= 1
            sum += len(archivos)
    return sum
    
#* ----------------------------------------------------------------
#* --------------------- Funciones de prueba ----------------------
#* ----------------------------------------------------------------

if __name__ == '__main__':    
    print(json.dumps(VerArchivos(), indent=4))