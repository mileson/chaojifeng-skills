"""Native serial renderer with atomic frames, fingerprints and frame-boundary cancellation."""
import argparse,json,os,signal,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import bpy_args,read_json,write_json,sha256,inside,ENGINES
import bpy
_STOP=False

def stopped(signum,frame):
    global _STOP
    _STOP=True

def png_size(path):
    import struct
    with open(path,'rb') as f:h=f.read(24)
    if len(h)!=24 or h[:8]!=b'\x89PNG\r\n\x1a\n':return None
    return list(struct.unpack('>II',h[16:24]))

ALLOWED_SETTINGS={
 'cycles.samples','cycles.use_adaptive_sampling','cycles.adaptive_min_samples','cycles.adaptive_threshold','cycles.use_denoising',
 'cycles.max_bounces','cycles.diffuse_bounces','cycles.glossy_bounces','cycles.transparent_max_bounces','cycles.caustics_reflective','cycles.caustics_refractive',
 'eevee.taa_render_samples','eevee.use_raytracing','eevee.use_gtao','eevee.gtao_quality','eevee.shadow_ray_count','eevee.shadow_step_count','eevee.shadow_resolution_scale',
 'render.use_motion_blur','render.motion_blur_shutter','view_settings.exposure'
}

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);a=p.parse_args(bpy_args());req=read_json(a.request);root=Path(req['job']);spec=req['spec'];r=spec['render'];out=Path(req['output']);out.mkdir(parents=True,exist_ok=True)
    signal.signal(signal.SIGTERM,stopped);signal.signal(signal.SIGINT,stopped)
    bpy.context.preferences.filepaths.use_scripts_auto_execute=False;bpy.ops.wm.open_mainfile(filepath=str(inside(root,spec['blend'])),load_ui=False);s=bpy.context.scene
    if abs(s.render.fps/s.render.fps_base-r['fps'])>1e-5:raise ValueError('Source animation FPS differs from the plan; rebuild/retime the animation, not merely the output header')
    if (s.frame_start,s.frame_end)!=(r['frame_start'],r['frame_end']):raise ValueError('Source timeline differs from the complete story contract')
    s.render.engine=ENGINES[r['engine']]
    for name,value in r.get('settings',{}).items():
        if name not in ALLOWED_SETTINGS:raise ValueError('Unsupported setting key: '+name)
        family,attr=name.split('.',1);obj=getattr(s,family,None)
        if obj is None or not hasattr(obj,attr):raise ValueError('Requested setting is unavailable in this Blender: '+name)
        setattr(obj,attr,value)
    device='EEVEE graphics backend'
    if r['engine']=='CYCLES':
        choice=r.get('device','AUTO');selected=False;prefs=bpy.context.preferences.addons['cycles'].preferences
        if choice!='CPU':
            choices=['METAL','OPTIX','CUDA','HIP','ONEAPI'] if choice=='AUTO' else [choice]
            for backend in choices:
                try:
                    prefs.compute_device_type=backend;prefs.get_devices();found=[d for d in prefs.devices if d.type==backend]
                    if not found:continue
                    for d in prefs.devices:d.use=d.type==backend
                    device=backend;s.cycles.device='GPU';selected=True;break
                except (TypeError,ValueError,RuntimeError):continue
            if not selected and choice!='AUTO':raise ValueError('Explicitly requested GPU backend is unavailable: '+choice)
        if not selected:device='CPU';s.cycles.device='CPU'
    s.render.resolution_x=r['width'];s.render.resolution_y=r['height'];s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=max(1,min(int(r.get('threads',4)),os.cpu_count() or 1));s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='16';s.render.use_persistent_data=True
    # Separate snapshots for this exact render configuration; do not alter the authored source.
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'render-scene.blend'))
    path=out/'native-frames.json';state=read_json(path) if path.exists() else {'fingerprint':req['fingerprint'],'frames':{}}
    if state['fingerprint']!=req['fingerprint']:raise ValueError('Mixed render fingerprints')
    state.update(status='running',width=r['width'],height=r['height'],fps=r['fps'],engine=s.render.engine,device=device,profile=r['profile'],expected_frames=r['frame_end']-r['frame_start']+1)
    start=time.monotonic();rendered=0;frames=req.get('frames') or list(range(r['frame_start'],r['frame_end']+1));budget=spec.get('constraints',{}).get('max_render_seconds')
    for f in frames:
        if _STOP or (out/'STOP').exists():state['status']='stopped';break
        if budget and time.monotonic()-start>float(budget):state['status']='budget_paused';break
        final=out/f'frame_{f:06d}.png';record=state['frames'].get(str(f))
        if record and final.exists() and png_size(final)==[r['width'],r['height']] and sha256(final)==record['sha256']:continue
        s.frame_set(f);partial=out/f'frame_{f:06d}.partial.png';s.render.filepath=str(partial);t=time.monotonic();bpy.ops.render.render(write_still=True)
        if png_size(partial)!=[r['width'],r['height']]:raise ValueError('Native renderer produced unexpected dimensions')
        os.replace(partial,final);state['frames'][str(f)]={'file':final.name,'sha256':sha256(final),'seconds':round(time.monotonic()-t,3)};rendered+=1
        state.update(completed=len(state['frames']),session_seconds=round(time.monotonic()-start,2));write_json(path,state)
        print('BPF_FRAME '+json.dumps({'frame':f,'completed':state['completed'],'total':state['expected_frames'],'seconds':state['frames'][str(f)]['seconds']}),flush=True)
    else:
        expected=set(map(str,range(r['frame_start'],r['frame_end']+1)))
        state['status']='complete' if expected.issubset(state['frames']) else 'benchmark_complete'
    state.update(completed=len(state['frames']),session_seconds=round(time.monotonic()-start,2),rendered_this_session=rendered);write_json(path,state)
    print('BPF_RENDER '+json.dumps({'status':state['status'],'completed':state['completed'],'device':device}),flush=True)
    os._exit(0 if state['status'] in ['complete','benchmark_complete'] else 3)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        import traceback;traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(2)
