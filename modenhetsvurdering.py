"""
MODENHETSVURDERING - GEVINSTREALISERING
Gjennomfores i samarbeid med konsern økonomi og digital transformasjon

For PDF-rapporter, installer:
  pip install fpdf2 filelock
"""

# Sjekk om fpdf er tilgjengelig
FPDF_AVAILABLE = False
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    pass

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pickle
import os
from io import BytesIO
import uuid
import shutil

# Filelock er valgfri
FILELOCK_AVAILABLE = False
try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    pass

st.set_page_config(
    page_title="Modenhetsvurdering - Bane NOR",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "modenhet_data.pkl"
LOCK_FILE = "modenhet_data.pkl.lock"
BACKUP_DIR = "backups"

# ============================================================================
# FLERBRUKER-STOTTE
# ============================================================================
def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    return st.session_state.session_id

def get_data_file():
    return DATA_FILE

COLORS = {
    'primary_dark': '#172141',
    'primary': '#0053A6',
    'primary_light': '#64C8FA',
    'success': '#35DE6D',
    'warning': '#FFA040',
    'danger': '#FF6B6B',
    'white': '#FFFFFF',
    'black': '#000000',
    'gray_light': '#F2FAFD',
    'gray': '#E8E8E8'
}

HENSIKT_TEKST = """
### Hensikt
Modenhetsvurderingen har som formål a synliggjøre gode erfaringer og identifisere forbedringsområder i vart arbeid med gevinster. Vi ønsker a lære av hverandre, dele beste praksis og hjelpe initiativer til a lykkes bedre med a skape og realisere gevinster.

Et sentralt fokusomrade er a sikre at gevinstene vi arbeider med er konkrete og realitetsorienterte.

### Hvem inviteres?
Vi ønsker a intervjue alle som har vært eller er involvert i gevinstarbeidet.

### Hva vurderes?
Intervjuene dekker hele gevinstlivssyklusen - fra planlegging og gjennomføring til realisering og evaluering.

### Gevinster i endringsinitiativ
Et endringsinitiativ kan ha flere konkrete gevinster. Intervjuene kan gjennomføres med fokus pa en spesifikk gevinst, eller for initiativet som helhet.
"""

ROLES = {
    "Prosjektleder / Programleder": {
        "description": "Ansvar for overordnet gjennomføring og leveranser",
        "recommended_questions": {
            "Planlegging": [1, 2, 3, 4, 8, 9, 14, 16, 17, 18, 19, 20, 21, 22, 23],
            "Gjennomføring": [1, 2, 3, 4, 6, 8, 9, 14, 16, 17, 18, 19, 20, 21, 22, 23],
            "Realisering": [1, 2, 3, 8, 16, 17, 18, 19, 20, 22, 23],
            "Realisert": [1, 2, 3, 16, 17, 18, 19, 20, 22, 23]
        }
    },
    "Gevinsteier": {
        "description": "Ansvar for at gevinster realiseres i linjen",
        "recommended_questions": {
            "Planlegging": [2, 3, 4, 6, 9, 10, 11, 12, 13, 16, 17, 20, 21],
            "Gjennomføring": [2, 6, 9, 10, 11, 12, 13, 16, 17, 20, 21],
            "Realisering": [1, 2, 3, 6, 8, 9, 10, 11, 12, 13, 16, 17, 20, 21],
            "Realisert": [1, 2, 6, 8, 11, 12, 13, 16, 17, 20, 21]
        }
    },
    "Gevinstansvarlig": {
        "description": "Operativt ansvar for oppfølging og rapportering av gevinster",
        "recommended_questions": {
            "Planlegging": [1, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            "Gjennomføring": [1, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            "Realisering": [1, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            "Realisert": [1, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        }
    },
    "Linjeleder / Mottaker": {
        "description": "Skal ta imot endringer og realisere gevinster i drift",
        "recommended_questions": {
            "Planlegging": [2, 8, 9, 12, 13, 18, 19, 20, 22, 24],
            "Gjennomføring": [2, 8, 9, 12, 13, 17, 18, 19, 20, 22, 24],
            "Realisering": [1, 2, 8, 9, 12, 13, 17, 18, 19, 20, 22, 24],
            "Realisert": [1, 2, 8, 12, 13, 17, 18, 19, 20, 22, 24]
        }
    },
    "Business Case-ansvarlig": {
        "description": "Utarbeidet gevinstgrunnlag og estimater",
        "recommended_questions": {
            "Planlegging": [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 21],
            "Gjennomføring": [1, 5, 6, 7, 10, 11, 14, 15, 21],
            "Realisering": [1, 5, 6, 7, 10, 11, 14, 15],
            "Realisert": [1, 5, 6, 7, 10, 11, 14, 15, 21]
        }
    },
    "Styringsgruppe": {
        "description": "Overordnet ansvar og beslutninger",
        "recommended_questions": {
            "Planlegging": [2, 4, 8, 14, 16, 19, 20, 21, 22, 24],
            "Gjennomføring": [2, 4, 8, 14, 16, 19, 20, 22, 24],
            "Realisering": [2, 4, 8, 16, 19, 20, 22, 24],
            "Realisert": [2, 4, 8, 16, 19, 20, 22, 24]
        }
    },
    "Controller / økonomi": {
        "description": "Oppfølging av økonomiske gevinster",
        "recommended_questions": {
            "Planlegging": [2, 4, 5, 6, 11, 12, 13, 21],
            "Gjennomføring": [2, 5, 6, 11, 12, 13, 21],
            "Realisering": [2, 5, 6, 11, 12, 13, 21],
            "Realisert": [2, 5, 6, 11, 12, 13, 21]
        }
    },
    "Endringsleder": {
        "description": "Ansvar for endringsledelse og kommunikasjon",
        "recommended_questions": {
            "Planlegging": [2, 8, 9, 18, 19, 20, 22, 23, 24],
            "Gjennomføring": [2, 8, 9, 18, 19, 20, 22, 23, 24],
            "Realisering": [1, 2, 8, 9, 18, 19, 20, 22, 23, 24],
            "Realisert": [1, 2, 8, 18, 19, 20, 22, 23, 24]
        }
    },
    "Interessent": {
        "description": "Personer som opplever endringer og effekter i praksis",
        "recommended_questions": {
            "Planlegging": [8, 9, 12, 13, 18, 19, 22, 24],
            "Gjennomføring": [8, 9, 12, 13, 18, 19, 22, 24],
            "Realisering": [8, 9, 12, 13, 18, 19, 20, 22, 24],
            "Realisert": [8, 12, 13, 18, 19, 20, 22, 24]
        }
    }
}

PARAMETERS = {
    "Strategisk forankring": {"description": "Strategisk retning, kobling til mål og KPI-er", "questions": [2, 4]},
    "Gevinstkart og visualisering": {"description": "Gevinstkart, sammenhenger mellom tiltak og effekter", "questions": [3]},
    "Nullpunkter og estimater": {"description": "Kvalitet pa nullpunkter, estimater og datagrunnlag", "questions": [6, 7, 11]},
    "Interessenter og forankring": {"description": "Interessentengasjement, kommunikasjon og forankring", "questions": [8, 19, 24]},
    "Eierskap og ansvar": {"description": "Roller, ansvar og eierskap for gevinstuttak", "questions": [20]},
    "Forutsetninger og risiko": {"description": "Gevinstforutsetninger, risiko og ulemper", "questions": [9, 10, 14, 15]},
    "Gevinstrealiseringsplan": {"description": "Plan som operativt styringsverktøy", "questions": [16, 17]},
    "Effektivitet og produktivitet": {"description": "Måling, disponering og baerekraft", "questions": [12, 13]},
    "læring og forbedring": {"description": "Bruk av tidligere erfaringer og kontinuerlig læring", "questions": [1]},
    "Momentum og tidlig gevinstuttak": {"description": "Bygge momentum gjennom tidlig gevinstrealisering", "questions": [5, 21, 22, 23]}
}

PHASES = ["Planlegging", "Gjennomføring", "Realisering", "Realisert"]

questions_data = {
    "Planlegging": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster?", "scale": ["Niva 1: Ingen læring fra tidligere arbeid anvendt.", "Niva 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.", "Niva 3: læring inkludert i planlegging for enkelte områder.", "Niva 4: Systematisk bruk av tidligere gevinstdata i planlegging og estimering.", "Niva 5: Kontinuerlig læring integrert i planleggingsprosessen og gevinststrategien."]},
        {"id": 2, "title": "Strategisk retning og gevinstforstaelse", "question": "Hvilke gevinster arbeider dere med, og hvorfor er de viktige for organisasjonens strategiske mål?", "scale": ["Niva 1: Gevinster er vagt definert, uten tydelig kobling til strategi.", "Niva 2: Gevinster er identifisert, men mangler klare kriterier og prioritering.", "Niva 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerhet.", "Niva 4: Gevinster er tydelig koblet til strategiske mål med konkrete måltall.", "Niva 5: Gevinster er fullt integrert i styringssystemet og brukes i beslutninger."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Er gevinstene synliggjort i gevinstkartet, med tydelig sammenheng mellom tiltak, effekter og mål?", "scale": ["Niva 1: Gevinstkart finnes ikke eller er utdatert.", "Niva 2: Et foreløpig gevinstkart eksisterer, men dekker ikke hele området.", "Niva 3: Kartet inkluderer hovedgevinster, men mangler validering og detaljer.", "Niva 4: Kartet er brukt aktivt i planlegging og oppfølging.", "Niva 5: Gevinstkartet oppdateres kontinuerlig og er integrert i styringsdialoger."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Er gevinstene tydelig knyttet til strategiske mål og eksisterende KPI-er?", "scale": ["Niva 1: Ingen kobling mellom gevinster og strategi eller KPI-er.", "Niva 2: Kobling er antatt, men ikke dokumentert.", "Niva 3: Kobling er etablert for enkelte KPI-er, men ikke konsistent.", "Niva 4: Tydelig kobling mellom gevinster og relevante KPI-er.", "Niva 5: Koblingen følges opp i styringssystem og rapportering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Er det tydelig avklart hvilke effekter som stammer fra programmet versus andre tiltak eller økte rammer?", "scale": ["Niva 1: Ingen skille mellom program- og eksterne effekter.", "Niva 2: Delvis omtalt, men uklart hva som er innenfor programmet.", "Niva 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.", "Niva 4: Avgrensning er dokumentert og anvendt i beregninger.", "Niva 5: Effektisolering er standard praksis og brukes systematisk."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Er nullpunkter og estimater etablert, testet og dokumentert pa en konsistent og troverdig mate?", "scale": ["Niva 1: Nullpunkter mangler eller bygger pa uprøvde antagelser.", "Niva 2: Enkelte nullpunkter finnes, men uten felles metode.", "Niva 3: Nullpunkter og estimater er definert, men med høy usikkerhet.", "Niva 4: Nullpunkter og estimater er basert pa testede data og validerte metoder.", "Niva 5: Nullpunkter og estimater kvalitetssikres jevnlig og brukes aktivt til læring."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Finnes formell prosess for hypotesetesting pa representative caser?", "scale": ["Niva 1: Ikke etablert/uklart; ingen dokumenterte praksiser.", "Niva 2: Delvis definert; uformell praksis uten forankring/validering.", "Niva 3: Etablert for deler av området; variabel kvalitet.", "Niva 4: Godt forankret og systematisk anvendt; måles og følges opp.", "Niva 5: Fullt integrert i styring; kontinuerlig forbedring og læring."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Ble relevante interessenter involvert i utarbeidelsen av gevinstgrunnlag?", "scale": ["Niva 1: Ingen involvering av interessenter.", "Niva 2: Begrenset og ustrukturert involvering.", "Niva 3: Bred deltakelse, men uten systematisk prosess.", "Niva 4: Systematisk og koordinert involvering med klar rollefordeling.", "Niva 5: Kontinuerlig engasjement med dokumentert medvirkning."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Er alle vesentlige forutsetninger ivaretatt for a muliggjøre gevinstrealisering?", "scale": ["Niva 1: Ingen kartlegging av gevinstforutsetninger.", "Niva 2: Noen forutsetninger er identifisert, men ikke systematisk dokumentert.", "Niva 3: Hovedforutsetninger er dokumentert, men uten klar eierskap.", "Niva 4: Alle kritiske forutsetninger er kartlagt med tildelt ansvar.", "Niva 5: Gevinstforutsetninger er integrert i risikostyring og oppfølges kontinuerlig."]},
        {"id": 10, "title": "Prinsipielle og vilkarsmessige kriterier", "question": "Er forutsetninger og kriterier som pavirker gevinstene tydelig definert og dokumentert?", "scale": ["Niva 1: Ingen kriterier dokumentert.", "Niva 2: Kriterier er beskrevet uformelt.", "Niva 3: Kriterier dokumentert i deler av planverket.", "Niva 4: Vesentlige kriterier er analysert og håndtert i gevinstrealiseringsplanen.", "Niva 5: Kriterier overvakes, følges opp og inngår i risikostyringen."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Er det oppnadd enighet blant nokkelinteressenter om nullpunkter og estimater?", "scale": ["Niva 1: Ingen enighet eller dokumentert praksis.", "Niva 2: Delvis enighet, men ikke formålisert.", "Niva 3: Enighet for hovedestimater, men med reservasjoner.", "Niva 4: Full enighet dokumentert og forankret.", "Niva 5: Kontinuerlig dialog og justering av estimater med interessentene."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert mellom prissatte og ikke-prissatte gevinster?", "scale": ["Niva 1: Ingen plan for disponering eller måling av besparelser.", "Niva 2: Delvis oversikt, men ikke dokumentert eller fulgt opp.", "Niva 3: Plan finnes for enkelte områder, men uten systematikk.", "Niva 4: Disponering og effekter dokumentert og målt.", "Niva 5: Frigjorte ressurser disponeres strategisk og måles som del av gevinstrealiseringen."]},
        {"id": 13, "title": "måling av effektivitet og produktivitet", "question": "Hvordan måles okt effektivitet og produktivitet som folge av besparelser?", "scale": ["Niva 1: Ingen måling av effektivitet eller produktivitet.", "Niva 2: Enkelte målinger, men ikke systematisk.", "Niva 3: måling for enkelte gevinster, men begrenset fokus pa baerekraft.", "Niva 4: Systematisk måling og vurdering av om gevinster opprettholdes over tid.", "Niva 5: måling integrert i gevinstoppfølgingen, baerekraftige gevinster sikres."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Er mulige negative konsekvenser eller ulemper knyttet til operasjonelle forhold identifisert, vurdert og håndtert i planen?", "scale": ["Niva 1: Negative effekter ikke vurdert.", "Niva 2: Kjent, men ikke håndtert.", "Niva 3: Beskrevet, men ikke fulgt opp systematisk.", "Niva 4: håndtert og overvaket med tilpasning til ulike operasjonelle scenarier.", "Niva 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan sikres det at balansen mellom gevinster og ulemper vurderes i styringsdialoger?", "scale": ["Niva 1: Ingen vurdering av balanse.", "Niva 2: Diskuteres uformelt.", "Niva 3: Del av enkelte oppfølgingsmøter.", "Niva 4: Systematisk vurdert i gevinststyring.", "Niva 5: inngår som fast punkt i styrings- og gevinstdialoger."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Er det utarbeidet en forankret gevinstrealiseringsplan som beskriver hvordan gevinstene skal hentes ut og måles?", "scale": ["Niva 1: Ingen formell gevinstrealiseringsplan.", "Niva 2: Utkast til plan finnes, men er ufullstendig.", "Niva 3: Plan er etablert, men ikke validert eller periodisert.", "Niva 4: Planen er forankret, oppdatert og koblet til gevinstkartet.", "Niva 5: Planen brukes aktivt som styringsdokument med revisjon."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan sikres det at gevinstrealiseringsplanen fungerer som en operativ handlingsplan i linjen med tilpasning til ulike strekningsforhold?", "scale": ["Niva 1: Planen brukes ikke som operativt styringsverktoy.", "Niva 2: Plan finnes, men uten operativ oppfølging.", "Niva 3: Planen følges delvis opp i linjen.", "Niva 4: Planen brukes aktivt som handlingsplan og styringsverktoy.", "Niva 5: Gevinstplanen er fullt operativt integrert i linjens handlingsplaner og rapportering med tilpasning til lokale forhold."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Er organisasjonen forberedt og har den tilstrekkelig kapasitet til a ta imot endringer og nye arbeidsformer som folger av programmet?", "scale": ["Niva 1: Ingen plan for endringsberedskap.", "Niva 2: Kapasitet vurderes uformelt, men ikke håndtert.", "Niva 3: Endringskapasitet omtales, men uten konkrete tiltak.", "Niva 4: Tilfredsstillende beredskap etablert og koordinert med linjen.", "Niva 5: Endringskapasitet er strukturert, overvaket og integrert i styring med tilpasning til lokale forhold."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Er gevinstgrunnlag, roller og forventninger godt kommunisert i organisasjonen?", "scale": ["Niva 1: Ingen felles forstaelse eller kommunikasjon.", "Niva 2: Informasjon deles sporadisk.", "Niva 3: Kommunikasjon er planlagt, men ikke systematisk målt.", "Niva 4: Kommunikasjon er systematisk og forankret i organisasjonen.", "Niva 5: Forankring skjer lopende som del av styringsdialog."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Er ansvar og roller tydelig definert for a sikre Gjennomføring og gevinstuttak?", "scale": ["Niva 1: Ansvar er uklart eller mangler.", "Niva 2: Ansvar er delvis definert, men ikke praktisert.", "Niva 3: Ansvar er kjent, men samhandling varierer.", "Niva 4: Roller og ansvar fungerer godt i praksis.", "Niva 5: Sterkt eierskap og kultur for ansvarliggjøring."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Er gevinstrealiseringsplanen periodisert, validert og godkjent av ansvarlige?", "scale": ["Niva 1: Ingen tidsplan eller forankring.", "Niva 2: Tidsplan foreligger, men ikke validert.", "Niva 3: Delvis forankret hos enkelte ansvarlige/eiere.", "Niva 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.", "Niva 5: Planen brukes aktivt i styringsdialog og rapportering."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Opplever dere at gevinstplanen og estimatene oppleves realistiske og engasjerer eierne og interessentene?", "scale": ["Niva 1: Ingen troverdighet eller engasjement.", "Niva 2: Begrenset tillit til estimater.", "Niva 3: Delvis aksept, men varierende engasjement.", "Niva 4: Høy troverdighet og engasjement.", "Niva 5: Sterk troverdighet og aktiv motivasjon i organisasjonen."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan planlegges det for a bygge momentum og realisere tidlige gevinster underveis i programmet?", "scale": ["Niva 1: Ingen plan for tidlig gevinstuttak eller oppbygging av momentum.", "Niva 2: Enkelte uformelle vurderinger av tidlige gevinster.", "Niva 3: Plan for tidlig gevinstuttak er identifisert, men ikke koordinert.", "Niva 4: Strukturert tilnaerming for tidlig gevinstuttak med tildelt ansvar.", "Niva 5: Tidlig gevinstuttak er integrert i programmets DNA og brukes aktivt for a bygge momentum."]},
        {"id": 24, "title": "Enighet og lojalitet til gevinster", "question": "Er det etablert tilstrekkelig enighet og lojalitet til de definerte gevinstene blant berørt personell gjennom endringsledelsesarbeidet?", "scale": ["Niva 1: Ingen systematisk arbeid med a bygge enighet eller lojalitet til gevinstene.", "Niva 2: Begrenset endringsledelsesarbeid - enighet og lojalitet er ikke vurdert.", "Niva 3: Endringsledelse er planlagt, men effekten pa enighet og lojalitet er usikker.", "Niva 4: Systematisk endringsledelse med dokumentert tilslutning fra hovedinteressenter.", "Niva 5: Omfattende endringsledelse har skapt bred enighet og aktiv lojalitet til gevinstene i berørt organisasjon."]}
    ],
    "Gjennomføring": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan brukes erfaringer og læring fra tidligere prosjekter og gevinstarbeid til a justere tiltak under gjennomføringen?", "scale": ["Niva 1: Ingen læring fra tidligere arbeid anvendt under gjennomføring.", "Niva 2: Enkelte erfaringer omtalt, men ikke strukturert brukt for justering.", "Niva 3: læring inkludert i justering for enkelte områder under gjennomføring.", "Niva 4: Systematisk bruk av tidligere gevinstdata for a justere tiltak underveis.", "Niva 5: Kontinuerlig læring integrert i gjennomføringsprosessen og gevinstjustering."]},
        {"id": 2, "title": "Strategisk retning og gevinstforstaelse", "question": "Hvordan opprettholdes den strategiske retningen og forstaelsen av gevinster under gjennomføring?", "scale": ["Niva 1: Strategisk kobling glemmes under gjennomføring.", "Niva 2: Strategi omtales, men ikke operasjonalisert i gjennomføring.", "Niva 3: Strategisk kobling vedlikeholdes i deler av gjennomføringen.", "Niva 4: Tydelig strategisk retning i gjennomføring med regelmessig oppdatering.", "Niva 5: Strategi og gevinstforstaelse dynamisk tilpasses underveis basert pa læring."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Hvordan brukes gevinstkartet aktivt under gjennomføring for a styre og kommunisere fremdrift?", "scale": ["Niva 1: Gevinstkartet brukes ikke under gjennomføring.", "Niva 2: Gevinstkartet vises, men ikke aktivt brukt.", "Niva 3: Gevinstkartet oppdateres og brukes i noen beslutninger.", "Niva 4: Gevinstkartet er aktivt styringsverktoy under gjennomføring.", "Niva 5: Gevinstkartet brukes dynamisk til a justere strategi og tiltak underveis."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Hvordan følges opp den strategiske koblingen og KPI-ene under gjennomføring?", "scale": ["Niva 1: Ingen oppfølging av strategisk kobling under gjennomføring.", "Niva 2: KPI-er måles, men kobling til strategi mangler.", "Niva 3: Noen KPI-er følges opp med strategisk kobling.", "Niva 4: Systematisk oppfølging av KPI-er med tydelig strategisk kobling.", "Niva 5: Dynamisk justering av KPI-er basert pa strategisk utvikling underveis."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Hvordan håndteres avgrensning av programgevinster under gjennomføring nar nye forhold oppstar?", "scale": ["Niva 1: Avgrensning glemmes under gjennomføring.", "Niva 2: Avgrensning omtales, men ikke operasjonalisert.", "Niva 3: Avgrensning håndteres for storre endringer.", "Niva 4: System for a handtere avgrensning under gjennomføring.", "Niva 5: Dynamisk avgrensningshandtering integrert i beslutningsprosesser."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan justeres nullpunkter og estimater under gjennomføring basert pa nye data og erfaringer?", "scale": ["Niva 1: Nullpunkter og estimater justeres ikke under gjennomføring.", "Niva 2: Justering skjer ad hoc uten struktur.", "Niva 3: Systematisk justering for store avvik.", "Niva 4: Regelmessig revisjon og justering av nullpunkter og estimater.", "Niva 5: Kontinuerlig justering basert pa realtidsdata og læring."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Hvordan testes hypoteser og datagrunnlag under gjennomføring for a validere tilnaermingen?", "scale": ["Niva 1: Hypoteser testes ikke under gjennomføring.", "Niva 2: Noen uformelle tester gjennomfores.", "Niva 3: Formell testing for kritiske hypoteser.", "Niva 4: Systematisk testing og validering under gjennomføring.", "Niva 5: Kontinuerlig hypotesetesting integrert i læringsprosesser."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement under gjennomføring?", "scale": ["Niva 1: Interessentengasjement avtar under gjennomføring.", "Niva 2: Begrenset engasjement for viktige beslutninger.", "Niva 3: Regelmessig engasjement for storre endringer.", "Niva 4: Systematisk interessentoppfølging under gjennomføring.", "Niva 5: Kontinuerlig dialog og samskaping med interessenter."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvakes og håndteres gevinstforutsetninger under gjennomføring?", "scale": ["Niva 1: Forutsetninger overvakes ikke under gjennomføring.", "Niva 2: Noen forutsetninger overvakes uformelt.", "Niva 3: Systematisk overvaking av kritiske forutsetninger.", "Niva 4: Aktiv handtering av endrede forutsetninger.", "Niva 5: Forutsetningsstyring integrert i risikostyring og beslutninger."]},
        {"id": 10, "title": "Prinsipielle og vilkarsmessige kriterier", "question": "Hvordan håndteres endringer i prinsipielle og vilkarsmessige kriterier under gjennomføring?", "scale": ["Niva 1: Endringer i kriterier håndteres ikke.", "Niva 2: Store endringer håndteres reaktivt.", "Niva 3: System for a handtere endringer i kriterier.", "Niva 4: Proaktiv handtering av endrede kriterier.", "Niva 5: Dynamisk tilpasning til endrede kriterier i sanntid."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under gjennomføring?", "scale": ["Niva 1: Enighet testes ikke under gjennomføring.", "Niva 2: Enighet bekreftes ved store endringer.", "Niva 3: Regelmessig bekreftelse av enighet.", "Niva 4: Systematisk arbeid for a opprettholde enighet.", "Niva 5: Kontinuerlig dialog og justering for a opprettholde enighet."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan håndteres disponering av besparelser under gjennomføring?", "scale": ["Niva 1: Disponering håndteres ikke under gjennomføring.", "Niva 2: Disponering justeres for store avvik.", "Niva 3: Systematisk revisjon av disponeringsplaner.", "Niva 4: Dynamisk tilpasning av disponering basert pa resultater.", "Niva 5: Optimål disponering integrert i beslutningsstotte."]},
        {"id": 13, "title": "måling av effektivitet og produktivitet", "question": "Hvordan måles og følges opp effektivitet og produktivitet under gjennomføring?", "scale": ["Niva 1: Effektivitet og produktivitet måles ikke underveis.", "Niva 2: Noen målinger registreres, men ikke analysert.", "Niva 3: Systematisk måling med begrenset analyse.", "Niva 4: Regelmessig analyse og justering basert pa målinger.", "Niva 5: Realtids overvaking og proaktiv justering."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Hvordan identifiseres og håndteres nye operasjonelle risikoer og ulemper under gjennomføring?", "scale": ["Niva 1: Nye risikoer identifiseres ikke underveis.", "Niva 2: Store risikoer håndteres reaktivt.", "Niva 3: Systematisk identifisering av nye risikoer.", "Niva 4: Proaktiv handtering av nye risikoer.", "Niva 5: Risikostyring integrert i daglig drift."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan vurderes balansen mellom gevinster og ulemper under gjennomføring?", "scale": ["Niva 1: Balansen vurderes ikke under gjennomføring.", "Niva 2: Balansen vurderes ved store endringer.", "Niva 3: Regelmessig vurdering av balansen.", "Niva 4: Systematisk overvaking av balansen.", "Niva 5: Balansevurdering integrert i beslutningsprosesser."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Hvordan oppdateres og brukes gevinstrealiseringsplanen under gjennomføring?", "scale": ["Niva 1: Gevinstrealiseringsplanen oppdateres ikke.", "Niva 2: Planen oppdateres ved store endringer.", "Niva 3: Regelmessig oppdatering av planen.", "Niva 4: Planen brukes aktivt i styring og beslutninger.", "Niva 5: Dynamisk oppdatering og bruk av planen i sanntid."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under gjennomføring?", "scale": ["Niva 1: Planen brukes ikke som operativ handlingsplan.", "Niva 2: Planen brukes til visse operasjoner.", "Niva 3: Planen er integrert i deler av den operative styringen.", "Niva 4: Planen er aktivt operativt styringsverktoy.", "Niva 5: Planen er fullt integrert i alle operative beslutninger."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hvordan utvikles endringsberedskap og operativ mottaksevne under gjennomføring?", "scale": ["Niva 1: Endringsberedskap utvikles ikke underveis.", "Niva 2: Begrenset fokus pa endringsberedskap.", "Niva 3: Systematisk arbeid med endringsberedskap.", "Niva 4: målrettet utvikling av mottaksevne.", "Niva 5: Kontinuerlig tilpasning og læring i endringsprosessen."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Hvordan opprettholdes kommunikasjon og forankring under gjennomføring?", "scale": ["Niva 1: Kommunikasjon avtar under gjennomføring.", "Niva 2: Begrenset kommunikasjon om viktige endringer.", "Niva 3: Regelmessig kommunikasjon om fremdrift.", "Niva 4: Systematisk kommunikasjonsplan under gjennomføring.", "Niva 5: Kontinuerlig dialog og tilbakemelding integrert i prosessen."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Hvordan utoves eierskap og ansvar under gjennomføring?", "scale": ["Niva 1: Eierskap og ansvar svekkes under gjennomføring.", "Niva 2: Begrenset eierskap i kritiske faser.", "Niva 3: Tydelig eierskap for sentrale ansvarsområder.", "Niva 4: Aktivt utovd eierskap gjennom hele prosessen.", "Niva 5: Sterk eierskapskultur som driver gjennomføring."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Hvordan justeres periodisering og forankring under gjennomføring?", "scale": ["Niva 1: Periodisering justeres ikke under gjennomføring.", "Niva 2: Store justeringer i periodisering.", "Niva 3: Regelmessig revisjon av periodisering.", "Niva 4: Dynamisk tilpasning av periodisering.", "Niva 5: Fleksibel periodisering integrert i styringssystemet."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Hvordan opprettholdes realisme og engasjement under gjennomføring?", "scale": ["Niva 1: Realisme og engasjement avtar.", "Niva 2: Begrenset fokus pa a opprettholde engasjement.", "Niva 3: Arbeid med a opprettholde realisme og engasjement.", "Niva 4: Systematisk arbeid for a styrke troverdighet.", "Niva 5: Høy troverdighet og engasjement gjennom hele prosessen."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan bygges momentum gjennom tidlig gevinstuttak under gjennomføringsfasen?", "scale": ["Niva 1: Ingen fokus pa momentum eller tidlig gevinstuttak.", "Niva 2: Noen tidlige gevinster realiseres, men uten strategi.", "Niva 3: Planlagt for tidlig gevinstuttak, men begrenset gjennomføring.", "Niva 4: Systematisk arbeid med tidlig gevinstuttak for a bygge momentum.", "Niva 5: Kontinuerlig fokus pa momentum gjennom suksessiv gevinstrealisering."]},
        {"id": 24, "title": "Enighet og lojalitet til gevinster", "question": "I hvilken grad oppleves det at endringsledelsesarbeidet har skapt reell enighet og lojalitet til gevinstene blant berørt personell under gjennomføringen?", "scale": ["Niva 1: Lav enighet - motstand eller likegyldighet til gevinstmålene i berørt organisasjon.", "Niva 2: Delvis enighet - noen grupper stotter gevinstene, men betydelig motstand finnes.", "Niva 3: Moderat enighet - flertallet aksepterer gevinstene, men engasjementet varierer.", "Niva 4: Høy enighet - bred aksept og stotte til gevinstene, med aktiv deltakelse i gjennomføring.", "Niva 5: Full lojalitet - gevinstene er internalisert som felles mål, berørt personell bidrar proaktivt til a na dem."]}
    ],
    "Realisering": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan anvendes læring fra tidligere prosjekter og gevinstarbeid for a optimålisere gevinstuttak under realiseringen?", "scale": ["Niva 1: Ingen læring anvendt i realiseringsfasen.", "Niva 2: Enkelte erfaringer tas i betraktning.", "Niva 3: Systematisk bruk av læring for a optimålisere uttak.", "Niva 4: læring integrert i realiseringsprosessen.", "Niva 5: Kontinuerlig læring og optimålisering under realisering."]},
        {"id": 2, "title": "Strategisk retning og gevinstforstaelse", "question": "Hvordan sikres strategisk retning og gevinstforstaelse under realiseringen?", "scale": ["Niva 1: Strategisk retning glemmes under realisering.", "Niva 2: Strategi refereres til, men ikke operasjonalisert.", "Niva 3: Tydelig strategisk retning i realiseringsarbeid.", "Niva 4: Strategi dynamisk tilpasses under realisering.", "Niva 5: Strategi og realisering fullt integrert og sammenvevd."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Hvordan brukes gevinstkartet for a styre realiseringsarbeidet?", "scale": ["Niva 1: Gevinstkartet brukes ikke under realisering.", "Niva 2: Gevinstkartet vises, men ikke aktivt brukt.", "Niva 3: Gevinstkartet brukes til a prioritere realisering.", "Niva 4: Gevinstkartet er aktivt styringsverktoy.", "Niva 5: Gevinstkartet dynamisk oppdateres basert pa realisering."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Hvordan følges opp strategisk kobling og KPI-er under realiseringen?", "scale": ["Niva 1: Ingen oppfølging av strategisk kobling.", "Niva 2: KPI-er måles, men kobling til strategi svak.", "Niva 3: Systematisk oppfølging av strategisk kobling.", "Niva 4: Dynamisk justering basert pa KPI-utvikling.", "Niva 5: Full integrasjon mellom strategi, KPI-er og realisering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Hvordan håndteres avgrensning av programgevinster under realiseringen?", "scale": ["Niva 1: Avgrensning håndteres ikke under realisering.", "Niva 2: Store avgrensningsutfordringer håndteres.", "Niva 3: System for a handtere avgrensning.", "Niva 4: Proaktiv handtering av avgrensning.", "Niva 5: Avgrensning integrert i realiseringsprosessen."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan valideres og justeres nullpunkter og estimater under realiseringen?", "scale": ["Niva 1: Nullpunkter og estimater valideres ikke.", "Niva 2: Store avvik håndteres reaktivt.", "Niva 3: Systematisk validering under realisering.", "Niva 4: Kontinuerlig justering basert pa realisering.", "Niva 5: Dynamisk oppdatering av nullpunkter og estimater."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Hvordan valideres hypoteser og datagrunnlag under realiseringen?", "scale": ["Niva 1: Hypoteser valideres ikke under realisering.", "Niva 2: Noen hypoteser testes uformelt.", "Niva 3: Systematisk testing av kritiske hypoteser.", "Niva 4: Omfattende validering under realisering.", "Niva 5: Kontinuerlig hypotesetesting og læring."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement under realiseringen?", "scale": ["Niva 1: Interessentengasjement avtar under realisering.", "Niva 2: Begrenset engasjement for viktige beslutninger.", "Niva 3: Regelmessig dialog med interessenter.", "Niva 4: Aktivt interessentengasjement gjennom realisering.", "Niva 5: Interessenter er drivkrefter i realiseringsarbeidet."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvakes og realiseres gevinstforutsetninger under realiseringen?", "scale": ["Niva 1: Forutsetninger overvakes ikke under realisering.", "Niva 2: Noen forutsetninger følges opp.", "Niva 3: Systematisk overvaking av forutsetninger.", "Niva 4: Aktiv realisering av forutsetninger.", "Niva 5: Forutsetningsrealisering integrert i gevinstuttak."]},
        {"id": 10, "title": "Prinsipielle og vilkarsmessige kriterier", "question": "Hvordan håndteres prinsipielle og vilkarsmessige kriterier under realiseringen?", "scale": ["Niva 1: Kriterier håndteres ikke under realisering.", "Niva 2: Store avvik fra kriterier håndteres.", "Niva 3: Systematisk handtering av kriterier.", "Niva 4: Proaktiv tilpasning til kriterier.", "Niva 5: Kriterier integrert i realiseringsbeslutninger."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under realiseringen?", "scale": ["Niva 1: Enighet testes ikke under realisering.", "Niva 2: Enighet bekreftes ved store endringer.", "Niva 3: Regelmessig bekreftelse av enighet.", "Niva 4: Kontinuerlig arbeid for a opprettholde enighet.", "Niva 5: Full enighet gjennom hele realiseringsfasen."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan håndteres disponering av besparelser under realiseringen?", "scale": ["Niva 1: Disponering håndteres ikke under realisering.", "Niva 2: Store endringer i disponering håndteres.", "Niva 3: Systematisk revisjon av disponering.", "Niva 4: Dynamisk tilpasning av disponering.", "Niva 5: Optimål disponering under realisering."]},
        {"id": 13, "title": "måling av effektivitet og produktivitet", "question": "Hvordan måles og forbedres effektivitet og produktivitet under realiseringen?", "scale": ["Niva 1: Effektivitet og produktivitet måles ikke.", "Niva 2: Noen målinger registreres.", "Niva 3: Systematisk måling og rapportering.", "Niva 4: målinger brukes til forbedring.", "Niva 5: Kontinuerlig forbedring basert pa målinger."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Hvordan håndteres operasjonelle risikoer og ulemper under realiseringen?", "scale": ["Niva 1: Risikoer og ulemper håndteres ikke.", "Niva 2: Store risikoer håndteres reaktivt.", "Niva 3: Systematisk identifisering og handtering.", "Niva 4: Proaktiv risikohandtering.", "Niva 5: Risikostyring integrert i realiseringsarbeid."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan vurderes balansen mellom gevinster og ulemper under realiseringen?", "scale": ["Niva 1: Balansen vurderes ikke under realisering.", "Niva 2: Balansen vurderes ved store endringer.", "Niva 3: Regelmessig vurdering av balansen.", "Niva 4: Systematisk overvaking av balansen.", "Niva 5: Balansevurdering integrert i beslutninger."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Hvordan brukes gevinstrealiseringsplanen under realiseringen?", "scale": ["Niva 1: Gevinstrealiseringsplanen brukes ikke.", "Niva 2: Planen refereres til ved behov.", "Niva 3: Planen brukes aktivt i realisering.", "Niva 4: Planen oppdateres og brukes kontinuerlig.", "Niva 5: Planen er sentralt styringsverktoy."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under realiseringen?", "scale": ["Niva 1: Planen brukes ikke som operativ handlingsplan.", "Niva 2: Planen brukes til enkelte operasjoner.", "Niva 3: Planen er integrert i operativ styring.", "Niva 4: Planen er aktivt operativt verktoy.", "Niva 5: Planen driver operativ virksomhet."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hvordan utvikles endringsberedskap og mottaksevne under realiseringen?", "scale": ["Niva 1: Endringsberedskap utvikles ikke.", "Niva 2: Begrenset fokus pa endringsberedskap.", "Niva 3: Systematisk arbeid med endringsberedskap.", "Niva 4: målrettet utvikling av mottaksevne.", "Niva 5: Høy mottaksevne og endringsberedskap."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Hvordan opprettholdes kommunikasjon og forankring under realiseringen?", "scale": ["Niva 1: Kommunikasjon avtar under realisering.", "Niva 2: Begrenset kommunikasjon om realisering.", "Niva 3: Regelmessig kommunikasjon om fremdrift.", "Niva 4: Systematisk kommunikasjon om realisering.", "Niva 5: Kontinuerlig dialog om realiseringsarbeid."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Hvordan utoves eierskap og ansvar under realiseringen?", "scale": ["Niva 1: Eierskap og ansvar svekkes.", "Niva 2: Begrenset eierskap i realiseringsfasen.", "Niva 3: Tydelig eierskap for realisering.", "Niva 4: Aktivt utovd eierskap.", "Niva 5: Sterk eierskapskultur i realisering."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Hvordan justeres periodisering og forankring under realiseringen?", "scale": ["Niva 1: Periodisering justeres ikke.", "Niva 2: Store justeringer i periodisering.", "Niva 3: Regelmessig revisjon av periodisering.", "Niva 4: Dynamisk tilpasning av periodisering.", "Niva 5: Fleksibel periodisering under realisering."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Hvordan opprettholdes realisme og engasjement under realiseringen?", "scale": ["Niva 1: Realisme og engasjement avtar.", "Niva 2: Begrenset fokus pa a opprettholde engasjement.", "Niva 3: Arbeid med a opprettholde realisme og engasjement.", "Niva 4: Systematisk arbeid for a styrke troverdighet.", "Niva 5: Høy troverdighet og engasjement."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan brukes tidlig gevinstuttak for a bygge momentum i realiseringsfasen?", "scale": ["Niva 1: Ingen systematisk bruk av tidlig gevinstuttak.", "Niva 2: Enkelte suksesser brukes til a motivere.", "Niva 3: Bevissthet pa viktigheten av momentum.", "Niva 4: Strategisk bruk av tidlige gevinster.", "Niva 5: Momentum systematisk bygget og vedlikeholdt."]},
        {"id": 24, "title": "Enighet og lojalitet til gevinster", "question": "I hvilken grad har endringsledelsesarbeidet resultert i vedvarende enighet og lojalitet til gevinstene nar realiseringen pagar?", "scale": ["Niva 1: Lav enighet - motstand eller tilbaketrekning fra gevinstarbeidet i berørt organisasjon.", "Niva 2: Delvis enighet - oppslutningen varierer og enkelte grupper trekker seg fra gevinstarbeidet.", "Niva 3: Moderat enighet - de fleste fortsetter a stotte gevinstene, men engasjementet svinger.", "Niva 4: høy enighet - vedvarende stotte og lojalitet til gevinstene gjennom realiseringsfasen.", "Niva 5: Full lojalitet - sterkt eierskap til gevinstene, berørt personell tar aktivt ansvar for a sikre varig realisering."]}
    ],
    "Realisert": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "I hvilken grad er læring fra gevinstrealiseringen dokumentert, delt og integrert i organisasjonens metodeverk for fremtidige initiativer?", "scale": ["Niva 1: Ingen systematisk dokumentasjon av læring eller erfaringer fra gevinstrealiseringen.", "Niva 2: Enkelte erfaringer er notert, men ikke strukturert eller tilgjengeliggjort for andre.", "Niva 3: læring er dokumentert i sluttrapport, men ikke aktivt delt eller integrert i metodeverk.", "Niva 4: Erfaringer er systematisk dokumentert, delt i relevante fora, og brukes i planlegging av nye initiativer.", "Niva 5: læring er fullt integrert i organisasjonens kunnskapsbase, metodeverk og opplæring, med sporbar effekt pa nye initiativer."]},
        {"id": 2, "title": "Strategisk retning og gevinstforstaelse", "question": "I hvilken grad har de realiserte gevinstene faktisk bidratt til organisasjonens strategiske mål, og er denne koblingen dokumentert og verifisert?", "scale": ["Niva 1: Ingen dokumentert kobling mellom realiserte gevinster og strategiske mål.", "Niva 2: Antatt kobling til strategi, men ikke målt eller verifisert.", "Niva 3: Delvis dokumentert strategisk effekt for hovedgevinster.", "Niva 4: Klar dokumentasjon av hvordan gevinstene har bidratt til spesifikke strategiske mål med måltall.", "Niva 5: Full sporbarhet fra realiserte gevinster til strategisk måloppnaelse, verifisert gjennom KPI-er og rapportert til ledelsen."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Er gevinstkartet oppdatert med faktisk realiserte verdier, og brukes det som referanse for fremtidige initiativer og kommunikasjon av oppnadde resultater?", "scale": ["Niva 1: Gevinstkartet er ikke oppdatert eller brukt etter realisering.", "Niva 2: Kartet eksisterer, men viser fortsatt planlagte verdier uten oppdatering.", "Niva 3: Gevinstkartet er delvis oppdatert med realiserte verdier for hovedgevinster.", "Niva 4: Kartet er fullt oppdatert med realiserte verdier og brukes i sluttrapportering.", "Niva 5: Gevinstkartet er oppdatert, arkivert som referanse, og brukes aktivt i kommunikasjon og som mål for nye initiativer."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Er de realiserte gevinstene målt og rapportert gjennom etablerte KPI-er, og er effekten synlig i organisasjonens styringssystem?", "scale": ["Niva 1: Ingen måling av realiserte gevinster gjennom KPI-er.", "Niva 2: Enkelte målinger finnes, men er ikke koblet til organisasjonens KPI-struktur.", "Niva 3: Hovedgevinster er målt og rapportert, men ikke integrert i lopende styring.", "Niva 4: Realiserte gevinster er målt gjennom KPI-er og rapporteres i styringsdialog.", "Niva 5: Full integrasjon der realiserte gevinster er synlige i dashboards, styringssystem og pavirker ressursallokering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Er det dokumentert og verifisert hvilke effekter som faktisk skyldes programmet versus andre faktorer, og er denne avgrensningen troverdig og akseptert?", "scale": ["Niva 1: Ingen dokumentert avgrensning - uklart hva som skyldes programmet.", "Niva 2: Generell pastand om programmets bidrag uten konkret dokumentasjon.", "Niva 3: Delvis dokumentert avgrensning for hovedgevinster med rimelig begrunnelse.", "Niva 4: Systematisk dokumentert effektisolering med metodebeskrivelse og datagrunnlag.", "Niva 5: Troverdig og verifisert avgrensning akseptert av interessenter, med transparent metodikk som kan gjenbrukes."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan samsvarer de realiserte gevinstene med opprinnelige estimater, og er avvik analysert og forklart?", "scale": ["Niva 1: Ingen sammenligning mellom estimater og realiserte verdier.", "Niva 2: Overordnet sammenligning uten detaljert avviksanalyse.", "Niva 3: Avvik er identifisert for hovedgevinster med generelle forklaringer.", "Niva 4: Systematisk avviksanalyse med dokumenterte arsaker og læring for fremtidige estimater.", "Niva 5: Detaljert analyse av estimatpresisjon brukes aktivt til a forbedre estimeringsmetodikk i organisasjonen."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Er de opprinnelige hypotesene om gevinstmekanismer validert eller falsifisert basert pa faktiske data, og er denne laringen dokumentert?", "scale": ["Niva 1: Ingen systematisk validering av opprinnelige hypoteser.", "Niva 2: Generell vurdering av om hypoteser stemte uten datagrunnlag.", "Niva 3: Hovedhypoteser er vurdert mot faktiske resultater med noe dokumentasjon.", "Niva 4: Systematisk validering av hypoteser med datagrunnlag og dokumenterte konklusjoner.", "Niva 5: Full hypotesevalidering integrert i læringsrapport, med innsikt som forbedrer fremtidige gevinstmodeller."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan vurderer interessentene selv sin involvering i gevinstrealiseringen, og er deres tilbakemeldinger innhentet og dokumentert?", "scale": ["Niva 1: Ingen systematisk innhenting av interessenters vurdering.", "Niva 2: Uformelle tilbakemeldinger fra enkelte interessenter.", "Niva 3: Strukturert tilbakemelding innhentet fra hovedinteressenter.", "Niva 4: Omfattende interessentevaluering med dokumenterte funn og forbedringsområder.", "Niva 5: Interessentvurdering integrert i sluttrapport, med konkrete tiltak for forbedring av fremtidig involvering."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "I hvilken grad ble de identifiserte gevinstforutsetningene faktisk oppfylt, og hvordan påvirket dette gevinstrealiseringen?", "scale": ["Niva 1: Ingen systematisk oppfølging av om forutsetninger ble oppfylt.", "Niva 2: Generell vurdering uten konkret dokumentasjon av forutsetningsstatus.", "Niva 3: Hovedforutsetninger er vurdert med dokumentasjon av oppfyllelsesgrad.", "Niva 4: Systematisk analyse av forutsetningsoppfyllelse og påvirkning pa gevinster.", "Niva 5: Full sporbarhet fra forutsetninger til gevinstresultat, med læring om kritiske forutsetninger for fremtiden."]},
        {"id": 10, "title": "Prinsipielle og vilkarsmessige kriterier", "question": "Ble alle identifiserte kriterier og vilkar for gevinstrealisering oppfylt, og er eventuelle avvik håndtert og dokumentert?", "scale": ["Niva 1: Ingen oppfølging av om kriterier og vilkar ble oppfylt.", "Niva 2: Generell vurdering uten systematisk gjennomgang.", "Niva 3: Hovedkriterier er gjennomgatt med dokumentasjon av status.", "Niva 4: Systematisk gjennomgang av alle kriterier med avvikshåndtering dokumentert.", "Niva 5: Full dokumentasjon av kriterieoppfyllelse integrert i sluttrapport med læring for fremtidige initiativer."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Er det oppnadd enighet blant interessenter om de endelige gevinstresultatene, og er eventuelle uenigheter lost eller dokumentert?", "scale": ["Niva 1: Ingen formell enighet om gevinstresultater - ulike oppfatninger eksisterer.", "Niva 2: Delvis enighet, men med uloste uenigheter om sentrale gevinster.", "Niva 3: Enighet om hovedresultater, men noen områder har fortsatt uavklarte sporsmål.", "Niva 4: Bred enighet om gevinstresultater dokumentert gjennom formell godkjenning.", "Niva 5: Full konsensus om alle gevinstresultater, med transparent prosess og dokumentert godkjenning fra alle nokkelinteressenter."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Er frigjorte ressurser fra kostnads- og tidsbesparelser faktisk omdisponert som planlagt, og er denne omdisponeringen dokumentert og verifisert?", "scale": ["Niva 1: Ingen dokumentasjon av hvordan frigjorte ressurser er disponert.", "Niva 2: Pastand om omdisponering uten konkret dokumentasjon eller verifisering.", "Niva 3: Delvis dokumentert omdisponering for hovedbesparelser.", "Niva 4: Systematisk dokumentasjon av ressursomdisponering med verifisering fra budsjettansvarlige.", "Niva 5: Full sporbarhet av frigjorte ressurser til ny verdiskapende aktivitet, rapportert i økonomioppfølging."]},
        {"id": 13, "title": "måling av effektivitet og produktivitet", "question": "Er okt effektivitet og produktivitet målt over tid for a verifisere at gevinstene er varige, ikke bare kortvarige effekter?", "scale": ["Niva 1: Ingen måling av om effektivitetsgevinster opprettholdes over tid.", "Niva 2: Enkeltmåling ved prosjektslutt uten oppfølging.", "Niva 3: målinger gjennomfort i en periode etter realisering med noe dokumentasjon.", "Niva 4: Systematisk måling over tid som bekrefter varige effekter.", "Niva 5: Langsiktig målingsprogram etablert som del av linjeorganisasjonens oppfølging, med dokumentert baerekraft."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Er de faktiske ulempene og negative konsekvensene kartlagt og vurdert opp mot de realiserte gevinstene i en helhetlig kost-nytte-vurdering?", "scale": ["Niva 1: Ingen kartlegging av faktiske ulemper eller negativ påvirkning.", "Niva 2: Uformell erkjennelse av noen ulemper uten systematisk vurdering.", "Niva 3: Hovedulemper er identifisert og vurdert mot gevinster.", "Niva 4: Systematisk kost-nytte-analyse med dokumenterte ulemper og gevinster.", "Niva 5: Helhetlig evaluering med transparent vurdering av netto verdiskapning, inkludert alle vesentlige ulemper."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Er den endelige balansen mellom oppnadde gevinster og papforte ulemper vurdert som akseptabel av interessentene, og er denne vurderingen dokumentert?", "scale": ["Niva 1: Ingen formell vurdering av gevinst-ulempe-balansen.", "Niva 2: Uformell vurdering uten interessentinvolvering.", "Niva 3: Vurdering gjennomfort med noe interessentinvolvering.", "Niva 4: Formell vurdering med dokumentert aksept fra hovedinteressenter.", "Niva 5: Omfattende evaluering med bred interessentinvolvering og dokumentert konsensus om at balansen er akseptabel."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Er gevinstrealiseringsplanen oppdatert med faktiske resultater og arkivert som referansedokument for organisasjonen?", "scale": ["Niva 1: Gevinstrealiseringsplanen er ikke oppdatert eller arkivert.", "Niva 2: Planen eksisterer, men er ikke oppdatert med faktiske resultater.", "Niva 3: Planen er delvis oppdatert med hovedresultater.", "Niva 4: Planen er fullt oppdatert med alle resultater og avvik dokumentert.", "Niva 5: Oppdatert plan er arkivert som beste praksis-referanse og brukes aktivt i opplæring og nye initiativer."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Fungerte gevinstrealiseringsplanen effektivt som operativt styringsverktoy gjennom hele realiseringen, og er erfaringene med dette dokumentert?", "scale": ["Niva 1: Planen ble ikke brukt operativt - kun et plandokument.", "Niva 2: Planen ble brukt sporadisk uten systematisk oppfølging.", "Niva 3: Planen ble brukt som styringsverktoy for deler av realiseringen.", "Niva 4: Planen fungerte som aktivt styringsverktoy med regelmessig oppdatering og oppfølging.", "Niva 5: Planen var sentralt styringsverktoy gjennom hele realiseringen, med dokumenterte erfaringer for metodeforbedring."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hadde organisasjonen tilstrekkelig kapasitet og kompetanse til a ta imot og forankre endringene varig, og er dette evaluert?", "scale": ["Niva 1: Ingen evaluering av organisasjonens mottaksevne eller endringskapasitet.", "Niva 2: Uformell vurdering uten systematisk evaluering.", "Niva 3: Evaluering gjennomfort for hovedområder med noe dokumentasjon.", "Niva 4: Systematisk evaluering av mottaksevne med dokumenterte funn og forbedringsområder.", "Niva 5: Omfattende evaluering med konkrete anbefalinger implementert for a styrke fremtidig endringskapasitet."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Er de realiserte gevinstene kommunisert til organisasjonen, og oppleves endringene som varig forankret i kultur og arbeidsprosesser?", "scale": ["Niva 1: Ingen systematisk kommunikasjon av oppnadde resultater.", "Niva 2: Begrenset kommunikasjon til utvalgte grupper.", "Niva 3: Resultater kommunisert bredt, men usikkert om varig forankring.", "Niva 4: Systematisk kommunikasjon med dokumentert forankring i berørt organisasjon.", "Niva 5: Gevinstene er kommunisert som suksesshistorie, og endringene er observerbart integrert i daglig praksis og kultur."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Er det etablert varig eierskap i linjen for a opprettholde de realiserte gevinstene, og er ansvar og roller for vedlikehold definert?", "scale": ["Niva 1: Ingen definert eierskap for vedlikehold av gevinster etter prosjektslutt.", "Niva 2: Uformelt eierskap uten klare roller eller ansvar.", "Niva 3: Eierskap definert for hovedgevinster, men ikke fullt operasjonalisert.", "Niva 4: Klart definert eierskap med roller og ansvar dokumentert og overfort til linjen.", "Niva 5: Varig eierskap etablert med integrering i stillingsbeskrivelser, målstyring og oppfølgingsrutiner."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Ble gevinstene realisert i henhold til planlagt periodisering, og er avvik fra tidsplan analysert og forklart?", "scale": ["Niva 1: Ingen sammenligning mellom planlagt og faktisk periodisering.", "Niva 2: Overordnet vurdering uten detaljert analyse av tidsavvik.", "Niva 3: Avvik fra periodisering identifisert for hovedgevinster med generelle forklaringer.", "Niva 4: Systematisk analyse av periodiseringsavvik med dokumenterte arsaker.", "Niva 5: Detaljert periodiseringsanalyse brukes til a forbedre fremtidig gevinstplanlegging og gi mer realistiske tidsestimater."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Viste de endelige resultatene at de opprinnelige estimatene var realistiske, og har dette påvirket organisasjonens troverdighet og engasjement for fremtidige gevinstarbeid?", "scale": ["Niva 1: Stor diskrepans mellom estimater og resultater som har svekket troverdighet.", "Niva 2: Moderate avvik som har skapt noe skepsis til fremtidige estimater.", "Niva 3: Akseptable avvik som ikke vesentlig har påvirket troverdighet.", "Niva 4: God overensstemmelse mellom estimater og resultater som styrker tillit.", "Niva 5: Høy presisjon i estimater har betydelig styrket organisasjonens engasjement og tillit til gevinstarbeid."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Bidro tidlig gevinstuttak til a bygge momentum og opprettholde engasjement gjennom hele realiseringen, og er denne effekten evaluert?", "scale": ["Niva 1: Ingen tidlig gevinstuttak eller evaluering av momentum-effekt.", "Niva 2: Noe tidlig gevinstuttak uten systematisk evaluering av effekten.", "Niva 3: Tidlige gevinster ble realisert og bidro til engasjement, med noe dokumentasjon.", "Niva 4: Systematisk tidlig gevinstuttak med dokumentert positiv effekt pa momentum og engasjement.", "Niva 5: Tidlig gevinstuttak var strategisk planlagt og evaluert, med læring som forbedrer fremtidige initiativer."]},
        {"id": 24, "title": "Enighet og lojalitet til gevinster", "question": "I hvilken grad har arbeidet med endringsledelse resultert i reell enighet og lojalitet til de definerte gevinstene blant berørt personell?", "scale": ["Niva 1: Lav enighet - betydelig motstand eller likegyldighet til gevinstmålene blant berørt personell.", "Niva 2: Delvis enighet - noen grupper stotter gevinstene, men det er fortsatt vesentlig motstand.", "Niva 3: Moderat enighet - flertallet aksepterer gevinstene, men engasjementet varierer.", "Niva 4: Høy enighet - bred aksept og aktiv stotte til gevinstene i berørt organisasjon.", "Niva 5: Full lojalitet - gevinstene er internalisert som felles mål, med observerbar atferdsendring og proaktiv innsats for a na dem."]}
    ]
}

# ============================================================================
# DATALAGRING MED FLERBRUKER-STOTTE
# ============================================================================
def ensure_backup_dir():
    # Opprett backup-mappe
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def create_backup():
    # Lag backup av datafilen
    data_file = get_data_file()
    if os.path.exists(data_file):
        ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.pkl")
        try:
            shutil.copy2(data_file, backup_path)
            backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.pkl')])
            while len(backups) > 50:
                os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))
        except Exception as e:
            print(f"Backup feilet: {e}")

def load_data():
    # Last data fra fil
    data_file = get_data_file()
    if os.path.exists(data_file):
        try:
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
                if 'projects' in data and 'initiatives' not in data:
                    data['initiatives'] = data['projects']
                    del data['projects']
                if 'initiatives' not in data:
                    data['initiatives'] = {}
                return data
        except:
            pass
    return {'initiatives': {}}

def save_data(data):
    # Lagre data til fil med las
    data_file = get_data_file()
    if FILELOCK_AVAILABLE:
        lock = FileLock(LOCK_FILE, timeout=10)
        try:
            with lock:
                create_backup()
                with open(data_file, 'wb') as f:
                    pickle.dump(data, f)
        except Exception as e:
            st.error(f"Feil ved lagring: {e}")
    else:
        try:
            create_backup()
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            st.error(f"Feil ved lagring: {e}")

def get_data():
    # Hent data
    if 'app_data' not in st.session_state:
        st.session_state.app_data = load_data()
        st.session_state.data_loaded_at = datetime.now()
    if 'initiatives' not in st.session_state.app_data:
        st.session_state.app_data['initiatives'] = {}
    return st.session_state.app_data

def refresh_data():
    # Tving oppdatering fra fil
    st.session_state.app_data = load_data()
    st.session_state.data_loaded_at = datetime.now()
    return st.session_state.app_data

def merge_data(file_data, session_data):
    # Sla sammen data fra fil og session
    merged = {'initiatives': {}}
    all_init_ids = set(file_data.get('initiatives', {}).keys()) | set(session_data.get('initiatives', {}).keys())
    
    for init_id in all_init_ids:
        file_init = file_data.get('initiatives', {}).get(init_id)
        session_init = session_data.get('initiatives', {}).get(init_id)
        
        if file_init is None:
            merged['initiatives'][init_id] = session_init
        elif session_init is None:
            merged['initiatives'][init_id] = file_init
        else:
            merged_init = session_init.copy()
            file_interviews = file_init.get('interviews', {})
            session_interviews = session_init.get('interviews', {})
            merged_interviews = {**file_interviews, **session_interviews}
            
            for iid in set(file_interviews.keys()) & set(session_interviews.keys()):
                def count_answers(interview):
                    return sum(1 for ph in interview.get('responses', {}).values() 
                              for r in ph.values() if r.get('score', 0) > 0)
                if count_answers(file_interviews[iid]) > count_answers(session_interviews[iid]):
                    merged_interviews[iid] = file_interviews[iid]
                else:
                    merged_interviews[iid] = session_interviews[iid]
            
            merged_init['interviews'] = merged_interviews
            merged_init['benefits'] = {**file_init.get('benefits', {}), **session_init.get('benefits', {})}
            merged['initiatives'][init_id] = merged_init
    
    return merged

def persist_data():
    # Lagre med merge for a unnga a overskrive andres data
    data_file = get_data_file()
    
    try:
        if FILELOCK_AVAILABLE:
            lock = FileLock(LOCK_FILE, timeout=10)
            with lock:
                current_file_data = load_data()
                session_data = st.session_state.app_data
                merged_data = merge_data(current_file_data, session_data)
                create_backup()
                with open(data_file, 'wb') as f:
                    pickle.dump(merged_data, f)
                st.session_state.app_data = merged_data
                st.session_state.data_loaded_at = datetime.now()
        else:
            current_file_data = load_data()
            session_data = st.session_state.app_data
            merged_data = merge_data(current_file_data, session_data)
            create_backup()
            with open(data_file, 'wb') as f:
                pickle.dump(merged_data, f)
            st.session_state.app_data = merged_data
            st.session_state.data_loaded_at = datetime.now()
    except Exception as e:
        st.error(f"Feil ved lagring: {e}")

# ============================================================================
# STYLING
# ============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Source Sans Pro', sans-serif; font-size: 16px; }}
.main-header {{ font-size: 2.2rem; color: {COLORS['primary_dark']}; text-align: center; margin-bottom: 0.3rem; font-weight: 700; }}
.sub-header {{ font-size: 1.1rem; color: {COLORS['primary']}; text-align: center; margin-bottom: 1.5rem; }}
.metric-card {{ background: {COLORS['gray_light']}; padding: 1.2rem; border-radius: 8px; border-left: 4px solid {COLORS['primary']}; text-align: center; margin: 0.3rem 0; }}
.metric-value {{ font-size: 2.2rem; font-weight: 700; color: {COLORS['primary_dark']}; }}
.metric-label {{ font-size: 0.95rem; color: #666; text-transform: uppercase; }}
.strength-card {{ background: linear-gradient(135deg, #DDFAE2 0%, {COLORS['gray_light']} 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['success']}; margin: 0.5rem 0; font-size: 1.05rem; }}
.improvement-card {{ background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, {COLORS['gray_light']} 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['danger']}; margin: 0.5rem 0; font-size: 1.05rem; }}
.stButton > button {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%); color: white; border: none; border-radius: 6px; padding: 0.6rem 1.2rem; font-weight: 600; font-size: 1rem; }}
.stProgress > div > div > div > div {{ background: linear-gradient(90deg, {COLORS['primary_light']} 0%, {COLORS['success']} 100%); }}
div[data-testid="stMetricValue"] {{ font-size: 2rem; }}
div[data-testid="stMarkdownContainer"] p {{ font-size: 1.05rem; }}
div[data-testid="stMarkdownContainer"] li {{ font-size: 1.05rem; }}
.stSelectbox label, .stTextInput label, .stTextArea label {{ font-size: 1rem; }}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HJELPEFUNKSJONER
# ============================================================================
def get_score_color(score):
    if score >= 4.5: return COLORS['success']
    elif score >= 3.5: return COLORS['primary_light']
    elif score >= 2.5: return COLORS['warning']
    else: return COLORS['danger']

def get_score_text(score):
    if score >= 4.5: return "høy modenhet"
    elif score >= 3.5: return "God modenhet"
    elif score >= 2.5: return "Moderat modenhet"
    elif score >= 1.5: return "Begrenset modenhet"
    else: return "Lav modenhet"

def get_recommended_questions(mode, selection, phase):
    if mode == "role" and selection in ROLES:
        return ROLES[selection].get('recommended_questions', {}).get(phase, [])
    elif mode == "parameter":
        recommended = set()
        for param_name in selection:
            if param_name in PARAMETERS:
                recommended.update(PARAMETERS[param_name]['questions'])
        return list(recommended)
    return []

def calculate_stats(initiative, benefit_filter=None):
    if not initiative.get('interviews'):
        return None
    
    all_scores = {}
    for phase in PHASES:
        all_scores[phase] = {}
        for q in questions_data[phase]:
            all_scores[phase][q['id']] = []
    
    interview_count = 0
    for interview in initiative['interviews'].values():
        if benefit_filter and benefit_filter != "all":
            if interview.get('info', {}).get('benefit_id') != benefit_filter:
                continue
        interview_count += 1
        
        for phase, questions in interview.get('responses', {}).items():
            for q_id, resp in questions.items():
                if resp.get('score', 0) > 0:
                    all_scores[phase][int(q_id)].append(resp['score'])
    
    stats = {
        'phases': {},
        'questions': {},
        'parameters': {},
        'total_interviews': interview_count,
        'overall_avg': 0,
        'high_maturity': [],
        'low_maturity': []
    }
    
    all_avgs = []
    
    for phase in PHASES:
        phase_scores = []
        stats['questions'][phase] = {}
        
        for q in questions_data[phase]:
            scores = all_scores[phase][q['id']]
            if scores:
                avg = np.mean(scores)
                stats['questions'][phase][q['id']] = {
                    'avg': avg, 'min': min(scores), 'max': max(scores),
                    'count': len(scores), 'title': q['title'], 'question': q['question']
                }
                phase_scores.append(avg)
                all_avgs.append(avg)
                
                item = {'phase': phase, 'question_id': q['id'], 'title': q['title'], 'score': avg}
                if avg >= 4:
                    stats['high_maturity'].append(item)
                elif avg < 3:
                    stats['low_maturity'].append(item)
        
        if phase_scores:
            stats['phases'][phase] = {'avg': np.mean(phase_scores), 'min': min(phase_scores), 'max': max(phase_scores)}
    
    for param_name, param_data in PARAMETERS.items():
        param_scores = []
        for phase in PHASES:
            if phase in stats['questions']:
                for q_id in param_data['questions']:
                    if q_id in stats['questions'][phase]:
                        param_scores.append(stats['questions'][phase][q_id]['avg'])
        if param_scores:
            stats['parameters'][param_name] = {'avg': np.mean(param_scores), 'description': param_data['description']}
    
    if all_avgs:
        stats['overall_avg'] = np.mean(all_avgs)
    
    stats['high_maturity'].sort(key=lambda x: x['score'], reverse=True)
    stats['low_maturity'].sort(key=lambda x: x['score'])
    
    return stats

# ============================================================================
# DIAGRAMMER
# ============================================================================
def create_phase_radar(phase_data):
    if not phase_data:
        return None
    categories = list(phase_data.keys())
    values = [phase_data[c]['avg'] for c in categories]
    # Dupliser hvis færre enn 3 punkter
    if len(categories) == 1:
        categories = categories * 3
        values = values * 3
    elif len(categories) == 2:
        categories = categories + [categories[0]]
        values = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(0, 83, 166, 0.3)', line=dict(color=COLORS['primary'], width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5], tickfont=dict(size=14)), angularaxis=dict(tickfont=dict(size=14))), showlegend=False, height=350, margin=dict(l=80, r=80, t=40, b=40), font=dict(size=14))
    return fig

def create_parameter_radar(param_data):
    if not param_data:
        return None
    categories = list(param_data.keys())
    values = [param_data[c]['avg'] for c in categories]
    # Dupliser hvis færre enn 3 punkter
    if len(categories) == 1:
        categories = categories * 3
        values = values * 3
    elif len(categories) == 2:
        categories = categories + [categories[0]]
        values = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(100, 200, 250, 0.3)', line=dict(color=COLORS['primary_light'], width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=14)), angularaxis=dict(tickfont=dict(size=13))), showlegend=False, height=400, margin=dict(l=100, r=100, t=40, b=40), font=dict(size=14))
    return fig

def create_strength_radar(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    categories = [f"{item['title'][:20]}..." if len(item['title']) > 20 else item['title'] for item in items]
    values = [item['score'] for item in items]
    # Radar krever minst 3 punkter - dupliser hvis færre
    if len(categories) == 1:
        categories = categories * 3
        values = values * 3
    elif len(categories) == 2:
        categories = categories + [categories[0]]
        values = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(53, 222, 109, 0.3)', line=dict(color=COLORS['success'], width=3), name='Styrker'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5], tickfont=dict(size=14)), angularaxis=dict(tickfont=dict(size=13))), showlegend=False, height=400, margin=dict(l=80, r=80, t=40, b=40), font=dict(size=14))
    return fig

def create_improvement_radar(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    categories = [f"{item['title'][:20]}..." if len(item['title']) > 20 else item['title'] for item in items]
    values = [item['score'] for item in items]
    # Radar krever minst 3 punkter - dupliser hvis færre
    if len(categories) == 1:
        categories = categories * 3
        values = values * 3
    elif len(categories) == 2:
        categories = categories + [categories[0]]
        values = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(255, 107, 107, 0.3)', line=dict(color=COLORS['danger'], width=3), name='Forbedring'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5], tickfont=dict(size=14))), showlegend=False, height=400, margin=dict(l=80, r=80, t=40, b=40), font=dict(size=14))
    return fig

def create_strength_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:25]}..." if len(item['title']) > 25 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['success'], text=[f"{s:.1f}" for s in scores], textposition='outside', textfont=dict(size=16))])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score", tickfont=dict(size=14)), yaxis=dict(autorange="reversed", tickfont=dict(size=13)), height=max(300, len(items) * 45), margin=dict(l=220, r=60, t=20, b=40), font=dict(size=14))
    return fig

def create_improvement_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:25]}..." if len(item['title']) > 25 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['danger'], text=[f"{s:.1f}" for s in scores], textposition='outside', textfont=dict(size=16))])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score", tickfont=dict(size=14)), yaxis=dict(autorange="reversed", tickfont=dict(size=13)), height=max(300, len(items) * 45), margin=dict(l=220, r=60, t=20, b=40), font=dict(size=14))
    return fig

def create_parameter_bar_chart(param_data):
    if not param_data:
        return None
    labels = list(param_data.keys())
    scores = [param_data[p]['avg'] for p in labels]
    colors = [COLORS['success'] if s >= 4 else COLORS['primary_light'] if s >= 3 else COLORS['warning'] if s >= 2 else COLORS['danger'] for s in scores]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=colors, text=[f"{s:.2f}" for s in scores], textposition='outside', textfont=dict(size=15))])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score", tickfont=dict(size=14)), yaxis=dict(autorange="reversed", tickfont=dict(size=12)), height=max(350, len(labels) * 40), margin=dict(l=200, r=60, t=20, b=40), font=dict(size=14))
    return fig

def create_phase_bar_chart(phase_data):
    if not phase_data:
        return None
    labels = list(phase_data.keys())
    scores = [phase_data[p]['avg'] for p in labels]
    colors = [COLORS['success'] if s >= 4 else COLORS['primary_light'] if s >= 3 else COLORS['warning'] if s >= 2 else COLORS['danger'] for s in scores]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=colors, text=[f"{s:.2f}" for s in scores], textposition='outside', textfont=dict(size=16))])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score", tickfont=dict(size=14)), yaxis=dict(autorange="reversed", tickfont=dict(size=14)), height=max(250, len(labels) * 50), margin=dict(l=150, r=60, t=20, b=40), font=dict(size=14))
    return fig

# ============================================================================
# RAPPORT-GENERERING
# ============================================================================
ANONYMOUS_NAMES = [
    "Deltaker A", "Deltaker B", "Deltaker C", "Deltaker D", "Deltaker E",
    "Deltaker F", "Deltaker G", "Deltaker H", "Deltaker I", "Deltaker J",
    "Deltaker K", "Deltaker L", "Deltaker M", "Deltaker N", "Deltaker O"
]

def get_anonymous_name(index):
    if index < len(ANONYMOUS_NAMES):
        return ANONYMOUS_NAMES[index]
    return f"Deltaker {index + 1}"

def generate_html_report(initiative, stats):
    # Generer HTML-rapport
    def create_svg_radar(categories, values, color, title="", width=450, height=400):
        if not categories or not values:
            return ""
        # Dupliser hvis færre enn 3 punkter
        if len(categories) == 1:
            categories = categories * 3
            values = values * 3
        elif len(categories) == 2:
            categories = categories + [categories[0]]
            values = values + [values[0]]
        import math
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 2 - 70
        n = len(categories)
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
            svg += f'<circle cx="{cx}" cy="{cy}" r="{radius * r}" fill="none" stroke="#E8E8E8" stroke-width="1"/>'
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            svg += f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#E8E8E8" stroke-width="1"/>'
        points = []
        for i, val in enumerate(values):
            angle = (2 * math.pi * i / n) - math.pi / 2
            r = (val / 5) * radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x},{y}")
        svg += f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="0.3" stroke="{color}" stroke-width="2"/>'
        for i, cat in enumerate(categories):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + (radius + 45) * math.cos(angle)
            y = cy + (radius + 45) * math.sin(angle)
            label = cat[:18] + "..." if len(cat) > 18 else cat
            svg += f'<text x="{x}" y="{y}" text-anchor="middle" font-size="13" fill="#172141">{label}</text>'
        if title:
            svg += f'<text x="{cx}" y="22" text-anchor="middle" font-size="16" font-weight="bold" fill="#172141">{title}</text>'
        svg += '</svg>'
        return svg

    def create_svg_bar_chart(labels, values, colors, title="", width=500, height=None):
        if not labels or not values:
            return ""
        bar_height = 35
        if height is None:
            height = len(labels) * (bar_height + 10) + 60
        max_val = 5
        bar_area_width = width - 220
        
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        if title:
            svg += f'<text x="{width//2}" y="25" text-anchor="middle" font-size="16" font-weight="bold" fill="#172141">{title}</text>'
        
        y_offset = 50
        for i, (label, val) in enumerate(zip(labels, values)):
            y = y_offset + i * (bar_height + 10)
            bar_width = (val / max_val) * bar_area_width
            color = colors[i] if isinstance(colors, list) else colors
            
            # Label
            display_label = label[:22] + "..." if len(label) > 22 else label
            svg += f'<text x="5" y="{y + bar_height//2 + 5}" font-size="12" fill="#172141">{display_label}</text>'
            # Bar
            svg += f'<rect x="180" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4"/>'
            # Value
            svg += f'<text x="{185 + bar_width}" y="{y + bar_height//2 + 5}" font-size="14" font-weight="bold" fill="#172141">{val:.2f}</text>'
        
        svg += '</svg>'
        return svg

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Modenhetsvurdering - {initiative['name']}</title>
    <style>
        body {{ font-family: 'Source Sans Pro', Arial, sans-serif; padding: 40px; max-width: 1200px; margin: 0 auto; color: #172141; line-height: 1.7; font-size: 16px; }}
        h1 {{ color: #172141; text-align: center; margin-bottom: 5px; font-size: 2rem; }}
        h2 {{ color: #0053A6; border-bottom: 2px solid #64C8FA; padding-bottom: 8px; margin-top: 40px; font-size: 1.6rem; }}
        h3 {{ color: #0053A6; margin-top: 25px; font-size: 1.3rem; }}
        h4 {{ color: #172141; margin-top: 20px; font-size: 1.15rem; }}
        .subtitle {{ text-align: center; color: #0053A6; margin-bottom: 30px; font-size: 1.1rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 1rem; }}
        th {{ background: #0053A6; color: white; padding: 12px; text-align: left; font-size: 1rem; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #E8E8E8; font-size: 1rem; }}
        tr:nth-child(even) {{ background: #F2FAFD; }}
        .metric-row {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .metric-card {{ flex: 1; min-width: 150px; background: #F2FAFD; padding: 18px; border-radius: 8px; border-left: 4px solid #0053A6; text-align: center; }}
        .metric-value {{ font-size: 2.4rem; font-weight: 700; color: #0053A6; }}
        .metric-label {{ font-size: 1rem; color: #666; text-transform: uppercase; }}
        .charts-row {{ display: flex; gap: 30px; margin: 20px 0; flex-wrap: wrap; justify-content: center; }}
        .chart-container {{ flex: 1; min-width: 350px; max-width: 500px; text-align: center; }}
        .item {{ padding: 12px 16px; margin: 8px 0; border-radius: 6px; font-size: 1.05rem; }}
        .item-strength {{ background: #DDFAE2; border-left: 4px solid #35DE6D; }}
        .item-improvement {{ background: rgba(255, 107, 107, 0.15); border-left: 4px solid #FF6B6B; }}
        .benefit-section {{ background: #F8F9FA; padding: 25px; margin: 30px 0; border-radius: 10px; border: 1px solid #E8E8E8; }}
        .benefit-header {{ background: #0053A6; color: white; padding: 15px 20px; margin: -25px -25px 20px -25px; border-radius: 10px 10px 0 0; }}
        .comment-phase {{ background: #64C8FA; color: white; padding: 12px 18px; margin-top: 20px; border-radius: 6px 6px 0 0; font-size: 1.1rem; font-weight: 600; }}
        .comment-question {{ background: #F2FAFD; padding: 12px 18px; border-left: 3px solid #0053A6; margin: 10px 0; }}
        .comment-question h4 {{ margin: 0 0 10px 0; color: #172141; font-size: 1.05rem; }}
        .comment-item {{ background: white; padding: 12px 18px; margin: 10px 0; border-radius: 4px; border: 1px solid #E8E8E8; }}
        .comment-meta {{ font-size: 0.95rem; color: #666; margin-bottom: 6px; }}
        .comment-text {{ color: #172141; font-size: 1.05rem; }}
        .score-badge {{ display: inline-block; background: #64C8FA; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.9rem; margin-left: 8px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E8E8E8; color: #666; font-size: 0.95rem; }}
        .page-break {{ page-break-before: always; }}
    </style>
</head>
<body>
    <h1>Modenhetsvurdering - Gevinstrealisering</h1>
    <p class="subtitle">Gjennomfores i samarbeid med konsern økonomi og digital transformasjon</p>
    
    <h2>DEL 1: Overordnede resultater</h2>
    
    <h3>1.1 Sammendrag</h3>
    <table>
        <tr><td><strong>Endringsinitiativ</strong></td><td>{initiative['name']}</td></tr>
        <tr><td><strong>Beskrivelse</strong></td><td>{initiative.get('description', '-')}</td></tr>
        <tr><td><strong>Rapportdato</strong></td><td>{datetime.now().strftime('%d.%m.%Y')}</td></tr>
        <tr><td><strong>Antall intervjuer</strong></td><td>{stats['total_interviews']}</td></tr>
        <tr><td><strong>Samlet modenhet</strong></td><td><strong>{stats['overall_avg']:.2f}</strong> ({get_score_text(stats['overall_avg'])})</td></tr>
    </table>
    
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">{stats['total_interviews']}</div>
            <div class="metric-label">Intervjuer</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: {'#35DE6D' if stats['overall_avg'] >= 3.5 else '#FFA040' if stats['overall_avg'] >= 2.5 else '#FF6B6B'}">{stats['overall_avg']:.2f}</div>
            <div class="metric-label">Gjennomsnitt</div>
        </div>
        <div class="metric-card" style="border-left-color: #35DE6D;">
            <div class="metric-value" style="color: #35DE6D;">{len(stats['high_maturity'])}</div>
            <div class="metric-label">Styrkeområder</div>
        </div>
        <div class="metric-card" style="border-left-color: #FF6B6B;">
            <div class="metric-value" style="color: #FF6B6B;">{len(stats['low_maturity'])}</div>
            <div class="metric-label">Forbedringsområder</div>
        </div>
    </div>
"""

    if stats['phases']:
        html += "<h3>1.2 Modenhet per fase</h3>"
        html += "<table><tr><th>Fase</th><th>Gjennomsnitt</th><th>Min</th><th>Maks</th></tr>"
        for phase, data in stats['phases'].items():
            html += f"<tr><td>{phase}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['min']:.2f}</td><td>{data['max']:.2f}</td></tr>"
        html += "</table>"
        
        phase_cats = list(stats['phases'].keys())
        phase_vals = [stats['phases'][p]['avg'] for p in phase_cats]
        phase_colors = ['#35DE6D' if v >= 4 else '#64C8FA' if v >= 3 else '#FFA040' if v >= 2 else '#FF6B6B' for v in phase_vals]
        
        html += '<div class="charts-row">'
        html += '<div class="chart-container">'
        html += create_svg_radar(phase_cats, phase_vals, '#0053A6', 'Modenhet per fase')
        html += '</div>'
        html += '<div class="chart-container">'
        html += create_svg_bar_chart(phase_cats, phase_vals, phase_colors, 'Faser - stolpediagram')
        html += '</div>'
        html += '</div>'
        
        if stats['parameters']:
            param_cats = list(stats['parameters'].keys())
            param_vals = [stats['parameters'][p]['avg'] for p in param_cats]
            param_colors = ['#35DE6D' if v >= 4 else '#64C8FA' if v >= 3 else '#FFA040' if v >= 2 else '#FF6B6B' for v in param_vals]
            
            html += '<div class="charts-row">'
            html += '<div class="chart-container">'
            html += create_svg_radar(param_cats, param_vals, '#64C8FA', 'Modenhet per parameter')
            html += '</div>'
            html += '<div class="chart-container">'
            html += create_svg_bar_chart(param_cats, param_vals, param_colors, 'Parametere - stolpediagram')
            html += '</div>'
            html += '</div>'

    html += "<h3>1.3 Styrkeområder og forbedringsområder</h3>"
    html += '<div class="charts-row">'
    if stats['high_maturity']:
        html += '<div class="chart-container">'
        strength_cats = [item['title'][:20] for item in stats['high_maturity'][:8]]
        strength_vals = [item['score'] for item in stats['high_maturity'][:8]]
        html += create_svg_radar(strength_cats, strength_vals, '#35DE6D', 'Styrkeområder')
        html += '</div>'
    if stats['low_maturity']:
        html += '<div class="chart-container">'
        improve_cats = [item['title'][:20] for item in stats['low_maturity'][:8]]
        improve_vals = [item['score'] for item in stats['low_maturity'][:8]]
        html += create_svg_radar(improve_cats, improve_vals, '#FF6B6B', 'Forbedringsområder')
        html += '</div>'
    html += '</div>'
    
    # Bar charts for styrker og forbedringer
    html += '<div class="charts-row">'
    if stats['high_maturity']:
        html += '<div class="chart-container">'
        strength_labels = [f"[{item['phase'][:4]}] {item['title'][:18]}" for item in stats['high_maturity'][:8]]
        strength_vals = [item['score'] for item in stats['high_maturity'][:8]]
        html += create_svg_bar_chart(strength_labels, strength_vals, '#35DE6D', 'Styrker - stolpediagram')
        html += '</div>'
    if stats['low_maturity']:
        html += '<div class="chart-container">'
        improve_labels = [f"[{item['phase'][:4]}] {item['title'][:18]}" for item in stats['low_maturity'][:8]]
        improve_vals = [item['score'] for item in stats['low_maturity'][:8]]
        html += create_svg_bar_chart(improve_labels, improve_vals, '#FF6B6B', 'Forbedring - stolpediagram')
        html += '</div>'
    html += '</div>'

    if stats['high_maturity']:
        html += "<h4>Styrkeområder (score >= 4)</h4>"
        for item in stats['high_maturity'][:10]:
            html += f'<div class="item item-strength"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'

    if stats['low_maturity']:
        html += "<h4>Forbedringsområder (score < 3)</h4>"
        for item in stats['low_maturity'][:10]:
            html += f'<div class="item item-improvement"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'

    if stats['parameters']:
        html += "<h3>1.4 Resultater per parameter</h3>"
        html += "<table><tr><th>Parameter</th><th>Score</th><th>Beskrivelse</th></tr>"
        for name, data in stats['parameters'].items():
            html += f"<tr><td>{name}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['description']}</td></tr>"
        html += "</table>"

    html += "<h3>1.5 Intervjuoversikt (anonymisert)</h3>"
    html += "<table><tr><th>Deltaker</th><th>Dato</th><th>Gevinst</th><th>Fase</th><th>Snitt</th></tr>"
    for idx, interview in enumerate(initiative.get('interviews', {}).values()):
        info = interview.get('info', {})
        total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        avg = total_score / total_answered if total_answered > 0 else 0
        anon_name = get_anonymous_name(idx)
        avg_str = f"{avg:.2f}" if avg > 0 else "-"
        html += f"<tr><td>{anon_name}</td><td>{info.get('date', '-')}</td><td>{info.get('benefit_name', 'Generelt')}</td><td>{info.get('phase', '-')}</td><td>{avg_str}</td></tr>"
    html += "</table>"

    # Del 2: Kommentarer
    html += '<div class="page-break"></div>'
    html += "<h2>DEL 2: Kommentarer</h2>"
    
    for phase in PHASES:
        phase_comments = {}
        for idx, interview in enumerate(initiative.get('interviews', {}).values()):
            responses = interview.get('responses', {}).get(phase, {})
            for q_id, resp in responses.items():
                notes = resp.get('notes', '').strip()
                if notes:
                    if q_id not in phase_comments:
                        phase_comments[q_id] = []
                    anon_name = get_anonymous_name(idx)
                    phase_comments[q_id].append({'participant': anon_name, 'score': resp.get('score', 0), 'notes': notes})
        
        if phase_comments:
            html += f'<div class="comment-phase"><strong>{phase}</strong></div>'
            phase_questions = {str(q['id']): q['title'] for q in questions_data.get(phase, [])}
            for q_id in sorted(phase_comments.keys(), key=lambda x: int(x)):
                q_title = phase_questions.get(q_id, f"Sporsmål {q_id}")
                html += f'<div class="comment-question"><h4>{q_id}. {q_title}</h4>'
                for comment in phase_comments[q_id]:
                    html += f'''<div class="comment-item">
                        <div class="comment-meta">{comment['participant']} <span class="score-badge">Niva {comment['score']}</span></div>
                        <div class="comment-text">{comment['notes']}</div>
                    </div>'''
                html += '</div>'

    html += f'<div class="footer">Generert {datetime.now().strftime("%d.%m.%Y %H:%M")} | Bane NOR - Modenhetsvurdering Gevinstrealisering</div></body></html>'
    return html

def generate_txt_report(initiative, stats):
    # Generer TXT-rapport
    lines = []
    lines.append("=" * 60)
    lines.append("MODENHETSVURDERING - GEVINSTREALISERING")
    lines.append("=" * 60)
    lines.append("")
    lines.append("1. SAMMENDRAG")
    lines.append("-" * 40)
    lines.append(f"Endringsinitiativ: {initiative['name']}")
    lines.append(f"Beskrivelse: {initiative.get('description', '-')}")
    lines.append(f"Rapportdato: {datetime.now().strftime('%d.%m.%Y')}")
    lines.append(f"Antall intervjuer: {stats['total_interviews']}")
    lines.append(f"Samlet modenhet: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})")
    lines.append("")

    if stats['phases']:
        lines.append("2. MODENHET PER FASE")
        lines.append("-" * 40)
        for phase, data in stats['phases'].items():
            lines.append(f"  {phase}: {data['avg']:.2f} (min: {data['min']:.2f}, maks: {data['max']:.2f})")
        lines.append("")

    if stats['high_maturity']:
        lines.append("3. STYRKEområder (score >= 4)")
        lines.append("-" * 40)
        for item in stats['high_maturity'][:10]:
            lines.append(f"  [{item['phase']}] {item['title']}: {item['score']:.2f}")
        lines.append("")

    if stats['low_maturity']:
        lines.append("4. FORBEDRINGSområder (score < 3)")
        lines.append("-" * 40)
        for item in stats['low_maturity'][:10]:
            lines.append(f"  [{item['phase']}] {item['title']}: {item['score']:.2f}")
        lines.append("")

    if stats['parameters']:
        lines.append("5. RESULTATER PER PARAMETER")
        lines.append("-" * 40)
        for name, data in stats['parameters'].items():
            lines.append(f"  {name}: {data['avg']:.2f}")
        lines.append("")

    lines.append("6. INTERVJUOVERSIKT (anonymisert)")
    lines.append("-" * 40)
    for idx, interview in enumerate(initiative.get('interviews', {}).values()):
        info = interview.get('info', {})
        total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        avg = total_score / total_answered if total_answered > 0 else 0
        anon_name = get_anonymous_name(idx)
        avg_str = f"{avg:.2f}" if avg > 0 else "-"
        lines.append(f"  {anon_name} | {info.get('date', '-')} | {info.get('benefit_name', 'Generelt')} | {info.get('phase', '-')} | Snitt: {avg_str}")
    lines.append("")

    lines.append("7. KOMMENTARER")
    lines.append("-" * 40)
    for phase in PHASES:
        phase_comments = {}
        for idx, interview in enumerate(initiative.get('interviews', {}).values()):
            responses = interview.get('responses', {}).get(phase, {})
            for q_id, resp in responses.items():
                notes = resp.get('notes', '').strip()
                if notes:
                    if q_id not in phase_comments:
                        phase_comments[q_id] = []
                    anon_name = get_anonymous_name(idx)
                    phase_comments[q_id].append({'participant': anon_name, 'score': resp.get('score', 0), 'notes': notes})
        if phase_comments:
            lines.append(f"\n  [{phase}]")
            phase_questions = {str(q['id']): q['title'] for q in questions_data.get(phase, [])}
            for q_id in sorted(phase_comments.keys(), key=lambda x: int(x)):
                q_title = phase_questions.get(q_id, f"Sporsmål {q_id}")
                lines.append(f"    {q_id}. {q_title}")
                for comment in phase_comments[q_id]:
                    lines.append(f"      - {comment['participant']} (Niva {comment['score']}): {comment['notes']}")
                lines.append("")

    lines.append("=" * 60)
    lines.append(f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR")
    return "\n".join(lines)

def safe_text(text):
    # Konverter norske tegn til ASCII for PDF
    replacements = {'ae': 'ae', 'Ae': 'Ae', 'o': 'o', 'O': 'O', 'a': 'a', 'A': 'A'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_pdf_report(initiative, stats):
    # Generer PDF-rapport
    if not FPDF_AVAILABLE:
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 10, 'Modenhetsvurdering - Gevinstrealisering', ln=True, align='C')
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 8, 'Bane NOR', ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '1. Sammendrag', ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, safe_text(f"Endringsinitiativ: {initiative['name']}"), ln=True)
        pdf.cell(0, 7, f"Rapportdato: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        pdf.cell(0, 7, f"Antall intervjuer: {stats['total_interviews']}", ln=True)
        pdf.cell(0, 7, safe_text(f"Samlet modenhet: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})"), ln=True)
        pdf.ln(5)

        if stats['phases']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '2. Modenhet per fase', ln=True)
            pdf.set_font('Helvetica', '', 11)
            for phase, data in stats['phases'].items():
                pdf.cell(0, 7, safe_text(f"  {phase}: {data['avg']:.2f}"), ln=True)
            pdf.ln(5)

        if stats['high_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, safe_text('3. Styrkeområder'), ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['high_maturity'][:8]:
                text = safe_text(f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}")
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)

        if stats['low_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, safe_text('4. Forbedringsområder'), ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['low_maturity'][:8]:
                text = safe_text(f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}")
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)

        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 10, f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR", ln=True, align='C')
        return bytes(pdf.output())
    except Exception as e:
        return None

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def show_project_selector(data):
    # Viser prosjektvelger
    st.markdown(f'''
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 style="margin:0;color:{COLORS['primary_dark']};font-size:2rem;font-weight:700;">Modenhetsvurdering</h1>
        <p style="color:{COLORS['primary']};font-size:0.95rem;margin-top:0.3rem;">Gevinstmodenhetsvurdering på tvers av endringsinitiativer i Bane NOR</p>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Apne eksisterende prosjekt")
        if data['initiatives']:
            project_names = {init_id: init['name'] for init_id, init in data['initiatives'].items()}
            selected_project = st.selectbox("Velg prosjekt", options=list(project_names.keys()), format_func=lambda x: project_names[x])
            initiative = data['initiatives'][selected_project]
            has_code = initiative.get('access_code', '') != ''
            if has_code:
                entered_code = st.text_input("Tilgangskode", type="password", key="access_code_input")
                if st.button("Apne prosjekt", use_container_width=True):
                    if entered_code == initiative.get('access_code', ''):
                        st.session_state['current_project'] = selected_project
                        st.rerun()
                    else:
                        st.error("Feil tilgangskode")
            else:
                if st.button("Apne prosjekt", use_container_width=True):
                    st.session_state['current_project'] = selected_project
                    st.rerun()
        else:
            st.info("Ingen prosjekter opprettet enda.")

    with col2:
        st.markdown("### Opprett nytt prosjekt")
        with st.form("new_project_form"):
            new_name = st.text_input("Prosjektnavn", placeholder="F.eks. ERTMS Ostlandet")
            new_desc = st.text_area("Beskrivelse", height=80)
            new_code = st.text_input("Tilgangskode (valgfritt)", type="password")
            new_code_confirm = st.text_input("Bekreft tilgangskode", type="password")
            if st.form_submit_button("Opprett prosjekt", use_container_width=True):
                if not new_name:
                    st.error("Prosjektnavn er pakrevd")
                elif new_code and new_code != new_code_confirm:
                    st.error("Tilgangskodene matcher ikke")
                else:
                    init_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    data['initiatives'][init_id] = {
                        'name': new_name,
                        'description': new_desc,
                        'access_code': new_code,
                        'created': datetime.now().isoformat(),
                        'benefits': {},
                        'interviews': {}
                    }
                    persist_data()
                    st.session_state['current_project'] = init_id
                    st.success(f"'{new_name}' opprettet!")
                    st.rerun()

def show_main_app(data, current_project_id):
    # Viser hovedapplikasjonen
    initiative = data['initiatives'][current_project_id]

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("< Bytt prosjekt"):
            del st.session_state['current_project']
            st.rerun()
    with col2:
        st.markdown(f'''
        <div style="text-align:center;">
            <h1 style="margin:0;color:{COLORS['primary_dark']};font-size:1.8rem;font-weight:700;">Modenhetsvurdering</h1>
            <p style="color:{COLORS['primary']};font-size:1rem;margin-top:0.2rem;"><strong>{initiative['name']}</strong></p>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        if st.button("Oppdater"):
            refresh_data()
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Om vurderingen", "Gevinster", "Intervju", "Resultater", "Rapport"])

    # TAB 1: OM VURDERINGEN
    with tab1:
        st.markdown(HENSIKT_TEKST)
        st.markdown("---")
        st.markdown("### Faser i gevinstlivssyklusen")
        cols = st.columns(4)
        for i, phase in enumerate(PHASES):
            with cols[i]:
                st.markdown(f'''<div style="text-align:center;padding:15px;background:{COLORS['gray_light']};border-radius:8px;border-top:4px solid {COLORS['primary']};">
                    <p style="margin:0;font-weight:600;color:{COLORS['primary_dark']};">{phase}</p>
                </div>''', unsafe_allow_html=True)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Tilgjengelige roller")
            for role_name, role_data in ROLES.items():
                st.markdown(f"**{role_name}**: {role_data['description']}")
        with col2:
            st.markdown("### Tilgjengelige parametere")
            for param_name, param_data in PARAMETERS.items():
                st.markdown(f"**{param_name}**: {param_data['description']}")

    # TAB 2: GEVINSTER
    with tab2:
        st.markdown(f"## Gevinster for {initiative['name']}")
        st.write(f"**Beskrivelse:** {initiative.get('description', 'Ingen')}")
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col2:
            st.markdown("### Legg til gevinst")
            with st.form("add_benefit_form"):
                new_benefit = st.text_input("Gevinstnavn", placeholder="F.eks. Redusert reisetid")
                if st.form_submit_button("Legg til", use_container_width=True):
                    if new_benefit:
                        if 'benefits' not in initiative:
                            initiative['benefits'] = {}
                        initiative['benefits'][datetime.now().strftime("%Y%m%d%H%M%S%f")] = {
                            'name': new_benefit,
                            'created': datetime.now().isoformat()
                        }
                        persist_data()
                        st.rerun()
        with col1:
            st.markdown("### Registrerte gevinster")
            if initiative.get('benefits'):
                for ben_id, benefit in initiative.get('benefits', {}).items():
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"- **{benefit['name']}**")
                    if col_b.button("Slett", key=f"del_ben_{ben_id}"):
                        del initiative['benefits'][ben_id]
                        persist_data()
                        st.rerun()
            else:
                st.info("Ingen gevinster registrert enda.")
        st.markdown("---")
        st.markdown("### Prosjektinnstillinger")
        with st.expander("Endre tilgangskode"):
            with st.form("change_code_form"):
                current_code = st.text_input("Navaerende kode", type="password")
                new_code = st.text_input("Ny tilgangskode", type="password")
                new_code_confirm = st.text_input("Bekreft ny kode", type="password")
                if st.form_submit_button("Oppdater kode"):
                    if current_code != initiative.get('access_code', ''):
                        st.error("Feil navaerende kode")
                    elif new_code != new_code_confirm:
                        st.error("Nye koder matcher ikke")
                    else:
                        initiative['access_code'] = new_code
                        persist_data()
                        st.success("Tilgangskode oppdatert!")
        with st.expander("Slett prosjekt", expanded=False):
            st.warning("Dette vil slette prosjektet og alle tilhorende data permanent!")
            confirm_name = st.text_input("Skriv prosjektnavnet for a bekrefte sletting")
            if st.button("Slett prosjekt permanent", type="primary"):
                if confirm_name == initiative['name']:
                    del data['initiatives'][current_project_id]
                    persist_data()
                    del st.session_state['current_project']
                    st.rerun()
                else:
                    st.error("Prosjektnavnet stemmer ikke")

    # TAB 3: INTERVJU
    with tab3:
        st.markdown("## Gjennomfor intervju")
        if 'active_interview' not in st.session_state:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Start nytt intervju")
                benefit_options = {"Generelt for initiativet": "all"}
                for ben_id, ben in initiative.get('benefits', {}).items():
                    benefit_options[ben['name']] = ben_id
                selected_benefit_name = st.selectbox("Gevinst", options=list(benefit_options.keys()))
                selected_benefit_id = benefit_options[selected_benefit_name]
                selected_phase = st.selectbox("Fase", options=PHASES)
                focus_mode = st.radio("Fokusmodus", options=["Rollebasert", "Parameterbasert", "Alle sporsmål"], horizontal=True)
                selected_role = None
                selected_params = []
                recommended = []
                if focus_mode == "Rollebasert":
                    selected_role = st.selectbox("Rolle", options=list(ROLES.keys()))
                    recommended = get_recommended_questions("role", selected_role, selected_phase)
                    st.caption(ROLES[selected_role]['description'])
                    st.success(f"{len(recommended)} anbefalte sporsmål. Alle 23 tilgjengelige.")
                elif focus_mode == "Parameterbasert":
                    selected_params = st.multiselect("Parametere", options=list(PARAMETERS.keys()), default=list(PARAMETERS.keys())[:2])
                    recommended = get_recommended_questions("parameter", selected_params, selected_phase)
                    st.success(f"{len(recommended)} anbefalte sporsmål. Alle 23 tilgjengelige.")
                with st.form("new_interview"):
                    interviewer = st.text_input("Intervjuer")
                    interviewee = st.text_input("Intervjuobjekt")
                    role_title = st.text_input("Stilling")
                    date = st.date_input("Dato", value=datetime.now())
                    if st.form_submit_button("Start intervju", use_container_width=True):
                        if interviewee:
                            interview_id = datetime.now().strftime("%Y%m%d%H%M%S")
                            initiative['interviews'][interview_id] = {
                                'info': {'interviewer': interviewer, 'interviewee': interviewee, 'role': role_title, 'date': date.strftime('%Y-%m-%d'), 'phase': selected_phase, 'benefit_id': selected_benefit_id, 'benefit_name': selected_benefit_name, 'focus_mode': focus_mode, 'selected_role': selected_role, 'selected_params': selected_params},
                                'recommended_questions': recommended, 'responses': {}
                            }
                            persist_data()
                            st.session_state['active_interview'] = {'init_id': current_project_id, 'interview_id': interview_id}
                            st.rerun()
            with col2:
                st.markdown("### Fortsett eksisterende")
                if initiative.get('interviews'):
                    interview_options = {f"{i['info']['interviewee']} - {i['info'].get('benefit_name', 'Generelt')} ({i['info'].get('phase', '?')})": iid for iid, i in initiative['interviews'].items()}
                    selected_interview = st.selectbox("Velg intervju", options=list(interview_options.keys()))
                    if st.button("Fortsett", use_container_width=True):
                        st.session_state['active_interview'] = {'init_id': current_project_id, 'interview_id': interview_options[selected_interview]}
                        st.rerun()
                else:
                    st.info("Ingen intervjuer registrert enda.")
        else:
            active = st.session_state['active_interview']
            if active['init_id'] in data['initiatives']:
                active_initiative = data['initiatives'][active['init_id']]
                if active['interview_id'] in active_initiative['interviews']:
                    interview = active_initiative['interviews'][active['interview_id']]
                    phase = interview['info'].get('phase', 'Planlegging')
                    recommended = interview.get('recommended_questions', [])
                    st.markdown(f"### Intervju: {interview['info']['interviewee']}")
                    st.caption(f"Gevinst: {interview['info'].get('benefit_name', 'Generelt')} | Fase: {phase}")
                    if phase not in interview['responses']:
                        interview['responses'][phase] = {}
                    answered = sum(1 for q_id in range(1, 25) if interview['responses'][phase].get(str(q_id), {}).get('score', 0) > 0)
                    st.progress(answered / 24)
                    st.caption(f"Besvart: {answered} av 24")
                    questions = questions_data[phase]
                    recommended_qs = [q for q in questions if q['id'] in recommended]
                    other_qs = [q for q in questions if q['id'] not in recommended]
                    if recommended_qs:
                        st.markdown("### Anbefalte sporsmål")
                        for q in recommended_qs:
                            q_id_str = str(q['id'])
                            if q_id_str not in interview['responses'][phase]:
                                interview['responses'][phase][q_id_str] = {'score': 0, 'notes': ''}
                            resp = interview['responses'][phase][q_id_str]
                            status = "V" if resp['score'] > 0 else "O"
                            with st.expander(f"{status} {q['id']}. {q['title']}" + (f" - Niva {resp['score']}" if resp['score'] > 0 else ""), expanded=(resp['score'] == 0)):
                                st.markdown(f"**{q['question']}**")
                                for level in q['scale']:
                                    st.write(f"- {level}")
                                new_score = st.radio("Niva:", options=[0,1,2,3,4,5], index=resp['score'], key=f"s_{phase}_{q['id']}", horizontal=True, format_func=lambda x: "Ikke vurdert" if x == 0 else f"Niva {x}")
                                new_notes = st.text_area("Notater:", value=resp['notes'], key=f"n_{phase}_{q['id']}", height=80)
                                if st.button("Lagre", key=f"save_{phase}_{q['id']}"):
                                    interview['responses'][phase][q_id_str] = {'score': new_score, 'notes': new_notes}
                                    persist_data()
                                    st.rerun()
                    if other_qs:
                        st.markdown("### Andre sporsmål")
                        for q in other_qs:
                            q_id_str = str(q['id'])
                            if q_id_str not in interview['responses'][phase]:
                                interview['responses'][phase][q_id_str] = {'score': 0, 'notes': ''}
                            resp = interview['responses'][phase][q_id_str]
                            status = "V" if resp['score'] > 0 else "O"
                            with st.expander(f"{status} {q['id']}. {q['title']}" + (f" - Niva {resp['score']}" if resp['score'] > 0 else ""), expanded=False):
                                st.markdown(f"**{q['question']}**")
                                for level in q['scale']:
                                    st.write(f"- {level}")
                                new_score = st.radio("Niva:", options=[0,1,2,3,4,5], index=resp['score'], key=f"s_{phase}_{q['id']}", horizontal=True, format_func=lambda x: "Ikke vurdert" if x == 0 else f"Niva {x}")
                                new_notes = st.text_area("Notater:", value=resp['notes'], key=f"n_{phase}_{q['id']}", height=80)
                                if st.button("Lagre", key=f"save_{phase}_{q['id']}"):
                                    interview['responses'][phase][q_id_str] = {'score': new_score, 'notes': new_notes}
                                    persist_data()
                                    st.rerun()
                    col1, col2 = st.columns(2)
                    if col1.button("Avslutt intervju", use_container_width=True):
                        del st.session_state['active_interview']
                        st.rerun()
                    if col2.button("Avbryt", use_container_width=True):
                        del st.session_state['active_interview']
                        st.rerun()

    # TAB 4: RESULTATER
    with tab4:
        st.markdown("## Resultater og analyse")
        benefit_filter_options = {"Alle gevinster": "all"}
        for ben_id, ben in initiative.get('benefits', {}).items():
            benefit_filter_options[ben['name']] = ben_id
        benefit_filter_name = st.selectbox("Filtrer pa gevinst:", options=list(benefit_filter_options.keys()))
        benefit_filter = benefit_filter_options[benefit_filter_name]
        stats = calculate_stats(initiative, benefit_filter if benefit_filter != "all" else None)
        if not stats or stats['total_interviews'] == 0:
            st.info("Ingen intervjuer gjennomfort enda")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f'<div class="metric-card"><div class="metric-label">Intervjuer</div><div class="metric-value">{stats["total_interviews"]}</div></div>', unsafe_allow_html=True)
            col2.markdown(f'<div class="metric-card"><div class="metric-label">Gjennomsnitt</div><div class="metric-value" style="color: {get_score_color(stats["overall_avg"])}">{stats["overall_avg"]:.2f}</div></div>', unsafe_allow_html=True)
            col3.markdown(f'<div class="metric-card" style="border-left-color:{COLORS["success"]}"><div class="metric-label">Styrker</div><div class="metric-value" style="color: {COLORS["success"]}">{len(stats["high_maturity"])}</div></div>', unsafe_allow_html=True)
            col4.markdown(f'<div class="metric-card" style="border-left-color:{COLORS["danger"]}"><div class="metric-label">Forbedring</div><div class="metric-value" style="color: {COLORS["danger"]}">{len(stats["low_maturity"])}</div></div>', unsafe_allow_html=True)
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Modenhet per fase")
                if stats['phases']:
                    for phase_name, phase_data in stats['phases'].items():
                        st.markdown(f'''<div style="display:flex;align-items:center;gap:10px;padding:10px;background:{COLORS['gray_light']};border-radius:6px;margin:5px 0;font-size:1.1rem;">
                            <span style="flex:1;font-weight:600;">{phase_name}</span>
                            <span style="color:{get_score_color(phase_data['avg'])};font-weight:700;font-size:1.2rem;">{phase_data['avg']:.2f}</span>
                        </div>''', unsafe_allow_html=True)
                    fig = create_phase_radar(stats['phases'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    fig_bar = create_phase_bar_chart(stats['phases'])
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)
            with col2:
                st.markdown("### Modenhet per parameter")
                if stats['parameters']:
                    fig = create_parameter_radar(stats['parameters'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    fig_bar = create_parameter_bar_chart(stats['parameters'])
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Styrkeområder")
                if stats['high_maturity']:
                    fig = create_strength_radar(stats['high_maturity'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    fig_bar = create_strength_bar_chart(stats['high_maturity'])
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)
                    st.markdown("#### Detaljer")
                    for item in stats['high_maturity'][:5]:
                        st.markdown(f'<div class="strength-card"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                else:
                    st.info("Ingen styrkeområder identifisert")
            with col2:
                st.markdown("### Forbedringsområder")
                if stats['low_maturity']:
                    fig = create_improvement_radar(stats['low_maturity'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    fig_bar = create_improvement_bar_chart(stats['low_maturity'])
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True)
                    st.markdown("#### Detaljer")
                    for item in stats['low_maturity'][:5]:
                        st.markdown(f'<div class="improvement-card"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                else:
                    st.success("Ingen kritiske forbedringsområder!")

    # TAB 5: RAPPORT
    with tab5:
        st.markdown("## Generer rapport")
        stats = calculate_stats(initiative)
        if not stats or stats['total_interviews'] == 0:
            st.info("Gjennomfor minst ett intervju forst")
        else:
            st.markdown("### Eksportformat")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### CSV")
                csv_data = []
                for phase in stats['questions']:
                    for q_id, q_data in stats['questions'][phase].items():
                        csv_data.append({'Fase': phase, 'SporsmålID': q_id, 'Tittel': q_data['title'], 'Gjennomsnitt': round(q_data['avg'], 2), 'AntallSvar': q_data['count']})
                csv_df = pd.DataFrame(csv_data)
                st.download_button("Last ned CSV", data=csv_df.to_csv(index=False, sep=';'), file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            with col2:
                st.markdown("#### TXT")
                txt_report = generate_txt_report(initiative, stats)
                st.download_button("Last ned TXT", data=txt_report, file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain", use_container_width=True)
            with col3:
                st.markdown("#### PDF")
                if FPDF_AVAILABLE:
                    try:
                        pdf_data = generate_pdf_report(initiative, stats)
                        if pdf_data:
                            st.download_button("Last ned PDF", data=pdf_data, file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
                        else:
                            st.warning("Kunne ikke generere PDF")
                    except Exception as e:
                        st.error(f"Feil ved PDF: {e}")
                else:
                    st.info("For PDF: pip install fpdf2")
            st.markdown("---")
            st.markdown("#### HTML-rapport")
            html_report = generate_html_report(initiative, stats)
            st.download_button("Last ned HTML", data=html_report, file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html", use_container_width=True)
            st.markdown("---")
            st.markdown("### Intervjuoversikt")
            interview_data = []
            for iid, interview in initiative.get('interviews', {}).items():
                info = interview.get('info', {})
                total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                avg = total_score / total_answered if total_answered > 0 else 0
                interview_data.append({'Dato': info.get('date', ''), 'Intervjuobjekt': info.get('interviewee', ''), 'Gevinst': info.get('benefit_name', 'Generelt'), 'Fase': info.get('phase', ''), 'Besvarte': total_answered, 'Snitt': round(avg, 2) if avg > 0 else '-'})
            if interview_data:
                st.dataframe(pd.DataFrame(interview_data), use_container_width=True)

def main():
    # Hovedfunksjon
    data = get_data()
    if 'current_project' not in st.session_state:
        show_project_selector(data)
    else:
        current_project_id = st.session_state['current_project']
        if current_project_id not in data['initiatives']:
            del st.session_state['current_project']
            st.rerun()
        else:
            show_main_app(data, current_project_id)

if __name__ == "__main__":
    main()
