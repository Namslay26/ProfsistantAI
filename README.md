# 🧠 Profsistant — Your AI Research Kickoff Assistant
![Header](./ProfsistantAI.png)
**Profsistant** is an intelligent assistant designed to help academic researchers — especially students — get started on research projects faster and more effectively. It helps you discover relevant papers, organize your reading, generate research gaps and ideas, and build a personalized reading plan.

> 📚 Turn scattered papers into a focused project.  
> 🤖 Powered by Gemini, built with Streamlit.

---

## ✨ Features

### 🔍 Paper Discovery & Summarization
- Enter a research topic and get top Google Scholar papers
- Automatically extract and display abstracts, links, and authors

### 📚 Reading Tracker
- Track progress: `To Read`, `Reading`, `Done`
- Add notes, sources, and custom tags to each paper
- Manually add your own papers too!

### 📊 Research Dashboard
- View charts showing reading progress and topic distribution
- Filter papers by label or source

### 📅 Personalized Planner
- Enter your availability
- Generate a research reading schedule
- Export it to a `.ics` calendar file

### 💡 Research Gap & Idea Generator
- Gemini analyzes your paper list
- Suggests research gaps, follow-up ideas, and mini-projects
- Add to a persistent, editable “Ideas List”

---

## 🏗️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **LLM:** [Gemini Pro (via Google Generative AI API)](https://ai.google.dev/)
- **Charts:** Plotly
- **Calendar Export:** Python `ics` library

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/profsistant.git
cd profsistant
```
### 2. Install requirements
```
pip install -r requirements.txt
```
### 3. Set your API key
Create a file: .streamlit/secrets.toml
```
GEMINI_API_KEY = "your-gemini-api-key-here"
```
### 4. Run the app
```
streamlit run Home.py
```

## 📁 Project Structure
```
Profsistant/
├── app.py                       # Search + summarize papers
├── pages/
│   ├── 1_ReadingList.py       # Reading list manager
│   ├── 2_Planner.py           # Planner + calendar export
│   ├── 3_Dashboard.py         # Stats and filters
│   └── 4_ResearchIdeas.py    # Gemini gap generator + ideas list
├── .streamlit/
│   └── secrets.toml              # API keys (never commit!)
└── README.md
```
## 💡 Why Use Profsistant?
Academic research is overwhelming — too many papers, too little structure. Profsistant bridges that gap by helping you:

* Stay focused on a goal

* Build a reading plan around your schedule

* Discover promising research directions faster

Whether you're starting a term paper, thesis, or capstone, Profsistant can help you take the first confident step.

## 🧪 Roadmap (Coming Soon)
* 🔍 PDF upload + summarizer

* 🔁 Notion export integration

* 🧠 Topic clustering + similarity view

*👥 Team mode for lab groups

## 🙌 Credits
Built with ❤️ by @Namslay26

🛡️ License
MIT License. Feel free to fork and build on it!
```
---
Let me know if you'd like:
- A `requirements.txt` auto-generated from your code
- GitHub topics or description text
- A logo/banner for your project
```
Happy pushing to GitHub! 🚀
