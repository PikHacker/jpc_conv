from binary_io import *
from binascii import hexlify, unhexlify
import re
import os

#the name of the folder used for textures
tex_folder = "temp"

#The .jpc file is really a big list of these JPAResource objects
class JPAResource(object): 
    def __init__(self):
        self.Index = 0
        self.ObjCount = 0 
        self.FieldCount = 0 
        self.KeyCount = 0
        self.unk1 = 0
        self.unk2 = 0
        self.children = []
    
    @classmethod
    def from_file(cls, f):
        node = cls()
        node.Index = read_uint16(f) #JPAResource header data
        node.ObjCount = read_uint16(f)
        node.FieldCount = read_uint8(f)
        node.KeyCount = read_uint8(f)
        node.unk1 = read_uint8(f)
        node.unk2 = read_uint8(f)

        print("New Resource ID {0}".format(node.Index))
        for x in range(node.ObjCount):
            next = peek_id(f)
            if next == b"BEM1":
                print("Found a BEM1 section")
                childnode = DynamicsBlock.from_file(f)
                node.children.append(childnode)

            elif next == b"BSP1":
                print("Found a BSP1 section")
                childnode = BaseShape.from_file(f)
                node.children.append(childnode)

            elif next == b"FLD1":
                print("Found a FLD1 section")
                childnode = FieldBlock.from_file(f)
                node.children.append(childnode)

            elif next == b"KFA1":
                print("Found a KFA1 section")
                childnode = KeyBlock.from_file(f)
                node.children.append(childnode)

            elif next == b"ESP1":
                print("Found a ESP1 section")
                childnode = ExtraShape.from_file(f)
                node.children.append(childnode)

            elif next == b"ETX1":
                print("Found a ETX1 section")
                childnode = ExTexShape.from_file(f)
                node.children.append(childnode)

            elif next == b"SSP1":
                print("Found a SSP1 section")
                childnode = ChildShape.from_file(f)
                node.children.append(childnode)

            elif next == b"TDB1":
                print("Found a TDB1 section")
                childnode = TextureData.from_file(f)
                node.children.append(childnode)
            else:
                raise RuntimeError("Unknown Section "+next)
        
        return node 

    def write(self, f):
        count = 0

        write_uint16(f, self.Index)#JPAResource header data
        write_uint16(f, self.ObjCount)
        write_uint8(f, self.FieldCount)
        write_uint8(f, self.KeyCount)
        write_uint8(f, self.unk1)
        write_uint8(f, self.unk2)

        for child in self.children:
            child.write(f)

        return count

    def serialize(self):
        sus = {}
        for key, val in self.__dict__.items():
            if key != "children":
                sus[key] = val 

        result = []
        result.append(sus)

        for child in self.children:
                result.append(child.serialize())
        
        return result 

    def assign(self, src, field):
        self.__dict__[field] = src[field]
    
    @classmethod 
    def deserialize(cls, obj):
        node = cls()
        node.assign(obj[0], "Index")
        node.assign(obj[0], "ObjCount")
        node.assign(obj[0], "FieldCount")
        node.assign(obj[0], "KeyCount")
        node.assign(obj[0], "unk1")
        node.assign(obj[0], "unk2")
        #print("New Resource ID {0}".format(node.Index))
        for x in range(node.ObjCount):
            item = obj[x+1]

            if "type" not in(item):
                check = item[0]
            else:
                check = item

          # print("found a "+check["type"])
            if check["type"] == "BEM1":#yes
                jpcitem = DynamicsBlock.deserialize(item)
            elif check["type"] == "BSP1":#yes
                jpcitem = BaseShape.deserialize(item)
            elif check["type"] == "FLD1":#yes
                jpcitem = FieldBlock.deserialize(item)
            elif check["type"] == "KFA1":#no
                jpcitem = KeyBlock.deserialize(item)
            elif check["type"] == "ESP1":#yes
                jpcitem = ExtraShape.deserialize(item)
            elif check["type"] == "ETX1":#no
                jpcitem = ExTexShape.deserialize(item)
            elif check["type"] == "SSP1":#no
                jpcitem = ChildShape.deserialize(item)
            elif check["type"] == "TDB1":#yes
                jpcitem = TextureData.deserialize(item)
            else:
                raise RuntimeError("Unknown item {0}".format(item["type"]))
            node.children.append(jpcitem)

        return node

