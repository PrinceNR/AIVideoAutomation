import win32com.client

print("Opening PowerPoint...")

app = win32com.client.Dispatch("PowerPoint.Application")
app.Visible = True

print("PowerPoint opened successfully!")

input("Press Enter to close PowerPoint...")

app.Quit()

print("Done.")