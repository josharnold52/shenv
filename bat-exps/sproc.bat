@ECHO OFF
FOR /F "eol=; tokens=1* delims=:" %%i in (sproc.cmds) do (
    IF X%%i==Xprint (
        echo %%j
    )
    IF X%%i==Xset (
        set %%j
    )
    IF X%%i==Xexec (
        cmd /c %%j
    )
)
