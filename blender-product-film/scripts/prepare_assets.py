"""Fetch pinned, licensed assets into an immutable cache; reject archive traversal.
Manifest license fields record an Agent-verified source, not an automatic legal determination.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,stat,tarfile,tempfile,urllib.parse,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from common import read_json,sha256,write_json,inside

def checked_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Use a public HTTPS asset URL without embedded credentials')
    sensitive={'token','key','api_key','signature','x-amz-signature','x-amz-credential','access_token'}
    if sensitive.intersection(k.lower() for k,v in urllib.parse.parse_qsl(p.query)):raise ValueError('Do not persist signed/secret URLs. Download with an authorized connector and use a local_path asset instead.')
    return p

def safe_extract(archive,destination,max_bytes=8*1024**3):
    dest=Path(destination).resolve();dest.mkdir(parents=True,exist_ok=True)
    def path(name):
        if '\\' in name or ':' in name:raise ValueError('Non-portable archive path')
        return inside(dest,name)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>max_bytes:raise ValueError('Archive exceeds extraction budget')
            for i in z.infolist():
                path(i.filename)
                if stat.S_ISLNK(i.external_attr>>16):raise ValueError('ZIP symlinks are not accepted')
            z.extractall(dest)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as t:
            members=t.getmembers()
            if sum(i.size for i in members)>max_bytes:raise ValueError('Archive exceeds extraction budget')
            for i in members:
                p=path(i.name)
                if not (i.isfile() or i.isdir() or i.issym() or i.islnk()):raise ValueError('Unsupported TAR member')
                if i.issym():
                    if PurePosixPath(i.linkname).is_absolute():raise ValueError('Absolute symlink')
                    inside(dest,str(PurePosixPath(i.name).parent/PurePosixPath(i.linkname)))
                if i.islnk():path(i.linkname)
            # Members and link targets have been checked; this also supports Python 3.9.
            t.extractall(dest,members=members)
    else:raise ValueError('Only ZIP or TAR archives are supported')

def fetch(asset,cache):
    required=['id','sha256','license','license_source']
    if not all(asset.get(k) for k in required):raise ValueError('Asset requires id, sha256, license and license_source')
    if asset.get('license_verified') is not True or asset['license'].lower() in ('unknown','pending'):raise ValueError('Verify asset license before preparing it')
    digest=asset['sha256'].lower()
    if len(digest)!=64 or any(x not in '0123456789abcdef' for x in digest):raise ValueError('Invalid SHA256')
    base=Path(cache).resolve()/digest;base.mkdir(parents=True,exist_ok=True);blob=base/'asset.bin'
    if not blob.exists() or sha256(blob)!=digest:
        tmp=base/('download-'+str(os.getpid())+'.partial')
        try:
            if asset.get('local_path'):
                with Path(asset['local_path']).expanduser().open('rb') as src,tmp.open('wb') as dst:shutil.copyfileobj(src,dst)
            else:
                checked_url(asset['url']);limit=int(asset.get('max_download_bytes',1024**3))
                with urllib.request.urlopen(asset['url'],timeout=60) as src,tmp.open('wb') as dst:
                    checked_url(src.url);total=0
                    for block in iter(lambda:src.read(1024*1024),b''):
                        total+=len(block)
                        if total>limit:raise ValueError('Download exceeds budget')
                        dst.write(block)
            if sha256(tmp)!=digest:raise ValueError('Downloaded asset checksum mismatch')
            os.replace(tmp,blob)
        finally:
            if tmp.exists():tmp.unlink()
    directory=None
    if asset.get('extract'):
        directory=base/'unpacked'
        if not (base/'extraction.json').exists():
            temp=Path(tempfile.mkdtemp(prefix='extract-',dir=base))
            try:
                safe_extract(blob,temp,int(asset.get('max_extract_bytes',8*1024**3)))
                if directory.exists():raise ValueError('Unfinished extraction exists: inspect it before reusing this cache entry')
                os.replace(temp,directory);write_json(base/'extraction.json',{'sha256':digest})
            finally:
                if temp.exists():shutil.rmtree(temp)
    return {k:asset[k] for k in ['id','sha256','license','license_source']}|{'file':str(blob),'directory':str(directory) if directory else None}

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--cache',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=[fetch(x,a.cache) for x in read_json(a.manifest)['assets']];write_json(a.output,{'assets':result});print(json.dumps({'count':len(result),'output':a.output}))
if __name__=='__main__':main()
