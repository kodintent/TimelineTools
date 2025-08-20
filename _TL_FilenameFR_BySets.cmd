@echo off 

setlocal

set ROOTSLASH=%~dp0
rem delete the slash from the end of the path, so it is passed cleanly.
set "ROOT=%ROOTSLASH:~0,-1%"
rem pass the parent of this .cmd script as the root dir, to the .py script.
python "%USERPROFILE%\CODE\TimelineTools\TL_FilenameFR_BySets.py" "%ROOT%"

endlocal

pause