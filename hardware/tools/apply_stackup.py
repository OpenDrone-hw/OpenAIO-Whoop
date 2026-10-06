#!/usr/bin/env python3
"""Set a KiCad 10 board's physical stackup headless, without hand-editing the file.

    /opt/kicad-agent-venv/bin/python -I apply_stackup.py board.kicad_pcb spec.json

KiCad must not have the board open. Steps:
  1. pcbnew: set the copper layer count (and a provisional thickness), save.
  2. pcbnew: reload, set m_HasStackup so KiCad writes its default stackup for
     that layer count (layer names, types, order), save.
  3. kicad-skip: set the per-layer values from the spec on the structure KiCad wrote.
  4. pcbnew: reload (KiCad's parser validates), set the board thickness to the
     sum of the stackup, save (KiCad's writer normalises the file).
spec = {"copper_layers": 6, "copper_finish": "ENIG",
        "layers": {"F.Cu": {"thickness": 0.035},
                   "dielectric 1": {"type": "prepreg", "thickness": 0.0994,
                                    "material": "3313", "epsilon_r": 4.1, "loss_tangent": 0.02}, ...}}
Layer keys are the names KiCad writes: copper by canonical name, dielectrics "dielectric N".
"""
import json, os, sys


def quiet_import_pcbnew():
    saved, null = os.dup(2), os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 2)
    try:
        import pcbnew
        return pcbnew
    finally:
        os.dup2(saved, 2); os.close(saved); os.close(null)


def main(board, spec_path):
    spec = json.load(open(spec_path))
    pcbnew = quiet_import_pcbnew()
    import skip

    # 1. copper layer count
    b = pcbnew.LoadBoard(board)
    if "copper_layers" in spec and b.GetCopperLayerCount() != spec["copper_layers"]:
        b.SetCopperLayerCount(spec["copper_layers"])
    total = round(sum(v.get("thickness", 0) for v in spec["layers"].values()), 4)
    b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(total))
    assert pcbnew.SaveBoard(board, b)

    # 2. let KiCad write its default stackup structure for this layer count
    b = pcbnew.LoadBoard(board)
    b.GetDesignSettings().m_HasStackup = True
    assert pcbnew.SaveBoard(board, b)

    # 3. per-layer values with kicad-skip
    pcb = skip.PCB(board)
    st = pcb.setup.stackup
    by_name = {l.value: l for l in st.layer}
    missing = sorted(set(spec["layers"]) - set(by_name))
    if missing:
        sys.exit(f"KiCad's stackup has no layer(s) {missing}; check copper_layers / names")
    for name, fields in spec["layers"].items():
        for key, val in fields.items():
            node = getattr(by_name[name], key, None)
            if node is None:
                sys.exit(f"{name}: KiCad wrote no ({key} ...) for this layer type")
            node.value = val
    if "copper_finish" in spec:
        st.copper_finish.value = spec["copper_finish"]
    pcb.overwrite()

    # 4. KiCad reload + thickness from the stackup + save
    b = pcbnew.LoadBoard(board)
    if b is None:
        sys.exit("KiCad could not load the edited board")
    stack_sum = round(sum(float(l.thickness.value) for l in st.layer if getattr(l, "thickness", None) is not None), 4)
    b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(stack_sum))
    assert pcbnew.SaveBoard(board, b)
    print(f"stackup applied: {b.GetCopperLayerCount()} copper layers, {stack_sum} mm")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
