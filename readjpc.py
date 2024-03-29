from binary_io import *
from binascii import hexlify, unhexlify
import re
import os

#the name of the folder used for textures
tex_folder = "temp"

#this is used to pair up common floats
class Vector3():
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    @classmethod
    def from_file(cls, f):
        node = cls()
        node.x = read_float(f)
        node.y = read_float(f)
        node.z = read_float(f)
        return node
    
    def write(self, f):
        write_float(f, self.x)
        write_float(f, self.y)
        write_float(f, self.z)

    def serialize(self):
        result = {}
        for key, val in self.__dict__.items():
            if isinstance(val, bytes):
                raise RuntimeError("hhhe")
            result[key] = val
                
        return result

    def assign(self, src, field):
        self.__dict__[field] = src[field]

    @classmethod
    def deserialize(cls, obj):
        item = cls()
        item.assign(obj, "x")
        item.assign(obj, "y")
        item.assign(obj, "z")
        return item 

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
        self.emitterScale: Vector3
        self.emitterTranslation: Vector3
        self.emitterDirection: Vector3
        
    @classmethod
    def from_file(cls, f):
        start = f.tell()#start point

        name = read_name(f)

        if name != "BEM1":
            raise RuntimeError("Not a BEM1 section")

        pane = cls()
        size = read_uint32(f)
        assert size == 0x7c
        pane.emitFlags = hex(read_uint32(f))

        pane.unk = read_uint32(f)
        pane.emitterScale = Vector3.from_file(f)

        pane.emitterTranslation = Vector3.from_file(f)

        pane.emitterDirection = Vector3.from_file(f)

        pane.initialVelOmni = read_float(f)
        pane.initialVelAxis = read_float(f)
        pane.initialVelRndm = read_float(f)
        pane.initialVelDir = read_float(f)

        pane.spread = read_float(f)
        pane.initialVelRatio = read_float(f)
        pane.rate = read_float(f)
        pane.rateRndm = read_float(f)
        pane.lifeTimeRndm = read_float(f)
        pane.volumeSweep = read_float(f)
        pane.volumeMinRad = read_float(f)
        pane.airResist = read_float(f)
        pane.momentRndm = read_float(f)

        pane.emitterRotX = read_uint16(f)
        pane.emitterRotY = read_uint16(f)
        pane.emitterRotZ = read_uint16(f)

        pane.maxFrame = read_uint16(f)
        pane.startFrame = read_uint16(f)
        pane.lifeTime = read_uint16(f)

        pane.volumeSize = read_uint16(f)
        pane.divNumber = read_uint16(f)
        pane.rateStep = read_uint8(f)
        read_uint16(f)#padding
        read_uint8(f)#padding
        
        assert f.tell() == start + size
        return pane

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x7c)
        write_uint32(f, int(self.emitFlags, base=16))

        write_uint32(f, self.unk)
        self.emitterScale.write(f)

        self.emitterTranslation.write(f)

        self.emitterDirection.write(f)

        write_float(f, self.initialVelOmni)
        write_float(f, self.initialVelAxis)
        write_float(f, self.initialVelRndm)
        write_float(f, self.initialVelDir)

        write_float(f, self.spread)
        write_float(f, self.initialVelRatio)
        write_float(f, self.rate)
        write_float(f, self.rateRndm)
        write_float(f, self.lifeTimeRndm)

        write_float(f, self.volumeSweep)
        write_float(f, self.volumeMinRad)
        write_float(f, self.airResist)
        write_float(f, self.momentRndm)

        write_uint16(f, self.emitterRotX)
        write_uint16(f, self.emitterRotY)
        write_uint16(f, self.emitterRotZ)

        write_uint16(f, self.maxFrame)
        write_uint16(f, self.startFrame)
        write_uint16(f, self.lifeTime)
        write_uint16(f, self.volumeSize)
        write_uint16(f, self.divNumber)
        write_uint8(f, self.rateStep)
        write_uint16(f, 0)
        write_uint8(f,0)

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
        item.assign(obj, "emitFlags")

        item.assign(obj, "unk")
        item.assign(obj, "emitterScale")
        vec = Vector3()
        vec.x = item.emitterScale["x"]
        vec.y = item.emitterScale["y"]
        vec.z = item.emitterScale["z"]
        item.emitterScale = vec

        item.assign(obj, "emitterTranslation")
        vec = Vector3()
        vec.x = item.emitterTranslation["x"]
        vec.y = item.emitterTranslation["y"]
        vec.z = item.emitterTranslation["z"]
        item.emitterTranslation = vec

        item.assign(obj, "emitterDirection")
        vec = Vector3()
        vec.x = item.emitterDirection["x"]
        vec.y = item.emitterDirection["y"]
        vec.z = item.emitterDirection["z"]
        item.emitterDirection = vec

        item.assign(obj, "initialVelOmni")
        item.assign(obj, "initialVelAxis")
        item.assign(obj, "initialVelRndm")
        item.assign(obj, "initialVelDir")

        item.assign(obj, "spread")
        item.assign(obj, "initialVelRatio")
        item.assign(obj, "rate")
        item.assign(obj, "rateRndm")
        item.assign(obj, "lifeTimeRndm")

        item.assign(obj, "volumeSweep")
        item.assign(obj, "volumeMinRad")
        item.assign(obj, "airResist")
        item.assign(obj, "momentRndm")

        item.assign(obj, "emitterRotX")
        item.assign(obj, "emitterRotY")
        item.assign(obj, "emitterRotZ")

        item.assign(obj, "maxFrame")
        item.assign(obj, "startFrame")
        item.assign(obj, "lifeTime")
        item.assign(obj, "volumeSize")
        item.assign(obj, "divNumber")
        item.assign(obj, "rateStep")

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

        shape.baseSizeX = read_float(f)
        shape.baseSizeY = read_float(f)

        shape.blendModeFlags = read_uint16(f)
        shape.alphaCompareFlags = read_uint8(f)
        shape.alphaRef0 = read_uint8(f)
        shape.alphaRef1 = read_uint8(f)
        shape.zModeFlags = read_uint8(f)
        shape.texFlags = read_uint8(f)
        shape.texIdxAnimCount = read_uint8(f)
        shape.texIdx = read_uint8(f)
        shape.colorFlags = read_uint8(f)

        shape.ColorTable1Count = read_uint8(f)# colortable has 6 bytes for each of these
        shape.ColorTable2Count = read_uint8(f)
        shape.repeatDiv = read_uint16(f)
        shape.ColorPrm = hex(read_uint32(f))
        shape.ColorEnv = hex(read_uint32(f))

        shape.anmRndm = read_uint8(f)
        shape.colorLoopOfStMask = read_uint8(f)
        shape.texIdxLoopOfstMask = read_uint8(f)
        read_uint16(f)
        read_uint8(f)

        #sometimes a BSP1 section decides it wants to have a whole float matrix thing instead of color sub data
        if int(shape.flags, base=16) & 0x1000000:
            shape.floatMatrix = []
            for x in range(10):
                shape.floatMatrix.append(read_float(f))

        if shape.texIdxAnimCount != 0:#this is for some extra junk only used by mergeIdx functions
            shape.MergeIdx = read_uint32(f)
            test = read_uint32(f)
            if shape.texIdxAnimCount > 4:#extended list
                shape.MergeIdx2 = test

        if colorTable1Offs != 0:
            f.seek(start + colorTable1Offs)
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
        write_float(f, self.baseSizeX)
        write_float(f, self.baseSizeY)
        write_uint16(f, self.blendModeFlags)
        write_uint8(f, self.alphaCompareFlags)
        write_uint8(f, self.alphaRef0)
        write_uint8(f, self.alphaRef1)
        write_uint8(f, self.zModeFlags)
        write_uint8(f, self.texFlags)
        write_uint8(f, self.texIdxAnimCount)
        write_uint8(f, self.texIdx)
        write_uint8(f, self.colorFlags)
        write_uint8(f, self.ColorTable1Count)
        write_uint8(f, self.ColorTable2Count)
        write_uint16(f, self.repeatDiv)
        write_uint32(f, int(self.ColorPrm, base=16))
        write_uint32(f, int(self.ColorEnv, base=16))
        write_uint8(f, self.anmRndm)
        write_uint8(f, self.colorLoopOfStMask)
        write_uint8(f, self.texIdxLoopOfstMask)
        write_uint16(f,0)
        write_uint8(f,0)

        offs2 = 0x34

        if int(self.flags, base=16) & 0x1000000:#float matrix
            for thing in self.floatMatrix:
                write_float(f, thing)
            offs2 += 0x28


        if self.texIdxAnimCount != 0:#mergeIdx
            write_uint32(f,self.MergeIdx)
            offs2 += 4

        if self.texIdxAnimCount > 4:#even more mergeIDx stuff
            write_uint32(f,self.MergeIdx2)
            offs2 += 4

        old = f.tell()
        f.seek(start+12)
        write_uint16(f,offs2)
        offs = offs2 + 6*self.ColorTable1Count
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

        item.assign(obj[0], "baseSizeX")
        item.assign(obj[0], "baseSizeY")

        item.assign(obj[0], "blendModeFlags")
        item.assign(obj[0], "alphaCompareFlags")
        item.assign(obj[0], "alphaRef0")
        item.assign(obj[0], "alphaRef1")
        item.assign(obj[0], "zModeFlags")
        item.assign(obj[0], "texFlags")
        item.assign(obj[0], "texIdxAnimCount")
        item.assign(obj[0], "texIdx")
        item.assign(obj[0], "colorFlags")

        item.assign(obj[0], "ColorTable1Count")
        item.assign(obj[0], "ColorTable2Count")
        item.assign(obj[0], "repeatDiv")
        item.assign(obj[0], "ColorPrm")
        item.assign(obj[0], "ColorEnv")

        if "MergeIdx" in obj[0]:
            item.assign(obj[0], "MergeIdx")
        if "MergeIdx2" in obj[0]:
            item.assign(obj[0], "MergeIdx2")

        item.assign(obj[0], "anmRndm")
        item.assign(obj[0], "colorLoopOfStMask")
        item.assign(obj[0], "texIdxLoopOfstMask")

        if "floatMatrix" in obj[0]:
            item.assign(obj[0], "floatMatrix")

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

        field.position = Vector3.from_file(f)
        field.direction = Vector3.from_file(f)

        field.param1 = read_float(f)
        field.param2 = read_float(f)
        field.param3 = read_float(f)
        field.fadeIn = read_float(f)
        field.fadeOut = read_float(f)
        field.enTime = read_float(f)
        field.disTime = read_float(f)
        field.cycle = read_uint8(f)
        read_uint16(f)
        read_uint8(f)

        assert f.tell() == start + 0x44
        return field 
      
    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x44)#size
        write_uint32(f, int(self.flags, base=16))
        self.position.write(f)
        self.direction.write(f)

        write_float(f, self.param1)
        write_float(f, self.param2)
        write_float(f, self.param3)
        write_float(f, self.fadeIn)
        write_float(f, self.fadeOut)
        write_float(f, self.enTime)
        write_float(f, self.disTime)
        write_uint8(f, self.cycle)
        write_uint16(f, 0)
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

        item.assign(obj, "position")
        vec = Vector3()
        vec.x = item.position["x"]
        vec.y = item.position["y"]
        vec.z = item.position["z"]
        item.position = vec

        item.assign(obj, "direction")
        vec = Vector3()
        vec.x = item.direction["x"]
        vec.y = item.direction["y"]
        vec.z = item.direction["z"]
        item.direction = vec

        item.assign(obj, "param1")
        item.assign(obj, "param2")
        item.assign(obj, "param3")

        item.assign(obj, "fadeIn")
        item.assign(obj, "fadeOut")

        item.assign(obj, "enTime")
        item.assign(obj, "disTime")
        item.assign(obj, "cycle")

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

        field.scaleInTiming = read_float(f)
        field.scaleOutTiming = read_float(f)
        field.scaleInValueX = read_float(f)
        field.scaleOutValueX = read_float(f)
        field.scaleInValueY = read_float(f)
        field.scaleOutValueY = read_float(f)
        field.scaleOutRandom = read_float(f)

        field.scaleAnmMaxFrameX = read_uint16(f)
        field.scaleAnmMaxFrameY = read_uint16(f)

        field.alphaInTiming = read_float(f)
        field.alphaOutTiming = read_float(f)
        field.alphaInValue = read_float(f)
        field.alphaBaseValue = read_float(f)
        field.alphaOutValue = read_float(f)

        field.alphaWaveFrequency = read_float(f)
        field.alphaWaveRandom = read_float(f)
        field.alphaWaveAmplitude = read_float(f)

        field.rotateAngle = read_float(f)
        field.rotateAngleRandom = read_float(f)
        field.rotateSpeed = read_float(f)
        field.rotateSpeedRandom = read_float(f)
        field.rotateDirection = read_float(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x60)
        write_uint32(f, int(self.flags, base=16))
        write_float(f, self.scaleInTiming)
        write_float(f, self.scaleOutTiming)
        write_float(f, self.scaleInValueX)
        write_float(f, self.scaleOutValueX)
        write_float(f, self.scaleInValueY)
        write_float(f, self.scaleOutValueY)
        write_float(f, self.scaleOutRandom)
        write_uint16(f, self.scaleAnmMaxFrameX)
        write_uint16(f, self.scaleAnmMaxFrameY)
        write_float(f, self.alphaInTiming)
        write_float(f, self.alphaOutTiming)
        write_float(f, self.alphaInValue)
        write_float(f, self.alphaBaseValue)
        write_float(f, self.alphaOutValue)
        write_float(f, self.alphaWaveFrequency)
        write_float(f, self.alphaWaveRandom)
        write_float(f, self.alphaWaveAmplitude)
        write_float(f, self.rotateAngle)
        write_float(f, self.rotateAngleRandom)
        write_float(f, self.rotateSpeed)
        write_float(f, self.rotateSpeedRandom)
        write_float(f, self.rotateDirection)

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

        item.assign(obj, "scaleInTiming")
        item.assign(obj, "scaleOutTiming")

        item.assign(obj, "scaleInValueX")
        item.assign(obj, "scaleOutValueX")

        item.assign(obj, "scaleInValueY")
        item.assign(obj, "scaleOutValueY")

        item.assign(obj, "scaleOutRandom")
        item.assign(obj, "scaleAnmMaxFrameX")
        item.assign(obj, "scaleAnmMaxFrameY")

        item.assign(obj, "alphaInTiming")
        item.assign(obj, "alphaOutTiming")
        item.assign(obj, "alphaInValue")
        item.assign(obj, "alphaBaseValue")
        item.assign(obj, "alphaOutValue")

        item.assign(obj, "alphaWaveFrequency")
        item.assign(obj, "alphaWaveRandom")
        item.assign(obj, "alphaWaveAmplitude")

        item.assign(obj, "rotateAngle")
        item.assign(obj, "rotateAngleRandom")
        item.assign(obj, "rotateSpeed")
        item.assign(obj, "rotateSpeedRandom")
        item.assign(obj, "rotateDirection")

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

        field.texMtx00 = read_float(f)
        field.texMtx01 = read_float(f)
        field.texMtx02 = read_float(f)
        field.texMtx10 = read_float(f)
        field.texMtx11 = read_float(f)
        field.texMtx12 = read_float(f)

        #field.flags2 = hex(read_uint32(f))
        field.scale = read_uint8(f)
        field.indTextureID = read_uint8(f)
        field.secondTextureIndex = read_uint8(f)
        read_uint8(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x28)
        write_uint32(f, int(self.flags, base=16))

        write_float(f, self.texMtx00)
        write_float(f, self.texMtx01)
        write_float(f, self.texMtx02)
        write_float(f, self.texMtx10)
        write_float(f, self.texMtx11)
        write_float(f, self.texMtx12)

        write_uint8(f, self.scale)
        write_uint8(f, self.indTextureID)
        write_uint8(f, self.secondTextureIndex)
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
        item.assign(obj, "texMtx00")
        item.assign(obj, "texMtx01")
        item.assign(obj, "texMtx02")
        item.assign(obj, "texMtx10")
        item.assign(obj, "texMtx11")
        item.assign(obj, "texMtx12")

        item.assign(obj, "scale")
        item.assign(obj, "indTextureID")
        item.assign(obj, "secondTextureIndex")

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

        field.posRndm = read_float(f)
        field.baseVel = read_float(f)
        field.baseVelRndm = read_float(f)
        field.velInfRate = read_float(f)
        field.gravity = read_float(f)
        field.globalScale2DX = read_float(f)
        field.globalScale2DY = read_float(f)
        field.inheritScale = read_float(f)
        field.inheritAlpha = read_float(f)
        field.inheritRGB = read_float(f)

        field.ColorPrm = hex(read_uint32(f))
        field.ColorEnv = hex(read_uint32(f))
        field.timing = read_float(f)
        field.life = read_uint16(f)
        field.rate = read_uint16(f)
        field.step = read_uint8(f)
        field.texIdx = read_uint8(f)
        field.rotateSpeed = read_uint16(f)

        assert f.tell() == start + size
        return field 

    def write(self, f):
        start = f.tell()
        write_name(f, self.name)
        write_uint32(f, 0x48)
        write_uint32(f, int(self.flags, base=16))

        write_float(f, self.posRndm)
        write_float(f, self.baseVel)
        write_float(f, self.baseVelRndm)
        write_float(f, self.velInfRate)
        write_float(f, self.gravity)
        write_float(f, self.globalScale2DX)
        write_float(f, self.globalScale2DY)
        write_float(f, self.inheritScale)
        write_float(f, self.inheritAlpha)
        write_float(f, self.inheritRGB)

        write_uint32(f, int(self.ColorPrm, base=16))
        write_uint32(f, int(self.ColorEnv, base=16))
        write_float(f, self.timing)
        write_uint16(f, self.life)
        write_uint16(f, self.rate)
        write_uint8(f, self.step)
        write_uint8(f, self.texIdx)
        write_uint16(f, self.rotateSpeed)

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
        item.assign(obj, "posRndm")
        item.assign(obj, "baseVel")
        item.assign(obj, "baseVelRndm")

        item.assign(obj, "velInfRate")
        item.assign(obj, "gravity")
        item.assign(obj, "globalScale2DX")
        item.assign(obj, "globalScale2DY")
        item.assign(obj, "inheritScale")
        item.assign(obj, "inheritAlpha")
        item.assign(obj, "inheritRGB")

        item.assign(obj, "ColorPrm")
        item.assign(obj, "ColorEnv")
        item.assign(obj, "timing")
        item.assign(obj, "life")
        item.assign(obj, "rate")
        item.assign(obj, "step")
        item.assign(obj, "texIdx")
        item.assign(obj, "rotateSpeed")

        return item