#the BEM1 block controls a lot of a particles "physics"
class DynamicsBlock(object):
    def __init__(self):
        self.name = "BEM1"
        
    @classmethod
    def from_file(cls, f):
        start = f.tell()#start point

        name = read_name(f)

        if name != "BEM1":
            raise RuntimeError("Not a BEM1 section")

        pane = cls()
        size = read_uint32(f)
        assert size == 0x7c
        pane.flags = hex(read_uint32(f))

        pane.unk1 = read_uint32(f)
        pane.unk2 = read_float(f)
        pane.unk3 = read_float(f)
        pane.unk4 = read_float(f)
        
        pane.pos_x = read_float(f)
        pane.pos_y = read_float(f)
        pane.pos_z = read_float(f)

        pane.axis_x = read_float(f)
        pane.axis_y = read_float(f)
        pane.axis_z = read_float(f)

        pane.rand_angle_x = read_float(f)
        pane.rand_angle_y = read_float(f)
        pane.rand_angle_z = read_float(f)

        pane.velocity_x = read_float(f)
        pane.velocity_y = read_float(f)
        pane.velocity_z = read_float(f)

        pane.texScale_x = read_float(f)
        pane.texScale_y = read_float(f)
        pane.texScale_z = read_float(f)

        pane.move_x = read_float(f)
        pane.move_y = read_float(f)
        pane.move_z = read_float(f)
        pane.forward_factor = read_float(f)

        pane.angle_x = read_uint16(f)
        pane.angle_y = read_uint16(f)
        pane.angle_z = read_uint16(f)

        pane.stopTime = read_uint16(f)
        pane.startTime = read_uint16(f)
        pane.duration = read_uint16(f)

        pane.unk5 = read_uint16(f)
        pane.unk6 = read_uint16(f)
        pane.interval = read_uint16(f)
        read_uint16(f)#padding
        
        assert f.tell() == start + size
        return pane

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x7c)
        write_uint32(f, int(self.flags, base=16))

        write_float(f, self.unk1)
        write_float(f, self.unk2)
        write_float(f, self.unk3)
        write_float(f, self.unk4)

        write_float(f, self.pos_x)
        write_float(f, self.pos_y)
        write_float(f, self.pos_z)

        write_float(f, self.axis_x)
        write_float(f, self.axis_y)
        write_float(f, self.axis_z)

        write_float(f, self.rand_angle_x)
        write_float(f, self.rand_angle_y)
        write_float(f, self.rand_angle_z)

        write_float(f, self.velocity_x)
        write_float(f, self.velocity_y)
        write_float(f, self.velocity_z)

        write_float(f, self.texScale_x)
        write_float(f, self.texScale_y)
        write_float(f, self.texScale_z)

        write_float(f, self.move_x)
        write_float(f, self.move_y)
        write_float(f, self.move_z)
        write_float(f, self.forward_factor)

        write_uint16(f, self.angle_x)
        write_uint16(f, self.angle_y)
        write_uint16(f, self.angle_z)

        write_uint16(f, self.stopTime)
        write_uint16(f, self.startTime)
        write_uint16(f, self.duration)
        write_uint16(f, self.unk5)
        write_uint16(f, self.unk6)
        write_uint16(f, self.interval)
        write_uint16(f, 0)

        assert f.tell() == start + 0x7c

    def serialize(self):
        result = {}
        result["type"] = "BEM1"

        for key, val in self.__dict__.items():
            if key != "name":
                if isinstance(val, bytes):
                    raise RuntimeError("hhhe")
                result[key] = val 
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        item = cls()
        item.name = "BEM1"
        item.assign(obj, "flags")

        item.assign(obj, "unk1")
        item.assign(obj, "unk2")
        item.assign(obj, "unk3")
        item.assign(obj, "unk4")

        item.assign(obj, "pos_x")
        item.assign(obj, "pos_y")
        item.assign(obj, "pos_z")

        item.assign(obj, "axis_x")
        item.assign(obj, "axis_y")
        item.assign(obj, "axis_z")

        item.assign(obj, "rand_angle_x")
        item.assign(obj, "rand_angle_y")
        item.assign(obj, "rand_angle_z")

        item.assign(obj, "velocity_x")
        item.assign(obj, "velocity_y")
        item.assign(obj, "velocity_z")

        item.assign(obj, "texScale_x")
        item.assign(obj, "texScale_y")
        item.assign(obj, "texScale_z")

        item.assign(obj, "move_x")
        item.assign(obj, "move_y")
        item.assign(obj, "move_z")
        item.assign(obj, "forward_factor")

        item.assign(obj, "angle_x")
        item.assign(obj, "angle_y")
        item.assign(obj, "angle_z")

        item.assign(obj, "stopTime")
        item.assign(obj, "startTime")
        item.assign(obj, "duration")
        item.assign(obj, "unk5")
        item.assign(obj, "unk6")
        item.assign(obj, "interval")
        return item 


