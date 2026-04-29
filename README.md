# 🌐 Google Maps Scraper

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Interface moderna e intuitiva para busca, extração e gestão de leads do Google Maps — com campanhas de WhatsApp integradas.

---

## ✨ Funcionalidades

- 🔍 **Busca Avançada** — Encontre negócios no Google Maps por localização, raio e palavras-chave
- 📧 **Extração de E-mails** — Varredura automática de websites para capturar e-mails de contato
- 🗄️ **Banco de Dados SQLite** — Armazenamento local com filtros, estatísticas e exportação
- 💬 **Campanhas WhatsApp** — Geração de links de disparo em massa com templates personalizáveis
- 📊 **Painel de Métricas** — Visualize estatísticas em tempo real sobre leads capturados
- 🎨 **Interface Material 3** — Design moderno, dark mode e responsivo

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.10+
- [Google Cloud API Key](https://console.cloud.google.com/apis/credentials) com Places API (New) e Geocoding API ativadas

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/google-maps-scraper.git
cd google-maps-scraper

# 2. Crie um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
```

Acesse em: [http://localhost:8501](http://localhost:8501)

---

## ⚙️ Configuração

1. Obtenha sua **Google API Key** em [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Ative as APIs necessárias:
   - **Places API (New)**
   - **Geocoding API**
3. Cole a chave no campo **"Google API Key"** da barra lateral da aplicação

---

## 📖 Como Usar

### 1. Buscar Negócios

1. Insira sua **API Key**
2. Defina a **localização** (ex: `Centro, Rio de Janeiro, RJ`)
3. Informe o **tipo de negócio** (ex: `dentista`, `academia`, `advogado`)
4. Ajuste o **raio de busca** e filtros opcionais
5. Clique em **"Buscar Negócios"**

### 2. Extrair Contatos

- Ative a opção **"Extrair e-mails"** na barra lateral
- O sistema varre automaticamente os websites encontrados
- Resultados são salvos no banco de dados SQLite

### 3. Campanha WhatsApp

1. Acesse a aba **"WhatsApp"**
2. Personalize o template da mensagem (use `{nome}`, `{telefone}`, etc.)
3. Selecione os leads desejados
4. Escolha uma ação:
   - **Abrir WhatsApp (local)** — abre conversas no navegador
   - **Gerar Launcher HTML** — arquivo standalone para disparo em massa
   - **Gerar Links CSV** — exporta links formatados

### 4. Gerenciar Dados

- A aba **"Banco de Dados"** exibe todos os leads salvos
- Filtre por query, localização, e-mail ou telefone
- Exporte para **CSV** ou **Excel**

---

## 🎨 Interface

O projeto utiliza o design system **Material 3 (Material You)** do Google, com:

- Paleta de cores dark mode calibrada
- Cards com elevação e micro-interações
- Botões estilo pill (altamente arredondados)
- Tipografia Inter com hierarquia visual clara
- Scrollbar e inputs estilizados

---

## 🏗️ Estrutura do Projeto

```
google-maps-scraper/
├── .streamlit/
│   └── config.toml          # Configuração do tema Streamlit
├── app.py                   # Interface principal (Streamlit)
├── scraper.py               # Lógica de busca e extração
├── database.py              # Modelos e operações SQLite
├── whatsapp.py              # Utilitários de campanha WhatsApp
├── config_manager.py        # Gerenciamento de configurações
├── requirements.txt         # Dependências Python
├── .gitignore               # Arquivos ignorados pelo Git
└── scraper.db               # Banco de dados SQLite (gerado automaticamente)
```

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|------------|-----|
| [Streamlit](https://streamlit.io/) | Interface web interativa |
| [Pandas](https://pandas.pydata.org/) | Manipulação e exportação de dados |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | Parsing de HTML para extração de e-mails |
| [Requests](https://requests.readthedocs.io/) | Requisições HTTP |
| [SQLite](https://sqlite.org/) | Banco de dados local |

---

## 📝 Placeholders do WhatsApp

Use as variáveis abaixo nos templates de mensagem:

| Placeholder | Descrição |
|-------------|-----------|
| `{nome}` | Nome do negócio |
| `{endereco}` | Endereço completo |
| `{telefone}` | Telefone de contato |
| `{email}` | E-mails extraídos |
| `{website}` | Website do negócio |
| `{avaliacao}` | Nota média (estrelas) |
| `{avaliacoes}` | Quantidade de avaliações |
| `{query}` | Termo de busca utilizado |
| `{local}` | Localização da busca |

---

## 🤝 Contribuição

Contribuições são bem-vindas! Para sugerir melhorias:

1. Faça um **fork** do projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'feat: adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um **Pull Request**

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 💡 Dicas

> ⚠️ **Limite de uso**: A API do Google Places possui cotas gratuitas. Monitore seu consumo no [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).

> 💾 **Backup**: O arquivo `scraper.db` contém todos os seus leads. Faça backups regulares.

> 🔒 **Segurança**: Nunca compartilhe sua `user_config.json` ou API Keys publicamente.

---

<p align="center">Desenvolvido com 💙 pela <strong>Hyska</strong></p>
