"""Stable, non-sensitive reason codes shared by the pipeline and API."""

from enum import StrEnum


class ReasonCode(StrEnum):
    """Machine-readable reasons without personal or score values."""

    STAGE_NOT_EVALUATED = "STAGE_NOT_EVALUATED"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    FACE_NOT_FOUND = "FACE_NOT_FOUND"
    FACE_MATCH_UNCERTAIN = "FACE_MATCH_UNCERTAIN"
    FACE_MISMATCH = "FACE_MISMATCH"
    OCR_CONFIDENCE_UNCERTAIN = "OCR_CONFIDENCE_UNCERTAIN"
    OCR_CONFIDENCE_LOW = "OCR_CONFIDENCE_LOW"
    REQUIRED_STAGE_MISSING = "REQUIRED_STAGE_MISSING"
    REQUIRED_SCORE_MISSING = "REQUIRED_SCORE_MISSING"
    STAGE_FAILED = "STAGE_FAILED"
    OCR_ID_DOB_MISMATCH = "OCR_ID_DOB_MISMATCH"


REASON_MESSAGES: dict[ReasonCode, str] = {
    ReasonCode.STAGE_NOT_EVALUATED: "A verification stage has not been evaluated.",
    ReasonCode.DOCUMENT_NOT_FOUND: "No document was found in the image.",
    ReasonCode.FACE_NOT_FOUND: "A required face was not found.",
    ReasonCode.FACE_MATCH_UNCERTAIN: "Face similarity requires manual review.",
    ReasonCode.FACE_MISMATCH: "The document and selfie faces do not match.",
    ReasonCode.OCR_CONFIDENCE_UNCERTAIN: "Text recognition requires manual review.",
    ReasonCode.OCR_CONFIDENCE_LOW: "Text recognition confidence is low.",
    ReasonCode.REQUIRED_STAGE_MISSING: "A required verification stage is missing.",
    ReasonCode.REQUIRED_SCORE_MISSING: "A required verification score is missing.",
    ReasonCode.STAGE_FAILED: "A verification stage could not produce a result.",
    ReasonCode.OCR_ID_DOB_MISMATCH: "Document fields are inconsistent.",
}
