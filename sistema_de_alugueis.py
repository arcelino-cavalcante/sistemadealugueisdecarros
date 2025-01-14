import tkinter as tk
from tkinter import messagebox, simpledialog
import datetime
import json
import os

# Para o gráfico (matplotlib)
import matplotlib
matplotlib.use("Agg")  # caso queira rodar sem interface de backend
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker

# ---------------------------------------------------------------------------------------
# Funções auxiliares para lidar com datas (datetime <-> string ISO-8601)
# ---------------------------------------------------------------------------------------
def datetime_to_str(dt):
    return dt.isoformat() if dt else None

def str_to_datetime(s):
    return datetime.datetime.fromisoformat(s) if s else None

# ---------------------------------------------------------------------------------------
# Definições de fonte, cores e estilos (para Tkinter)
# ---------------------------------------------------------------------------------------
DEFAULT_FONT = ("Arial", 13)
BG_MAIN  = "#ECECEC"       # Fundo principal da janela
BG_FRAME = "#FFFFFF"       # Fundo dos frames
FG_TEXT  = "#333333"       # Cor do texto

# Botões pretos
BUTTON_BG   = "#000000"
BUTTON_FG   = "#FFFFFF"
BUTTON_STYLE = {
    "font":             DEFAULT_FONT,
    "bg":               BUTTON_BG,
    "fg":               BUTTON_FG,
    "activebackground": "#333333",
    "cursor":           "hand2"
}

ENTRY_STYLE = {
    "font":   DEFAULT_FONT,
    "fg":     FG_TEXT,
    "bg":     "#FFFFFF",
    "bd":     2,
    "relief": "solid"
}

