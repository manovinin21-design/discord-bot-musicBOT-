este é um bot de música e de comandos simples para discord desenvolvido inteiramente em Python VScode

funcionalidades:
- ele consegue entrar em canais de voz
- possui todas as funções padrão de um BOT de musica para discord
- responde comandos personalizados
- sistema de XP com níveis e ranking
- comandos de moderação completos (mute, ban, warn, lock...)
- comandos sociais (ship, kiss, nakano)

comandos dentro do discord:

Interação:
1. !ping / responde com "Pong! 🏓"
2. !oi / diz olá
3. !dado / rola um dado
4. !ajuda / mostra os comandos disponíveis
5. !ship <usuário1> <usuário2> / calcula a compatibilidade entre dois usuários
6. !topships / mostra o ranking dos ships mais altos
7. !kiss <usuário> / beija um usuário
8. !nakano / sorteia uma das quíntuplas
9. !rank [usuário] / mostra o rank de XP de um usuário
10. !leaderboard / mostra o ranking de XP do servidor

Música:
1. !entrar / entra no canal de voz
2. !tocar <pesquisa> / toca uma música
3. !fim / finaliza a música atual
4. !sair / sai do canal de voz
5. !continuar / retoma a música pausada
6. !pausar / pausa a música em execução
7. !encerrar / limpa a fila de músicas
8. !fila / mostra as músicas na fila
9. !removerdafila <número> / remove uma música da fila
10. !mover <de> <para> / move uma música de posição na fila
11. !replay / repete a última música tocada
12. !skip / pula para a próxima música
13. !duração / mostra a duração da música atual

Moderação:
1. !mute <usuário> <minutos> [motivo] / silencia um usuário
2. !unmute <usuário> / remove o silêncio
3. !ban <usuário> [motivo] / bane um usuário
4. !unban <usuário> / remove o banimento (ID ou nome)
5. !kick <usuário> [motivo] / expulsa um usuário
6. !clear <quantidade> / apaga mensagens
7. !warn <usuário> [motivo] / dá uma advertência
8. !warnings <usuário> / mostra as advertências
9. !clearwarns <usuário> / remove as advertências
10. !lock e !unlock / bloqueia/desbloqueia o canal
11. !lockall e !unlockall / bloqueia/desbloqueia todos os canais
12. !addxp e !removexp <usuário> <quantidade> / gerencia o XP

DIFERENCIAIS:
facil de modificar/adicionar
bem organizado, facil de entender
linguagem simples

Suas Tecnologias:
- Python
- discord.py
- FFmpeg

Como instalar:
1. clone o projeto
2. instale as dependências com este comando no terminal powershell:

pip install -r requirements.txt

após isso...

3. configure o token do SEU bot de Discord (dica: é importante que voce nao deixe seu token exposto, crie um .env e coloque-o la)
4. e agora o execute

<img width="1576" height="937" alt="image" src="https://github.com/user-attachments/assets/3e6d1394-59e2-4813-a6b0-24ad41c65f63" />

