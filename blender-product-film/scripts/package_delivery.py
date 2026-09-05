"""Package only an explicit job-local delivery allowlist, never vendor/runtime/private history."""
import argparse,json,zipfile
from pathlib import Path
from common import read_json,inside,sha256,write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--files',required=True,help='JSON list of job-relative deliverable files');p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.job).resolve();report=read_json(root/'delivery.json')
    if report['status']!='success':raise ValueError('Package a successful final delivery only; report partial work explicitly instead')
    names=read_json(a.files)
    if not isinstance(names,list) or not all(isinstance(x,str) for x in names):raise ValueError('files must be a JSON array of relative file paths')
    blocked={'.git','node_modules','vendor','.runtime','runtime','data','logs'}
    output=Path(a.output).resolve();paths=[]
    names=[n.replace('\\','/') for n in names]
    for name in names:
        if (root/name).is_symlink():raise ValueError('Symlink is not a delivery file')
        p=inside(root,name)
        if blocked.intersection(Path(name).parts) or p.is_symlink() or not p.is_file():raise ValueError('Unsupported delivery item: '+name)
        if p==output:raise ValueError('Archive cannot contain itself')
        paths.append((name,p))
    if report['video'] not in names or 'delivery.json' not in names:raise ValueError('Include the verified video and delivery.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,p in paths:z.write(p,Path(name).as_posix())
    print(json.dumps({'archive':str(output),'sha256':sha256(output),'files':len(paths)}))
if __name__=='__main__':main()