#Color Data sub-objects within the BSP1 block
class BaseShape_ColorData(object):
    def __init__(self):
        self.name = "ColorData"
        self.MatId = 0
        self.color = 0

    @classmethod
    def from_file(cls, f, id, x):
        shape = cls()
        shape.MatId = read_uint16(f)
        shape.color = hex(read_uint32(f))
        shape.name = "ColorData_" + format(id) + "_" + format(x)
        return shape

    def write(self, f):
        write_uint16(f, self.MatId)
        write_uint32(f, int(self.color, base=16))


    def serialize(self):
        result = {}

        for key, val in self.__dict__.items():
                result[key] = val 

        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        item = cls()

        item.assign(obj, "MatId")
        item.assign(obj, "color")
        return item

#the BSP1 block controls a particles color data
class BaseShape(object):
    def __init__(self):
        self.name = "BSP1"
        self.colorData1 = []
        self.colorData2 = []

    @classmethod
    def from_file(cls, f):
        start = f.tell()

        name = read_name(f)
        if name != "BSP1":
            raise RuntimeError("Not a BSP1 section")

        size = read_uint32(f)
        assert size >= 0x34#minimum size of this block

        shape = cls()
        shape.flags = hex(read_uint32(f))
        colorTable1Offs = read_uint16(f)
        colorTable2Offs = read_uint16(f)

        shape.Scale_x = read_float(f)
        shape.Scale_y = read_float(f)

        shape.GXBlend = read_uint16(f)
        shape.GXAlpha1 = read_uint8(f)
        shape.GXAlpha2 = read_uint8(f)
        shape.GXAlpha3 = read_uint8(f)
        shape.GXZcomp = read_uint8(f)
        shape.flags2 = read_uint8(f)
        shape.colorDiv = read_uint8(f)
        shape.TexIndex = read_uint8(f)

        shape.ColorTableFlags = read_uint8(f)
        shape.ColorTable1Count = read_uint8(f)# colortable has 6 bytes for each of these
        shape.ColorTable2Count = read_uint8(f)
        shape.repeatDiv = read_uint16(f)
        shape.Color1 = hex(read_uint32(f))
        shape.Color2 = hex(read_uint32(f))

        shape.init_p = read_uint8(f)
        shape.repeatFlag = read_uint8(f)
        shape.mergeFlag = read_uint8(f)
        read_uint16(f)
        read_uint8(f)

        if shape.colorDiv != 0:#this is for some extra junk only used by mergeIdx functions
            shape.MergeIdx1 = read_uint32(f)
            shape.MergeIdx2 = read_uint32(f)

        if colorTable1Offs != 0:
            f.seek(start + colorTable1Offs)#the BSP1 likes to have a lot of junk data in it for no reason, so these seeks skip it
            for x in range(shape.ColorTable1Count):
                shape.colorData1.append(BaseShape_ColorData.from_file(f,1,x))

        if colorTable2Offs != 0:
            f.seek(start + colorTable2Offs)
            for x in range(shape.ColorTable2Count):
                shape.colorData2.append(BaseShape_ColorData.from_file(f,2,x))

        f.seek(start + size)
        assert f.tell() == start + size
        return shape

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0)#temporary
        write_uint32(f, int(self.flags, base=16))
        write_uint16(f, 0x34)
        offs = 0x34 + 6*self.ColorTable1Count
        if offs % 4 != 0:
            offs +=2
        write_uint16(f, offs)#dynamically determine second color table offset
        write_float(f, self.Scale_x)
        write_float(f, self.Scale_y)
        write_uint16(f, self.GXBlend)
        write_uint8(f, self.GXAlpha1)
        write_uint8(f, self.GXAlpha2)
        write_uint8(f, self.GXAlpha3)
        write_uint8(f, self.GXZcomp)
        write_uint8(f, self.flags2)
        write_uint8(f, self.colorDiv)
        write_uint8(f, self.TexIndex)

        write_uint8(f, self.ColorTableFlags)
        write_uint8(f, self.ColorTable1Count)
        write_uint8(f, self.ColorTable2Count)
        write_uint16(f, self.repeatDiv)
        write_uint32(f, int(self.Color1, base=16))
        write_uint32(f, int(self.Color2, base=16))
        write_uint8(f, self.init_p)
        write_uint8(f, self.repeatFlag)
        write_uint8(f, self.mergeFlag)
        write_uint16(f,0)
        write_uint8(f,0)

        if self.colorDiv != 0:
            write_uint32(f,self.MergeIdx1)
            write_uint32(f,self.MergeIdx2)
            old = f.tell()
            f.seek(start+12)
            write_uint16(f,0x3c)
            offs = 0x3c + 6*self.ColorTable1Count
            if offs % 4 != 0:
                offs +=2
            write_uint16(f,offs)
            f.seek(old)
    

        for child in self.colorData1:
                child.write(f)
        if f.tell() % 4 != 0:#padding fix
            write_uint16(f,0)

        for child in self.colorData2:
                child.write(f)
        if f.tell() % 4 != 0:
            write_uint16(f,0)

        size = f.tell() - start#how to write a dynamic block size
        f.seek(start + 4)
        write_uint32(f,size)

        f.seek(start+12)#this makes the offset not exist if there is no color data for it
        if self.ColorTable1Count == 0:
            write_uint16(f,0)
        f.seek(start+14)
        if self.ColorTable2Count == 0:
            write_uint16(f,0)

        f.seek(start + size)
        assert f.tell() == start + size

    def serialize(self):
        result = {}
        result["type"] = "BSP1"
        for key, val in self.__dict__.items():
            if key != "name" and key != "colorData2" and key != "colorData1":
                result[key] = val 

        result2 = []
        result2.append(result)

        for child in self.colorData1:
            result2.append(child.serialize())
        for child in self.colorData2:
            result2.append(child.serialize())
        
        return result2

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj[0] and obj[0]["type"] == "BSP1"
        item = cls()
        item.name = "BSP1"
        item.assign(obj[0], "flags")

        item.assign(obj[0], "Scale_x")
        item.assign(obj[0], "Scale_y")

        item.assign(obj[0], "GXBlend")
        item.assign(obj[0], "GXAlpha1")
        item.assign(obj[0], "GXAlpha2")
        item.assign(obj[0], "GXAlpha3")
        item.assign(obj[0], "GXZcomp")
        item.assign(obj[0], "flags2")
        item.assign(obj[0], "colorDiv")
        item.assign(obj[0], "TexIndex")

        item.assign(obj[0], "ColorTableFlags")
        item.assign(obj[0], "ColorTable1Count")
        item.assign(obj[0], "ColorTable2Count")
        item.assign(obj[0], "repeatDiv")
        item.assign(obj[0], "Color1")
        item.assign(obj[0], "Color2")

        if "MergeIdx1" in obj[0]:
            item.assign(obj[0], "MergeIdx1")
            item.assign(obj[0], "MergeIdx2")

        item.assign(obj[0], "init_p")
        item.assign(obj[0], "repeatFlag")
        item.assign(obj[0], "mergeFlag")
        for x in range(item.ColorTable1Count):
            item.colorData1.append(BaseShape_ColorData.deserialize(obj[1+x]))
        for x in range(item.ColorTable2Count):
            item.colorData2.append(BaseShape_ColorData.deserialize(obj[1 + item.ColorTable1Count + x]))

        return item 

