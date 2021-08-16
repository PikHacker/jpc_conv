jpc_conv
From PikHacker (and Yoshi2)

This tool converts .jpc files from Pikmin 2 to a readable format and back.
It also extracts and repacks the textures for easy editing.

To use the tool, run readjpc.py with python, the usage will look like

python readjpc.py [input file] [texture path] [output file]

[input file] is required and must be either a .jpc or a .json, the tool
will act accordingly based on which you provide.

[texture path] is where the textures from the .jpc will be stored and read from.
it must end with a / to represent being a folder and not an extension to the file name.

[output file] is optional, and specifies the name of the file created. If not given, 
the output file will be the input file name with the new extension added on.

To briefly describe what the .json file contains, a jpc is a big list of JPAResource objects,
each of which has sub-objects such as BEM1 BSP1 and TDB1.

BEM1 controls most of the "physics" of a particle, such as how it moves

BSP1 controls the color of a particle mainly, it also has sub-objects of its
own that represent colors at different points in the effect I believe.

FLD1 has a lot of data for controlling the position of a particle.
A single JPAResource can use multiple of these.

ESP1 has a lot of stuff for timing and movement stuff.

TDB1 is a list of texture IDs that are referenced from the TEX1 table.

ETX1 has mainly GX flags and stuff for rendering purposes.

SSP1 has a lot of modifiers for scale and color and stuff.

KFA1 has data for key frames in a particle effect, it has its own
sub objects for each key frame data.

TEX1 is a list of texture file names, the textures themselves are in the texture folder.

Keep in mind a lot of these names I give variables are temporary, I'm not perfect
at figuring out these complex systems, but for now its better than nothing.
