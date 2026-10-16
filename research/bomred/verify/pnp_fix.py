# Re-run of bomred/vfm/pnp.py with both signs of the base-current term.
# PNP: base current leaves the base and flows through Rb into the PWM source, so Vb = Vpwm + Ib*Rb.
import math
VDD=3.3; Rb=2000.0
def veb(ic): return 0.65+0.0595*math.log10(max(ic,1e-12)/1e-3)
def ic_of(D,Re,hfe,sign,vdd=VDD,Rb=Rb):
    vpwm=vdd*D; lo,hi=0.0,0.2
    for _ in range(200):
        ic=(lo+hi)/2; ib=ic/hfe; ie=ic+ib
        vb=vpwm+sign*ib*Rb
        if (vdd-ie*Re)-vb>veb(ic): lo=ic
        else: hi=ic
    return ic
cnts=(2000,2500,3000,3100,3200,3300,3400,3500,3600,3700)
for label,sign in (("report (vb=vpwm-ib*Rb)",-1),("corrected (vb=vpwm+ib*Rb)",+1)):
  print("==",label)
  for Re in (10.0,15.0,27.0,33.0):
    for hfe in (220,475):
      row=[f"{c}:{ic_of(c*1000//4096/1000,Re,hfe,sign)*1e3:5.1f}" for c in cnts]
      print(f"Re={Re:4.0f} hFE={hfe}: "+"  ".join(row))
  for Re in (27.0,):
    for hfe in (220,475):
      imax=ic_of(2000*1000//4096/1000,Re,hfe,sign)
      pts=[(c,ic_of(c*1000//4096/1000,Re,hfe,sign)) for c in range(2000,3701)]
      c90=max(c for c,i in pts if i>=0.9*imax); c10=max(c for c,i in pts if i>=0.1*imax)
      print(f"  Re={Re} hFE={hfe}: Ic(YOLO)={imax*1e3:.1f} mA, 90% at {c90}, 10% at {c10}")
# hFE spread at Re=27 for the YOLO ceiling
for sign in (-1,1):
  a=ic_of(2000*1000//4096/1000,27,220,sign); b=ic_of(2000*1000//4096/1000,27,475,sign)
  print("sign",sign,"YOLO spread 220..475: %.1f..%.1f mA (+/-%.0f%%)"%(b*1e3,a*1e3,100*(a-b)/(a+b)))
