:: test bat file

:: NOTE:
:: To run from the anaconda command line regardless of the current directory
:: (required to have the cd flag use the current directory as the source)
:: Add the image_sorter directory to the path variable for both the User and
:: System (search for "edit env" in the windows start menu)
@echo off

call conda deactivate
call conda activate viewer

::Check if inputs are provided and insert dummy variables if not provided
if "%~1"=="" (SET in1=empty) else (SET in1=%1%)
if "%~2"=="" (SET in2=empty) else (SET in2=%2%)
if "%~3"=="" (SET in3=empty) else (SET in3=%3%)
if "%~4"=="" (SET in4=empty) else (SET in4=%4%)

:: Set the source and destination directories to "none"
set d_dir=None
set s_dir=None

:: Check for source or destination directories in the first input pair
if %in1%==ddir (set d_dir=%in2%)
if %in1%==sdir (set s_dir=%in2%)
:: Check for source or destination directories in the second input pair
if %in2%==ddir (set d_dir=%in3%)
if %in2%==sdir (set s_dir=%in3%)
:: Check for source or destination directories in the third input pair
if %in3%==ddir (set d_dir=%in4%)
if %in3%==sdir (set s_dir=%in4%)

:: if any of the inputs are "cur-dir" set the source to the current directory
if %in1%==cd (set s_dir=%CD%)
if %in2%==cd (set s_dir=%CD%)
if %in3%==cd (set s_dir=%CD%)
if %in4%==cd (set s_dir=%CD%)

set d_dir=%d_dir:"=%
set s_dir=%s_dir:"=%

:: Run the image sorter script
call python %~dp0img_sorter.py -s_dir "%s_dir%" -d_dir "%d_dir%"

