"""Verify native frame provenance, encoded media and a separately authored visual review.
A successful decoder run or a high bone count alone never certifies a finished product film.
"""
from __future__ import annotations
import argparse,json,shutil
from fractions import Fraction
from pathlib import Path
from common import load_job,read_json,write_json,sha256,inside,run,fingerprint

def verify(job):
    root,spec=load_job(job);errors=[];r=spec['render'];result=read_json(root/'render-result.json');video=inside(root,result['video']);state=read_json(inside(root,result['native_manifest']));audit=read_json(root/'scene-audit.json');expected=r['frame_end']-r['frame_start']+1
    if state.get('status')!='complete' or len(state['frames'])!=expected:errors.append('Incomplete native frame sequence')
    if result.get('profile')!='final':errors.append('Preview/smoke output is not a final delivery')
    if sha256(video)!=result['sha256']:errors.append('Video changed after assembly')
    from render import stamp
    if stamp(root,spec,read_json(root/'runtime.json'))!=result['fingerprint']:errors.append('Render inputs changed after assembly')
    if audit.get('spec_sha256')!=fingerprint(spec):errors.append('Scene contract audit is stale')
    if state.get('fingerprint')!=result['fingerprint']:errors.append('Render fingerprint mismatch')
    if audit.get('scene_sha256')!=sha256(inside(root,spec['blend'])) or audit.get('status')!='passed':errors.append('Scene audit is stale or failed')
    for item in state['frames'].values():
        path=inside(inside(root,result['native_manifest']).parent,item['file'])
        if not path.exists() or sha256(path)!=item['sha256']:errors.append('Native frame is missing or changed: '+item['file']);break
    ffprobe=shutil.which('ffprobe');ffmpeg=shutil.which('ffmpeg')
    if not ffprobe or not ffmpeg:raise RuntimeError('ffprobe and ffmpeg are required for verification')
    p=run([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',video],timeout=180)
    if p.returncode:raise RuntimeError('ffprobe failed: '+p.stderr[-1000:])
    media=json.loads(p.stdout);streams=media['streams'];v=next((x for x in streams if x['codec_type']=='video'),None)
    if not v:errors.append('No video stream')
    else:
        if [v['width'],v['height']]!=[r['width'],r['height']]:errors.append('Wrong encoded dimensions')
        if Fraction(v['r_frame_rate'])!=r['fps']:errors.append('Wrong encoded fps')
        if int(v.get('nb_read_frames',v.get('nb_frames',-1)))!=expected:errors.append('Wrong decoded frame count')
    if abs(float(media['format']['duration'])-expected/r['fps'])>1/r['fps']+.06:errors.append('Duration differs from story')
    if spec.get('audio',{}).get('required') and not any(x['codec_type']=='audio' for x in streams):errors.append('Required audio missing')
    p=run([ffmpeg,'-v','error','-i',video,'-f','null','-'],timeout=max(180,int(expected/r['fps']*10)))
    if p.returncode or p.stderr.strip():errors.append('Complete decode reported errors')
    visual_path=root/'visual-review.json';visual=read_json(visual_path) if visual_path.exists() else {'status':'missing'}
    if visual.get('status')!='passed':errors.append('Agent visual review is missing or failed')
    if not visual.get('evidence'):errors.append('Visual review needs actual exported-frame/playback evidence')
    for name in visual.get('evidence',[]):
        if not inside(root,name).is_file():errors.append('Visual evidence file is missing: '+name)
    if visual.get('product_claims')!='checked':errors.append('Product-claim review was not completed')
    out={'status':'success' if not errors else 'partial','errors':errors,'video':result['video'],'video_sha256':sha256(video),'fingerprint':result['fingerprint'],'native_renderer':state['engine'],'native_device':state.get('device'),'native_frames':len(state['frames']),'media':media,'scene_audit':'scene-audit.json','visual_review':visual,'scope':spec.get('delivery_scope','complete product film'),'limitations':spec.get('limitations',[])}
    write_json(root/'delivery.json',out);return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args();r=verify(a.job);print(json.dumps({'status':r['status'],'errors':r['errors']},ensure_ascii=False));raise SystemExit(0 if r['status']=='success' else 2)
if __name__=='__main__':main()
