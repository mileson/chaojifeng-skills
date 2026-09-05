"""Reuse Blender/bpy first; optionally prepare the official bpy runtime via user-scoped uv.
Writes a runtime command manifest inside the job. Never changes shell profiles or user preferences.
"""
from __future__ import annotations
import argparse,json,os,shutil,site,sys
from pathlib import Path
from common import run,write_json,read_json
from doctor import blender_candidates

EXPR="import bpy,json,os; print('BPF_RUNTIME '+json.dumps({'version':bpy.app.version_string,'version_tuple':list(bpy.app.version)}),flush=True); os._exit(0)"

def probe(kind,command,timeout=120):
    args=command+(['--background','--factory-startup','--disable-autoexec','--python-expr',EXPR] if kind=='blender' else ['-c',EXPR])
    try:p=run(args,timeout=timeout)
    except Exception as exc:
        return None,str(exc)
    for line in p.stdout.splitlines():
        if line.startswith('BPF_RUNTIME '):
            info=json.loads(line[len('BPF_RUNTIME '):])
            if info['version_tuple'][:2] < [4,5]:return None,'Blender 4.5+ required; do not change a user installation in place'
            return {'kind':kind,'command':command,**info},None
    return None,(p.stderr or p.stdout)[-1600:]

def ensure(job,blender=None,bpy_python=None,allow_install=False,bpy_version='4.5.3',python_version='3.11'):
    root=Path(job).resolve();root.mkdir(parents=True,exist_ok=True);errors=[]
    previous=root/'runtime.json'
    if previous.exists() and not blender and not bpy_python:
        old=read_json(previous);found,err=probe(old['kind'],old['command'])
        if found:
            old.update(found);write_json(previous,old);return old
        errors.append(err)
    for b in ([blender] if blender else blender_candidates()):
        rt,err=probe('blender',[str(Path(b).resolve())])
        if rt:rt['preparation']='reused Blender executable';break
        errors.append(err)
    else:rt=None
    if not rt:
        for p in list(dict.fromkeys([x for x in [bpy_python,sys.executable] if x])):
            rt,err=probe('bpy',[str(Path(p).resolve())],30)
            if rt:rt['preparation']='reused existing Python bpy';break
            errors.append(err)
    uv=shutil.which('uv')
    if not rt and uv:
        base=[uv,'run','--no-project','--python',python_version,'--with','bpy=='+bpy_version,'python']
        cached=base[:2]+['--offline']+base[2:];rt,err=probe('bpy',cached)
        if rt:rt['preparation']='reused cached uv/bpy runtime'
        else:errors.append(err)
    if not rt and allow_install:
        if not uv:
            # PyPI/user scope only. Hosts without pip should use the official archive route.
            p=run([sys.executable,'-m','pip','install','--user','uv'],timeout=300)
            candidates=[shutil.which('uv'),str(Path(site.USER_BASE)/('Scripts/uv.exe' if os.name=='nt' else 'bin/uv'))]
            uv=next((x for x in candidates if x and Path(x).is_file()),None)
            if p.returncode or not uv:raise RuntimeError('Cannot prepare uv with user-scoped pip. Use a verified official portable Blender archive; do not run an unreviewed installer. '+p.stderr[-800:])
        base=[uv,'run','--no-project','--python',python_version,'--with','bpy=='+bpy_version,'python']
        rt,err=probe('bpy',base,600)
        if rt:rt['preparation']='prepared managed Python and official bpy with uv'
        else:errors.append(err)
    if not rt:raise RuntimeError('No usable runtime. Inspect the final error, check official wheel/platform support, or use install_blender_archive.py. No GUI application was installed.\n'+'\n'.join(x for x in errors if x)[-2200:])
    rt['gui_installed_by_this_step']=False;write_json(root/'runtime.json',rt);return rt

def main():
    a=argparse.ArgumentParser();a.add_argument('--job',required=True);a.add_argument('--blender');a.add_argument('--bpy-python');a.add_argument('--allow-install',action='store_true');a.add_argument('--bpy-version',default='4.5.3');a.add_argument('--python-version',default='3.11');v=a.parse_args();print(json.dumps(ensure(v.job,v.blender,v.bpy_python,v.allow_install,v.bpy_version,v.python_version),indent=2))
if __name__=='__main__':main()
