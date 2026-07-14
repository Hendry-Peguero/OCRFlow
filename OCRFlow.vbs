Dim fso, dir, py, script
Set fso = CreateObject("Scripting.FileSystemObject")
dir    = fso.GetParentFolderName(WScript.ScriptFullName)
py     = dir & "\.venv\Scripts\pythonw.exe"
script = dir & "\gui\app.py"

If Not fso.FileExists(py) Then
    MsgBox "No se encontro el entorno virtual." & vbCrLf & _
           "Ejecuta instalador.bat primero.", vbCritical, "OCRFlow"
    WScript.Quit 1
End If

Dim shell
Set shell = CreateObject("WScript.Shell")
shell.Run """" & py & """ """ & script & """", 1, False
