"""Install a verified official portable Blender distribution into the job, without admin rights.
Resolve version/platform URL and checksum from Blender's official release before invoking.
"""
import argparse,os,shutil,sys
from pathlib import Path
from common import run,write_json
from prepare_assets import fetch,checked_url
from bootstrap_runtime import probe

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--url',required=True);p.add_argument('--sha256',required=True);p.add_argument('--checksum-source',required=True);a=p.parse_args()
    if checked_url(a.url).hostname!='download.blender.org':raise ValueError('Automatic executable installation only accepts download.blender.org')
    root=Path(a.job).resolve();cache=root/'.runtime/downloads'
    dmg=a.url.lower().endswith('.dmg')
    item=fetch({'id':'official-blender','url':a.url,'sha256':a.sha256,'license_verified':True,'license':'Blender GPL distribution','license_source':a.checksum_source,'max_download_bytes':2*1024**3,'extract':not dmg},cache)
    if dmg:
        if sys.platform!='darwin':raise ValueError('DMG requires macOS')
        mount=root/'.runtime/mount';mount.mkdir(parents=True,exist_ok=True)
        archive=Path(item['file']);dmg_path=archive.with_name('blender.dmg')
        if not dmg_path.exists():shutil.copyfile(archive,dmg_path)
        result=run(['hdiutil','attach',dmg_path,'-readonly','-nobrowse','-mountpoint',mount],timeout=120)
        if result.returncode:raise RuntimeError(result.stderr)
        try:
            apps=list(mount.glob('*.app'))
            if len(apps)!=1:raise RuntimeError('Expected exactly one Blender application')
            target=root/'.runtime/Blender.app'
            if not target.exists():shutil.copytree(apps[0],target,symlinks=True)
        finally:run(['hdiutil','detach',mount],timeout=60)
        binary=target/'Contents/MacOS/Blender'
    else:
        folder=Path(item['directory']);name='blender.exe' if os.name=='nt' else 'blender';found=[x for x in folder.rglob(name) if x.is_file()]
        if len(found)!=1:raise RuntimeError('Cannot uniquely locate the Blender executable')
        binary=found[0]
        if os.name!='nt':binary.chmod(binary.stat().st_mode|0o111)
    rt,err=probe('blender',[str(binary)],120)
    if not rt:raise RuntimeError('Installed distribution failed its version probe: '+str(err))
    rt['preparation']='verified official distribution in job-local runtime';rt['gui_available']=True
    write_json(root/'runtime.json',rt);print('Prepared '+str(binary))
if __name__=='__main__':main()
