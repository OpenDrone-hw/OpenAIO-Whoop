#!/usr/bin/env python3
"""Autoroute a board with Freerouting, headless, on top of the existing routing.

    $KPY hardware/tools/freeroute.py hardware/OpenAIO-Whoop.kicad_pcb --jar freerouting-2.5.0.jar
                                     [--passes 20] [--threads 1] [--timeout 1800]
                                     [--rip-up | --strip-layers In2.Cu,In3.Cu] [--no-protect]
                                     [--planes In1.Cu,In4.Cu]
                                     [--keep-files DIR] [--no-drc]

Runs under KiCad's Python (KPY, see AGENTS.md). Get the jar from
https://github.com/freerouting/freerouting/releases (2.5 needs Java 25, 2.1-2.3
run on Java 21; the newest JVM in /usr/lib/jvm is used). Close KiCad first.

What it does, and why each step exists (verified on KiCad 10.0.6 + Freerouting 2.5.0):
  1. Inner layers that carry a zone (or --planes) are marked "power" for the
     export only, so Freerouting keeps signals off the planes. Without this it
     routes through them: KiCad exports zones as planes but the layer as signal.
  2. pcbnew.ExportSpecctraDSN. KiCad writes every existing track and via as
     (type route), locked or not; they are rewritten to (type protect) so hand
     routing (power, fan-out) is kept and only the missing connections are
     routed. --no-protect lets the router move them; --rip-up deletes all
     tracks and vias first; --strip-layers deletes the tracks on those layers
     (re-route the inner signal layers, keep fan-out and power).
  3. Freerouting with --router.hole_clearance_um set from Board Setup: the DSN
     has no hole-to-copper rule, so without it vias break KiCad's hole clearance.
  4. pcbnew.ImportSpecctraSES onto a fresh load of the board. The import
     replaces all tracks and vias with the session wiring (which includes the
     protected items).
  5. Tracks Freerouting necked down below their netclass width are widened
     back (it does this between fine-pitch pads even with neck-down off), zones
     are refilled, the board is saved and DRC runs with schematic parity.

Freerouting rounds coordinates to 1 um, so pads at sub-micron positions get
tiny joining stubs; harmless for DRC. Its result depends on item order: the
same toy geometry routed completely in one DSN and stalled at 2 unrouted in
another (only the footprint order differed). Scripted fan-out plus
--strip-layers is the dependable mode; full --rip-up is a gamble. Exit 0 when DRC has no errors and nothing
is unrouted, 1 otherwise.
"""
import argparse
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcb_build as pb  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("--jar", required=True, help="freerouting-X.Y.Z.jar")
    ap.add_argument("--passes", type=int, default=20)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=1800, help="seconds")
    ap.add_argument("--rip-up", action="store_true", help="delete all tracks and vias first")
    ap.add_argument("--strip-layers", help="comma-separated layers whose tracks are deleted first")
    ap.add_argument("--no-protect", action="store_true", help="let the router move existing routing")
    ap.add_argument("--planes", help="comma-separated plane layers (default: inner layers with zones)")
    ap.add_argument("--keep-files", metavar="DIR", help="keep the .dsn/.ses/log here")
    ap.add_argument("--no-drc", action="store_true")
    a = ap.parse_args(argv)
    board = os.path.abspath(a.board)
    work = a.keep_files or tempfile.mkdtemp(prefix="freeroute_")
    os.makedirs(work, exist_ok=True)
    base = os.path.join(work, os.path.splitext(os.path.basename(board))[0])
    dsn, ses = base + ".dsn", base + ".ses"

    t0 = time.time()
    brd = pb.Board(board)
    strip = {brd.layer(n.strip()) for n in (a.strip_layers or "").split(",") if n.strip()}

    def strip_tracks(b):
        if a.rip_up:
            b.clear_tracks()
        for tr in list(b.b.GetTracks()):
            if tr.GetClass() == "PCB_TRACK" and tr.GetLayer() in strip:
                b.b.Delete(tr)
    strip_tracks(brd)
    outer = {brd.layer("F.Cu"), brd.layer("B.Cu")}
    if a.planes:
        planes = [p.strip() for p in a.planes.split(",") if p.strip()]
    else:
        planes = sorted({brd.b.GetLayerName(l) for z in brd.b.Zones()
                         for l in z.GetLayerSet().CuStack() if l not in outer})
    for name in planes:
        brd.set_layer_type(name, "power")
    before = brd.unrouted()
    brd.export_dsn(dsn, protect_existing=not a.no_protect)
    print("exported %s (planes: %s, %d unrouted)" % (dsn, ", ".join(planes) or "none", before))

    t1 = time.time()
    r = pb.freeroute(a.jar, dsn, ses, passes=a.passes, timeout=a.timeout, threads=a.threads,
                     hole_clearance=pb.P.ToMM(brd.ds.m_HoleClearance))
    with open(base + ".log", "w") as f:
        f.write(" ".join(r.args) + "\n" + r.stdout + r.stderr)
    t2 = time.time()
    print("freerouting %.1fs (log %s.log)" % (t2 - t1, base))

    out = pb.Board(board)                 # fresh load: the layer-type change is not saved
    strip_tracks(out)
    out.import_ses(ses)
    widened = out.enforce_min_width()
    out.fill_zones()
    out.save()
    left = out.unrouted()
    print("imported SES, widened %d necked-down tracks, %d unrouted, %.1fs total" % (widened, left, time.time() - t0))
    if not a.keep_files:
        shutil.rmtree(work, ignore_errors=True)
    if a.no_drc:
        return 0 if left == 0 else 1
    d = pb.drc(board)
    print("DRC: %d errors, %d warnings, %d unconnected, %d parity" % (d["errors"], d["warnings"], d["unconnected"], d["parity"]))
    for k, n in sorted(d["by_type"].items()):
        print("    %-8s %-28s %d" % (k[0], k[1], n))
    return 0 if left == 0 and d["errors"] == 0 and d["unconnected"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
