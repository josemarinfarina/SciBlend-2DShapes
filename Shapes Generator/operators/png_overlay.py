import bpy
import numpy as np
from bpy.types import Operator
from ..utils.shape_generator import generate_shape

class SHAPESGENERATOR_OT_UpdateShapes(Operator):
    bl_idname = "shapesgenerator.update_shapes"
    bl_label = "Update Shapes"

    def execute(self, context):
        scene = context.scene
        print("Starting SHAPESGENERATOR_OT_UpdateShapes")
        
        if not scene.use_nodes:
            scene.use_nodes = True
        tree = scene.node_tree
        print(f"Node tree obtained: {tree}")

        composite = tree.nodes.get("Composite")
        if not composite:
            composite = tree.nodes.new(type='CompositorNodeComposite')
        print(f"Composite Node: {composite}")

        preexisting_alpha_over = tree.nodes.get("Alpha Over")  
        if not preexisting_alpha_over:
            print("No preexisting Alpha Over node found.")
        else:
            print(f"Preexisting Alpha Over node found: {preexisting_alpha_over.name}")

        main_alpha_over = tree.nodes.get("ShapesGenerator_MainAlphaOver")
        if not main_alpha_over:
            main_alpha_over = tree.nodes.new(type='CompositorNodeAlphaOver')
            main_alpha_over.name = "ShapesGenerator_MainAlphaOver"
            main_alpha_over.location = (composite.location.x - 200, composite.location.y)

        if preexisting_alpha_over:
            if preexisting_alpha_over.inputs[1].links:
                tree.links.remove(preexisting_alpha_over.inputs[1].links[0])
            tree.links.new(main_alpha_over.outputs[0], preexisting_alpha_over.inputs[1])
            print(f"Connected {main_alpha_over.name} to {preexisting_alpha_over.name} as input 1")
        else:
            if composite.inputs['Image'].links:
                tree.links.remove(composite.inputs['Image'].links[0])
            tree.links.new(main_alpha_over.outputs[0], composite.inputs['Image'])
            print(f"Connected {main_alpha_over.name} directly to {composite.name}")

        render_layers = tree.nodes.get("Render Layers")
        if not render_layers:
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
        
        if not main_alpha_over.inputs[1].links:
            tree.links.new(render_layers.outputs['Image'], main_alpha_over.inputs[1])

        shapes = scene.shapesgenerator_shapes
        existing_nodes = [node for node in tree.nodes if node.name.startswith("ShapesGenerator_") and node != main_alpha_over]
        
        node_spacing_x = 800  
        node_spacing_y = -600  
        start_x = 0
        start_y = 0

        render_layers.location = (start_x, start_y + node_spacing_y * -2)  # Multiplicamos por -2 para moverlo hacia arriba

        main_alpha_over.location = (composite.location.x - node_spacing_x, composite.location.y)

        for i, shape in enumerate(shapes):
            print(f"Processing shape {i+1}: {shape.name}, Type: {shape.shape_type}")
            
            image_node = tree.nodes.get(f"ShapesGenerator_Image_{i}")
            if not image_node:
                image_node = tree.nodes.new(type='CompositorNodeImage')
                image_node.name = f"ShapesGenerator_Image_{i}"
            
            scale_node = tree.nodes.get(f"ShapesGenerator_Scale_{i}")
            if not scale_node:
                scale_node = tree.nodes.new(type='CompositorNodeScale')
                scale_node.name = f"ShapesGenerator_Scale_{i}"
            scale_node.space = 'RENDER_SIZE'
            scale_node.frame_method = 'CROP'
            
            transform_node = tree.nodes.get(f"ShapesGenerator_Transform_{i}")
            if not transform_node:
                transform_node = tree.nodes.new(type='CompositorNodeTransform')
                transform_node.name = f"ShapesGenerator_Transform_{i}"
            
            alpha_over_node = tree.nodes.get(f"ShapesGenerator_AlphaOver_{i}")
            if not alpha_over_node:
                alpha_over_node = tree.nodes.new(type='CompositorNodeAlphaOver')
                alpha_over_node.name = f"ShapesGenerator_AlphaOver_{i}"
            
            additional_scale_node = tree.nodes.get(f"ShapesGenerator_AdditionalScale_{i}")
            if not additional_scale_node:
                additional_scale_node = tree.nodes.new('CompositorNodeScale')
                additional_scale_node.name = f"ShapesGenerator_AdditionalScale_{i}"
            additional_scale_node.space = 'RELATIVE'

            base_x = start_x
            base_y = start_y + i * node_spacing_y  

            image_node.location = (base_x, base_y)
            transform_node.location = (base_x + node_spacing_x * 0.5, base_y)
            scale_node.location = (base_x + node_spacing_x, base_y)
            additional_scale_node.location = (base_x + node_spacing_x * 1.5, base_y)
            alpha_over_node.location = (base_x + node_spacing_x * 2, base_y)

            image = generate_shape(shape.shape_type, **{
                'dimension_x': shape.dimension_x,
                'dimension_y': shape.dimension_y,
                'arrow_length': shape.arrow_length,
                'arrow_width': shape.arrow_width,
                'circle_radius': shape.circle_radius,
                'rectangle_width': shape.rectangle_width,
                'rectangle_height': shape.rectangle_height,
                'ellipse_width': shape.ellipse_width,
                'ellipse_height': shape.ellipse_height,
                'star_outer_radius': shape.star_outer_radius,
                'star_inner_radius': shape.star_inner_radius,
                'star_points': shape.star_points,
                'fill_color': (*shape.fill_color[:3], shape.fill_alpha),
                'line_color': (*shape.line_color[:3], shape.line_alpha),
                'line_width': shape.line_width,
                'rotation': shape.rotation,
                'text_content': shape.text_content,
                'font_size': shape.font_size,
                'font_path': shape.font_path,
                'latex_formula': shape.latex_formula,
                'font_color': (*shape.font_color[:3], shape.font_color[3]),
                'line_size': shape.line_size,
                'custom_shape_path': shape.custom_shape_path,
                'scale_x': shape.scale_x,
                'scale_y': shape.scale_y
            })
            if image is None:
                print(f"Error: No image generated for shape {shape.name}")
                continue

            temp_path = bpy.path.abspath(f"//temp_shape_{shape.name}.png")
            image.save(temp_path, format='PNG')
            
            if image_node.image:
                bpy.data.images.remove(image_node.image)
            image_node.image = bpy.data.images.load(temp_path)
            
            transform_node.inputs['X'].default_value = shape.position_x * 1000 # Amplificar el efecto de la posición
            transform_node.inputs['Y'].default_value = shape.position_y * 1000 # Amplificar el efecto de la posición
            transform_node.inputs['Angle'].default_value = shape.rotation
            
            if 'X' in scale_node.inputs and 'Y' in scale_node.inputs:
                scale_node.inputs['X'].default_value = shape.dimension_x / scene.render.resolution_x
                scale_node.inputs['Y'].default_value = shape.dimension_y / scene.render.resolution_y
            elif 'Scale' in scale_node.inputs:
                scale_x = shape.dimension_x / scene.render.resolution_x
                scale_y = shape.dimension_y / scene.render.resolution_y
                scale_node.inputs['Scale'].default_value = (scale_x + scale_y) / 2
            else:
                print(f"Error: No valid inputs found for scale node of shape {shape.name}")
            
            if 'X' in additional_scale_node.inputs and 'Y' in additional_scale_node.inputs:
                additional_scale_node.inputs['X'].default_value = shape.scale_x
                additional_scale_node.inputs['Y'].default_value = shape.scale_y
            elif 'Scale' in additional_scale_node.inputs:
                additional_scale_node.inputs['Scale'].default_value = (shape.scale_x + shape.scale_y) / 2
            else:
                print(f"Error: No valid inputs found for additional scale node of shape {shape.name}")

            tree.links.new(image_node.outputs[0], transform_node.inputs[0])
            tree.links.new(transform_node.outputs[0], scale_node.inputs[0])
            tree.links.new(scale_node.outputs[0], additional_scale_node.inputs[0])
            tree.links.new(additional_scale_node.outputs[0], alpha_over_node.inputs[2])
            
            if i == 0:
                tree.links.new(render_layers.outputs['Image'], alpha_over_node.inputs[1])
            else:
                prev_alpha_over = tree.nodes.get(f"ShapesGenerator_AlphaOver_{i-1}")
                if prev_alpha_over:
                    tree.links.new(prev_alpha_over.outputs[0], alpha_over_node.inputs[1])
            
            if i == len(shapes) - 1:
                tree.links.new(alpha_over_node.outputs[0], main_alpha_over.inputs[2])
            
            existing_nodes = [node for node in existing_nodes if node not in [image_node, scale_node, transform_node, alpha_over_node, additional_scale_node]]
        
        if shapes:
            last_alpha_over = tree.nodes.get(f"ShapesGenerator_AlphaOver_{len(shapes)-1}")
            if last_alpha_over:
                main_alpha_over.location = (last_alpha_over.location.x + node_spacing_x, last_alpha_over.location.y)

        for node in existing_nodes:
            tree.nodes.remove(node)

        self.force_update(context)

        print("SHAPESGENERATOR_OT_UpdateShapes completed")
        return {'FINISHED'}

    def force_update(self, context):
        context.view_layer.update()

        for area in context.screen.areas:
            area.tag_redraw()

        context.scene.update_tag()

        if context.scene.node_tree:
            context.scene.node_tree.update_tag()

        current_frame = context.scene.frame_current
        context.scene.frame_set(current_frame)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces[0]
                current_shading = space.shading.type
                
                space.shading.type = 'SOLID'
                context.view_layer.update()
                
                space.shading.type = current_shading
                context.view_layer.update()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        depsgraph = context.evaluated_depsgraph_get()
        depsgraph.update()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            context.view_layer.update()
                            region.tag_redraw()

        for node in context.scene.node_tree.nodes:
            node.update()

class SHAPESGENERATOR_OT_NewShape(Operator):
    bl_idname = "shapesgenerator.new_shape"
    bl_label = "New Shape"

    def execute(self, context):
        new_shape = context.scene.shapesgenerator_shapes.add()
        new_shape.name = f"Shape {len(context.scene.shapesgenerator_shapes)}"
        new_shape.position_x = 0  
        new_shape.position_y = 0  
        context.scene.shapesgenerator_active_shape_index = len(context.scene.shapesgenerator_shapes) - 1
        return {'FINISHED'}

class SHAPESGENERATOR_OT_DeleteShape(Operator):
    bl_idname = "shapesgenerator.delete_shape"
    bl_label = "Delete Shape"

    def execute(self, context):
        shapes = context.scene.shapesgenerator_shapes
        index = context.scene.shapesgenerator_active_shape_index

        if index >= 0 and index < len(shapes):
            shapes.remove(index)
            context.scene.shapesgenerator_active_shape_index = min(max(0, index - 1), len(shapes) - 1)

        return {'FINISHED'}
