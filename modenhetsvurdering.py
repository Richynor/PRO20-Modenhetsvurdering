import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import json
import base64
from io import BytesIO
import sqlite3
import os
from pathlib import Path

# ============================================================================
# KONFIGURASJON
# ============================================================================
st.set_page_config(
    page_title="Gevinstrealisering - Modenhetsvurdering",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database path
DB_PATH = "modenhetsvurdering.db"

# ============================================================================
# DATABASE FUNKSJONER
# ============================================================================
def init_database():
    """Initialiser SQLite database for lagring av intervjuer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabell for prosjekter
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabell for intervjuer
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            interviewer_name TEXT,
            interviewee_name TEXT,
            interviewee_role TEXT,
            interview_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    
    # Tabell for svar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER,
            phase TEXT,
            question_id INTEGER,
            score INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (interview_id) REFERENCES interviews (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_projects():
    """Hent alle prosjekter"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM projects ORDER BY created_at DESC", conn)
    conn.close()
    return df

def create_project(name, description=""):
    """Opprett nytt prosjekt"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO projects (name, description) VALUES (?, ?)", (name, description))
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id

def delete_project(project_id):
    """Slett prosjekt og tilhørende data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM responses WHERE interview_id IN (SELECT id FROM interviews WHERE project_id = ?)", (project_id,))
    cursor.execute("DELETE FROM interviews WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def get_interviews(project_id):
    """Hent alle intervjuer for et prosjekt"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM interviews WHERE project_id = ? ORDER BY interview_date DESC", 
        conn, 
        params=(project_id,)
    )
    conn.close()
    return df

def create_interview(project_id, interviewer_name, interviewee_name, interviewee_role, interview_date, notes=""):
    """Opprett nytt intervju"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO interviews (project_id, interviewer_name, interviewee_name, interviewee_role, interview_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, interviewer_name, interviewee_name, interviewee_role, interview_date, notes))
    interview_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return interview_id

def delete_interview(interview_id):
    """Slett intervju og tilhørende svar"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM responses WHERE interview_id = ?", (interview_id,))
    cursor.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
    conn.commit()
    conn.close()

def save_response(interview_id, phase, question_id, score, notes=""):
    """Lagre eller oppdater et svar"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sjekk om svar allerede eksisterer
    cursor.execute("""
        SELECT id FROM responses 
        WHERE interview_id = ? AND phase = ? AND question_id = ?
    """, (interview_id, phase, question_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE responses SET score = ?, notes = ? 
            WHERE interview_id = ? AND phase = ? AND question_id = ?
        """, (score, notes, interview_id, phase, question_id))
    else:
        cursor.execute("""
            INSERT INTO responses (interview_id, phase, question_id, score, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (interview_id, phase, question_id, score, notes))
    
    conn.commit()
    conn.close()

def get_responses(interview_id):
    """Hent alle svar for et intervju"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM responses WHERE interview_id = ?", 
        conn, 
        params=(interview_id,)
    )
    conn.close()
    return df

def get_aggregated_responses(project_id):
    """Hent aggregerte svar (gjennomsnitt) for et prosjekt"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT 
            r.phase,
            r.question_id,
            AVG(r.score) as avg_score,
            MIN(r.score) as min_score,
            MAX(r.score) as max_score,
            COUNT(r.score) as response_count,
            GROUP_CONCAT(r.notes, ' | ') as all_notes
        FROM responses r
        JOIN interviews i ON r.interview_id = i.id
        WHERE i.project_id = ? AND r.score > 0
        GROUP BY r.phase, r.question_id
    """, conn, params=(project_id,))
    conn.close()
    return df

# ============================================================================
# SPØRSMÅLSDATA (forkortet for lesbarhet - bruk original phases_data)
# ============================================================================
phases_data = {
    "Planlegging": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring og gevinstdata",
            "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster?",
            "scale": [
                "Nivå 1: Ingen læring fra tidligere arbeid anvendt.",
                "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.",
                "Nivå 3: Læring inkludert i planlegging for enkelte områder.",
                "Nivå 4: Systematisk bruk av tidligere gevinstdata i planlegging og estimering.",
                "Nivå 5: Kontinuerlig læring integrert i planleggingsprosessen og gevinststrategien."
            ]
        },
        {
            "id": 2,
            "title": "Strategisk retning og gevinstforståelse",
            "question": "Hvilke gevinster arbeider dere med, og hvorfor er de viktige for organisasjonens strategiske mål?",
            "scale": [
                "Nivå 1: Gevinster er vagt definert, uten tydelig kobling til strategi.",
                "Nivå 2: Gevinster er identifisert, men mangler klare kriterier og prioritering.",
                "Nivå 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerhet.",
                "Nivå 4: Gevinster er tydelig koblet til strategiske mål med konkrete måltall.",
                "Nivå 5: Gevinster er fullt integrert i styringssystemet og brukes i beslutninger."
            ]
        },
        {
            "id": 3,
            "title": "Gevinstkart og visualisering",
            "question": "Er gevinstene synliggjort i gevinstkartet, med tydelig sammenheng mellom tiltak, effekter og mål?",
            "scale": [
                "Nivå 1: Gevinstkart finnes ikke eller er utdatert.",
                "Nivå 2: Et foreløpig gevinstkart eksisterer, men dekker ikke hele området.",
                "Nivå 3: Kartet inkluderer hovedgevinster, men mangler validering og detaljer.",
                "Nivå 4: Kartet er brukt aktivt i planlegging og oppfølging.",
                "Nivå 5: Gevinstkartet oppdateres kontinuerlig og er integrert i styringsdialoger."
            ]
        },
        {
            "id": 4,
            "title": "Strategisk kobling og KPI-er",
            "question": "Er gevinstene tydelig knyttet til strategiske mål og eksisterende KPI-er?",
            "scale": [
                "Nivå 1: Ingen kobling mellom gevinster og strategi eller KPI-er.",
                "Nivå 2: Kobling er antatt, men ikke dokumentert.",
                "Nivå 3: Kobling er etablert for enkelte KPI-er, men ikke konsistent.",
                "Nivå 4: Tydelig kobling mellom gevinster og relevante KPI-er.",
                "Nivå 5: Koblingen følges opp i styringssystem og rapportering."
            ]
        },
        {
            "id": 5,
            "title": "Avgrensning av programgevinst",
            "question": "Er det tydelig avklart hvilke effekter som stammer fra programmet versus andre tiltak eller økte rammer?",
            "scale": [
                "Nivå 1: Ingen skille mellom program- og eksterne effekter.",
                "Nivå 2: Delvis omtalt, men uklart hva som er innenfor programmet.",
                "Nivå 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.",
                "Nivå 4: Avgrensning er dokumentert og anvendt i beregninger.",
                "Nivå 5: Effektisolering er standard praksis og brukes systematisk."
            ]
        },
        {
            "id": 6,
            "title": "Nullpunkter og estimater",
            "question": "Er nullpunkter og estimater etablert, testet og dokumentert på en konsistent og troverdig måte?",
            "scale": [
                "Nivå 1: Nullpunkter mangler eller bygger på uprøvde antagelser.",
                "Nivå 2: Enkelte nullpunkter finnes, men uten felles metode.",
                "Nivå 3: Nullpunkter og estimater er definert, men med høy usikkerhet.",
                "Nivå 4: Nullpunkter og estimater er basert på testede data og validerte metoder.",
                "Nivå 5: Nullpunkter og estimater kvalitetssikres jevnlig og brukes aktivt til læring."
            ]
        },
        {
            "id": 7,
            "title": "Hypotesetesting og datagrunnlag",
            "question": "Finnes formell prosess for hypotesetesting på representative caser?",
            "scale": [
                "Nivå 1: Ikke etablert/uklart; ingen dokumenterte praksiser.",
                "Nivå 2: Delvis definert; uformell praksis uten forankring/validering.",
                "Nivå 3: Etablert for deler av området; variabel kvalitet.",
                "Nivå 4: Godt forankret og systematisk anvendt; måles og følges opp.",
                "Nivå 5: Fullt integrert i styring; kontinuerlig forbedring og læring."
            ]
        },
        {
            "id": 8,
            "title": "Interessentengasjement",
            "question": "Ble relevante interessenter involvert i utarbeidelsen av gevinstgrunnlag?",
            "scale": [
                "Nivå 1: Ingen involvering av interessenter.",
                "Nivå 2: Begrenset og ustrukturert involvering.",
                "Nivå 3: Bred deltakelse, men uten systematisk prosess.",
                "Nivå 4: Systematisk og koordinert involvering med klar rollefordeling.",
                "Nivå 5: Kontinuerlig engasjement med dokumentert medvirkning."
            ]
        },
        {
            "id": 9,
            "title": "Gevinstforutsetninger",
            "question": "Er alle vesentlige forutsetninger ivaretatt for å muliggjøre gevinstrealisering?",
            "scale": [
                "Nivå 1: Ingen kartlegging av gevinstforutsetninger.",
                "Nivå 2: Noen forutsetninger er identifisert, men ikke systematisk dokumentert.",
                "Nivå 3: Hovedforutsetninger er dokumentert, men uten klar eierskap.",
                "Nivå 4: Alle kritiske forutsetninger er kartlagt med tildelt ansvar.",
                "Nivå 5: Gevinstforutsetninger er integrert i risikostyring og oppfølges kontinuerlig."
            ]
        },
        {
            "id": 10,
            "title": "Eierskap og ansvar",
            "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?",
            "scale": [
                "Nivå 1: Ansvar er uklart eller mangler.",
                "Nivå 2: Ansvar er delvis definert, men ikke praktisert.",
                "Nivå 3: Ansvar er kjent, men samhandling varierer.",
                "Nivå 4: Roller og ansvar fungerer godt i praksis.",
                "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."
            ]
        }
    ],
    "Gjennomføring": [
        {
            "id": 1,
            "title": "Bruk av tidligere læring",
            "question": "Hvordan brukes erfaringer fra tidligere prosjekter til å justere tiltak under gjennomføringen?",
            "scale": [
                "Nivå 1: Ingen læring anvendt under gjennomføring.",
                "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.",
                "Nivå 3: Læring inkludert for enkelte områder.",
                "Nivå 4: Systematisk bruk av tidligere gevinstdata for justering.",
                "Nivå 5: Kontinuerlig læring integrert i gjennomføringsprosessen."
            ]
        },
        {
            "id": 2,
            "title": "Oppfølging av gevinster",
            "question": "Hvordan følges gevinstene opp under gjennomføring?",
            "scale": [
                "Nivå 1: Ingen oppfølging av gevinster.",
                "Nivå 2: Sporadisk oppfølging uten struktur.",
                "Nivå 3: Regelmessig oppfølging for hovedgevinster.",
                "Nivå 4: Systematisk oppfølging med rapportering.",
                "Nivå 5: Integrert oppfølging i alle beslutningsprosesser."
            ]
        },
        {
            "id": 3,
            "title": "Justering av planer",
            "question": "Hvordan justeres gevinstrealiseringsplanen basert på erfaringer?",
            "scale": [
                "Nivå 1: Planen justeres ikke.",
                "Nivå 2: Store avvik fører til ad hoc justering.",
                "Nivå 3: Regelmessig revisjon av planen.",
                "Nivå 4: Dynamisk tilpasning basert på måleresultater.",
                "Nivå 5: Kontinuerlig forbedring integrert i styringsprosessen."
            ]
        },
        {
            "id": 4,
            "title": "Interessentengasjement",
            "question": "Hvordan opprettholdes interessentengasjement under gjennomføring?",
            "scale": [
                "Nivå 1: Interessentengasjement avtar.",
                "Nivå 2: Begrenset engasjement for viktige beslutninger.",
                "Nivå 3: Regelmessig engasjement for større endringer.",
                "Nivå 4: Systematisk interessentoppfølging.",
                "Nivå 5: Kontinuerlig dialog og samskaping."
            ]
        },
        {
            "id": 5,
            "title": "Risikohåndtering",
            "question": "Hvordan håndteres risikoer som kan påvirke gevinstene?",
            "scale": [
                "Nivå 1: Risikoer identifiseres ikke.",
                "Nivå 2: Store risikoer håndteres reaktivt.",
                "Nivå 3: Systematisk identifisering av risikoer.",
                "Nivå 4: Proaktiv risikohåndtering med tiltak.",
                "Nivå 5: Risikostyring integrert i gevinstarbeidet."
            ]
        }
    ],
    "Realisering": [
        {
            "id": 1,
            "title": "Gevinstuttak",
            "question": "Hvordan sikres faktisk uttak av planlagte gevinster?",
            "scale": [
                "Nivå 1: Ingen systematisk gevinstuttak.",
                "Nivå 2: Enkelte gevinster tas ut ad hoc.",
                "Nivå 3: Planlagt uttak for hovedgevinster.",
                "Nivå 4: Systematisk uttak med oppfølging.",
                "Nivå 5: Full integrasjon av gevinstuttak i drift."
            ]
        },
        {
            "id": 2,
            "title": "Måling og dokumentasjon",
            "question": "Hvordan måles og dokumenteres realiserte gevinster?",
            "scale": [
                "Nivå 1: Ingen måling eller dokumentasjon.",
                "Nivå 2: Sporadisk måling uten struktur.",
                "Nivå 3: Regelmessig måling for hovedgevinster.",
                "Nivå 4: Systematisk måling og rapportering.",
                "Nivå 5: Integrert måling i styringssystemet."
            ]
        },
        {
            "id": 3,
            "title": "Bærekraft i gevinster",
            "question": "Hvordan sikres at gevinstene opprettholdes over tid?",
            "scale": [
                "Nivå 1: Ingen fokus på bærekraft.",
                "Nivå 2: Begrenset oppfølging av bærekraft.",
                "Nivå 3: Plan for å opprettholde gevinster.",
                "Nivå 4: Systematisk arbeid med bærekraft.",
                "Nivå 5: Bærekraft integrert i organisasjonskulturen."
            ]
        },
        {
            "id": 4,
            "title": "Kommunikasjon av resultater",
            "question": "Hvordan kommuniseres realiserte gevinster?",
            "scale": [
                "Nivå 1: Ingen kommunikasjon av resultater.",
                "Nivå 2: Begrenset kommunikasjon til utvalgte.",
                "Nivå 3: Regelmessig kommunikasjon om resultater.",
                "Nivå 4: Systematisk kommunikasjon til alle interessenter.",
                "Nivå 5: Transparent og kontinuerlig kommunikasjon."
            ]
        },
        {
            "id": 5,
            "title": "Læring og forbedring",
            "question": "Hvordan brukes erfaringer til læring og forbedring?",
            "scale": [
                "Nivå 1: Ingen systematisk læring.",
                "Nivå 2: Enkelte erfaringer deles uformelt.",
                "Nivå 3: Regelmessig erfaringsdeling.",
                "Nivå 4: Systematisk læring og forbedring.",
                "Nivå 5: Læring integrert i organisasjonens kunnskapsbase."
            ]
        }
    ],
    "Realisert": [
        {
            "id": 1,
            "title": "Evaluering av resultater",
            "question": "Hvordan evalueres de endelige resultatene mot planlagte gevinster?",
            "scale": [
                "Nivå 1: Ingen evaluering gjennomført.",
                "Nivå 2: Begrenset evaluering av utvalgte gevinster.",
                "Nivå 3: Systematisk evaluering av hovedgevinster.",
                "Nivå 4: Omfattende evaluering med analyse.",
                "Nivå 5: Full evaluering integrert i porteføljestyring."
            ]
        },
        {
            "id": 2,
            "title": "Dokumentasjon av læring",
            "question": "Hvordan dokumenteres og deles læring for fremtidige prosjekter?",
            "scale": [
                "Nivå 1: Ingen dokumentasjon av læring.",
                "Nivå 2: Enkelte erfaringer dokumentert.",
                "Nivå 3: Systematisk dokumentasjon av læring.",
                "Nivå 4: Læring deles aktivt i organisasjonen.",
                "Nivå 5: Læring integrert i metodeverk og opplæring."
            ]
        },
        {
            "id": 3,
            "title": "Langsiktig oppfølging",
            "question": "Hvordan følges gevinstene opp på lang sikt?",
            "scale": [
                "Nivå 1: Ingen langsiktig oppfølging.",
                "Nivå 2: Sporadisk oppfølging.",
                "Nivå 3: Planlagt oppfølging over tid.",
                "Nivå 4: Systematisk langsiktig oppfølging.",
                "Nivå 5: Integrert i virksomhetsstyringen."
            ]
        },
        {
            "id": 4,
            "title": "Bidrag til organisasjonsutvikling",
            "question": "Hvordan har gevinstarbeidet bidratt til organisasjonens utvikling?",
            "scale": [
                "Nivå 1: Ingen synlig bidrag.",
                "Nivå 2: Begrenset bidrag til enkelte områder.",
                "Nivå 3: Merkbart bidrag til utvikling.",
                "Nivå 4: Betydelig bidrag til organisasjonsutvikling.",
                "Nivå 5: Gevinstarbeid driver organisasjonsutviklingen."
            ]
        },
        {
            "id": 5,
            "title": "Strategisk verdiskapning",
            "question": "Hvordan har gevinstene bidratt til strategisk verdiskapning?",
            "scale": [
                "Nivå 1: Ingen synlig strategisk verdi.",
                "Nivå 2: Begrenset strategisk verdi.",
                "Nivå 3: Merkbar strategisk verdiskapning.",
                "Nivå 4: Betydelig strategisk verdiskapning.",
                "Nivå 5: Gevinster er sentrale for strategisk suksess."
            ]
        }
    ]
}

# ============================================================================
# STYLING
# ============================================================================
def apply_custom_css():
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
        
        /* Global font */
        html, body, [class*="css"] {
            font-family: 'Source Sans Pro', sans-serif;
        }
        
        /* Main header */
        .main-header {
            font-size: 2.2rem;
            color: #172141;
            text-align: center;
            margin-bottom: 0.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .sub-header {
            font-size: 1rem;
            color: #0053A6;
            text-align: center;
            margin-bottom: 1.5rem;
            font-weight: 400;
        }
        
        /* Phase header */
        .phase-header {
            color: #172141;
            border-bottom: 3px solid #64C8FA;
            padding-bottom: 0.5rem;
            margin-top: 1.5rem;
            font-weight: 600;
            font-size: 1.4rem;
        }
        
        /* Cards */
        .metric-card {
            background: linear-gradient(135deg, #F2FAFD 0%, #ffffff 100%);
            padding: 1.2rem;
            border-radius: 12px;
            border-left: 4px solid #0053A6;
            box-shadow: 0 2px 8px rgba(0, 83, 166, 0.1);
            margin: 0.5rem 0;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #172141;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #64C8FA 0%, #35DE6D 100%);
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #0053A6 0%, #172141 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 6px rgba(0, 83, 166, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 83, 166, 0.4);
        }
        
        /* Info boxes */
        .info-box {
            background: linear-gradient(135deg, #C4EFFF 0%, #F2FAFD 100%);
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 4px solid #64C8FA;
            margin: 1rem 0;
            font-size: 0.95rem;
        }
        
        .success-box {
            background: linear-gradient(135deg, #DDFAE2 0%, #F2FAFD 100%);
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 4px solid #35DE6D;
            margin: 1rem 0;
        }
        
        .warning-box {
            background: linear-gradient(135deg, rgba(255, 160, 64, 0.15) 0%, #F2FAFD 100%);
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 4px solid #FFA040;
            margin: 1rem 0;
        }
        
        /* Expander styling */
        .stExpander {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            margin: 0.5rem 0;
            overflow: hidden;
        }
        
        .stExpander > div:first-child {
            background: #F2FAFD;
            border-bottom: 1px solid #e0e0e0;
        }
        
        /* Score indicators */
        .score-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        .score-1, .score-2 { background: #FFE5E5; color: #D32F2F; }
        .score-3 { background: #FFF3E0; color: #F57C00; }
        .score-4 { background: #E3F2FD; color: #1976D2; }
        .score-5 { background: #E8F5E9; color: #388E3C; }
        
        /* Table styling */
        .dataframe {
            font-size: 0.9rem;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #F2FAFD;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #F2FAFD;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            font-weight: 600;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0053A6;
            color: white;
        }
        
        /* Radio buttons */
        .stRadio > div {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .stRadio > div > label {
            background: #F2FAFD;
            padding: 8px 16px;
            border-radius: 20px;
            border: 2px solid #e0e0e0;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .stRadio > div > label:hover {
            border-color: #64C8FA;
        }
        
        /* Selectbox */
        .stSelectbox > div > div {
            background-color: #F2FAFD;
            border-radius: 8px;
        }
        
        /* Text area */
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #64C8FA;
            box-shadow: 0 0 0 2px rgba(100, 200, 250, 0.2);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        </style>
    """, unsafe_allow_html=True)

# ============================================================================
# HJELPEFUNKSJONER
# ============================================================================
def get_score_color(score):
    """Returner farge basert på score"""
    if score >= 4.5:
        return "#35DE6D"
    elif score >= 3.5:
        return "#64C8FA"
    elif score >= 2.5:
        return "#FFA040"
    else:
        return "#FF6B6B"

def get_score_badge(score):
    """Returner HTML badge for score"""
    if score >= 4.5:
        return f'<span class="score-badge score-5">{score:.1f}</span>'
    elif score >= 3.5:
        return f'<span class="score-badge score-4">{score:.1f}</span>'
    elif score >= 2.5:
        return f'<span class="score-badge score-3">{score:.1f}</span>'
    else:
        return f'<span class="score-badge score-1">{score:.1f}</span>'

def create_radar_chart(data, title="Modenhetsoversikt"):
    """Lag radardiagram"""
    categories = list(data.keys())
    values = list(data.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(100, 200, 250, 0.3)',
        line=dict(color='#0053A6', width=3),
        name='Modenhet'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5'],
                gridcolor='#C4EFFF',
                linecolor='#64C8FA'
            ),
            angularaxis=dict(
                gridcolor='#C4EFFF',
                linecolor='#64C8FA'
            ),
            bgcolor='#F2FAFD'
        ),
        showlegend=False,
        title=dict(
            text=title,
            font=dict(size=16, color='#172141')
        ),
        height=400,
        margin=dict(l=80, r=80, t=60, b=60),
        paper_bgcolor='white',
        plot_bgcolor='#F2FAFD'
    )
    
    return fig

