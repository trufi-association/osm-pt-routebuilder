import sys
import urllib2
import json
from javax.swing import JOptionPane
from org.openstreetmap.josm.gui import MainApplication
from org.openstreetmap.josm.data.osm import Way, Relation, RelationMember
from org.openstreetmap.josm.io import OsmReader
from org.openstreetmap.josm.gui.layer import GpxLayer
from org.openstreetmap.josm.data.gpx import GpxData, GpxTrack, GpxTrackSegment, WayPoint
from java.io import ByteArrayInputStream
from java.util import HashMap
from java.util import ArrayList

# Módulo persistente para almacenar la traza (modo memoria)
if "traza_memoria" not in sys.modules:
    import types
    sys.modules["traza_memoria"] = types.ModuleType("traza_memoria")
    sys.modules["traza_memoria"].way_ids = []

import traza_memoria

layer_manager = MainApplication.getLayerManager()

# Obtener capa de edición activa de forma segura
edit_layer_obj = layer_manager.getEditLayer()
if edit_layer_obj is None:
    from org.openstreetmap.josm.gui.layer import OsmDataLayer
    from org.openstreetmap.josm.data.osm import DataSet
    from java.io import File

    nueva_capa = OsmDataLayer(DataSet(), "Nueva capa PT generada", File(""))
    layer_manager.addLayer(nueva_capa)
    layer_manager.setActiveLayer(nueva_capa)
    edit_layer = nueva_capa.data
else:
    edit_layer = edit_layer_obj.data

selection = edit_layer.getSelected()
selected_ways = [p for p in selection if isinstance(p, Way)]
selected_relations = [p for p in selection if isinstance(p, Relation)]

# === MODO 1 === Procesar traza con Valhalla
if selected_ways and not selected_relations:
    points = []
    for way in selected_ways:
        points.extend([{ "lat": node.getCoor().lat(), "lon": node.getCoor().lon() } for node in way.getNodes()])

    if len(points) < 2:
        JOptionPane.showMessageDialog(None, "La traza seleccionada no tiene suficientes puntos.")
    else:
        try:
            url = "http://valhalla1.openstreetmap.de/trace_attributes"
            headers = {"Content-Type": "application/json"}
            request_data = {
                "shape": points,
                "costing": "auto",
                "shape_match": "walk_or_snap"
            }
            data = json.dumps(request_data)
            request = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(request)
            result = json.loads(response.read())

            raw_way_ids = [str(edge["way_id"]) for edge in result.get("edges", [])]
            way_ids = []
            for i, wid in enumerate(raw_way_ids):
                if i == 0 or wid != raw_way_ids[i - 1]:
                    way_ids.append(int(wid))

            if not way_ids:
                JOptionPane.showMessageDialog(None, "Valhalla no devolvió ninguna vía.")
            else:
                traza_memoria.way_ids = way_ids

                # Crear GPX a partir de la capa activa
                active_layer = layer_manager.getActiveLayer()
                if not active_layer or not hasattr(active_layer, 'data'):
                    JOptionPane.showMessageDialog(None, "No se pudo crear la capa GPX.")
                else:
                    dataset = active_layer.data
                    gpx_data = GpxData()
                    all_segments = []

                    for primitive in dataset.getWays():
                        if primitive.isUsable():
                            wp_list = []
                            for node in primitive.getNodes():
                                if node.isLatLonKnown():
                                    wp_list.append(WayPoint(node.getCoor()))
                            if wp_list:
                                all_segments.append(GpxTrackSegment(wp_list))

                    if all_segments:
                        segments_java = ArrayList()
                        for s in all_segments:
                            segments_java.add(s)

                        gpx_track = GpxTrack(segments_java, HashMap())
                        gpx_data.addTrack(gpx_track)
                        gpx_layer = GpxLayer(gpx_data, "Traza GPX visual")
                        layer_manager.addLayer(gpx_layer)

                        # Activar nueva capa y eliminar la anterior sin confirmación
                        if gpx_layer in layer_manager.getLayers():
                            layer_manager.setActiveLayer(gpx_layer)
                        layer_manager.removeLayer(active_layer)

                        JOptionPane.showMessageDialog(
                            None,
                            "Valhalla completado.\nSe guardaron {} vias en memoria.\n\nAhora selecciona la relacion a actualizar y vuelve a ejecutar el script.".format(len(way_ids))

                        )
                    else:
                        JOptionPane.showMessageDialog(None, "No se pudieron generar segmentos GPX.")
        except Exception as e:
            JOptionPane.showMessageDialog(None, "Error en Valhalla:\n{}".format(str(e)))

# === MODO 2 === Aplicar traza almacenada a relación seleccionada
elif selected_relations and not selected_ways:
    way_ids = getattr(traza_memoria, "way_ids", [])
    if not way_ids:
        JOptionPane.showMessageDialog(None, "No hay vías almacenadas. Primero selecciona una traza.")
    elif len(selected_relations) > 1:
        JOptionPane.showMessageDialog(None, "Selecciona solo una relación.")
    else:
        relation = selected_relations[0]
        new_members = []

        # ==== BLOQUE NUEVO: descarga masiva desde Overpass ====
        try:
            import urllib
            from java.net import URL
            from java.io import ByteArrayInputStream
            from org.openstreetmap.josm.io import OsmReader

            # Construir consulta Overpass
            query = '[out:xml][timeout:25];('
            for wid in way_ids:
                query += 'way(' + str(wid) + ');'
            query += ');(._;>;);out meta;'

            encoded_query = urllib.quote(query, safe='')
            overpass_url = 'https://overpass-api.de/api/interpreter?data=' + encoded_query
            input_stream = URL(overpass_url).openStream()
            downloaded_data = OsmReader.parseDataSet(input_stream, None)
            edit_layer.mergeFrom(downloaded_data)
        except Exception as e:
            JOptionPane.showMessageDialog(None, "❌ Error al descargar las vías desde Overpass:\n{}".format(str(e)))
        # ==== FIN BLOQUE NUEVO ====

        # Buscar las vías descargadas dentro de la capa
        for wid in way_ids:
            way = None
            for primitive in edit_layer.allPrimitives():
                if isinstance(primitive, Way) and primitive.getId() == wid:
                    way = primitive
                    break
            if way:
                new_members.append(RelationMember("", way))

        if new_members:
            relation.setMembers(new_members)
            count = len(new_members)
            traza_memoria.way_ids = []
            JOptionPane.showMessageDialog(
                None,
                "Relacion {} actualizada con {} miembros.\n\n"
                "ATENCION:\n"
                "Todos los miembros anteriores fueron reemplazados.\n"
                "Revisa la relacion en el mapa para asegurarte de que no haya interrupciones o errores antes de subir los cambios.".format(relation.getUniqueId(), len(new_members))
            )
        else:
            JOptionPane.showMessageDialog(None, "No se pudieron agregar miembros a la relación.")

# === MODO inválido ===
else:
    count = len(traza_memoria.way_ids)
    JOptionPane.showMessageDialog(None, "Modo no válido.\nSelecciona solo Ways para Valhalla o solo una relación.\nVías en memoria: {}".format(count))