#the FLD1 block controls a particles position in global space?
class FieldBlock(object):
    def __init__(self):
        self.name = "FLD1"

    @classmethod
    def from_file(cls, f):
        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)
        assert size == 0x44

        if name != "FLD1":
            raise RuntimeError("Not a FLD1 section")

        field = cls()
        field.name = name
        field.flags = hex(read_uint32(f))

        field.offset_x = read_float(f)
        field.offset_y = read_float(f)
        field.offset_z = read_float(f)

        field.move_x = read_float(f)
        field.move_y = read_float(f)
        field.move_z = read_float(f)

        field.amplitude = read_float(f)

        field.vortex_speed = read_float(f)
        field.newton_speed = read_float(f)
        field.timerMax1 = read_float(f)
        field.timerMax2 = read_float(f)
        field.timerOffset1 = read_float(f)
        field.timerOffset2 = read_float(f)
        field.randDiv = read_uint8(f)
        read_uint16(f)
        read_uint8(f)

        assert f.tell() == start + 0x44
        return field 
      
    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x44)#size
        write_uint32(f, int(self.flags, base=16))
        write_float(f, self.offset_x)
        write_float(f, self.offset_y)
        write_float(f, self.offset_z)
        write_float(f, self.move_x)
        write_float(f, self.move_y)
        write_float(f, self.move_z)
        write_float(f, self.amplitude)
        write_float(f, self.vortex_speed)
        write_float(f, self.newton_speed)
        write_float(f, self.timerMax1)
        write_float(f, self.timerMax2)
        write_float(f, self.timerOffset1)
        write_float(f, self.timerOffset2)
        write_uint8(f, self.randDiv)
        write_uint8(f, 0)
        write_uint8(f, 0)
        write_uint8(f, 0)

        assert f.tell() == start + 0x44

    def serialize(self):
        result = {}
        result["type"] = "FLD1"
        for key, val in self.__dict__.items():
            if key != "name":
                result[key] = val 
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "FLD1"

        item = cls()
        item.name = "FLD1"
        item.assign(obj, "flags")

        item.assign(obj, "offset_x")
        item.assign(obj, "offset_y")
        item.assign(obj, "offset_z")

        item.assign(obj, "move_x")
        item.assign(obj, "move_y")
        item.assign(obj, "move_z")

        item.assign(obj, "amplitude")

        item.assign(obj, "vortex_speed")
        item.assign(obj, "newton_speed")

        item.assign(obj, "timerMax1")
        item.assign(obj, "timerMax2")

        item.assign(obj, "timerOffset1")
        item.assign(obj, "timerOffset2")
        item.assign(obj, "randDiv")

        return item

