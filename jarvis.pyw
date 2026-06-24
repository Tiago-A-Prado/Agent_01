import queue
import webbrowser #Abre URL do navegador
import urllib.parse #Formata textos para formato URL
import json #lê e escreve arquivos .json (ex: memoria.json)
import os #interação com sistema (arquivos, por exemplo)
import threading #Roda tarefas em paralelo
import glob #buscado de arquivos à partir de padrão
import sounddevice as sd
import numpy as np
import io
import wave
import subprocess
import speech_recognition as sr

from tkinter import * #Interface gráfica 
from pathlib import Path #abilita a função Path, extrai somente o nome do arquivos
from rapidfuzz import process, fuzz #process -> realiza busca texto x lista de opções.
# fuzz -> contém os algot=ritmos de comparação de texto 

usuario = os.getenv('USER') #Pega o noe do usuário do computador, facilita montagem de caminho para arquivos

#---------------------AUDIO----------------------#
r = sr.Recognizer()
def reconhecimento_voz(exibir):
    try:
        exibir('Calibrando...')
        fs = 16000
        duration = 5
        exibir('Ouvindo...')
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        # Converte para formato wav em memória
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(audio.tobytes())
        buffer.seek(0)
        
        # Envia para o Google
        with sr.AudioFile(buffer) as fonte:
            audio_data = r.record(fonte)
            texto = r.recognize_google(audio_data, language='pt-BR')
            exibir(f'Texto reconhecido: {texto}')
            return texto.lower().strip()
            
    except Exception as e:
        exibir(f'Voz não reconhecido {e}')
        return ''

#---------------------CACHE----------------------#
CACHE_FILE = 'program_cache.json' #adere o arquivo da memoria a uma variável

SEARCH_DIRS = [
    '/usr/bin',
    '/usr/local/bin',
    '/usr/share/applications',
    f'/home/{usuario}/.local/share/applications',
]
APELIDOS = {
    'code': 'visual studio code',
    'vscode': 'visual studio code',
    'excel': 'microsoft excel'
}


def const_index():  #indexa todos os programas
    index = {}  #Dicionário que será preenchido
    for base in SEARCH_DIRS:  #Uma busca em array que percorre a lista de pastas
        if not os.path.exists(base): 
            continue  #se o diretório não existe, pula a linha
        if base in ('/usr/bin', "/usr/local/bin"):  #repete a busca para arquivos sem extenção
            for path in glob.glob(os.path.join(base, "*")): #Monta o caminho de busca e retorna com os arquivos que batem com o padrão
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    name = Path(path).stem.lower()
                    index[name] = path #path extrai somente o nome do arquivos, colocando o nome do arquivos como chave e o caminho completo como valor
        #Busca para arquivos.desktop
        for path in glob.glob(os.path.join(base, '**', '*.desktop'), recursive=True):
            name = Path(path).stem.lower()
            index[name] = path

    return index #retorna o dicionário completo

def car_cache():
    if os.path.exists(CACHE_FILE):
        with open (CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f) #Tenta carregar o cache já existente, se já existir, abre e retorna o conteúdo
    return{}
    
def salvar_cache(index): #Salva o dicionário no arquivo JSON.
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2) #Permite salvar caractere especial, formata arquivo com identação

def recarregar_cache_back(): #reconstrói e salva o cache
    def _run():
        salvar_cache(const_index())
    threading.Thread(target=_run, daemon=True).start() #Cria uma thread separada para rodar, a thread é encerrada quando o programa encerra


#-----------------------------FUNÇÕES MEMORIA--------------------------#

    #---------------carregar memoria---------------------#
def memoria(): #tenta abrir memória e retorna seu conteúdo
    try:
        with open('memoria.json', 'r') as arquivo:
            return json.load(arquivo)
    except:
        return{} #se não existir, retorna dicionário vazio


    #-----------------salvar memoria--------------------#

def salvar_memoria(memoria): #salva o dicionário na memória. Sobrescreve sobre a versão anterior
    with open('memoria.json', 'w') as arquivo:
        json.dump(memoria, arquivo)

    #---------------------FUNÇÃO DE COMANDOS---------------------------#
