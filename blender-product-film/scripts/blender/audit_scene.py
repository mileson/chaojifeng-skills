"""Blender-side readback of actual rigs, weighted deformation and dependencies.
This is structural evidence only. The Agent must still inspect actual rendered images.
"""
import argparse,hashlib,json,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import bpy_args,load_job,inside,write_json,sha256,fingerprint
import bpy

def signature(obj,dg):
    e=obj.evaluated_get(dg);mesh=e.to_mesh();h=hashlib.sha256()
    try:
        for v in mesh.vertices:h.update(('%0.6f,%0.6f,%0.6f'%(v.co.x,v.co.y,v.co.z)).encode())
    finally:e.to_mesh_clear()
    return h.hexdigest()

def matrix_data(m):return [round(x,6) for row in m for x in row]

def audit(job):
    root,spec=load_job(job);bpy.context.preferences.filepaths.use_scripts_auto_execute=False;bpy.ops.wm.open_mainfile(filepath=str(inside(root,spec['blend'])),load_ui=False);s=bpy.context.scene
    errors=[];characters=[];frames=spec.get('qa',{}).get('frames') or sorted(set([s.frame_start,(s.frame_start+s.frame_end)//2,s.frame_end]))
    snapshots={};objects=spec.get('animated_objects',[])
    for f in frames:
        s.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();row={}
        for c in spec.get('characters',[]):
            rig=bpy.data.objects.get(c['rig_object']);body=bpy.data.objects.get(c['body_object'])
            if not rig or rig.type!='ARMATURE' or not body or body.type!='MESH':continue
            row[c['id']]={'mesh':signature(body,dg),'pose':{b.name:matrix_data(b.matrix) for b in rig.pose.bones},'facial':{n:matrix_data(rig.pose.bones[n].parent.matrix.inverted()@rig.pose.bones[n].matrix if rig.pose.bones[n].parent else rig.pose.bones[n].matrix) for n in c.get('facial_bones',[]) if n in rig.pose.bones}}
        row['objects']={n:matrix_data(bpy.data.objects[n].matrix_world) for n in objects if n in bpy.data.objects};snapshots[str(f)]=row
    for c in spec.get('characters',[]):
        rig=bpy.data.objects.get(c['rig_object']);body=bpy.data.objects.get(c['body_object']);name=c['id']
        if not rig or rig.type!='ARMATURE' or not body or body.type!='MESH':errors.append(name+': missing body/armature');continue
        modifier_ok=any(m.type=='ARMATURE' and m.object==rig and m.show_render for m in body.modifiers)
        deform_names={b.name for b in rig.data.bones if b.use_deform};indices={g.index for g in body.vertex_groups if g.name in deform_names};weighted=sum(any(g.group in indices and g.weight>0 for g in v.groups) for v in body.data.vertices)
        mesh_changes=len({v[name]['mesh'] for v in snapshots.values()})>1
        pose_changes=len({json.dumps(v[name]['pose'],sort_keys=True) for v in snapshots.values()})>1
        face_changes=len({json.dumps(v[name]['facial'],sort_keys=True) for v in snapshots.values()})>1
        clothing=[]
        for objname in c.get('clothing_objects',[]):
            obj=bpy.data.objects.get(objname);valid=bool(obj and obj.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig and m.show_render for m in obj.modifiers))
            if valid:
                garment_groups={g.index for g in obj.vertex_groups if g.name in deform_names}
                valid=any(g.group in garment_groups and g.weight>0 for v in obj.data.vertices for g in v.groups)
            if not valid:errors.append(name+': garment not skinned: '+objname)
            clothing.append({'object':objname,'armature_modifier':valid})
        if not modifier_ok or not weighted:errors.append(name+': no effective skinning')
        if c.get('motion_required') and not (mesh_changes and pose_changes):errors.append(name+': required skeletal deformation was not observed at QA frames')
        if c.get('facial_required'):
            if any(n not in rig.pose.bones for n in c['facial_bones']):errors.append(name+': missing required face bones')
            if not face_changes:errors.append(name+': facial bone deformation was not observed')
        characters.append({'id':name,'bones':len(rig.data.bones),'weighted_vertices':weighted,'modifier':modifier_ok,'mesh_changes':mesh_changes,'pose_changes':pose_changes,'face_changes':face_changes,'clothing':clothing})
    if spec.get('requires_humans') and not characters:errors.append('Required human characters are missing')
    if objects and not any(len({json.dumps(v['objects'].get(n)) for v in snapshots.values()})>1 for n in objects):errors.append('No required product/camera motion observed')
    for name in spec.get('required_uv_objects',[]):
        ob=bpy.data.objects.get(name)
        if not ob or ob.type!='MESH' or not ob.data.uv_layers:errors.append('Missing mesh UVs: '+name)
    dependencies=[]
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file:
            p=Path(bpy.path.abspath(image.filepath))
            dependencies.append({'path':str(p),'exists':p.is_file()})
            if not p.is_file():errors.append('Missing image dependency: '+image.name)
    result={'scene_sha256':sha256(inside(root,spec['blend'])),'spec_sha256':fingerprint(spec),'status':'passed' if not errors else 'failed','errors':errors,'characters':characters,'frames_checked':frames,'source_resolution':[s.render.resolution_x,s.render.resolution_y],'source_fps':s.render.fps,'dependencies':dependencies,'visual_review':'required separately; counters cannot certify beauty, contact, penetration or flicker'}
    write_json(root/'scene-audit.json',result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(bpy_args());r=audit(a.job);print(json.dumps(r,ensure_ascii=False),flush=True);os._exit(0 if r['status']=='passed' else 2)
if __name__=='__main__':main()
