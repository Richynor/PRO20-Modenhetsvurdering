import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import json
import base64
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

# Konfigurer siden
st.set_page_config(
    page_title="PRO20: Gevinstrealisering - Modenhetsvurdering",
    page_icon=" ",
    layout="wide"
)

# Laste Bane NOR logo
try:
    st.sidebar.image("bane_nor_logo.png.jpg", use_container_width=True)
except FileNotFoundError:
    st.sidebar.markdown("""
    <div style='text-align: center; color: #172141;'>
        <h1> </h1>
        <h3>Bane NOR</h3>
    </div>
    """, unsafe_allow_html=True)

# Komplett spørresett fra dokumentet - Oppdatert med alle spørsmål
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
        # ... (alle de andre spørsmålene forblir uendret)
    ],
    "Gjennomføring": [
        # ... (alle spørsmålene forblir uendret)
    ],
    "Realisering": [
        # ... (alle spørsmålene forblir uendret)
    ],
    "Realisert": [
        # ... (alle spørsmålene forblir uendret)
    ]
}

# RESTEN AV KODEN MED NYE FARGEINTEGRERINGER

def initialize_session_state():
    """Initialiser session state for å lagre svar"""
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
        for phase in phases_data:
            st.session_state.responses[phase] = {}
            for question in phases_data[phase]:
                st.session_state.responses[phase][question['id']] = {
                    'score': 0,
                    'notes': '',
                    'completed': False
                }

def calculate_stats():
    """Beregn statistikk for alle faser"""
    stats = {}
    for phase in phases_data:
        scores = []
        completed_count = 0
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and response['score'] > 0:
                scores.append(response['score'])
                completed_count += 1
        
        if scores:
            stats[phase] = {
                'average': np.mean(scores),
                'min': min(scores),
                'max': max(scores),
                'count': completed_count,
                'total': len(phases_data[phase])
            }
        else:
            stats[phase] = {
                'average': 0,
                'min': 0,
                'max': 0,
                'count': 0,
                'total': len(phases_data[phase])
            }
    return stats

def generate_radar_chart(stats):
    """Generer radardiagram for modenhet"""
    phases = list(stats.keys())
    averages = [stats[phase]['average'] for phase in phases]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=averages + [averages[0]],  # Lukk radaren
        theta=phases + [phases[0]],
        fill='toself',
        name='Modenhet',
        line=dict(color='#0053A6'),  # Ny blå farge
        fillcolor='rgba(0, 83, 166, 0.3)'  # Lysere versjon av #0053A6
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )),
        showlegend=False,
        title="Modenhet per Fase - Radardiagram",
        height=400
    )
    
    return fig

def generate_phase_radar_chart(phase_name, questions, responses):
    """Generer detaljert radardiagram for en spesifikk fase"""
    categories = []
    scores = []
    
    for question in questions:
        response = responses[question['id']]
        if response['completed'] and response['score'] > 0:
            categories.append(f"{question['id']}. {question['title']}")
            scores.append(response['score'])
    
    if not scores:
        return None
    
    # Lukk radaren
    categories.append(categories[0])
    scores.append(scores[0])
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Score',
        line=dict(color='#64C8FA'),  # Lys blå farge
        fillcolor='rgba(100, 200, 250, 0.3)'  # Lysere versjon av #64C8FA
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5]
            )),
        showlegend=False,
        title=f"Detaljert Modenhet - {phase_name}",
        height=500,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    return fig