def interpretar_comando(comando):
    comando = comando.lower().strip() #FORMATAÇÃO PADRÃO PARA COMANDO, SEM ESPAÇO E MINUSCULO
    if 'abrir' in comando:  #SE 'abrir' ESTIVER EM COMANDO
        partes = comando.split('abrir') #QUEBRA A STRING EM UM ARRAY COMEÇANDO DA PALAVRA ENTRE PARENTESES. USA ABRIR COMO DIVISOR
        alvo = partes[1].strip() if len(partes) > 1 else '' #ALVO É DEFINIDO COMO O SEGUNDO ELEMENTO DO ARRAY, OU NADA CASO NÃO EXISTA SEGUNDO ELEMENTO 

        return {  #RETORNA UM DICIONÁRIO PADRONIZADO E FEITO MANUALMENTE
            "tipo": "comando", #Pega o tipo da entrada
            "acao": "abrir", #pega o tipo da ação
            "alvo": alvo #o resto é o alvo da ação
        }
        
    
    #---------------O COMANDO REPETE PARA OS OUTROS PRÉ COLOCADOS-----------------#
    elif 'pesquisar' in comando:
        partes = comando.split('pesquisar')
        alvo = partes[1].strip() if len(partes) > 1 else ''

        return {
            "tipo": "comando",
            "acao": "pesquisar",
            "alvo": alvo
        }
    
    elif 'criar' in comando:
        partes = comando.split('criar')
        alvo = partes[1].strip() if len(partes) > 1 else ''

        return{
            "tipo": 'comando',
            'acao': 'criar',
            'alvo': alvo
        }
    
    #0----------------------FUNÇÃO MEMORIA-------------------------#
    elif 'meu nome é' in comando:
        nome = comando.replace('meu nome é', '').strip()

        return{
            'tipo': 'memoria',
            'acao': 'salvar_nome',
            'valor': nome
        }
    
    elif 'qual meu nome' in comando:
        return{
            'tipo': 'memoria',
            'acao': 'ler_nome'
        }
    
    elif 'histórico' in comando:
        return{
            'tipo': 'memoria',
            'acao': 'historico',
        }
    
    elif 'sair' in comando:
        return{
            'tipo': 'comando',
            'acao': 'sair',
        }


    else: #SE NÃO IDENTIFICA NENHUM COMANDO PRÉ COLOCADO, RETORNA APENAS COMO CONVERSA E O CONTEUDO É O INPUT COMPLETO
        return{
            "tipo": "conversa",
            "conteudo": comando
        }
    
#----------------------------------------------------------------------------#

#----------------------------função de busca de programas
def busca(alvo, index, exibir): #cria a função de busca utilizando a chave 'alvo' e o dicionário criado como parâmetro

    alvo = alvo.lower().strip() #Padroniza alvo
    alvo = APELIDOS.get(alvo, alvo) #substitui apelido por nome

    if alvo in index: #Comparação direta entre valores, se bater, retorna caminho direto
        return index[alvo]
    
    resultado = process.extractOne(alvo, index.keys(), scorer=fuzz.WRatio) #Se não bater. Compara alvo com as chaves de index, retornando 3 valores: nome_encontrado, acore, índice. fuzz.WRatio é algoritmo de comparação, tolerante a abreviação e variação

    if resultado and resultado[1] >=70:
        nome_encontrado = resultado[0]
        exibir(f'reconhecido como: "{nome_encontrado}"')
        return index[nome_encontrado]

#--------------------EXECUTANDO COMANDOS-----------------------#


def executar(interpretar_comando, memoria, historico, index, exibir):  #Função de execução pega valor do RETURN de funções anteriores
    if interpretar_comando["tipo"] == "comando": #Pega o valor do tipo e vê se e igual a 'comando', se for:

        acao = interpretar_comando["acao"]  #Armazena valor de 'acao'
        

        if acao == "abrir":  #Pega palavra chave
            alvo = interpretar_comando["alvo"] #Armazena valor do 'alvo'
            if alvo: #garante que a busca seja feita
                
                caminho = busca(alvo, index, exibir) #chama a função busca com alvo e index como parâmetro
                if caminho:
                    if caminho.endswith('.desktop'):
                        subprocess.Popen(['xdg-open', caminho])
                    else:
                        subprocess.Popen([caminho])
                    recarregar_cache_back() #depois atualiza o índice
                else:
                    exibir(f'Programa "{alvo}" não encontrado')
        
        elif acao == "sair":
            exibir('Encerrando...')

        elif acao == "pesquisar":
            alvo = interpretar_comando["alvo"] #Armazena valor do 'alvo'
            if alvo:
                query = urllib.parse.quote(alvo) #transforma texto em formato para URL
                url = f"https://www.google.com/search?q={query}"
                webbrowser.open(url)


#------------------------comandos memoria--------------------------#

    elif interpretar_comando['tipo'] == 'memoria':  #Pega tipo do comando
        if interpretar_comando['acao'] == 'salvar_nome':  #Valor da acao do return
            memoria['nome'] = interpretar_comando['valor']  #Adere o valor correto ao campo 'nome'
            salvar_memoria(memoria)   #SALVA O COMANDO
            exibir(f'identificação salva')

        elif interpretar_comando['acao'] == 'ler_nome':
            nome = memoria.get('nome', 'não sei')
            exibir(f'Seu nome é {nome}')
        
        elif interpretar_comando ['acao'] == 'historico':
            for item in historico:
                exibir(item)
        

#--------------------------------------------------------------------------#
    
#--------------------------CODIGO PARA COMANDOS---------------------------#

