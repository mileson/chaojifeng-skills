"""Small native product-object fixture demonstrating the builder contract, not a finished ad.
Copy into a job, fill scene.json, then invoke via run_blender.py. No third-party assets required.
"""
import argparse,math,os,sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--skill-root',required=True);a=p.parse_args(args)
sys.path.insert(0,str(Path(a.skill_root)/'scripts'))
from common import load_job,inside
from blender.helpers import area_light,pack_and_save
import bpy
from mathutils import Vector
root,spec=load_job(a.job);r=spec['render'];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def material(name,color,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;return m
body=material('Product ceramic',(.08,.18,.17));screen=material('Display glass',(.025,.045,.045),.2);ground=material('Studio floor',(.7,.64,.53),.65)
def cube(name,loc,size,mat,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:m=o.modifiers.new('Rounded real geometry','BEVEL');m.width=bevel;m.segments=4;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
obj=cube('Product',(0,0,.65),(1.2,.45,1.1),body);panel=cube('Display',(0,-.245,.70),(.93,.025,.62),screen,.03);panel.parent=obj;panel.matrix_parent_inverse=obj.matrix_world.inverted()
cube('Ground',(0,0,-.02),(100,100,.04),ground,0)
bpy.ops.object.camera_add(location=(3,-5,2.6));cam=bpy.context.object;cam.name='ProductCamera';cam.data.lens=52;bpy.context.scene.camera=cam
for frame,x in [(r['frame_start'],2.7),(r['frame_end'],2.1)]:
 cam.location.x=x;cam.rotation_euler=(Vector((0,0,.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)
area_light('Warm key',(-3,-4,5),(0,0,.7),650,4,(1,.82,.65));area_light('Cool rim',(3,2,3),(0,0,.7),550,3,(.5,.75,1))
s=bpy.context.scene;s.world.color=(.15,.15,.15);s.frame_start=r['frame_start'];s.frame_end=r['frame_end'];s.render.fps=r['fps'];s.render.fps_base=1;s.render.resolution_x=r['width'];s.render.resolution_y=r['height'];s.render.resolution_percentage=100;s.frame_set(r['frame_start']);pack_and_save(inside(root,spec['blend']));print('BPF_BUILDER_COMPLETE',flush=True);os._exit(0)