#Key Frame sub-objects within the KFA1 block
class KeyBlock_field(object):
    def __init__(self):
        self.time = 0.0
        self.value = 0.0
        self.tangent_in = 0.0
        self.tangent_out = 0.0

    @classmethod
    def from_file(cls, f):
        shape = cls()
        shape.time = read_float(f)
        shape.value = read_float(f)
        shape.tangent_in = read_float(f)
        shape.tangent_out = read_float(f)
        return shape

    def write(self, f):
        write_float(f, self.time)
        write_float(f, self.value)
        write_float(f, self.tangent_in)
        write_float(f, self.tangent_out)

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
        item.assign(obj, "time")
        item.assign(obj, "value")
        item.assign(obj, "tangent_in")
        item.assign(obj, "tangent_out")
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
        shape.isLoopEnable = read_uint8(f)
        shape.unk2 = read_uint8(f)

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
        write_uint8(f, self.isLoopEnable)
        write_uint8(f, self.unk2)

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
        item.assign(obj[0], "isLoopEnable")
        item.assign(obj[0], "unk2")

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
            text = f.read(0x14).decode("shift_jis_2004")
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
            json.dump(jpc.serialize(), f, indent=4, ensure_ascii=False, default=vars)

    elif inputfile.endswith(".json"):
        if outfile == None:
            outfile = inputfile + ".jpc"

        with open(inputfile, "r", encoding="utf-8") as f:
            jpc = JPAContainer.deserialize(json.load(f))
        with open(outfile, "wb") as f:
            jpc.write(f)