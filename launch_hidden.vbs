' launch_hidden.vbs
' Double-click this file to start the CDR Dashboard with NO visible CMD window.
' Also used by Task Scheduler for auto-start on server boot.

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\CDR_Dashboard\start_cdr_dashboard.bat", 0, False
Set WshShell = Nothing