#the ESP1 block controls a particles moving/time data stuff
class ExtraShape(object):
    def __init__(self):
        self.name = "ESP1"

    @classmethod
    def from_file(cls, f):
        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)
        assert size == 0x60

        if name != "ESP1":
            raise RuntimeError("Not a ESP1 section")

        field = cls()
        field.name = name
        field.flags = hex(read_uint32(f))

        field.growrate = read_float(f)
        field.decay = read_float(f)
        field.startscale = read_float(f)

        field.unk_x = read_float(f)
        field.unk_y = read_float(f)
        field.unk_z = read_float(f)

        field.randscale = read_float(f)

        field.repeatX = read_uint16(f)
        field.repeatY = read_uint16(f)

        field.fadeout = read_float(f)
        field.fadein = read_float(f)
        field.alphamod = read_float(f)
        field.fadestart = read_float(f)
        field.fadeend = read_float(f)

        field.alphaFlick1 = read_float(f)
        field.radius = read_float(f)
        field.alphaFlick2 = read_float(f)

        field.A1_factor1 = read_float(f)
        field.A1_factor2 = read_float(f)
        field.A2_factor1 = read_float(f)
        field.A2_factor2 = read_float(f)
        field.Aflip_threshold = read_float(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x60)
        write_uint32(f, int(self.flags, base=16))
        write_float(f, self.growrate)
        write_float(f, self.decay)
        write_float(f, self.startscale)
        write_float(f, self.unk_x)
        write_float(f, self.unk_y)
        write_float(f, self.unk_z)
        write_float(f, self.randscale)
        write_uint16(f, self.repeatX)
        write_uint16(f, self.repeatY)
        write_float(f, self.fadeout)
        write_float(f, self.fadein)
        write_float(f, self.alphamod)
        write_float(f, self.fadestart)
        write_float(f, self.fadeend)
        write_float(f, self.alphaFlick1)
        write_float(f, self.radius)
        write_float(f, self.alphaFlick2)
        write_float(f, self.A1_factor1)
        write_float(f, self.A1_factor2)
        write_float(f, self.A2_factor1)
        write_float(f, self.A2_factor2)
        write_float(f, self.Aflip_threshold)

        assert f.tell() == start + 0x60

    def serialize(self):
        result = {}
        result["type"] = "ESP1"

        for key, val in self.__dict__.items():
            if key != "name":
                if isinstance(val, bytes):
                    raise RuntimeError("hhhe")
                result[key] = val 
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "ESP1"

        item = cls()
        item.name = "ESP1"
        item.assign(obj, "flags")

        item.assign(obj, "growrate")
        item.assign(obj, "decay")
        item.assign(obj, "startscale")

        item.assign(obj, "unk_x")
        item.assign(obj, "unk_y")
        item.assign(obj, "unk_z")

        item.assign(obj, "randscale")
        item.assign(obj, "repeatX")
        item.assign(obj, "repeatY")

        item.assign(obj, "fadeout")
        item.assign(obj, "fadein")
        item.assign(obj, "alphamod")
        item.assign(obj, "fadestart")
        item.assign(obj, "fadeend")

        item.assign(obj, "alphaFlick1")
        item.assign(obj, "radius")
        item.assign(obj, "alphaFlick2")

        item.assign(obj, "A1_factor1")
        item.assign(obj, "A1_factor2")
        item.assign(obj, "A2_factor1")
        item.assign(obj, "A2_factor2")
        item.assign(obj, "Aflip_threshold")

        return item

#the TDB1 block has a few shorts for a list of texture IDs
class TextureData(object):
    def __init__(self):
        self.name = "TDB1"
        self.TextureIDList = []

    @classmethod
    def from_file(cls, f):
        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)

        if name != "TDB1":
            raise RuntimeError("Not a TDB1 section")

        field = cls()
        field.name = name
        for x in range(int((size-8) / 2)):
            field.TextureIDList.append(read_uint16(f))

        assert f.tell() == start + size
        return field

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x0)#temp

        for thing in self.TextureIDList:
            write_uint16(f, thing)

        size = 8 + (len(self.TextureIDList) * 2)
        f.seek(start + 4)
        write_uint32(f,size)
        f.seek(start+size)
        assert f.tell() == start + size

    def serialize(self):
        result = {}
        result["type"] = "TDB1"

        for key, val in self.__dict__.items():
            if key != "name":
                if isinstance(val, bytes):
                    raise RuntimeError("hhhe")
                result[key] = val 

        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "TDB1"
        item = cls()
        item.name = "TDB1"
        item.assign(obj, "TextureIDList")

        return item

