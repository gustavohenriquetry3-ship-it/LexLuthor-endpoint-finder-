import tkinter as tk
from tkinter import filedialog, messagebox, ttk 
import requests
from requests.exceptions import RequestException
from threading import Thread
import sys 


DEFAULT_URL = "https://example.com"
DEFAULT_TIMEOUT = 10
DEFAULT_AGENT = '_GUI_Finder/1.0 (Lex TheGreat)'

class EndpointFinderApp:
    def __init__(self, master):
       
        self.master = master
        self.master.title("LexLuthor (endpoint finder 2.0)")

        
        self.url_var = tk.StringVar(value=DEFAULT_URL)
        self.wordlist_path_var = tk.StringVar()
        self.status_codes_var = tk.StringVar(value="200") 

        self.scan_active = False
        self.setup_widgets()

    def setup_widgets(self):
        
        config_frame = tk.Frame(self.master, padx=15, pady=15, bd=2, relief=tk.GROOVE)
        config_frame.pack(fill="x", pady=10)

       
        tk.Label(config_frame, text="URL Alvo:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.url_entry = tk.Entry(config_frame, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5)

       
        tk.Label(config_frame, text="Wordlist:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.wordlist_path_entry = tk.Entry(config_frame, textvariable=self.wordlist_path_var, width=50)
        self.wordlist_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.browse_button = tk.Button(config_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=1, column=2, padx=10, pady=5)

       
        tk.Label(config_frame, text="Status Ativo:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        tk.Label(config_frame, text="200 OK (Foco Atual)").grid(row=2, column=1, sticky="w", padx=10, pady=5)

       
        self.find_button = tk.Button(config_frame, text="INICIAR SCANNER", command=self.start_scan_thread, bg="#4CAF50", fg="white", font=('Arial', 10, 'bold'))
        self.find_button.grid(row=3, column=0, columnspan=3, pady=20)

       
        tk.Label(self.master, text="Progresso do Scan:", font=('Arial', 10, 'bold')).pack(padx=15, anchor="w")
        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=850, mode="determinate")
        self.progress_bar.pack(padx=15, fill="x", pady=5)

       
        tk.Label(self.master, text=">>> RESULTADOS ENCONTRADOS (Endpoints Ativos) <<<", font=('Arial', 12, 'bold')).pack(padx=15, anchor="w")
        self.results_text = tk.Text(self.master, wrap=tk.WORD, height=20, font=('Consolas', 10), padx=10, pady=10)
        self.results_text.pack(padx=15, pady=10, fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.master, command=self.results_text.yview)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o Arquivo Wordlist (.txt)",
            filetypes=(("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*"))
        )
        if file_path:
            self.wordlist_path_var.set(file_path)

    def load_wordlist(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            return words
        except FileNotFoundError:
            messagebox.showerror("Erro de Arquivo", "Wordlist não encontrada. Verifique o caminho!")
            return []
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Erro ao ler o arquivo: {e}")
            return []

    def run_scanner(self, url, wordlist):
        results = []
        total_items = len(wordlist)

        for idx, word in enumerate(wordlist, start=1):
            path = word.strip('/')
            full_url = f"{url.rstrip('/')}/{path}"

            try:
                headers = {'User-Agent': DEFAULT_AGENT}
                response = requests.get(full_url, headers=headers, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
                
                if response.status_code == 200:
                    length = len(response.content)
                    results.append(f"[200 OK] {full_url} | Tamanho: {length} bytes")

            except RequestException:
                pass

            
            progress_percent = (idx / total_items) * 100
            self.master.after(0, lambda p=progress_percent: self._update_progress(p))

        return results

    def _update_progress(self, percent):
        self.progress_bar['value'] = percent

    def start_scan_thread(self):
        if self.scan_active:
            messagebox.showwarning("Aviso", "O scanner já está rodando!")
            return

        url = self.url_var.get().strip()
        wordlist_path = self.wordlist_path_var.get().strip()

        if not url:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira a URL Alvo.")
            return

        if not wordlist_path:
            messagebox.showwarning("Entrada Inválida", "Por favor, selecione o arquivo Wordlist.")
            return

        self.scan_active = True
        self.find_button.config(state=tk.DISABLED, text="SCANNING...")
        self.results_text.delete("1.0", tk.END) 
        self.progress_bar['value'] = 0

        scanner_thread = Thread(target=self._scan_worker, args=(url, wordlist_path))
        scanner_thread.daemon = True
        scanner_thread.start()

    def _scan_worker(self, url, wordlist_path):
        wordlist = self.load_wordlist(wordlist_path)
        if not wordlist:
            
            self.master.after(0, self.reset_ui_after_scan)
            return

        results = self.run_scanner(url, wordlist)
        self.master.after(0, lambda: self.update_ui_after_scan(results))

    def update_ui_after_scan(self, results):
        output_text = "\n" + "="*70 + "\n"
        output_text += ">>> ENDPOINTS ENCONTRADOS (STATUS 200 OK) <<<\n"
        output_text += "="*70 + "\n"
        if results:
            for res in results:
                output_text += res + "\n"
        else:
            output_text += "Nenhum endpoint ativo (200 OK) foi encontrado após o scan completo.\n"

        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, output_text)
        self.reset_ui_after_scan()

    def reset_ui_after_scan(self):
        self.scan_active = False
        self.find_button.config(state=tk.NORMAL, text="INICIAR SCANNER")


if __name__ == "__main__":
    try:
        
        root = tk.Tk()
        
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        app = EndpointFinderApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] Aplicativo fechado pelo usuário.")
    except Exception as e:
        print(f"\n[!!! ERRO FATAL NA GUI] Ocorreu um erro ao iniciar o programa: {e}")
        sys.exit(1)
