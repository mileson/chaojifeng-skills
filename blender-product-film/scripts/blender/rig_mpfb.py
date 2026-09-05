"""Optional MPFB2 adapter, based on the actually exercised 2.0.17 / Blender 4.5 path.
Supply verified source and CC0/licensed assets from the cache; no downloads or global addon install.
"""
import importlib,shutil,sys
from pathlib import Path
import bpy
from .helpers import drive_shape
_SERVICES=None
_SOURCE=None

def register(source_dir,data_dir,asset_dir):
    global _SERVICES,_SOURCE
    source=Path(source_dir).resolve();data=Path(data_dir).resolve();assets=Path(asset_dir).resolve()
    if _SERVICES:
        if source!=_SOURCE:raise ValueError('Use one pinned MPFB source per Blender process')
        return _SERVICES
    if not (source/'mpfb/__init__.py').is_file():raise ValueError('source_dir must contain the mpfb package')
    data.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(source))
    import mpfb
    from mpfb._preferences import MpfbPreferences
    # A fresh headless process is required; never reconfigure a user's running addon.
    if 'mpfb' in bpy.context.preferences.addons:raise ValueError('Use a fresh factory/background runtime for the task-local MPFB adapter')
    bpy.utils.register_class(MpfbPreferences);addon=bpy.context.preferences.addons.new();addon.module='mpfb';addon.preferences.mpfb_user_data=str(data)
    old=bpy.utils.extension_path_user
    bpy.utils.extension_path_user=lambda package,**kw:str(data) if package=='mpfb' else old(package,**kw)
    try:mpfb.register()
    finally:bpy.utils.extension_path_user=old
    from mpfb.services import HumanService,TargetService,FaceService,LocationService
    addon.preferences.mpfb_second_root=str(assets);LocationService.update_second_root()
    _SOURCE=source;_SERVICES=(HumanService,TargetService,FaceService);return _SERVICES

def create_character(spec,source_dir,data_dir,asset_dir,face_targets_dir=None):
    """Create real weighted bodies/clothes. Author scenario-specific actions separately."""
    Human,Target,Face=register(source_dir,data_dir,asset_dir);assets=Path(asset_dir).resolve();before=set(bpy.context.scene.objects)
    macro=Target.get_default_macro_info_dict()
    # MPFB's source macro.json establishes 0=female, 1=male; do not trust inverted sample comments.
    for k,v in spec.get('phenotype',{}).items():
        if k not in macro:raise ValueError('Unknown MPFB phenotype '+k)
        macro[k]=v
    h=Human.create_human(macro_detail_dict=macro);h.name=spec.get('body_object','Char.'+spec['id']+'.Body');bpy.context.view_layer.update();rest_height=h.dimensions.z
    rig=Human.add_builtin_rig(h,'default');rig.name=spec.get('rig_object','Char.'+spec['id']+'.Rig')
    rig['bpf_character']=spec['id'];h['bpf_character']=spec['id'];h['bpf_role']='body';loaded=[]
    for i,item in enumerate(spec.get('assets',[])):
        path=(assets/item['path']).resolve()
        try:path.relative_to(assets)
        except ValueError:raise ValueError('Asset path escapes its verified root')
        if not path.is_file():raise FileNotFoundError(path)
        if item['kind']=='skin':Human.set_character_skin(str(path),h,skin_type='MAKESKIN');continue
        o=Human.add_mhclo_asset(str(path),h,asset_type=item['kind'],subdiv_levels=1,interpolate_weights=True)
        o.name='Char.'+spec['id']+'.'+item['kind']+'.'+str(i);o['bpf_character']=spec['id'];o['bpf_role']=item['kind'];loaded.append(o)
    expressions=spec.get('expressions',[])
    if expressions:
        if not face_targets_dir:raise ValueError('Provide the verified face-target pack')
        dest=Path(data_dir)/'data/targets/faceunits';dest.mkdir(parents=True,exist_ok=True)
        for name in expressions:
            if '/' in name or '\\' in name or '..' in name:raise ValueError('Expression must be a target basename')
            p=Path(face_targets_dir)/(name+'.target')
            if not p.is_file():raise FileNotFoundError(p)
            shutil.copyfile(p,dest/p.name)
        Target.bulk_load_targets(h,[{'target':n,'value':0} for n in expressions]);Face.interpolate_targets(h)
        keys=h.data.shape_keys.key_blocks
        if any(n not in keys for n in expressions):raise ValueError('Required facial targets did not load')
        for o in [h]+loaded:
            if not o.data.shape_keys:continue
            for name in expressions:
                if name not in o.data.shape_keys.key_blocks:continue
                prop='blink' if 'eyeBlink' in name else ('smile' if 'mouthSmile' in name or 'cheekSquint' in name else name)
                drive_shape(o,name,rig,'head',prop,.22 if 'cheekSquint' in name else 1)
    bpy.context.view_layer.update();height=float(spec.get('height',1.75))
    if rest_height<=0:raise ValueError('Invalid base-mesh height')
    rig.scale=(height/rest_height,)*3;rig.location=spec.get('position',[0,0,0]);rig.rotation_euler.z=float(spec.get('rotation_z',0))
    for o in set(bpy.context.scene.objects)-before:
        if o.type=='MESH':
            for p in o.data.polygons:p.use_smooth=True
    return {'body':h,'rig':rig,'assets':loaded,'rest_height':rest_height}