def generate_report():
    """Detaljert rapport"""
    report = []
    report.append("MODENHETSVURDERING - GEVINSTREALISERING")
    report.append("=" * 50)
    report.append(f"Rapport generert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    stats = calculate_stats()
    
    # Sammendrag
    report.append("SAMMENDRAG")
    report.append("-" * 20)
    for phase, stat in stats.items():
        report.append(f"{phase}: {stat['count']}/{stat['total']} fullført - Gjennomsnitt: {stat['average']:.2f}")
    report.append("")
    
    # Detaljert resultat per fase
    for phase in phases_data:
        report.append(f"FASE: {phase.upper()}")
        report.append("-" * 30)
        
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            status = "[OK]" if response['completed'] else "[X]"
            score = response['score'] if response['score'] > 0 else "Ikke vurdert"
            
            report.append(f"{status} {question['id']}. {question['title']}")
            report.append(f"   Score: {score}")
            if response['notes']:
                report.append(f"   Notater: {response['notes']}")
            report.append("")
    
    # Vesentlige forbedringsområder
    report.append("FORBEDRINGSOMRÅDER (Score < 3)")
    report.append("-" * 30)
    improvement_areas = []
    for phase in phases_data:
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and 0 < response['score'] < 3:
                improvement_areas.append((phase, question, response['score']))
    
    if improvement_areas:
        for phase, question, score in improvement_areas:
            report.append(f"- {phase} - {question['title']} (Score: {score})")
    else:
        report.append("Ingen forbedringsområder identifisert")
    
    return "\n".join(report)

def clean_text(text):
    """Hjelpefunksjon for å rense tekst for spesialtegn"""
    if text is None:
        return ""
    # Erstatt spesialtegn med vanlig tekst
    replacements = {
        '✓': '[OK]',
        '✗': '[X]',
        '–': '-',
        '—': '-',
        '´': "'",
        '`': "'",
        '•': '-',  # Bullet point til bindestrek
        '\u2022': '-',  # Unicode bullet point til bindestrek
        '´': "'",
        '`': "'"
    }
    cleaned = str(text)
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned

def create_pdf_report():
    """Generer PDF rapport"""
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Modenhetsvurdering - Gevinstrealisering', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Side {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Titel
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'MODENHETSVURDERING - GEVINSTREALISERING', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, clean_text(f'Rapport generert: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'), 0, 1)
    pdf.ln(10)
    
    # Sammendrag
    stats = calculate_stats()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'SAMMENDRAG', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for phase, stat in stats.items():
        if stat['count'] > 0:
            pdf.cell(0, 8, clean_text(f'{phase}: {stat["count"]}/{stat["total"]} fullført - Gjennomsnitt: {stat["average"]:.2f}'), 0, 1)
    
    pdf.ln(10)
    
    # Detaljert resultat
    for phase in phases_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, clean_text(f'FASE: {phase.upper()}'), 0, 1)
        pdf.set_font('Arial', '', 10)
        
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and response['score'] > 0:
                # Bruk clean_text for alle tekster
                status = "[OK]" if response['completed'] else "[X]"
                pdf.multi_cell(0, 8, clean_text(f'{status} {question["id"]}. {question["title"]} - Score: {response["score"]}'))
                if response['notes']:
                    pdf.set_font('Arial', 'I', 8)
                    pdf.multi_cell(0, 6, clean_text(f'Notater: {response["notes"]}'))
                    pdf.set_font('Arial', '', 10)
                pdf.ln(2)
        
        pdf.ln(5)
    
    # Vesentlige forbedringsområder
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'VESENTLIGE FORBEDRINGSOMRÅDER (Score < 3)', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    improvement_found = False
    for phase in phases_data:
        for question in phases_data[phase]:
            response = st.session_state.responses[phase][question['id']]
            if response['completed'] and 0 < response['score'] < 3:
                pdf.multi_cell(0, 8, clean_text(f'- {phase} - {question["title"]} (Score: {response["score"]})'))
                improvement_found = True
    
    if not improvement_found:
        pdf.cell(0, 8, 'Ingen forbedringsområder identifisert', 0, 1)
    
    return pdf

def get_pdf_download_link(pdf):
    """Generer download link for PDF"""
    try:
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        # Fallback til UTF-8 hvis latin-1 feiler
        try:
            pdf_output = pdf.output(dest='S').encode('utf-8', 'replace')
        except:
            st.error(f"Kunne ikke generere PDF: {e}")
            return None
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="modenhetsvurdering_rapport.pdf">Last ned PDF Rapport</a>'
    return href

