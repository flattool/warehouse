import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

blp_compiler = sys.argv[1]
src_dir = Path(sys.argv[2])
out_dir = sys.argv[3]
ui_xml_in = sys.argv[4]
ui_xml_out = sys.argv[5]

try:
    blps = list(src_dir.rglob("*.blp"))
    subprocess.run(
        [blp_compiler, "batch-compile", out_dir, src_dir]
        + [str(file.absolute()) for file in blps],
        check=True,
    )

    ui_xml = ET.parse(ui_xml_in)
    ui_resource = ui_xml.getroot()[0]  # this is -> <gresource prefix="...">
    for blp in blps:
        ui_path = blp.relative_to(src_dir).with_suffix(".ui")
        element = ET.SubElement(ui_resource, "file")
        element.set("preprocess", "xml-stripblanks")
        element.text = str(ui_path).replace("\\\\", "/")

    ET.indent(ui_xml, space="\t")
    ui_xml.write(ui_xml_out, encoding="utf-8", xml_declaration=True)
except Exception as e:
    print("ERROR Compiling Blueprints:", e)
    sys.exit(1)
