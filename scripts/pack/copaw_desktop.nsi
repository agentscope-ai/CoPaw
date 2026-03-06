; CoPaw Desktop NSIS installer. Run makensis from repo root after
; building dist/win-unpacked (see scripts/pack/build_win.ps1).
; Usage: makensis /DCOPAW_VERSION=1.2.3 /DOUTPUT_EXE=dist\CoPaw-Setup-1.2.3.exe scripts\pack\copaw_desktop.nsi

!include "MUI2.nsh"
!define MUI_ABORTWARNING
; Leave MUI_ICON/MUI_UNICON undefined to use NSIS default (no custom icon).

!ifndef COPAW_VERSION
  !define COPAW_VERSION "0.0.0"
!endif
!ifndef OUTPUT_EXE
  !define OUTPUT_EXE "dist\CoPaw-Setup-${COPAW_VERSION}.exe"
!endif

Name "CoPaw Desktop"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\CoPaw"
InstallDirRegKey HKCU "Software\CoPaw" "InstallPath"
RequestExecutionLevel user

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

; Pass /DUNPACKED=full_path from build_win.ps1 so path works when cwd != repo root
!ifndef UNPACKED
  !define UNPACKED "dist\win-unpacked"
!endif

Section "CoPaw Desktop" SEC01
  SetOutPath "$INSTDIR"
  File /r /x "*.pyc" /x "__pycache__" "${UNPACKED}\*.*"
  WriteRegStr HKCU "Software\CoPaw" "InstallPath" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\CoPaw Desktop.lnk" "$INSTDIR\CoPaw Desktop.bat" "" \
    "$INSTDIR\CoPaw Desktop.bat" 0
  CreateShortcut "$DESKTOP\CoPaw Desktop.lnk" "$INSTDIR\CoPaw Desktop.bat" "" \
    "$INSTDIR\CoPaw Desktop.bat" 0
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\CoPaw Desktop.lnk"
  Delete "$DESKTOP\CoPaw Desktop.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\CoPaw"
SectionEnd
