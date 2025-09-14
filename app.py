import os
import sys
import requests
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk  # 背景画像表示のためにPillowを使用
import zipfile  # ZIP解凍のために使用
import winsound  # 警告音のために使用
import threading  # スレッド処理のために使用
import subprocess  # ParrotClient実行用


# 実行ファイルがPyInstallerでビルドされたかどうかのチェック
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # PyInstallerでビルドされた場合のリソースパス
else:
    base_path = os.path.abspath(".")  # 開発環境の場合のパス

# リソースファイルのパス設定（ここはそのまま）
background_image_path = os.path.join(base_path, "background.png")
icon_path = os.path.join(base_path, "yuzu.ico")

def finish_ui_update():
    progress_bar.place_forget()
    progress_text_label.place_forget()
    status_label.config(text="インストールが完了しました")
    install_button.config(state="normal", text="完了", command=finish_installation)
    cancel_button.config(state="disabled")  # キャンセルボタンを無効化
    run_checkbox.place(relx=0.55, rely=0.948, anchor="w")  # チェックボックスを表示


# 完了ボタンの動作
def finish_installation():
    if run_var.get():  # チェックボックスが選択されている場合
        minecraft_exe_path = r"C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe"
        if os.path.exists(minecraft_exe_path):
            subprocess.Popen([minecraft_exe_path])
        else:
            messagebox.showerror("エラー", "Minecraftの実行ファイルが見つかりません。パスを確認してください。")
    root.quit()

# キャンセル時に使うフラグ
cancel_flag = threading.Event()

# ダウンロード開始（スレッド化）
def start_download_thread():
    # スレッドを作成して開始
    download_thread = threading.Thread(target=start_download, daemon=True)
    download_thread.start()

# ダウンロード関数
def download_file(url, save_path, progress_var, status_label, progress_text_label, file_index, total_files):
    file_name = os.path.basename(save_path)
    status_label.config(text=f"{file_name} {file_index}/{total_files}")
    root.update_idletasks()

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('Content-Length', 0))
    with open(save_path, 'wb') as file:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=1024):
            if cancel_flag.is_set():  # キャンセルが要求されている場合
                status_label.config(text="ダウンロードがキャンセルされました。")
                return
            if chunk:
                file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress_percentage = (downloaded / total_size) * 100
                    progress_var.set(progress_percentage)
                    progress_text_label.config(
                        text=f"{int(downloaded / 1024 / 1024)}MB / {int(total_size / 1024 / 1024)}MB"
                    )
                root.update_idletasks()  # 更新を即座に反映

# ダウンロード開始処理
def start_download():
    try:
        install_button.config(state="disabled", text="インストール中...")
        progress_bar.place(relx=0.43, rely=0.5, anchor="center")
        progress_text_label.place(relx=0.0256, rely=0.984, anchor="w")

        save_dir = os.path.join(os.getenv("APPDATA"), ".minecraft", "versions", "parrot")
        downloads = [
            {
                "url": "https://github.com/yuzu-krs/ParrotClient-dlfile/raw/refs/heads/main/parrot.jar",
                "save_path": os.path.join(save_dir, "parrot.jar")
            },
            {
                "url": "https://raw.githubusercontent.com/yuzu-krs/ParrotClient-dlfile/main/parrot.json",
                "save_path": os.path.join(save_dir, "parrot.json")
            }
        ]
      

        progress_var.set(0)
        total_files = len(downloads)
        for i, download in enumerate(downloads, start=1):
            if cancel_flag.is_set():  # キャンセルチェック
                break
            os.makedirs(os.path.dirname(download["save_path"]), exist_ok=True)
            download_file(
                download["url"], download["save_path"],
                progress_var, status_label, progress_text_label, i, total_files
            )

        if not cancel_flag.is_set():
            root.after(0, finish_ui_update)
    except Exception as e:
        messagebox.showerror("エラー", f"エラーが発生しました: {e}")

# キャンセルボタンの処理
def cancel_download():
    winsound.MessageBeep(winsound.MB_ICONHAND)  # 警告音を鳴らす
    confirm = messagebox.askyesno("ParrotClient セットアップ", "ParrotClient セットアップを中止しますか？")
    if confirm:
        cancel_flag.set()  # キャンセルフラグをセット
        root.quit()  # GUIを閉じる

# GUI作成
root = tk.Tk()
root.title("ParrotClient セットアップ")
root.geometry("800x500")  # ウィンドウのサイズを800x500に変更
root.resizable(False, False)  # ウィンドウのリサイズを無効化

# アイコン設定（yuzu.icoをそのまま使う）
root.iconbitmap(icon_path)

# 背景画像の設定（background.pngをそのまま使う）
background_image = Image.open(background_image_path)
background_image = background_image.resize((800, 500), Image.Resampling.LANCZOS)
bg = ImageTk.PhotoImage(background_image)

canvas = tk.Canvas(root, width=800, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg, anchor="nw")

# ボタン用帯（下部に配置）
button_frame = tk.Frame(root, bg="#f0f0f0", bd=1)
button_frame.place(relx=0, rely=0.9, relwidth=1, relheight=0.1)

# 進行状況バー（初期状態では非表示）
progress_var = tk.DoubleVar()

progress_bar = ttk.Progressbar(button_frame, length=450, mode='determinate', variable=progress_var)

# 進行状況表示用ラベル（初期状態では非表示）
progress_text_label = tk.Label(root, text="", bg="#f0f0f0", font=("Arial", 7))
progress_text_label.place(relx=1, rely=0.98, anchor="e")

# キャンセルボタン
cancel_button = ttk.Button(button_frame, text="キャンセル", command=cancel_download)
cancel_button.pack(side="right", padx=10)

# インストールボタン
install_button = ttk.Button(button_frame, text="インストール", command=start_download_thread)
install_button.pack(side="right", padx=10)

# 実行するチェックボックス
run_var = tk.BooleanVar()
run_checkbox = ttk.Checkbutton(root, text="Minecraft Launcherを実行", variable=run_var)

status_label = tk.Label(button_frame, text="", bg="#f0f0f0", anchor="w", font=("Arial", 8))
status_label.pack(fill="x", padx=(20, 10), side="left")

root.mainloop()
