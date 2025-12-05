import requests
import json
from json_Hilos import ExtraerDatosConfig
from datetime import datetime
import variablesG
import time

"""
CLIENTE API REST - NIVELES 4-5 (MES/ERP)
Consume la API REST de api_erp_mes_completa.py

Niveles:
- Nivel 4 (MES): Órdenes de producción, viabilidad
- Nivel 5 (ERP): Pedidos, inventario, producción, plantas
"""

valores_api = {}
"""Diccionario para almacenar los valores de la API"""

API_DISPONIBLE = False
"""Flag para saber si la API está disponible"""

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def ExtraerConfigAPI():
    """Extrae la configuración de la API desde config.json"""
    datos = ExtraerDatosConfig()
    
    # Si no existe la configuración de API, usar defaults
    if 'API' not in datos:
        return {
            'ESTADO': False,
            'BASE_URL': 'http://localhost:5000',  # o Colocar la IP del PC
            'TIMEOUT': 5,
            'ENDPOINTS': {
                # Nivel 4 - MES
                'mes_ordenes': '/api/mes/ordenes',
                'mes_viabilidad': '/api/mes/viabilidad',
                # Nivel 5 - ERP
                'erp_pedidos': '/api/erp/pedidos',
                'erp_inventario': '/api/erp/inventario',
                'erp_produccion_hoy': '/api/erp/produccion/hoy',
                'erp_plantas': '/api/erp/plantas',
                'erp_albaranes': '/api/erp/albaranes/ultimo',
                'health': '/api/health'
            }
        }
    
    return datos['API']

def VerificarConexionAPI():
    """Verifica si la API está disponible"""
    global API_DISPONIBLE
    
    config = ExtraerConfigAPI()
    
    if not config['ESTADO']:
        API_DISPONIBLE = False
        return False
    
    try:
        url = f"{config['BASE_URL']}/api/health"
        response = requests.get(url, timeout=config['TIMEOUT'])
        
        if response.status_code == 200:
            data = response.json()
            API_DISPONIBLE = True
            print(f"✅ API REST conectada: {data.get('status', 'online')}")
            return True
        else:
            API_DISPONIBLE = False
            print(f"⚠️  API respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        API_DISPONIBLE = False
        print(f"❌ Timeout al conectar a la API REST")
        return False
    except requests.exceptions.ConnectionError as e:
        API_DISPONIBLE = False
        print(f"❌ No se puede conectar a la API REST: {e}")
        return False
    except requests.exceptions.RequestException as e:
        API_DISPONIBLE = False
        print(f"❌ Error en API REST: {e}")
        return False

def ConsultarEndpoint(endpoint, params=None, method='GET', data=None):
    """Consulta un endpoint de la API
    
    Args:
        endpoint: Ruta del endpoint (ej: '/api/erp/pedidos')
        params: Query parameters (para GET)
        method: Método HTTP ('GET' o 'POST')
        data: Datos JSON (para POST)
    
    Returns:
        dict con la respuesta o None si error
    """
    if not API_DISPONIBLE:
        return None
    
    config = ExtraerConfigAPI()
    
    try:
        url = f"{config['BASE_URL']}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, params=params, timeout=config['TIMEOUT'])
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=config['TIMEOUT'])
        else:
            print(f"⚠️  Método HTTP no soportado: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Error en {endpoint}: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout en {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Error consultando {endpoint}: {type(e).__name__}")
        return None

#! ----------------------------------------------------------------
#! ---------------------- Funciones NIVEL 4 - MES -----------------
#! ----------------------------------------------------------------

def ConsultarOrdenesMES(planta=None):
    """
    Consulta órdenes de producción en MES
    
    Args:
        planta: ID de planta (1, 2, etc.) o None para todas
    
    Returns:
        dict con órdenes de producción
    """
    if not API_DISPONIBLE:
        return None
    
    params = {}
    if planta:
        params['planta'] = planta
    
    return ConsultarEndpoint('/api/mes/ordenes', params=params)

