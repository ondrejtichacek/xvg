
from xvg import read_xvg


print(read_xvg("f0.xvg"))
print(read_xvg("f0.xvg", ("Time (ps)",)))
print(read_xvg("f0.xvg", ["Angle (degrees)"]))

print(read_xvg("f1.xvg"))
print(read_xvg("f1.xvg", ("Structure",)))
print(read_xvg("f1.xvg", ["Coil", "B-Sheet", "Time (ps)"]))

print(read_xvg("f2.xvg"))
print(read_xvg("f2.xvg", ["res0_ACE"]))
print(read_xvg("f2.xvg", ("res0_ACE", "Time (ps)", "res2_TRP",)))
print(read_xvg("f2.xvg", ["res0_ACE", "Time (ps)", "res2_TRP", "res1_ALA"]))