def create_bar_chart(data, title="Score per fase"):
    """Lag søylediagram"""
    categories = list(data.keys())
    values = list(data.values())
    colors = [get_score_color(v) for v in values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.1f}' for v in values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#172141')),
        xaxis_title="",
        yaxis_title="Score",
        yaxis=dict(range=[0, 5.5], gridcolor='#e0e0e0'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=350
    )
    
    return fig

def create_comparison_chart(interviews_data, question_titles):
    """Lag sammenligningsdiagram for flere intervjuer"""
    fig = go.Figure()
    
    for interview_name, scores in interviews_data.items():
        fig.add_trace(go.Scatterpolar(
            r=list(scores.values()),
            theta=list(scores.keys()),
            name=interview_name,
            fill='toself',
            opacity=0.6
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5])
        ),
        showlegend=True,
        title="Sammenligning av intervjuer",
        height=500
    )
    
    return fig

def export_to_json(project_id, project_name):
    """Eksporter prosjektdata til JSON"""
    interviews = get_interviews(project_id)
    
    export_data = {
        "project_name": project_name,
        "export_date": datetime.now().isoformat(),
        "interviews": []
    }
    
    for _, interview in interviews.iterrows():
        responses = get_responses(interview['id'])
        interview_data = {
            "interviewer": interview['interviewer_name'],
            "interviewee": interview['interviewee_name'],
            "role": interview['interviewee_role'],
            "date": str(interview['interview_date']),
            "responses": []
        }
        
        for _, response in responses.iterrows():
            interview_data["responses"].append({
                "phase": response['phase'],
                "question_id": response['question_id'],
                "score": response['score'],
                "notes": response['notes']
            })
        
        export_data["interviews"].append(interview_data)
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def import_from_json(json_data, project_id):
    """Importer data fra JSON til eksisterende prosjekt"""
    data = json.loads(json_data)
    
    for interview in data.get("interviews", []):
        interview_id = create_interview(
            project_id=project_id,
            interviewer_name=interview.get("interviewer", "Ukjent"),
            interviewee_name=interview.get("interviewee", "Ukjent"),
            interviewee_role=interview.get("role", ""),
            interview_date=interview.get("date", datetime.now().date()),
            notes=""
        )
        
        for response in interview.get("responses", []):
            save_response(
                interview_id=interview_id,
                phase=response["phase"],
                question_id=response["question_id"],
                score=response["score"],
                notes=response.get("notes", "")
            )
    
    return True

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def main():
    # Initialiser database
    init_database()
    
    # Apply CSS
    apply_custom_css()
    
    # Logo og header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("bane_nor_logo.png.jpg", width=200)
        except:
            st.markdown("### 🚂 Bane NOR")
    
    st.markdown('<h1 class="main-header">Modenhetsvurdering</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gevinstrealisering | Systematisk vurdering på tvers av prosjekter</p>', unsafe_allow_html=True)
    
    # Hovednavigasjon med tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Prosjekter", 
        "🎤 Intervju", 
        "📊 Resultater", 
        "⚙️ Innstillinger"
    ])
    
    # ========================================================================
    # TAB 1: PROSJEKTOVERSIKT
    # ========================================================================
    with tab1:
        st.markdown('<h2 class="phase-header">Prosjektoversikt</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Eksisterende prosjekter")
            projects = get_projects()
            
            if projects.empty:
                st.markdown('<div class="info-box">Ingen prosjekter opprettet ennå. Opprett et nytt prosjekt for å starte.</div>', unsafe_allow_html=True)
            else:
                for _, project in projects.iterrows():
                    interviews = get_interviews(project['id'])
                    agg_data = get_aggregated_responses(project['id'])
                    
                    avg_score = agg_data['avg_score'].mean() if not agg_data.empty else 0
                    
                    with st.expander(f"📁 {project['name']} ({len(interviews)} intervjuer)", expanded=False):
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        
                        with col_a:
                            st.write(f"**Beskrivelse:** {project['description'] or 'Ingen beskrivelse'}")
                            st.write(f"**Opprettet:** {project['created_at'][:10]}")
                            st.write(f"**Antall intervjuer:** {len(interviews)}")
                        
                        with col_b:
                            if avg_score > 0:
                                st.markdown(f"**Gjennomsnitt:**")
                                st.markdown(get_score_badge(avg_score), unsafe_allow_html=True)
                        
                        with col_c:
                            if st.button("🗑️ Slett", key=f"del_{project['id']}"):
                                delete_project(project['id'])
                                st.rerun()
                        
                        if not interviews.empty:
                            st.markdown("---")
                            st.markdown("**Intervjuer:**")
                            for _, interview in interviews.iterrows():
                                st.write(f"• {interview['interviewee_name']} ({interview['interviewee_role']}) - {interview['interview_date']}")
        
        with col2:
            st.markdown("### Opprett nytt prosjekt")
            with st.form("new_project_form"):
                project_name = st.text_input("Prosjektnavn *", placeholder="F.eks. ERTMS Østlandet")
                project_desc = st.text_area("Beskrivelse", placeholder="Kort beskrivelse av prosjektet...", height=100)
                
                if st.form_submit_button("➕ Opprett prosjekt", use_container_width=True):
                    if project_name:
                        create_project(project_name, project_desc)
                        st.success(f"Prosjekt '{project_name}' opprettet!")
                        st.rerun()
                    else:
                        st.error("Prosjektnavn er påkrevd")
    
    # ========================================================================
    # TAB 2: INTERVJU
    # ========================================================================
    with tab2:
        st.markdown('<h2 class="phase-header">Gjennomfør intervju</h2>', unsafe_allow_html=True)
        
        projects = get_projects()
        
        if projects.empty:
            st.warning("Opprett et prosjekt først under 'Prosjekter'-fanen.")
        else:
            # Velg prosjekt
            project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for _, p in projects.iterrows()}
            selected_project = st.selectbox("Velg prosjekt", options=list(project_options.keys()))
            project_id = project_options[selected_project]
            
            st.markdown("---")
            
            # Opprett nytt intervju eller velg eksisterende
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Nytt intervju")
                with st.form("new_interview_form"):
                    interviewer = st.text_input("Intervjuer", placeholder="Ditt navn")
                    interviewee = st.text_input("Intervjuobjekt *", placeholder="Navn på den som intervjues")
                    role = st.text_input("Rolle/stilling", placeholder="F.eks. Prosjektleder, Gevinsteier")
                    interview_date = st.date_input("Dato", value=datetime.now())
                    
                    if st.form_submit_button("🎤 Start intervju", use_container_width=True):
                        if interviewee:
                            interview_id = create_interview(
                                project_id=project_id,
                                interviewer_name=interviewer,
                                interviewee_name=interviewee,
                                interviewee_role=role,
                                interview_date=interview_date
                            )
                            st.session_state['active_interview_id'] = interview_id
                            st.success(f"Intervju opprettet! ID: {interview_id}")
                            st.rerun()
                        else:
                            st.error("Navn på intervjuobjekt er påkrevd")
            
            with col2:
                st.markdown("### Fortsett eksisterende")
                interviews = get_interviews(project_id)
                
                if not interviews.empty:
                    interview_options = {
                        f"{i['interviewee_name']} ({i['interview_date']})": i['id'] 
                        for _, i in interviews.iterrows()
                    }
                    selected_interview = st.selectbox(
                        "Velg intervju", 
                        options=list(interview_options.keys())
                    )
                    
                    if st.button("📝 Fortsett dette intervjuet", use_container_width=True):
                        st.session_state['active_interview_id'] = interview_options[selected_interview]
                        st.rerun()
                else:
                    st.info("Ingen intervjuer i dette prosjektet ennå.")
            
            # Aktiv intervjuseksjon
            if 'active_interview_id' in st.session_state:
                interview_id = st.session_state['active_interview_id']
                existing_responses = get_responses(interview_id)
                
                st.markdown("---")
                st.markdown(f"### 📋 Intervju #{interview_id}")
                
                # Fasevalg
                selected_phase = st.selectbox(
                    "Velg fase",
                    options=list(phases_data.keys()),
                    key="interview_phase"
                )
                
                # Vis fremdrift for denne fasen
                phase_questions = phases_data[selected_phase]
                answered = existing_responses[
                    (existing_responses['phase'] == selected_phase) & 
                    (existing_responses['score'] > 0)
                ]
                progress = len(answered) / len(phase_questions)
                
                st.progress(progress)
                st.caption(f"{len(answered)} av {len(phase_questions)} spørsmål besvart i denne fasen")
                
                # Spørsmålsvisning
                st.markdown("---")
                
                for question in phase_questions:
                    # Sjekk om allerede besvart
                    existing = existing_responses[
                        (existing_responses['phase'] == selected_phase) & 
                        (existing_responses['question_id'] == question['id'])
                    ]
                    
                    current_score = int(existing['score'].values[0]) if not existing.empty else 0
                    current_notes = existing['notes'].values[0] if not existing.empty and existing['notes'].values[0] else ""
                    
                    status_icon = "✅" if current_score > 0 else "⬜"
                    
                    with st.expander(f"{status_icon} {question['id']}. {question['title']}", expanded=False):
                        st.markdown(f"**Spørsmål:** {question['question']}")
                        
                        st.markdown("**Modenhetsskala:**")
                        for level in question['scale']:
                            st.markdown(f"- {level}")
                        
                        st.markdown("---")
                        
                        # Score input
                        score = st.radio(
                            "Velg modenhetsnivå:",
                            options=[0, 1, 2, 3, 4, 5],
                            index=current_score,
                            key=f"score_{selected_phase}_{question['id']}",
                            horizontal=True,
                            format_func=lambda x: "Ikke vurdert" if x == 0 else f"Nivå {x}"
                        )
                        
                        # Notater
                        notes = st.text_area(
                            "Notater og observasjoner:",
                            value=current_notes,
                            key=f"notes_{selected_phase}_{question['id']}",
                            placeholder="Dokumenter begrunnelse, sitater eller observasjoner...",
                            height=100
                        )
                        
                        # Lagre-knapp
                        if st.button("💾 Lagre svar", key=f"save_{selected_phase}_{question['id']}", use_container_width=True):
                            save_response(interview_id, selected_phase, question['id'], score, notes)
                            st.success("Svar lagret!")
                            st.rerun()
                
                # Avslutt intervju
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Avslutt intervju", use_container_width=True):
                        del st.session_state['active_interview_id']
                        st.success("Intervju avsluttet og lagret!")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Slett intervju", use_container_width=True):
                        delete_interview(interview_id)
                        del st.session_state['active_interview_id']
                        st.warning("Intervju slettet")
                        st.rerun()
    
    # ========================================================================
    # TAB 3: RESULTATER
    # ========================================================================
    with tab3:
        st.markdown('<h2 class="phase-header">Resultater og rapporter</h2>', unsafe_allow_html=True)
        
        projects = get_projects()
        
        if projects.empty:
            st.warning("Ingen prosjekter å vise resultater for.")
        else:
            project_options = {f"{p['name']}": p['id'] for _, p in projects.iterrows()}
            selected_project_name = st.selectbox("Velg prosjekt", options=list(project_options.keys()), key="results_project")
            project_id = project_options[selected_project_name]
            
            interviews = get_interviews(project_id)
            agg_data = get_aggregated_responses(project_id)
            
            if interviews.empty:
                st.info("Ingen intervjuer gjennomført for dette prosjektet ennå.")
            else:
                # Oversiktskort
                col1, col2, col3, col4 = st.columns(4)
                
                total_responses = len(agg_data)
                avg_score = agg_data['avg_score'].mean() if not agg_data.empty else 0
                min_score = agg_data['avg_score'].min() if not agg_data.empty else 0
                max_score = agg_data['avg_score'].max() if not agg_data.empty else 0
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Intervjuer</div>
                            <div class="metric-value">{len(interviews)}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Gjennomsnitt</div>
                            <div class="metric-value" style="color: {get_score_color(avg_score)}">{avg_score:.1f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Laveste</div>
                            <div class="metric-value" style="color: {get_score_color(min_score)}">{min_score:.1f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Høyeste</div>
                            <div class="metric-value" style="color: {get_score_color(max_score)}">{max_score:.1f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Visualiseringer
                if not agg_data.empty:
                    col1, col2 = st.columns(2)
                    
                    # Gjennomsnitt per fase
                    phase_averages = agg_data.groupby('phase')['avg_score'].mean().to_dict()
                    
                    with col1:
                        if len(phase_averages) >= 3:
                            radar_fig = create_radar_chart(phase_averages, "Modenhet per fase (gjennomsnitt)")
                            st.plotly_chart(radar_fig, use_container_width=True)
                        else:
                            st.info("Trenger data fra minst 3 faser for radardiagram")
                    
                    with col2:
                        bar_fig = create_bar_chart(phase_averages, "Gjennomsnittsscore per fase")
                        st.plotly_chart(bar_fig, use_container_width=True)
                    
                    # Detaljert tabell
                    st.markdown("### Detaljerte resultater")
                    
                    # Forbered visningstabell
                    display_data = []
                    for _, row in agg_data.iterrows():
                        phase = row['phase']
                        q_id = row['question_id']
                        
                        # Finn spørsmålstittel
                        q_title = "Ukjent"
                        for q in phases_data.get(phase, []):
                            if q['id'] == q_id:
                                q_title = q['title']
                                break
                        
                        display_data.append({
                            'Fase': phase,
                            'Spørsmål': f"{q_id}. {q_title}",
                            'Gjennomsnitt': round(row['avg_score'], 2),
                            'Min': row['min_score'],
                            'Maks': row['max_score'],
                            'Antall svar': row['response_count']
                        })
                    
                    df_display = pd.DataFrame(display_data)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Forbedringsområder
                    st.markdown("### 🎯 Forbedringsområder (Score < 3)")
                    low_scores = agg_data[agg_data['avg_score'] < 3].sort_values('avg_score')
                    
                    if low_scores.empty:
                        st.markdown('<div class="success-box">Ingen kritiske forbedringsområder identifisert! 🎉</div>', unsafe_allow_html=True)
                    else:
                        for _, row in low_scores.iterrows():
                            phase = row['phase']
                            q_id = row['question_id']
                            q_title = "Ukjent"
                            for q in phases_data.get(phase, []):
                                if q['id'] == q_id:
                                    q_title = q['title']
                                    break
                            
                            st.markdown(f"""
                                <div class="warning-box">
                                    <strong>{phase}</strong> - {q_title}<br>
                                    Score: {get_score_badge(row['avg_score'])} (spredning: {row['min_score']}-{row['max_score']})
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Eksport
                    st.markdown("---")
                    st.markdown("### 📥 Eksporter data")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # JSON eksport
                        json_data = export_to_json(project_id, selected_project_name)
                        st.download_button(
                            "📄 Last ned JSON",
                            data=json_data,
                            file_name=f"modenhet_{selected_project_name}_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    with col2:
                        # CSV eksport
                        csv_data = df_display.to_csv(index=False, sep=';')
                        st.download_button(
                            "📊 Last ned CSV",
                            data=csv_data,
                            file_name=f"modenhet_{selected_project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col3:
                        # Tekstrapport
                        report_text = f"""
MODENHETSVURDERING - {selected_project_name.upper()}
{'='*50}
Generert: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Antall intervjuer: {len(interviews)}

SAMMENDRAG
{'-'*30}
Gjennomsnittlig modenhet: {avg_score:.2f}
Laveste score: {min_score:.1f}
Høyeste score: {max_score:.1f}

SCORE PER FASE
{'-'*30}
"""
                        for phase, score in phase_averages.items():
                            report_text += f"{phase}: {score:.2f}\n"
                        
                        report_text += f"\nFORBEDRINGSOMRÅDER (Score < 3)\n{'-'*30}\n"
                        if low_scores.empty:
                            report_text += "Ingen kritiske forbedringsområder identifisert.\n"
                        else:
                            for _, row in low_scores.iterrows():
                                phase = row['phase']
                                q_id = row['question_id']
                                q_title = "Ukjent"
                                for q in phases_data.get(phase, []):
                                    if q['id'] == q_id:
                                        q_title = q['title']
                                        break
                                report_text += f"- {phase} - {q_title}: {row['avg_score']:.2f}\n"
                        
                        st.download_button(
                            "📝 Last ned rapport",
                            data=report_text,
                            file_name=f"rapport_{selected_project_name}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
    
    # ========================================================================
    # TAB 4: INNSTILLINGER
    # ========================================================================
    with tab4:
        st.markdown('<h2 class="phase-header">Innstillinger og administrasjon</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 Importer data")
            st.markdown("Last opp en tidligere eksportert JSON-fil for å importere data til et prosjekt.")
            
            projects = get_projects()
            if not projects.empty:
                project_options = {f"{p['name']}": p['id'] for _, p in projects.iterrows()}
                target_project = st.selectbox("Målprosjekt", options=list(project_options.keys()), key="import_target")
                
                uploaded_file = st.file_uploader("Velg JSON-fil", type=['json'])
                
                if uploaded_file and st.button("📥 Importer", use_container_width=True):
                    try:
                        json_content = uploaded_file.read().decode('utf-8')
                        import_from_json(json_content, project_options[target_project])
                        st.success("Data importert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Feil ved import: {e}")
            else:
                st.info("Opprett et prosjekt først for å importere data.")
        
        with col2:
            st.markdown("### 🗄️ Database")
            st.markdown("Informasjon om lokal database.")
            
            if os.path.exists(DB_PATH):
                db_size = os.path.getsize(DB_PATH) / 1024  # KB
                st.write(f"**Databasefil:** {DB_PATH}")
                st.write(f"**Størrelse:** {db_size:.1f} KB")
                
                # Last ned database
                with open(DB_PATH, 'rb') as f:
                    st.download_button(
                        "💾 Last ned database-backup",
                        data=f.read(),
                        file_name=f"modenhet_backup_{datetime.now().strftime('%Y%m%d')}.db",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
            
            st.markdown("---")
            st.markdown("### ⚠️ Faresone")
            
            if st.checkbox("Vis slettealternativer"):
                if st.button("🗑️ Slett ALL data", type="secondary"):
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                        st.warning("All data slettet!")
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Om applikasjonen")
        st.markdown("""
        <div class="info-box">
        <strong>Modenhetsvurdering for Gevinstrealisering</strong><br><br>
        Denne applikasjonen støtter systematisk vurdering av modenhet i gevinstarbeid gjennom:
        <ul>
            <li>Prosjektbasert organisering av vurderinger</li>
            <li>Støtte for flere intervjuer per prosjekt</li>
            <li>Automatisk aggregering og gjennomsnitt</li>
            <li>Lokal lagring i SQLite database</li>
            <li>Eksport til JSON, CSV og tekstrapport</li>
        </ul>
        <br>
        <strong>Versjon:</strong> 2.0<br>
        <strong>Utviklet for:</strong> Bane NOR - Konsern Controlling
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
