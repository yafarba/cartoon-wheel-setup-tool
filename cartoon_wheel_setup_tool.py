import maya.cmds as cmds
import math

# ==============================================================================
# Create the main user interface
# ==============================================================================

def create_cartoon_wheel_ui():
    window_id = "cartoonWheelSetupUI"
    
    if cmds.window(window_id, exists=True):
        cmds.deleteUI(window_id)
        
    window = cmds.window(window_id, title="Cartoon Wheel Setup", widthHeight=(440, 210), sizeable=True)
    main_form = cmds.formLayout()
    
    title_text = cmds.text(label="Cartoon Wheel Settings", font="boldLabelFont", align="center", height=25)
    sep_top = cmds.separator(height=2, style="in")
    
    sliders_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    joints_field = cmds.intSliderGrp(label="Joints Count: ", min=4, max=64, value=24, field=True, columnWidth3=[150, 50, 150], columnAlign3=["left", "left", "left"])
    sections_field = cmds.intSliderGrp(label="Curve Sections: ", min=4, max=32, value=12, field=True, columnWidth3=[150, 50, 150], columnAlign3=["left", "left", "left"])
    radius_field = cmds.floatSliderGrp(label="Tire Radius: ", min=0.1, max=10.0, value=2.5, field=True, step=0.1, columnWidth3=[150, 50, 150], columnAlign3=["left", "left", "left"])
    cmds.setParent('..')
    
    squash_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=[150, 200], height=22)
    cmds.text(label="")
    squash_check = cmds.checkBox(label="Add Squash and Stretch deformation", value=False)
    cmds.setParent('..')
    
    help_text = cmds.text(
        label="* Selection order matters:\nSelect the TIRE first, then select all rigid parts (rim, bolts, etc.)", 
        align="center", 
        font="obliqueLabelFont",
        height=30
    )
    
    create_btn = cmds.button(
        label="Create Rig",
        height=40,
        backgroundColor=[0.25, 0.4, 0.5],
        command=lambda x: run_cluster_rig_from_ui(joints_field, radius_field, sections_field, squash_check)
    )
    
    cmds.formLayout(main_form, edit=True,
        attachForm=[
            (title_text, 'top', 10), (title_text, 'left', 10), (title_text, 'right', 10),
            (sep_top, 'left', 10), (sep_top, 'right', 10),
            (sliders_layout, 'left', 20), (sliders_layout, 'right', 10),
            (squash_layout, 'left', 20), (squash_layout, 'right', 10),
            (help_text, 'left', 10), (help_text, 'right', 10),
            (create_btn, 'bottom', 10), (create_btn, 'left', 10), (create_btn, 'right', 10)
        ],
        attachControl=[
            (sep_top, 'top', 2, title_text),
            (sliders_layout, 'top', 15, sep_top),
            (squash_layout, 'top', 4, sliders_layout),
            (help_text, 'top', 10, squash_layout),
            (create_btn, 'top', 5, help_text)
        ]
    )
    
    cmds.showWindow(window)

# ==============================================================================
# Read UI values and build the complete wheel rig
# ==============================================================================

