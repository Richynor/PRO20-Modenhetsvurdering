"""
MODENHETSVURDERING - GEVINSTREALISERING
Bane NOR - Konsern økonomi og digital transformasjon
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import pickle
import os
import tempfile
import base64
from io import BytesIO

# ============================================================================
# KONFIGURASJON
# ============================================================================
st.set_page_config(
    page_title="Modenhetsvurdering - Bane NOR",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "modenhet_data.pkl"

# ============================================================================
# BANE NOR FARGEPALETT
# ============================================================================
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

# ============================================================================
# HENSIKT OG FORMÅL
# ============================================================================
HENSIKT_TEKST = """
### Hensikt
Modenhetsvurderingen har som formål å synliggjøre gode erfaringer og identifisere forbedringsområder i vårt arbeid med gevinster. Vi ønsker å lære av hverandre, dele beste praksis og hjelpe initiativer til å lykkes bedre med å skape og realisere gevinster.

Et sentralt fokusområde er å sikre at gevinstene vi arbeider med er konkrete og realitetsorienterte. Dette innebærer at nullpunkter og estimater er testet og validert, at hypoteser er prøvd mot representative caser og faktiske arbeidsforhold, og at forutsetningene for gevinstuttak er realistiske og forankret.

### Hvem inviteres?
Vi ønsker å intervjue alle som har vært eller er involvert i gevinstarbeidet – enten du har bidratt til utarbeidelse av business case, gevinstkart, gevinstrealiseringsplaner eller målinger, eller du har hatt ansvar for oppfølging og realisering.

### Hva vurderes?
Intervjuene dekker hele gevinstlivssyklusen – fra planlegging og gjennomføring til realisering og evaluering.

