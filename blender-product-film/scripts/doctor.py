"""Read-only runtime/resource discovery. Does not install packages or launch a renderer."""
from __future__ import annotations
import argparse,glob,importlib.util,os,platform,shutil,sys,subprocess
from pathlib import Path
from common import run,write_json

def blender_candidates():
    values=[shutil.which('blender')]
    if sys.platform=='darwin':values += ['/Applications/Blender.app/Contents/MacOS/Blender',str(Path.home()/'Applications/Blender.app/Contents/MacOS/Blender')]
    if os.name=='nt':
        for base in [os.environ.get('PROGRAMFILES'),os.environ.get('LOCALAPPDATA')]:
            if base:values += glob.glob(str(Path(base)/'Blender Foundation/Blender */blender.exe'))
    return list(dict.fromkeys(str(Path(x).resolve()) for x in values if x and Path(x).is_file()))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',default='.');ap.add_argument('--output');a=ap.parse_args()
    root=Path(a.workspace).resolve();disk=shutil.disk_usage(root);installed=[]
    for candidate in blender_candidates():
        try:
            p=run([candidate,'--version'],timeout=20);installed.append({'path':candidate,'version_line':p.stdout.splitlines()[0] if p.returncode==0 and p.stdout else None})
        except (OSError,subprocess.TimeoutExpired):installed.append({'path':candidate,'version_line':None})
    data={'platform':platform.system(),'architecture':platform.machine(),'python':sys.version.split()[0],'cpu_count':os.cpu_count(),'disk_free_bytes':disk.free,'blender':installed,'current_python_has_bpy':importlib.util.find_spec('bpy') is not None,'tools':{x:shutil.which(x) for x in ['uv','ffmpeg','ffprobe','node','npm']},'native_imagegen':'agent_must_check_tool_availability','gpu':'probe in the selected Blender runtime, not inferred from model name','active_resources':'agent must inspect ownership and pressure before heavy work','tested_platform_note':'Only macOS ARM64 has been exercised by the originating workflow; other hosts require their own smoke run.'}
    if a.output:write_json(a.output,data)
    import json;print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
