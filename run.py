if __name__ == "__main__":
    from config import ROOT
    from modules.win import Independent_Process

    main_path = ROOT + "\\main.py"
    headless_cmd = [
        "powershell.exe",
        "Start-Process",
        "-FilePath",
        "python",
        "-Args",
        f'"{main_path}"',
        "-WindowStyle",
        "Hidden",
    ]
    main_process = Independent_Process(headless_cmd)
