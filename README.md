# Conversor de vídeos do YouTube para MP3

### Visão Geral
Uma aplicação web que permite aos usuários converter vídeos do YouTube para formato MP3, utilizando FastAPI como backend e uma interface moderna com HTML/CSS/JavaScript.

### Funcionalidades
- Converter vídeos únicos do YouTube para MP3
- Rastreamento de progresso em tempo real
- Interface simples e intuitiva
- Suporte para download de arquivos convertidos

### Pré-requisitos
- Python 3.8 ou superior
- Docker e Docker Compose (opcional, para implantação em contêiner)

### Instalação

#### Opção 1: Usando Docker (Recomendado)
```bash
docker-compose up --build

# Acesse a aplicação em http://localhost:8000
```

#### Opção 2: Instalação Manual
1. Clone o repositório:
```bash
git clone [seu-url-do-repositório]
cd youtube-to-mp3
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install fastapi uvicorn yt-dlp pydub
```

4. Execute a aplicação:
```bash
python app/main.py
```

### Uso
1. Abra seu navegador e navegue até `http://localhost:8000`
2. Insira uma URL de vídeo do YouTube
3. Clique em "Converter para MP3"
4. Aguarde a conversão ser concluída (a barra de progresso mostrará o status)
5. Baixe o arquivo MP3 convertido

### Estrutura do Projeto
```
youtube-to-mp3/
├── app/
│   ├── main.py          # Aplicação FastAPI
│   └── static/
│       ├── index.html   # Interface frontend
│       ├── style.css    # Estilização
│       └── script.js    # Lógica frontend
├── Dockerfile
└── docker-compose.yml
```

### Contribuindo
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça o commit das suas mudanças
4. Faça o push para a branch
5. Crie um novo Pull Request
