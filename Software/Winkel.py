import math

y1 = 113
x1 = 52
x2 = 105
y2 = 56

m = (y2-y1)/(x2-x1)
print(m)

# math.atan2(y, x) -> Reihenfolge ist y, dann x!
winkel_rad = math.atan2((y2-y1),(x2-x1))
winkel_deg = math.degrees(winkel_rad)
winkel = math.degrees(math.atan2((y2-y1),(x2-x1)))
winkelm = math.tan(winkel)
x=((100-y1)*(x2-x1)/(y2-y1))+x1
print(winkel, winkelm, x)

#print(f"Winkel (Rad): {winkel_rad}")
print(f"Winkel (Deg): {winkel_deg}") # Output: 45.0
