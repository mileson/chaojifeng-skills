"""Host controller: audit, render/benchmark, stop, and assemble. One render owner per job."""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from common import load_job,read_json,write_json,sha256,fingerprint,inside,blender_command
HERE=Path(__file__).resolve().parent

def alive(pid):
    try:os.kill(int(pid),0);return True
    except ProcessLookupError:return False
    except PermissionError:return True
    except (ValueError,OSError):return False

def stamp(root,spec,runtime):
    deps={}
    for name in spec.get('dependency_files',[]):deps[name]=sha256(inside(root,name))
    audit=read_json(root/'scene-audit.json')
    for d in audit.get('dependencies',[]):
        p=Path(d['path']).resolve()
        try:rel=str(p.relative_to(root))
        except ValueError:raise ValueError('Pack assets or copy external dependencies into the job before rendering: '+p.name)
        deps[rel]=sha256(p)
    return fingerprint({'blend':sha256(inside(root,spec['blend'])),'spec':{k:v for k,v in spec.items() if k!='constraints'},'runtime':runtime,'dependencies':deps,'worker':sha256(HERE/'blender/render_worker.py')})

def invoke(root,runtime,script,args,logname):
    with (root/logname).open('w',encoding='utf-8') as log:
        p=subprocess.run(blender_command(runtime,script,args),cwd=root,stdout=log,stderr=subprocess.STDOUT)
    return p.returncode

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['audit','render','benchmark','stop','assemble']);ap.add_argument('--job',required=True);ap.add_argument('--resume',action='store_true');ap.add_argument('--recover-lock',action='store_true');ap.add_argument('--frames',help='Benchmark frame numbers, comma separated');a=ap.parse_args();root,spec=load_job(a.job);runtime=read_json(root/'runtime.json');active=root/'active-render.json'
    if a.action=='audit':
        rc=invoke(root,runtime,HERE/'blender/audit_scene.py',['--job',str(root)],'audit.log');print('Audit exit:',rc);raise SystemExit(rc)
    if a.action=='stop':
        if not active.exists():raise ValueError('No job-owned active render')
        record=read_json(active);out=inside(root,record['output']);(out/'STOP').write_text('Requested by job controller\n',encoding='utf-8');print('Stop requested at the next completed-frame boundary');return
    audit=read_json(root/'scene-audit.json')
    if audit['status']!='passed' or audit.get('scene_sha256')!=sha256(inside(root,spec['blend'])) or audit.get('spec_sha256')!=fingerprint(spec):raise ValueError('Run audit for the current scene and contract before rendering')
    fp=stamp(root,spec,runtime);out=root/'renders'/fp;out.mkdir(parents=True,exist_ok=True)
    if a.action=='assemble':
        state=read_json(out/'native-frames.json');r=spec['render'];expected=set(map(str,range(r['frame_start'],r['frame_end']+1)))
        if state.get('status')!='complete' or not expected.issubset(state['frames']):raise ValueError('Full native frame sequence is not complete')
        for f in expected:
            item=state['frames'][f]
            if sha256(inside(out,item['file']))!=item['sha256']:raise ValueError('Frame checksum changed')
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg:raise ValueError('FFmpeg missing; prepare it from an official source')
        output=root/'final.mp4';temporary=root/'final.partial.mp4';seconds=state['expected_frames']/r['fps']
        cmd=[ffmpeg,'-y','-hide_banner','-loglevel','warning','-thread_queue_size','64','-framerate',str(r['fps']),'-start_number',str(r['frame_start']),'-i',str(out/'frame_%06d.png')]
        audio=spec.get('audio',{}).get('file')
        if audio:cmd+=['-i',str(inside(root,audio)),'-map','0:v:0','-map','1:a:0']
        cmd+=['-t',str(seconds),'-c:v','libx264','-threads',str(min(4,os.cpu_count() or 1)),'-crf','17','-pix_fmt','yuv420p','-movflags','+faststart']
        if audio:cmd+=['-c:a','aac','-b:a','192k']
        cmd+=[str(temporary)]
        with (root/'encode.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        if p.returncode:raise RuntimeError('Encoding failed; inspect encode.log')
        os.replace(temporary,output);write_json(root/'render-result.json',{'fingerprint':fp,'native_manifest':str(out.relative_to(root)/'native-frames.json'),'video':'final.mp4','sha256':sha256(output),'engine':state['engine'],'profile':state['profile']});print(output);return
    if active.exists():
        old=read_json(active)
        if alive(old['owner_pid']):raise ValueError('A controller already owns this job; inspect or stop that job, do not start a duplicate')
        if not a.recover_lock:raise ValueError('Stale render lock; inspect the previous log, then use --recover-lock')
        if old.get('child_pid') and alive(old['child_pid']):raise ValueError('Previous worker may still be running; do not recover the lock yet')
        active.unlink()
    if (out/'STOP').exists():
        if not a.resume:raise ValueError('This render was stopped; explicit --resume is required')
        (out/'STOP').unlink()
    r=spec['render'];free=shutil.disk_usage(root).free;minimum=int(spec.get('constraints',{}).get('minimum_free_bytes',2*1024**3))
    if free<minimum:raise ValueError('Insufficient disk headroom; do not delete user caches automatically')
    frames=None
    if a.action=='benchmark':
        frames=[int(x) for x in (a.frames or ','.join(map(str,spec.get('qa',{}).get('frames',[r['frame_start']])))).split(',')]
        if any(f<r['frame_start'] or f>r['frame_end'] for f in frames):raise ValueError('Benchmark frame outside source timeline')
    request={'job':str(root),'spec':spec,'output':str(out),'fingerprint':fp,'frames':frames};write_json(out/'request.json',request)
    # Exclusive creation closes the race between two controllers.
    fd=os.open(active,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'owner_pid':os.getpid(),'output':str(out.relative_to(root)),'fingerprint':fp},f)
    rc=2
    try:
        with (out/'render.log').open('a',encoding='utf-8') as log:
            p=subprocess.Popen(blender_command(runtime,HERE/'blender/render_worker.py',['--request',str(out/'request.json')]),cwd=root,stdout=log,stderr=subprocess.STDOUT)
            write_json(active,{'owner_pid':os.getpid(),'child_pid':p.pid,'output':str(out.relative_to(root)),'fingerprint':fp})
            try:rc=p.wait()
            except KeyboardInterrupt:
                (out/'STOP').write_text('Controller interrupted\n');print('Waiting for current frame to finish...',flush=True);rc=p.wait()
    finally:
        if active.exists() and read_json(active).get('owner_pid')==os.getpid():active.unlink()
    print(json.dumps({'exit_code':rc,'render_dir':str(out)}));raise SystemExit(rc)
if __name__=='__main__':main()
