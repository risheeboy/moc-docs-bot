"""Language enum with all 23 Indian language codes from §9 of Shared Contracts."""

from enum import Enum


class Language(str, Enum):
    """ISO 639-1 language codes for all Indian scheduled languages plus English."""

    HI = "hi"  # Hindi - Devanagari
    EN = "en"  # English - Latin
    BN = "bn"  # Bengali - Bengali
    TE = "te"  # Telugu - Telugu
    MR = "mr"  # Marathi - Devanagari
    TA = "ta"  # Tamil - Tamil
    UR = "ur"  # Urdu - Perso-Arabic
    GU = "gu"  # Gujarati - Gujarati
    KN = "kn"  # Kannada - Kannada
    ML = "ml"  # Malayalam - Malayalam
    OR = "or"  # Odia - Odia
    PA = "pa"  # Punjabi - Gurmukhi
    AS_LANG = "as"  # Assamese - Bengali (as_ to avoid conflict with built-in)
    MAI = "mai"  # Maithili - Devanagari
    SA = "sa"  # Sanskrit - Devanagari
    NE = "ne"  # Nepali - Devanagari
    SD = "sd"  # Sindhi - Perso-Arabic
    KOK = "kok"  # Konkani - Devanagari
    DOI = "doi"  # Dogri - Devanagari
    MNI = "mni"  # Manipuri - Meitei
    SAT = "sat"  # Santali - Ol Chiki
    BO = "bo"  # Bodo - Devanagari
    KS = "ks"  # Kashmiri - Perso-Arabic

    @classmethod
    def validate(cls, value: str) -> "Language":
        """Validate and return Language enum value.

        Args:
            value: Language code string (e.g., "hi", "en")

        Returns:
            Language enum member

        Raises:
            ValueError: If language code is not supported
        """
        value_lower = value.lower()
        for member in cls:
            if member.value == value_lower:
                return member
        raise ValueError(
            f"Unsupported language code: {value}. "
            f"Supported codes: {', '.join(m.value for m in cls)}"
        )

    @classmethod
    def get_all_codes(cls) -> list[str]:
        """Get all supported language codes."""
        return [member.value for member in cls]

    def __str__(self) -> str:
        """Return language code."""
        return self.value

    @property
    def script(self) -> str:
        """Return the script used by this language."""
        scripts = {
            Language.HI.value: "Devanagari",
            Language.EN.value: "Latin",
            Language.BN.value: "Bengali",
            Language.TE.value: "Telugu",
            Language.MR.value: "Devanagari",
            Language.TA.value: "Tamil",
            Language.UR.value: "Perso-Arabic",
            Language.GU.value: "Gujarati",
            Language.KN.value: "Kannada",
            Language.ML.value: "Malayalam",
            Language.OR.value: "Odia",
            Language.PA.value: "Gurmukhi",
            Language.AS_LANG.value: "Bengali",
            Language.MAI.value: "Devanagari",
            Language.SA.value: "Devanagari",
            Language.NE.value: "Devanagari",
            Language.SD.value: "Perso-Arabic",
            Language.KOK.value: "Devanagari",
            Language.DOI.value: "Devanagari",
            Language.MNI.value: "Meitei",
            Language.SAT.value: "Ol Chiki",
            Language.BO.value: "Devanagari",
            Language.KS.value: "Perso-Arabic",
        }
        return scripts.get(self.value, "Unknown")

    @property
    def name_english(self) -> str:
        """Return English name of the language."""
        names = {
            Language.HI.value: "Hindi",
            Language.EN.value: "English",
            Language.BN.value: "Bengali",
            Language.TE.value: "Telugu",
            Language.MR.value: "Marathi",
            Language.TA.value: "Tamil",
            Language.UR.value: "Urdu",
            Language.GU.value: "Gujarati",
            Language.KN.value: "Kannada",
            Language.ML.value: "Malayalam",
            Language.OR.value: "Odia",
            Language.PA.value: "Punjabi",
            Language.AS_LANG.value: "Assamese",
            Language.MAI.value: "Maithili",
            Language.SA.value: "Sanskrit",
            Language.NE.value: "Nepali",
            Language.SD.value: "Sindhi",
            Language.KOK.value: "Konkani",
            Language.DOI.value: "Dogri",
            Language.MNI.value: "Manipuri",
            Language.SAT.value: "Santali",
            Language.BO.value: "Bodo",
            Language.KS.value: "Kashmiri",
        }
        return names.get(self.value, "Unknown")

    @property
    def is_indic(self) -> bool:
        """Return True if language uses Indic scripts."""
        return self.value != Language.EN.value and self.value != Language.UR.value and self.value != Language.SD.value and self.value != Language.KS.value