class Application:
    def __init__(self, master=None):

        self.fila = queue.Queue() #cria uma fila para comunicação entre threads, caso seja necessário
        self.escrevendo = False #variável para controlar se está escrevendo na interface gráfica, evitando conflitos de acesso

        master.title("01") #configura o título da janela

        master.attributes('-topmost', True) #mantém a janela sempre no topo, mesmo que outra janela seja selecionada
        
        self.x = -500 #posição inicial da janela, fora da tela
        self.master = master
        self.master.geometry("400x300+-500+100") #configura o tamanho da janela e a posição inicial (fora da tela, para depois deslizar)
        self.master.after(10, self.deslizar)

        master.configure(bg='black') #configura a cor de fundo da janela

        self.ativo = True
        threading.Thread(target=self._escuta, daemon=True).start() #Inicia a thread de escuta, que roda em paralelo com a interface gráfica

        self.memoria = memoria()
        self.historico = []
        self.index = car_cache()


        if not self.index: #se cache estiver vazio, faz varredura e indexa devidamente os programas
            print('Indexando programas novos')
            self.index = const_index()
            salvar_cache(self.index)
            print(f'{len(self.index)} programas encontrados')
        


        self.fontePadrao = ("comic sans ms", "10") #configura a fonte padrão para os widgets
        self.container1 = Frame(master, bg='black') #cria o primeiro frame dentro da janela principal
        
        self.container2 = Frame(master, bg='black') #cria o segundo frame dentro da janela principal

        #-----------------------CONTAINER 1-------------#

        self.titulo = Label(self.container1, bg='black', fg="#a200ff") #cria um rótulo com o texto "JARVIS" dentro do primeiro frame

        self.titulo["text"] = "01" #configura o texto do rótulo

        self.titulo["font"] = self.fontePadrao #configura a fonte do rótulo
        self.titulo.pack() #exibe o rótulo no frame

        self.container1.pack() #exibe o primeiro frame na janela

        #-----------------------CONTAINER 2-------------#
        self.texto = Text(self.container2, bg='black', fg="#a200ff") #cria um widget de texto dentro do segundo frame
        self.texto["font"] = self.fontePadrao #configura a fonte do widget de texto
        self.texto["width"] = 50 #configura a largura do widget de texto
        self.texto["height"] = 30 #configura a altura do widget de texto
        self.texto.pack() #exibe o widget de texto no frame
        
        self.texto.after(100, self.processar_fila) #chama a função de processar fila a cada 100 milissegundos, garantindo que as mensagens sejam exibidas na interface gráfica mesmo que venham de outra thread

        self.container2.pack() #exibe o segundo frame na janela

    def deslizar(self):
        if self.x < 100:
            self.x += 50
            self.master.geometry(f"400x500+{self.x}+100")
            self.master.after(10, self.deslizar)


    def exibir(self, mensagem):
        self.fila.put(mensagem)
    
    def processar_fila(self):
        if not self.fila.empty() and not self.escrevendo: #verifica se a fila não está vazia e se não está escrevendo
            self.escrevendo = True #indica que está escrevendo
            mensagem = self.fila.get() #pega a próxima mensagem da fila
            self._exibir(mensagem, 0) #chama a função de digitar para exibir a mensagem
        self.texto.after(100, self.processar_fila) #chama a função novamente após um curto intervalo de tempo para verificar a fila novamente
            

    def _exibir(self, mensagem, index=0):
        if index < len(mensagem):
            self.texto.insert(END, mensagem[index]) #insere o próximo caractere da mensagem no widget de texto
            self.texto.see(END) #rola o widget de texto para exibir a nova linha
            self.texto.after(30, self._exibir, mensagem, index + 1) #chama a função novamente após um curto intervalo de tempo para criar o efeito de digitação')
        else:
            self.texto.insert(END, '\n') #insere uma nova linha após a mensagem completa
            self.texto.see(END) #rola o widget de texto para exibir a nova linha
            self.escrevendo = False #indica que terminou de escrever a mensagem
    
    def _escuta(self):

        while True: 
            comando = reconhecimento_voz(self.exibir)
            if not comando:
                continue
            if not self.ativo:
                if '01' in comando:
                    self.ativo = True
                    self.exibir('Ativado')
            else:

                resultado = interpretar_comando(comando)
                executar(resultado, self.memoria, self.historico, self.index, self.exibir) #chama a função de execução, passando o resultado do comando interpretado, a memória, o histórico, o índice e a função de exibição como parâmetros
                if resultado.get('acao') == 'sair':
                    self.ativo = False #desativa a escuta, encerrando o loop e a thread
                    


root = Tk() #cria a janela principal da aplicação
Application(root) #chama a classe Application, passando a janela principal como argumento
root.mainloop() #inicia o loop principal da aplicação, permitindo que a janela seja exibida
