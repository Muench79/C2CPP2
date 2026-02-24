import math

y1 = 39
x1 = 262
x2 = 295
y2 = 81

m = (y2-y1)/(x2-x1)
print(m)

# math.atan2(y, x) -> Reihenfolge ist y, dann x!
winkel_rad = math.atan2((y2-y1),(x2-x1))
winkel_deg = math.degrees(winkel_rad)
winkel = math.degrees(math.atan2((y2-y1),(x2-x1)))
print(winkel)

#print(f"Winkel (Rad): {winkel_rad}")
print(f"Winkel (Deg): {winkel_deg}") # Output: 45.0
