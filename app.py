import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from yt_dlp import YoutubeDL
import re

# Configuration du thème pour un design épuré et premium
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Téléchargeur Vidéo Pro")
        self.geometry("550x450")
        self.resizable(False, False)

        # Variables
        self.url_var = ctk.StringVar()
        self.format_var = ctk.StringVar(value="MP4")
        self.qualite_var = ctk.StringVar(value="Haute")
        self.folder_var = ctk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # Titre principal
        title_label = ctk.CTkLabel(self, text="YouTube Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 10))

        # Champ URL
        ctk.CTkLabel(self, text="Lien YouTube :").pack(anchor="w", padx=40)
        self.url_entry = ctk.CTkEntry(self, textvariable=self.url_var, width=470, placeholder_text="Collez le lien ici...")
        self.url_entry.pack(pady=(0, 15))

        # Options de format et qualité (sur la même ligne)
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=40, pady=5)

        ctk.CTkLabel(options_frame, text="Format :").pack(side="left")
        self.format_menu = ctk.CTkOptionMenu(options_frame, variable=self.format_var, values=["MP4", "MP3"], width=100)
        self.format_menu.pack(side="left", padx=(10, 30))

        ctk.CTkLabel(options_frame, text="Qualité :").pack(side="left")
        self.qualite_menu = ctk.CTkOptionMenu(options_frame, variable=self.qualite_var, values=["Haute", "Moyenne", "Basse"], width=100)
        self.qualite_menu.pack(side="left", padx=(10, 0))

        # Choix du dossier
        ctk.CTkLabel(self, text="Dossier de destination :").pack(anchor="w", padx=40, pady=(15, 0))
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(fill="x", padx=40)
        
        self.folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var, width=350)
        self.folder_entry.pack(side="left", pady=5)
        
        self.btn_browse = ctk.CTkButton(folder_frame, text="Parcourir", width=100, command=self.choisir_dossier)
        self.btn_browse.pack(side="right", pady=5)

        # Zone de progression
        self.progress_label = ctk.CTkLabel(self, text="Prêt", text_color="gray")
        self.progress_label.pack(pady=(20, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self, width=470)
        self.progress_bar.set(0)
        self.progress_bar.pack()

        # Bouton Télécharger
        self.btn_download = ctk.CTkButton(self, text="TÉLÉCHARGER", font=ctk.CTkFont(weight="bold"), height=40, command=self.lancer_telechargement)
        self.btn_download.pack(pady=30)

    def choisir_dossier(self):
        dossier = filedialog.askdirectory()
        if dossier:
            self.folder_var.set(dossier)

    def nettoyer_ansi(self, texte):
        """Enlève les codes de couleurs invisibles générés par yt-dlp dans la console"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', texte)

    def hook_progression(self, d):
        if d['status'] == 'downloading':
            p_str = self.nettoyer_ansi(d.get('_percent_str', '0%')).strip()
            speed = self.nettoyer_ansi(d.get('_speed_str', 'N/A')).strip()
            eta = self.nettoyer_ansi(d.get('_eta_str', 'N/A')).strip()

            try:
                percent = float(p_str.replace('%', '')) / 100.0
            except ValueError:
                percent = 0.0

            texte_status = f"Téléchargement : {p_str} | Vitesse : {speed} | Reste : {eta}"
            
            # Mise à jour sécurisée de l'interface depuis un thread secondaire
            self.after(0, self.mettre_a_jour_ui, percent, texte_status)

        elif d['status'] == 'finished':
            self.after(0, self.mettre_a_jour_ui, 1.0, "Téléchargement terminé ! Fusion audio/vidéo en cours...")

    def mettre_a_jour_ui(self, percent, texte):
        self.progress_bar.set(percent)
        self.progress_label.configure(text=texte)

    def lancer_telechargement(self):
        url = self.url_var.get().strip()
        dossier = self.folder_var.get()

        if not url or not dossier:
            messagebox.showerror("Erreur", "Veuillez entrer un lien et choisir un dossier.")
            return

        # Désactiver le bouton pendant le téléchargement
        self.btn_download.configure(state="disabled", text="En cours...")
        
        # Lancement dans un thread
        thread = threading.Thread(target=self.telecharger, args=(url, dossier))
        thread.start()

    def telecharger(self, url, dossier):
        fmt = self.format_var.get()
        qualite = self.qualite_var.get()

        ydl_opts = {
            'outtmpl': os.path.join(dossier, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook_progression],
            'noprogress': True,
            'quiet': True,
            'noplaylist': True, # Évite de télécharger toute une playlist par erreur
        }

        if fmt == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # On demande le meilleur format dispo selon la hauteur, sans forcer l'extension ici
            # yt-dlp s'occupera de convertir en mp4 grâce à 'merge_output_format'
            formats = {
                "Haute": 'bestvideo+bestaudio/best',
                "Moyenne": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                "Basse": 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            }
            ydl_opts.update({
                'format': formats[qualite],
                'merge_output_format': 'mp4', # Fusionne le tout en MP4 proprement
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self.fin_telechargement, "Succès", "Téléchargement terminé avec succès !")
        except Exception as e:
            # On nettoie l'erreur pour enlever les codes bizarres [0;31m
            message_erreur = self.nettoyer_ansi(str(e))
            self.after(0, self.fin_telechargement, "Erreur", f"Erreur de téléchargement :\n{message_erreur}")

    def fin_telechargement(self, titre, message):
        self.progress_label.configure(text=message)
        self.btn_download.configure(state="normal", text="TÉLÉCHARGER")
        self.progress_bar.set(0)
        if titre == "Succès":
            messagebox.showinfo(titre, message)
        else:
            messagebox.showerror(titre, message)

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()