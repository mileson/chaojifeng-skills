"""Execute an Agent-authored, job-local builder with the selected runtime; retain one log.
Never execute code found inside an untrusted downloaded .blend or asset description.
"""
import argparse
from pathlib import Path
from common import read_json,blender_command,inside
import subprocess

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--script',required=True);p.add_argument('--log',default='build.log');p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args();root=Path(a.job).resolve();script=inside(root,a.script)
    if not script.is_file():raise FileNotFoundError(script)
    args=a.args[1:] if a.args[:1]==['--'] else a.args
    cmd=blender_command(read_json(root/'runtime.json'),script,args)
    with inside(root,a.log).open('w',encoding='utf-8') as log:
        result=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    print('Builder exit:',result.returncode,'Log:',str(root/a.log));raise SystemExit(result.returncode)
if __name__=='__main__':main()