#the ETX1 Handles GX stuff for rendering the textures
class ExTexShape(object):
    def __init__(self):
        self.name = "ETX1"

    @classmethod
    def from_file(cls, f):
        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)
        assert size == 0x28

        if name != "ETX1":
            raise RuntimeError("Not a ETX1 section")

        field = cls()
        field.name = name
        field.flags = hex(read_uint32(f))

        field.texMtx1 = read_float(f)
        field.texMtx2 = read_float(f)
        field.texMtx3 = read_float(f)
        field.texMtx4 = read_float(f)
        field.texMtx5 = read_float(f)
        field.texMtx6 = read_float(f)

        #field.flags2 = hex(read_uint32(f))
        field.texMtxID = read_uint8(f)
        field.EXTexID1 = read_uint8(f)
        field.EXTexID2 = read_uint8(f)
        read_uint8(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x28)
        write_uint32(f, int(self.flags, base=16))

        write_float(f, self.texMtx1)
        write_float(f, self.texMtx2)
        write_float(f, self.texMtx3)
        write_float(f, self.texMtx4)
        write_float(f, self.texMtx5)
        write_float(f, self.texMtx6)

        write_uint8(f, self.texMtxID)
        write_uint8(f, self.EXTexID1)
        write_uint8(f, self.EXTexID2)
        write_uint8(f, 0)

        assert f.tell() == start + 0x28

    def serialize(self):
        result = {}
        result["type"] = "ETX1"

        for key, val in self.__dict__.items():
            if key != "name":
                if isinstance(val, bytes):
                    raise RuntimeError("hhhe")
                result[key] = val 
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "ETX1"
        item = cls()
        item.name = "ETX1"
        item.assign(obj, "flags")
        item.assign(obj, "texMtx1")
        item.assign(obj, "texMtx2")
        item.assign(obj, "texMtx3")
        item.assign(obj, "texMtx4")
        item.assign(obj, "texMtx5")
        item.assign(obj, "texMtx6")

        item.assign(obj, "texMtxID")
        item.assign(obj, "EXTexID1")
        item.assign(obj, "EXTexID2")

        return item

#the SSP1 does weird scale modifier and child stuff mainly
class ChildShape(object):
    def __init__(self):
        self.name = "SSP1"

    @classmethod
    def from_file(cls, f):
        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)
        assert size == 0x48

        if name != "SSP1":
            raise RuntimeError("Not a SSP1 section")

        field = cls()
        field.name = name
        field.flags = hex(read_uint32(f))

        field.radiusFactor1 = read_float(f)
        field.radiusFactor2 = read_float(f)
        field.radiusFactor3 = read_float(f)
        field.scaleModifier = read_float(f)
        field.Y_offset = read_float(f)
        field.X_scale = read_float(f)
        field.Y_scale = read_float(f)
        field.childScale = read_float(f)
        field.AlphaModifier = read_float(f)
        field.ColorModifier = read_float(f)

        field.TEVColor1 = hex(read_uint32(f))
        field.TEVColor2 = hex(read_uint32(f))
        field.ChildCountModifier = read_float(f)
        field.calc_count = read_uint16(f)
        field.ChildEmitterCount = read_uint16(f)
        field.maxChildren = read_uint8(f)
        field.TexIndex_offset = read_uint8(f)
        field.unk_Alpha = read_uint16(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x48)
        write_uint32(f, int(self.flags, base=16))

        write_float(f, self.radiusFactor1)
        write_float(f, self.radiusFactor2)
        write_float(f, self.radiusFactor3)
        write_float(f, self.scaleModifier)
        write_float(f, self.Y_offset)
        write_float(f, self.X_scale)
        write_float(f, self.Y_scale)
        write_float(f, self.childScale)
        write_float(f, self.AlphaModifier)
        write_float(f, self.ColorModifier)

        write_uint32(f, int(self.TEVColor1, base=16))
        write_uint32(f, int(self.TEVColor2, base=16))
        write_float(f, self.ChildCountModifier)
        write_uint16(f, self.calc_count)
        write_uint16(f, self.ChildEmitterCount)
        write_uint8(f, self.maxChildren)
        write_uint8(f, self.TexIndex_offset)
        write_uint16(f, self.unk_Alpha)

        assert f.tell() == start + 0x48

    def serialize(self):
        result = {}
        result["type"] = "SSP1"

        for key, val in self.__dict__.items():
            if key != "name":
                if isinstance(val, bytes):
                    raise RuntimeError("hhhe")
                result[key] = val 
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "SSP1"
        item = cls()
        item.name = "SSP1"
        item.assign(obj, "flags")
        item.assign(obj, "radiusFactor1")
        item.assign(obj, "radiusFactor2")
        item.assign(obj, "radiusFactor3")

        item.assign(obj, "scaleModifier")
        item.assign(obj, "Y_offset")
        item.assign(obj, "X_scale")
        item.assign(obj, "Y_scale")
        item.assign(obj, "childScale")
        item.assign(obj, "AlphaModifier")
        item.assign(obj, "ColorModifier")

        item.assign(obj, "TEVColor1")
        item.assign(obj, "TEVColor2")
        item.assign(obj, "ChildCountModifier")
        item.assign(obj, "calc_count")
        item.assign(obj, "ChildEmitterCount")
        item.assign(obj, "maxChildren")
        item.assign(obj, "TexIndex_offset")
        item.assign(obj, "unk_Alpha")

        return item

