
from xvg import read_xvg


print(read_xvg("f2.xvg"))
print(read_xvg("f2.xvg", ["res0_ACE"]))
print(read_xvg("f2.xvg", ["res0_ACE", "Time (ps)", "res2_TRP"]))
print(read_xvg("f2.xvg", ["res0_ACE", "Time (ps)", "res2_TRP", "res1_ALA"]))
