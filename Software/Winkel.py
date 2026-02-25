import math

yoff = 50
x1 = 40
y1 = 101
x2 = 68
y2 = 69
x1i = 274
y1i = 51
x2i = 298
y2i = 119
x1o = 30
y1o = 92
x2o = 64
y2o = 59
x1o1 = 280
y1o1 = 44
x2o1 = 299
y2o1 = 85
m = (y2-y1)/(x2-x1)
print(m)

# math.atan2(y, x) -> Reihenfolge ist y, dann x!
winkel_rad = math.atan2((y2-y1),(x2-x1))
winkel_deg = math.degrees(winkel_rad)
winkel = math.degrees(math.atan2((y2-y1),(x2-x1)))
winkelm = math.tan(winkel)
x=((yoff-y1)*(x2-x1)/(y2-y1))+x1
xi=((yoff-y1i)*(x2i-x1i)/(y2i-y1i))+x1i
xn=((xi-x)/2)+x
print(x, xi, xn)


xo=((yoff-y1o)*(x2o-x1o)/(y2o-y1o))+x1o
xo1=((yoff-y1o1)*(x2o1-x1o1)/(y2o1-y1o1))+x1o1
xon=((xo1-xo)/2)+xo

xfi=(xon+xn)/2
print(xo, xo1, xon, "Mittelwert", xfi)
#print(f"Winkel (Rad): {winkel_rad}")
#print(f"Winkel (Deg): {winkel_deg}") # Output: 45.0

#winkel_rad = math.atan2((y2-y1),(x2-x1))
#winkel_deg = math.degrees(winkel_rad)
#winkel = math.degrees(math.atan2((y2-y1),(x2-x1)))
#winkelm = math.tan(winkel)
r=50/(xfi-160)
winkel1 = math.degrees(math.atan2(yoff,(160-xfi)))
winkelkorr = 90-winkel1
print("Winkel", r , winkel1)

'''

'''