#Key Frame sub-objects within the KFA1 block
class KeyBlock_field(object):
    def __init__(self):
        self.Frame = 0.0
        self.calc = 0.0
        self.tangent1 = 0.0
        self.tangent2 = 0.0

    @classmethod
    def from_file(cls, f):
        shape = cls()
        shape.Frame = read_float(f)
        shape.calc = read_float(f)
        shape.tangent1 = read_float(f)
        shape.tangent2 = read_float(f)
        return shape

    def write(self, f):
        write_float(f, self.Frame)
        write_float(f, self.calc)
        write_float(f, self.tangent1)
        write_float(f, self.tangent2)

    def serialize(self):
        result = {}

        for key, val in self.__dict__.items():
                result[key] = val 

        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        item = cls()
        item.assign(obj, "Frame")
        item.assign(obj, "calc")
        item.assign(obj, "tangent1")
        item.assign(obj, "tangent2")
        return item

#the KFA1 does animation key frame calculation stuff
class KeyBlock(object):
    def __init__(self):
        self.name = "KFA1"
        self.calcList = []

    @classmethod
    def from_file(cls, f):

        start = f.tell()
        name = read_name(f)
        size = read_uint32(f)

        if name != "KFA1":
            raise RuntimeError("Not a KFA1 section")

        shape = cls()
        shape.name = name
        assert size >= 0x2c

        shape.flag = read_uint8(f)
        shape.KeyFrameCount = read_uint8(f)
        read_uint8(f)
        read_uint8(f)

        for x in range(shape.KeyFrameCount):
            shape.calcList.append(KeyBlock_field.from_file(f))

        assert f.tell() == start + size
        return shape 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0)#temp
        write_uint8(f, self.flag)
        write_uint8(f, self.KeyFrameCount)
        write_uint8(f, 0)
        write_uint8(f, 0)

        for field in self.calcList:
            field.write(f)

        size = f.tell() - start#how to write a dynamic block size
        f.seek(start + 4)
        write_uint32(f,size)
        f.seek(start + size)

        assert f.tell() == start + size

    def serialize(self):
        result = {}
        result["type"] = "KFA1"

        for key, val in self.__dict__.items():
            if key != "name" and key != "calcList":
                result[key] = val 

        result2 = []
        result2.append(result)

        for child in self.calcList:
            result2.append(child.serialize())
        
        return result2

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj[0] and obj[0]["type"] == "KFA1"
        item = cls()
        item.name = "KFA1"
        item.assign(obj[0], "flag")
        item.assign(obj[0], "KeyFrameCount")

        for x in range(item.KeyFrameCount):
            item.calcList.append(KeyBlock_field.deserialize(obj[x+1]))

        return item