def VerificarViabilidadMES(volumen_m3, tipo_hormigon, fecha_entrega=None):
    """
    Verifica viabilidad de producción en MES
    
    Args:
        volumen_m3: Volumen solicitado en metros cúbicos
        tipo_hormigon: Tipo de hormigón (ej: 'C25/30')
        fecha_entrega: Fecha de entrega (opcional)
    
    Returns:
        dict con viabilidad, materiales necesarios, etc.
    """
    if not API_DISPONIBLE:
        return None
    
    data = {
        'volumen_m3': volumen_m3,
        'tipo_hormigon': tipo_hormigon
    }
    
    if fecha_entrega:
        data['fecha_entrega'] = fecha_entrega
    
    return ConsultarEndpoint('/api/mes/viabilidad', method='POST', data=data)

#! ----------------------------------------------------------------
#! ---------------------- Funciones NIVEL 5 - ERP -----------------
#! ----------------------------------------------------------------

def ConsultarPedidoERP(pedido_id):
    """
    Consulta detalles de un pedido específico en ERP
    
    Args:
        pedido_id: ID del pedido (ej: 2847)
    
    Returns:
        dict con detalles del pedido
    """
    if not API_DISPONIBLE:
        return None
    
    return ConsultarEndpoint(f'/api/erp/pedidos/{pedido_id}')

def ListarPedidosERP(estado=None, cliente=None):
    """
    Lista pedidos en ERP con filtros opcionales
    
    Args:
        estado: 'produccion', 'pendiente', 'completado' o None para todos
        cliente: Nombre del cliente o None para todos
    
    Returns:
        dict con lista de pedidos
    """
    if not API_DISPONIBLE:
        return None
    
    params = {}
    if estado:
        params['estado'] = estado
    if cliente:
        params['cliente'] = cliente
    
    return ConsultarEndpoint('/api/erp/pedidos', params=params)

def ConsultarInventarioERP(material=None):
    """
    Consulta inventario de materiales en ERP
    
    Args:
        material: 'cemento', 'aridos_gruesos', 'aridos_finos', 'agua', etc.
                 o None para todo el inventario
    
    Returns:
        dict con datos de inventario
    """
    if not API_DISPONIBLE:
        return None
    
    params = {}
    if material:
        params['material'] = material
    
    return ConsultarEndpoint('/api/erp/inventario', params=params)

def ConsultarProduccionHoyERP(planta=None):
    """
    Consulta producción del día actual en ERP
    
    Args:
        planta: ID de planta (1, 2, etc.) o None para todas
    
    Returns:
        dict con metros cúbicos producidos, cargas, etc.
    """
    if not API_DISPONIBLE:
        return None
    
    params = {}
    if planta:
        params['planta'] = planta
    
    return ConsultarEndpoint('/api/erp/produccion/hoy', params=params)

def ConsultarPlantasERP():
    """
    Consulta lista de plantas disponibles en ERP
    
    Returns:
        dict con lista de plantas
    """
    if not API_DISPONIBLE:
        return None
    
    return ConsultarEndpoint('/api/erp/plantas')

