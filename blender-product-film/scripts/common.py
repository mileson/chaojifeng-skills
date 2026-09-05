"""Portable job contracts, safe paths, hashing and subprocess helpers. Standard library only."""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path, PureWindowsPath

SCHEMA_VERSION=1
ENGINES={'EEVEE':'BLENDER_EEVEE_NEXT','CYCLES':'CYCLES'}

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def inside(root,relative):
    root=Path(root).resolve()
    if PureWindowsPath(str(relative)).drive:raise ValueError("Drive-qualified path is not job-relative")
    p=Path(str(relative).replace("\\", "/"))
    if p.is_absolute():raise ValueError('Expected a project-relative path: '+str(relative))
    result=(root/p).resolve()
    try:result.relative_to(root)
    except ValueError:raise ValueError('Path escapes the job directory: '+str(relative))
    return result

def run(command,timeout=120,cwd=None):
    return subprocess.run([str(x) for x in command],cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)

def validate_spec(spec):
    if spec.get('schema_version')!=SCHEMA_VERSION:raise ValueError('Unsupported scene schema_version')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',spec.get('id','')):raise ValueError('id must be a portable lowercase slug')
    product=spec.get('product',{})
    for key in ['name','positioning','audience','user_outcome']:
        if not isinstance(product.get(key),str) or not product[key].strip():raise ValueError('Missing product.'+key)
        if product[key].startswith('REPLACE_'):raise ValueError('Unfilled product template: '+key)
    r=spec.get('render',{})
    for key in ['width','height','fps','frame_start','frame_end']:
        if type(r.get(key)) is not int:raise ValueError('render.'+key+' must be an integer')
    if not 1<=r['fps']<=120 or r['width']<32 or r['height']<32 or r['width']%2 or r['height']%2:raise ValueError('Invalid native dimensions or fps')
    if r['frame_start']<1 or r['frame_end']<r['frame_start']:raise ValueError('Invalid frame range')
    if r.get('engine') not in ENGINES:raise ValueError('Choose EEVEE or CYCLES after a representative benchmark')
    if r.get('profile') not in ['preview','final','smoke']:raise ValueError('Invalid render.profile')
    if not isinstance(r.get('settings',{}),dict):raise ValueError('render.settings must be a mapping')
    if not spec.get('shots'):raise ValueError('A story needs at least one shot')
    end=r['frame_start']
    for shot in spec['shots']:
        if shot.get('start')!=end or type(shot.get('end')) is not int or shot['end']<end:raise ValueError('Shots must cover a contiguous inclusive frame range')
        for key in ['purpose','action','product_role']:
            if not shot.get(key):raise ValueError('Missing shot.'+key)
        end=shot['end']+1
    if end!=r['frame_end']+1:raise ValueError('Shots do not cover the requested duration')
    for claim in spec.get('claims',[]):
        if claim.get('status') not in ['observed','documented','concept','unknown']:raise ValueError('Invalid claim status')
        if claim['status'] in ['observed','documented'] and not claim.get('source'):raise ValueError('Verified product claims require a source')
    if spec.get('requires_humans') and not spec.get('characters'):raise ValueError('Human scenes need character contracts')
    for c in spec.get('characters',[]):
        if not all(c.get(k) for k in ['id','body_object','rig_object','motion_required']):raise ValueError('Character requires id/body/rig/motion_required')
        if c.get('facial_required') and not c.get('facial_bones'):raise ValueError('Facial validation needs named face bones')
    return spec

def load_job(job):
    root=Path(job).resolve();spec=validate_spec(read_json(root/'scene.json'));return root,spec

def blender_command(runtime,script,args=()):
    cmd=list(runtime['command'])
    if runtime['kind']=='blender':return cmd+['--background','--factory-startup','--disable-autoexec','--python',str(script),'--']+list(map(str,args))
    if runtime['kind']=='bpy':return cmd+[str(script)]+list(map(str,args))
    raise ValueError('Unknown runtime kind')

def bpy_args():
    return sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
