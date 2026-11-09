import cv2
import numpy as np

def draw_zoom(frame, box, code, confidence, locked=True):
    x1,y1,x2,y2=box
    color=(0,220,255) if locked else (255,160,0)
    cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
    label=f"{code} {confidence:.0%}"
    cv2.rectangle(frame,(x1,max(0,y1-25)),(min(frame.shape[1],x1+len(label)*10+12),y1),color,-1)
    cv2.putText(frame,label,(x1+5,max(17,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.48,(0,0,0),1,cv2.LINE_AA)
    if x2>x1 and y2>y1:
        crop=frame[y1:y2,x1:x2]
        if crop.size:
            inset_w=210; inset_h=90
            zoom=cv2.resize(crop,(inset_w,inset_h),interpolation=cv2.INTER_CUBIC)
            # Put zoom inset at lower right.
            ix=max(5,frame.shape[1]-inset_w-12); iy=max(5,frame.shape[0]-inset_h-12)
            frame[iy:iy+inset_h,ix:ix+inset_w]=zoom
            cv2.rectangle(frame,(ix,iy),(ix+inset_w,iy+inset_h),(0,220,255),2)
            cv2.putText(frame,code,(ix+4,iy+inset_h-6),cv2.FONT_HERSHEY_SIMPLEX,.42,(255,255,255),1)
    return frame

def annotate(frame, reads, states, show_zoom=True):
    out=frame.copy()
    for r in reads:
        state=states.get(r.code)
        locked=bool(state and state.locked)
        out=draw_zoom(out,r.box,r.code,r.confidence,locked) if show_zoom else out
        x1,y1,x2,y2=r.box
        if not show_zoom:
            cv2.rectangle(out,(x1,y1),(x2,y2),(0,220,255),2)
        if not locked:
            cv2.putText(out,"VERIFYING",(x1,max(18,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,180,0),1)
    if states:
        panel_x=10; panel_y=10
        cv2.rectangle(out,(panel_x,panel_y),(min(out.shape[1]-5,270),min(out.shape[0]-5,120)),(15,15,15),-1)
        cv2.putText(out,"CONTAINER CODES",(panel_x+8,panel_y+22),cv2.FONT_HERSHEY_SIMPLEX,.52,(0,220,255),1)
        for i,(code,s) in enumerate(list(states.items())[:3]):
            y=panel_y+45+i*22
            status="LOCKED" if s.locked else "VERIFYING"
            cv2.putText(out,f"{code}  {status}",(panel_x+8,y),cv2.FONT_HERSHEY_SIMPLEX,.42,(80,255,120) if s.locked else (255,180,0),1)
    return out
