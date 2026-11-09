import cv2
import numpy as np
from dataclasses import dataclass
from .iso6346 import find_candidates, normalize_code, is_iso6346_format, validate_check_digit

@dataclass
class PlateRead:
    code: str
    confidence: float
    box: tuple
    valid_format: bool
    valid_check_digit: bool

class ContainerOCR:
    def __init__(self, languages=None, gpu=False, min_confidence=0.18):
        import easyocr
        self.reader = easyocr.Reader(languages or ["en"], gpu=gpu)
        self.min_confidence = min_confidence

    @staticmethod
    def preprocess(frame):
        # CLAHE helps contrast on painted/aged container markings.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def read(self, frame):
        prepared = self.preprocess(frame)
        results = self.reader.readtext(
            prepared, detail=1, paragraph=False,
            text_threshold=0.55, low_text=0.25, link_threshold=0.35
        )
        reads=[]
        for box,text,conf in results:
            if float(conf) < self.min_confidence:
                continue
            candidates=find_candidates(text)
            # A text box may contain the full code with spaces or separators.
            compact=normalize_code(text)
            if not candidates and len(compact) >= 10:
                candidates=find_candidates(compact)
            for code in candidates:
                pts=np.asarray(box,dtype=np.int32)
                x1=max(0,int(pts[:,0].min())); y1=max(0,int(pts[:,1].min()))
                x2=min(frame.shape[1],int(pts[:,0].max())); y2=min(frame.shape[0],int(pts[:,1].max()))
                if x2>x1 and y2>y1:
                    reads.append(PlateRead(code,float(conf),(x1,y1,x2,y2),
                                           is_iso6346_format(code),validate_check_digit(code)))
        # Keep highest confidence duplicate.
        unique={}
        for item in reads:
            if item.code not in unique or item.confidence>unique[item.code].confidence:
                unique[item.code]=item
        return list(unique.values())
