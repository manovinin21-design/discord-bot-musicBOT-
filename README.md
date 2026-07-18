# 🎵 JotaBeEli — Bot de Música e Comunidade para Discord

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.7-5865F2?logo=discord&logoColor=white)
![Licença](https://img.shields.io/badge/feito%20com-%E2%9D%A4%EF%B8%8F%20e%20Python-red)

O **JotaBeEli** é um bot de Discord completo, desenvolvido inteiramente em Python, que nasceu como um simples bot de música e cresceu até virar um canivete suíço para servidores: toca música do YouTube com fila e controles completos, tem sistema de XP com ranking, comandos de moderação para manter a ordem e comandos sociais para animar a resenha — incluindo a famosa calculadora de ship. 💘

<img width="1866" height="934" alt="JotaBeEli em ação" src="https://github.com/user-attachments/assets/c4772af2-fb27-4950-9ae5-666e9ba46837" />

---

## ✨ O que ele faz

- 🎶 **Música do YouTube** — busca por nome ou link, fila por servidor, pause/resume, replay, navegação pelo tempo da música (`!jumpto`), letra da música (`!lyrics`), remoção e reordenação de músicas, barra de progresso e embeds bonitos com thumbnail
- ⚡ **Player rápido** — o link do áudio é resolvido na busca e a próxima música é pré-carregada em segundo plano, então a troca de faixas é praticamente instantânea
- 💬 **Mensagens automáticas** — boas-vindas, despedidas e agradecimento de boost em embeds com a foto do membro, cada uma ativada no canal que você escolher
- 📊 **Sistema de XP** — os membros ganham XP conversando (com cooldown anti-spam), sobem de nível e disputam o ranking do servidor
- 🛡️ **Moderação completa** — mute com tempo, ban/kick, advertências salvas em banco de dados, bloqueio de canais individual ou em massa e limpeza de mensagens
- 💘 **Social** — calculadora de ship com ranking dos casais, beijos com GIFs e mais
- 🔒 **Robusto** — tudo separado por servidor, banco de dados com recuperação automática de corrupção e reconexão do player em quedas de rede

---

## 📋 Comandos

> Use `!ajuda` dentro do Discord para ver essa lista a qualquer momento.

### 🎮 Interação

| Comando | O que faz |
|---|---|
| `!ping` | Responde com "Pong! 🏓" e a latência |
| `!oi` | Diz olá |
| `!dado` | Rola um dado de 6 lados |
| `!ship <usuário1> <usuário2>` | Calcula a compatibilidade entre duas pessoas |
| `!topships` | Ranking dos ships mais fortes do servidor |
| `!kiss <usuário>` | Beija alguém (com GIF) |
| `!rank [usuário]` | Mostra o nível e XP de alguém |
| `!leaderboard` | Ranking de XP do servidor |
| `!ajuda` | Lista todos os comandos |

*Dizem que existem comandos secretos... 👀*

### 🎵 Música

| Comando | O que faz |
|---|---|
| `!entrar` | Entra no seu canal de voz |
| `!tocar <nome ou link>` | Toca uma música ou adiciona à fila (atalhos: `!play`, `!p`) |
| `!fila` | Mostra a música atual e as próximas (atalhos: `!queue`, `!q`) |
| `!removerdafila <número>` | Remove uma música específica da fila (atalho: `!remover`) |
| `!mover <de> <para>` | Muda uma música de posição na fila |
| `!skip` | Pula para a próxima música |
| `!pausar` / `!continuar` | Pausa e retoma a música |
| `!jumpto <tempo>` | Pula a música para um momento específico (ex.: `!jumpto 1:23`) |
| `!reset` | Reseta o tempo da música (volta para o início) |
| `!duração` | Progresso da música atual com barra (atalho: `!np`) |
| `!replay` | Volta para o início da última música tocada — a atual fica como próxima |
| `!replayall` | Duplica todas as músicas (até as que já tocaram) e coloca como próximas |
| `!lyrics` | Mostra a letra da música atual ou a legenda do vídeo (atalho: `!letra`) |
| `!fim` | Finaliza a música atual |
| `!encerrar` | Limpa a fila |
| `!sair` | Sai do canal de voz |

### 💬 Mensagens automáticas

Embeds de boas-vindas, saída e boost com a foto do membro. **Elas vêm desativadas** — cada uma só passa a funcionar depois que você ativar com o comando dela (é preciso a permissão *Gerenciar servidor*):

| Comando | O que faz |
|---|---|
| `!addmsgin <#canal>` | Ativa as mensagens de boas-vindas no canal escolhido |
| `!addmsgout <#canal>` | Ativa as mensagens de saída no canal escolhido |
| `!addmsgboost <#canal>` | Ativa as mensagens de boost no canal escolhido |
| `!delmsgin` / `!delmsgout` / `!delmsgboost` | Desativa a mensagem correspondente |
| `!msgconfig` | Mostra os canais configurados no servidor |

> ⚠️ Essas mensagens dependem do **Server Members Intent** ativado no Discord Developer Portal (passo 2 da instalação).

### 🛡️ Moderação

| Comando | O que faz | Permissão necessária |
|---|---|---|
| `!mute <usuário> <minutos> [motivo]` | Silencia por um tempo | Moderar membros |
| `!unmute <usuário>` | Remove o silêncio | Moderar membros |
| `!warn <usuário> [motivo]` | Aplica uma advertência | Moderar membros |
| `!warnings <usuário>` | Lista as advertências | — |
| `!clearwarns <usuário>` | Apaga as advertências | Moderar membros |
| `!ban <usuário> [motivo]` | Bane | Banir membros |
| `!unban <ID ou nome>` | Desbane | Banir membros |
| `!kick <usuário> [motivo]` | Expulsa | Expulsar membros |
| `!clear <quantidade>` | Apaga até 100 mensagens | Gerenciar mensagens |
| `!lock` / `!unlock` | Bloqueia/libera o canal atual | Gerenciar canais |
| `!lockall` / `!unlockall` | Bloqueia/libera todos os canais | Administrador |
| `!addxp` / `!removexp <usuário> <qtd>` | Ajusta o XP de alguém | Administrador |

---

## 🧰 Tecnologias

- [Python](https://www.python.org/) 3.11+
- [discord.py](https://discordpy.readthedocs.io/) — conexão com o Discord
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — busca e extração de áudio do YouTube
- [FFmpeg](https://ffmpeg.org/) — processamento do áudio
- SQLite — banco de dados de XP, advertências e configuração das mensagens automáticas (nativo do Python, sem instalar nada)
- [LRCLIB](https://lrclib.net/) — busca de letras de música para o `!lyrics` (API gratuita, sem chave)

---

## 🚀 Instalação passo a passo

### 1. Pré-requisitos

- **Python 3.11 ou superior** — [python.org/downloads](https://www.python.org/downloads/) (no Windows, marque a opção *"Add Python to PATH"* na instalação)
- **FFmpeg** — necessário para tocar música:
  - **Windows:** `winget install Gyan.FFmpeg` no terminal, ou baixe em [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) e adicione ao PATH
  - **Linux:** `sudo apt install ffmpeg`
- **Git** (para clonar o projeto)

### 2. Crie o seu bot no Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications) e clique em **New Application**
2. Na aba **Bot**, clique em **Reset Token** e **copie o token** (você vai usar já já — e nunca compartilhe ele com ninguém!)
3. Ainda na aba Bot, ative as opções **Message Content Intent** e **Server Members Intent**
4. Na aba **OAuth2 → URL Generator**, marque `bot`, selecione as permissões (ou marque `Administrator` para simplificar) e use a URL gerada para adicionar o bot ao seu servidor

### 3. Baixe e configure o projeto

```bash
# Clone o repositório
git clone https://github.com/manovinin21-design/discord-bot-musicBOT-.git
cd discord-bot-musicBOT-

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

### 4. Configure o token

Crie um arquivo chamado `.env` na pasta do projeto com o conteúdo:

```
DISCORD_TOKEN=cole_seu_token_aqui
```

> 💡 O `.env` já está no `.gitignore` — seu token nunca vai parar no GitHub por acidente.

### 5. Rode o bot

```bash
python main.py
```

Se aparecer `✅ Bot conectado como SeuBot#0000`, está funcionando! O banco de dados (`database.db`) é criado automaticamente na primeira execução. 🎉

---

## 📁 Estrutura do projeto

```
musicBOT/
├── main.py         # Ponto de entrada: conecta o bot e carrega os módulos
├── config.py       # Configurações, constantes e opções do player
├── database.py     # Banco de dados SQLite (XP e advertências)
├── utils.py        # Funções auxiliares compartilhadas
├── music.py        # 🎵 Comandos de música
├── eventos.py      # 💬 Mensagens de boas-vindas, saída e boost
├── moderation.py   # 🛡️ Comandos de moderação
├── xp.py           # 📊 Sistema de XP e níveis
├── social.py       # 💘 Ship, kiss e afins
├── fun.py          # 🎮 Comandos de diversão
├── admin.py        # ⚙️ Ajuda e comandos do dono
└── ships.json      # Histórico dos ships calculados
```

Cada módulo é um *cog* independente do discord.py — para criar um comando novo, basta adicioná-lo ao módulo do tema (ou criar um módulo novo e registrá-lo na lista `COGS` do `main.py`).

---

## ☁️ Rodando 24 horas

O bot roda em qualquer máquina com Python + FFmpeg: um PC que fica ligado, um Raspberry Pi ou uma VM na nuvem (o free tier da [Oracle Cloud](https://www.oracle.com/cloud/free/) é uma boa opção gratuita). Só lembre de criar o `.env` na máquina nova — ele não vai junto no clone, de propósito.

---

## 🤝 Contribuindo

Achou um bug ou tem uma ideia de comando? Abra uma issue ou mande um pull request — o projeto foi organizado justamente para ser fácil de estender.

Feito com ❤️, Python e muita resenha.
