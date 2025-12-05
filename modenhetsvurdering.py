"""
MODENHETSVURDERING - GEVINSTREALISERING
Gjennomfores i samarbeid med konsern okonomi og digital transformasjon

For PDF-rapporter, installer:
  pip install fpdf2
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

st.set_page_config(
    page_title="Modenhetsvurdering - Bane NOR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "modenhet_data.pkl"

# ============================================================================
# FLERBRUKER-STØTTE
# ============================================================================
import uuid

def get_session_id():
    """Hent eller opprett en unik session ID for denne brukeren"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    return st.session_state.session_id

def get_data_file():
    """Returner datafil for denne sesjonen"""
    # Bruk felles datafil for alle (standard oppførsel)
    # For separate filer per bruker, kommenter ut linjen under og bruk session-spesifikk fil
    return DATA_FILE
    # return f"modenhet_data_{get_session_id()}.pkl"

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
Modenhetsvurderingen har som formål å synliggjøre gode erfaringer og identifisere forbedringsområder i vårt arbeid med gevinster. Vi ønsker å lære av hverandre, dele beste praksis og hjelpe initiativer til å lykkes bedre med å skape og realisere gevinster.

Et sentralt fokusområde er å sikre at gevinstene vi arbeider med er konkrete og realitetsorienterte.

### Hvem inviteres?
Vi ønsker å intervjue alle som har vært eller er involvert i gevinstarbeidet.

### Hva vurderes?
Intervjuene dekker hele gevinstlivssyklusen – fra planlegging og gjennomføring til realisering og evaluering.

### Gevinster i endringsinitiativ
Et endringsinitiativ kan ha flere konkrete gevinster. Intervjuene kan gjennomføres med fokus på én spesifikk gevinst, eller for initiativet som helhet.
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
            "Planlegging": [2, 8, 9, 12, 13, 18, 19, 20, 22],
            "Gjennomføring": [2, 8, 9, 12, 13, 17, 18, 19, 20, 22],
            "Realisering": [1, 2, 8, 9, 12, 13, 17, 18, 19, 20, 22],
            "Realisert": [1, 2, 8, 12, 13, 17, 18, 19, 20, 22]
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
            "Planlegging": [2, 4, 8, 14, 16, 19, 20, 21, 22],
            "Gjennomføring": [2, 4, 8, 14, 16, 19, 20, 22],
            "Realisering": [2, 4, 8, 16, 19, 20, 22],
            "Realisert": [2, 4, 8, 16, 19, 20, 22]
        }
    },
    "Controller / Økonomi": {
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
            "Planlegging": [2, 8, 9, 18, 19, 20, 22, 23],
            "Gjennomføring": [2, 8, 9, 18, 19, 20, 22, 23],
            "Realisering": [1, 2, 8, 9, 18, 19, 20, 22, 23],
            "Realisert": [1, 2, 8, 18, 19, 20, 22, 23]
        }
    },
    "Interessent": {
        "description": "Personer som opplever endringer og effekter i praksis (f.eks. montører, operatører)",
        "recommended_questions": {
            "Planlegging": [8, 9, 12, 13, 18, 19, 22],
            "Gjennomføring": [8, 9, 12, 13, 18, 19, 22],
            "Realisering": [8, 9, 12, 13, 18, 19, 20, 22],
            "Realisert": [8, 12, 13, 18, 19, 20, 22]
        }
    }
}

PARAMETERS = {
    "Strategisk forankring": {"description": "Strategisk retning, kobling til mål og KPI-er", "questions": [2, 4]},
    "Gevinstkart og visualisering": {"description": "Gevinstkart, sammenhenger mellom tiltak og effekter", "questions": [3]},
    "Nullpunkter og estimater": {"description": "Kvalitet på nullpunkter, estimater og datagrunnlag", "questions": [6, 7, 11]},
    "Interessenter og forankring": {"description": "Interessentengasjement, kommunikasjon og forankring", "questions": [8, 19]},
    "Eierskap og ansvar": {"description": "Roller, ansvar og eierskap for gevinstuttak", "questions": [20]},
    "Forutsetninger og risiko": {"description": "Gevinstforutsetninger, risiko og ulemper", "questions": [9, 10, 14, 15]},
    "Gevinstrealiseringsplan": {"description": "Plan som operativt styringsverktøy", "questions": [16, 17]},
    "Effektivitet og produktivitet": {"description": "Måling, disponering og bærekraft", "questions": [12, 13]},
    "Læring og forbedring": {"description": "Bruk av tidligere erfaringer og kontinuerlig læring", "questions": [1]},
    "Momentum og tidlig gevinstuttak": {"description": "Bygge momentum gjennom tidlig gevinstrealisering", "questions": [5, 21, 22, 23]}
}

PHASES = ["Planlegging", "Gjennomføring", "Realisering", "Realisert"]

