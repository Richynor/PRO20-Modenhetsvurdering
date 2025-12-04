"""
MODENHETSVURDERING - GEVINSTREALISERING
Gjennomføres i samarbeid med konsern okonomi og digital transformasjon

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
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "modenhet_data_v5.pkl"

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
    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Modenhetsvurdering - {initiative['name']}</title>
    <style>
        body {{ font-family: 'Source Sans Pro', sans-serif; padding: 40px; max-width: 1000px; margin: 0 auto; color: #172141; line-height: 1.6; }}
        h1 {{ color: #172141; text-align: center; }}
        h2 {{ color: #0053A6; border-bottom: 2px solid #64C8FA; padding-bottom: 5px; }}
        h3 {{ color: #0053A6; }}
        .subtitle {{ text-align: center; color: #0053A6; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #0053A6; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #E8E8E8; }}
        tr:nth-child(even) {{ background: #F2FAFD; }}
        .item {{ padding: 8px 12px; margin: 5px 0; border-radius: 6px; }}
        .item-strength {{ background: #DDFAE2; border-left: 4px solid #35DE6D; }}
        .item-improvement {{ background: rgba(255, 107, 107, 0.15); border-left: 4px solid #FF6B6B; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E8E8E8; color: #666; }}
    </style>
</head>
<body>
    <h1>Modenhetsvurdering - Gevinstrealisering</h1>
    <p class="subtitle">Bane NOR - Konsern okonomi og digital transformasjon</p>
    
    <h2>1. Sammendrag</h2>
    <table>
        <tr><td><strong>Endringsinitiativ</strong></td><td>{initiative['name']}</td></tr>
        <tr><td><strong>Beskrivelse</strong></td><td>{initiative.get('description', '-')}</td></tr>
        <tr><td><strong>Rapportdato</strong></td><td>{datetime.now().strftime('%d.%m.%Y')}</td></tr>
        <tr><td><strong>Antall intervjuer</strong></td><td>{stats['total_interviews']}</td></tr>
        <tr><td><strong>Samlet modenhet</strong></td><td><strong>{stats['overall_avg']:.2f}</strong> ({get_score_text(stats['overall_avg'])})</td></tr>
    </table>
"""
    
    if stats['phases']:
        html += "<h2>2. Modenhet per fase</h2><table><tr><th>Fase</th><th>Gjennomsnitt</th><th>Min</th><th>Maks</th></tr>"
        for phase, data in stats['phases'].items():
            html += f"<tr><td>{phase}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['min']:.2f}</td><td>{data['max']:.2f}</td></tr>"
        html += "</table>"
    
    if stats['high_maturity']:
        html += "<h2>3. Styrkeomrader (score >= 4)</h2>"
        for item in stats['high_maturity'][:15]:
            html += f'<div class="item item-strength"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
    
    if stats['low_maturity']:
        html += "<h2>4. Forbedringsomrader (score < 3)</h2>"
        for item in stats['low_maturity'][:15]:
            html += f'<div class="item item-improvement"><strong>[{item["phase"]}]</strong> {item["title"]}: <strong>{item["score"]:.2f}</strong></div>'
    
    if stats['parameters']:
        html += "<h2>5. Resultater per parameter</h2><table><tr><th>Parameter</th><th>Score</th><th>Beskrivelse</th></tr>"
        for name, data in stats['parameters'].items():
            html += f"<tr><td>{name}</td><td><strong>{data['avg']:.2f}</strong></td><td>{data['description']}</td></tr>"
        html += "</table>"
    
    html += "<h2>6. Detaljerte resultater per sporsmal</h2>"
    for phase in PHASES:
        if phase in stats['questions'] and stats['questions'][phase]:
            html += f"<h3>{phase}</h3><table><tr><th>ID</th><th>Sporsmal</th><th>Score</th><th>Antall</th></tr>"
            for q_id, q_data in sorted(stats['questions'][phase].items()):
                html += f"<tr><td>{q_id}</td><td>{q_data['title']}</td><td><strong>{q_data['avg']:.2f}</strong></td><td>{q_data['count']}</td></tr>"
            html += "</table>"
    
    html += "<h2>7. Intervjuoversikt (anonymisert)</h2><table><tr><th>Deltaker</th><th>Dato</th><th>Gevinst</th><th>Fase</th><th>Snitt</th></tr>"
    for idx, interview in enumerate(initiative.get('interviews', {}).values()):
        info = interview.get('info', {})
        total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
        avg = total_score / total_answered if total_answered > 0 else 0
        anon_name = get_anonymous_name(idx)
        date_str = info.get('date', '-')
        benefit_name = info.get('benefit_name', 'Generelt')
        phase_str = info.get('phase', '-')
        avg_str = f"{avg:.2f}" if avg > 0 else "-"
        html += f"<tr><td>{anon_name}</td><td>{date_str}</td><td>{benefit_name}</td><td>{phase_str}</td><td>{avg_str}</td></tr>"
    html += "</table>"
    
    html += f'<div class="footer">Generert {datetime.now().strftime("%d.%m.%Y %H:%M")} | Bane NOR</div></body></html>'
    return html

