invals = ["13/5", "2/1", "27/10", "29/20", "23/10", "5/1", "5/1"]

out = []

for x in invals:
    n, d = x.split("/")
    n, d = int(n), int(d)
    val = n/d + 1
    out.append(val)

print(out)

