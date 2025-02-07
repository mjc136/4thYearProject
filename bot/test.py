import os

index_path = "index.html"
if os.path.exists(index_path):
    print("cum")
else:
    print("index.html not found")
