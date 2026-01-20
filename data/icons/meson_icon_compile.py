import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ICON_PREFIX = "warehouse:"

icon_dir = Path(sys.argv[1])
icon_xml_in = sys.argv[2]
icon_xml_out = sys.argv[3]

try:
	icons = list(icon_dir.glob("*.svg"))
	icon_xml = ET.parse(icon_xml_in)
	icon_resouce = icon_xml.getroot()[0]  # this is -> <gresource prefix="...">
	for icon in icons:
		element = ET.SubElement(icon_resouce, "file")
		element.set("preprocess", "xml-stripblanks")
		element.set("alias", f"{ICON_PREFIX}{icon.name}")
		element.text = icon.name

	ET.indent(icon_xml, space="\t")
	icon_xml.write(icon_xml_out, encoding="utf-8", xml_declaration=True)
except Exception as e:
	print("ERROR Compiling Icons:", e)
	sys.exit(1)
