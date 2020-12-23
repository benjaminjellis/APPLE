import os

if os.system("echo ${}".format("GCP_PROJECT")):
    print("On cloud")
else:
    print("local")