from direct.showbase.ShowBase import ShowBase
from panda3d.core import OrthographicLens, AmbientLight, DirectionalLight, TextNode, Shader
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectSlider import DirectSlider
from direct.task import Task
import math
from boat import Boat
from ocean import Ocean


class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        self.disableMouse()
        self.setBackgroundColor(0, 0, 0)

        self.boat = Boat(self.render, self.loader)
        self.ocean = Ocean(self.render)

        self.camera_zoom = 2
       
        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.8, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        lens = OrthographicLens()        
        lens.setFilmSize(30 * self.camera_zoom, 22.5 * self.camera_zoom)
        self.cam.node().setLens(lens) # type: ignore
        self.camera.setPos(45, -45, 50) # type: ignore
        self.camera.lookAt(0, 0, 0) # type: ignore

        # Create GUI slider for storm control
        self.storm_label = OnscreenText(
            text=f"Storm Factor: {self.ocean.storm_factor:.2f}",
            pos=(-1.3, 0.9),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        self.storm_slider = DirectSlider(
            range=(0.01, 2.0),
            value=self.ocean.storm_factor,
            pageSize=0.1,
            command=self.update_storm_factor,
            pos=(-0.8, 0, 0.85),
            scale=0.5
        )
        
        # Create GUI slider for boat heading control
        self.heading_label = OnscreenText(
            text=f"Boat Heading: {self.boat.local_coords['heading']:.0f}°",
            pos=(-1.3, 0.75),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        self.heading_slider = DirectSlider(
            range=(0, 360),
            value=self.boat.local_coords["heading"],
            pageSize=10,
            command=self.update_boat_heading,
            pos=(-0.8, 0, 0.70),
            scale=0.5
        )

        shader = Shader.load(Shader.SL_GLSL, "shader.vs", "shader.fs")
        
        self.ocean.plane.setShader(shader)
        
        for name, value in self.ocean.shader_inputs.items():
            self.ocean.plane.setShaderInput(name, value)
        
        # Add task to update ocean geometry and animate waves
        self.taskMgr.add(self.animate_waves, "animate_waves")
    
       
    def update_storm_factor(self):
        """Update storm factor and recalculate wave amplitude"""
        self.ocean.storm_factor = self.storm_slider['value']
        self.ocean.swell['amplitude'] = self.ocean.swell_period * self.ocean.storm_factor
        self.ocean.plane.setShaderInput('swell_amplitude', self.ocean.swell['amplitude'])  
        self.storm_label.setText(f"Storm Factor: {self.ocean.storm_factor:.2f}")
    
    def update_boat_heading(self):
        """Update boat heading (rotation around Z axis)"""
        self.boat.local_coords["heading"] = self.heading_slider['value']
        self.heading_label.setText(f"Boat Heading: {self.boat.local_coords["heading"]:.0f}°")
    
    def animate_waves(self, task):
        """Animate ocean waves by updating geometry and boat position"""
        self.update_boat(task.time)

        self.ocean.plane.setShaderInput('wave_time', task.time)

        return Task.cont
    
    def update_boat(self, time):
        # Convert local boat coordinates to world coordinates accounting for current rotation
        center_world = self.render.getRelativePoint(self.boat.pivot, self.boat.local_coords["center"])
        bow_world = self.render.getRelativePoint(self.boat.pivot, self.boat.local_coords["bow"])
        stern_world = self.render.getRelativePoint(self.boat.pivot, self.boat.local_coords["stern"])
        port_world = self.render.getRelativePoint(self.boat.pivot, self.boat.local_coords["port"])
        starboard_world = self.render.getRelativePoint(self.boat.pivot, self.boat.local_coords["starboard"])
        
        # Sample wave surface at world coordinates, correcting for Gerstner horizontal displacement
        center_displacement = self.ocean.get_surface_at_world_pos(center_world.x, center_world.y, time)
        bow_displacement = self.ocean.get_surface_at_world_pos(bow_world.x, bow_world.y, time)
        stern_displacement = self.ocean.get_surface_at_world_pos(stern_world.x, stern_world.y, time)
        port_displacement = self.ocean.get_surface_at_world_pos(port_world.x, port_world.y, time)
        starboard_displacement = self.ocean.get_surface_at_world_pos(starboard_world.x, starboard_world.y, time)
        
        # Calculate pitch angle (rotation around X-axis, bow vs stern)
        # Use the actual world distance between points after rotation
        bow_stern_dist = math.sqrt((bow_world.x - stern_world.x)**2 + (bow_world.y - stern_world.y)**2)
        pitch_angle = math.degrees(math.atan2(bow_displacement.z - stern_displacement.z, bow_stern_dist))
        
        # Calculate roll angle (rotation around Y-axis, port vs starboard)
        # Use the actual world distance between points after rotation
        beam = math.sqrt((starboard_world.x - port_world.x)**2 + (starboard_world.y - port_world.y)**2)
        roll_angle = -math.degrees(math.atan2(starboard_displacement.z - port_displacement.z, beam))
        
        # Lower damping_factor = more responsive
        self.boat.current_pitch += (pitch_angle - self.boat.current_pitch) / self.boat.pitch_damping
        self.boat.current_roll += (roll_angle - self.boat.current_roll) / self.boat.roll_damping

        # Position boat at wave height while preserving XY position
        #self.boat.pivot.setPos(current_pos.x, current_pos.y, center_displacement.z) # type: ignore
        self.boat.pivot.setZ(center_displacement.z)
        # Apply smoothed rotations (HPR = Heading, Pitch, Roll)
        self.boat.pivot.setHpr(self.boat.local_coords["heading"], self.boat.current_pitch, self.boat.current_roll) # type: ignore



app = MyApp()
app.run()