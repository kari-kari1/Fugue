; Custom uninstaller — kill backend sidecar before removing files
Section "Uninstall"
  ; Kill fugue-backend processes before removing files
  nsExec::ExecToLog 'taskkill /F /IM fugue-backend.exe'
  ; Also kill the main app process
  nsExec::ExecToLog 'taskkill /F /IM fugue.exe'
  ; Wait briefly for processes to exit
  Sleep 2000
  ; Now Tauri's default uninstall will clean up files
SectionEnd