questions_data = {
    "Planlegging": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster?", "scale": ["Nivå 1: Ingen læring fra tidligere arbeid anvendt.", "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.", "Nivå 3: Læring inkludert i planlegging for enkelte områder.", "Nivå 4: Systematisk bruk av tidligere gevinstdata i planlegging og estimering.", "Nivå 5: Kontinuerlig læring integrert i planleggingsprosessen og gevinststrategien."]},
        {"id": 2, "title": "Strategisk retning og gevinstforståelse", "question": "Hvilke gevinster arbeider dere med, og hvorfor er de viktige for organisasjonens strategiske mål?", "scale": ["Nivå 1: Gevinster er vagt definert, uten tydelig kobling til strategi.", "Nivå 2: Gevinster er identifisert, men mangler klare kriterier og prioritering.", "Nivå 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerhet.", "Nivå 4: Gevinster er tydelig koblet til strategiske mål med konkrete måltall.", "Nivå 5: Gevinster er fullt integrert i styringssystemet og brukes i beslutninger."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Er gevinstene synliggjort i gevinstkartet, med tydelig sammenheng mellom tiltak, effekter og mål?", "scale": ["Nivå 1: Gevinstkart finnes ikke eller er utdatert.", "Nivå 2: Et foreløpig gevinstkart eksisterer, men dekker ikke hele området.", "Nivå 3: Kartet inkluderer hovedgevinster, men mangler validering og detaljer.", "Nivå 4: Kartet er brukt aktivt i planlegging og oppfølging.", "Nivå 5: Gevinstkartet oppdateres kontinuerlig og er integrert i styringsdialoger."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Er gevinstene tydelig knyttet til strategiske mål og eksisterende KPI-er?", "scale": ["Nivå 1: Ingen kobling mellom gevinster og strategi eller KPI-er.", "Nivå 2: Kobling er antatt, men ikke dokumentert.", "Nivå 3: Kobling er etablert for enkelte KPI-er, men ikke konsistent.", "Nivå 4: Tydelig kobling mellom gevinster og relevante KPI-er.", "Nivå 5: Koblingen følges opp i styringssystem og rapportering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Er det tydelig avklart hvilke effekter som stammer fra programmet versus andre tiltak eller økte rammer?", "scale": ["Nivå 1: Ingen skille mellom program- og eksterne effekter.", "Nivå 2: Delvis omtalt, men uklart hva som er innenfor programmet.", "Nivå 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.", "Nivå 4: Avgrensning er dokumentert og anvendt i beregninger.", "Nivå 5: Effektisolering er standard praksis og brukes systematisk."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Er nullpunkter og estimater etablert, testet og dokumentert på en konsistent og troverdig måte?", "scale": ["Nivå 1: Nullpunkter mangler eller bygger på uprøvde antagelser.", "Nivå 2: Enkelte nullpunkter finnes, men uten felles metode.", "Nivå 3: Nullpunkter og estimater er definert, men med høy usikkerhet.", "Nivå 4: Nullpunkter og estimater er basert på testede data og validerte metoder.", "Nivå 5: Nullpunkter og estimater kvalitetssikres jevnlig og brukes aktivt til læring."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Finnes formell prosess for hypotesetesting på representative caser?", "scale": ["Nivå 1: Ikke etablert/uklart; ingen dokumenterte praksiser.", "Nivå 2: Delvis definert; uformell praksis uten forankring/validering.", "Nivå 3: Etablert for deler av området; variabel kvalitet.", "Nivå 4: Godt forankret og systematisk anvendt; måles og følges opp.", "Nivå 5: Fullt integrert i styring; kontinuerlig forbedring og læring."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Ble relevante interessenter involvert i utarbeidelsen av gevinstgrunnlag?", "scale": ["Nivå 1: Ingen involvering av interessenter.", "Nivå 2: Begrenset og ustrukturert involvering.", "Nivå 3: Bred deltakelse, men uten systematisk prosess.", "Nivå 4: Systematisk og koordinert involvering med klar rollefordeling.", "Nivå 5: Kontinuerlig engasjement med dokumentert medvirkning."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Er alle vesentlige forutsetninger ivaretatt for å muliggjøre gevinstrealisering?", "scale": ["Nivå 1: Ingen kartlegging av gevinstforutsetninger.", "Nivå 2: Noen forutsetninger er identifisert, men ikke systematisk dokumentert.", "Nivå 3: Hovedforutsetninger er dokumentert, men uten klar eierskap.", "Nivå 4: Alle kritiske forutsetninger er kartlagt med tildelt ansvar.", "Nivå 5: Gevinstforutsetninger er integrert i risikostyring og oppfølges kontinuerlig."]},
        {"id": 10, "title": "Prinsipielle og vilkårsmessige kriterier", "question": "Er forutsetninger og kriterier som påvirker gevinstene tydelig definert og dokumentert?", "scale": ["Nivå 1: Ingen kriterier dokumentert.", "Nivå 2: Kriterier er beskrevet uformelt.", "Nivå 3: Kriterier dokumentert i deler av planverket.", "Nivå 4: Vesentlige kriterier er analysert og håndtert i gevinstrealiseringsplanen.", "Nivå 5: Kriterier overvåkes, følges opp og inngår i risikostyringen."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Er det oppnådd enighet blant nøkkelinteressenter om nullpunkter og estimater?", "scale": ["Nivå 1: Ingen enighet eller dokumentert praksis.", "Nivå 2: Delvis enighet, men ikke formalisert.", "Nivå 3: Enighet for hovedestimater, men med reservasjoner.", "Nivå 4: Full enighet dokumentert og forankret.", "Nivå 5: Kontinuerlig dialog og justering av estimater med interessentene."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert mellom prissatte og ikke-prissatte gevinster?", "scale": ["Nivå 1: Ingen plan for disponering eller måling av besparelser.", "Nivå 2: Delvis oversikt, men ikke dokumentert eller fulgt opp.", "Nivå 3: Plan finnes for enkelte områder, men uten systematikk.", "Nivå 4: Disponering og effekter dokumentert og målt.", "Nivå 5: Frigjorte ressurser disponeres strategisk og måles som del av gevinstrealiseringen."]},
        {"id": 13, "title": "Måling av effektivitet og produktivitet", "question": "Hvordan måles økt effektivitet og produktivitet som følge av besparelser?", "scale": ["Nivå 1: Ingen måling av effektivitet eller produktivitet.", "Nivå 2: Enkelte målinger, men ikke systematisk.", "Nivå 3: Måling for enkelte gevinster, men begrenset fokus på bærekraft.", "Nivå 4: Systematisk måling og vurdering av om gevinster opprettholdes over tid.", "Nivå 5: Måling integrert i gevinstoppfølgingen, bærekraftige gevinster sikres."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Er mulige negative konsekvenser eller ulemper knyttet til operasjonelle forhold identifisert, vurdert og håndtert i planen?", "scale": ["Nivå 1: Negative effekter ikke vurdert.", "Nivå 2: Kjent, men ikke håndtert.", "Nivå 3: Beskrevet, men ikke fulgt opp systematisk.", "Nivå 4: Håndtert og overvåket med tilpasning til ulike operasjonelle scenarier.", "Nivå 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan sikres det at balansen mellom gevinster og ulemper vurderes i styringsdialoger?", "scale": ["Nivå 1: Ingen vurdering av balanse.", "Nivå 2: Diskuteres uformelt.", "Nivå 3: Del av enkelte oppfølgingsmøter.", "Nivå 4: Systematisk vurdert i gevinststyring.", "Nivå 5: Inngår som fast punkt i styrings- og gevinstdialoger."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Er det utarbeidet en forankret gevinstrealiseringsplan som beskriver hvordan gevinstene skal hentes ut og måles?", "scale": ["Nivå 1: Ingen formell gevinstrealiseringsplan.", "Nivå 2: Utkast til plan finnes, men er ufullstendig.", "Nivå 3: Plan er etablert, men ikke validert eller periodisert.", "Nivå 4: Planen er forankret, oppdatert og koblet til gevinstkartet.", "Nivå 5: Planen brukes aktivt som styringsdokument med revisjon."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan sikres det at gevinstrealiseringsplanen fungerer som en operativ handlingsplan i linjen med tilpasning til ulike strekningsforhold?", "scale": ["Nivå 1: Planen brukes ikke som operativt styringsverktøy.", "Nivå 2: Plan finnes, men uten operativ oppfølging.", "Nivå 3: Planen følges delvis opp i linjen.", "Nivå 4: Planen brukes aktivt som handlingsplan og styringsverktøy.", "Nivå 5: Gevinstplanen er fullt operativt integrert i linjens handlingsplaner og rapportering med tilpasning til lokale forhold."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Er organisasjonen forberedt og har den tilstrekkelig kapasitet til å ta imot endringer og nye arbeidsformer som følger av programmet?", "scale": ["Nivå 1: Ingen plan for endringsberedskap.", "Nivå 2: Kapasitet vurderes uformelt, men ikke håndtert.", "Nivå 3: Endringskapasitet omtales, men uten konkrete tiltak.", "Nivå 4: Tilfredsstillende beredskap etablert og koordinert med linjen.", "Nivå 5: Endringskapasitet er strukturert, overvåket og integrert i styring med tilpasning til lokale forhold."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Er gevinstgrunnlag, roller og forventninger godt kommunisert i organisasjonen?", "scale": ["Nivå 1: Ingen felles forståelse eller kommunikasjon.", "Nivå 2: Informasjon deles sporadisk.", "Nivå 3: Kommunikasjon er planlagt, men ikke systematisk målt.", "Nivå 4: Kommunikasjon er systematisk og forankret i organisasjonen.", "Nivå 5: Forankring skjer løpende som del av styringsdialog."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?", "scale": ["Nivå 1: Ansvar er uklart eller mangler.", "Nivå 2: Ansvar er delvis definert, men ikke praktisert.", "Nivå 3: Ansvar er kjent, men samhandling varierer.", "Nivå 4: Roller og ansvar fungerer godt i praksis.", "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Er gevinstrealiseringsplanen periodisert, validert og godkjent av ansvarlige?", "scale": ["Nivå 1: Ingen tidsplan eller forankring.", "Nivå 2: Tidsplan foreligger, men ikke validert.", "Nivå 3: Delvis forankret hos enkelte ansvarlige/eiere.", "Nivå 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.", "Nivå 5: Planen brukes aktivt i styringsdialog og rapportering."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Opplever dere at gevinstplanen og estimatene oppleves realistiske og engasjerer eierne og interessentene?", "scale": ["Nivå 1: Ingen troverdighet eller engasjement.", "Nivå 2: Begrenset tillit til estimater.", "Nivå 3: Delvis aksept, men varierende engasjement.", "Nivå 4: Høy troverdighet og engasjement.", "Nivå 5: Sterk troverdighet og aktiv motivasjon i organisasjonen."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan planlegges det for å bygge momentum og realisere tidlige gevinster underveis i programmet?", "scale": ["Nivå 1: Ingen plan for tidlig gevinstuttak eller oppbygging av momentum.", "Nivå 2: Enkelte uformelle vurderinger av tidlige gevinster.", "Nivå 3: Plan for tidlig gevinstuttak er identifisert, men ikke koordinert.", "Nivå 4: Strukturert tilnærming for tidlig gevinstuttak med tildelt ansvar.", "Nivå 5: Tidlig gevinstuttak er integrert i programmets DNA og brukes aktivt for å bygge momentum."]}
    ],
    "Gjennomføring": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan brukes erfaringer og læring fra tidligere prosjekter og gevinstarbeid til å justere tiltak under gjennomføringen?", "scale": ["Nivå 1: Ingen læring fra tidligere arbeid anvendt under gjennomføring.", "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt for justering.", "Nivå 3: Læring inkludert i justering for enkelte områder under gjennomføring.", "Nivå 4: Systematisk bruk av tidligere gevinstdata for å justere tiltak underveis.", "Nivå 5: Kontinuerlig læring integrert i gjennomføringsprosessen og gevinstjustering."]},
        {"id": 2, "title": "Strategisk retning og gevinstforståelse", "question": "Hvordan opprettholdes den strategiske retningen og forståelsen av gevinster under gjennomføring?", "scale": ["Nivå 1: Strategisk kobling glemmes under gjennomføring.", "Nivå 2: Strategi omtales, men ikke operasjonalisert i gjennomføring.", "Nivå 3: Strategisk kobling vedlikeholdes i deler av gjennomføringen.", "Nivå 4: Tydelig strategisk retning i gjennomføring med regelmessig oppdatering.", "Nivå 5: Strategi og gevinstforståelse dynamisk tilpasses underveis basert på læring."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Hvordan brukes gevinstkartet aktivt under gjennomføring for å styre og kommunisere fremdrift?", "scale": ["Nivå 1: Gevinstkartet brukes ikke under gjennomføring.", "Nivå 2: Gevinstkartet vises, men ikke aktivt brukt.", "Nivå 3: Gevinstkartet oppdateres og brukes i noen beslutninger.", "Nivå 4: Gevinstkartet er aktivt styringsverktøy under gjennomføring.", "Nivå 5: Gevinstkartet brukes dynamisk til å justere strategi og tiltak underveis."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Hvordan følges opp den strategiske koblingen og KPI-ene under gjennomføring?", "scale": ["Nivå 1: Ingen oppfølging av strategisk kobling under gjennomføring.", "Nivå 2: KPI-er måles, men kobling til strategi mangler.", "Nivå 3: Noen KPI-er følges opp med strategisk kobling.", "Nivå 4: Systematisk oppfølging av KPI-er med tydelig strategisk kobling.", "Nivå 5: Dynamisk justering av KPI-er basert på strategisk utvikling underveis."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Hvordan håndteres avgrensning av programgevinster under gjennomføring når nye forhold oppstår?", "scale": ["Nivå 1: Avgrensning glemmes under gjennomføring.", "Nivå 2: Avgrensning omtales, men ikke operasjonalisert.", "Nivå 3: Avgrensning håndteres for større endringer.", "Nivå 4: System for å håndtere avgrensning under gjennomføring.", "Nivå 5: Dynamisk avgrensningshåndtering integrert i beslutningsprosesser."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan justeres nullpunkter og estimater under gjennomføring basert på nye data og erfaringer?", "scale": ["Nivå 1: Nullpunkter og estimater justeres ikke under gjennomføring.", "Nivå 2: Justering skjer ad hoc uten struktur.", "Nivå 3: Systematisk justering for store avvik.", "Nivå 4: Regelmessig revisjon og justering av nullpunkter og estimater.", "Nivå 5: Kontinuerlig justering basert på realtidsdata og læring."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Hvordan testes hypoteser og datagrunnlag under gjennomføring for å validere tilnærmingen?", "scale": ["Nivå 1: Hypoteser testes ikke under gjennomføring.", "Nivå 2: Noen uformelle tester gjennomføres.", "Nivå 3: Formell testing for kritiske hypoteser.", "Nivå 4: Systematisk testing og validering under gjennomføring.", "Nivå 5: Kontinuerlig hypotesetesting integrert i læringsprosesser."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement under gjennomføring?", "scale": ["Nivå 1: Interessentengasjement avtar under gjennomføring.", "Nivå 2: Begrenset engasjement for viktige beslutninger.", "Nivå 3: Regelmessig engasjement for større endringer.", "Nivå 4: Systematisk interessentoppfølging under gjennomføring.", "Nivå 5: Kontinuerlig dialog og samskaping med interessenter."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvåkes og håndteres gevinstforutsetninger under gjennomføring?", "scale": ["Nivå 1: Forutsetninger overvåkes ikke under gjennomføring.", "Nivå 2: Noen forutsetninger overvåkes uformelt.", "Nivå 3: Systematisk overvåkning av kritiske forutsetninger.", "Nivå 4: Aktiv håndtering av endrede forutsetninger.", "Nivå 5: Forutsetningsstyring integrert i risikostyring og beslutninger."]},
        {"id": 10, "title": "Prinsipielle og vilkårsmessige kriterier", "question": "Hvordan håndteres endringer i prinsipielle og vilkårsmessige kriterier under gjennomføring?", "scale": ["Nivå 1: Endringer i kriterier håndteres ikke.", "Nivå 2: Store endringer håndteres reaktivt.", "Nivå 3: System for å håndtere endringer i kriterier.", "Nivå 4: Proaktiv håndtering av endrede kriterier.", "Nivå 5: Dynamisk tilpasning til endrede kriterier i sanntid."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under gjennomføring?", "scale": ["Nivå 1: Enighet testes ikke under gjennomføring.", "Nivå 2: Enighet bekreftes ved store endringer.", "Nivå 3: Regelmessig bekreftelse av enighet.", "Nivå 4: Systematisk arbeid for å opprettholde enighet.", "Nivå 5: Kontinuerlig dialog og justering for å opprettholde enighet."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan håndteres disponering av besparelser under gjennomføring?", "scale": ["Nivå 1: Disponering håndteres ikke under gjennomføring.", "Nivå 2: Disponering justeres for store avvik.", "Nivå 3: Systematisk revisjon av disponeringsplaner.", "Nivå 4: Dynamisk tilpasning av disponering basert på resultater.", "Nivå 5: Optimal disponering integrert i beslutningsstøtte."]},
        {"id": 13, "title": "Måling av effektivitet og produktivitet", "question": "Hvordan måles og følges opp effektivitet og produktivitet under gjennomføring?", "scale": ["Nivå 1: Effektivitet og produktivitet måles ikke underveis.", "Nivå 2: Noen målinger registreres, men ikke analysert.", "Nivå 3: Systematisk måling med begrenset analyse.", "Nivå 4: Regelmessig analyse og justering basert på målinger.", "Nivå 5: Realtids overvåkning og proaktiv justering."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Hvordan identifiseres og håndteres nye operasjonelle risikoer og ulemper under gjennomføring?", "scale": ["Nivå 1: Nye risikoer identifiseres ikke underveis.", "Nivå 2: Store risikoer håndteres reaktivt.", "Nivå 3: Systematisk identifisering av nye risikoer.", "Nivå 4: Proaktiv håndtering av nye risikoer.", "Nivå 5: Risikostyring integrert i daglig drift."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan vurderes balansen mellom gevinster og ulemper under gjennomføring?", "scale": ["Nivå 1: Balansen vurderes ikke under gjennomføring.", "Nivå 2: Balansen vurderes ved store endringer.", "Nivå 3: Regelmessig vurdering av balansen.", "Nivå 4: Systematisk overvåkning av balansen.", "Nivå 5: Balansevurdering integrert i beslutningsprosesser."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Hvordan oppdateres og brukes gevinstrealiseringsplanen under gjennomføring?", "scale": ["Nivå 1: Gevinstrealiseringsplanen oppdateres ikke.", "Nivå 2: Planen oppdateres ved store endringer.", "Nivå 3: Regelmessig oppdatering av planen.", "Nivå 4: Planen brukes aktivt i styring og beslutninger.", "Nivå 5: Dynamisk oppdatering og bruk av planen i sanntid."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under gjennomføring?", "scale": ["Nivå 1: Planen brukes ikke som operativ handlingsplan.", "Nivå 2: Planen brukes til visse operasjoner.", "Nivå 3: Planen er integrert i deler av den operative styringen.", "Nivå 4: Planen er aktivt operativt styringsverktøy.", "Nivå 5: Planen er fullt integrert i alle operative beslutninger."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hvordan utvikles endringsberedskap og operativ mottaksevne under gjennomføring?", "scale": ["Nivå 1: Endringsberedskap utvikles ikke underveis.", "Nivå 2: Begrenset fokus på endringsberedskap.", "Nivå 3: Systematisk arbeid med endringsberedskap.", "Nivå 4: Målrettet utvikling av mottaksevne.", "Nivå 5: Kontinuerlig tilpasning og læring i endringsprosessen."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Hvordan opprettholdes kommunikasjon og forankring under gjennomføring?", "scale": ["Nivå 1: Kommunikasjon avtar under gjennomføring.", "Nivå 2: Begrenset kommunikasjon om viktige endringer.", "Nivå 3: Regelmessig kommunikasjon om fremdrift.", "Nivå 4: Systematisk kommunikasjonsplan under gjennomføring.", "Nivå 5: Kontinuerlig dialog og tilbakemelding integrert i prosessen."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Hvordan utøves eierskap og ansvar under gjennomføring?", "scale": ["Nivå 1: Eierskap og ansvar svekkes under gjennomføring.", "Nivå 2: Begrenset eierskap i kritiske faser.", "Nivå 3: Tydelig eierskap for sentrale ansvarsområder.", "Nivå 4: Aktivt utøvd eierskap gjennom hele prosessen.", "Nivå 5: Sterk eierskapskultur som driver gjennomføring."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Hvordan justeres periodisering og forankring under gjennomføring?", "scale": ["Nivå 1: Periodisering justeres ikke under gjennomføring.", "Nivå 2: Store justeringer i periodisering.", "Nivå 3: Regelmessig revisjon av periodisering.", "Nivå 4: Dynamisk tilpasning av periodisering.", "Nivå 5: Fleksibel periodisering integrert i styringssystemet."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Hvordan opprettholdes realisme og engasjement under gjennomføring?", "scale": ["Nivå 1: Realisme og engasjement avtar.", "Nivå 2: Begrenset fokus på å opprettholde engasjement.", "Nivå 3: Arbeid med å opprettholde realisme og engasjement.", "Nivå 4: Systematisk arbeid for å styrke troverdighet.", "Nivå 5: Høy troverdighet og engasjement gjennom hele prosessen."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan bygges momentum gjennom tidlig gevinstuttak under gjennomføringsfasen?", "scale": ["Nivå 1: Ingen fokus på momentum eller tidlig gevinstuttak.", "Nivå 2: Noen tidlige gevinster realiseres, men uten strategi.", "Nivå 3: Planlagt for tidlig gevinstuttak, men begrenset gjennomføring.", "Nivå 4: Systematisk arbeid med tidlig gevinstuttak for å bygge momentum.", "Nivå 5: Kontinuerlig fokus på momentum gjennom suksessiv gevinstrealisering."]}
    ],
    "Realisering": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan anvendes læring fra tidligere prosjekter og gevinstarbeid for å optimalisere gevinstuttak under realiseringen?", "scale": ["Nivå 1: Ingen læring anvendt i realiseringsfasen.", "Nivå 2: Enkelte erfaringer tas i betraktning.", "Nivå 3: Systematisk bruk av læring for å optimalisere uttak.", "Nivå 4: Læring integrert i realiseringsprosessen.", "Nivå 5: Kontinuerlig læring og optimalisering under realisering."]},
        {"id": 2, "title": "Strategisk retning og gevinstforståelse", "question": "Hvordan sikres strategisk retning og gevinstforståelse under realiseringen?", "scale": ["Nivå 1: Strategisk retning glemmes under realisering.", "Nivå 2: Strategi refereres til, men ikke operasjonalisert.", "Nivå 3: Tydelig strategisk retning i realiseringsarbeid.", "Nivå 4: Strategi dynamisk tilpasses under realisering.", "Nivå 5: Strategi og realisering fullt integrert og sammenvevd."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Hvordan brukes gevinstkartet for å styre realiseringsarbeidet?", "scale": ["Nivå 1: Gevinstkartet brukes ikke under realisering.", "Nivå 2: Gevinstkartet vises, men ikke aktivt brukt.", "Nivå 3: Gevinstkartet brukes til å prioritere realisering.", "Nivå 4: Gevinstkartet er aktivt styringsverktøy.", "Nivå 5: Gevinstkartet dynamisk oppdateres basert på realisering."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Hvordan følges opp strategisk kobling og KPI-er under realiseringen?", "scale": ["Nivå 1: Ingen oppfølging av strategisk kobling.", "Nivå 2: KPI-er måles, men kobling til strategi svak.", "Nivå 3: Systematisk oppfølging av strategisk kobling.", "Nivå 4: Dynamisk justering basert på KPI-utvikling.", "Nivå 5: Full integrasjon mellom strategi, KPI-er og realisering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Hvordan håndteres avgrensning av programgevinster under realiseringen?", "scale": ["Nivå 1: Avgrensning håndteres ikke under realisering.", "Nivå 2: Store avgrensningsutfordringer håndteres.", "Nivå 3: System for å håndtere avgrensning.", "Nivå 4: Proaktiv håndtering av avgrensning.", "Nivå 5: Avgrensning integrert i realiseringsprosessen."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan valideres og justeres nullpunkter og estimater under realiseringen?", "scale": ["Nivå 1: Nullpunkter og estimater valideres ikke.", "Nivå 2: Store avvik håndteres reaktivt.", "Nivå 3: Systematisk validering under realisering.", "Nivå 4: Kontinuerlig justering basert på realisering.", "Nivå 5: Dynamisk oppdatering av nullpunkter og estimater."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Hvordan valideres hypoteser og datagrunnlag under realiseringen?", "scale": ["Nivå 1: Hypoteser valideres ikke under realisering.", "Nivå 2: Noen hypoteser testes uformelt.", "Nivå 3: Systematisk testing av kritiske hypoteser.", "Nivå 4: Omfattende validering under realisering.", "Nivå 5: Kontinuerlig hypotesetesting og læring."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement under realiseringen?", "scale": ["Nivå 1: Interessentengasjement avtar under realisering.", "Nivå 2: Begrenset engasjement for viktige beslutninger.", "Nivå 3: Regelmessig dialog med interessenter.", "Nivå 4: Aktivt interessentengasjement gjennom realisering.", "Nivå 5: Interessenter er drivkrefter i realiseringsarbeidet."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvåkes og realiseres gevinstforutsetninger under realiseringen?", "scale": ["Nivå 1: Forutsetninger overvåkes ikke under realisering.", "Nivå 2: Noen forutsetninger følges opp.", "Nivå 3: Systematisk overvåkning av forutsetninger.", "Nivå 4: Aktiv realisering av forutsetninger.", "Nivå 5: Forutsetningsrealisering integrert i gevinstuttak."]},
        {"id": 10, "title": "Prinsipielle og vilkårsmessige kriterier", "question": "Hvordan håndteres prinsipielle og vilkårsmessige kriterier under realiseringen?", "scale": ["Nivå 1: Kriterier håndteres ikke under realisering.", "Nivå 2: Store avvik fra kriterier håndteres.", "Nivå 3: Systematisk håndtering av kriterier.", "Nivå 4: Proaktiv tilpasning til kriterier.", "Nivå 5: Kriterier integrert i realiseringsbeslutninger."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Hvordan opprettholdes enighet om nullpunkter og estimater under realiseringen?", "scale": ["Nivå 1: Enighet testes ikke under realisering.", "Nivå 2: Enighet bekreftes ved store endringer.", "Nivå 3: Regelmessig bekreftelse av enighet.", "Nivå 4: Kontinuerlig arbeid for å opprettholde enighet.", "Nivå 5: Full enighet gjennom hele realiseringsfasen."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan håndteres disponering av besparelser under realiseringen?", "scale": ["Nivå 1: Disponering håndteres ikke under realisering.", "Nivå 2: Store endringer i disponering håndteres.", "Nivå 3: Systematisk revisjon av disponering.", "Nivå 4: Dynamisk tilpasning av disponering.", "Nivå 5: Optimal disponering under realisering."]},
        {"id": 13, "title": "Måling av effektivitet og produktivitet", "question": "Hvordan måles og forbedres effektivitet og produktivitet under realiseringen?", "scale": ["Nivå 1: Effektivitet og produktivitet måles ikke.", "Nivå 2: Noen målinger registreres.", "Nivå 3: Systematisk måling og rapportering.", "Nivå 4: Målinger brukes til forbedring.", "Nivå 5: Kontinuerlig forbedring basert på målinger."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Hvordan håndteres operasjonelle risikoer og ulemper under realiseringen?", "scale": ["Nivå 1: Risikoer og ulemper håndteres ikke.", "Nivå 2: Store risikoer håndteres reaktivt.", "Nivå 3: Systematisk identifisering og håndtering.", "Nivå 4: Proaktiv risikohåndtering.", "Nivå 5: Risikostyring integrert i realiseringsarbeid."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan vurderes balansen mellom gevinster og ulemper under realiseringen?", "scale": ["Nivå 1: Balansen vurderes ikke under realisering.", "Nivå 2: Balansen vurderes ved store endringer.", "Nivå 3: Regelmessig vurdering av balansen.", "Nivå 4: Systematisk overvåkning av balansen.", "Nivå 5: Balansevurdering integrert i beslutninger."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Hvordan brukes gevinstrealiseringsplanen under realiseringen?", "scale": ["Nivå 1: Gevinstrealiseringsplanen brukes ikke.", "Nivå 2: Planen refereres til ved behov.", "Nivå 3: Planen brukes aktivt i realisering.", "Nivå 4: Planen oppdateres og brukes kontinuerlig.", "Nivå 5: Planen er sentralt styringsverktøy."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan fungerer gevinstrealiseringsplanen som operativ handlingsplan under realiseringen?", "scale": ["Nivå 1: Planen brukes ikke som operativ handlingsplan.", "Nivå 2: Planen brukes til enkelte operasjoner.", "Nivå 3: Planen er integrert i operativ styring.", "Nivå 4: Planen er aktivt operativt verktøy.", "Nivå 5: Planen driver operativ virksomhet."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hvordan utvikles endringsberedskap og mottaksevne under realiseringen?", "scale": ["Nivå 1: Endringsberedskap utvikles ikke.", "Nivå 2: Begrenset fokus på endringsberedskap.", "Nivå 3: Systematisk arbeid med endringsberedskap.", "Nivå 4: Målrettet utvikling av mottaksevne.", "Nivå 5: Høy mottaksevne og endringsberedskap."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Hvordan opprettholdes kommunikasjon og forankring under realiseringen?", "scale": ["Nivå 1: Kommunikasjon avtar under realisering.", "Nivå 2: Begrenset kommunikasjon om realisering.", "Nivå 3: Regelmessig kommunikasjon om fremdrift.", "Nivå 4: Systematisk kommunikasjon om realisering.", "Nivå 5: Kontinuerlig dialog om realiseringsarbeid."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Hvordan utøves eierskap og ansvar under realiseringen?", "scale": ["Nivå 1: Eierskap og ansvar svekkes.", "Nivå 2: Begrenset eierskap i realiseringsfasen.", "Nivå 3: Tydelig eierskap for realisering.", "Nivå 4: Aktivt utøvd eierskap.", "Nivå 5: Sterk eierskapskultur i realisering."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Hvordan justeres periodisering og forankring under realiseringen?", "scale": ["Nivå 1: Periodisering justeres ikke.", "Nivå 2: Store justeringer i periodisering.", "Nivå 3: Regelmessig revisjon av periodisering.", "Nivå 4: Dynamisk tilpasning av periodisering.", "Nivå 5: Fleksibel periodisering under realisering."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Hvordan opprettholdes realisme og engasjement under realiseringen?", "scale": ["Nivå 1: Realisme og engasjement avtar.", "Nivå 2: Begrenset fokus på å opprettholde engasjement.", "Nivå 3: Arbeid med å opprettholde realisme og engasjement.", "Nivå 4: Systematisk arbeid for å styrke troverdighet.", "Nivå 5: Høy troverdighet og engasjement."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan brukes tidlig gevinstuttak for å bygge momentum i realiseringsfasen?", "scale": ["Nivå 1: Ingen systematisk bruk av tidlig gevinstuttak.", "Nivå 2: Enkelte suksesser brukes til å motivere.", "Nivå 3: Bevissthet på viktigheten av momentum.", "Nivå 4: Strategisk bruk av tidlige gevinster.", "Nivå 5: Momentum systematisk bygget og vedlikeholdt."]}
    ],
    "Realisert": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan dokumenteres og deles læring fra gevinstrealiseringen for fremtidig bruk?", "scale": ["Nivå 1: Ingen dokumentasjon eller deling av læring.", "Nivå 2: Enkelte erfaringer deles uformelt.", "Nivå 3: Systematisk dokumentasjon av læring.", "Nivå 4: Læring deles og diskuteres i organisasjonen.", "Nivå 5: Læring integrert i organisasjonens kunnskapsbase."]},
        {"id": 2, "title": "Strategisk retning og gevinstforståelse", "question": "Hvordan bidro den strategiske retningen til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Strategisk retning bidro lite til suksess.", "Nivå 2: Strategi var viktig for enkelte gevinster.", "Nivå 3: Strategi bidro til flere gevinster.", "Nivå 4: Strategi var avgjørende for gevinstrealisering.", "Nivå 5: Strategi og gevinstrealisering fullt integrert."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Hvordan bidro gevinstkartet til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Gevinstkartet bidro lite til suksess.", "Nivå 2: Kartet var nyttig for enkelte gevinster.", "Nivå 3: Kartet bidro til flere gevinster.", "Nivå 4: Kartet var viktig for gevinstrealisering.", "Nivå 5: Kartet var avgjørende for suksess."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Hvordan bidro den strategiske koblingen og KPI-ene til gevinstrealisering?", "scale": ["Nivå 1: Strategisk kobling bidro lite.", "Nivå 2: Kobling var viktig for enkelte gevinster.", "Nivå 3: Kobling bidro til flere gevinster.", "Nivå 4: Kobling var avgjørende for realisering.", "Nivå 5: Full integrasjon mellom strategi og realisering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Hvordan bidro avgrensningsarbeidet til gevinstrealiseringens troverdighet?", "scale": ["Nivå 1: Avgrensning bidro lite til troverdighet.", "Nivå 2: Avgrensning viktig for enkelte gevinster.", "Nivå 3: Avgrensning bidro til troverdighet for flere gevinster.", "Nivå 4: Avgrensning var avgjørende for troverdighet.", "Nivå 5: Avgrensning styrket troverdighet betydelig."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan bidro nullpunkter og estimater til gevinstrealiseringens nøyaktighet?", "scale": ["Nivå 1: Nullpunkter og estimater bidro lite.", "Nivå 2: Estimater var nøyaktige for enkelte gevinster.", "Nivå 3: Estimater var nøyaktige for flere gevinster.", "Nivå 4: Høy nøyaktighet i estimater.", "Nivå 5: Estimater var svært nøyaktige."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Hvordan bidro hypotesetesting og datagrunnlag til gevinstrealiseringens kvalitet?", "scale": ["Nivå 1: Testing og datagrunnlag bidro lite.", "Nivå 2: Testing viktig for enkelte gevinster.", "Nivå 3: Testing bidro til kvalitet for flere gevinster.", "Nivå 4: Testing var avgjørende for kvalitet.", "Nivå 5: Testing og datagrunnlag styrket kvalitet betydelig."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan bidro interessentengasjement til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Interessentengasjement bidro lite.", "Nivå 2: Engasjement viktig for enkelte gevinster.", "Nivå 3: Engasjement bidro til flere gevinster.", "Nivå 4: Engasjement var avgjørende for suksess.", "Nivå 5: Interessenter var drivkrefter for suksess."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan bidro håndtering av gevinstforutsetninger til realiseringens suksess?", "scale": ["Nivå 1: Forutsetningshåndtering bidro lite.", "Nivå 2: Håndtering viktig for enkelte gevinster.", "Nivå 3: Håndtering bidro til flere gevinster.", "Nivå 4: Håndtering var avgjørende for suksess.", "Nivå 5: Forutsetningshåndtering var suksessfaktor."]},
        {"id": 10, "title": "Prinsipielle og vilkårsmessige kriterier", "question": "Hvordan bidro håndtering av kriterier til gevinstrealisering?", "scale": ["Nivå 1: Kriteriehåndtering bidro lite.", "Nivå 2: Håndtering viktig for enkelte gevinster.", "Nivå 3: Håndtering bidro til flere gevinster.", "Nivå 4: Håndtering var avgjørende for realisering.", "Nivå 5: Kriteriehåndtering styrket realisering."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Hvordan bidro enighet om nullpunkter og estimater til realiseringens suksess?", "scale": ["Nivå 1: Enighet bidro lite til suksess.", "Nivå 2: Enighet viktig for enkelte gevinster.", "Nivå 3: Enighet bidro til flere gevinster.", "Nivå 4: Enighet var avgjørende for suksess.", "Nivå 5: Full enighet styrket suksess betydelig."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan bidro disponering av besparelser til gevinstrealiseringens verdiskapning?", "scale": ["Nivå 1: Disponering bidro lite til verdiskapning.", "Nivå 2: Disponering viktig for enkelte gevinster.", "Nivå 3: Disponering bidro til verdi for flere gevinster.", "Nivå 4: Disponering var avgjørende for verdiskapning.", "Nivå 5: Optimal disponering maksimerte verdi."]},
        {"id": 13, "title": "Måling av effektivitet og produktivitet", "question": "Hvordan bidro måling av effektivitet og produktivitet til gevinstrealisering?", "scale": ["Nivå 1: Måling bidro lite til realisering.", "Nivå 2: Måling viktig for enkelte gevinster.", "Nivå 3: Måling bidro til flere gevinster.", "Nivå 4: Måling var avgjørende for realisering.", "Nivå 5: Måling drevet gevinstrealisering."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Hvordan bidro håndtering av risiko og ulemper til gevinstrealiseringens robusthet?", "scale": ["Nivå 1: Risikohåndtering bidro lite.", "Nivå 2: Håndtering viktig for enkelte gevinster.", "Nivå 3: Håndtering bidro til robusthet for flere gevinster.", "Nivå 4: Håndtering var avgjørende for robusthet.", "Nivå 5: Risikohåndtering styrket robusthet betydelig."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan bidro balansevurdering til gevinstrealiseringens bærekraft?", "scale": ["Nivå 1: Balansevurdering bidro lite.", "Nivå 2: Vurdering viktig for enkelte gevinster.", "Nivå 3: Vurdering bidro til bærekraft for flere gevinster.", "Nivå 4: Vurdering var avgjørende for bærekraft.", "Nivå 5: Balansevurdering styrket bærekraft betydelig."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Hvordan bidro gevinstrealiseringsplanen til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Planen bidro lite til suksess.", "Nivå 2: Planen viktig for enkelte gevinster.", "Nivå 3: Planen bidro til flere gevinster.", "Nivå 4: Planen var avgjørende for suksess.", "Nivå 5: Planen var suksessfaktor for realisering."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan bidro gevinstrealiseringsplanen som operativ handlingsplan til suksess?", "scale": ["Nivå 1: Planen som handlingsplan bidro lite.", "Nivå 2: Planen viktig for enkelte operasjoner.", "Nivå 3: Planen bidro til flere operasjoner.", "Nivå 4: Planen var avgjørende for operativ suksess.", "Nivå 5: Planen drevet operativ gevinstrealisering."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Hvordan bidro endringsberedskap og mottaksevne til gevinstrealisering?", "scale": ["Nivå 1: Beredskap og mottaksevne bidro lite.", "Nivå 2: Beredskap viktig for enkelte gevinster.", "Nivå 3: Beredskap bidro til flere gevinster.", "Nivå 4: Beredskap var avgjørende for realisering.", "Nivå 5: Høy mottaksevne drevet realisering."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Hvordan bidro kommunikasjon og forankring til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Kommunikasjon bidro lite til suksess.", "Nivå 2: Kommunikasjon viktig for enkelte gevinster.", "Nivå 3: Kommunikasjon bidro til flere gevinster.", "Nivå 4: Kommunikasjon var avgjørende for suksess.", "Nivå 5: God kommunikasjon styrket suksess betydelig."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Hvordan bidro eierskap og ansvar til gevinstrealiseringens suksess?", "scale": ["Nivå 1: Eierskap og ansvar bidro lite.", "Nivå 2: Eierskap viktig for enkelte gevinster.", "Nivå 3: Eierskap bidro til flere gevinster.", "Nivå 4: Eierskap var avgjørende for suksess.", "Nivå 5: Sterkt eierskap drevet suksess."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Hvordan bidro periodisering og forankring til gevinstrealiseringens effektivitet?", "scale": ["Nivå 1: Periodisering bidro lite til effektivitet.", "Nivå 2: Periodisering viktig for enkelte gevinster.", "Nivå 3: Periodisering bidro til effektivitet for flere gevinster.", "Nivå 4: Periodisering var avgjørende for effektivitet.", "Nivå 5: God periodisering maksimerte effektivitet."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Hvordan bidro realisme og engasjement til gevinstrealiseringens troverdighet?", "scale": ["Nivå 1: Realisme og engasjement bidro lite.", "Nivå 2: Realisme viktig for enkelte gevinster.", "Nivå 3: Realisme bidro til troverdighet for flere gevinster.", "Nivå 4: Realisme var avgjørende for troverdighet.", "Nivå 5: Høy troverdighet styrket realisering."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan bidro arbeid med momentum og tidlig gevinstuttak til langsiktig suksess?", "scale": ["Nivå 1: Momentum og tidlig uttak bidro lite.", "Nivå 2: Tidlig uttak viktig for enkelte gevinster.", "Nivå 3: Tidlig uttak bidro til momentum for flere gevinster.", "Nivå 4: Momentum var avgjørende for suksess.", "Nivå 5: Momentum og tidlig uttak drevet langsiktig suksess."]}
    ]
}

# ============================================================================
# DATALAGRING
# ============================================================================
def load_data():
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
    data_file = get_data_file()
    with open(data_file, 'wb') as f:
        pickle.dump(data, f)

def get_data():
    if 'app_data' not in st.session_state:
        st.session_state.app_data = load_data()
    if 'initiatives' not in st.session_state.app_data:
        st.session_state.app_data['initiatives'] = {}
    return st.session_state.app_data

def persist_data():
    save_data(st.session_state.app_data)

# ============================================================================
# STYLING
# ============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Source Sans Pro', sans-serif; }}
.main-header {{ font-size: 2rem; color: {COLORS['primary_dark']}; text-align: center; margin-bottom: 0.3rem; font-weight: 700; }}
.sub-header {{ font-size: 0.95rem; color: {COLORS['primary']}; text-align: center; margin-bottom: 1.5rem; }}
.metric-card {{ background: {COLORS['gray_light']}; padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['primary']}; text-align: center; margin: 0.3rem 0; }}
.metric-value {{ font-size: 1.6rem; font-weight: 700; color: {COLORS['primary_dark']}; }}
.metric-label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; }}
.strength-card {{ background: linear-gradient(135deg, #DDFAE2 0%, {COLORS['gray_light']} 100%); padding: 0.8rem; border-radius: 8px; border-left: 4px solid {COLORS['success']}; margin: 0.4rem 0; }}
.improvement-card {{ background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, {COLORS['gray_light']} 100%); padding: 0.8rem; border-radius: 8px; border-left: 4px solid {COLORS['danger']}; margin: 0.4rem 0; }}
.stButton > button {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%); color: white; border: none; border-radius: 6px; padding: 0.5rem 1rem; font-weight: 600; }}
.stProgress > div > div > div > div {{ background: linear-gradient(90deg, {COLORS['primary_light']} 0%, {COLORS['success']} 100%); }}
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
    if score >= 4.5: return "Høy modenhet"
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
    if len(categories) < 3:
        fig = go.Figure(data=[go.Bar(x=categories, y=values, marker_color=COLORS['primary'])])
        fig.update_layout(yaxis=dict(range=[0, 5], title="Score"), height=350, margin=dict(l=40, r=40, t=40, b=40))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(0, 83, 166, 0.3)', line=dict(color=COLORS['primary'], width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5])), showlegend=False, height=350, margin=dict(l=80, r=80, t=40, b=40))
    return fig

def create_parameter_radar(param_data):
    if not param_data:
        return None
    categories = list(param_data.keys())
    values = [param_data[c]['avg'] for c in categories]
    if len(categories) < 3:
        fig = go.Figure(data=[go.Bar(x=categories, y=values, marker_color=COLORS['primary_light'])])
        fig.update_layout(yaxis=dict(range=[0, 5], title="Score"), height=350, margin=dict(l=40, r=40, t=40, b=40))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(100, 200, 250, 0.3)', line=dict(color=COLORS['primary_light'], width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, height=400, margin=dict(l=100, r=100, t=40, b=40))
    return fig

def create_strength_radar(items, max_items=8):
    """Radar chart for strength areas"""
    if not items or len(items) < 3:
        return None
    items = items[:max_items]
    categories = [f"{item['title'][:20]}..." if len(item['title']) > 20 else item['title'] for item in items]
    values = [item['score'] for item in items]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], 
        theta=categories + [categories[0]], 
        fill='toself', 
        fillcolor='rgba(53, 222, 109, 0.3)',
        line=dict(color=COLORS['success'], width=3),
        name='Styrker'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5])), 
        showlegend=False, 
        height=400, 
        margin=dict(l=80, r=80, t=40, b=40)
    )
    return fig

def create_improvement_radar(items, max_items=8):
    """Radar chart for improvement areas"""
    if not items or len(items) < 3:
        return None
    items = items[:max_items]
    categories = [f"{item['title'][:20]}..." if len(item['title']) > 20 else item['title'] for item in items]
    values = [item['score'] for item in items]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], 
        theta=categories + [categories[0]], 
        fill='toself', 
        fillcolor='rgba(255, 107, 107, 0.3)',
        line=dict(color=COLORS['danger'], width=3),
        name='Forbedring'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5])), 
        showlegend=False, 
        height=400, 
        margin=dict(l=80, r=80, t=40, b=40)
    )
    return fig

def create_strength_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:25]}..." if len(item['title']) > 25 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['success'], text=[f"{s:.1f}" for s in scores], textposition='outside')])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score"), yaxis=dict(autorange="reversed"), height=max(250, len(items) * 35), margin=dict(l=200, r=50, t=20, b=40))
    return fig

def create_improvement_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:25]}..." if len(item['title']) > 25 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['danger'], text=[f"{s:.1f}" for s in scores], textposition='outside')])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score"), yaxis=dict(autorange="reversed"), height=max(250, len(items) * 35), margin=dict(l=200, r=50, t=20, b=40))
    return fig

# ============================================================================
# RAPPORT-GENERERING - HTML
# ============================================================================
# Liste med hyggelige anonyme navn
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
    """Genererer HTML-rapport med embedded radar-diagrammer og per-gevinst resultater"""
    
    # Hjelpefunksjon for å lage SVG radar chart
    def create_svg_radar(categories, values, color, title="", width=400, height=350):
        if len(categories) < 3:
            return ""
        
        import math
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 2 - 60
        n = len(categories)
        
        # Start SVG
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        
        # Bakgrunnsirkler
        for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
            svg += f'<circle cx="{cx}" cy="{cy}" r="{radius * r}" fill="none" stroke="#E8E8E8" stroke-width="1"/>'
        
        # Linjer fra sentrum
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            svg += f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#E8E8E8" stroke-width="1"/>'
        
        # Data polygon
        points = []
        for i, val in enumerate(values):
            angle = (2 * math.pi * i / n) - math.pi / 2
            r = (val / 5) * radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x},{y}")
        
        svg += f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="0.3" stroke="{color}" stroke-width="2"/>'
        
        # Labels
        for i, cat in enumerate(categories):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + (radius + 35) * math.cos(angle)
            y = cy + (radius + 35) * math.sin(angle)
            # Forkorte lange labels
            label = cat[:18] + "..." if len(cat) > 18 else cat
            anchor = "middle"
            if angle > math.pi / 4 and angle < 3 * math.pi / 4:
                anchor = "start"
            elif angle > -3 * math.pi / 4 and angle < -math.pi / 4:
                anchor = "start"
            svg += f'<text x="{x}" y="{y}" text-anchor="middle" font-size="10" fill="#172141">{label}</text>'
        
        # Tittel
        if title:
            svg += f'<text x="{cx}" y="20" text-anchor="middle" font-size="14" font-weight="bold" fill="#172141">{title}</text>'
        
        svg += '</svg>'
        return svg
    
    # Hjelpefunksjon for å lage bar chart SVG
    def create_svg_bar(items, color, title="", width=450, max_items=8):
        if not items:
            return ""
        items = items[:max_items]
        bar_height = 28
        height = len(items) * (bar_height + 8) + 60
        
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        
        if title:
            svg += f'<text x="10" y="20" font-size="14" font-weight="bold" fill="#172141">{title}</text>'
        
        y_offset = 40
        for i, item in enumerate(items):
            y = y_offset + i * (bar_height + 8)
            bar_width = (item['score'] / 5) * (width - 180)
            label = item['title'][:25] + "..." if len(item['title']) > 25 else item['title']
            
            svg += f'<text x="10" y="{y + 18}" font-size="11" fill="#172141">{label}</text>'
            svg += f'<rect x="170" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4"/>'
            svg += f'<text x="{175 + bar_width}" y="{y + 18}" font-size="11" fill="#172141">{item["score"]:.1f}</text>'
        
        svg += '</svg>'
        return svg

    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Modenhetsvurdering - {initiative['name']}</title>
    <style>
        body {{ font-family: 'Source Sans Pro', Arial, sans-serif; padding: 40px; max-width: 1200px; margin: 0 auto; color: #172141; line-height: 1.6; }}
        h1 {{ color: #172141; text-align: center; margin-bottom: 5px; }}
        h2 {{ color: #0053A6; border-bottom: 2px solid #64C8FA; padding-bottom: 8px; margin-top: 40px; }}
        h3 {{ color: #0053A6; margin-top: 25px; }}
        h4 {{ color: #172141; margin-top: 20px; }}
        .subtitle {{ text-align: center; color: #0053A6; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #0053A6; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #E8E8E8; }}
        tr:nth-child(even) {{ background: #F2FAFD; }}
        .metric-row {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .metric-card {{ flex: 1; min-width: 150px; background: #F2FAFD; padding: 15px; border-radius: 8px; border-left: 4px solid #0053A6; text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: 700; color: #0053A6; }}
        .metric-label {{ font-size: 0.85rem; color: #666; text-transform: uppercase; }}
        .charts-row {{ display: flex; gap: 30px; margin: 20px 0; flex-wrap: wrap; justify-content: center; }}
        .chart-container {{ flex: 1; min-width: 350px; max-width: 500px; text-align: center; }}
        .item {{ padding: 8px 12px; margin: 5px 0; border-radius: 6px; }}
        .item-strength {{ background: #DDFAE2; border-left: 4px solid #35DE6D; }}
        .item-improvement {{ background: rgba(255, 107, 107, 0.15); border-left: 4px solid #FF6B6B; }}
        .benefit-section {{ background: #F8F9FA; padding: 25px; margin: 30px 0; border-radius: 10px; border: 1px solid #E8E8E8; }}
        .benefit-header {{ background: #0053A6; color: white; padding: 15px 20px; margin: -25px -25px 20px -25px; border-radius: 10px 10px 0 0; }}
        .comment-phase {{ background: #64C8FA; color: white; padding: 10px 15px; margin-top: 20px; border-radius: 6px 6px 0 0; }}
        .comment-question {{ background: #F2FAFD; padding: 10px 15px; border-left: 3px solid #0053A6; margin: 10px 0; }}
        .comment-question h4 {{ margin: 0 0 10px 0; color: #172141; font-size: 0.95rem; }}
        .comment-item {{ background: white; padding: 10px 15px; margin: 8px 0; border-radius: 4px; border: 1px solid #E8E8E8; }}
        .comment-meta {{ font-size: 0.85em; color: #666; margin-bottom: 5px; }}
        .comment-text {{ color: #172141; font-size: 0.95rem; }}
        .score-badge {{ display: inline-block; background: #64C8FA; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 8px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E8E8E8; color: #666; }}
        .page-break {{ page-break-before: always; }}
        @media print {{
            .page-break {{ page-break-before: always; }}
            body {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <h1>Modenhetsvurdering - Gevinstrealisering</h1>
    <p class="subtitle">Gjennomfores i samarbeid med konsern okonomi og digital transformasjon</p>
    
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
            <div class="metric-label">Styrkeomrader</div>
        </div>
        <div class="metric-card" style="border-left-color: #FF6B6B;">
            <div class="metric-value" style="color: #FF6B6B;">{len(stats['low_maturity'])}</div>
            <div class="metric-label">Forbedringsomrader</div>
        </div>
    </div>
"""
    
    # Fase og parameter diagrammer
    if stats['phases']:
        html += "<h3>1.2 Modenhet per fase</h3>"
        html += "<table><tr><th>Fase</th><th>Gjennomsnitt</th><th>Min</th><th>Maks</th></tr>"
        for phase, data in stats['phases'].items():
            html += f"<tr><td>{phase}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['min']:.2f}</td><td>{data['max']:.2f}</td></tr>"
        html += "</table>"
        
        # Fase radar
        if len(stats['phases']) >= 3:
            phase_cats = list(stats['phases'].keys())
            phase_vals = [stats['phases'][p]['avg'] for p in phase_cats]
            html += '<div class="charts-row">'
            html += '<div class="chart-container">'
            html += create_svg_radar(phase_cats, phase_vals, '#0053A6', 'Modenhet per fase')
            html += '</div>'
            
            # Parameter radar
            if stats['parameters'] and len(stats['parameters']) >= 3:
                param_cats = list(stats['parameters'].keys())
                param_vals = [stats['parameters'][p]['avg'] for p in param_cats]
                html += '<div class="chart-container">'
                html += create_svg_radar(param_cats, param_vals, '#64C8FA', 'Modenhet per parameter')
                html += '</div>'
            html += '</div>'
    
    # Styrker og forbedringer med diagrammer
    html += "<h3>1.3 Styrkeomrader og forbedringsomrader</h3>"
    html += '<div class="charts-row">'
    
    if stats['high_maturity']:
        html += '<div class="chart-container">'
        if len(stats['high_maturity']) >= 3:
            strength_cats = [item['title'][:20] for item in stats['high_maturity'][:8]]
            strength_vals = [item['score'] for item in stats['high_maturity'][:8]]
            html += create_svg_radar(strength_cats, strength_vals, '#35DE6D', 'Styrkeomrader')
        html += '</div>'
    
    if stats['low_maturity']:
        html += '<div class="chart-container">'
        if len(stats['low_maturity']) >= 3:
            improve_cats = [item['title'][:20] for item in stats['low_maturity'][:8]]
            improve_vals = [item['score'] for item in stats['low_maturity'][:8]]
            html += create_svg_radar(improve_cats, improve_vals, '#FF6B6B', 'Forbedringsomrader')
        html += '</div>'
    html += '</div>'
    
    # Detaljer
    if stats['high_maturity']:
        html += "<h4>Styrkeomrader (score >= 4)</h4>"
        for item in stats['high_maturity'][:10]:
            html += f'<div class="item item-strength"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
    
    if stats['low_maturity']:
        html += "<h4>Forbedringsomrader (score < 3)</h4>"
        for item in stats['low_maturity'][:10]:
            html += f'<div class="item item-improvement"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
    
    # Parameter resultater
    if stats['parameters']:
        html += "<h3>1.4 Resultater per parameter</h3>"
        html += "<table><tr><th>Parameter</th><th>Score</th><th>Beskrivelse</th></tr>"
        for name, data in stats['parameters'].items():
            html += f"<tr><td>{name}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['description']}</td></tr>"
        html += "</table>"
    
    # Intervjuoversikt
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
    
    # DEL 2: Resultater per gevinst
    html += '<div class="page-break"></div>'
    html += "<h2>DEL 2: Resultater per gevinst</h2>"
    
    # Samle gevinster
    benefits = initiative.get('benefits', {})
    benefit_interviews = {}  # benefit_id -> list of interviews
    general_interviews = []  # Intervjuer uten spesifikk gevinst
    
    for idx, (iid, interview) in enumerate(initiative.get('interviews', {}).items()):
        benefit_id = interview.get('info', {}).get('benefit_id', 'all')
        if benefit_id == 'all' or benefit_id not in benefits:
            general_interviews.append((idx, iid, interview))
        else:
            if benefit_id not in benefit_interviews:
                benefit_interviews[benefit_id] = []
            benefit_interviews[benefit_id].append((idx, iid, interview))
    
    # Hjelpefunksjon for å vise kommentarer for en gruppe intervjuer
    def render_comments_section(interviews_list, section_title="Kommentarer"):
        comments_html = ""
        has_any_comments = False
        
        for phase in PHASES:
            phase_comments = {}
            
            for idx, iid, interview in interviews_list:
                responses = interview.get('responses', {}).get(phase, {})
                for q_id, resp in responses.items():
                    notes = resp.get('notes', '').strip()
                    if notes:
                        if q_id not in phase_comments:
                            phase_comments[q_id] = []
                        anon_name = get_anonymous_name(idx)
                        phase_comments[q_id].append({
                            'participant': anon_name,
                            'score': resp.get('score', 0),
                            'notes': notes
                        })
                        has_any_comments = True
            
            if phase_comments:
                comments_html += f'<div class="comment-phase"><strong>{phase}</strong></div>'
                phase_questions = {str(q['id']): q['title'] for q in questions_data.get(phase, [])}
                
                for q_id in sorted(phase_comments.keys(), key=lambda x: int(x)):
                    q_title = phase_questions.get(q_id, f"Sporsmal {q_id}")
                    comments_html += f'<div class="comment-question"><h4>{q_id}. {q_title}</h4>'
                    
                    for comment in phase_comments[q_id]:
                        comments_html += f'''<div class="comment-item">
                            <div class="comment-meta">{comment['participant']} <span class="score-badge">Niva {comment['score']}</span></div>
                            <div class="comment-text">{comment['notes']}</div>
                        </div>'''
                    
                    comments_html += '</div>'
        
        if has_any_comments:
            return f"<h4>{section_title}</h4>" + comments_html
        return ""
    
    # Hjelpefunksjon for å beregne stats for en gruppe intervjuer
    def calculate_benefit_stats(interviews_list):
        if not interviews_list:
            return None
        
        all_scores = {}
        for phase in PHASES:
            all_scores[phase] = {}
            for q in questions_data[phase]:
                all_scores[phase][q['id']] = []
        
        for idx, iid, interview in interviews_list:
            for phase, questions in interview.get('responses', {}).items():
                for q_id, resp in questions.items():
                    if resp.get('score', 0) > 0:
                        all_scores[phase][int(q_id)].append(resp['score'])
        
        benefit_stats = {
            'phases': {},
            'questions': {},
            'parameters': {},
            'total_interviews': len(interviews_list),
            'overall_avg': 0,
            'high_maturity': [],
            'low_maturity': []
        }
        
        all_avgs = []
        for phase in PHASES:
            phase_scores = []
            benefit_stats['questions'][phase] = {}
            
            for q in questions_data[phase]:
                scores = all_scores[phase][q['id']]
                if scores:
                    avg = sum(scores) / len(scores)
                    benefit_stats['questions'][phase][q['id']] = {'avg': avg, 'count': len(scores), 'title': q['title']}
                    phase_scores.append(avg)
                    all_avgs.append(avg)
                    
                    item = {'phase': phase, 'question_id': q['id'], 'title': q['title'], 'score': avg}
                    if avg >= 4:
                        benefit_stats['high_maturity'].append(item)
                    elif avg < 3:
                        benefit_stats['low_maturity'].append(item)
            
            if phase_scores:
                benefit_stats['phases'][phase] = {'avg': sum(phase_scores)/len(phase_scores), 'min': min(phase_scores), 'max': max(phase_scores)}
        
        if all_avgs:
            benefit_stats['overall_avg'] = sum(all_avgs) / len(all_avgs)
        
        benefit_stats['high_maturity'].sort(key=lambda x: x['score'], reverse=True)
        benefit_stats['low_maturity'].sort(key=lambda x: x['score'])
        
        return benefit_stats
    
    # Vis resultater per gevinst
    if benefits and benefit_interviews:
        for ben_id, ben in benefits.items():
            if ben_id in benefit_interviews and benefit_interviews[ben_id]:
                interviews_list = benefit_interviews[ben_id]
                ben_stats = calculate_benefit_stats(interviews_list)
                
                if ben_stats and ben_stats['total_interviews'] > 0:
                    html += f'''
                    <div class="benefit-section">
                        <div class="benefit-header">
                            <h3 style="margin: 0; color: white;">Gevinst: {ben['name']}</h3>
                        </div>
                        
                        <div class="metric-row">
                            <div class="metric-card">
                                <div class="metric-value">{ben_stats['total_interviews']}</div>
                                <div class="metric-label">Intervjuer</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{ben_stats['overall_avg']:.2f}</div>
                                <div class="metric-label">Gjennomsnitt</div>
                            </div>
                            <div class="metric-card" style="border-left-color: #35DE6D;">
                                <div class="metric-value" style="color: #35DE6D;">{len(ben_stats['high_maturity'])}</div>
                                <div class="metric-label">Styrker</div>
                            </div>
                            <div class="metric-card" style="border-left-color: #FF6B6B;">
                                <div class="metric-value" style="color: #FF6B6B;">{len(ben_stats['low_maturity'])}</div>
                                <div class="metric-label">Forbedring</div>
                            </div>
                        </div>
                    '''
                    
                    # Diagrammer for denne gevinsten
                    if ben_stats['phases'] and len(ben_stats['phases']) >= 3:
                        html += '<div class="charts-row">'
                        phase_cats = list(ben_stats['phases'].keys())
                        phase_vals = [ben_stats['phases'][p]['avg'] for p in phase_cats]
                        html += '<div class="chart-container">'
                        html += create_svg_radar(phase_cats, phase_vals, '#0053A6', f'Faser - {ben["name"][:20]}')
                        html += '</div>'
                        html += '</div>'
                    
                    # Styrker og forbedringer for denne gevinsten
                    if ben_stats['high_maturity']:
                        html += "<h4>Styrkeomrader</h4>"
                        for item in ben_stats['high_maturity'][:5]:
                            html += f'<div class="item item-strength"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
                    
                    if ben_stats['low_maturity']:
                        html += "<h4>Forbedringsomrader</h4>"
                        for item in ben_stats['low_maturity'][:5]:
                            html += f'<div class="item item-improvement"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
                    
                    # Kommentarer for denne gevinsten
                    html += render_comments_section(interviews_list, "Kommentarer for denne gevinsten")
                    
                    html += "</div>"  # End benefit-section
    
    # Generelle intervjuer (uten spesifikk gevinst)
    if general_interviews:
        html += '''
        <div class="benefit-section">
            <div class="benefit-header">
                <h3 style="margin: 0; color: white;">Generelt for initiativet</h3>
            </div>
        '''
        
        gen_stats = calculate_benefit_stats(general_interviews)
        if gen_stats and gen_stats['total_interviews'] > 0:
            html += f'''
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-value">{gen_stats['total_interviews']}</div>
                    <div class="metric-label">Intervjuer</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{gen_stats['overall_avg']:.2f}</div>
                    <div class="metric-label">Gjennomsnitt</div>
                </div>
            </div>
            '''
        
        # Kommentarer for generelle intervjuer
        html += render_comments_section(general_interviews, "Kommentarer")
        html += "</div>"
    
    # Hvis ingen gevinst-spesifikke intervjuer, vis alle kommentarer på overordnet nivå
    if not benefit_interviews and not general_interviews:
        all_interviews = [(idx, iid, interview) for idx, (iid, interview) in enumerate(initiative.get('interviews', {}).items())]
        if all_interviews:
            html += '''
            <div class="benefit-section">
                <div class="benefit-header">
                    <h3 style="margin: 0; color: white;">Alle kommentarer</h3>
                </div>
            '''
            html += render_comments_section(all_interviews, "Kommentarer fra alle intervjuer")
            html += "</div>"
    
    html += f'<div class="footer">Generert {datetime.now().strftime("%d.%m.%Y %H:%M")} | Bane NOR - Modenhetsvurdering Gevinstrealisering</div></body></html>'
    return html

# ============================================================================
# RAPPORT-GENERERING - TXT
# ============================================================================
def generate_txt_report(initiative, stats):
    lines = []
    lines.append("=" * 60)
    lines.append("MODENHETSVURDERING - GEVINSTREALISERING")
    lines.append("Gjennomfores i samarbeid med konsern okonomi og digital transformasjon")
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
        lines.append("3. STYRKEOMRADER (score >= 4)")
        lines.append("-" * 40)
        for item in stats['high_maturity'][:10]:
            lines.append(f"  [{item['phase']}] {item['title']}: {item['score']:.2f}")
        lines.append("")
    
    if stats['low_maturity']:
        lines.append("4. FORBEDRINGSOMRADER (score < 3)")
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
    
    # Seksjon 7: Kommentarer
    lines.append("7. KOMMENTARER PER FASE OG SPORSMAL")
    lines.append("-" * 40)
    has_any_comments = False
    
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
                    phase_comments[q_id].append({
                        'participant': anon_name,
                        'score': resp.get('score', 0),
                        'notes': notes
                    })
                    has_any_comments = True
        
        if phase_comments:
            lines.append("")
            lines.append(f"  [{phase}]")
            lines.append("  " + "~" * 30)
            
            phase_questions = {str(q['id']): q['title'] for q in questions_data.get(phase, [])}
            
            for q_id in sorted(phase_comments.keys(), key=lambda x: int(x)):
                q_title = phase_questions.get(q_id, f"Sporsmal {q_id}")
                lines.append(f"    {q_id}. {q_title}")
                
                for comment in phase_comments[q_id]:
                    lines.append(f"      - {comment['participant']} (Niva {comment['score']}):")
                    # Bryt opp lange kommentarer
                    words = comment['notes'].split()
                    line = "        "
                    for word in words:
                        if len(line) + len(word) + 1 > 70:
                            lines.append(line)
                            line = "        " + word
                        else:
                            line = line + " " + word if line.strip() else "        " + word
                    if line.strip():
                        lines.append(line)
                lines.append("")
    
    if not has_any_comments:
        lines.append("  Ingen kommentarer registrert.")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR")
    lines.append("=" * 60)
    
    return "\n".join(lines)

# ============================================================================
# RAPPORT-GENERERING - PDF (med FPDF)
# ============================================================================
def safe_text(text):
    """Convert Norwegian characters to ASCII for PDF"""
    replacements = {
        'æ': 'ae', 'Æ': 'Ae',
        'ø': 'o', 'Ø': 'O',
        'å': 'a', 'Å': 'A'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_pdf_report(initiative, stats):
    if not FPDF_AVAILABLE:
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Tittel
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 10, 'Modenhetsvurdering - Gevinstrealisering', ln=True, align='C')
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 8, 'Bane NOR', ln=True, align='C')
        pdf.ln(10)
        
        # Sammendrag
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '1. Sammendrag', ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, safe_text(f"Endringsinitiativ: {initiative['name']}"), ln=True)
        pdf.cell(0, 7, f"Rapportdato: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        pdf.cell(0, 7, f"Antall intervjuer: {stats['total_interviews']}", ln=True)
        pdf.cell(0, 7, safe_text(f"Samlet modenhet: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})"), ln=True)
        pdf.ln(5)
        
        # Faser
        if stats['phases']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '2. Modenhet per fase', ln=True)
            pdf.set_font('Helvetica', '', 11)
            for phase, data in stats['phases'].items():
                pdf.cell(0, 7, safe_text(f"  {phase}: {data['avg']:.2f}"), ln=True)
            pdf.ln(5)
        
        # Styrker
        if stats['high_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, safe_text('3. Styrkeomrader'), ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['high_maturity'][:8]:
                text = safe_text(f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}")
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)
        
        # Forbedring
        if stats['low_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, safe_text('4. Forbedringsomrader'), ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['low_maturity'][:8]:
                text = safe_text(f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}")
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)
        
        # Parametere
        if stats['parameters']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '5. Resultater per parameter', ln=True)
            pdf.set_font('Helvetica', '', 10)
            for name, data in stats['parameters'].items():
                pdf.cell(0, 6, safe_text(f"  {name}: {data['avg']:.2f}"), ln=True)
            pdf.ln(5)
        
        # Intervjuoversikt (anonymisert)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '6. Intervjuoversikt (anonymisert)', ln=True)
        pdf.set_font('Helvetica', '', 10)
        for idx, interview in enumerate(initiative.get('interviews', {}).values()):
            info = interview.get('info', {})
            total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
            total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
            avg = total_score / total_answered if total_answered > 0 else 0
            anon_name = get_anonymous_name(idx)
            avg_str = f"{avg:.2f}" if avg > 0 else "-"
            pdf.cell(0, 6, safe_text(f"  {anon_name} | {info.get('phase', '-')} | Snitt: {avg_str}"), ln=True)
        pdf.ln(5)
        
        # NY SEKSJON: Kommentarer per sporsmal
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '7. Kommentarer per fase og sporsmal', ln=True)
        
        # Samle alle kommentarer fra alle intervjuer
        for phase in PHASES:
            phase_has_comments = False
            phase_comments = {}
            
            # Sjekk om det finnes kommentarer for denne fasen
            for idx, interview in enumerate(initiative.get('interviews', {}).values()):
                responses = interview.get('responses', {}).get(phase, {})
                for q_id, resp in responses.items():
                    notes = resp.get('notes', '').strip()
                    if notes:
                        if q_id not in phase_comments:
                            phase_comments[q_id] = []
                        anon_name = get_anonymous_name(idx)
                        phase_comments[q_id].append({
                            'participant': anon_name,
                            'score': resp.get('score', 0),
                            'notes': notes
                        })
                        phase_has_comments = True
            
            if phase_has_comments:
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, safe_text(f"\n{phase}"), ln=True)
                pdf.set_font('Helvetica', '', 9)
                
                # Finn sporsmalstitler
                phase_questions = {str(q['id']): q['title'] for q in questions_data.get(phase, [])}
                
                for q_id in sorted(phase_comments.keys(), key=lambda x: int(x)):
                    q_title = phase_questions.get(q_id, f"Sporsmal {q_id}")
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, safe_text(f"  {q_id}. {q_title[:50]}"), ln=True)
                    pdf.set_font('Helvetica', '', 9)
                    
                    for comment in phase_comments[q_id]:
                        # Deltaker og score
                        pdf.set_font('Helvetica', 'I', 9)
                        pdf.cell(0, 5, safe_text(f"    {comment['participant']} (Niva {comment['score']}):"), ln=True)
                        # Kommentar - bryt opp lange linjer
                        pdf.set_font('Helvetica', '', 9)
                        notes_text = safe_text(comment['notes'])
                        # Del opp i linjer på maks 80 tegn
                        words = notes_text.split()
                        line = "      "
                        for word in words:
                            if len(line) + len(word) + 1 > 85:
                                pdf.cell(0, 4, line, ln=True)
                                line = "      " + word
                            else:
                                line = line + " " + word if line.strip() else "      " + word
                        if line.strip():
                            pdf.cell(0, 4, line, ln=True)
                    pdf.ln(2)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 10, f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR", ln=True, align='C')
        
        # Return as bytes
        return bytes(pdf.output())
    except Exception as e:
        return None

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def show_project_selector(data):
    """Viser prosjektvelger-skjermen"""
    st.markdown(f'''
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 style="margin:0;color:{COLORS['primary_dark']};font-size:2rem;font-weight:700;">Modenhetsvurdering</h1>
        <p style="color:{COLORS['primary']};font-size:0.95rem;margin-top:0.3rem;">Gjennomfores i samarbeid med konsern okonomi og digital transformasjon</p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Apne eksisterende prosjekt")
        if data['initiatives']:
            # Vis liste over prosjekter (bare navn)
            project_names = {init_id: init['name'] for init_id, init in data['initiatives'].items()}
            selected_project = st.selectbox("Velg prosjekt", options=list(project_names.keys()), format_func=lambda x: project_names[x])
            
            # Sjekk om prosjektet har tilgangskode
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
            st.info("Ingen prosjekter opprettet enda. Opprett et nytt prosjekt til hoyre.")
    
    with col2:
        st.markdown("### Opprett nytt prosjekt")
        with st.form("new_project_form"):
            new_name = st.text_input("Prosjektnavn", placeholder="F.eks. ERTMS Ostlandet")
            new_desc = st.text_area("Beskrivelse", height=80)
            new_code = st.text_input("Tilgangskode (valgfritt)", type="password", help="La sta tom for apent prosjekt")
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
    
    st.markdown("---")
    st.markdown(f'<div style="text-align:center;color:#666;font-size:0.85rem;padding:10px 0;">Gjennomfores i samarbeid med konsern okonomi og digital transformasjon</div>', unsafe_allow_html=True)

def show_main_app(data, current_project_id):
    """Viser hovedapplikasjonen for valgt prosjekt"""
    initiative = data['initiatives'][current_project_id]
    
    # Header med prosjektnavn og logg ut-knapp
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
        st.write("")  # Placeholder for balanse
    
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
    
    # TAB 2: GEVINSTER (tidligere Endringsinitiativ)
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
                current_code = st.text_input("Navaerende kode (la tom hvis ingen)", type="password")
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
                
                focus_mode = st.radio("Fokusmodus", options=["Rollebasert", "Parameterbasert", "Alle sporsmal"], horizontal=True)
                
                selected_role = None
                selected_params = []
                recommended = []
                
                if focus_mode == "Rollebasert":
                    selected_role = st.selectbox("Rolle", options=list(ROLES.keys()))
                    recommended = get_recommended_questions("role", selected_role, selected_phase)
                    st.caption(ROLES[selected_role]['description'])
                    st.success(f"{len(recommended)} anbefalte sporsmal. Alle 23 tilgjengelige.")
                elif focus_mode == "Parameterbasert":
                    selected_params = st.multiselect("Parametere", options=list(PARAMETERS.keys()), default=list(PARAMETERS.keys())[:2])
                    recommended = get_recommended_questions("parameter", selected_params, selected_phase)
                    st.success(f"{len(recommended)} anbefalte sporsmal. Alle 23 tilgjengelige.")
                
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
                    
                    answered = sum(1 for q_id in range(1, 24) if interview['responses'][phase].get(str(q_id), {}).get('score', 0) > 0)
                    st.progress(answered / 23)
                    st.caption(f"Besvart: {answered} av 23")
                    
                    questions = questions_data[phase]
                    recommended_qs = [q for q in questions if q['id'] in recommended]
                    other_qs = [q for q in questions if q['id'] not in recommended]
                    
                    if recommended_qs:
                        st.markdown("### Anbefalte sporsmal")
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
                        st.markdown("### Andre sporsmal")
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
                        st.markdown(f'''<div style="display:flex;align-items:center;gap:10px;padding:8px;background:{COLORS['gray_light']};border-radius:6px;margin:4px 0;">
                            <span style="flex:1;font-weight:600;">{phase_name}</span>
                            <span style="color:{get_score_color(phase_data['avg'])};font-weight:700;">{phase_data['avg']:.2f}</span>
                        </div>''', unsafe_allow_html=True)
                    fig = create_phase_radar(stats['phases'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("### Modenhet per parameter")
                if stats['parameters']:
                    fig = create_parameter_radar(stats['parameters'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Styrkeomrader")
                if stats['high_maturity']:
                    # Radar diagram FØRST
                    fig = create_strength_radar(stats['high_maturity'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Fallback til bar chart hvis færre enn 3 items
                        fig = create_strength_bar_chart(stats['high_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    # Deretter detaljer
                    st.markdown("#### Detaljer")
                    for item in stats['high_maturity'][:5]:
                        st.markdown(f'<div class="strength-card"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                else:
                    st.info("Ingen styrkeomrader identifisert")
            with col2:
                st.markdown("### Forbedringsomrader")
                if stats['low_maturity']:
                    # Radar diagram FØRST
                    fig = create_improvement_radar(stats['low_maturity'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Fallback til bar chart hvis færre enn 3 items
                        fig = create_improvement_bar_chart(stats['low_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    # Deretter detaljer
                    st.markdown("#### Detaljer")
                    for item in stats['low_maturity'][:5]:
                        st.markdown(f'<div class="improvement-card"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                else:
                    st.success("Ingen kritiske forbedringsomrader!")
    
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
                        csv_data.append({'Fase': phase, 'SporsmalID': q_id, 'Tittel': q_data['title'], 'Gjennomsnitt': round(q_data['avg'], 2), 'AntallSvar': q_data['count']})
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
                    st.info("For PDF-rapport, kjor: `pip install fpdf2`")
            
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
    
    st.markdown("---")
    st.markdown(f'<div style="text-align:center;color:#666;font-size:0.85rem;padding:10px 0;">Gevinstmodenhetsvurdering på tvers av endringsinitiativer</div>', unsafe_allow_html=True)

def main():
    """Hovedfunksjon - håndterer prosjektvalg og hovedapplikasjon"""
    data = get_data()
    
    # Sjekk om bruker har valgt et prosjekt
    if 'current_project' not in st.session_state:
        show_project_selector(data)
    else:
        current_project_id = st.session_state['current_project']
        # Verifiser at prosjektet fortsatt eksisterer
        if current_project_id not in data['initiatives']:
            del st.session_state['current_project']
            st.rerun()
        else:
            show_main_app(data, current_project_id)

if __name__ == "__main__":
    main()
