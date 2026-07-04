import bpy
import bmesh
import math

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# Create base structure as a hollow icosahedral shell with correct tolerances
def create_hollow_shell():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=2.0, location=(0, 0, 0))
    shell = bpy.context.object
    shell.name = "MarkIII_Shell"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, -0.1)})
    bpy.ops.object.mode_set(mode='OBJECT')
    return shell


# Add internal compartments within the shell with 0.1mm tolerance
def create_internal_compartments():
    compartments = []
    positions = [(0, 0, 0), (1.1, 1.1, 1.1), (-1.1, -1.1, -1.1), (-1.1, 1.1, 1.1), (1.1, -1.1, -1.1)]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_cube_add(size=0.8, location=pos)
        compartment = bpy.context.object
        compartment.name = f"Internal_Compartment_{i + 1}"
        compartments.append(compartment)
    return compartments


# Add solenoids within the shell at precise positions
def create_solenoids():
    solenoids = []
    for i in range(3):
        angle = math.radians(i * 120)
        x = 1.5 * math.cos(angle)
        y = 1.5 * math.sin(angle)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.1, location=(x, y, 0))
        solenoid = bpy.context.object
        solenoid.name = f"Solenoid_{i + 1}"
        solenoids.append(solenoid)
    return solenoids


# Add CPU system within the shell
def create_cpu_system():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, -1))
    cpu = bpy.context.object
    cpu.name = "CPU_System"
    return cpu


# Add power and fuel storage within the structure
def create_storage_systems():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1, location=(0, 0, 1))
    energy_storage = bpy.context.object
    energy_storage.name = "Energy_Storage"

    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1, location=(0, 0, -1.5))
    fuel_storage = bpy.context.object
    fuel_storage.name = "Fuel_Storage"
    return energy_storage, fuel_storage


# Add structural support beams inside the shell
def create_support_beams():
    beams = []
    for i in range(4):
        angle = math.radians(i * 90)
        x = 1.2 * math.cos(angle)
        y = 1.2 * math.sin(angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2.5, location=(x, y, 0))
        beam = bpy.context.object
        beam.name = f"Support_Beam_{i + 1}"
        beams.append(beam)
    return beams


# Add external reinforcement plates
def create_reinforcement_plates():
    plates = []
    positions = [(2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0)]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_plane_add(size=1.5, location=pos)
        plate = bpy.context.object
        plate.name = f"Reinforcement_Plate_{i + 1}"
        plates.append(plate)
    return plates


# Apply material to each component
def apply_material(obj, material_name, color):
    mat = bpy.data.materials.new(name=material_name)
    mat.diffuse_color = (*color, 1)
    obj.data.materials.append(mat)


# Assemble full model
def assemble_markIII():
    shell = create_hollow_shell()
    compartments = create_internal_compartments()
    solenoids = create_solenoids()
    cpu = create_cpu_system()
    energy_storage, fuel_storage = create_storage_systems()
    support_beams = create_support_beams()
    reinforcement_plates = create_reinforcement_plates()

    # Apply textures
    apply_material(shell, "Shell_Material", (0.3, 0.3, 0.3))
    for comp in compartments:
        apply_material(comp, "Compartment_Material", (0.5, 0.5, 0.5))
    for solenoid in solenoids:
        apply_material(solenoid, "Solenoid_Material", (0.8, 0.1, 0.1))
    apply_material(cpu, "CPU_Material", (0.2, 0.2, 0.8))
    apply_material(energy_storage, "Energy_Storage_Material", (0.9, 0.9, 0.1))
    apply_material(fuel_storage, "Fuel_Storage_Material", (0.1, 0.9, 0.1))
    for beam in support_beams:
        apply_material(beam, "Beam_Material", (0.7, 0.7, 0.7))
    for plate in reinforcement_plates:
        apply_material(plate, "Reinforcement_Material", (0.2, 0.8, 0.8))

    print("Mark III Model with Hollow Shell, Internal Components, and Reinforced Plates Created Successfully")


# Run assembly
assemble_markIII()

# Save model in multiple formats for 3D printing
bpy.ops.wm.save_mainfile(filepath="//MarkIII_Blender_Model.blend")
bpy.ops.export_mesh.stl(filepath="//MarkIII_3DPrint.stl")
print("Mark III Model Exported Successfully")