def ConsultarUltimoAlbaranERP(planta=None):
    """
    Consulta último albarán generado en ERP
    
    Args:
        planta: Nombre de planta (ej: 'Planta 1') o None
    
    Returns:
        dict con datos del albarán
    """
    if not API_DISPONIBLE:
        return None
    
    params = {}
    if planta:
        params['planta'] = planta
    
    return ConsultarEndpoint('/api/erp/albaranes/ultimo', params=params)

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def GenerarDatos():
    """
    Función para actualizar datos desde la API periódicamente
    Similar a GenerarDatos() en localC.py y globalC.py
    
    Actualiza cada 60 segundos (API es menos frecuente que SCADA)
    """
    global valores_api, API_DISPONIBLE
    
    config = ExtraerConfigAPI()
    
    if not config['ESTADO']:
        print("ℹ️  API REST deshabilitada en config.json")
        variablesG.nivel_api = False
        return
    
    # Verificar conexión inicial con reintentos
    max_reintentos = 3
    reintentos = 0
    
    while reintentos < max_reintentos and variablesG.Var:
        if VerificarConexionAPI():
            break
        else:
            reintentos += 1
            if reintentos < max_reintentos:
                print(f"⏳ Reintentando conexión a API REST en 5 segundos... ({reintentos}/{max_reintentos})")
                time.sleep(5)
    
    if not API_DISPONIBLE:
        print("❌ No se pudo conectar a la API REST después de varios intentos")
        print("ℹ️  El sistema continuará sin datos API (MES/ERP)")
        variablesG.nivel_api = False
        return
    
    print("🌐 Iniciando consultas periódicas a API REST...")
    
    try:
        errores_consecutivos = 0
        max_errores = 3
        
        while variablesG.Var and API_DISPONIBLE:
            try:
                # Consultar datos de todos los niveles
                
                # Nivel 4 - MES
                ordenes = ConsultarOrdenesMES()
                if ordenes:
                    valores_api['mes_ordenes'] = ordenes
                
                # Nivel 5 - ERP
                pedidos = ListarPedidosERP()
                if pedidos:
                    valores_api['erp_pedidos'] = pedidos
                
                inventario = ConsultarInventarioERP()
                if inventario:
                    valores_api['erp_inventario'] = inventario
                
                produccion = ConsultarProduccionHoyERP()
                if produccion:
                    valores_api['erp_produccion_hoy'] = produccion
                
                plantas = ConsultarPlantasERP()
                if plantas:
                    valores_api['erp_plantas'] = plantas
                
                # Reset contador de errores
                errores_consecutivos = 0
                
                # Actualizar cada 60 segundos
                for _ in range(60):
                    if not variablesG.Var:
                        break
                    time.sleep(1)
                
            except Exception as e:
                errores_consecutivos += 1
                print(f"⚠️  Error en consulta API: {e}")
                
                if errores_consecutivos >= max_errores:
                    print(f"❌ Demasiados errores consecutivos ({max_errores}), deteniendo API")
                    API_DISPONIBLE = False
                    variablesG.nivel_api = False
                    break
                
                time.sleep(5)
                
    except Exception as e:
        print(f"❌ Error general en GenerarDatos API: {e}")
        API_DISPONIBLE = False
        variablesG.nivel_api = False
    finally:
        print("🌐 Consultas a API REST detenidas")

def ExtraerVariables():
    """Función para extraer las variables generadas por la API"""
    return valores_api

def EstaDisponible():
    """Verifica si la API está disponible"""
    return API_DISPONIBLE

#! ----------------------------------------------------------------
#! ---------------------- Funciones de consulta rápida ------------
#! ----------------------------------------------------------------

def ObtenerDatosCompletosAPI():
    """
    Obtiene un snapshot completo de todos los datos de la API
    Útil para consultas multinivel del LLM
    
    Returns:
        dict con todos los datos disponibles
    """
    if not API_DISPONIBLE:
        return None
    
    datos_completos = {
        'timestamp': datetime.now().isoformat(),
        'nivel_4_mes': {
            'ordenes': ConsultarOrdenesMES(),
        },
        'nivel_5_erp': {
            'pedidos': ListarPedidosERP(),
            'inventario': ConsultarInventarioERP(),
            'produccion_hoy': ConsultarProduccionHoyERP(),
            'plantas': ConsultarPlantasERP()
        }
    }
    
    return datos_completos

def ConsultaRapidaMultinivel(consulta_tipo):
    """
    Ejecuta consultas predefinidas comunes para el LLM
    
    Args:
        consulta_tipo: 'produccion', 'inventario', 'viabilidad', 'completo'
    
    Returns:
        dict con datos relevantes
    """
    if not API_DISPONIBLE:
        return None
    
    if consulta_tipo == 'produccion':
        return {
            'produccion_hoy': ConsultarProduccionHoyERP(),
            'plantas': ConsultarPlantasERP(),
            'ordenes_activas': ConsultarOrdenesMES()
        }
    
    elif consulta_tipo == 'inventario':
        return {
            'inventario': ConsultarInventarioERP(),
            'puede_producir': True  # Se podría calcular
        }
    
    elif consulta_tipo == 'pedidos':
        return {
            'pedidos_pendientes': ListarPedidosERP(estado='pendiente'),
            'pedidos_produccion': ListarPedidosERP(estado='produccion'),
            'inventario': ConsultarInventarioERP()
        }
    
    elif consulta_tipo == 'completo':
        return ObtenerDatosCompletosAPI()
    
    else:
        return None

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------

