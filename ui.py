import streamlit as st

LIGHT = {"paper":"#E4E8EC","paper_raised":"#EEF1F4","ink":"#1C2733","ink_soft":"#566373","rule":"#BAC5D0","rust":"#3D6C8D","rust_dim":"#9DB9C9","blue":"#5C4B7A"}
DARK = {"paper":"#121A22","paper_raised":"#182029","ink":"#DCE3E9","ink_soft":"#8B9BAA","rule":"#2B3946","rust":"#6FA0C2","rust_dim":"#3A5164","blue":"#8B78AC"}

def init_theme():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"
    if "theme_toggle" not in st.session_state:
        st.session_state.theme_toggle = False

def apply_theme():
    init_theme()
    t = DARK if st.session_state.theme_mode == "dark" else LIGHT
    st.markdown(f"""
    <style>
    :root {{
      --paper:{t['paper']}; --paper-raised:{t['paper_raised']}; --ink:{t['ink']};
      --ink-soft:{t['ink_soft']}; --rule:{t['rule']}; --rust:{t['rust']};
      --rust-dim:{t['rust_dim']}; --blue:{t['blue']};
    }}
    .stApp, [data-testid="stAppViewContainer"] {{ background:var(--paper); color:var(--ink); }}
    [data-testid="stHeader"] {{ background:var(--paper); }}
    [data-testid="stSidebar"] {{ background:var(--paper-raised); border-right:1px solid var(--rule); }}
    [data-testid="stSidebar"] * {{ color:var(--ink) !important; }}
    [data-testid="stSidebarNav"] {{ padding-top:.5rem; }}
    .block-container {{ max-width:1180px; padding-top:2.5rem; padding-bottom:4rem; }}
    h1,h2,h3 {{ color:var(--ink) !important; letter-spacing:-.025em; }}
    p,label,[data-testid="stMarkdownContainer"] {{ color:var(--ink); }}
    .muted {{ color:var(--ink-soft) !important; }}
    .brand-mark {{ display:flex; align-items:center; gap:.65rem; font-weight:800; font-size:1.35rem; color:var(--ink); }}
    .brand-icon {{ width:2rem; height:2rem; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--rule); background:var(--paper); border-radius:.6rem; }}
    .eyebrow {{ color:var(--rust) !important; text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:800; }}
    .hero-title {{ font-size:clamp(2.15rem,5vw,3.8rem); line-height:1.03; margin:.25rem 0 .75rem; }}
    .hero-copy {{ max-width:720px; color:var(--ink-soft) !important; font-size:1.04rem; line-height:1.65; }}
    .section-rule {{ height:1px; background:var(--rule); margin:1.6rem 0; }}
    .research-card,.stat-card,.callout,.task-card {{ background:var(--paper-raised); border:1px solid var(--rule); border-radius:14px; }}
    .research-card {{ padding:1.25rem 1.35rem; margin:.65rem 0 .35rem; }}
    .research-card-title {{ font-size:1.16rem; font-weight:800; line-height:1.35; color:var(--ink) !important; margin-bottom:.4rem; }}
    .meta {{ color:var(--ink-soft) !important; font-size:.86rem; }}
    .chip {{ display:inline-block; padding:.2rem .55rem; margin:.2rem .2rem 0 0; border:1px solid var(--rule); border-radius:999px; color:var(--rust) !important; background:var(--paper); font-size:.74rem; font-weight:750; }}
    .stat-card {{ padding:1rem 1.1rem; min-height:100px; }}
    .stat-number {{ font-size:1.85rem; font-weight:850; color:var(--ink) !important; }}
    .stat-label {{ color:var(--ink-soft) !important; font-size:.82rem; }}
    .callout {{ padding:1.1rem 1.2rem; border-left:4px solid var(--blue); }}
    .task-card {{ padding:1rem 1.15rem; margin:.5rem 0; }}
    a {{ color:var(--rust) !important; }}
    [data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"],[data-baseweb="popover"] > div {{ background:var(--paper-raised) !important; }}
    [data-baseweb="input"] input,[data-baseweb="textarea"] textarea {{ color:var(--ink) !important; }}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {{ border-color:var(--rule) !important; }}
    .stButton > button,.stLinkButton > a {{ border:1px solid var(--rule) !important; background:var(--paper-raised) !important; color:var(--ink) !important; border-radius:9px !important; font-weight:750 !important; }}
    .stButton > button:hover,.stLinkButton > a:hover {{ border-color:var(--rust) !important; color:var(--rust) !important; }}
    .stButton > button[kind="primary"] {{ background:var(--rust) !important; border-color:var(--rust) !important; color:#FFFFFF !important; }}
    [data-testid="stPills"] button,[data-testid="stSegmentedControl"] button {{ border-color:var(--rule) !important; color:var(--ink) !important; background:var(--paper-raised) !important; }}
    [data-testid="stExpander"] {{ border-color:var(--rule) !important; background:var(--paper-raised) !important; border-radius:12px !important; }}
    hr {{ border-color:var(--rule) !important; }}
    </style>
    """, unsafe_allow_html=True)

def sidebar():
    init_theme()
    with st.sidebar:
        st.markdown('<div class="brand-mark"><span class="brand-icon">▣</span> Profsistant</div>', unsafe_allow_html=True)
        st.caption("Your research workspace")
        st.divider()
        current = st.toggle("Dark mode", value=st.session_state.theme_mode == "dark", key="theme_toggle")
        new_mode = "dark" if current else "light"
        if new_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = new_mode
            st.rerun()

def page_header(eyebrow, title, description=None):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{title}</div>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="hero-copy">{description}</div>', unsafe_allow_html=True)

def stat_card(number, label):
    st.markdown(f'<div class="stat-card"><div class="stat-number">{number}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

def chips(labels):
    return " ".join(f'<span class="chip">{x}</span>' for x in labels) if labels else ""
