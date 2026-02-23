from panda3d.core import LineSegs, LPoint3

class Boat():
    def __init__(self, render, loader):
        self.render = render
        self.loader = loader

        self.pivot = self.render.attachNewNode('boat-pivot')
        self.pivot.setPos(0.0, 0.0, 0.0)
        self.model = self.pivot.attachNewNode('boat-model')
        self.cube = self.loader.loadModel('box') # type: ignore
        self.cube.reparentTo(self.model) # type: ignore
        self.model.setScale(3.0, 10.0, 5.0) # type: ignore
        min_point, max_point = self.cube.getTightBounds(self.cube) # type: ignore
        
        center_x = (max_point.x + min_point.x) / 2
        center_y = (max_point.y + min_point.y) / 2
        center_z = (max_point.z + min_point.z) / 2
        self.cube.setPos(-center_x, -center_y, -center_z)

        self.local_coords: dict[str, LPoint3] = {
            "heading": 0.0,
            "center": LPoint3(0.0, 0.0, 0.0),
            "bow": LPoint3(0.0, max_point.y - center_y, 0.0),      
            "stern": LPoint3(0.0, min_point.y - center_y, 0.0),   
            "port": LPoint3(min_point.x - center_x, 0.0, 0.0),    
            "starboard": LPoint3(max_point.x - center_x, 0.0, 0.0) 
        }

        # Physics state for damping/lag simulation
        self.current_pitch = 0.0
        self.current_roll = 0.0
        self.roll_damping = 5
        self.pitch_damping = 7

        self.pivot.setHpr(self.local_coords["heading"], self.current_pitch, self.current_roll) # type: ignore
        
        self.debug_vector_display()

    def debug_vector_display(self):
        self.cube.setRenderModeWireframe() # type: ignore

        # Draw lines to visualize boat coordinate points in local space
        # Bow line (red)
        bow_line = LineSegs()
        bow_line.setThickness(3)
        bow_line.setColor(1, 0, 0, 1)  # Red
        bow_line.moveTo(self.local_coords["center"])
        bow_line.drawTo(self.local_coords["bow"])
        bow_node = self.pivot.attachNewNode(bow_line.create())
        bow_node.setScale(self.model.getScale())
        
        # Stern line (blue)
        stern_line = LineSegs()
        stern_line.setThickness(3)
        stern_line.setColor(0, 0, 1, 1)  # Blue
        stern_line.moveTo(self.local_coords["center"])
        stern_line.drawTo(self.local_coords["stern"])
        stern_node = self.pivot.attachNewNode(stern_line.create())
        stern_node.setScale(self.model.getScale())
        
        # Port line (green)
        port_line = LineSegs()
        port_line.setThickness(3)
        port_line.setColor(0, 1, 0, 1)  # Green
        port_line.moveTo(self.local_coords["center"])
        port_line.drawTo(self.local_coords["port"])
        port_node = self.pivot.attachNewNode(port_line.create())
        port_node.setScale(self.model.getScale())
        
        # Starboard line (yellow)
        starboard_line = LineSegs()
        starboard_line.setThickness(3)
        starboard_line.setColor(1, 1, 0, 1)  # Yellow
        starboard_line.moveTo(self.local_coords["center"])
        starboard_line.drawTo(self.local_coords["starboard"])
        starboard_node = self.pivot.attachNewNode(starboard_line.create())
        starboard_node.setScale(self.model.getScale())