#tex TEX1 section is really a completely different file from the JPAResource section, its just a big list of textures
class JPATexture(object):
    def __init__(self):
        self.name = "TEX1"
        self.text = []

    @classmethod
    def from_file(cls, f):
		#This is a dumb way to skip through a variable amount of padding but it works
        pad = 0
        while read_uint8(f) != 0x54:#0x54 is T
            pad += 1

        f.seek(f.tell()-1)
        print("Parsing the TEX1 data. " + format(pad) + " bytes of padding")

        shape = cls()
        name = read_name(f)
        while name == "TEX1":
            size = read_uint32(f)
            read_uint32(f)
            text = f.read(0x10).decode("shift_jis_2004")
            f.read(4)#padding?
            text = re.sub(r'\u0000',"",text)
            shape.text.append(text)
            print(text)
            text = tex_folder+text+".bti"

            with open(text, "wb") as j:
                bti = f.read(size-0x20)
                j.write(bti)

            name = read_name(f)

        return shape 

    def write(self, f):
        while f.tell() % 32 != 0:
            write_uint8(f,0)

        start = f.tell()
        for text in self.text:
            write_name(f, self.name)
            size = os.path.getsize(tex_folder+"/"+text+".bti")
            write_uint32(f, size+0x20)#file size
            write_uint32(f,0)
            name = bytes(text, encoding="ascii")

            f.write(name)
            while f.tell() % 16 != 0:
                write_uint8(f,0)

            with open(tex_folder+"/"+text+".bti", "rb") as j:
                bti = j.read(size)
                f.write(bti)
        return start

    def serialize(self):
        result = {}
        result["type"] = "TEX1"
        result["text"] = self.text 
        
        return result 

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        assert "type" in obj and obj["type"] == "TEX1"
        item = cls()
        item.name = "TEX1"
        item.assign(obj, "text")
        return item

#The header data for the start of the .jpc file
class Header(object):
    def __init__(self):
        self.ResCount = 0 
        self.TexCount = 0 
        self.TexOffset = 0
    
    @classmethod 
    def from_file(cls, f):
        thing = f.read(8)
        if thing != b"JPAC2-10":
            raise RuntimeError("Not a valid JPC format!")
        
        inf = cls()
        inf.ResCount = read_uint16(f)
        inf.TexCount = read_uint16(f)
        inf.TexOffset = read_uint32(f)
        
        return inf 

    def write(self, f):
        f.write(b"JPAC2-10")
        write_uint16(f, self.ResCount)
        write_uint16(f, self.TexCount)
        write_uint32(f, self.TexOffset)

    def serialize(self):
        result = {}
        result["format"] = "JPAC2-10"
        result["Resource_Count"] = self.ResCount 
        result["Texture_Count"] = self.TexCount 
        
        return result 

    @classmethod
    def deserialize(cls, obj):
        assert obj["format"] == "JPAC2-10"
        info = cls()
        info.ResCount = obj["Resource_Count"]
        info.TexCount = obj["Texture_Count"]
        
        return info 

 
#The base class for the .jpc file working
class JPAContainer(object):
    def __init__(self):
        self.info = Header()
        self.root = []
        self.texdata = JPATexture()
        
    @classmethod 
    def from_file(cls, f):
        jpc = cls()
        jpc.info = Header.from_file(f)
        
        for x in range(jpc.info.ResCount):
            jpc.root.append(JPAResource.from_file(f))

        jpc.texdata = JPATexture.from_file(f)

        #for thing in jpc.root:
        #    thing = JPAResource.from_file(f)

        return jpc

    def write(self, f):
        start = f.tell()
        self.info.write(f)

        for thing in self.root:
            thing.write(f)

        start = self.texdata.write(f)

        f.seek(0xc)
        write_uint32(f,start)
        print("Done writing to jpc!")

    def serialize(self):
        result = []
        result.append(self.info.serialize())

        for thing in self.root:
            result.append(thing.serialize())

        result.append(self.texdata.serialize())
        
        return result

    @classmethod
    def deserialize(cls, obj):
        jpc = cls()
        jpc.info = Header.deserialize(obj[0])

        for x in range(jpc.info.ResCount):
            jpc.root.append(JPAResource.deserialize(obj[x+1]))

        jpc.texdata = JPATexture.deserialize(obj[jpc.info.ResCount+1])

        return jpc

if __name__ == "__main__":  
    import json 
    import sys
    if len(sys.argv) < 3:
        raise RuntimeError("Usage: python readjpc.py [input_file] [texture_folder] [output_file](optional)")

    inputfile = sys.argv[1]

    if len(sys.argv) > 3:
        outfile = sys.argv[3]
    else:
        outfile = None

    tex_folder = sys.argv[2]

    if tex_folder.endswith("/"):
        tex_folder = os.getcwd() +"/"+tex_folder
        if not os.path.exists(tex_folder):
            os.mkdir(tex_folder)
    else:
        raise RuntimeError("Texture folder must end with /")

    if inputfile.endswith(".jpc"):
        if outfile == None:
            outfile = inputfile + ".json"

        with open(inputfile, "rb") as f:
            jpc = JPAContainer.from_file(f)

        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(jpc.serialize(), f, indent=4, ensure_ascii=False)

    elif inputfile.endswith(".json"):
        if outfile == None:
            outfile = inputfile + ".jpc"

        with open(inputfile, "r", encoding="utf-8") as f:
            jpc = JPAContainer.deserialize(json.load(f))
        with open(outfile, "wb") as f:
            jpc.write(f)
