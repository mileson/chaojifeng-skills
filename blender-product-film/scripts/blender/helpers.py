"""Reusable native geometry/material/contact helpers. No character billboards or model claims."""
import json,math
from pathlib import Path
import bpy
from mathutils import Vector

def uv_albedo(material,image_path,scale=(1,1,1),offset=(0,0,0),uv_map='UVMap'):
    """Connect an image to existing mesh UVs; retain the rest of the PBR node tree."""
    image=bpy.data.images.load(str(Path(image_path).resolve()),check_existing=True);image.pack();material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links;bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs is None:raise ValueError('Expected an existing Principled BSDF')
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uv_map;mapping=nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=scale;mapping.inputs['Location'].default_value=offset
    tex=nodes.new('ShaderNodeTexImage');tex.image=image;links.new(uv.outputs['UV'],mapping.inputs['Vector']);links.new(mapping.outputs['Vector'],tex.inputs['Vector']);links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return tex

def normalize_prop_basis(root,reference):
    """Call BEFORE placing a prop or authoring contacts. Normalize around its actual mesh basis."""
    if reference.parent!=root:raise ValueError('Reference must be a direct child of the prop root')
    if root.get('bpf_basis_normalized'):return
    bpy.context.view_layer.update();basis=reference.matrix_local.copy()
    for child in list(root.children):child.matrix_local=basis.inverted()@child.matrix_local
    root['bpf_basis_normalized']=True;bpy.context.view_layer.update()

def add_ik(rig,tip_bone,target,chain_count,pole=None,pole_angle=0):
    if rig.type!='ARMATURE' or tip_bone not in rig.pose.bones:raise ValueError('Missing real armature/tip bone')
    bone=rig.pose.bones[tip_bone];available=1;parent=bone.parent
    while parent:available+=1;parent=parent.parent
    if not 1<=chain_count<=available:raise ValueError('Invalid IK chain length')
    con=bone.constraints.new('IK');con.name='BPF contact IK';con.target=target;con.chain_count=chain_count;con.use_stretch=False;con.iterations=80
    if pole:con.pole_target=pole;con.pole_angle=pole_angle
    return con

def calibrate_pole(rig,constraint,elbow_bone,desired_world,samples=16):
    """Fit this rig's pole angle numerically; do not assume the example's -90 degrees."""
    best=None
    for i in range(samples):
        a=-math.pi+i*2*math.pi/samples;constraint.pole_angle=a;bpy.context.view_layer.update()
        error=(rig.matrix_world@rig.pose.bones[elbow_bone].head-Vector(desired_world)).length
        if best is None or error<best[0]:best=(error,a)
    constraint.pole_angle=best[1];bpy.context.view_layer.update();return {'distance':best[0],'pole_angle':best[1]}

def drive_shape(mesh,key_name,rig,bone_name,property_name,strength=1.0):
    if not mesh.data.shape_keys or key_name not in mesh.data.shape_keys.key_blocks:raise ValueError('Missing corrective shape '+key_name)
    if bone_name not in rig.pose.bones:raise ValueError('Missing facial control bone')
    bone=rig.pose.bones[bone_name]
    if property_name not in bone:bone[property_name]=0.0
    d=mesh.data.shape_keys.key_blocks[key_name].driver_add('value').driver
    while d.variables:d.variables.remove(d.variables[0])
    var=d.variables.new();var.name='control';var.type='SINGLE_PROP';var.targets[0].id=rig;var.targets[0].data_path='pose.bones['+json.dumps(bone_name)+']['+json.dumps(property_name)+']';d.expression='control*'+str(float(strength))

def area_light(name,position,target,power,size,color):
    bpy.ops.object.light_add(type='AREA',location=position);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def pack_and_save(path):
    """Keep texture/font dependencies portable; unsupported external videos must be declared separately."""
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(path).resolve()))
