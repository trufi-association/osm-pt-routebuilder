# osm-pt-routebuilder

Herramienta para construir y actualizar relaciones de transporte público en OpenStreetMap (OSM) utilizando trazas GPS y el servicio Valhalla.

Este proyecto contiene dos scripts en Jython diseñados para ejecutarse dentro del entorno de JOSM (Java OpenStreetMap Editor), facilitando la creación o modificación de relaciones de tipo `route=bus` a partir de datos de trazas.

---

## 🔧 Configuración en JOSM

Para que los scripts funcionen correctamente, es necesario realizar algunos pasos previos en JOSM.

### 1. Activar los plugins necesarios
![Plugins requeridos](images/imagen1.png)

### 2. Configurar el entorno de scripting
![Configuración del scripting](images/imagen2.png)

### 3. Versión compatible del plugin de scripting
![Versión del plugin](images/imagen3.png)

### 4. Abrir los archivos `.py` desde el motor de scripting
![Menú para ejecutar scripts](images/imagen4.png)  
![Abrir archivos descargados](images/imagen5.png)

### 5. Seleccionar el motor Jython
![Seleccionar motor Jython](images/imagen6.png)

---

## 📂 Archivos incluidos

### `rt_creator.py`
- Genera una nueva relación OSM de tipo `route=bus` usando `way_id` obtenidos desde Valhalla.
- Exporta la relación a un archivo `.osm`.
- Genera una capa GPX a partir de las vías seleccionadas.

### `rt_updater.py`
- Tiene dos modos:
  - **Modo 1**: convierte una traza en `way_id` y los guarda en memoria.
  - **Modo 2**: aplica esos `way_id` a una relación seleccionada, reemplazando sus miembros.

---

## 🧩 Requisitos

- [JOSM](https://josm.openstreetmap.de/)
- Plugin de scripting habilitado
- Motor Jython configurado
- Conexión a internet (para Valhalla y OSM API)

---

## 🚀 Uso

A continuación se describen dos flujos de trabajo separados:

---

## 🧭 Crear una nueva relación

Este flujo está diseñado para construir una nueva relación de tipo `route=bus` desde cero, utilizando una traza GPS.

### 1. Cargar el archivo fuente en una capa independiente
![Archivo fuente seleccionado en rojo](images/imagen7.png)

### 2. Ejecutar el script `rt_creator.py`
![Selección del script con traza activa](images/imagen8.png)

### 3. Conversión automática a GPX
![Conversión automática a GPX](images/imagen11.png)

### 4. Abrir el archivo `rel.osm` generado

### 5. Ver la relación sin miembros descargados
![Relación sin miembros descargados](images/imagen9.png)

### 6. Descargar miembros de la relación
![Descarga de miembros de la relación](images/imagen10.png)

---

## 🔁 Actualizar una relación existente

Este flujo permite actualizar los miembros de una relación existente usando una traza nueva.

### 1. Cargar el archivo fuente como en la creación

### 2. Cargar la relación existente
![Relación cargada correctamente en capa aparte](images/imagen13.png)

### 3. Ejecutar el script `rt_updater.py` con la traza seleccionada
![Ejecutar el script con traza seleccionada](images/imagen12.png)

### 4. Seleccionar la relación existente
![Selección correcta de la relación](images/imagen14.png)

### 5. Ejecutar nuevamente el script con la relación seleccionada
![Ejecutar el script con traza seleccionada](images/imagen12.png)

> ⏳ Este paso puede tardar de 15 a 60 segundos.

### 6. Validar la relación actualizada

> ⚠️ Asegúrese de que la nueva relación no tenga interrupciones ni errores antes de subirla a OSM.

---

## 🗂️ Estructura del proyecto

```plaintext
osm-pt-routebuilder/
├── rt_creator.py
├── rt_updater.py
├── images/
│   ├── imagen1.png
│   ├── imagen2.png
│   ├── imagen3.png
│   ├── imagen4.png
│   ├── imagen5.png
│   ├── imagen6.png
│   ├── imagen7.png
│   ├── imagen8.png
│   ├── imagen9.png
│   ├── imagen10.png
│   ├── imagen11.png
│   ├── imagen12.png
│   ├── imagen13.png
│   └── imagen14.png
└── README.md