# ---------------------------------------------------------------------------------------
# CarRentalSystem - Lógica principal
# ---------------------------------------------------------------------------------------
class CarRentalSystem:
    """
    Gerencia dados (usuários, veículos e aluguéis) em um arquivo JSON.
    """
    def __init__(self, json_file_path="data.json"):
        self.json_file_path = json_file_path
        self.users = []
        self.vehicles = []
        self.rentals = []
        self.current_user = None
        self.load_data()
        
        # Cria admin padrão se não existir
        if not any(u["role"] == "admin" for u in self.users):
            self.users.append({"username": "admin", "password": "admin", "role": "admin"})
            self.save_data()

    def load_data(self):
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.users = data.get("users", [])
            self.vehicles = data.get("vehicles", [])
            for r in data.get("rentals", []):
                self.rentals.append({
                    "rental_id":  r["rental_id"],
                    "vehicle_id": r["vehicle_id"],
                    "nome_cliente": r.get("nome_cliente", ""),
                    "user_alugou": r["user_alugou"],
                    "cpf":         r["cpf"],
                    "whatsapp":    r["whatsapp"],
                    "dias":        r["dias"],
                    "valor_por_dia": r["valor_por_dia"],
                    "valor_total":   r["valor_total"],
                    "data_retirada": str_to_datetime(r["data_retirada"]),
                    "data_devolucao_estimada": str_to_datetime(r["data_devolucao_estimada"]),
                    "data_devolucao_efetiva":  str_to_datetime(r["data_devolucao_efetiva"])
                })

    def save_data(self):
        data = {
            "users": self.users,
            "vehicles": self.vehicles,
            "rentals": []
        }
        for r in self.rentals:
            data["rentals"].append({
                "rental_id": r["rental_id"],
                "vehicle_id": r["vehicle_id"],
                "nome_cliente": r.get("nome_cliente", ""),
                "user_alugou": r["user_alugou"],
                "cpf": r["cpf"],
                "whatsapp": r["whatsapp"],
                "dias": r["dias"],
                "valor_por_dia": r["valor_por_dia"],
                "valor_total": r["valor_total"],
                "data_retirada": datetime_to_str(r["data_retirada"]),
                "data_devolucao_estimada": datetime_to_str(r["data_devolucao_estimada"]),
                "data_devolucao_efetiva":  datetime_to_str(r["data_devolucao_efetiva"])
            })
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def clear_data(self):
        """
        Apaga todos os dados e recria apenas o admin padrão (admin/admin).
        """
        self.users = []
        self.vehicles = []
        self.rentals = []
        # Recria admin
        self.users.append({"username": "admin", "password": "admin", "role": "admin"})
        self.save_data()

    # ------------------ Login / Logout ------------------
    def login(self, username, password):
        for user in self.users:
            if user["username"] == username and user["password"] == password:
                self.current_user = user
                return True
        return False

    def logout(self):
        self.current_user = None

    def get_current_user(self):
        return self.current_user

    def is_admin(self):
        return self.current_user and self.current_user.get("role") == "admin"

    # ------------------ Usuários ------------------
    def create_user(self, username, password, role):
        if not self.is_admin():
            return "Permissão negada. Somente admin pode criar usuários."
        if any(u["username"] == username for u in self.users):
            return "Usuário já existe!"
        if role not in ("admin", "padrao"):
            return "Tipo de usuário inválido! Use 'admin' ou 'padrao'."
        self.users.append({"username": username, "password": password, "role": role})
        self.save_data()
        return f"Usuário '{username}' criado com sucesso!"

    # ------------------ Veículos ------------------
    def register_vehicle(self, nome, marca, ano, placa):
        if not self.is_admin():
            return "Somente admin pode cadastrar veículos."
        if any(v["placa"].lower() == placa.lower() for v in self.vehicles):
            return "Já existe um veículo com essa placa!"
        self.vehicles.append({
            "id": len(self.vehicles) + 1,
            "nome": nome,
            "marca": marca,
            "ano": ano,
            "placa": placa,
            "disponivel": True
        })
        self.save_data()
        return f"Veículo '{nome}' cadastrado com sucesso!"

    def list_vehicles(self):
        return self.vehicles

    def modify_vehicle(self, vehicle_id, nome, marca, ano, placa):
        if not self.is_admin():
            return "Somente admin pode modificar veículos."
        for v in self.vehicles:
            if v["id"] == vehicle_id:
                if placa:
                    # Verifica placa duplicada
                    for other in self.vehicles:
                        if other["placa"].lower() == placa.lower() and other["id"] != vehicle_id:
                            return "Já existe outro veículo com essa placa!"
                if nome:  v["nome"]  = nome
                if marca: v["marca"] = marca
                if ano:   v["ano"]   = ano
                if placa: v["placa"] = placa
                self.save_data()
                return "Veículo modificado com sucesso!"
        return "Veículo não encontrado!"

    # ------------------ Aluguéis ------------------
    def rent_vehicle(self, vehicle_id, nome_cliente, cpf, whatsapp, dias, valor_por_dia):
        if not self.current_user:
            return "É necessário estar logado para alugar!"
        for v in self.vehicles:
            if v["id"] == vehicle_id:
                if not v["disponivel"]:
                    return "Veículo indisponível para aluguel."
                v["disponivel"] = False
                data_retirada = datetime.datetime.now()
                valor_total = dias * valor_por_dia
                self.rentals.append({
                    "rental_id": len(self.rentals) + 1,
                    "vehicle_id": v["id"],
                    "nome_cliente": nome_cliente,
                    "user_alugou": self.current_user["username"],
                    "cpf": cpf,
                    "whatsapp": whatsapp,
                    "dias": dias,
                    "valor_por_dia": valor_por_dia,
                    "valor_total": valor_total,
                    "data_retirada": data_retirada,
                    "data_devolucao_estimada": data_retirada + datetime.timedelta(days=dias),
                    "data_devolucao_efetiva": None
                })
                self.save_data()
                return (f"Aluguel realizado!\n"
                        f"Cliente: {nome_cliente}\n"
                        f"Carro: {v['nome']}\n"
                        f"Total: R$ {valor_total:.2f}\n"
                        f"Retirada: {data_retirada.strftime('%d/%m/%Y %H:%M')}\n"
                        f"Devolução Estimada: "
                        f"{(data_retirada + datetime.timedelta(days=dias)).strftime('%d/%m/%Y %H:%M')}")
        return "Veículo não encontrado!"

    def return_vehicle(self, rental_id):
        if not self.current_user:
            return "É necessário estar logado para devolver!"
        for r in self.rentals:
            if r["rental_id"] == rental_id and r["data_devolucao_efetiva"] is None:
                r["data_devolucao_efetiva"] = datetime.datetime.now()
                for v in self.vehicles:
                    if v["id"] == r["vehicle_id"]:
                        v["disponivel"] = True
                        break
                self.save_data()
                return (f"Devolução realizada!\nAluguel ID: {rental_id}\n"
                        f"Data/hora: {r['data_devolucao_efetiva'].strftime('%d/%m/%Y %H:%M')}")
        return "Aluguel não encontrado ou já devolvido!"

    def list_open_rentals(self):
        return [r for r in self.rentals if r["data_devolucao_efetiva"] is None]

    # ------------------ Estatísticas ------------------
    def list_rentals_last_7_days(self):
        agora = datetime.datetime.now()
        sete_dias_atras = agora - datetime.timedelta(days=7)
        rentals_7d = []
        for r in self.rentals:
            if r["data_retirada"] >= sete_dias_atras:
                status = "Em aberto" if r["data_devolucao_efetiva"] is None else "Devolvido"
                rentals_7d.append((r, status))
        return rentals_7d

    def list_rentals_current_week(self):
        agora = datetime.datetime.now()
        weekday = agora.weekday()  # seg=0, dom=6
        start_of_week = agora - datetime.timedelta(days=weekday)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)

        weekly_list = []
        for r in self.rentals:
            if start_of_week <= r["data_retirada"] <= end_of_week:
                status = "Em aberto" if r["data_devolucao_efetiva"] is None else "Devolvido"
                rentals_7d.append((r, status))
        return weekly_list

    def get_top_5_veiculos_mes(self):
        from collections import Counter
        agora = datetime.datetime.now()
        mes = agora.month
        ano = agora.year
        filtered = [r for r in self.rentals 
                    if r["data_retirada"].year == ano and r["data_retirada"].month == mes]
        contagens = Counter(r["vehicle_id"] for r in filtered)
        top5 = contagens.most_common(5)
        resultado = []
        for (vid, count) in top5:
            nome_veic = None
            for v in self.vehicles:
                if v["id"] == vid:
                    nome_veic = v["nome"]
                    break
            if nome_veic:
                resultado.append((nome_veic, count))
        return resultado

    def get_top_5_clientes_mes(self):
        from collections import Counter
        agora = datetime.datetime.now()
        mes = agora.month
        ano = agora.year
        filtered = [r for r in self.rentals 
                    if r["data_retirada"].year == ano and r["data_retirada"].month == mes]
        contagens = Counter(r["cpf"] for r in filtered)
        return contagens.most_common(5)

    def get_7days_faturamento(self):
        """
        Retorna (labels, values) para os últimos 7 dias,
        com labels no formato "DD/MM" e values = soma de valor_total do dia.
        """
        agora = datetime.datetime.now()
        datas = [(agora - datetime.timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                 for i in range(7)]
        datas.sort()

        daily_totals = {}
        for d in datas:
            key = d.date()
            daily_totals[key] = 0.0

        for r in self.rentals:
            data_r = r["data_retirada"].date()
            if data_r in daily_totals:
                daily_totals[data_r] += r["valor_total"]

        labels = []
        values = []
        for d in sorted(daily_totals.keys()):
            labels.append(d.strftime("%d/%m"))
            values.append(daily_totals[d])

        return (labels, values)

# ---------------------------------------------------------------------------------------
# Segunda Tela: VisaoGeralWindow
# ---------------------------------------------------------------------------------------
class VisaoGeralWindow(tk.Toplevel):
    """
    Exibe:
      - Aluguéis por Semana (Últimos 7 dias ou Semana Atual)
      - Top 5 Carros no Mês
      - Top 5 Clientes no Mês
      - Gráfico de Linhas (últimos 7 dias, sem y negativo)
    """
    def __init__(self, master, system, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master
        self.system = system
        self.title("Visão Geral - Estatísticas (Últimos 7 dias)")
        self.configure(bg=BG_MAIN)
        self.geometry("1000x700")

        container = tk.Frame(self, bg=BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # 2 linhas × 2 colunas
        for r in range(2):
            container.rowconfigure(r, weight=1, minsize=300)
        for c in range(2):
            container.columnconfigure(c, weight=1, minsize=450)

        # Frame Aluguéis por Semana
        frame_semana = tk.LabelFrame(container, text="Aluguéis por Semana",
                                     font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        frame_semana.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_semana(frame_semana)

        # Frame Gráfico
        frame_grafico = tk.LabelFrame(container, text="Faturamento (Últimos 7 dias)",
                                      font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        frame_grafico.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_grafico(frame_grafico)

        # Frame Top 5 Carros
        frame_top_veic = tk.LabelFrame(container, text="Top 5 Carros no Mês",
                                       font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        frame_top_veic.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_top_veic(frame_top_veic)

        # Frame Top 5 Clientes
        frame_top_clients = tk.LabelFrame(container, text="Top 5 Clientes no Mês",
                                          font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        frame_top_clients.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_top_clients(frame_top_clients)

        # Atualiza tudo
        self.update_all()

    def setup_semana(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        self.semana_var = tk.StringVar(value="last7")

        radio_ultimos7 = tk.Radiobutton(parent, text="Últimos 7 dias",
                                        variable=self.semana_var, value="last7",
                                        font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT,
                                        command=self.update_semana)
        radio_ultimos7.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        radio_semana_atual = tk.Radiobutton(parent, text="Semana Atual",
                                            variable=self.semana_var, value="currentweek",
                                            font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT,
                                            command=self.update_semana)
        radio_semana_atual.grid(row=0, column=0, padx=5, pady=2, sticky="e")

        self.text_semana = tk.Text(parent, wrap="word", font=DEFAULT_FONT, bg="#F9F9F9", fg=FG_TEXT)
        self.text_semana.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def update_semana(self):
        self.text_semana.delete("1.0", tk.END)
        choice = self.semana_var.get()
        if choice == "last7":
            rentals_7d = self.system.list_rentals_last_7_days()
            if not rentals_7d:
                self.text_semana.insert(tk.END, "Nenhum aluguel encontrado nos últimos 7 dias.\n")
                return
            for (r, status) in rentals_7d:
                dt_ret = r["data_retirada"].strftime('%d/%m/%Y %H:%M')
                self.text_semana.insert(tk.END,
                    f"Aluguel ID: {r['rental_id']} | Veículo ID: {r['vehicle_id']} | "
                    f"Cliente: {r['nome_cliente']} | Retirada: {dt_ret} | Status: {status}\n"
                )
        else:
            rentals_week = self.system.list_rentals_current_week()
            if not rentals_week:
                self.text_semana.insert(tk.END, "Nenhum aluguel encontrado na semana atual.\n")
                return
            for (r, status) in rentals_week:
                dt_ret = r["data_retirada"].strftime('%d/%m/%Y %H:%M')
                self.text_semana.insert(tk.END,
                    f"Aluguel ID: {r['rental_id']} | Veículo ID: {r['vehicle_id']} | "
                    f"Cliente: {r['nome_cliente']} | Retirada: {dt_ret} | Status: {status}\n"
                )

    def setup_grafico(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.frame_chart = tk.Frame(parent, bg=BG_FRAME)
        self.frame_chart.grid(row=0, column=0, sticky="nsew")

        self.fig = None
        self.canvas_mpl = None

    def update_chart(self):
        (labels, values) = self.system.get_7days_faturamento()
        if self.canvas_mpl:
            self.canvas_mpl.get_tk_widget().destroy()
            self.canvas_mpl = None
            self.fig = None

        self.fig = Figure(figsize=(5,3), dpi=100)
        ax = self.fig.add_subplot(111)

        # Plot
        ax.plot(labels, values, marker='o', color='#000000', linewidth=2, markersize=8)
        ax.set_title("Faturamento dos Últimos 7 Dias", fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel("Dia", fontsize=12)
        ax.set_ylabel("Valor (R$)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.6)

        ax.set_ylim(bottom=0)

        def formato_moeda(x, pos):
            return f"R$ {x:,.2f}"
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(formato_moeda))

        self.fig.tight_layout()

        self.canvas_mpl = FigureCanvasTkAgg(self.fig, master=self.frame_chart)
        self.canvas_mpl.draw()
        self.canvas_mpl.get_tk_widget().pack(fill="both", expand=True)

    def setup_top_veic(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        self.top_veic_text = tk.Text(parent, wrap="word", font=DEFAULT_FONT, bg="#F9F9F9", fg=FG_TEXT)
        self.top_veic_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def update_top_veic(self):
        self.top_veic_text.delete("1.0", tk.END)
        top5 = self.system.get_top_5_veiculos_mes()
        if not top5:
            self.top_veic_text.insert(tk.END, "Nenhum aluguel este mês.\n")
            return
        for (nome, count) in top5:
            self.top_veic_text.insert(tk.END, f"{nome} - {count} aluguéis\n")

    def setup_top_clients(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        self.top_clients_text = tk.Text(parent, wrap="word", font=DEFAULT_FONT, bg="#F9F9F9", fg=FG_TEXT)
        self.top_clients_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    def update_top_clients(self):
        self.top_clients_text.delete("1.0", tk.END)
        top5 = self.system.get_top_5_clientes_mes()
        if not top5:
            self.top_clients_text.insert(tk.END, "Nenhum aluguel este mês.\n")
            return
        for (cpf, count) in top5:
            self.top_clients_text.insert(tk.END, f"CPF: {cpf} - {count} aluguéis\n")

    def update_all(self):
        self.update_semana()
        self.update_top_veic()
        self.update_top_clients()
        self.update_chart()

# ---------------------------------------------------------------------------------------
# Tela Principal (CarRentalApp)
# ---------------------------------------------------------------------------------------
class CarRentalApp(tk.Tk):
    """
    Tela Principal (3 colunas, 3 linhas).
    Seção "Alugar Veículo" com Nome do Cliente.
    Na listagem de aluguéis abertos, mostra "Devolução Estimada".
    Botão "Apagar Base de Dados" agora abaixo do botão "Visão Geral".
    """
    def __init__(self, system, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.system = system

        self.title("Sistema de Aluguel de Carros - Tela Principal")
        self.configure(bg=BG_MAIN)
        self.geometry("1200x700")

        container = tk.Frame(self, bg=BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        for r in range(3):
            container.rowconfigure(r, weight=1, minsize=200)
        for c in range(3):
            container.columnconfigure(c, weight=1, minsize=370)

        # Coluna 0
        self.frame_login = tk.LabelFrame(container, text="Login / Logout", font=DEFAULT_FONT,
                                         bg=BG_FRAME, fg=FG_TEXT)
        self.frame_login.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_login_logout(self.frame_login)

        self.frame_create_user = tk.LabelFrame(container, text="Criar Usuário (Admin)",
                                              font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        self.frame_create_user.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_criar_usuario(self.frame_create_user)

        self.frame_vehicle = tk.LabelFrame(container, text="Cadastrar Veículo (Admin)",
                                           font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        self.frame_vehicle.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_cadastrar_veiculo(self.frame_vehicle)

        # Coluna 1
        self.frame_mod_vehicle = tk.LabelFrame(container, text="Modificar Veículo (Admin)",
                                               font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)
        self.frame_mod_vehicle.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_modificar_veiculo(self.frame_mod_vehicle)

        self.frame_rent = tk.LabelFrame(container, text="Alugar Veículo", font=DEFAULT_FONT,
                                        bg=BG_FRAME, fg=FG_TEXT)
        self.frame_rent.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_alugar(self.frame_rent)

        self.frame_return = tk.LabelFrame(container, text="Devolução de Veículo", font=DEFAULT_FONT,
                                          bg=BG_FRAME, fg=FG_TEXT)
        self.frame_return.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        self.setup_devolver(self.frame_return)

        # Coluna 2
        self.frame_listings = tk.LabelFrame(container, text="Listagens Gerais", font=DEFAULT_FONT,
                                            bg=BG_FRAME, fg=FG_TEXT)
        self.frame_listings.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.setup_listagens(self.frame_listings)

        # Frame col=2, row=2 - para Visão Geral + Apagar Base
        self.frame_visao_geral = tk.Frame(container, bg=BG_MAIN)
        self.frame_visao_geral.grid(row=2, column=2, sticky="nsew", padx=5, pady=5)
        self.setup_visao_geral_button(self.frame_visao_geral)

        self.update_ui()

    # ------------------ Métodos de Setup ------------------
    def setup_login_logout(self, parent):
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="Usuário:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_username = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_username.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Senha:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_password = tk.Entry(parent, show="*", **ENTRY_STYLE)
        self.entry_password.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        btn_login = tk.Button(parent, text="Login", **BUTTON_STYLE, command=self.handle_login)
        btn_login.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        btn_logout = tk.Button(parent, text="Logout", **BUTTON_STYLE, command=self.handle_logout)
        btn_logout.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.label_logged_user = tk.Label(parent, text="Não logado", fg="red",
                                          font=(DEFAULT_FONT[0], DEFAULT_FONT[1], "italic"), bg=BG_FRAME)
        self.label_logged_user.grid(row=3, column=0, columnspan=2, pady=5)

    def setup_criar_usuario(self, parent):
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="Username:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_newuser_username = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_newuser_username.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Senha:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_newuser_password = tk.Entry(parent, show="*", **ENTRY_STYLE)
        self.entry_newuser_password.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Tipo:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.role_var = tk.StringVar(value="padrao")
        role_options = ["admin", "padrao"]
        option_role = tk.OptionMenu(parent, self.role_var, *role_options)
        option_role.config(font=DEFAULT_FONT, bg="#FFFFFF", fg=FG_TEXT, bd=2, relief="solid")
        option_role.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        btn_createuser = tk.Button(parent, text="Criar", **BUTTON_STYLE, command=self.handle_create_user)
        btn_createuser.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_cadastrar_veiculo(self, parent):
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="Nome:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_veic_nome = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_veic_nome.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Marca:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_veic_marca = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_veic_marca.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Ano:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.entry_veic_ano = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_veic_ano.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Placa:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.entry_veic_placa = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_veic_placa.grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        btn_register_veic = tk.Button(parent, text="Cadastrar", **BUTTON_STYLE, command=self.handle_register_vehicle)
        btn_register_veic.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_modificar_veiculo(self, parent):
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="ID:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_mod_id = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_mod_id.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Novo Nome:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_mod_nome = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_mod_nome.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Nova Marca:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.entry_mod_marca = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_mod_marca.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Novo Ano:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.entry_mod_ano = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_mod_ano.grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Nova Placa:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=4, column=0, sticky="e", padx=5, pady=3)
        self.entry_mod_placa = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_mod_placa.grid(row=4, column=1, sticky="ew", padx=5, pady=3)

        btn_mod_vehicle = tk.Button(parent, text="Modificar", **BUTTON_STYLE, command=self.handle_modify_vehicle)
        btn_mod_vehicle.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_alugar(self, parent):
        parent.columnconfigure(1, weight=1)

        tk.Label(parent, text="ID Veículo:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_id = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_id.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Nome do Cliente:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_nome = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_nome.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="CPF:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_cpf = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_cpf.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="WhatsApp:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_whatsapp = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_whatsapp.grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="Dias:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=4, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_dias = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_dias.grid(row=4, column=1, sticky="ew", padx=5, pady=3)

        tk.Label(parent, text="R$/dia:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=5, column=0, sticky="e", padx=5, pady=3)
        self.entry_rent_valordia = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_rent_valordia.grid(row=5, column=1, sticky="ew", padx=5, pady=3)

        btn_rent = tk.Button(parent, text="Alugar", **BUTTON_STYLE, command=self.handle_rent_vehicle)
        btn_rent.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_devolver(self, parent):
        parent.columnconfigure(1, weight=1)
        tk.Label(parent, text="ID Aluguel:", font=DEFAULT_FONT, bg=BG_FRAME, fg=FG_TEXT)\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_return_id = tk.Entry(parent, **ENTRY_STYLE)
        self.entry_return_id.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        btn_return = tk.Button(parent, text="Devolver", **BUTTON_STYLE, command=self.handle_return_vehicle)
        btn_return.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_listagens(self, parent):
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        btn_list_vehicles = tk.Button(parent, text="Listar Veículos", **BUTTON_STYLE,
                                      command=self.handle_list_vehicles)
        btn_list_vehicles.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        btn_list_open_rentals = tk.Button(parent, text="Listar Aluguéis em Aberto",
                                          **BUTTON_STYLE, command=self.handle_list_open_rentals)
        btn_list_open_rentals.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.text_list = tk.Text(parent, wrap="word", font=DEFAULT_FONT, bg="#F9F9F9", fg=FG_TEXT)
        self.text_list.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

    def setup_visao_geral_button(self, parent):
        # Botão "Visão Geral"
        btn_visao = tk.Button(parent, text="Visão Geral", **BUTTON_STYLE,
                              command=self.open_visao_geral)
        btn_visao.pack(fill="x", padx=5, pady=5)

        # Botão "Apagar Base de Dados" abaixo do "Visão Geral"
        btn_clear_db = tk.Button(parent, text="Apagar Base de Dados", **BUTTON_STYLE,
                                 command=self.handle_clear_database)
        btn_clear_db.pack(fill="x", padx=5, pady=5)

    # ------------------ Métodos-Handler ------------------
    def open_visao_geral(self):
        if not self.system.get_current_user():
            messagebox.showerror("Erro", "É necessário estar logado para abrir a Visão Geral!")
            return
        visao = VisaoGeralWindow(self, self.system)
        visao.grab_set()

    def handle_login(self):
        user = self.entry_username.get().strip()
        pw   = self.entry_password.get().strip()
        if self.system.login(user, pw):
            messagebox.showinfo("Login", f"Bem-vindo, {user}!")
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.")
        self.update_ui()

    def handle_logout(self):
        self.system.logout()
        self.update_ui()

    def handle_create_user(self):
        username = self.entry_newuser_username.get().strip()
        password = self.entry_newuser_password.get().strip()
        role     = self.role_var.get().strip()
        msg = self.system.create_user(username, password, role)
        messagebox.showinfo("Criar Usuário", msg)
        self.update_ui()

    def handle_register_vehicle(self):
        nome  = self.entry_veic_nome.get().strip()
        marca = self.entry_veic_marca.get().strip()
        ano   = self.entry_veic_ano.get().strip()
        placa = self.entry_veic_placa.get().strip()
        msg   = self.system.register_vehicle(nome, marca, ano, placa)
        messagebox.showinfo("Cadastro de Veículo", msg)
        self.update_ui()

    def handle_modify_vehicle(self):
        try:
            vehicle_id = int(self.entry_mod_id.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "ID do veículo inválido!")
            return
        nome  = self.entry_mod_nome.get().strip()
        marca = self.entry_mod_marca.get().strip()
        ano   = self.entry_mod_ano.get().strip()
        placa = self.entry_mod_placa.get().strip()
        msg   = self.system.modify_vehicle(vehicle_id, nome, marca, ano, placa)
        messagebox.showinfo("Modificar Veículo", msg)
        self.update_ui()

    def handle_rent_vehicle(self):
        try:
            vehicle_id = int(self.entry_rent_id.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "ID do veículo inválido!")
            return

        nome_cliente = self.entry_rent_nome.get().strip()
        cpf          = self.entry_rent_cpf.get().strip()
        whatsapp     = self.entry_rent_whatsapp.get().strip()

        try:
            dias          = int(self.entry_rent_dias.get().strip())
            valor_por_dia = float(self.entry_rent_valordia.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Dias ou valor por dia inválidos!")
            return

        msg = self.system.rent_vehicle(vehicle_id, nome_cliente, cpf, whatsapp, dias, valor_por_dia)
        messagebox.showinfo("Aluguel", msg)

        # Limpar campos após alugar
        self.entry_rent_id.delete(0, tk.END)
        self.entry_rent_nome.delete(0, tk.END)
        self.entry_rent_cpf.delete(0, tk.END)
        self.entry_rent_whatsapp.delete(0, tk.END)
        self.entry_rent_dias.delete(0, tk.END)
        self.entry_rent_valordia.delete(0, tk.END)

        self.update_ui()

    def handle_return_vehicle(self):
        try:
            rental_id = int(self.entry_return_id.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "ID do aluguel inválido!")
            return
        msg = self.system.return_vehicle(rental_id)
        messagebox.showinfo("Devolução", msg)
        self.update_ui()

    def handle_list_vehicles(self):
        self.text_list.delete("1.0", tk.END)
        vehicles = self.system.list_vehicles()
        if not vehicles:
            self.text_list.insert(tk.END, "Nenhum veículo cadastrado.\n")
            return
        for v in vehicles:
            status = "Disponível" if v["disponivel"] else "Indisponível"
            linha = (f"ID: {v['id']} | {v['nome']} - {v['marca']} "
                     f"- {v['ano']} - {v['placa']} [{status}]\n")
            self.text_list.insert(tk.END, linha)

    def handle_list_open_rentals(self):
        self.text_list.delete("1.0", tk.END)
        open_rentals = self.system.list_open_rentals()
        if not open_rentals:
            self.text_list.insert(tk.END, "Não há aluguéis em aberto.\n")
            return
        for r in open_rentals:
            dt_ret = r["data_retirada"].strftime('%d/%m/%Y %H:%M')
            dt_dev_est = r["data_devolucao_estimada"].strftime('%d/%m/%Y %H:%M')
            linha = (f"Aluguel ID: {r['rental_id']} | Veículo ID: {r['vehicle_id']} | "
                     f"Cliente: {r['nome_cliente']} | CPF: {r['cpf']} | Dias: {r['dias']} | "
                     f"Retirada: {dt_ret} | Devolução Estimada: {dt_dev_est}\n")
            self.text_list.insert(tk.END, linha)

    def handle_clear_database(self):
        """
        Botão "Apagar Base de Dados" (agora abaixo do botão "Visão Geral"):
        - Verifica se o usuário é admin
        - Pede confirmação (messagebox.askyesno)
        - Pede senha do admin (simpledialog.askstring)
        - Se ok, chama system.clear_data()
        """
        if not self.system.is_admin():
            messagebox.showerror("Erro", "Somente admin pode apagar a base de dados.")
            return

        confirm = messagebox.askyesno("Confirmação", 
                                      "Você tem certeza que deseja APAGAR TODOS OS DADOS?\nEsta ação é irreversível!")
        if not confirm:
            return

        # Pede senha do admin
        admin_pass = simpledialog.askstring("Senha do Admin", 
                                            "Por favor, insira a senha do admin para confirmar:",
                                            show='*')
        if admin_pass is None:
            # Usuário cancelou o input
            return

        # Verifica se a senha está correta
        # Precisamos achar o user admin ("admin") e verificar a password
        admin_user = None
        for u in self.system.users:
            if u["role"] == "admin" and u["username"] == "admin":
                admin_user = u
                break

        if admin_user is not None and admin_user["password"] == admin_pass:
            self.system.clear_data()
            messagebox.showinfo("Sucesso", "Base de dados apagada com sucesso. Admin recriado (admin/admin).")
        else:
            messagebox.showerror("Erro", "Senha de admin incorreta. Base de dados não foi apagada.")

    def update_ui(self):
        user = self.system.get_current_user()
        if user:
            self.label_logged_user.config(text=f"Logado como: {user['username']}", fg="green")
        else:
            self.label_logged_user.config(text="Não logado", fg="red")

        is_logged_in = bool(user)
        is_admin = self.system.is_admin()

        # Criar usuário: só admin
        state_create_user = "normal" if is_admin else "disabled"
        self.entry_newuser_username.config(state=state_create_user)
        self.entry_newuser_password.config(state=state_create_user)
        for w in self.frame_create_user.children.values():
            if isinstance(w, tk.OptionMenu):
                w.config(state=state_create_user)
            if isinstance(w, tk.Button) and w.cget("text") == "Criar":
                w.config(state=state_create_user)

        # Cadastrar e modificar veículos: só admin
        state_vehicle_admin = "normal" if is_admin else "disabled"
        self.entry_veic_nome.config(state=state_vehicle_admin)
        self.entry_veic_marca.config(state=state_vehicle_admin)
        self.entry_veic_ano.config(state=state_vehicle_admin)
        self.entry_veic_placa.config(state=state_vehicle_admin)

        self.entry_mod_id.config(state=state_vehicle_admin)
        self.entry_mod_nome.config(state=state_vehicle_admin)
        self.entry_mod_marca.config(state=state_vehicle_admin)
        self.entry_mod_ano.config(state=state_vehicle_admin)
        self.entry_mod_placa.config(state=state_vehicle_admin)

        for w in self.frame_vehicle.children.values():
            if isinstance(w, tk.Button) and w.cget("text") == "Cadastrar":
                w.config(state=state_vehicle_admin)
        for w in self.frame_mod_vehicle.children.values():
            if isinstance(w, tk.Button) and w.cget("text") == "Modificar":
                w.config(state=state_vehicle_admin)

        # Alugar e devolver: qualquer usuário logado
        state_rent_return = "normal" if is_logged_in else "disabled"
        self.entry_rent_id.config(state=state_rent_return)
        self.entry_rent_nome.config(state=state_rent_return)
        self.entry_rent_cpf.config(state=state_rent_return)
        self.entry_rent_whatsapp.config(state=state_rent_return)
        self.entry_rent_dias.config(state=state_rent_return)
        self.entry_rent_valordia.config(state=state_rent_return)
        self.entry_return_id.config(state=state_rent_return)

        for w in self.frame_rent.children.values():
            if isinstance(w, tk.Button) and w.cget("text") == "Alugar":
                w.config(state=state_rent_return)
        for w in self.frame_return.children.values():
            if isinstance(w, tk.Button) and w.cget("text") == "Devolver":
                w.config(state=state_rent_return)


def main():
    system = CarRentalSystem("data.json")
    app = CarRentalApp(system)
    app.mainloop()

if __name__ == "__main__":
    main()
