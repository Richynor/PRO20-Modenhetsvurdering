"""
MODENHETSVURDERING - GEVINSTREALISERING
Bane NOR - i samarbeid med digital transformasjon og konsern økonomi

Versjon: 4A - ROLLEBASERT SPØRSMÅLSUTVALG
Velg personens rolle → får automatisk relevante spørsmål
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import pickle
import os
import subprocess
import tempfile

# ============================================================================
# KONFIGURASJON
# ============================================================================
st.set_page_config(
    page_title="Modenhetsvurdering - Bane NOR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "modenhet_data.pkl"

# ============================================================================
# ROLLEDEFINISJONER MED SPØRSMÅLSUTVALG
# ============================================================================
ROLES = {
    "Prosjektleder / Programleder": {
        "description": "Ansvar for overordnet gjennomføring og leveranser",
        "icon": "👔",
        "phases": ["Planlegging", "Gjennomføring"],
        "questions": {
            "Planlegging": [2, 3, 4, 8, 16, 17, 19, 20, 21, 22],
            "Gjennomføring": [2, 6, 8, 14, 16, 19, 20, 22]
        }
    },
    "Gevinsteier": {
        "description": "Ansvar for at gevinster realiseres i linjen",
        "icon": "🎯",
        "phases": ["Realisering", "Realisert"],
        "questions": {
            "Planlegging": [9, 11, 12, 20],
            "Realisering": [1, 2, 6, 8, 9, 12, 13, 16, 17, 20],
            "Realisert": [1, 6, 8, 12, 13, 20]
        }
    },
    "Linjeleder / Mottaker": {
        "description": "Skal ta imot endringer og realisere gevinster i drift",
        "icon": "🏢",
        "phases": ["Realisering"],
        "questions": {
            "Planlegging": [18, 19],
            "Gjennomføring": [18, 19],
            "Realisering": [8, 9, 13, 17, 18, 19, 20]
        }
    },
    "Business Case-ansvarlig": {
        "description": "Utarbeidet gevinstgrunnlag og estimater",
        "icon": "📊",
        "phases": ["Planlegging"],
        "questions": {
            "Planlegging": [1, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        }
    },
    "Sponsor / Styringsgruppe": {
        "description": "Overordnet ansvar og beslutninger",
        "icon": "⭐",
        "phases": ["Planlegging", "Realisert"],
        "questions": {
            "Planlegging": [2, 4, 20, 21, 22],
            "Realisert": [2, 4, 16, 20]
        }
    },
    "Controller / Økonomi": {
        "description": "Oppfølging av økonomiske gevinster",
        "icon": "💰",
        "phases": ["Gjennomføring", "Realisering"],
        "questions": {
            "Planlegging": [6, 11, 12, 21],
            "Gjennomføring": [6, 12, 13],
            "Realisering": [6, 12, 13, 21]
        }
    },
    "Endringsleder": {
        "description": "Ansvar for endringsledelse og kommunikasjon",
        "icon": "🔄",
        "phases": ["Gjennomføring", "Realisering"],
        "questions": {
            "Planlegging": [8, 18, 19, 23],
            "Gjennomføring": [8, 18, 19, 22, 23],
            "Realisering": [8, 18, 19, 22, 23]
        }
    },
    "Manuelt utvalg": {
        "description": "Velg spørsmål selv",
        "icon": "✏️",
        "phases": [],
        "questions": {}
    },
    "Alle spørsmål": {
        "description": "Vis alle 23 spørsmål per fase",
        "icon": "📋",
        "phases": ["Planlegging", "Gjennomføring", "Realisering", "Realisert"],
        "questions": "ALL"
    }
}

# ============================================================================
# HENSIKT OG FORMÅL TEKST
# ============================================================================
HENSIKT_TEKST = """
### Hensikt
Modenhetsvurderingen har som formål å synliggjøre gode erfaringer og identifisere forbedringsområder i vårt arbeid med gevinster. Vi ønsker å lære av hverandre, dele beste praksis og hjelpe initiativer til å lykkes bedre med å skape og realisere gevinster. Gjennom denne tilnærmingen bygger vi en kultur for kontinuerlig læring og forbedring, der vi blir stadig dyktigere til å hente ut effekter og synliggjøre den verdiskapningen vi bidrar med.

Et sentralt fokusområde er å sikre at gevinstene vi arbeider med er konkrete og realitetsorienterte. Dette innebærer at nullpunkter og estimater er testet og validert, at hypoteser er prøvd mot representative caser og faktiske arbeidsforhold, og at forutsetningene for gevinstuttak er realistiske og forankret. Målet er at gevinstene vi planlegger for faktisk kan hentes ut i praksis – ikke at de forblir hypotetiske tall i et planverk.

### Hvem inviteres?
Vi ønsker å intervjue alle som har vært eller er involvert i gevinstarbeidet – enten du har bidratt til utarbeidelse av business case, gevinstkart, gevinstrealiseringsplaner eller målinger, eller du har hatt ansvar for oppfølging og realisering.

