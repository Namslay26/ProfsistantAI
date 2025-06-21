# 🧠 Profsistant — Your AI Research Kickoff Assistant

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
