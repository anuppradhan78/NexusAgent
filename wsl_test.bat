@echo off
REM Run tests in WSL

echo ================================================================================
echo   Running Tests in WSL
echo ================================================================================
echo.

set "WSL_PATH=/mnt/c/Users/anupp/Documents/NexusAgent"

echo Running end-to-end tests...
echo.

wsl bash -c "cd '%WSL_PATH%' && source venv/bin/activate && pytest backend/test_e2e_query_flow.py -v -s"

echo.
echo ================================================================================
echo   Tests Complete!
echo ================================================================================
echo.

pause
