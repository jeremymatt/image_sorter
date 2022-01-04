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


echo in1: %in1%
echo in2: %in2%
echo in3: %in3%
echo in4: %in4%


if %in1%==-help (set in1=-h)

if %in1%==-h (
	echo Help file
	echo      noflags Run with the default settings specified in
	echo              the settings.py file
	echo      -h      This help menu
	echo      -fdir   The absolute path to the directory to be
	echo              backed up
	echo              NOTE: "C:\\" to back up entire C drive
	echo      -tdir   The absolute path to the directory where the
	echo              backup will be saved
	echo              NOTE: "T:\\" to back up to the T drive
	echo      -cd     Backup the current directory to the location 
	echo              specified in the .bkup_settings file
)

set f_dir=None
set t_dir=None

:: echo .
:: echo before set dirs
:: echo from dir %f_dir%
:: echo to dir %t_dir%

:: Check for source or destination directories in the first input pair
if %in1%==-fdir (set f_dir=%in2%)
if %in1%==-tdir (set t_dir=%in2%)
:: Check for source or destination directories in the second input pair
:: if %in2%==-fdir (echo ERROR: invalid entry in second input)
:: if %in2%==-tdir (echo ERROR: invalid entry in second input)
:: Check for source or destination directories in the third input pair
if %in3%==-fdir (set f_dir=%in4%)
if %in3%==-tdir (set t_dir=%in4%)

:: echo .
:: echo after set dirs
:: echo from dir %f_dir%
:: echo to dir %t_dir%

:: if any of the inputs are "cur-dir" set the source to the current directory
if %in1%==-cd (set f_dir=%CD%)
if %in1%==-cd (set t_dir=CD)


:: echo .
:: echo after CD
:: echo from dir %f_dir%
:: echo to dir %t_dir%


:: Strip off quotes if user passes in path within double quotes
set f_dir=%f_dir:"=%
set t_dir=%t_dir:"=%
:: Strip off quotes if user passes in path within double quotes
set f_dir=%f_dir:'=%
set t_dir=%t_dir:'=%

:: echo .
:: echo after quote strip
:: echo from dir %f_dir%
:: echo to dir %t_dir%

:: Confirm correct formating for drive to drive
:: backup on windows
if "%f_dir:~-2%"==":\" (set f_dir=%f_dir%\)
if "%f_dir:~-1%"==":" (set f_dir=%f_dir%\\)
if "%t_dir:~-2%"==":\" (set t_dir=%t_dir%\)
if "%t_dir:~-1%"==":" (set t_dir=%t_dir%\\)


:: echo .
:: echo after check for missing \
:: echo from dir %f_dir%
:: echo to dir %t_dir%

:: Run the image sorter script.  %~dp0 is the absolute path to the directory
:: containing the batch file
if %in1% NEQ -h (call python %~dp0driver_backup.py -f_dir "%f_dir%" -t_dir "%t_dir%")

