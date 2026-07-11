# 🎵 MusicBOT para Discord inteiramente em python

<img width="1866" height="934" alt="image" src="https://github.com/user-attachments/assets/c4772af2-fb27-4950-9ae5-666e9ba46837" />


Um bot para Discord desenvolvido em **Python** usando **discord.py**, com foco em músicas, moderação de servidores e comandos de interação.
(ao instalar, use !ajuda para listar os comandos disponiveis)

---

## as funcionalidades

### Música
- ele em canais de voz
- toca de músicas pelo YouTube
- tem um sistema de fila
- tem replay de músicas
- Pausa e continua a música
- encerra a música
- limpar fila
- sai do canal de voz

---

### Moderação

- Ban
- Unban
- Kick
- Mute (Timeout)
- Unmute
- Advertências (Warnings)
- Lista advertências
- Remove advertências
- Limpa mensagens
- Lock/Unlock de canais
- LockAll/UnlockAll para todos os canais

As advertências são armazenadas em um banco de dados **SQLite**.

---

### Interação

- Calculadora de Ship 
- Ranking dos melhores Ships
- Dado aleatório 
- Ping
- Olá
- Comando de ajuda

Os Ships são armazenados em um arquivo JSON para manter o histórico.

---

## Estrutura do projeto

```
musicBOT/
│
├── main.py
├── database.db
├── ships.json
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

---

## Tecnologias usadas

- Python 3
- discord.py
- yt-dlp
- FFmpeg
- SQLite
- python-dotenv

---

## passo a passo da instalação

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/musicBOT.git
```

Entre na pasta:

```bash
cd musicBOT
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
DISCORD_TOKEN=SEU_TOKEN_AQUI
```

> IMPORTANTE: nunca envie o seu `.env` para o GitHub, pois lá vai ficar os seus Tokens e informações que nao podem ser publicas.

---

## Executando

```bash
python main.py
```

---

## Comandos do bot para usar no discord:

### Música

| Comando | Descrição |
|----------|-----------|
| `!entrar` | Entra no canal de voz |
| `!tocar <música>` | Toca uma música |
| `!replay` | Repete a última música |
| `!pausar` | Pausa a música |
| `!continuar` | Continua a reprodução |
| `!fim` | Finaliza a música |
| `!encerrar` | Limpa a fila |
| `!sair` | Sai do canal |

---

### Moderação

| Comando | Descrição |
|----------|-----------|
| `!mute` | Silencia um usuário |
| `!unmute` | Remove o silêncio |
| `!warn` | Adiciona advertência |
| `!warnings` | Lista advertências |
| `!clearwarns` | Remove advertências |
| `!ban` | Bane um usuário |
| `!unban` | Remove banimento |
| `!kick` | Expulsa um usuário |
| `!clear` | Apaga mensagens |
| `!lock` | Bloqueia o canal |
| `!unlock` | Desbloqueia o canal |
| `!lockall` | Bloqueia todos os canais |
| `!unlockall` | Desbloqueia todos os canais |

---

### Diversão

| Comando | Descrição |
|----------|-----------|
| `!ship @user1 @user2` | Calcula compatibilidade |
| `!topships` | Ranking dos ships |
| `!dado` | Rola um dado com numeros de 1 a 6 |
| `!oi` | te cumprimenta |
| `!ping` | Testa latência e responde com pong |
| `!ajuda` | Exibe a lista de comandos |


---

## Banco de Dados

O projeto utiliza **SQLite** para armazenar:

- Advertências
- Moderador responsável
- Motivo da advertência

---

## Requisitos

Além das bibliotecas Python, é necessário possuir o **FFmpeg** instalado e configurado no PATH do sistema.

---

## Licença

Este projeto foi desenvolvido para fins de estudo e aprendizado utilizando Python e Discord.py.

