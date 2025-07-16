import urllib
import urllib2
import json
import traceback
import os

from javax.swing import JOptionPane
from org.openstreetmap.josm.gui import MainApplication
from org.openstreetmap.josm.data.osm import Way
from org.openstreetmap.josm.gui.layer import GpxLayer
from org.openstreetmap.josm.data.gpx import GpxData, GpxTrack, GpxTrackSegment, WayPoint
from java.util import HashMap, ArrayList
from java.io import File

# Determinar la carpeta de salida según el sistema operativo
if os.name == "nt":
    base_dir = os.getenv("TEMP")
else:
    base_dir = os.path.expanduser("~")

output_file = os.path.join(base_dir, "rel.osm")
log_file = os.path.join(base_dir, "valhalla_log")

try:
    # Obtener la capa de edición activa
    layer_manager = MainApplication.getLayerManager()
    edit_layer_obj = layer_manager.getEditLayer()
    if edit_layer_obj is None:
        JOptionPane.showMessageDialog(None, "No hay capa activa de edición.")
    else:
        dataset = edit_layer_obj.data
        selection = dataset.getSelected()
        selected_ways = [primitive for primitive in selection if isinstance(primitive, Way)]

        if not selected_ways:
            JOptionPane.showMessageDialog(None, "Debes seleccionar al menos una línea en JOSM.")
        else:
            points = []
            for way in selected_ways:
                points.extend([{ "lat": node.getCoor().lat(), "lon": node.getCoor().lon() } for node in way.getNodes()])

            if len(points) < 2:
                JOptionPane.showMessageDialog(None, "Las líneas seleccionadas no tienen suficientes puntos.")
            else:
                JOptionPane.showMessageDialog(None, "Se procesarán {} puntos.".format(len(points)))

                url = "http://valhalla1.openstreetmap.de/trace_attributes"
                request_data = {
                    "shape": points,
                    "costing": "auto",
                    "shape_match": "walk_or_snap"
                }

                data = json.dumps(request_data)
                headers = {"Content-Type": "application/json"}
                request = urllib2.Request(url, data, headers)

                try:
                    response = urllib2.urlopen(request)
                    result = json.loads(response.read())

                    raw_way_ids = [str(edge["way_id"]) for edge in result.get("edges", [])]
                    way_ids = []
                    for i, way_id in enumerate(raw_way_ids):
                        if i == 0 or way_id != raw_way_ids[i - 1]:
                            way_ids.append(way_id)

                    if not way_ids:
                        JOptionPane.showMessageDialog(None, "No se encontraron vías en la respuesta de Valhalla.")
                    else:
                        # Crear XML de la relación
                        relation_id = -1
                        osm_data = [
                            '<?xml version="1.0"?>',
                            '<osm version="0.6" generator="JOSM">',
                            '  <relation id="{}">'.format(relation_id),
                            '    <tag k="type" v="route"/>',
                            '    <tag k="route" v="bus"/>'
                        ]

                        for way_id in way_ids:
                            osm_data.append('    <member type="way" ref="{}" role=""/>'.format(way_id))

                        osm_data.append("  </relation>")
                        osm_data.append("</osm>")

                        with open(output_file, "w") as f:
                            f.write("\n".join(osm_data))

                        # Convertir la capa en GPX
                        gpx_data = GpxData()
                        all_segments = []

                        for way in dataset.getWays():
                            if way.isUsable():
                                wp_list = []
                                for node in way.getNodes():
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
                            gpx_layer = GpxLayer(gpx_data, "GPX desde Valhalla")

                            layer_manager.addLayer(gpx_layer)
                            layer_manager.setActiveLayer(gpx_layer)
                            layer_manager.removeLayer(edit_layer_obj)

                        JOptionPane.showMessageDialog(None, "Relación escrita en {}\nGPX creado.".format(output_file))

                except urllib2.HTTPError as e:
                    with open(log_file, "w") as log:
                        log.write("Error en la consulta a Valhalla: {}\n".format(e))
                    JOptionPane.showMessageDialog(None, "Error en la consulta a Valhalla. Revisa el log en {}".format(log_file))
                except urllib2.URLError as e:
                    with open(log_file, "w") as log:
                        log.write("Error de conexión: {}\n".format(e))
                    JOptionPane.showMessageDialog(None, "Error de conexión. Revisa el log en {}".format(log_file))
                except Exception as e:
                    with open(log_file, "w") as log:
                        log.write("Error inesperado: {}\n".format(traceback.format_exc()))
                    JOptionPane.showMessageDialog(None, "Error inesperado. Revisa el log en {}".format(log_file))
except Exception as e:
    with open(log_file, "w") as log:
        log.write("Error fuera del try principal: {}\n".format(traceback.format_exc()))
    JOptionPane.showMessageDialog(None, "Error inesperado. Revisa el log en {}".format(log_file))