if __name__ == "__main__":
    import threading
    variablesG.Var = True
    variablesG.EventoOPCUA = threading.Event()
    variablesG.EventoOPCUA.set()
    
    print("="*70)
    print("🧪 PRUEBA DE apiC.py - Cliente API MES/ERP")
    print("="*70)
    
    config = ExtraerConfigAPI()
    print(f"\n📡 URL base: {config['BASE_URL']}")
    
    # Verificar conexión
    print("\n🔌 Verificando conexión...")
    if VerificarConexionAPI():
        print("\n✅ Conexión exitosa\n")
        
        # Probar Nivel 4 - MES
        print("="*70)
        print("📊 NIVEL 4 - MES (Manufacturing Execution System)")
        print("="*70)
        
        print("\n1. Órdenes de producción:")
        ordenes = ConsultarOrdenesMES()
        if ordenes:
            print(f"   ✅ Total órdenes: {ordenes.get('count', 0)}")
            for orden in ordenes.get('ordenes', [])[:2]:
                print(f"   - Orden {orden['id_orden']}: {orden['tipo_hormigon']} - {orden['volumen_m3']}m³")
        
        print("\n2. Verificar viabilidad de producción:")
        viabilidad = VerificarViabilidadMES(45, 'C25/30')
        if viabilidad:
            print(f"   ✅ Viable: {viabilidad.get('viable', False)}")
            print(f"   - Planta: {viabilidad.get('planta_disponible', 'N/A')}")
            print(f"   - Comentario: {viabilidad.get('comentario', 'N/A')}")
        
        # Probar Nivel 5 - ERP
        print("\n" + "="*70)
        print("📈 NIVEL 5 - ERP (Enterprise Resource Planning)")
        print("="*70)
        
        print("\n3. Pedidos:")
        pedidos = ListarPedidosERP()
        if pedidos:
            print(f"   ✅ Total pedidos: {pedidos.get('count', 0)}")
            for pedido in pedidos.get('pedidos', [])[:2]:
                print(f"   - #{pedido['id']}: {pedido['cliente']} - {pedido['volumen_m3']}m³ ({pedido['estado']})")
        
        print("\n4. Inventario:")
        inventario = ConsultarInventarioERP()
        if inventario and 'inventario' in inventario:
            inv = inventario['inventario']
            print(f"   ✅ Cemento: {inv['cemento']['nivel_porcentaje']:.1f}% ({inv['cemento']['stock_actual_kg']} kg)")
            print(f"   ✅ Áridos gruesos: {inv['aridos_gruesos']['nivel_porcentaje']:.1f}% ({inv['aridos_gruesos']['stock_actual_kg']} kg)")
            print(f"   ✅ Agua: {inv['agua']['nivel_porcentaje']:.1f}% ({inv['agua']['stock_actual_litros']} L)")
        
        print("\n5. Producción de hoy:")
        produccion = ConsultarProduccionHoyERP()
        if produccion and 'produccion' in produccion:
            prod = produccion['produccion']
            print(f"   ✅ Total: {prod['total']['m3_producidos']} m³")
            print(f"   - Planta 1: {prod.get('planta_1', {}).get('m3_producidos', 0)} m³")
            print(f"   - Planta 2: {prod.get('planta_2', {}).get('m3_producidos', 0)} m³")

        print("\n6. Plantas disponibles:")
        plantas = ConsultarPlantasERP()
        if plantas:
            for planta in plantas.get('plantas', []):
                print(f"   ✅ {planta['nombre']}: {planta['capacidad_m3_hora']} m³/h ({planta['estado']})")
        
        print("\n7. Consulta multinivel completa:")
        completo = ObtenerDatosCompletosAPI()
        if completo:
            print("   ✅ Datos combinados de MES + ERP")
            print(f"   - Timestamp: {completo['timestamp']}")
            print(f"   - Órdenes MES: {len(completo['nivel_4_mes'].get('ordenes', {}).get('ordenes', []))}")
            print(f"   - Pedidos ERP: {len(completo['nivel_5_erp'].get('pedidos', {}).get('pedidos', []))}")
        
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*70)
        
    else:
        print("\n❌ No se pudo conectar a la API")
        print("\nVerifica que:")
        print("  1. api_erp_mes_completa.py esté corriendo en el PC")
        print("  2. La IP en config.json sea correcta")
        print("  3. El firewall permita conexiones al puerto 5000")