# ============================================================================
# RAPPORT-GENERERING - TXT
# ============================================================================
def generate_txt_report(initiative, stats):
    lines = []
    lines.append("=" * 60)
    lines.append("MODENHETSVURDERING - GEVINSTREALISERING")
    lines.append("Bane NOR - Konsern okonomi og digital transformasjon")
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
    lines.append("=" * 60)
    lines.append(f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR")
    lines.append("=" * 60)
    
    return "\n".join(lines)

# ============================================================================
# RAPPORT-GENERERING - PDF (med FPDF)
# ============================================================================
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
        pdf.cell(0, 7, f"Endringsinitiativ: {initiative['name']}", ln=True)
        pdf.cell(0, 7, f"Rapportdato: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        pdf.cell(0, 7, f"Antall intervjuer: {stats['total_interviews']}", ln=True)
        pdf.cell(0, 7, f"Samlet modenhet: {stats['overall_avg']:.2f} ({get_score_text(stats['overall_avg'])})", ln=True)
        pdf.ln(5)
        
        # Faser
        if stats['phases']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '2. Modenhet per fase', ln=True)
            pdf.set_font('Helvetica', '', 11)
            for phase, data in stats['phases'].items():
                pdf.cell(0, 7, f"  {phase}: {data['avg']:.2f}", ln=True)
            pdf.ln(5)
        
        # Styrker
        if stats['high_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '3. Styrkeomrader', ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['high_maturity'][:8]:
                text = f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}"
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)
        
        # Forbedring
        if stats['low_maturity']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '4. Forbedringsomrader', ln=True)
            pdf.set_font('Helvetica', '', 10)
            for item in stats['low_maturity'][:8]:
                text = f"  [{item['phase'][:4]}] {item['title'][:40]}: {item['score']:.2f}"
                pdf.cell(0, 6, text, ln=True)
            pdf.ln(5)
        
        # Intervjuoversikt (anonymisert)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '5. Intervjuoversikt (anonymisert)', ln=True)
        pdf.set_font('Helvetica', '', 10)
        for idx, interview in enumerate(initiative.get('interviews', {}).values()):
            info = interview.get('info', {})
            total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
            total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
            avg = total_score / total_answered if total_answered > 0 else 0
            anon_name = get_anonymous_name(idx)
            avg_str = f"{avg:.2f}" if avg > 0 else "-"
            pdf.cell(0, 6, f"  {anon_name} | {info.get('phase', '-')} | Snitt: {avg_str}", ln=True)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 10, f"Generert {datetime.now().strftime('%d.%m.%Y %H:%M')} | Bane NOR", ln=True, align='C')
        
        # Return as bytes
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        return pdf_output
    except Exception as e:
        return None

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def main():
    data = get_data()
    
    st.markdown(f'''
    <div style="text-align:center;margin-bottom:1.5rem;">
        <h1 style="margin:0;color:{COLORS['primary_dark']};font-size:2rem;font-weight:700;">🚂 Modenhetsvurdering 🚂</h1>
        <p style="color:{COLORS['primary']};font-size:0.95rem;margin-top:0.3rem;">Bane NOR - Konsern okonomi og digital transformasjon</p>
    </div>
    ''', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Om vurderingen", "Endringsinitiativ", "Intervju", "Resultater", "Rapport"])
    
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
    
    # TAB 2: ENDRINGSINITIATIV
    with tab2:
        st.markdown("## Endringsinitiativ og gevinster")
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### Nytt endringsinitiativ")
            with st.form("new_initiative"):
                init_name = st.text_input("Navn", placeholder="F.eks. ERTMS Ostlandet")
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
                st.info("Ingen endringsinitiativ enda. Opprett et nytt for a starte.")
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
                            col_a.write(f"- {benefit['name']}")
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
        st.markdown("## Gjennomfor intervju")
        if not data['initiatives']:
            st.warning("Opprett et endringsinitiativ forst")
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
        if not data['initiatives']:
            st.warning("Ingen endringsinitiativ a vise")
        else:
            init_options = {p['name']: pid for pid, p in data['initiatives'].items()}
            selected_init_name = st.selectbox("Velg endringsinitiativ", options=list(init_options.keys()), key="res_init")
            selected_init_id = init_options[selected_init_name]
            initiative = data['initiatives'][selected_init_id]
            
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
                        fig = create_strength_bar_chart(stats['high_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        for item in stats['high_maturity'][:5]:
                            st.markdown(f'<div class="strength-card">[{item["phase"]}] {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                    else:
                        st.info("Ingen styrkeomrader identifisert")
                with col2:
                    st.markdown("### Forbedringsomrader")
                    if stats['low_maturity']:
                        fig = create_improvement_bar_chart(stats['low_maturity'])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        for item in stats['low_maturity'][:5]:
                            st.markdown(f'<div class="improvement-card">[{item["phase"]}] {item["title"]}: <strong>{item["score"]:.2f}</strong></div>', unsafe_allow_html=True)
                    else:
                        st.success("Ingen kritiske forbedringsomrader!")
    
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
                for iid, interview in initiative['interviews'].items():
                    info = interview.get('info', {})
                    total_answered = sum(1 for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                    total_score = sum(resp.get('score', 0) for phase in interview.get('responses', {}).values() for resp in phase.values() if resp.get('score', 0) > 0)
                    avg = total_score / total_answered if total_answered > 0 else 0
                    interview_data.append({'Dato': info.get('date', ''), 'Intervjuobjekt': info.get('interviewee', ''), 'Gevinst': info.get('benefit_name', 'Generelt'), 'Fase': info.get('phase', ''), 'Besvarte': total_answered, 'Snitt': round(avg, 2) if avg > 0 else '-'})
                if interview_data:
                    st.dataframe(pd.DataFrame(interview_data), use_container_width=True)
    
    st.markdown("---")
    st.markdown(f'<div style="text-align:center;color:#666;font-size:0.85rem;padding:10px 0;">Bane NOR - Konsern okonomi og digital transformasjon </div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
