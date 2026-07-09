"""ENT-specific search queries for the Daily Digest.

Each topic has PubMed/Europe PMC search queries that find
relevant recent publications.
"""

from __future__ import annotations

from api.digest.models import ENTSubspecialty

TOPIC_QUERIES: dict[ENTSubspecialty, list[str]] = {
    ENTSubspecialty.OTOLOGY: [
        "otology OR otitis media OR tympanoplasty OR cholesteatoma",
        "cochlear implant OR hearing loss OR tinnitus",
        "otosclerosis OR stapedotomy OR ossicular chain",
    ],
    ENTSubspecialty.RHINOLOGY: [
        "rhinology OR chronic rhinosinusitis OR nasal polyps",
        "functional endoscopic sinus surgery OR FESS",
        "allergic rhinitis OR olfactory dysfunction OR anosmia",
    ],
    ENTSubspecialty.LARYNGOLOGY: [
        "laryngology OR vocal cord OR dysphonia OR hoarseness",
        "laryngeal cancer OR laryngectomy OR voice therapy",
        "laryngopharyngeal reflux OR laryngeal papillomatosis",
    ],
    ENTSubspecialty.HEAD_NECK_SURGERY: [
        "head and neck cancer OR oral cavity cancer OR oropharyngeal cancer",
        "neck dissection OR thyroid surgery OR parotidectomy",
        "HPV oropharyngeal squamous cell carcinoma",
        "free flap reconstruction OR microvascular head neck",
    ],
    ENTSubspecialty.AUDIOLOGY: [
        "audiology OR hearing aid OR audiometry OR otoacoustic emissions",
        "newborn hearing screening OR auditory neuropathy",
        "age-related hearing loss OR presbycusis",
    ],
    ENTSubspecialty.VESTIBULAR: [
        "vestibular OR vertigo OR Meniere disease OR BPPV",
        "vestibular neuritis OR labyrinthitis OR balance disorder",
        "vestibular rehabilitation OR VNG OR videonystagmography",
    ],
    ENTSubspecialty.SLEEP_MEDICINE: [
        "sleep apnea OR OSA OR obstructive sleep apnea",
        "CPAP OR uvulopalatopharyngoplasty OR hypoglossal nerve stimulation",
        "sleep disordered breathing OR polysomnography",
    ],
    ENTSubspecialty.PEDIATRIC_ENT: [
        "pediatric otolaryngology OR pediatric ENT",
        "pediatric hearing loss OR pediatric sinusitis",
        "tonsillectomy OR adenoidectomy OR pediatric airway",
    ],
    ENTSubspecialty.FACIAL_PLASTICS: [
        "facial plastic surgery OR rhinoplasty OR facelift",
        "facial nerve paralysis OR facial reanimation",
        "otoplasty OR blepharoplasty OR facial trauma reconstruction",
    ],
    ENTSubspecialty.SKULL_BASE: [
        "skull base surgery OR endoscopic skull base",
        "pituitary surgery OR acoustic neuroma OR vestibular schwannoma",
        "cerebrospinal fluid leak repair OR anterior skull base",
    ],
    ENTSubspecialty.GENERAL_ENT: [
        "otolaryngology OR ENT",
        "otorhinolaryngology clinical practice guideline",
        "ENT emergency OR peritonsillar abscess OR epistaxis",
    ],
}