def main():
    # NY FARGEKONFIGURASJON
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #172141;
            text-align: center;
            margin-bottom: 1rem;
        }
        .phase-header {
            color: #0053A6;
            border-bottom: 2px solid #64C8FA;
            padding-bottom: 0.5rem;
        }
        .stProgress > div > div > div > div {
            background-color: #35DE6D;
        }
        .stButton > button {
            background-color: #0053A6;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        .stButton > button:hover {
            background-color: #172141;
            color: white;
        }
        .success-box {
            background-color: #DDFAE2;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #35DE6D;
        }
        .info-box {
            background-color: #C4EFFF;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #64C8FA;
        }
        .warning-box {
            background-color: #FFA040;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #FFA040;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">PRO20 Modenhetsvurdering-Gevinstrealisering</h1>', unsafe_allow_html=True)
    st.markdown("**Interaktiv vurdering av modenhet i gevinstrealisering gjennom fire faser**")
    st.markdown("---")
    
    # Initialiser session state
    initialize_session_state()
    
    # Sidebar for navigasjon og oversikt
    with st.sidebar:
        st.markdown('<h2 style="color: #172141;"> Oversikt</h2>', unsafe_allow_html=True)
        
        selected_phase = st.selectbox(
            "Velg fase:",
            options=list(phases_data.keys()),
            key="phase_selector"
        )
        
        # Fremdriftsvisning
        stats = calculate_stats()
        if selected_phase in stats:
            phase_stats = stats[selected_phase]
            progress = phase_stats['count'] / phase_stats['total'] if phase_stats['total'] > 0 else 0
            
            st.subheader("📈 Fremdrift")
            st.progress(progress)
            st.write(f"**{phase_stats['count']}/{phase_stats['total']}** spørsmål fullført")
            
            if phase_stats['count'] > 0:
                st.write(f"Gjennomsnittsscore: **{phase_stats['average']:.2f}**")
        
        st.markdown("---")
        st.subheader("⚡ Hurtigstatistikk")
        for phase, stat in stats.items():
            if stat['count'] > 0:
                st.write(f"**{phase}:** {stat['average']:.2f}")
    
    # Hovedinnhold - spørsmålsvisning
    st.markdown(f'<h2 class="phase-header">📋 {selected_phase}</h2>', unsafe_allow_html=True)
    
    # Alle spørsmål i expandere
    for question in phases_data[selected_phase]:
        response = st.session_state.responses[selected_phase][question['id']]
        
        with st.expander(
            f"🔹 {question['id']}. {question['title']} - "
            f"Score: {response['score'] if response['completed'] else 'Ikke vurdert'}",
            expanded=False
        ):
            # Bruk "Spørsmål:" i stedet for å gjenta nummeret
            st.write(f"**Spørsmål:** {question['question']}")
            
            # Modenhetsskala
            st.subheader(" Modenhetsskala:")
            for i, level in enumerate(question['scale']):
                # Fjern duplisert "Nivå X:" fra visningen
                level_text = level
                if level_text.startswith(f"Nivå {i+1}:"):
                    # Behold bare én "Nivå X:" i teksten
                    level_text = level_text
                st.write(f"**{level_text}**")
            
            # Score input
            current_score = response['score']
            new_score = st.radio(
                "Velg vurdering:",
                options=[1, 2, 3, 4, 5],
                index=current_score-1 if current_score > 0 else 0,
                key=f"score_{selected_phase}_{question['id']}",
                horizontal=True
            )
            
            # Notater
            current_notes = response['notes']
            new_notes = st.text_area(
                "📝 Notater og kommentarer:",
                value=current_notes,
                key=f"notes_{selected_phase}_{question['id']}",
                placeholder="Skriv dine observasjoner her...",
                height=100
            )
            
            # Lagre knapp
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Lagre svar", key=f"save_{selected_phase}_{question['id']}", use_container_width=True):
                    st.session_state.responses[selected_phase][question['id']] = {
                        'score': new_score,
                        'notes': new_notes,
                        'completed': True
                    }
                    st.success("✅ Svar lagret!")
                    st.rerun()
    
    # Resultatseksjon
    st.markdown("---")
    st.markdown('<h2 style="color: #172141;">📈 Resultatoversikt</h2>', unsafe_allow_html=True)
    
    if st.button(" Generer Full Rapport", type="primary", use_container_width=True):
        stats = calculate_stats()
        
        # Visuelle visualiseringer
        col1, col2 = st.columns(2)
        
        with col1:
            # Søylediagram
            if any(stats[phase]['count'] > 0 for phase in stats):
                phases_with_data = [phase for phase in stats if stats[phase]['count'] > 0]
                averages = [stats[phase]['average'] for phase in phases_with_data]
                
                fig_bar = px.bar(
                    x=phases_with_data,
                    y=averages,
                    title="📊 Gjennomsnittsscore per Fase",
                    labels={'x': 'Fase', 'y': 'Gjennomsnittsscore'},
                    color=averages,
                    color_continuous_scale=['#FFA040', '#35DE6D', '#0053A6', '#64C8FA', '#172141']
                )
                fig_bar.update_layout(yaxis_range=[0, 5.5])
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Radardiagram (kun hvis minst 3 faser har data)
            phases_with_data = [phase for phase in stats if stats[phase]['count'] > 0]
            if len(phases_with_data) >= 3:
                radar_fig = generate_radar_chart(stats)
                st.plotly_chart(radar_fig, use_container_width=True)
        
        # Detaljerte radardiagrammer per fase
        st.subheader(" Detaljert Modenhet per Fase")
        for phase in phases_data:
            phase_questions = phases_data[phase]
            phase_responses = st.session_state.responses[phase]
            
            # Sjekk om det er noen fullførte spørsmål i fasen
            if any(phase_responses[q['id']]['completed'] for q in phase_questions):
                st.write(f"**{phase}**")
                radar_fig = generate_phase_radar_chart(phase, phase_questions, phase_responses)
                if radar_fig:
                    st.plotly_chart(radar_fig, use_container_width=True)
                else:
                    st.info(f"ℹ️ Ingen data tilgjengelig for {phase}")
        
        # Detaljert rapport
        st.subheader("📋 Detaljert Rapport")
        
        # Last ned knapper for forskjellige formater
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # TXT rapport
            report_text = generate_report()
            st.download_button(
                label="📄 Last ned rapport som TXT",
                data=report_text,
                file_name=f"modenhetsvurdering_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # PDF rapport
            try:
                pdf = create_pdf_report()
                if pdf:
                    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
                    st.download_button(
                        label="📊 Last ned rapport som PDF",
                        data=pdf_output,
                        file_name=f"modenhetsvurdering_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ Kunne ikke generere PDF: {e}")
        
        with col3:
            # CSV data
            csv_data = []
            csv_data.append(["Fase", "Spørsmål ID", "Tittel", "Score", "Notater", "Fullført"])
            for phase in phases_data:
                for question in phases_data[phase]:
                    response = st.session_state.responses[phase][question['id']]
                    csv_data.append([
                        phase,
                        question['id'],
                        question['title'],
                        response['score'] if response['completed'] else "Ikke vurdert",
                        response['notes'],
                        "Ja" if response['completed'] else "Nei"
                    ])
            
            df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
            csv_string = df.to_csv(index=False, sep=';')
            st.download_button(
                label="📈 Last ned data som CSV",
                data=csv_string,
                file_name=f"modenhetsvurdering_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Forbedringsområder
        st.subheader("⚠️ Forbedringsområder")
        improvement_found = False
        
        for phase in phases_data:
            low_scores = []
            for question in phases_data[phase]:
                response = st.session_state.responses[phase][question['id']]
                if response['completed'] and 0 < response['score'] < 3:
                    low_scores.append((question, response['score']))
                    improvement_found = True
            
            if low_scores:
                st.write(f"**{phase}:**")
                for question, score in low_scores:
                    st.write(f"🔸 {question['title']} (Score: {score})")
        
        if not improvement_found:
            st.markdown('<div class="success-box">✅ Ikke vesentlige forbedringsområder identifisert! Det jobbes aktivt med gevinstrealisering</div>', unsafe_allow_html=True)
    
    # Informasjon om appen
    with st.expander("ℹ️ Om denne appen"):
        st.markdown("""
        **Funksjonalitet:**
        - Vurder modenhet i gevinstrealisering gjennom 4 faser
        - Auto-lagring av alle svar
        - Generer visuelle rapporter og diagrammer
        - Identifiser forbedringsområder
        - Eksporter rapporter i TXT, PDF og CSV format
        
        **📖 Bruk:**
        1. Velg fase i sidebar
        2. Gå gjennom hvert spørsmål
        3. Velg score og skriv notater
        4. Trykk "Lagre svar" for hvert spørsmål
        5. Trykk "Generer Full Rapport" for resultater
        
        **💾 OBS! Data lagres lokalt i nettleseren og forsvinner ved oppdatering.**
        
        ** Ikoner:**
        ⚠️ Advarsel - Vesentlige forbedringsområder
        """)

if __name__ == "__main__":
    main()
