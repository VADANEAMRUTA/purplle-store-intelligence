@echo off
REM Wrapper batch file for evaluation scripts from project root.
cd /d %~dp0
python "%~dp0run_evaluation.py" %*
EXIT /B %ERRORLEVEL%