def run_cluster_rig_from_ui(joints_f, radius_f, sections_f, squash_c):
    num_joints = cmds.intSliderGrp(joints_f, q=True, value=True)
    custom_radius = cmds.floatSliderGrp(radius_f, q=True, value=True)
    curve_sections = cmds.intSliderGrp(sections_f, q=True, value=True)
    use_squash = cmds.checkBox(squash_c, q=True, value=True)
    
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.confirmDialog(title="Error", message="Please select the wheel GEOMETRY first!", button=["OK"])
        return
        
    meshes = []
    for obj in selection:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        if shapes and cmds.nodeType(shapes[0]) == "mesh":
            meshes.append(obj)
            
    if not meshes:
        cmds.warning("Please select at least one polygon mesh.")
        return
        
    wheel_mesh = meshes[0]
    
    all_bboxes = [cmds.exactWorldBoundingBox(m) for m in meshes]
    xmin = min(b[0] for b in all_bboxes)
    ymin = min(b[1] for b in all_bboxes)
    zmin = min(b[2] for b in all_bboxes)
    xmax = max(b[3] for b in all_bboxes)
    ymax = max(b[4] for b in all_bboxes)
    zmax = max(b[5] for b in all_bboxes)
    
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    cz = (zmin + zmax) / 2.0
    
    # --------------------------------------------------------------------------
    # Create the spline curve used by the IK chain
    # --------------------------------------------------------------------------
    path_curve = cmds.circle(r=custom_radius, nr=(1, 0, 0), d=3, ut=0, s=curve_sections, ch=False, n=f"{wheel_mesh}_OpenPath_CRV")[0]
    cmds.xform(path_curve, ws=True, t=(cx, cy, cz))
    cmds.rotate(0, 0, 0, path_curve)
    cmds.makeIdentity(path_curve, apply=True, t=1, r=1, s=1, n=0)
    
    cmds.select(cl=True)
    wheel_joints = []
    for i in range(num_joints + 1):
        angle = (float(i) / num_joints) * 2 * math.pi
        x = cx
        y = cy + custom_radius * math.sin(angle)
        z = cz + custom_radius * math.cos(angle)
        
        jnt = cmds.joint(p=(x, y, z), n=f"{wheel_mesh}_IKSpline_{i}_JNT")
        wheel_joints.append(jnt)
        
    ik_nodes = cmds.ikHandle(sj=wheel_joints[0], ee=wheel_joints[-1], c=path_curve, ccv=False, pcv=False, sol="ikSplineSolver", n=f"{wheel_mesh}_IKHandle")
    ik_handle = ik_nodes[0]
    cmds.setAttr(f"{ik_handle}.visibility", False)
    
    for m in meshes:
        cmds.skinCluster(wheel_joints[:-1], m, tsb=True, bm=0, nw=1, wd=2)
        
    cv_count = cmds.getAttr(f"{path_curve}.spans") + cmds.getAttr(f"{path_curve}.degree")
    all_ctrl_groups = []
    all_cluster_handles = []
    
    # --------------------------------------------------------------------------
    # Create clusters and animation controls for each curve CV
    # --------------------------------------------------------------------------
    for i in range(cv_count):
        cv_string = f"{path_curve}.cv[{i}]"
        cv_pos = cmds.xform(cv_string, q=True, ws=True, t=True)
        
        cluster_nodes = cmds.cluster(cv_string, n=f"{wheel_mesh}_CV_{i}_Cluster")
        cluster_handle = cluster_nodes[1]
        cmds.setAttr(f"{cluster_handle}.visibility", False)
        all_cluster_handles.append(cluster_handle)
        
        ctrl = cmds.circle(r=custom_radius*0.15, nr=(1, 0, 0), ch=False, n=f"{wheel_mesh}_Form_{i}_CTRL")[0]
        cmds.setAttr(f"{ctrl}.overrideEnabled", 1)
        cmds.setAttr(f"{ctrl}.overrideColor", 17)
        
        ctrl_grp = cmds.group(ctrl, n=f"{ctrl}_GRP")
        cmds.xform(ctrl_grp, ws=True, t=cv_pos)
        
        cmds.delete(ctrl, ch=True)
        cmds.makeIdentity(ctrl, apply=True, t=1, r=1, s=1, n=0)
        
        cmds.connectAttr(f"{ctrl}.translate", f"{cluster_handle}.translate")
        cmds.connectAttr(f"{ctrl}.rotate", f"{cluster_handle}.rotate")
        cmds.connectAttr(f"{ctrl}.scale", f"{cluster_handle}.scale")
        
        all_ctrl_groups.append(ctrl_grp)
        
    clusters_grp = cmds.group(all_cluster_handles, n=f"{wheel_mesh}_CLS_GRP")
    cmds.setAttr(f"{clusters_grp}.visibility", False)
    
    controls_main_grp = cmds.group(all_ctrl_groups, n=f"{wheel_mesh}_FormControls_GRP")
    
    # --------------------------------------------------------------------------
    # Create the main wheel controller
    # --------------------------------------------------------------------------
    main_ctrl = cmds.circle(r=custom_radius*1.5, nr=(1, 0, 0), ch=False, n=f"{wheel_mesh}_Main_CTRL")[0]
    cmds.setAttr(f"{main_ctrl}.overrideEnabled", 1)
    cmds.setAttr(f"{main_ctrl}.overrideColor", 13)
    
    main_ctrl_grp = cmds.group(main_ctrl, n=f"{main_ctrl}_GRP")
    cmds.xform(main_ctrl_grp, ws=True, t=(cx, cy, cz))
    
    cmds.delete(main_ctrl, ch=True)
    cmds.makeIdentity(main_ctrl, apply=True, t=1, r=1, s=1, n=0)
    
    cmds.group(path_curve, controls_main_grp, wheel_joints[0], ik_handle, n=f"{wheel_mesh}_Cartoon_Rig_GRP")
    cmds.parent(f"{wheel_mesh}_Cartoon_Rig_GRP", main_ctrl)
    
    # --------------------------------------------------------------------------
    # Drive wheel rotation using the custom attribute
    # --------------------------------------------------------------------------
    cmds.addAttr(main_ctrl, ln="wheelRotate", sn="wRot", at="double", k=True)
    conversion_node = cmds.createNode("multiplyDivide", n=f"{wheel_mesh}_RotationToOffset_MD")
    cmds.setAttr(f"{conversion_node}.operation", 2)
    cmds.setAttr(f"{conversion_node}.input2X", 360.0)
    cmds.connectAttr(f"{main_ctrl}.wheelRotate", f"{conversion_node}.input1X")
    
    multiplier_node = cmds.createNode("multiplyDivide", n=f"{wheel_mesh}_OffsetMultiplier_MD")
    cmds.setAttr(f"{multiplier_node}.operation", 1)
    cmds.setAttr(f"{multiplier_node}.input2X", float(curve_sections))
    
    cmds.connectAttr(f"{conversion_node}.outputX", f"{multiplier_node}.input1X")
    cmds.connectAttr(f"{multiplier_node}.outputX", f"{ik_handle}.offset")
    
    # --------------------------------------------------------------------------
    # Optional squash & stretch setup
    # --------------------------------------------------------------------------
    if use_squash:
        
        flare_nodes = cmds.nonLinear(meshes, type='flare', n=f"{wheel_mesh}_Squash_FLR")
        flare_deformer = flare_nodes[0]
        flare_handle = flare_nodes[1]
        
        cmds.xform(flare_handle, ws=True, t=(cx, cy, cz))
        deform_main_grp = cmds.group(flare_handle, n=f"{wheel_mesh}_Deform_GRP")
        cmds.setAttr(f"{deform_main_grp}.visibility", False)
        
        cmds.parentConstraint(main_ctrl, flare_handle, mo=True, n=f"{flare_handle}_parentConstraint1")
        cmds.scaleConstraint(main_ctrl, flare_handle, mo=True, n=f"{flare_handle}_scaleConstraint1")
        
        cmds.addAttr(main_ctrl, ln="lowPartDeformX", sn="lpdX", at="double", dv=1.0, k=True)
        cmds.addAttr(main_ctrl, ln="lowPartDeformZ", sn="lpdZ", at="double", dv=1.0, k=True)
        cmds.addAttr(main_ctrl, ln="topPartDeformX", sn="tpdX", at="double", dv=1.0, k=True)
        cmds.addAttr(main_ctrl, ln="topPartDeformZ", sn="tpdZ", at="double", dv=1.0, k=True)
        cmds.addAttr(main_ctrl, ln="middlePartDeform", sn="mpd", at="double", dv=0.0, k=True)
        
        cmds.connectAttr(f"{main_ctrl}.lowPartDeformX", f"{flare_deformer}.startFlareX")
        cmds.connectAttr(f"{main_ctrl}.lowPartDeformZ", f"{flare_deformer}.startFlareZ")
        cmds.connectAttr(f"{main_ctrl}.topPartDeformX", f"{flare_deformer}.endFlareX")
        cmds.connectAttr(f"{main_ctrl}.topPartDeformZ", f"{flare_deformer}.endFlareZ")
        cmds.connectAttr(f"{main_ctrl}.middlePartDeform", f"{flare_deformer}.curve")
        
    print(f"Cartoon Rig ready for: {wheel_mesh} ")

# =============================================================================================
# Launch tool UI
# =============================================================================================

def onMayaDroppedPythonFile(*args, **kwargs):
    
    create_cartoon_wheel_ui()
    return True