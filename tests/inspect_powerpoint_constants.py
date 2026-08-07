import win32com.client

app = win32com.client.Dispatch("PowerPoint.Application")

print(type(app))

print("Application Version:", app.Version)

print("\nApplication object methods:")
for name in dir(app):
    if "Effect" in name or "Anim" in name or "Media" in name:
        print(name)

input("\nPress Enter...")