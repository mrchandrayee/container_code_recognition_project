import argparse, csv, json, os, time
from pathlib import Path
import cv2, yaml
from .ocr import ContainerOCR
from .lock import RecognitionLock
from .visualize import annotate

def load_config(path):
    with open(path,encoding="utf-8") as f: return yaml.safe_load(f)

def main():
    ap=argparse.ArgumentParser(description="Container ISO code OCR and recognition lock")
    ap.add_argument("--source",default=None,help="Video path, webcam index, or RTSP URL; overrides config")
    ap.add_argument("--config",default="config.yaml")
    args=ap.parse_args()
    cfg=load_config(args.config)
    src=args.source if args.source is not None else cfg["input"]["source"]
    src=int(src) if str(src).isdigit() else src
    cap=cv2.VideoCapture(src)
    if not cap.isOpened(): raise RuntimeError(f"Cannot open source: {src}")
    o=cfg["ocr"]; rec=cfg["recognition"]; disp=cfg["display"]; outcfg=cfg["output"]
    reader=ContainerOCR(o.get("languages",["en"]),o.get("gpu",False),o.get("min_confidence",.18))
    lock=RecognitionLock(rec.get("lock_after_hits",3),rec.get("forget_after_misses",18))
    fps=cap.get(cv2.CAP_PROP_FPS) or 25
    width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target=cfg["input"].get("resize_width",1280)
    writer=None
    if outcfg.get("save_video",True):
        path=Path(outcfg["video_path"]); path.parent.mkdir(parents=True,exist_ok=True)
        scale=min(1,target/max(width,1)); ow=int(width*scale); oh=int(height*scale)
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),fps,(ow,oh))
    interval=max(1,int(o.get("interval_frames",3)))
    reads=[]; frame_no=0; events={}
    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            frame_no+=1
            if frame.shape[1]>target:
                nh=int(frame.shape[0]*target/frame.shape[1])
                frame=cv2.resize(frame,(target,nh))
            if frame_no % interval == 0 or frame_no == 1:
                reads=reader.read(frame)
            states=lock.update(reads)
            annotated=annotate(frame,reads,states,disp.get("show_zoom_inset",True))
            if writer: writer.write(annotated)
            for code,s in states.items():
                if s.locked and code not in events:
                    events[code]={"container_code":code,"first_locked_at":time.strftime("%Y-%m-%d %H:%M:%S"),
                                  "confidence":round(s.confidence,3),"iso_format_valid":True}
            if disp.get("show_status",True):
                cv2.imshow("Container Code Recognition — press q to quit",annotated)
                if cv2.waitKey(1)&0xFF==ord("q"): break
    finally:
        cap.release()
        if writer: writer.release()
        cv2.destroyAllWindows()
        Path(outcfg["events_csv"]).parent.mkdir(parents=True,exist_ok=True)
        rows=list(events.values())
        if rows:
            with open(outcfg["events_csv"],"w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        with open(outcfg["events_json"],"w",encoding="utf-8") as f: json.dump(rows,f,indent=2)
    print(f"Recognized unique locked codes: {len(events)}")
    print(f"Events: {outcfg['events_csv']} and {outcfg['events_json']}")
    if writer: print(f"Annotated video: {outcfg['video_path']}")

if __name__=="__main__": main()
