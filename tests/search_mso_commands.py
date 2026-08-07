import win32com.client


app = win32com.client.Dispatch("PowerPoint.Application")
app.Visible = True

candidate_commands = [
    "InsertAudio",
    "InsertAudioFromFile",
    "MediaInsertAudio",
    "AudioInsert",
    "InsertMedia",
    "Media",
    "InsertSound",
    "SoundInsert",
    "InsertOnlineAudio",
]

print("=" * 60)

for cmd in candidate_commands:

    try:
        app.CommandBars.ExecuteMso(cmd)
        print("SUCCESS:", cmd)

    except Exception as e:
        print("FAILED :", cmd)

print("=" * 60)

input("Press Enter...")