### Gevinster i endringsinitiativ
Et endringsinitiativ kan ha flere konkrete gevinster. Intervjuene kan gjennomføres med fokus på én spesifikk gevinst, eller for initiativet som helhet.
"""

# ============================================================================
# ROLLEDEFINISJONER
# ============================================================================
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
    "Sponsor / Styringsgruppe": {
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
    }
}

# ============================================================================
# PARAMETERE
# ============================================================================
PARAMETERS = {
    "Strategisk forankring": {
        "description": "Strategisk retning, kobling til mål og KPI-er",
        "questions": [2, 4]
    },
    "Gevinstkart og visualisering": {
        "description": "Gevinstkart, sammenhenger mellom tiltak og effekter",
        "questions": [3]
    },
    "Nullpunkter og estimater": {
        "description": "Kvalitet på nullpunkter, estimater og datagrunnlag",
        "questions": [6, 7, 11]
    },
    "Interessenter og forankring": {
        "description": "Interessentengasjement, kommunikasjon og forankring",
        "questions": [8, 19]
    },
    "Eierskap og ansvar": {
        "description": "Roller, ansvar og eierskap for gevinstuttak",
        "questions": [20]
    },
    "Forutsetninger og risiko": {
        "description": "Gevinstforutsetninger, risiko og ulemper",
        "questions": [9, 10, 14, 15]
    },
    "Gevinstrealiseringsplan": {
        "description": "Plan som operativt styringsverktøy",
        "questions": [16, 17]
    },
    "Effektivitet og produktivitet": {
        "description": "Måling, disponering og bærekraft",
        "questions": [12, 13]
    },
    "Læring og forbedring": {
        "description": "Bruk av tidligere erfaringer og kontinuerlig læring",
        "questions": [1]
    },
    "Momentum og tidlig gevinstuttak": {
        "description": "Bygge momentum gjennom tidlig gevinstrealisering",
        "questions": [5, 21, 22, 23]
    }
}

# ============================================================================
# KOMPLETT SPØRSMÅLSSETT - ALLE 23 SPØRSMÅL PER FASE
# ============================================================================
PHASES = ["Planlegging", "Gjennomføring", "Realisering", "Realisert"]

questions_data = {
    "Planlegging": [
        {"id": 1, "title": "Bruk av tidligere læring og gevinstdata", "question": "Hvordan anvendes erfaringer og læring fra tidligere prosjekter og gevinstarbeid i planleggingen av nye gevinster?",
         "scale": ["Nivå 1: Ingen læring fra tidligere arbeid anvendt.", "Nivå 2: Enkelte erfaringer omtalt, men ikke strukturert brukt.", "Nivå 3: Læring inkludert i planlegging for enkelte områder.", "Nivå 4: Systematisk bruk av tidligere gevinstdata i planlegging og estimering.", "Nivå 5: Kontinuerlig læring integrert i planleggingsprosessen og gevinststrategien."]},
        {"id": 2, "title": "Strategisk retning og gevinstforståelse", "question": "Hvilke gevinster arbeider dere med, og hvorfor er de viktige for organisasjonens strategiske mål?",
         "scale": ["Nivå 1: Gevinster er vagt definert, uten tydelig kobling til strategi.", "Nivå 2: Gevinster er identifisert, men mangler klare kriterier og prioritering.", "Nivå 3: Gevinster er dokumentert og delvis knyttet til strategiske mål, men grunnlaget har usikkerhet.", "Nivå 4: Gevinster er tydelig koblet til strategiske mål med konkrete måltall.", "Nivå 5: Gevinster er fullt integrert i styringssystemet og brukes i beslutninger."]},
        {"id": 3, "title": "Gevinstkart og visualisering", "question": "Er gevinstene synliggjort i gevinstkartet, med tydelig sammenheng mellom tiltak, effekter og mål?",
         "scale": ["Nivå 1: Gevinstkart finnes ikke eller er utdatert.", "Nivå 2: Et foreløpig gevinstkart eksisterer, men dekker ikke hele området.", "Nivå 3: Kartet inkluderer hovedgevinster, men mangler validering og detaljer.", "Nivå 4: Kartet er brukt aktivt i planlegging og oppfølging.", "Nivå 5: Gevinstkartet oppdateres kontinuerlig og er integrert i styringsdialoger."]},
        {"id": 4, "title": "Strategisk kobling og KPI-er", "question": "Er gevinstene tydelig knyttet til strategiske mål og eksisterende KPI-er?",
         "scale": ["Nivå 1: Ingen kobling mellom gevinster og strategi eller KPI-er.", "Nivå 2: Kobling er antatt, men ikke dokumentert.", "Nivå 3: Kobling er etablert for enkelte KPI-er, men ikke konsistent.", "Nivå 4: Tydelig kobling mellom gevinster og relevante KPI-er.", "Nivå 5: Koblingen følges opp i styringssystem og rapportering."]},
        {"id": 5, "title": "Avgrensning av programgevinst", "question": "Er det tydelig avklart hvilke effekter som stammer fra programmet versus andre tiltak eller økte rammer?",
         "scale": ["Nivå 1: Ingen skille mellom program- og eksterne effekter.", "Nivå 2: Delvis omtalt, men uklart hva som er innenfor programmet.", "Nivå 3: Avgrensning er gjort i plan, men ikke dokumentert grundig.", "Nivå 4: Avgrensning er dokumentert og anvendt i beregninger.", "Nivå 5: Effektisolering er standard praksis og brukes systematisk."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Er nullpunkter og estimater etablert, testet og dokumentert på en konsistent og troverdig måte?",
         "scale": ["Nivå 1: Nullpunkter mangler eller bygger på uprøvde antagelser.", "Nivå 2: Enkelte nullpunkter finnes, men uten felles metode.", "Nivå 3: Nullpunkter og estimater er definert, men med høy usikkerhet.", "Nivå 4: Nullpunkter og estimater er basert på testede data og validerte metoder.", "Nivå 5: Nullpunkter og estimater kvalitetssikres jevnlig og brukes aktivt til læring."]},
        {"id": 7, "title": "Hypotesetesting og datagrunnlag", "question": "Finnes formell prosess for hypotesetesting på representative caser?",
         "scale": ["Nivå 1: Ikke etablert/uklart; ingen dokumenterte praksiser.", "Nivå 2: Delvis definert; uformell praksis uten forankring/validering.", "Nivå 3: Etablert for deler av området; variabel kvalitet.", "Nivå 4: Godt forankret og systematisk anvendt; måles og følges opp.", "Nivå 5: Fullt integrert i styring; kontinuerlig forbedring og læring."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Ble relevante interessenter involvert i utarbeidelsen av gevinstgrunnlag?",
         "scale": ["Nivå 1: Ingen involvering av interessenter.", "Nivå 2: Begrenset og ustrukturert involvering.", "Nivå 3: Bred deltakelse, men uten systematisk prosess.", "Nivå 4: Systematisk og koordinert involvering med klar rollefordeling.", "Nivå 5: Kontinuerlig engasjement med dokumentert medvirkning."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Er alle vesentlige forutsetninger ivaretatt for å muliggjøre gevinstrealisering?",
         "scale": ["Nivå 1: Ingen kartlegging av gevinstforutsetninger.", "Nivå 2: Noen forutsetninger er identifisert, men ikke systematisk dokumentert.", "Nivå 3: Hovedforutsetninger er dokumentert, men uten klar eierskap.", "Nivå 4: Alle kritiske forutsetninger er kartlagt med tildelt ansvar.", "Nivå 5: Gevinstforutsetninger er integrert i risikostyring og oppfølges kontinuerlig."]},
        {"id": 10, "title": "Prinsipielle og vilkårsmessige kriterier", "question": "Er forutsetninger og kriterier som påvirker gevinstene tydelig definert og dokumentert?",
         "scale": ["Nivå 1: Ingen kriterier dokumentert.", "Nivå 2: Kriterier er beskrevet uformelt.", "Nivå 3: Kriterier dokumentert i deler av planverket.", "Nivå 4: Vesentlige kriterier er analysert og håndtert i gevinstrealiseringsplanen.", "Nivå 5: Kriterier overvåkes, følges opp og inngår i risikostyringen."]},
        {"id": 11, "title": "Enighet om nullpunkter/estimater", "question": "Er det oppnådd enighet blant nøkkelinteressenter om nullpunkter og estimater?",
         "scale": ["Nivå 1: Ingen enighet eller dokumentert praksis.", "Nivå 2: Delvis enighet, men ikke formalisert.", "Nivå 3: Enighet for hovedestimater, men med reservasjoner.", "Nivå 4: Full enighet dokumentert og forankret.", "Nivå 5: Kontinuerlig dialog og justering av estimater med interessentene."]},
        {"id": 12, "title": "Disponering av kostnads- og tidsbesparelser", "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert mellom prissatte og ikke-prissatte gevinster?",
         "scale": ["Nivå 1: Ingen plan for disponering eller måling av besparelser.", "Nivå 2: Delvis oversikt, men ikke dokumentert eller fulgt opp.", "Nivå 3: Plan finnes for enkelte områder, men uten systematikk.", "Nivå 4: Disponering og effekter dokumentert og målt.", "Nivå 5: Frigjorte ressurser disponeres strategisk og måles som del av gevinstrealiseringen."]},
        {"id": 13, "title": "Måling av effektivitet og produktivitet", "question": "Hvordan måles økt effektivitet og produktivitet som følge av besparelser?",
         "scale": ["Nivå 1: Ingen måling av effektivitet eller produktivitet.", "Nivå 2: Enkelte målinger, men ikke systematisk.", "Nivå 3: Måling for enkelte gevinster, men begrenset fokus på bærekraft.", "Nivå 4: Systematisk måling og vurdering av om gevinster opprettholdes over tid.", "Nivå 5: Måling integrert i gevinstoppfølgingen, bærekraftige gevinster sikres."]},
        {"id": 14, "title": "Operasjonell risiko og ulemper", "question": "Er mulige negative konsekvenser eller ulemper identifisert og håndtert?",
         "scale": ["Nivå 1: Negative effekter ikke vurdert.", "Nivå 2: Kjent, men ikke håndtert.", "Nivå 3: Beskrevet, men ikke fulgt opp systematisk.", "Nivå 4: Håndtert og overvåket med tilpasning til ulike scenarier.", "Nivå 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."]},
        {"id": 15, "title": "Balanse mellom gevinster og ulemper", "question": "Hvordan sikres det at balansen mellom gevinster og ulemper vurderes?",
         "scale": ["Nivå 1: Ingen vurdering av balanse.", "Nivå 2: Diskuteres uformelt.", "Nivå 3: Del av enkelte oppfølgingsmøter.", "Nivå 4: Systematisk vurdert i gevinststyring.", "Nivå 5: Inngår som fast punkt i styrings- og gevinstdialoger."]},
        {"id": 16, "title": "Dokumentasjon og gevinstrealiseringsplan", "question": "Er det utarbeidet en forankret gevinstrealiseringsplan?",
         "scale": ["Nivå 1: Ingen formell gevinstrealiseringsplan.", "Nivå 2: Utkast til plan finnes, men er ufullstendig.", "Nivå 3: Plan er etablert, men ikke validert eller periodisert.", "Nivå 4: Planen er forankret, oppdatert og koblet til gevinstkartet.", "Nivå 5: Planen brukes aktivt som styringsdokument med revisjon."]},
        {"id": 17, "title": "Gevinstrealiseringsplan som operativ handlingsplan", "question": "Hvordan sikres det at gevinstrealiseringsplanen fungerer som en operativ handlingsplan?",
         "scale": ["Nivå 1: Planen brukes ikke som operativt styringsverktøy.", "Nivå 2: Plan finnes, men uten operativ oppfølging.", "Nivå 3: Planen følges delvis opp i linjen.", "Nivå 4: Planen brukes aktivt som handlingsplan og styringsverktøy.", "Nivå 5: Gevinstplanen er fullt operativt integrert i linjens handlingsplaner."]},
        {"id": 18, "title": "Endringsberedskap og operativ mottaksevne", "question": "Er organisasjonen forberedt på å ta imot endringer fra programmet?",
         "scale": ["Nivå 1: Ingen plan for endringsberedskap.", "Nivå 2: Kapasitet vurderes uformelt, men ikke håndtert.", "Nivå 3: Endringskapasitet omtales, men uten konkrete tiltak.", "Nivå 4: Tilfredsstillende beredskap etablert og koordinert med linjen.", "Nivå 5: Endringskapasitet er strukturert, overvåket og integrert i styring."]},
        {"id": 19, "title": "Kommunikasjon og forankring", "question": "Er gevinstgrunnlag, roller og forventninger godt kommunisert?",
         "scale": ["Nivå 1: Ingen felles forståelse eller kommunikasjon.", "Nivå 2: Informasjon deles sporadisk.", "Nivå 3: Kommunikasjon er planlagt, men ikke systematisk målt.", "Nivå 4: Kommunikasjon er systematisk og forankret i organisasjonen.", "Nivå 5: Forankring skjer løpende som del av styringsdialog."]},
        {"id": 20, "title": "Eierskap og ansvar", "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?",
         "scale": ["Nivå 1: Ansvar er uklart eller mangler.", "Nivå 2: Ansvar er delvis definert, men ikke praktisert.", "Nivå 3: Ansvar er kjent, men samhandling varierer.", "Nivå 4: Roller og ansvar fungerer godt i praksis.", "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."]},
        {"id": 21, "title": "Periodisering og forankring", "question": "Er gevinstrealiseringsplanen periodisert, validert og godkjent?",
         "scale": ["Nivå 1: Ingen tidsplan eller forankring.", "Nivå 2: Tidsplan foreligger, men ikke validert.", "Nivå 3: Delvis forankret hos enkelte ansvarlige/eiere.", "Nivå 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.", "Nivå 5: Planen brukes aktivt i styringsdialog og rapportering."]},
        {"id": 22, "title": "Realisme og engasjement", "question": "Oppleves gevinstplanen og estimatene realistiske og engasjerende?",
         "scale": ["Nivå 1: Ingen troverdighet eller engasjement.", "Nivå 2: Begrenset tillit til estimater.", "Nivå 3: Delvis aksept, men varierende engasjement.", "Nivå 4: Høy troverdighet og engasjement.", "Nivå 5: Sterk troverdighet og aktiv motivasjon i organisasjonen."]},
        {"id": 23, "title": "Bygge momentum og tidlig gevinstuttak", "question": "Hvordan planlegges det for å bygge momentum og realisere tidlige gevinster?",
         "scale": ["Nivå 1: Ingen plan for tidlig gevinstuttak.", "Nivå 2: Enkelte uformelle vurderinger av tidlige gevinster.", "Nivå 3: Plan for tidlig gevinstuttak er identifisert, men ikke koordinert.", "Nivå 4: Strukturert tilnærming for tidlig gevinstuttak med tildelt ansvar.", "Nivå 5: Tidlig gevinstuttak er integrert i programmets DNA."]}
    ],
    "Gjennomføring": [
        {"id": 1, "title": "Bruk av tidligere læring", "question": "Hvordan brukes erfaringer fra tidligere til å justere tiltak under gjennomføringen?",
         "scale": ["Nivå 1: Ingen læring anvendt.", "Nivå 2: Enkelte erfaringer omtalt.", "Nivå 3: Læring inkludert for enkelte områder.", "Nivå 4: Systematisk bruk av tidligere gevinstdata.", "Nivå 5: Kontinuerlig læring integrert."]},
        {"id": 2, "title": "Strategisk retning", "question": "Hvordan opprettholdes strategisk retning under gjennomføring?",
         "scale": ["Nivå 1: Strategisk kobling glemmes.", "Nivå 2: Strategi omtales, men ikke operasjonalisert.", "Nivå 3: Strategisk kobling vedlikeholdes delvis.", "Nivå 4: Tydelig strategisk retning med oppdatering.", "Nivå 5: Strategi dynamisk tilpasses."]},
        {"id": 3, "title": "Gevinstkart", "question": "Hvordan brukes gevinstkartet aktivt under gjennomføring?",
         "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Vises, men ikke aktivt brukt.", "Nivå 3: Oppdateres og brukes i noen beslutninger.", "Nivå 4: Aktivt styringsverktøy.", "Nivå 5: Brukes dynamisk til justering."]},
        {"id": 4, "title": "KPI-oppfølging", "question": "Hvordan følges strategisk kobling og KPI-er opp?",
         "scale": ["Nivå 1: Ingen oppfølging.", "Nivå 2: KPI-er måles, men kobling mangler.", "Nivå 3: Noen KPI-er følges opp.", "Nivå 4: Systematisk oppfølging.", "Nivå 5: Dynamisk justering."]},
        {"id": 5, "title": "Avgrensning", "question": "Hvordan håndteres avgrensning når nye forhold oppstår?",
         "scale": ["Nivå 1: Avgrensning glemmes.", "Nivå 2: Omtales, men ikke operasjonalisert.", "Nivå 3: Håndteres for større endringer.", "Nivå 4: System for håndtering.", "Nivå 5: Dynamisk avgrensning integrert."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan justeres nullpunkter og estimater basert på nye data?",
         "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Ad hoc justering.", "Nivå 3: Systematisk for store avvik.", "Nivå 4: Regelmessig revisjon.", "Nivå 5: Kontinuerlig basert på realtidsdata."]},
        {"id": 7, "title": "Hypotesetesting", "question": "Hvordan testes hypoteser under gjennomføring?",
         "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Noen uformelle tester.", "Nivå 3: Formell testing for kritiske hypoteser.", "Nivå 4: Systematisk testing og validering.", "Nivå 5: Kontinuerlig testing integrert."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement?",
         "scale": ["Nivå 1: Engasjement avtar.", "Nivå 2: Begrenset for viktige beslutninger.", "Nivå 3: Regelmessig for større endringer.", "Nivå 4: Systematisk oppfølging.", "Nivå 5: Kontinuerlig dialog og samskaping."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvåkes gevinstforutsetninger?",
         "scale": ["Nivå 1: Overvåkes ikke.", "Nivå 2: Noen overvåkes uformelt.", "Nivå 3: Systematisk for kritiske.", "Nivå 4: Aktiv håndtering av endrede.", "Nivå 5: Integrert i risikostyring."]},
        {"id": 10, "title": "Kriterier", "question": "Hvordan håndteres endringer i kriterier?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store endringer reaktivt.", "Nivå 3: System for håndtering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Dynamisk tilpasning."]},
        {"id": 11, "title": "Enighet", "question": "Hvordan opprettholdes enighet om estimater?",
         "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Bekreftes ved store endringer.", "Nivå 3: Regelmessig bekreftelse.", "Nivå 4: Systematisk arbeid.", "Nivå 5: Kontinuerlig dialog."]},
        {"id": 12, "title": "Disponering", "question": "Hvordan håndteres disponering av besparelser?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Justeres for store avvik.", "Nivå 3: Systematisk revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Optimal disponering integrert."]},
        {"id": 13, "title": "Effektivitetsmåling", "question": "Hvordan måles effektivitet og produktivitet?",
         "scale": ["Nivå 1: Måles ikke.", "Nivå 2: Noen målinger registreres.", "Nivå 3: Systematisk med begrenset analyse.", "Nivå 4: Regelmessig analyse og justering.", "Nivå 5: Realtids overvåkning."]},
        {"id": 14, "title": "Risiko", "question": "Hvordan identifiseres nye risikoer?",
         "scale": ["Nivå 1: Identifiseres ikke.", "Nivå 2: Store håndteres reaktivt.", "Nivå 3: Systematisk identifisering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Integrert i daglig drift."]},
        {"id": 15, "title": "Balanse", "question": "Hvordan vurderes balansen gevinster/ulemper?",
         "scale": ["Nivå 1: Vurderes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig vurdering.", "Nivå 4: Systematisk overvåkning.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 16, "title": "Plan-oppdatering", "question": "Hvordan oppdateres gevinstrealiseringsplanen?",
         "scale": ["Nivå 1: Oppdateres ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig oppdatering.", "Nivå 4: Aktivt i styring.", "Nivå 5: Dynamisk i sanntid."]},
        {"id": 17, "title": "Operativ plan", "question": "Hvordan fungerer planen som operativ handlingsplan?",
         "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Til visse operasjoner.", "Nivå 3: Integrert i deler.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Fullt integrert."]},
        {"id": 18, "title": "Endringsberedskap", "question": "Hvordan utvikles endringsberedskap?",
         "scale": ["Nivå 1: Utvikles ikke.", "Nivå 2: Begrenset fokus.", "Nivå 3: Systematisk arbeid.", "Nivå 4: Målrettet utvikling.", "Nivå 5: Kontinuerlig tilpasning."]},
        {"id": 19, "title": "Kommunikasjon", "question": "Hvordan opprettholdes kommunikasjon?",
         "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset om endringer.", "Nivå 3: Regelmessig om fremdrift.", "Nivå 4: Systematisk plan.", "Nivå 5: Kontinuerlig dialog integrert."]},
        {"id": 20, "title": "Eierskap", "question": "Hvordan utøves eierskap og ansvar?",
         "scale": ["Nivå 1: Svekkes.", "Nivå 2: Begrenset i kritiske faser.", "Nivå 3: Tydelig for sentrale områder.", "Nivå 4: Aktivt gjennom hele prosessen.", "Nivå 5: Sterk kultur som driver."]},
        {"id": 21, "title": "Periodisering", "question": "Hvordan justeres periodisering?",
         "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Store justeringer.", "Nivå 3: Regelmessig revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Fleksibel integrert."]},
        {"id": 22, "title": "Realisme", "question": "Hvordan opprettholdes realisme og engasjement?",
         "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset fokus.", "Nivå 3: Arbeid med å opprettholde.", "Nivå 4: Systematisk styrking.", "Nivå 5: Høy gjennom hele prosessen."]},
        {"id": 23, "title": "Momentum", "question": "Hvordan bygges momentum gjennom tidlig gevinstuttak?",
         "scale": ["Nivå 1: Ingen fokus.", "Nivå 2: Noen gevinster uten strategi.", "Nivå 3: Planlagt, men begrenset.", "Nivå 4: Systematisk arbeid.", "Nivå 5: Kontinuerlig fokus."]}
    ],
    "Realisering": [
        {"id": 1, "title": "Læring", "question": "Hvordan anvendes læring for å optimalisere gevinstuttak?",
         "scale": ["Nivå 1: Ingen læring.", "Nivå 2: Enkelte erfaringer.", "Nivå 3: Systematisk bruk.", "Nivå 4: Integrert i prosessen.", "Nivå 5: Kontinuerlig optimalisering."]},
        {"id": 2, "title": "Strategisk retning", "question": "Hvordan sikres strategisk retning under realisering?",
         "scale": ["Nivå 1: Glemmes.", "Nivå 2: Refereres, ikke operasjonalisert.", "Nivå 3: Tydelig retning.", "Nivå 4: Dynamisk tilpasses.", "Nivå 5: Fullt integrert."]},
        {"id": 3, "title": "Gevinstkart", "question": "Hvordan brukes gevinstkartet for å styre realiseringen?",
         "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Vises, ikke aktivt.", "Nivå 3: Brukes til prioritering.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Dynamisk oppdateres."]},
        {"id": 4, "title": "KPI-er", "question": "Hvordan følges KPI-er opp under realisering?",
         "scale": ["Nivå 1: Ingen oppfølging.", "Nivå 2: Måles, svak kobling.", "Nivå 3: Systematisk oppfølging.", "Nivå 4: Dynamisk justering.", "Nivå 5: Full integrasjon."]},
        {"id": 5, "title": "Avgrensning", "question": "Hvordan håndteres avgrensning under realisering?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store utfordringer håndteres.", "Nivå 3: System for håndtering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Integrert i prosessen."]},
        {"id": 6, "title": "Nullpunkter", "question": "Hvordan valideres nullpunkter under realisering?",
         "scale": ["Nivå 1: Valideres ikke.", "Nivå 2: Store avvik reaktivt.", "Nivå 3: Systematisk validering.", "Nivå 4: Kontinuerlig justering.", "Nivå 5: Dynamisk oppdatering."]},
        {"id": 7, "title": "Hypoteser", "question": "Hvordan valideres hypoteser under realisering?",
         "scale": ["Nivå 1: Valideres ikke.", "Nivå 2: Noen testes uformelt.", "Nivå 3: Systematisk for kritiske.", "Nivå 4: Omfattende validering.", "Nivå 5: Kontinuerlig testing."]},
        {"id": 8, "title": "Interessenter", "question": "Hvordan opprettholdes interessentengasjement?",
         "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset for beslutninger.", "Nivå 3: Regelmessig dialog.", "Nivå 4: Aktivt engasjement.", "Nivå 5: Interessenter er drivkrefter."]},
        {"id": 9, "title": "Forutsetninger", "question": "Hvordan realiseres gevinstforutsetninger?",
         "scale": ["Nivå 1: Overvåkes ikke.", "Nivå 2: Noen følges opp.", "Nivå 3: Systematisk overvåkning.", "Nivå 4: Aktiv realisering.", "Nivå 5: Integrert i gevinstuttak."]},
        {"id": 10, "title": "Kriterier", "question": "Hvordan håndteres kriterier under realisering?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store avvik håndteres.", "Nivå 3: Systematisk håndtering.", "Nivå 4: Proaktiv tilpasning.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 11, "title": "Enighet", "question": "Hvordan opprettholdes enighet?",
         "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig bekreftelse.", "Nivå 4: Kontinuerlig arbeid.", "Nivå 5: Full enighet gjennom fasen."]},
        {"id": 12, "title": "Disponering", "question": "Hvordan håndteres disponering?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store endringer håndteres.", "Nivå 3: Systematisk revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Optimal disponering."]},
        {"id": 13, "title": "Effektivitet", "question": "Hvordan forbedres effektivitet?",
         "scale": ["Nivå 1: Måles ikke.", "Nivå 2: Noen målinger.", "Nivå 3: Systematisk rapportering.", "Nivå 4: Brukes til forbedring.", "Nivå 5: Kontinuerlig forbedring."]},
        {"id": 14, "title": "Risiko", "question": "Hvordan håndteres risikoer?",
         "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store reaktivt.", "Nivå 3: Systematisk håndtering.", "Nivå 4: Proaktiv.", "Nivå 5: Integrert i arbeid."]},
        {"id": 15, "title": "Balanse", "question": "Hvordan vurderes balansen?",
         "scale": ["Nivå 1: Vurderes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig.", "Nivå 4: Systematisk.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 16, "title": "Plan", "question": "Hvordan brukes planen?",
         "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Refereres ved behov.", "Nivå 3: Aktivt i realisering.", "Nivå 4: Oppdateres kontinuerlig.", "Nivå 5: Sentralt verktøy."]},
        {"id": 17, "title": "Operativ plan", "question": "Hvordan fungerer planen operativt?",
         "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Til enkelte operasjoner.", "Nivå 3: Integrert i styring.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Driver virksomhet."]},
        {"id": 18, "title": "Mottaksevne", "question": "Hvordan utvikles mottaksevne?",
         "scale": ["Nivå 1: Utvikles ikke.", "Nivå 2: Begrenset fokus.", "Nivå 3: Systematisk arbeid.", "Nivå 4: Målrettet utvikling.", "Nivå 5: Høy mottaksevne."]},
        {"id": 19, "title": "Kommunikasjon", "question": "Hvordan opprettholdes kommunikasjon?",
         "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset.", "Nivå 3: Regelmessig.", "Nivå 4: Systematisk.", "Nivå 5: Kontinuerlig dialog."]},
        {"id": 20, "title": "Eierskap", "question": "Hvordan utøves eierskap?",
         "scale": ["Nivå 1: Svekkes.", "Nivå 2: Begrenset.", "Nivå 3: Tydelig.", "Nivå 4: Aktivt.", "Nivå 5: Sterk kultur."]},
        {"id": 21, "title": "Periodisering", "question": "Hvordan justeres periodisering?",
         "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Store justeringer.", "Nivå 3: Regelmessig revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Fleksibel."]},
        {"id": 22, "title": "Realisme", "question": "Hvordan opprettholdes realisme?",
         "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset fokus.", "Nivå 3: Arbeid med å opprettholde.", "Nivå 4: Systematisk styrking.", "Nivå 5: Høy troverdighet."]},
        {"id": 23, "title": "Momentum", "question": "Hvordan brukes tidlig gevinstuttak?",
         "scale": ["Nivå 1: Ingen systematisk.", "Nivå 2: Enkelte suksesser motiverer.", "Nivå 3: Bevissthet på viktighet.", "Nivå 4: Strategisk bruk.", "Nivå 5: Systematisk bygget."]}
    ],
    "Realisert": [
        {"id": 1, "title": "Læringsdokumentasjon", "question": "Hvordan dokumenteres læring for fremtidig bruk?",
         "scale": ["Nivå 1: Ingen dokumentasjon.", "Nivå 2: Enkelte deles uformelt.", "Nivå 3: Systematisk dokumentasjon.", "Nivå 4: Deles aktivt.", "Nivå 5: Integrert i kunnskapsbase."]},
        {"id": 2, "title": "Strategisk bidrag", "question": "Hvordan bidro strategisk retning til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Fullt integrert."]},
        {"id": 3, "title": "Gevinstkart-bidrag", "question": "Hvordan bidro gevinstkartet til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Nyttig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Viktig.", "Nivå 5: Avgjørende."]},
        {"id": 4, "title": "KPI-bidrag", "question": "Hvordan bidro KPI-er til realisering?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Full integrasjon."]},
        {"id": 5, "title": "Avgrensning-troverdighet", "question": "Hvordan bidro avgrensning til troverdighet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til troverdighet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 6, "title": "Estimat-nøyaktighet", "question": "Hvordan bidro estimater til nøyaktighet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Nøyaktige for enkelte.", "Nivå 3: Nøyaktige for flere.", "Nivå 4: Høy nøyaktighet.", "Nivå 5: Svært nøyaktige."]},
        {"id": 7, "title": "Testing-kvalitet", "question": "Hvordan bidro hypotesetesting til kvalitet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til kvalitet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 8, "title": "Interessent-suksess", "question": "Hvordan bidro interessentengasjement til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drivkrefter for suksess."]},
        {"id": 9, "title": "Forutsetning-suksess", "question": "Hvordan bidro forutsetningshåndtering til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Suksessfaktor."]},
        {"id": 10, "title": "Kriterie-realisering", "question": "Hvordan bidro kriteriehåndtering til realisering?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket realisering."]},
        {"id": 11, "title": "Enighet-suksess", "question": "Hvordan bidro enighet til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 12, "title": "Disponering-verdi", "question": "Hvordan bidro disponering til verdiskapning?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til verdi.", "Nivå 4: Avgjørende.", "Nivå 5: Maksimerte verdi."]},
        {"id": 13, "title": "Måling-realisering", "question": "Hvordan bidro måling til realisering?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet realisering."]},
        {"id": 14, "title": "Risiko-robusthet", "question": "Hvordan bidro risikohåndtering til robusthet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til robusthet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 15, "title": "Balanse-bærekraft", "question": "Hvordan bidro balansevurdering til bærekraft?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til bærekraft.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 16, "title": "Plan-suksess", "question": "Hvordan bidro planen til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Suksessfaktor."]},
        {"id": 17, "title": "Operativ-suksess", "question": "Hvordan bidro planen som operativ handlingsplan?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet realisering."]},
        {"id": 18, "title": "Beredskap-realisering", "question": "Hvordan bidro endringsberedskap til realisering?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Høy mottaksevne drevet."]},
        {"id": 19, "title": "Kommunikasjon-suksess", "question": "Hvordan bidro kommunikasjon til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 20, "title": "Eierskap-suksess", "question": "Hvordan bidro eierskap til suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet suksess."]},
        {"id": 21, "title": "Periodisering-effektivitet", "question": "Hvordan bidro periodisering til effektivitet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til effektivitet.", "Nivå 4: Avgjørende.", "Nivå 5: Maksimerte effektivitet."]},
        {"id": 22, "title": "Realisme-troverdighet", "question": "Hvordan bidro realisme til troverdighet?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til troverdighet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket realisering."]},
        {"id": 23, "title": "Momentum-langsiktig", "question": "Hvordan bidro momentum til langsiktig suksess?",
         "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til momentum.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet langsiktig suksess."]}
    ]
}

# ============================================================================
# DATALAGRING
# ============================================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'rb') as f:
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
    with open(DATA_FILE, 'wb') as f:
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

.info-box {{ background: linear-gradient(135deg, #C4EFFF 0%, {COLORS['gray_light']} 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['primary_light']}; margin: 0.8rem 0; }}
.success-box {{ background: linear-gradient(135deg, #DDFAE2 0%, {COLORS['gray_light']} 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['success']}; margin: 0.8rem 0; }}
.warning-box {{ background: linear-gradient(135deg, rgba(255, 160, 64, 0.15) 0%, {COLORS['gray_light']} 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid {COLORS['warning']}; margin: 0.8rem 0; }}

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

def create_strength_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:20]}..." if len(item['title']) > 20 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['success'], text=[f"{s:.1f}" for s in scores], textposition='outside')])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score"), yaxis=dict(autorange="reversed"), height=max(250, len(items) * 35), margin=dict(l=200, r=50, t=20, b=40))
    return fig

def create_improvement_bar_chart(items, max_items=8):
    if not items:
        return None
    items = items[:max_items]
    labels = [f"{item['phase'][:4]}: {item['title'][:20]}..." if len(item['title']) > 20 else f"{item['phase'][:4]}: {item['title']}" for item in items]
    scores = [item['score'] for item in items]
    fig = go.Figure(data=[go.Bar(x=scores, y=labels, orientation='h', marker_color=COLORS['danger'], text=[f"{s:.1f}" for s in scores], textposition='outside')])
    fig.update_layout(xaxis=dict(range=[0, 5.5], title="Score"), yaxis=dict(autorange="reversed"), height=max(250, len(items) * 35), margin=dict(l=200, r=50, t=20, b=40))
    return fig

# ============================================================================
# RAPPORT-GENERERING
# ============================================================================
def generate_word_report(initiative, stats):
    """Generer Word-rapport"""
    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        # Tittel
        title = doc.add_heading('Modenhetsvurdering - Gevinstrealisering', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_paragraph('Bane NOR - Konsern økonomi og digital transformasjon')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        
        # Sammendrag
        doc.add_heading('Sammendrag', level=1)
        doc.add_paragraph(f"Endringsinitiativ: {initiative['name']}")
        doc.add_paragraph(f"Beskrivelse: {initiative.get('description', '-')}")
        doc.add_paragraph(f"Rapportdato: {datetime.now().strftime('%d.%m.%Y')}")
        doc.add_paragraph(f"Antall intervjuer: {stats['total_interviews']}")
        doc.add_paragraph(f"Samlet modenhet: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})")
        
        # Modenhet per fase
        if stats['phases']:
            doc.add_heading('Modenhet per fase', level=1)
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Fase'
            hdr_cells[1].text = 'Score'
            for phase, data in stats['phases'].items():
                row_cells = table.add_row().cells
                row_cells[0].text = phase
                row_cells[1].text = f"{data['avg']:.2f}"
        
        # Styrkeområder
        if stats['high_maturity']:
            doc.add_heading('Styrkeområder (score >= 4)', level=1)
            for item in stats['high_maturity'][:10]:
                doc.add_paragraph(f"• [{item['phase']}] {item['title']}: {item['score']:.2f}", style='List Bullet')
        
        # Forbedringsområder
        if stats['low_maturity']:
            doc.add_heading('Forbedringsområder (score < 3)', level=1)
            for item in stats['low_maturity'][:10]:
                doc.add_paragraph(f"• [{item['phase']}] {item['title']}: {item['score']:.2f}", style='List Bullet')
        
        # Parameterresultater
        if stats['parameters']:
            doc.add_heading('Resultater per parameter', level=1)
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Parameter'
            hdr_cells[1].text = 'Score'
            for param_name, param_data in stats['parameters'].items():
                row_cells = table.add_row().cells
                row_cells[0].text = param_name
                row_cells[1].text = f"{param_data['avg']:.2f}"
        
        # Lagre
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
        
    except ImportError:
        return None

def generate_pdf_report(initiative, stats):
    """Generer PDF-rapport via HTML"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Source Sans Pro', Arial, sans-serif; margin: 40px; color: #172141; }}
            h1 {{ color: #0053A6; text-align: center; border-bottom: 3px solid #64C8FA; padding-bottom: 10px; }}
            h2 {{ color: #172141; margin-top: 30px; border-left: 4px solid #0053A6; padding-left: 10px; }}
            .summary {{ background: #F2FAFD; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ border: 1px solid #E8E8E8; padding: 10px; text-align: left; }}
            th {{ background: #0053A6; color: white; }}
            .strength {{ color: #35DE6D; }}
            .improvement {{ color: #FF6B6B; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>Modenhetsvurdering - Gevinstrealisering</h1>
        <p style="text-align: center; color: #0053A6;">Bane NOR - Konsern økonomi og digital transformasjon</p>
        
        <div class="summary">
            <h2>Sammendrag</h2>
            <p><strong>Endringsinitiativ:</strong> {initiative['name']}</p>
            <p><strong>Beskrivelse:</strong> {initiative.get('description', '-')}</p>
            <p><strong>Rapportdato:</strong> {datetime.now().strftime('%d.%m.%Y')}</p>
            <p><strong>Antall intervjuer:</strong> {stats['total_interviews']}</p>
            <p><strong>Samlet modenhet:</strong> {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})</p>
        </div>
        
        <h2>Modenhet per fase</h2>
        <table>
            <tr><th>Fase</th><th>Score</th></tr>
            {''.join(f"<tr><td>{phase}</td><td>{data['avg']:.2f}</td></tr>" for phase, data in stats['phases'].items())}
        </table>
        
        <h2>Styrkeområder (score >= 4)</h2>
        <ul>
            {''.join(f"<li class='strength'>[{item['phase']}] {item['title']}: {item['score']:.2f}</li>" for item in stats['high_maturity'][:10])}
        </ul>
        
        <h2>Forbedringsområder (score < 3)</h2>
        <ul>
            {''.join(f"<li class='improvement'>[{item['phase']}] {item['title']}: {item['score']:.2f}</li>" for item in stats['low_maturity'][:10])}
        </ul>
        
        <h2>Resultater per parameter</h2>
        <table>
            <tr><th>Parameter</th><th>Score</th></tr>
            {''.join(f"<tr><td>{name}</td><td>{data['avg']:.2f}</td></tr>" for name, data in stats['parameters'].items())}
        </table>
        
        <div class="footer">
            <p>Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR - Konsern økonomi og digital transformasjon</p>
        </div>
    </body>
    </html>
    """
    return html_content

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def main():
    data = get_data()
    
    # Header
    st.markdown('<h1 class="main-header">Modenhetsvurdering</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">I samarbeid med Konsern økonomi og digital transformasjon</p>', unsafe_allow_html=True)
    
    # Navigasjon
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Om vurderingen", "Endringsinitiativ", "Intervju", "Resultater", "Rapport"])
    
    # TAB 1: OM VURDERINGEN
    with tab1:
        st.markdown(HENSIKT_TEKST)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Tilgjengelige roller")
            for role_name, role_data in ROLES.items():
                st.markdown(f"**{role_name}**")
                st.caption(role_data['description'])
        with col2:
            st.markdown("### Tilgjengelige parametere")
            for param_name, param_data in PARAMETERS.items():
                st.markdown(f"**{param_name}**")
                st.caption(param_data['description'])
    
    # TAB 2: ENDRINGSINITIATIV
    with tab2:
        st.markdown("## Endringsinitiativ og gevinster")
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### Nytt endringsinitiativ")
            with st.form("new_initiative"):
                init_name = st.text_input("Navn", placeholder="F.eks. ERTMS Østlandet")
                init_desc = st.text_area("Beskrivelse", height=80)
                if st.form_submit_button("Opprett", use_container_width=True):
                    if init_name:
                        init_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        data['initiatives'][init_id] = {'name': init_name, 'description': init_desc, 'created': datetime.now().isoformat(), 'benefits': {}, 'interviews': {}}
                        persist_data()
                        st.success(f"'{init_name}' opprettet!")
                        st.rerun()
        
        with col1:
            st.markdown("### Mine endringsinitiativ")
            if not data['initiatives']:
                st.info("Ingen endringsinitiativ ennå. Opprett et nytt for å starte.")
            else:
                for init_id, initiative in data['initiatives'].items():
                    num_interviews = len(initiative.get('interviews', {}))
                    num_benefits = len(initiative.get('benefits', {}))
                    with st.expander(f"{initiative['name']} ({num_benefits} gevinster, {num_interviews} intervjuer)"):
                        st.write(f"**Beskrivelse:** {initiative.get('description', 'Ingen')}")
                        st.markdown("#### Gevinster")
                        with st.form(f"add_benefit_{init_id}"):
                            new_benefit = st.text_input("Ny gevinst", key=f"ben_{init_id}")
                            if st.form_submit_button("Legg til"):
                                if new_benefit:
                                    if 'benefits' not in initiative:
                                        initiative['benefits'] = {}
                                    initiative['benefits'][datetime.now().strftime("%Y%m%d%H%M%S%f")] = {'name': new_benefit, 'created': datetime.now().isoformat()}
                                    persist_data()
                                    st.rerun()
                        for ben_id, benefit in initiative.get('benefits', {}).items():
                            col_a, col_b = st.columns([4, 1])
                            col_a.write(f"• {benefit['name']}")
                            if col_b.button("Slett", key=f"del_ben_{ben_id}"):
                                del initiative['benefits'][ben_id]
                                persist_data()
                                st.rerun()
                        st.markdown("---")
                        if st.button("Slett initiativ", key=f"del_{init_id}"):
                            del data['initiatives'][init_id]
                            persist_data()
                            st.rerun()
    
    # TAB 3: INTERVJU
    with tab3:
        st.markdown("## Gjennomfør intervju")
        if not data['initiatives']:
            st.warning("Opprett et endringsinitiativ først")
        else:
            init_options = {p['name']: pid for pid, p in data['initiatives'].items()}
            selected_init_name = st.selectbox("Velg endringsinitiativ", options=list(init_options.keys()))
            selected_init_id = init_options[selected_init_name]
            initiative = data['initiatives'][selected_init_id]
            
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
                    focus_mode = st.radio("Fokusmodus", options=["Rollebasert", "Parameterbasert", "Alle spørsmål"], horizontal=True)
                    
                    selected_role = None
                    selected_params = []
                    recommended = []
                    
                    if focus_mode == "Rollebasert":
                        selected_role = st.selectbox("Rolle", options=list(ROLES.keys()))
                        recommended = get_recommended_questions("role", selected_role, selected_phase)
                        st.caption(ROLES[selected_role]['description'])
                        st.success(f"{len(recommended)} anbefalte spørsmål. Alle 23 tilgjengelige.")
                    elif focus_mode == "Parameterbasert":
                        selected_params = st.multiselect("Parametere", options=list(PARAMETERS.keys()), default=list(PARAMETERS.keys())[:2])
                        recommended = get_recommended_questions("parameter", selected_params, selected_phase)
                        st.success(f"{len(recommended)} anbefalte spørsmål. Alle 23 tilgjengelige.")
                    
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
                                st.session_state['active_interview'] = {'init_id': selected_init_id, 'interview_id': interview_id}
                                st.rerun()
                
                with col2:
                    st.markdown("### Fortsett eksisterende")
                    if initiative['interviews']:
                        interview_options = {f"{i['info']['interviewee']} - {i['info'].get('benefit_name', 'Generelt')} ({i['info'].get('phase', '?')})": iid for iid, i in initiative['interviews'].items()}
                        selected_interview = st.selectbox("Velg intervju", options=list(interview_options.keys()))
                        if st.button("Fortsett", use_container_width=True):
                            st.session_state['active_interview'] = {'init_id': selected_init_id, 'interview_id': interview_options[selected_interview]}
                            st.rerun()
            
            else:
                active = st.session_state['active_interview']
                if active['init_id'] in data['initiatives']:
                    initiative = data['initiatives'][active['init_id']]
                    if active['interview_id'] in initiative['interviews']:
                        interview = initiative['interviews'][active['interview_id']]
                        phase = interview['info'].get('phase', 'Planlegging')
                        recommended = interview.get('recommended_questions', [])
                        
                        st.markdown(f"### Intervju: {interview['info']['interviewee']}")
                        st.caption(f"Gevinst: {interview['info'].get('benefit_name', 'Generelt')} | Fase: {phase} | Stilling: {interview['info']['role']}")
                        
                        if phase not in interview['responses']:
                            interview['responses'][phase] = {}
                        
                        answered = sum(1 for q_id in range(1, 24) if interview['responses'][phase].get(str(q_id), {}).get('score', 0) > 0)
                        st.progress(answered / 23)
                        st.caption(f"Besvart: {answered} av 23")
                        
                        questions = questions_data[phase]
                        recommended_qs = [q for q in questions if q['id'] in recommended]
                        other_qs = [q for q in questions if q['id'] not in recommended]
                        
                        if recommended_qs:
                            st.markdown("### Anbefalte spørsmål")
                            for q in recommended_qs:
                                q_id_str = str(q['id'])
                                if q_id_str not in interview['responses'][phase]:
                                    interview['responses'][phase][q_id_str] = {'score': 0, 'notes': ''}
                                resp = interview['responses'][phase][q_id_str]
                                status = "✓" if resp['score'] > 0 else "○"
                                with st.expander(f"{status} {q['id']}. {q['title']}" + (f" - Nivå {resp['score']}" if resp['score'] > 0 else ""), expanded=(resp['score'] == 0)):
                                    st.markdown(f"**{q['question']}**")
                                    for level in q['scale']:
                                        st.write(f"- {level}")
                                    new_score = st.radio("Nivå:", options=[0,1,2,3,4,5], index=resp['score'], key=f"s_{phase}_{q['id']}", horizontal=True, format_func=lambda x: "Ikke vurdert" if x == 0 else f"Nivå {x}")
                                    new_notes = st.text_area("Notater:", value=resp['notes'], key=f"n_{phase}_{q['id']}", height=80)
                                    if st.button("Lagre", key=f"save_{phase}_{q['id']}"):
                                        interview['responses'][phase][q_id_str] = {'score': new_score, 'notes': new_notes}
                                        persist_data()
                                        st.rerun()
                        
                        if other_qs:
                            st.markdown("### Andre spørsmål")
                            for q in other_qs:
                                q_id_str = str(q['id'])
                                if q_id_str not in interview['responses'][phase]:
                                    interview['responses'][phase][q_id_str] = {'score': 0, 'notes': ''}
                                resp = interview['responses'][phase][q_id_str]
                                status = "✓" if resp['score'] > 0 else "○"
                                with st.expander(f"{status} {q['id']}. {q['title']}" + (f" - Nivå {resp['score']}" if resp['score'] > 0 else ""), expanded=False):
                                    st.markdown(f"**{q['question']}**")
                                    for level in q['scale']:
                                        st.write(f"- {level}")
                                    new_score = st.radio("Nivå:", options=[0,1,2,3,4,5], index=resp['score'], key=f"s_{phase}_{q['id']}", horizontal=True, format_func=lambda x: "Ikke vurdert" if x == 0 else f"Nivå {x}")
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
        if not data['initiatives']:
            st.warning("Ingen endringsinitiativ å vise")
        else:
            init_options = {p['name']: pid for pid, p in data['initiatives'].items()}
            selected_init_name = st.selectbox("Velg endringsinitiativ", options=list(init_options.keys()), key="res_init")
            selected_init_id = init_options[selected_init_name]
            initiative = data['initiatives'][selected_init_id]
            
            benefit_filter_options = {"Alle gevinster": "all"}
            for ben_id, ben in initiative.get('benefits', {}).items():
                benefit_filter_options[ben['name']] = ben_id
            benefit_filter_name = st.selectbox("Filtrer på gevinst:", options=list(benefit_filter_options.keys()))
            benefit_filter = benefit_filter_options[benefit_filter_name]
            
            stats = calculate_stats(initiative, benefit_filter if benefit_filter != "all" else None)
            
            if not stats or stats['total_interviews'] == 0:
                st.info("Ingen intervjuer gjennomført ennå")
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
                    st.markdown("### Styrkeområder")
                    if stats['high_maturity']:
                        fig = create_strength_bar_chart(stats['high_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        for item in stats['high_maturity'][:5]:
                            st.markdown(f'<div class="strength-card">[{item["phase"]}] {item["title"]}: {item["score"]:.2f}</div>', unsafe_allow_html=True)
                    else:
                        st.info("Ingen styrkeområder identifisert")
                with col2:
                    st.markdown("### Forbedringsområder")
                    if stats['low_maturity']:
                        fig = create_improvement_bar_chart(stats['low_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        for item in stats['low_maturity'][:5]:
                            st.markdown(f'<div class="improvement-card">[{item["phase"]}] {item["title"]}: {item["score"]:.2f}</div>', unsafe_allow_html=True)
                    else:
                        st.success("Ingen kritiske forbedringsområder!")
    
    # TAB 5: RAPPORT
    with tab5:
        st.markdown("## Generer rapport")
        if not data['initiatives']:
            st.warning("Ingen endringsinitiativ")
        else:
            init_options = {p['name']: pid for pid, p in data['initiatives'].items()}
            selected_init_name = st.selectbox("Velg endringsinitiativ", options=list(init_options.keys()), key="rep_init")
            selected_init_id = init_options[selected_init_name]
            initiative = data['initiatives'][selected_init_id]
            stats = calculate_stats(initiative)
            
            if not stats or stats['total_interviews'] == 0:
                st.info("Gjennomfør minst ett intervju først")
            else:
                st.markdown("### Eksportformat")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### CSV")
                    csv_data = []
                    for phase in stats['questions']:
                        for q_id, q_data in stats['questions'][phase].items():
                            csv_data.append({'Fase': phase, 'SpørsmålID': q_id, 'Tittel': q_data['title'], 'Gjennomsnitt': round(q_data['avg'], 2), 'AntallSvar': q_data['count']})
                    csv_df = pd.DataFrame(csv_data)
                    st.download_button("Last ned CSV", data=csv_df.to_csv(index=False, sep=';'), file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
                
                with col2:
                    st.markdown("#### Word")
                    word_buffer = generate_word_report(initiative, stats)
                    if word_buffer:
                        st.download_button("Last ned Word", data=word_buffer, file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                    else:
                        st.warning("Installer python-docx")
                
                with col3:
                    st.markdown("#### PDF (HTML)")
                    html_content = generate_pdf_report(initiative, stats)
                    st.download_button("Last ned HTML/PDF", data=html_content, file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html", use_container_width=True)
                    st.caption("Åpne i nettleser og skriv ut som PDF")
                
                st.markdown("---")
                st.markdown("### Intervjuoversikt")
                interview_data = []
                for iid, interview in initiative['interviews'].items():
                    info = interview['info']
                    total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                    total_score = sum(resp['score'] for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                    avg = total_score / total_answered if total_answered > 0 else 0
                    interview_data.append({'Dato': info.get('date', ''), 'Intervjuobjekt': info.get('interviewee', ''), 'Gevinst': info.get('benefit_name', 'Generelt'), 'Fase': info.get('phase', ''), 'Besvarte': total_answered, 'Snitt': round(avg, 2) if avg > 0 else '-'})
                if interview_data:
                    st.dataframe(pd.DataFrame(interview_data), use_container_width=True)
    
    st.markdown("---")
    st.markdown('<p style="text-align:center;color:#666;font-size:0.8rem;">Bane NOR - Konsern økonomi og digital transformasjon</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
