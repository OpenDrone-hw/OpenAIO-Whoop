import sys, json
sys.argv=['x']
exec(open('/tmp/claude-0/-home-user/84218be5-e7e2-573d-8ce2-dce426a96e71/scratchpad/bomred/integ/integrate.py').read().split("if __name__")[0])
ORDER=[("BR-01 RV-4",BR_RV4),("BR-02 V2",BR_V2),("BR-03 V1",BR_V1),("BR-04 F1",BR_F1),("BR-05 PE-7",BR_PE7),
 ("BR-06 PS-08",BR_PS08),("BR-07 PS-05",BR_PS05),("BR-08 F2",BR_F2),("BR-09 GYRO",BR_GYRO),("BR-10 PE-1",BR_PE1),
 ("BR-11 PS-10",BR_PE3),("BR-12 PS-11",BR_PS11),("BR-13 PS-07",BR_PS07),("BR-14 PS-18",BR_PS18),("BR-15 V4",BR_V4),
 ("BR-16 V3",BR_V3),("BR-17 V5",BR_V5),("BR-18 PS-01",BR_PS01),("BR-19 PS-02",BR_PS02),("BR-20 PS-03",BR_PS03),
 ("BR-21 PS-17",BR_PS17),("BR-22 PS-15",lambda s:o4en(s,"PS-15")),("BR-23 PS-13",lambda s:fb(s,"47k/6.2k")),
 ("BR-24 PE-10",lambda s:r11(s,"2.4k")),("BR-25 RV-1",BR_RV1),("BR-26 PS-19",BR_PS19)]
s=S(base()); corrected(s); prev=s.stats(); c0=prev
for n,f in ORDER:
    t=S(base()); corrected(t); a=t.stats(); f(t); sa=delta(a,t.stats())
    f(s); cur=s.stats(); d=delta(prev,cur)
    print(f"{n:12s} parts {d['parts']:+3d} lines_inset {d['lines']:+d} lines_alone {sa['lines']:+d} haloF {d['halo_F']:+6.2f} haloB {d['halo_B']:+6.2f} pkgF {d['pkg_F']:+6.2f} pkgB {d['pkg_B']:+6.2f}")
    prev=cur
print(fmt(cur)); print(delta(c0,cur))
