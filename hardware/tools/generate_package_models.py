#!/usr/bin/env python3
"""Generate the simplified FXMAR2104 UMLP package model using OCP.

This is an envelope/contact model, not manufacturer internal geometry.
Dimensions: onsemi FXMAR2104 Rev. 1.0.1, p14, MKT-UMLP12Arev4:
https://www.onsemi.com/download/data-sheet/pdf/fxmar2104-d.pdf
Body 1.8 x 1.8 mm; model height 0.50 mm (drawing maximum 0.55 mm),
0.05 mm standoff, nominal 0.40 x 0.20 mm terminals at 0.40 mm pitch.
Contact height 0.152 mm. Pin 1 uses the drawing's 0.10 mm corner cut.
The 12 contacts follow the footprint's 4/2/4/2 edge arrangement. Model Y
is up; schematic/footprint Y is down. STEP and WRL share this geometry.

Run: python3 hardware/tools/generate_package_models.py
Dependency: cadquery-ocp (OCP bindings); no CAD GUI is required.
"""

from pathlib import Path
import math

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCP.gp import gp_Pnt, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen


OUTPUT = Path(__file__).resolve().parents[1] / "lib.3dshapes"
NAME = "FXMAR2104_UMLP12_1.8x1.8x0.5_Simplified"


def rectangle(x, y, width, height):
    return [(x - width / 2, y - height / 2),
            (x + width / 2, y - height / 2),
            (x + width / 2, y + height / 2),
            (x - width / 2, y + height / 2)]


def prism(points, z, height):
    wire = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        wire.Add(gp_Pnt(x, y, z))
    wire.Close()
    return BRepPrimAPI_MakePrism(
        BRepBuilderAPI_MakeFace(wire.Wire()).Face(), gp_Vec(0, 0, height)
    ).Shape()


def wrl_prism(points, z, height, rgb):
    """KiCad VRML models use 0.1-inch units; source dimensions are mm."""
    count = len(points)
    vertices = [(x / 2.54, y / 2.54, zz / 2.54)
                for zz in (z, z + height) for x, y in points]
    faces = [list(reversed(range(count))), list(range(count, count * 2))]
    faces.extend([[i, (i + 1) % count, (i + 1) % count + count, i + count]
                  for i in range(count)])
    coordinates = ",\n".join(" ".join(f"{v:.9g}" for v in xyz) for xyz in vertices)
    indices = ",\n".join(" ".join(map(str, face)) + " -1" for face in faces)
    return ("Shape { appearance Appearance { material Material { diffuseColor "
            + " ".join(map(str, rgb))
            + " } } geometry IndexedFaceSet { solid TRUE coord Coordinate { point [\n"
            + coordinates + "\n] } coordIndex [\n" + indices + "\n] } }\n")


def main():
    # Pin numbering follows top-through view. Inner pin-1 corner is chamfered.
    contacts = [
        [(-0.9, 0.1), (-0.5, 0.1), (-0.5, 0.2), (-0.6, 0.3), (-0.9, 0.3)],
        rectangle(-0.7, -0.2, 0.4, 0.2),
        *[rectangle(x, -0.7, 0.2, 0.4) for x in (-0.6, -0.2, 0.2, 0.6)],
        rectangle(0.7, -0.2, 0.4, 0.2),
        rectangle(0.7, 0.2, 0.4, 0.2),
        *[rectangle(x, 0.7, 0.2, 0.4) for x in (0.6, 0.2, -0.2, -0.6)],
    ]
    body_polygon = rectangle(0, 0, 1.8, 1.8)
    body = BRepPrimAPI_MakeBox(gp_Pnt(-0.9, -0.9, 0.05), 1.8, 1.8, 0.45).Shape()
    metal_shapes = [prism(points, 0, 0.152) for points in contacts]
    for metal in metal_shapes:
        body = BRepAlgoAPI_Cut(body, metal).Shape()
    marker = [(-0.64 + 0.065 * math.cos(i * math.tau / 24),
               0.64 + 0.065 * math.sin(i * math.tau / 24)) for i in range(24)]
    marker_shape = prism(marker, 0.496, 0.004)
    body = BRepAlgoAPI_Cut(body, marker_shape).Shape()
    parts = [("Simplified mould envelope", body, (0.12, 0.12, 0.13))]
    parts.extend((f"Terminal {i + 1}", shape, (0.72, 0.73, 0.74))
                 for i, shape in enumerate(metal_shapes))
    parts.append(("Pin 1 identification", marker_shape, (0.72, 0.72, 0.72)))

    document = TDocStd_Document(TCollection_ExtendedString(NAME))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(document.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(document.Main())
    for name, shape, rgb in parts:
        label = shapes.AddShape(shape, False)
        TDataStd_Name.Set_s(label, TCollection_ExtendedString(name))
        colors.SetColor(label, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorGen)
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    assert writer.Transfer(document, STEPControl_AsIs)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert writer.Write(str(OUTPUT / (NAME + ".step"))) == IFSelect_RetDone

    # The visual WRL has embedded contact overlap; the STEP solids are disjoint.
    vrml = "#VRML V2.0 utf8\n# Simplified envelope/contact model; regenerate with generate_package_models.py\n"
    vrml += wrl_prism(body_polygon, 0.05, 0.45, parts[0][2])
    for points in contacts:
        vrml += wrl_prism(points, 0, 0.152, (0.72, 0.73, 0.74))
    vrml += wrl_prism(marker, 0.496, 0.004, (0.72, 0.72, 0.72))
    (OUTPUT / (NAME + ".wrl")).write_text(vrml)
    print(OUTPUT / (NAME + ".step"))


if __name__ == "__main__":
    main()
