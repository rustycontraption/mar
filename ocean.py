from panda3d.core import LPoint3, LPoint2, NodePath, GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomNode
import numpy


class Ocean():
    def __init__(self, render):
        self.render = render

        self.ocean_size = 192
        self.ocean_subdivisions = 96
        self.swell_period = 8
        self.storm_factor = .01

        self.swell = {
            'amplitude': self.swell_period * self.storm_factor,
            'period': self.swell_period,
            # Simplified version of the wavelength formula for waves in the deep ocean
            'wavelength': 1.56 * (self.swell_period * self.swell_period),
            'dir': {"x": 1.0, "y": .2},
            'offsets': {
                "wavelength": 1.8,
                "amplitude": 0.8,
                "period": 1.4,
                "x": 0.8,
                "y": -1.5
            },
            'sharpness': 0.2
        }

        self.plane = self.create_plane(
            self.ocean_size, 
            self.ocean_subdivisions
        )
        
        self.plane.reparentTo(self.render)
        self.plane.setPos(0, 0, 0)
        #self.plane.setRenderModeWireframe() # type: ignore

        self.shader_inputs = {
            'swell_amplitude': self.swell['amplitude'],
            'swell_period': self.swell['period'],
            'swell_wavelength': self.swell['wavelength'],
            'swell_dir_x': self.swell['dir']["x"],
            'swell_dir_y': self.swell['dir']["y"],
            'swell_wavelength_offset': self.swell['offsets']["wavelength"],
            'swell_amplitude_offset': self.swell['offsets']["amplitude"],
            'swell_period_offset': self.swell['offsets']["period"],
            'swell_x_offset': self.swell['offsets']["x"],
            'swell_y_offset': self.swell['offsets']["y"],   
            'swell_sharpness': self.swell['sharpness']                          
        }


    def calculate_wave_displacement(self, x, y, time):
        """Calculate wave displacement using Gerstner wave formula
        
        Returns 3D displacement vector with .x, .y, .z attributes at position (x, y)
        """
        position = LPoint3(x, y, 0.0)
        displacement = LPoint3(0.0, 0.0, 0.0)

        def gerstner_wave(position: LPoint3, wavelength: float, amplitude: float, 
                         period: float, direction: LPoint2, time: float):
            """Calculate Gerstner wave displacement vector"""
            wave_number = 2.0 * numpy.pi / wavelength
            angular_freq = 2.0 * numpy.pi / period
            
            # Normalize direction vector
            dir_length = numpy.sqrt(direction.x**2 + direction.y**2)
            unit_vector = LPoint2(direction.x / dir_length, direction.y / dir_length)
            
            # Calculate wave phase: φ = k·r - ωt
            wave_phase = wave_number * (unit_vector.x * position.x + unit_vector.y * position.y) - angular_freq * time
            
            # Calculate displacement components
            cos_phase = numpy.cos(wave_phase)
            sin_phase = numpy.sin(wave_phase)
            
            sharpness = 0.2

            return LPoint3(
                unit_vector.x * amplitude * cos_phase * sharpness,  # x
                unit_vector.y * amplitude * cos_phase * sharpness,  # y
                amplitude * sin_phase                               # z
            )
        
        # Swell 1 - primary direction
        displacement += gerstner_wave(
            position,
            self.swell['wavelength'], 
            self.swell['amplitude'], 
            self.swell['period'], 
            LPoint2(self.swell['dir']["x"], self.swell['dir']["y"]),
            time
        )
        
        # Swell 2 - different direction and varied parameters
        displacement += gerstner_wave(
            position,
            self.swell['wavelength'] * self.swell['offsets']['wavelength'], 
            self.swell['amplitude'] * self.swell['offsets']['amplitude'], 
            self.swell['period'] * self.swell['offsets']['period'], 
            LPoint2(
                self.swell['dir']['x'] * self.swell['offsets']['x'],
                self.swell['dir']['y'] * self.swell['offsets']['y']
            ),
            time
        )

        return position + displacement

    def get_surface_at_world_pos(self, wx, wy, time, iterations=4):
        """Sample wave surface at a world position, accounting for Gerstner horizontal displacement.
        
        Uses fixed-point iteration to invert horizontal displacement:
        finds the rest position (rx, ry) whose displaced position equals (wx, wy),
        then returns the full displacement evaluated at that rest position.
        """
        rx, ry = wx, wy
        for _ in range(iterations):
            d = self.calculate_wave_displacement(rx, ry, time)
            # d.x = rx + dx, d.y = ry + dy — subtract horizontal displacement to get rest pos
            rx = wx - (d.x - rx)
            ry = wy - (d.y - ry)
        return self.calculate_wave_displacement(rx, ry, time)

    def create_plane(self, size, subdiv):
        """Create a subdivided plane for CPU-based deformation"""
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('plane', format, Geom.UHDynamic)  # Changed to UHDynamic for CPU updates
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        
        # Store original vertex positions for wave calculations
        self.base_positions = []
        
        # Create vertices
        for y in range(subdiv + 1):
            for x in range(subdiv + 1):
                px = (x / subdiv - 0.5) * size
                py = (y / subdiv - 0.5) * size
                vertex.addData3(px, py, 0)
                normal.addData3(0, 0, 1)
                color.addData4(0.2, 0.4, 0.8, 1)
                self.base_positions.append((px, py))
        
        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)
        for y in range(subdiv):
            for x in range(subdiv):
                v0 = y * (subdiv + 1) + x
                v1 = v0 + 1
                v2 = v0 + (subdiv + 1)
                v3 = v2 + 1
                
                tris.addVertices(v0, v1, v2)
                tris.addVertices(v1, v3, v2)
        
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('plane')
        node.addGeom(geom)
        
        # Store reference to vertex data for updates
        self.vdata = vdata
        
        return NodePath(node)