### Hva vurderes?
Intervjuene dekker hele gevinstlivssyklusen – fra planlegging og gjennomføring til realisering og evaluering. Vi ser på elementer som strategisk retning, gevinstkart, nullpunkter og estimater, hypotesetesting, interessentengasjement, eierskap og ansvar, kommunikasjon, risikohåndtering og læring.
"""

# ============================================================================
# PARAMETERE (KATEGORIER)
# ============================================================================
PARAMETERS = {
    "Strategisk forankring": {
        "description": "Strategisk retning, kobling til mål og KPI-er",
        "questions": {
            "Planlegging": [2, 4],
            "Gjennomføring": [2, 4],
            "Realisering": [2, 4],
            "Realisert": [2, 4]
        }
    },
    "Gevinstkart og visualisering": {
        "description": "Gevinstkart, sammenhenger mellom tiltak og effekter",
        "questions": {
            "Planlegging": [3],
            "Gjennomføring": [3],
            "Realisering": [3],
            "Realisert": [3]
        }
    },
    "Nullpunkter og estimater": {
        "description": "Kvalitet på nullpunkter, estimater og datagrunnlag",
        "questions": {
            "Planlegging": [6, 7, 11],
            "Gjennomføring": [6, 7, 11],
            "Realisering": [6, 7, 11],
            "Realisert": [6, 7, 11]
        }
    },
    "Interessenter og forankring": {
        "description": "Interessentengasjement, kommunikasjon og forankring",
        "questions": {
            "Planlegging": [8, 19],
            "Gjennomføring": [8, 19],
            "Realisering": [8, 19],
            "Realisert": [8, 19]
        }
    },
    "Eierskap og ansvar": {
        "description": "Roller, ansvar og eierskap for gevinstuttak",
        "questions": {
            "Planlegging": [20],
            "Gjennomføring": [20],
            "Realisering": [20],
            "Realisert": [20]
        }
    },
    "Forutsetninger og risiko": {
        "description": "Gevinstforutsetninger, risiko og ulemper",
        "questions": {
            "Planlegging": [9, 10, 14, 15],
            "Gjennomføring": [9, 10, 14, 15],
            "Realisering": [9, 10, 14, 15],
            "Realisert": [9, 10, 14, 15]
        }
    },
    "Gevinstrealiseringsplan": {
        "description": "Plan som operativt styringsverktøy",
        "questions": {
            "Planlegging": [16, 17],
            "Gjennomføring": [16, 17],
            "Realisering": [16, 17],
            "Realisert": [16, 17]
        }
    },
    "Effektivitet og produktivitet": {
        "description": "Måling, disponering og bærekraft",
        "questions": {
            "Planlegging": [12, 13],
            "Gjennomføring": [12, 13],
            "Realisering": [12, 13],
            "Realisert": [12, 13]
        }
    },
    "Læring og forbedring": {
        "description": "Bruk av tidligere erfaringer og kontinuerlig læring",
        "questions": {
            "Planlegging": [1],
            "Gjennomføring": [1],
            "Realisering": [1],
            "Realisert": [1]
        }
    },
    "Momentum og tidlig gevinstuttak": {
        "description": "Bygge momentum gjennom tidlig gevinstrealisering",
        "questions": {
            "Planlegging": [23],
            "Gjennomføring": [23],
            "Realisering": [23],
            "Realisert": [23]
        }
    }
}

# ============================================================================
# KOMPLETT SPØRSMÅLSSETT
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
            "title": "Prinsipielle og vilkårsmessige kriterier",
            "question": "Er forutsetninger og kriterier som påvirker gevinstene tydelig definert og dokumentert?",
            "scale": [
                "Nivå 1: Ingen kriterier dokumentert.",
                "Nivå 2: Kriterier er beskrevet uformelt.",
                "Nivå 3: Kriterier dokumentert i deler av planverket.",
                "Nivå 4: Vesentlige kriterier er analysert og håndtert i gevinstrealiseringsplanen.",
                "Nivå 5: Kriterier overvåkes, følges opp og inngår i risikostyringen."
            ]
        },
        {
            "id": 11,
            "title": "Enighet om nullpunkter/estimater",
            "question": "Er det oppnådd enighet blant nøkkelinteressenter om nullpunkter og estimater?",
            "scale": [
                "Nivå 1: Ingen enighet eller dokumentert praksis.",
                "Nivå 2: Delvis enighet, men ikke formalisert.",
                "Nivå 3: Enighet for hovedestimater, men med reservasjoner.",
                "Nivå 4: Full enighet dokumentert og forankret.",
                "Nivå 5: Kontinuerlig dialog og justering av estimater med interessentene."
            ]
        },
        {
            "id": 12,
            "title": "Disponering av kostnads- og tidsbesparelser",
            "question": "Hvordan er kostnads- og tidsbesparelser planlagt disponert mellom prissatte og ikke-prissatte gevinster?",
            "scale": [
                "Nivå 1: Ingen plan for disponering eller måling av besparelser.",
                "Nivå 2: Delvis oversikt, men ikke dokumentert eller fulgt opp.",
                "Nivå 3: Plan finnes for enkelte områder, men uten systematikk.",
                "Nivå 4: Disponering og effekter dokumentert og målt.",
                "Nivå 5: Frigjorte ressurser disponeres strategisk og måles som del av gevinstrealiseringen."
            ]
        },
        {
            "id": 13,
            "title": "Måling av effektivitet og produktivitet",
            "question": "Hvordan måles økt effektivitet og produktivitet som følge av besparelser?",
            "scale": [
                "Nivå 1: Ingen måling av effektivitet eller produktivitet.",
                "Nivå 2: Enkelte målinger, men ikke systematisk.",
                "Nivå 3: Måling for enkelte gevinster, men begrenset fokus på bærekraft.",
                "Nivå 4: Systematisk måling og vurdering av om gevinster opprettholdes over tid.",
                "Nivå 5: Måling integrert i gevinstoppfølgingen, bærekraftige gevinster sikres."
            ]
        },
        {
            "id": 14,
            "title": "Operasjonell risiko og ulemper",
            "question": "Er mulige negative konsekvenser eller ulemper identifisert og håndtert?",
            "scale": [
                "Nivå 1: Negative effekter ikke vurdert.",
                "Nivå 2: Kjent, men ikke håndtert.",
                "Nivå 3: Beskrevet, men ikke fulgt opp systematisk.",
                "Nivå 4: Håndtert og overvåket med tilpasning til ulike scenarier.",
                "Nivå 5: Systematisk vurdert og del av gevinstdialogen med kontinuerlig justering."
            ]
        },
        {
            "id": 15,
            "title": "Balanse mellom gevinster og ulemper",
            "question": "Hvordan sikres det at balansen mellom gevinster og ulemper vurderes?",
            "scale": [
                "Nivå 1: Ingen vurdering av balanse.",
                "Nivå 2: Diskuteres uformelt.",
                "Nivå 3: Del av enkelte oppfølgingsmøter.",
                "Nivå 4: Systematisk vurdert i gevinststyring.",
                "Nivå 5: Inngår som fast punkt i styrings- og gevinstdialoger."
            ]
        },
        {
            "id": 16,
            "title": "Dokumentasjon og gevinstrealiseringsplan",
            "question": "Er det utarbeidet en forankret gevinstrealiseringsplan?",
            "scale": [
                "Nivå 1: Ingen formell gevinstrealiseringsplan.",
                "Nivå 2: Utkast til plan finnes, men er ufullstendig.",
                "Nivå 3: Plan er etablert, men ikke validert eller periodisert.",
                "Nivå 4: Planen er forankret, oppdatert og koblet til gevinstkartet.",
                "Nivå 5: Planen brukes aktivt som styringsdokument med revisjon."
            ]
        },
        {
            "id": 17,
            "title": "Gevinstrealiseringsplan som operativ handlingsplan",
            "question": "Hvordan sikres det at gevinstrealiseringsplanen fungerer som en operativ handlingsplan?",
            "scale": [
                "Nivå 1: Planen brukes ikke som operativt styringsverktøy.",
                "Nivå 2: Plan finnes, men uten operativ oppfølging.",
                "Nivå 3: Planen følges delvis opp i linjen.",
                "Nivå 4: Planen brukes aktivt som handlingsplan og styringsverktøy.",
                "Nivå 5: Gevinstplanen er fullt operativt integrert i linjens handlingsplaner."
            ]
        },
        {
            "id": 18,
            "title": "Endringsberedskap og operativ mottaksevne",
            "question": "Er organisasjonen forberedt på å ta imot endringer fra programmet?",
            "scale": [
                "Nivå 1: Ingen plan for endringsberedskap.",
                "Nivå 2: Kapasitet vurderes uformelt, men ikke håndtert.",
                "Nivå 3: Endringskapasitet omtales, men uten konkrete tiltak.",
                "Nivå 4: Tilfredsstillende beredskap etablert og koordinert med linjen.",
                "Nivå 5: Endringskapasitet er strukturert, overvåket og integrert i styring."
            ]
        },
        {
            "id": 19,
            "title": "Kommunikasjon og forankring",
            "question": "Er gevinstgrunnlag, roller og forventninger godt kommunisert?",
            "scale": [
                "Nivå 1: Ingen felles forståelse eller kommunikasjon.",
                "Nivå 2: Informasjon deles sporadisk.",
                "Nivå 3: Kommunikasjon er planlagt, men ikke systematisk målt.",
                "Nivå 4: Kommunikasjon er systematisk og forankret i organisasjonen.",
                "Nivå 5: Forankring skjer løpende som del av styringsdialog."
            ]
        },
        {
            "id": 20,
            "title": "Eierskap og ansvar",
            "question": "Er ansvar og roller tydelig definert for å sikre gjennomføring og gevinstuttak?",
            "scale": [
                "Nivå 1: Ansvar er uklart eller mangler.",
                "Nivå 2: Ansvar er delvis definert, men ikke praktisert.",
                "Nivå 3: Ansvar er kjent, men samhandling varierer.",
                "Nivå 4: Roller og ansvar fungerer godt i praksis.",
                "Nivå 5: Sterkt eierskap og kultur for ansvarliggjøring."
            ]
        },
        {
            "id": 21,
            "title": "Periodisering og forankring",
            "question": "Er gevinstrealiseringsplanen periodisert, validert og godkjent?",
            "scale": [
                "Nivå 1: Ingen tidsplan eller forankring.",
                "Nivå 2: Tidsplan foreligger, men ikke validert.",
                "Nivå 3: Delvis forankret hos enkelte ansvarlige/eiere.",
                "Nivå 4: Fullt forankret og koordinert med budsjett- og styringsprosesser.",
                "Nivå 5: Planen brukes aktivt i styringsdialog og rapportering."
            ]
        },
        {
            "id": 22,
            "title": "Realisme og engasjement",
            "question": "Oppleves gevinstplanen og estimatene realistiske og engasjerende?",
            "scale": [
                "Nivå 1: Ingen troverdighet eller engasjement.",
                "Nivå 2: Begrenset tillit til estimater.",
                "Nivå 3: Delvis aksept, men varierende engasjement.",
                "Nivå 4: Høy troverdighet og engasjement.",
                "Nivå 5: Sterk troverdighet og aktiv motivasjon i organisasjonen."
            ]
        },
        {
            "id": 23,
            "title": "Bygge momentum og tidlig gevinstuttak",
            "question": "Hvordan planlegges det for å bygge momentum og realisere tidlige gevinster?",
            "scale": [
                "Nivå 1: Ingen plan for tidlig gevinstuttak.",
                "Nivå 2: Enkelte uformelle vurderinger av tidlige gevinster.",
                "Nivå 3: Plan for tidlig gevinstuttak er identifisert, men ikke koordinert.",
                "Nivå 4: Strukturert tilnærming for tidlig gevinstuttak med tildelt ansvar.",
                "Nivå 5: Tidlig gevinstuttak er integrert i programmets DNA."
            ]
        }
    ],
    "Gjennomføring": [
        {"id": 1, "title": "Bruk av tidligere læring", "question": "Hvordan brukes erfaringer fra tidligere til å justere tiltak under gjennomføringen?", "scale": ["Nivå 1: Ingen læring anvendt.", "Nivå 2: Enkelte erfaringer omtalt.", "Nivå 3: Læring inkludert for enkelte områder.", "Nivå 4: Systematisk bruk av tidligere gevinstdata.", "Nivå 5: Kontinuerlig læring integrert."]},
        {"id": 2, "title": "Strategisk retning", "question": "Hvordan opprettholdes strategisk retning under gjennomføring?", "scale": ["Nivå 1: Strategisk kobling glemmes.", "Nivå 2: Strategi omtales, men ikke operasjonalisert.", "Nivå 3: Strategisk kobling vedlikeholdes delvis.", "Nivå 4: Tydelig strategisk retning med oppdatering.", "Nivå 5: Strategi dynamisk tilpasses."]},
        {"id": 3, "title": "Gevinstkart", "question": "Hvordan brukes gevinstkartet aktivt under gjennomføring?", "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Vises, men ikke aktivt brukt.", "Nivå 3: Oppdateres og brukes i noen beslutninger.", "Nivå 4: Aktivt styringsverktøy.", "Nivå 5: Brukes dynamisk til justering."]},
        {"id": 4, "title": "KPI-oppfølging", "question": "Hvordan følges strategisk kobling og KPI-er opp?", "scale": ["Nivå 1: Ingen oppfølging.", "Nivå 2: KPI-er måles, men kobling mangler.", "Nivå 3: Noen KPI-er følges opp.", "Nivå 4: Systematisk oppfølging.", "Nivå 5: Dynamisk justering."]},
        {"id": 5, "title": "Avgrensning", "question": "Hvordan håndteres avgrensning når nye forhold oppstår?", "scale": ["Nivå 1: Avgrensning glemmes.", "Nivå 2: Omtales, men ikke operasjonalisert.", "Nivå 3: Håndteres for større endringer.", "Nivå 4: System for håndtering.", "Nivå 5: Dynamisk avgrensning integrert."]},
        {"id": 6, "title": "Nullpunkter og estimater", "question": "Hvordan justeres nullpunkter og estimater basert på nye data?", "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Ad hoc justering.", "Nivå 3: Systematisk for store avvik.", "Nivå 4: Regelmessig revisjon.", "Nivå 5: Kontinuerlig basert på realtidsdata."]},
        {"id": 7, "title": "Hypotesetesting", "question": "Hvordan testes hypoteser under gjennomføring?", "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Noen uformelle tester.", "Nivå 3: Formell testing for kritiske hypoteser.", "Nivå 4: Systematisk testing og validering.", "Nivå 5: Kontinuerlig testing integrert."]},
        {"id": 8, "title": "Interessentengasjement", "question": "Hvordan opprettholdes interessentengasjement?", "scale": ["Nivå 1: Engasjement avtar.", "Nivå 2: Begrenset for viktige beslutninger.", "Nivå 3: Regelmessig for større endringer.", "Nivå 4: Systematisk oppfølging.", "Nivå 5: Kontinuerlig dialog og samskaping."]},
        {"id": 9, "title": "Gevinstforutsetninger", "question": "Hvordan overvåkes gevinstforutsetninger?", "scale": ["Nivå 1: Overvåkes ikke.", "Nivå 2: Noen overvåkes uformelt.", "Nivå 3: Systematisk for kritiske.", "Nivå 4: Aktiv håndtering av endrede.", "Nivå 5: Integrert i risikostyring."]},
        {"id": 10, "title": "Kriterier", "question": "Hvordan håndteres endringer i kriterier?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store endringer reaktivt.", "Nivå 3: System for håndtering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Dynamisk tilpasning."]},
        {"id": 11, "title": "Enighet", "question": "Hvordan opprettholdes enighet om estimater?", "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Bekreftes ved store endringer.", "Nivå 3: Regelmessig bekreftelse.", "Nivå 4: Systematisk arbeid.", "Nivå 5: Kontinuerlig dialog."]},
        {"id": 12, "title": "Disponering", "question": "Hvordan håndteres disponering av besparelser?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Justeres for store avvik.", "Nivå 3: Systematisk revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Optimal disponering integrert."]},
        {"id": 13, "title": "Effektivitetsmåling", "question": "Hvordan måles effektivitet og produktivitet?", "scale": ["Nivå 1: Måles ikke.", "Nivå 2: Noen målinger registreres.", "Nivå 3: Systematisk med begrenset analyse.", "Nivå 4: Regelmessig analyse og justering.", "Nivå 5: Realtids overvåkning."]},
        {"id": 14, "title": "Risiko", "question": "Hvordan identifiseres nye risikoer?", "scale": ["Nivå 1: Identifiseres ikke.", "Nivå 2: Store håndteres reaktivt.", "Nivå 3: Systematisk identifisering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Integrert i daglig drift."]},
        {"id": 15, "title": "Balanse", "question": "Hvordan vurderes balansen gevinster/ulemper?", "scale": ["Nivå 1: Vurderes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig vurdering.", "Nivå 4: Systematisk overvåkning.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 16, "title": "Plan-oppdatering", "question": "Hvordan oppdateres gevinstrealiseringsplanen?", "scale": ["Nivå 1: Oppdateres ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig oppdatering.", "Nivå 4: Aktivt i styring.", "Nivå 5: Dynamisk i sanntid."]},
        {"id": 17, "title": "Operativ plan", "question": "Hvordan fungerer planen som operativ handlingsplan?", "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Til visse operasjoner.", "Nivå 3: Integrert i deler.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Fullt integrert."]},
        {"id": 18, "title": "Endringsberedskap", "question": "Hvordan utvikles endringsberedskap?", "scale": ["Nivå 1: Utvikles ikke.", "Nivå 2: Begrenset fokus.", "Nivå 3: Systematisk arbeid.", "Nivå 4: Målrettet utvikling.", "Nivå 5: Kontinuerlig tilpasning."]},
        {"id": 19, "title": "Kommunikasjon", "question": "Hvordan opprettholdes kommunikasjon?", "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset om endringer.", "Nivå 3: Regelmessig om fremdrift.", "Nivå 4: Systematisk plan.", "Nivå 5: Kontinuerlig dialog integrert."]},
        {"id": 20, "title": "Eierskap", "question": "Hvordan utøves eierskap og ansvar?", "scale": ["Nivå 1: Svekkes.", "Nivå 2: Begrenset i kritiske faser.", "Nivå 3: Tydelig for sentrale områder.", "Nivå 4: Aktivt gjennom hele prosessen.", "Nivå 5: Sterk kultur som driver."]},
        {"id": 21, "title": "Periodisering", "question": "Hvordan justeres periodisering?", "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Store justeringer.", "Nivå 3: Regelmessig revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Fleksibel integrert."]},
        {"id": 22, "title": "Realisme", "question": "Hvordan opprettholdes realisme og engasjement?", "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset fokus.", "Nivå 3: Arbeid med å opprettholde.", "Nivå 4: Systematisk styrking.", "Nivå 5: Høy gjennom hele prosessen."]},
        {"id": 23, "title": "Momentum", "question": "Hvordan bygges momentum gjennom tidlig gevinstuttak?", "scale": ["Nivå 1: Ingen fokus.", "Nivå 2: Noen gevinster uten strategi.", "Nivå 3: Planlagt, men begrenset.", "Nivå 4: Systematisk arbeid.", "Nivå 5: Kontinuerlig fokus."]}
    ],
    "Realisering": [
        {"id": 1, "title": "Læring", "question": "Hvordan anvendes læring for å optimalisere gevinstuttak?", "scale": ["Nivå 1: Ingen læring.", "Nivå 2: Enkelte erfaringer.", "Nivå 3: Systematisk bruk.", "Nivå 4: Integrert i prosessen.", "Nivå 5: Kontinuerlig optimalisering."]},
        {"id": 2, "title": "Strategisk retning", "question": "Hvordan sikres strategisk retning under realisering?", "scale": ["Nivå 1: Glemmes.", "Nivå 2: Refereres, ikke operasjonalisert.", "Nivå 3: Tydelig retning.", "Nivå 4: Dynamisk tilpasses.", "Nivå 5: Fullt integrert."]},
        {"id": 3, "title": "Gevinstkart", "question": "Hvordan brukes gevinstkartet for å styre realiseringen?", "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Vises, ikke aktivt.", "Nivå 3: Brukes til prioritering.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Dynamisk oppdateres."]},
        {"id": 4, "title": "KPI-er", "question": "Hvordan følges KPI-er opp under realisering?", "scale": ["Nivå 1: Ingen oppfølging.", "Nivå 2: Måles, svak kobling.", "Nivå 3: Systematisk oppfølging.", "Nivå 4: Dynamisk justering.", "Nivå 5: Full integrasjon."]},
        {"id": 5, "title": "Avgrensning", "question": "Hvordan håndteres avgrensning under realisering?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store utfordringer håndteres.", "Nivå 3: System for håndtering.", "Nivå 4: Proaktiv håndtering.", "Nivå 5: Integrert i prosessen."]},
        {"id": 6, "title": "Nullpunkter", "question": "Hvordan valideres nullpunkter under realisering?", "scale": ["Nivå 1: Valideres ikke.", "Nivå 2: Store avvik reaktivt.", "Nivå 3: Systematisk validering.", "Nivå 4: Kontinuerlig justering.", "Nivå 5: Dynamisk oppdatering."]},
        {"id": 7, "title": "Hypoteser", "question": "Hvordan valideres hypoteser under realisering?", "scale": ["Nivå 1: Valideres ikke.", "Nivå 2: Noen testes uformelt.", "Nivå 3: Systematisk for kritiske.", "Nivå 4: Omfattende validering.", "Nivå 5: Kontinuerlig testing."]},
        {"id": 8, "title": "Interessenter", "question": "Hvordan opprettholdes interessentengasjement?", "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset for beslutninger.", "Nivå 3: Regelmessig dialog.", "Nivå 4: Aktivt engasjement.", "Nivå 5: Interessenter er drivkrefter."]},
        {"id": 9, "title": "Forutsetninger", "question": "Hvordan realiseres gevinstforutsetninger?", "scale": ["Nivå 1: Overvåkes ikke.", "Nivå 2: Noen følges opp.", "Nivå 3: Systematisk overvåkning.", "Nivå 4: Aktiv realisering.", "Nivå 5: Integrert i gevinstuttak."]},
        {"id": 10, "title": "Kriterier", "question": "Hvordan håndteres kriterier under realisering?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store avvik håndteres.", "Nivå 3: Systematisk håndtering.", "Nivå 4: Proaktiv tilpasning.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 11, "title": "Enighet", "question": "Hvordan opprettholdes enighet?", "scale": ["Nivå 1: Testes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig bekreftelse.", "Nivå 4: Kontinuerlig arbeid.", "Nivå 5: Full enighet gjennom fasen."]},
        {"id": 12, "title": "Disponering", "question": "Hvordan håndteres disponering?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store endringer håndteres.", "Nivå 3: Systematisk revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Optimal disponering."]},
        {"id": 13, "title": "Effektivitet", "question": "Hvordan forbedres effektivitet?", "scale": ["Nivå 1: Måles ikke.", "Nivå 2: Noen målinger.", "Nivå 3: Systematisk rapportering.", "Nivå 4: Brukes til forbedring.", "Nivå 5: Kontinuerlig forbedring."]},
        {"id": 14, "title": "Risiko", "question": "Hvordan håndteres risikoer?", "scale": ["Nivå 1: Håndteres ikke.", "Nivå 2: Store reaktivt.", "Nivå 3: Systematisk håndtering.", "Nivå 4: Proaktiv.", "Nivå 5: Integrert i arbeid."]},
        {"id": 15, "title": "Balanse", "question": "Hvordan vurderes balansen?", "scale": ["Nivå 1: Vurderes ikke.", "Nivå 2: Ved store endringer.", "Nivå 3: Regelmessig.", "Nivå 4: Systematisk.", "Nivå 5: Integrert i beslutninger."]},
        {"id": 16, "title": "Plan", "question": "Hvordan brukes planen?", "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Refereres ved behov.", "Nivå 3: Aktivt i realisering.", "Nivå 4: Oppdateres kontinuerlig.", "Nivå 5: Sentralt verktøy."]},
        {"id": 17, "title": "Operativ plan", "question": "Hvordan fungerer planen operativt?", "scale": ["Nivå 1: Brukes ikke.", "Nivå 2: Til enkelte operasjoner.", "Nivå 3: Integrert i styring.", "Nivå 4: Aktivt verktøy.", "Nivå 5: Driver virksomhet."]},
        {"id": 18, "title": "Mottaksevne", "question": "Hvordan utvikles mottaksevne?", "scale": ["Nivå 1: Utvikles ikke.", "Nivå 2: Begrenset fokus.", "Nivå 3: Systematisk arbeid.", "Nivå 4: Målrettet utvikling.", "Nivå 5: Høy mottaksevne."]},
        {"id": 19, "title": "Kommunikasjon", "question": "Hvordan opprettholdes kommunikasjon?", "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset.", "Nivå 3: Regelmessig.", "Nivå 4: Systematisk.", "Nivå 5: Kontinuerlig dialog."]},
        {"id": 20, "title": "Eierskap", "question": "Hvordan utøves eierskap?", "scale": ["Nivå 1: Svekkes.", "Nivå 2: Begrenset.", "Nivå 3: Tydelig.", "Nivå 4: Aktivt.", "Nivå 5: Sterk kultur."]},
        {"id": 21, "title": "Periodisering", "question": "Hvordan justeres periodisering?", "scale": ["Nivå 1: Justeres ikke.", "Nivå 2: Store justeringer.", "Nivå 3: Regelmessig revisjon.", "Nivå 4: Dynamisk tilpasning.", "Nivå 5: Fleksibel."]},
        {"id": 22, "title": "Realisme", "question": "Hvordan opprettholdes realisme?", "scale": ["Nivå 1: Avtar.", "Nivå 2: Begrenset fokus.", "Nivå 3: Arbeid med å opprettholde.", "Nivå 4: Systematisk styrking.", "Nivå 5: Høy troverdighet."]},
        {"id": 23, "title": "Momentum", "question": "Hvordan brukes tidlig gevinstuttak?", "scale": ["Nivå 1: Ingen systematisk.", "Nivå 2: Enkelte suksesser motiverer.", "Nivå 3: Bevissthet på viktighet.", "Nivå 4: Strategisk bruk.", "Nivå 5: Systematisk bygget."]}
    ],
    "Realisert": [
        {"id": 1, "title": "Læringsdokumentasjon", "question": "Hvordan dokumenteres læring for fremtidig bruk?", "scale": ["Nivå 1: Ingen dokumentasjon.", "Nivå 2: Enkelte deles uformelt.", "Nivå 3: Systematisk dokumentasjon.", "Nivå 4: Deles aktivt.", "Nivå 5: Integrert i kunnskapsbase."]},
        {"id": 2, "title": "Strategisk bidrag", "question": "Hvordan bidro strategisk retning til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Fullt integrert."]},
        {"id": 3, "title": "Gevinstkart-bidrag", "question": "Hvordan bidro gevinstkartet til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Nyttig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Viktig.", "Nivå 5: Avgjørende."]},
        {"id": 4, "title": "KPI-bidrag", "question": "Hvordan bidro KPI-er til realisering?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Full integrasjon."]},
        {"id": 5, "title": "Avgrensning-troverdighet", "question": "Hvordan bidro avgrensning til troverdighet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til troverdighet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 6, "title": "Estimat-nøyaktighet", "question": "Hvordan bidro estimater til nøyaktighet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Nøyaktige for enkelte.", "Nivå 3: Nøyaktige for flere.", "Nivå 4: Høy nøyaktighet.", "Nivå 5: Svært nøyaktige."]},
        {"id": 7, "title": "Testing-kvalitet", "question": "Hvordan bidro hypotesetesting til kvalitet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til kvalitet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 8, "title": "Interessent-suksess", "question": "Hvordan bidro interessentengasjement til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drivkrefter for suksess."]},
        {"id": 9, "title": "Forutsetning-suksess", "question": "Hvordan bidro forutsetningshåndtering til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Suksessfaktor."]},
        {"id": 10, "title": "Kriterie-realisering", "question": "Hvordan bidro kriteriehåndtering til realisering?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket realisering."]},
        {"id": 11, "title": "Enighet-suksess", "question": "Hvordan bidro enighet til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 12, "title": "Disponering-verdi", "question": "Hvordan bidro disponering til verdiskapning?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til verdi.", "Nivå 4: Avgjørende.", "Nivå 5: Maksimerte verdi."]},
        {"id": 13, "title": "Måling-realisering", "question": "Hvordan bidro måling til realisering?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet realisering."]},
        {"id": 14, "title": "Risiko-robusthet", "question": "Hvordan bidro risikohåndtering til robusthet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til robusthet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 15, "title": "Balanse-bærekraft", "question": "Hvordan bidro balansevurdering til bærekraft?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til bærekraft.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 16, "title": "Plan-suksess", "question": "Hvordan bidro planen til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Suksessfaktor."]},
        {"id": 17, "title": "Operativ-suksess", "question": "Hvordan bidro planen som operativ handlingsplan?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet realisering."]},
        {"id": 18, "title": "Beredskap-realisering", "question": "Hvordan bidro endringsberedskap til realisering?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Høy mottaksevne drevet."]},
        {"id": 19, "title": "Kommunikasjon-suksess", "question": "Hvordan bidro kommunikasjon til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket betydelig."]},
        {"id": 20, "title": "Eierskap-suksess", "question": "Hvordan bidro eierskap til suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til flere.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet suksess."]},
        {"id": 21, "title": "Periodisering-effektivitet", "question": "Hvordan bidro periodisering til effektivitet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til effektivitet.", "Nivå 4: Avgjørende.", "Nivå 5: Maksimerte effektivitet."]},
        {"id": 22, "title": "Realisme-troverdighet", "question": "Hvordan bidro realisme til troverdighet?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til troverdighet.", "Nivå 4: Avgjørende.", "Nivå 5: Styrket realisering."]},
        {"id": 23, "title": "Momentum-langsiktig", "question": "Hvordan bidro momentum til langsiktig suksess?", "scale": ["Nivå 1: Bidro lite.", "Nivå 2: Viktig for enkelte.", "Nivå 3: Bidro til momentum.", "Nivå 4: Avgjørende.", "Nivå 5: Drevet langsiktig suksess."]}
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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans Pro', sans-serif; }
.main-header { font-size: 2rem; color: #172141; text-align: center; margin-bottom: 0.3rem; font-weight: 700; }
.sub-header { font-size: 0.95rem; color: #0053A6; text-align: center; margin-bottom: 1.5rem; }
.info-box { background: linear-gradient(135deg, #C4EFFF 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #64C8FA; margin: 0.8rem 0; }
.success-box { background: linear-gradient(135deg, #DDFAE2 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #35DE6D; margin: 0.8rem 0; }
.warning-box { background: linear-gradient(135deg, rgba(255, 160, 64, 0.15) 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #FFA040; margin: 0.8rem 0; }
.critical-box { background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #FF6B6B; margin: 0.8rem 0; }
.metric-card { background: #F2FAFD; padding: 1rem; border-radius: 10px; border-left: 4px solid #0053A6; text-align: center; margin: 0.3rem 0; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #172141; }
.metric-label { font-size: 0.75rem; color: #666; text-transform: uppercase; }
.role-card { background: linear-gradient(135deg, #F2FAFD 0%, #E8F4FD 100%); padding: 1.2rem; border-radius: 12px; border: 2px solid #64C8FA; margin: 0.5rem 0; cursor: pointer; transition: all 0.2s; }
.role-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 83, 166, 0.2); }
.role-card-selected { background: linear-gradient(135deg, #0053A6 0%, #172141 100%); color: white; border-color: #172141; }
.high-maturity-card { background: linear-gradient(135deg, #DDFAE2 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #35DE6D; margin: 0.5rem 0; }
.low-maturity-card { background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, #F2FAFD 100%); padding: 1rem; border-radius: 10px; border-left: 4px solid #FF6B6B; margin: 0.5rem 0; }
.question-count { background: #0053A6; color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.stButton > button { background: linear-gradient(135deg, #0053A6 0%, #172141 100%); color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 83, 166, 0.3); }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #64C8FA 0%, #35DE6D 100%); }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HJELPEFUNKSJONER
# ============================================================================
def get_score_color(score):
    if score >= 4.5: return "#35DE6D"
    elif score >= 3.5: return "#64C8FA"
    elif score >= 2.5: return "#FFA040"
    else: return "#FF6B6B"

def get_score_text(score):
    if score >= 4.5: return "Høy modenhet"
    elif score >= 3.5: return "God modenhet"
    elif score >= 2.5: return "Moderat modenhet"
    elif score >= 1.5: return "Begrenset modenhet"
    else: return "Lav modenhet"

def get_questions_for_role(role_name):
    """Hent alle spørsmål for en rolle"""
    if role_name not in ROLES:
        return {}
    
    role = ROLES[role_name]
    if role['questions'] == "ALL":
        return {phase: list(range(1, 24)) for phase in phases_data.keys()}
    
    return role['questions']

def count_role_questions(role_name):
    """Tell totalt antall spørsmål for en rolle"""
    questions = get_questions_for_role(role_name)
    return sum(len(q_ids) for q_ids in questions.values())

def calculate_stats(initiative):
    """Beregn statistikk for et endringsinitiativ"""
    if not initiative.get('interviews'):
        return None
    
    all_scores = {}
    for phase in phases_data:
        all_scores[phase] = {}
        for q in phases_data[phase]:
            all_scores[phase][q['id']] = []
    
    for interview in initiative['interviews'].values():
        for phase, questions in interview.get('responses', {}).items():
            for q_id, resp in questions.items():
                if resp.get('score', 0) > 0:
                    all_scores[phase][int(q_id)].append(resp['score'])
    
    stats = {
        'phases': {},
        'questions': {},
        'parameters': {},
        'total_interviews': len(initiative['interviews']),
        'overall_avg': 0,
        'high_maturity': [],
        'low_maturity': []
    }
    
    all_avgs = []
    
    for phase in phases_data:
        phase_scores = []
        stats['questions'][phase] = {}
        
        for q in phases_data[phase]:
            scores = all_scores[phase][q['id']]
            if scores:
                avg = np.mean(scores)
                stats['questions'][phase][q['id']] = {
                    'avg': avg, 'min': min(scores), 'max': max(scores),
                    'count': len(scores), 'title': q['title'], 'question': q['question']
                }
                phase_scores.append(avg)
                all_avgs.append(avg)
                
                item = {'phase': phase, 'question_id': q['id'], 'question': q['title'], 'score': avg}
                if avg >= 4:
                    stats['high_maturity'].append(item)
                elif avg < 3:
                    stats['low_maturity'].append(item)
        
        if phase_scores:
            stats['phases'][phase] = {'avg': np.mean(phase_scores), 'min': min(phase_scores), 'max': max(phase_scores)}
    
    for param_name, param_data in PARAMETERS.items():
        param_scores = []
        for phase, q_ids in param_data['questions'].items():
            if phase in stats['questions']:
                for q_id in q_ids:
                    if q_id in stats['questions'][phase]:
                        param_scores.append(stats['questions'][phase][q_id]['avg'])
        if param_scores:
            stats['parameters'][param_name] = {
                'avg': np.mean(param_scores),
                'description': param_data['description'],
                'questions': param_data['questions']
            }
    
    if all_avgs:
        stats['overall_avg'] = np.mean(all_avgs)
    
    stats['high_maturity'].sort(key=lambda x: x['score'], reverse=True)
    stats['low_maturity'].sort(key=lambda x: x['score'])
    
    return stats

def create_phase_radar(phase_data):
    if not phase_data or len(phase_data) < 3:
        return None
    categories = list(phase_data.keys())
    values = [phase_data[c]['avg'] for c in categories]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(0, 83, 166, 0.3)', line=dict(color='#0053A6', width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[1,2,3,4,5])),
        showlegend=False, height=400, margin=dict(l=80, r=80, t=40, b=40), paper_bgcolor='white')
    return fig

def create_parameter_radar(param_data):
    if not param_data or len(param_data) < 3:
        return None
    categories = list(param_data.keys())
    values = [param_data[c]['avg'] for c in categories]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(100, 200, 250, 0.3)', line=dict(color='#64C8FA', width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False, height=450, margin=dict(l=100, r=100, t=40, b=40))
    return fig

# ============================================================================
# HOVEDAPPLIKASJON
# ============================================================================
def main():
    data = get_data()
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("bane_nor_logo.png.jpg", width=180)
        except:
            st.markdown("### 🚂 Bane NOR")
    
    st.markdown('<h1 class="main-header">Modenhetsvurdering</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">I samarbeid med Konsern økonomi og digital transformasjon</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#0053A6; font-weight:600;">🎯 Versjon A: Rollebasert spørsmålsutvalg</p>', unsafe_allow_html=True)
    
    # Navigasjon
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "ℹ️ Om vurderingen",
        "📁 Endringsinitiativ",
        "🎤 Intervju", 
        "📊 Resultater",
        "📋 Rapport"
    ])
    
    # TAB 1: OM VURDERINGEN
    with tab1:
        st.markdown(HENSIKT_TEKST)
        
        st.markdown("---")
        st.markdown("### 🎭 Tilgjengelige roller")
        st.markdown("Velg rolle ved oppstart av intervju for å få tilpasset spørsmålssett:")
        
        cols = st.columns(3)
        for idx, (role_name, role_data) in enumerate(ROLES.items()):
            with cols[idx % 3]:
                q_count = count_role_questions(role_name)
                phases_str = ", ".join(role_data['phases'][:2]) if role_data['phases'] else "Velg selv"
                st.markdown(f"""
                <div class="role-card">
                    <span style="font-size:1.5rem">{role_data['icon']}</span>
                    <strong>{role_name}</strong><br>
                    <small>{role_data['description']}</small><br>
                    <span class="question-count">{q_count} spørsmål</span>
                    <small style="color:#666"> • {phases_str}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 2: ENDRINGSINITIATIV
    with tab2:
        st.markdown("## Endringsinitiativ")
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### ➕ Nytt endringsinitiativ")
            with st.form("new_initiative"):
                init_name = st.text_input("Navn på endringsinitiativ", placeholder="F.eks. ERTMS Østlandet")
                init_desc = st.text_area("Beskrivelse", placeholder="Kort beskrivelse...", height=80)
                
                if st.form_submit_button("Opprett", use_container_width=True):
                    if init_name:
                        init_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        data['initiatives'][init_id] = {
                            'name': init_name,
                            'description': init_desc,
                            'created': datetime.now().isoformat(),
                            'interviews': {}
                        }
                        persist_data()
                        st.success(f"✅ '{init_name}' opprettet!")
                        st.rerun()
                    else:
                        st.error("Skriv inn et navn")
        
        with col1:
            st.markdown("### Mine endringsinitiativ")
            
            if not data['initiatives']:
                st.markdown('<div class="info-box">Ingen endringsinitiativ ennå. Opprett et nytt for å starte →</div>', unsafe_allow_html=True)
            else:
                for init_id, initiative in data['initiatives'].items():
                    num_interviews = len(initiative.get('interviews', {}))
                    stats = calculate_stats(initiative)
                    avg_score = stats['overall_avg'] if stats else 0
                    
                    with st.expander(f"📁 {initiative['name']} ({num_interviews} intervjuer)", expanded=False):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.write(f"**Beskrivelse:** {initiative.get('description', 'Ingen')}")
                            if num_interviews > 0 and avg_score > 0:
                                st.write(f"**Gjennomsnitt:** {avg_score:.2f} ({get_score_text(avg_score)})")
                        with col_b:
                            if st.button("🗑️ Slett", key=f"del_{init_id}"):
                                del data['initiatives'][init_id]
                                persist_data()
                                st.rerun()
    
    # TAB 3: INTERVJU
    with tab3:
        st.markdown("## Gjennomfør intervju")
        
        if not data['initiatives']:
            st.warning("⚠️ Opprett et endringsinitiativ først")
        else:
            init_options = {p['name']: pid for pid, p in data['initiatives'].items()}
            selected_init_name = st.selectbox("Velg endringsinitiativ", options=list(init_options.keys()))
            selected_init_id = init_options[selected_init_name]
            initiative = data['initiatives'][selected_init_id]
            
            st.markdown("---")
            
            # Sjekk om vi har aktivt intervju
            if 'active_interview' not in st.session_state:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🆕 Start nytt intervju")
                    
                    # STEG 1: Velg rolle
                    st.markdown("**Steg 1: Velg rolle**")
                    role_options = list(ROLES.keys())
                    selected_role = st.selectbox(
                        "Intervjuobjektets rolle",
                        options=role_options,
                        format_func=lambda x: f"{ROLES[x]['icon']} {x} ({count_role_questions(x)} spm)"
                    )
                    
                    role_info = ROLES[selected_role]
                    st.markdown(f"*{role_info['description']}*")
                    
                    if selected_role == "Manuelt utvalg":
                        st.info("Du velger spørsmål manuelt etter at intervjuet er startet")
                    else:
                        q_by_phase = get_questions_for_role(selected_role)
                        st.markdown("**Inkluderte spørsmål:**")
                        for phase, q_ids in q_by_phase.items():
                            st.write(f"- {phase}: {len(q_ids)} spørsmål")
                    
                    st.markdown("---")
                    st.markdown("**Steg 2: Intervjuinfo**")
                    
                    with st.form("new_interview"):
                        interviewer = st.text_input("Intervjuer (deg)", placeholder="Ditt navn")
                        interviewee = st.text_input("Intervjuobjekt *", placeholder="Navn på personen")
                        role_title = st.text_input("Stilling", placeholder="F.eks. Prosjektleder", value=selected_role.split("/")[0].strip() if "/" in selected_role else "")
                        date = st.date_input("Dato", value=datetime.now())
                        
                        if st.form_submit_button("▶️ Start intervju", use_container_width=True):
                            if interviewee:
                                interview_id = datetime.now().strftime("%Y%m%d%H%M%S")
                                
                                # Hent spørsmål for rollen
                                selected_questions = get_questions_for_role(selected_role)
                                
                                initiative['interviews'][interview_id] = {
                                    'info': {
                                        'interviewer': interviewer,
                                        'interviewee': interviewee,
                                        'role': role_title,
                                        'role_type': selected_role,
                                        'date': date.strftime('%Y-%m-%d')
                                    },
                                    'selected_questions': selected_questions,
                                    'responses': {}
                                }
                                persist_data()
                                st.session_state['active_interview'] = {
                                    'init_id': selected_init_id,
                                    'interview_id': interview_id
                                }
                                st.success(f"✅ Intervju med {interviewee} startet!")
                                st.rerun()
                            else:
                                st.error("Skriv inn navn på intervjuobjekt")
                
                with col2:
                    st.markdown("### 📝 Fortsett eksisterende")
                    if initiative['interviews']:
                        interview_options = {
                            f"{i['info']['interviewee']} - {i['info'].get('role_type', 'Ukjent')} ({i['info']['date']})": iid 
                            for iid, i in initiative['interviews'].items()
                        }
                        selected_interview = st.selectbox("Velg intervju", options=list(interview_options.keys()))
                        
                        if st.button("Fortsett dette intervjuet", use_container_width=True):
                            st.session_state['active_interview'] = {
                                'init_id': selected_init_id,
                                'interview_id': interview_options[selected_interview]
                            }
                            st.rerun()
                    else:
                        st.info("Ingen intervjuer i dette endringsinitiativet ennå")
            
            else:
                # Aktivt intervju
                active = st.session_state['active_interview']
                
                if active['init_id'] in data['initiatives']:
                    initiative = data['initiatives'][active['init_id']]
                    if active['interview_id'] in initiative['interviews']:
                        interview = initiative['interviews'][active['interview_id']]
                        
                        role_type = interview['info'].get('role_type', 'Alle spørsmål')
                        selected_questions = interview.get('selected_questions', {})
                        
                        # Header med info
                        st.markdown(f"""
                        ### 🎤 Intervju: **{interview['info']['interviewee']}**
                        **Rolle:** {role_type} | **Stilling:** {interview['info']['role']} | **Dato:** {interview['info']['date']}
                        """)
                        
                        # Tell besvarte
                        total_q = sum(len(q_ids) for q_ids in selected_questions.items())
                        answered = 0
                        for phase, q_ids in selected_questions.items():
                            if phase in interview.get('responses', {}):
                                for q_id in q_ids:
                                    if interview['responses'][phase].get(str(q_id), {}).get('score', 0) > 0:
                                        answered += 1
                        
                        st.progress(answered / max(total_q, 1))
                        st.caption(f"Besvart: {answered} av {total_q} spørsmål")
                        
                        # Mulighet for å legge til spørsmål
                        with st.expander("➕ Legg til flere spørsmål"):
                            add_phase = st.selectbox("Fra fase:", options=list(phases_data.keys()), key="add_phase")
                            available = [q for q in phases_data[add_phase] 
                                        if q['id'] not in selected_questions.get(add_phase, [])]
                            
                            if available:
                                add_q = st.selectbox(
                                    "Velg spørsmål:",
                                    options=available,
                                    format_func=lambda x: f"{x['id']}. {x['title']}"
                                )
                                if st.button("➕ Legg til"):
                                    if add_phase not in selected_questions:
                                        selected_questions[add_phase] = []
                                    selected_questions[add_phase].append(add_q['id'])
                                    interview['selected_questions'] = selected_questions
                                    persist_data()
                                    st.rerun()
                            else:
                                st.info("Alle spørsmål fra denne fasen er allerede valgt")
                        
                        st.markdown("---")
                        
                        # Vis kun valgte spørsmål, organisert per fase
                        for phase_name in phases_data.keys():
                            if phase_name in selected_questions and selected_questions[phase_name]:
                                q_ids_for_phase = selected_questions[phase_name]
                                
                                # Initialiser responses for denne fasen
                                if phase_name not in interview['responses']:
                                    interview['responses'][phase_name] = {}
                                
                                phase_answered = sum(1 for q_id in q_ids_for_phase 
                                                    if interview['responses'][phase_name].get(str(q_id), {}).get('score', 0) > 0)
                                
                                st.markdown(f"### {phase_name} ({phase_answered}/{len(q_ids_for_phase)} besvart)")
                                
                                for q_id in q_ids_for_phase:
                                    # Finn spørsmålet
                                    q = next((q for q in phases_data[phase_name] if q['id'] == q_id), None)
                                    if not q:
                                        continue
                                    
                                    q_id_str = str(q_id)
                                    
                                    if q_id_str not in interview['responses'][phase_name]:
                                        interview['responses'][phase_name][q_id_str] = {'score': 0, 'notes': ''}
                                    
                                    resp = interview['responses'][phase_name][q_id_str]
                                    status = "✅" if resp['score'] > 0 else "⬜"
                                    score_display = f" → Nivå {resp['score']}" if resp['score'] > 0 else ""
                                    
                                    with st.expander(f"{status} {q['id']}. {q['title']}{score_display}"):
                                        st.markdown(f"**{q['question']}**")
                                        
                                        st.markdown("**Modenhetsskala:**")
                                        for level in q['scale']:
                                            st.write(f"- {level}")
                                        
                                        st.markdown("---")
                                        
                                        new_score = st.radio(
                                            "Velg nivå:",
                                            options=[0, 1, 2, 3, 4, 5],
                                            index=resp['score'],
                                            key=f"s_{phase_name}_{q_id}",
                                            horizontal=True,
                                            format_func=lambda x: "Ikke vurdert" if x == 0 else f"Nivå {x}"
                                        )
                                        
                                        new_notes = st.text_area(
                                            "Notater:",
                                            value=resp['notes'],
                                            key=f"n_{phase_name}_{q_id}",
                                            placeholder="Begrunnelse, sitater, observasjoner...",
                                            height=80
                                        )
                                        
                                        if st.button("💾 Lagre", key=f"save_{phase_name}_{q_id}"):
                                            interview['responses'][phase_name][q_id_str] = {
                                                'score': new_score,
                                                'notes': new_notes
                                            }
                                            persist_data()
                                            st.success("Lagret!")
                                            st.rerun()
                        
                        # Avslutt intervju
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Avslutt intervju", use_container_width=True):
                                del st.session_state['active_interview']
                                st.success("Intervju avsluttet og lagret!")
                                st.rerun()
                        with col2:
                            if st.button("🚪 Avbryt uten å lagre", use_container_width=True):
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
            
            stats = calculate_stats(initiative)
            
            if not stats or stats['total_interviews'] == 0:
                st.info("Ingen intervjuer gjennomført ennå")
            else:
                # Nøkkeltall
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Intervjuer</div><div class="metric-value">{stats["total_interviews"]}</div></div>', unsafe_allow_html=True)
                with col2:
                    color = get_score_color(stats['overall_avg'])
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Gjennomsnitt</div><div class="metric-value" style="color: {color}">{stats["overall_avg"]:.2f}</div></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="high-maturity-card"><div class="metric-label">Styrkeområder</div><div class="metric-value" style="color: #35DE6D">{len(stats["high_maturity"])}</div></div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="low-maturity-card"><div class="metric-label">Forbedringsområder</div><div class="metric-value" style="color: #FF6B6B">{len(stats["low_maturity"])}</div></div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Radardiagrammer
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Modenhet per fase")
                    radar = create_phase_radar(stats['phases'])
                    if radar:
                        st.plotly_chart(radar, use_container_width=True)
                
                with col2:
                    st.markdown("### Modenhet per parameter")
                    param_radar = create_parameter_radar(stats['parameters'])
                    if param_radar:
                        st.plotly_chart(param_radar, use_container_width=True)
                
                # Styrker og svakheter
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Styrkeområder (score ≥ 4)")
                    if not stats['high_maturity']:
                        st.info("Ingen områder med høy modenhet")
                    else:
                        for item in stats['high_maturity'][:8]:
                            st.markdown(f'<div class="high-maturity-card"><strong>{item["phase"]}</strong> - {item["question"]}<br>Score: {item["score"]:.2f}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### ⚠️ Forbedringsområder (score < 3)")
                    if not stats['low_maturity']:
                        st.success("Ingen kritiske forbedringsområder!")
                    else:
                        for item in stats['low_maturity'][:8]:
                            st.markdown(f'<div class="low-maturity-card"><strong>{item["phase"]}</strong> - {item["question"]}<br>Score: {item["score"]:.2f}</div>', unsafe_allow_html=True)
                
                # Parameterresultater
                st.markdown("---")
                st.markdown("### 📋 Resultater per parameter")
                
                for param_name, param_data in stats['parameters'].items():
                    avg = param_data['avg']
                    color = get_score_color(avg)
                    
                    with st.expander(f"**{param_name}** - Score: {avg:.2f} ({get_score_text(avg)})"):
                        st.markdown(f"*{PARAMETERS[param_name]['description']}*")
                        
                        for phase, q_ids in PARAMETERS[param_name]['questions'].items():
                            if phase in stats['questions']:
                                st.markdown(f"**{phase}:**")
                                for q_id in q_ids:
                                    if q_id in stats['questions'][phase]:
                                        q_data = stats['questions'][phase][q_id]
                                        q_color = get_score_color(q_data['avg'])
                                        st.markdown(f"- Sp. {q_id}: {q_data['title']} - <span style='color:{q_color};font-weight:bold'>{q_data['avg']:.2f}</span>", unsafe_allow_html=True)
    
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
                # CSV-eksport
                st.markdown("### Eksporter data")
                
                csv_data = []
                for phase in stats['questions']:
                    for q_id, q_data in stats['questions'][phase].items():
                        csv_data.append({
                            'Fase': phase,
                            'SpørsmålID': q_id,
                            'Tittel': q_data['title'],
                            'Gjennomsnitt': round(q_data['avg'], 2),
                            'Min': q_data['min'],
                            'Maks': q_data['max'],
                            'AntallSvar': q_data['count']
                        })
                
                csv_df = pd.DataFrame(csv_data)
                csv_string = csv_df.to_csv(index=False, sep=';')
                
                st.download_button(
                    "📥 Last ned CSV-data",
                    data=csv_string,
                    file_name=f"modenhet_{initiative['name']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Modenhetsvurdering v4A (Rollebasert) | Bane NOR - Konsern økonomi og digital transformasjon
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
